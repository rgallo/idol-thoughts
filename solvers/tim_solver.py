import argparse
import collections
import csv
import datetime
import time
import json
import math
import statistics
import os
import re
import sys
import uuid
from glob import glob
import numpy as np
import itertools

from scipy.optimize import differential_evolution
from scipy.optimize import NonlinearConstraint

sys.path.append("..")

from solvers import base_solver
from helpers import StlatTerm, get_weather_idx
from idolthoughts import load_stat_data, calc_stlat_stats
import tim

STAT_CACHE = {}
GAME_CACHE = {}

BEST_RESULT = 1000000000.0

ALLOWED_IN_BASE = {"AFFINITY_FOR_CROWS", "GROWTH", "TRAVELING"}
FORCE_REGEN = {"AFFINITY_FOR_CROWS", "GROWTH", "TRAVELING"}

BIRD_WEATHER = get_weather_idx("Birds")

TIM_STLAT_LIST = tim.TIM.OFFENSE_TERMS + tim.TIM.DEFENSE_TERMS

SHUTOUT_PCT = None
TOTAL_SHUTOUTS = 0
CURRENT_ITERATION = 1
LAST_CANDIDATE = 1
MOST_RED_HOTS = 1
MIN_SHO = 0.0
MAX_NSHO = 0.0
BEST_CUTOFF = 0.0
LAST_MEAN_RATIO = 1.0
LAST_CHECKTIME = 0.0
BEST_SABL = 0
LAST_SPAN = 0.0
FINAL_SHO_VALS = []
FINAL_NSHO_VALS = []

def get_bucket_idx(val, bucket_bounds, min_sho_val, max_nsho_val):
    start_bucket, end_bucket = 0.00, 0.00
    indexofval = -1
    if min_sho_val > val >= 0.00:
        indexofval = 0
    else:
        if 1.0 >= val > max_nsho_val:
            indexofval = 6
            # print("------ red hot value = {}, max nonsho = {}".format(val, max_nsho_val))
        else:
            start_bucket = min_sho_val
            for idx, interval in enumerate(bucket_bounds):                
                end_bucket = start_bucket + ((max_nsho_val - min_sho_val) * bucket_bounds[idx])
                if end_bucket >= val >= start_bucket:
                    indexofval = idx + 1            
                start_bucket = end_bucket
    return indexofval      

def constr_fn(x):    
    return np.array(x[0] + x[1] + x[2] + x[3])

def calc_linearity(sorted_sho_nsho, red_hots):
    linears, lin_denominator, hots, shos_above_baseline = 0, 0, 0, 0
    lin_points, current_ratio, past_ratio, last_ratio, best_ratio = 0.0, 0.0, 0.0, 0.0, 0.0
    window_start, window_end, summation_start, sabls = 0, 1, 0, 0
    #window_start, window_end, summation_start, sabls = 0, 299, 0, 0    
    #back_list = []
    #front_list = []
    #previous_ratios = collections.deque([0] * 20)
    while window_end < len(sorted_sho_nsho):                        
        if sorted_sho_nsho[window_end] == 1:
            lin_denominator += 1
            current_ratio = sum(sorted_sho_nsho[window_start:window_end]) / (window_end + 1)
            if past_ratio > 0 and current_ratio >= past_ratio:
                linears += 1        
            past_ratio = current_ratio
            if sorted_sho_nsho[window_end] == 1 and window_end > 198:
                summation_start = window_end - 199            
                sabl_ratio = (sum(sorted_sho_nsho[summation_start:window_end])) / 200.0
                shos_above_baseline += sabl_ratio
                sabls += 1 if sabl_ratio > 0.075 else 0        
        window_end += 1
    #while window_end < len(sorted_sho_nsho):        
    #    previous_ratios.rotate(-1)        
    #    previous_ratios[19] = sum(sorted_sho_nsho[window_start:window_end])
    #    back_list = itertools.islice(previous_ratios, 0, 9)
    #    front_list = itertools.islice(previous_ratios, 10, 19)
    #    past_ratio = sum(back_list)
    #    current_ratio = sum(front_list)                
    #    lin_denominator += 1
    #    if current_ratio >= past_ratio:
    #        linears += 1        
    #    if sorted_sho_nsho[window_end] == 1:
    #        summation_start = window_end - 199            
    #        sabl_ratio = (sum(sorted_sho_nsho[summation_start:window_end])) / 200.0
    #        shos_above_baseline += sabl_ratio
    #        sabls += 1 if sabl_ratio > 0.06 else 0
    #    window_start += 1
    #    window_end += 1
    # we've exited the loop, so now window end should be = to len sorted sho nsho; now we get our best hot ratio
    window_end = len(sorted_sho_nsho) - red_hots - 1
    window_start = window_end
    target_shos = 0
    while target_shos < 160:
        window_start -= 1	
        last_ratio = sum(sorted_sho_nsho[window_start:window_end]) / (window_end - window_start + 1)
        if last_ratio >= best_ratio:
            best_ratio = last_ratio
            hots = sum(sorted_sho_nsho[window_start:window_end])
        else:
            target_shos = (best_ratio * (window_end - window_start + 1)) - sum(sorted_sho_nsho[window_start:window_end])
            target_shos = target_shos / (1 - best_ratio)       
    # % of values that are linear with respect to the mean value of the front half of their window versus the back half
    if lin_denominator > 0:
        lin_points = float(linears) / float(lin_denominator)
    # best possible hot ratio, should favor solutions of equal red hots with better hot ratios    
    return lin_points, best_ratio, hots, shos_above_baseline, sabls

def run_tims(game, season_team_attrs, team_stat_data, pitcher_stat_data, pitchers, terms, mods, tim_tier):
    awayMods, homeMods = [], []
    game_attrs = base_solver.get_attrs_from_paired_game(season_team_attrs, game)
    special_game_attrs = (game_attrs["home"].union(game_attrs["away"])) - base_solver.ALLOWED_IN_BASE
    if special_game_attrs:
        return -1, False, -1, False
    away_game, home_game = game["away"], game["home"]
    is_away_shutout, is_home_shutout = not float(away_game["opposing_team_rbi"]), not float(home_game["opposing_team_rbi"])

    awayPitcher, awayTeam = pitchers.get(away_game["pitcher_id"])
    homePitcher, homeTeam = pitchers.get(home_game["pitcher_id"])
    awayStlatdata = calc_stlat_stats(awayPitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data)
    homeStlatdata = calc_stlat_stats(homePitcher, homeTeam, awayTeam, team_stat_data, pitcher_stat_data)
    return tim_tier.calc(awayStlatdata), is_away_shutout, tim_tier.calc(homeStlatdata), is_home_shutout

def minimize_func(parameters, *data):
    run_id = uuid.uuid4()
    starttime = datetime.datetime.now()    
    global BEST_RESULT
    global SHUTOUT_PCT
    global TOTAL_SHUTOUTS
    global CURRENT_ITERATION
    global MOST_RED_HOTS
    global MIN_SHO
    global MAX_NSHO
    global BEST_CUTOFF
    global LAST_MEAN_RATIO
    global LAST_CANDIDATE
    global LAST_CHECKTIME
    global BEST_SABL
    global LAST_SPAN
    global FINAL_SHO_VALS
    global FINAL_NSHO_VALS
    if len(parameters) > 4:
        coefficients = parameters
        bucket_bounds = [0.2, 0.2, 0.2, 0.2]
        static_bounds = True
        stlat_list, mod_list, stat_file_map, game_list, team_attrs, debug, debug2, debug3 = data
    else:
        bucket_bounds = parameters
        static_bounds = False
        coefficients, stlat_list, mod_list, stat_file_map, game_list, team_attrs, debug, debug2, debug3 = data
    base_solver.debug_print("func start: {}".format(starttime), debug3, run_id)
    if type(stlat_list) == dict:  # mod mode
        terms = stlat_list
        mods = collections.defaultdict(lambda: {"opp": {}, "same": {}})
        for mod, (a, b, c) in zip(mod_list, zip(*[iter(coefficients)] * 3)):
            mods[mod.attr.lower()][mod.team.lower()][mod.stat.lower()] = StlatTerm(a, b, c)
    else:  # base mode
        terms = {stat: StlatTerm(a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(coefficients)] * 3))}
        mods = {}
    results = [[] for _ in range(7)]    
    tim_tier = tim.TIM("asdf", terms, None, None, None)
    sho_vals = []
    nsho_vals = []
    all_vals = []
    sho_nsho = []
    reject_solution, viability_unchecked = False, True
    quarter_mean_ratio, quarter_span = 1.0, 0.0
    min_sho_val, max_sho_val, min_nsho_val, max_nsho_val, median_sho_val, median_nsho_val, mean_sho_val, mean_nsho_val, shos, nshos = 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0, 0
    if not FINAL_SHO_VALS:
        for season in range(3, 12):        
            season_start = datetime.datetime.now()
            base_solver.debug_print("season {} start: {}".format(season, season_start), debug3, run_id)
            pitchers, team_stat_data, pitcher_stat_data, last_stat_filename = None, None, None, None
            season_team_attrs = team_attrs.get(str(season), {})
            season_days = 0        
            if static_bounds:
                if TOTAL_SHUTOUTS > 0 and len(sho_vals) >= (TOTAL_SHUTOUTS / 4) and viability_unchecked:
                    # check this solution for viability for later rejection criteria
                    quarter_mean_ratio = (sum(sho_vals) * len(nsho_vals)) / (len(sho_vals) * sum(nsho_vals))      
                    quarter_span = max(sho_vals) - min(nsho_vals)
                    viability_unchecked = False
                    if (quarter_mean_ratio / LAST_MEAN_RATIO) < 0.95 and quarter_mean_ratio < 1.45:
                        reject_solution = True
                        break
                    if (LAST_SPAN * 0.9) > quarter_span:
                        reject_solution = True
                        break
            for day in range(1, 125):
                cached_games = GAME_CACHE.get((season, day))
                if cached_games:
                    games = cached_games
                else:
                    games = [row for row in game_list if row["season"] == str(season) and row["day"] == str(day)]
                    if not games:
                        continue
                    GAME_CACHE[(season, day)] = games
                season_days += 1
                paired_games = base_solver.pair_games(games)
                schedule = base_solver.get_schedule_from_paired_games(paired_games)
                day_mods = base_solver.get_attrs_from_paired_games(season_team_attrs, paired_games)
                cached_stats = STAT_CACHE.get((season, day))
                if cached_stats:
                    team_stat_data, pitcher_stat_data, pitchers = cached_stats
                else:
                    stat_filename = stat_file_map.get((season, day))
                    if stat_filename:
                        last_stat_filename = stat_filename
                        pitchers = base_solver.get_pitcher_id_lookup(stat_filename)
                        team_stat_data, pitcher_stat_data = load_stat_data(stat_filename, schedule, day, season_team_attrs)
                    elif base_solver.should_regen(day_mods):
                        pitchers = base_solver.get_pitcher_id_lookup(last_stat_filename)
                        team_stat_data, pitcher_stat_data = load_stat_data(last_stat_filename, schedule, day, season_team_attrs)
                    STAT_CACHE[(season, day)] = (team_stat_data, pitcher_stat_data, pitchers)
                if not pitchers:
                    raise Exception("No stat file found")
                for game in paired_games:
                    awayTIM, awayShutout, homeTIM, homeShutout = run_tims(game, season_team_attrs, team_stat_data, pitcher_stat_data, pitchers, terms, mods, tim_tier)                
                    if awayTIM > 0:
                        min_sho_val = awayTIM if awayTIM < min_sho_val and awayShutout else min_sho_val
                        max_sho_val = awayTIM if awayTIM > max_sho_val and awayShutout else max_sho_val
                        min_nsho_val = awayTIM if awayTIM < min_nsho_val and not awayShutout else min_nsho_val
                        max_nsho_val = awayTIM if awayTIM > max_nsho_val and not awayShutout else max_nsho_val
                        all_vals.append(awayTIM)
                        if awayShutout:
                            sho_vals.append(awayTIM)                            
                            sho_nsho.append(1)
                        else:
                            nsho_vals.append(awayTIM)                                                                        
                            sho_nsho.append(0)
                    if homeTIM > 0:
                        min_sho_val = homeTIM if homeTIM < min_sho_val and homeShutout else min_sho_val
                        max_sho_val = homeTIM if homeTIM > max_sho_val and homeShutout else max_sho_val
                        min_nsho_val = homeTIM if homeTIM < min_nsho_val and not homeShutout else min_nsho_val
                        max_nsho_val = homeTIM if homeTIM > max_nsho_val and not homeShutout else max_nsho_val  
                        all_vals.append(homeTIM)
                        if homeShutout:
                            sho_vals.append(homeTIM)                                                
                            sho_nsho.append(1)
                        else:
                            nsho_vals.append(homeTIM)                           
                            sho_nsho.append(0)    

    if not static_bounds and not FINAL_SHO_VALS:
        FINAL_SHO_VALS = sho_vals
        FINAL_NSHO_VALS = nsho_vals
    if not static_bounds:
        sho_vals = FINAL_SHO_VALS
        nsho_vals = FINAL_NSHO_VALS
        
    total_unexvar = 1000000000.0
    shos = len(sho_vals)
    nshos = len(nsho_vals)
    mean_sho_val = sum(sho_vals) / shos
    mean_nsho_val = sum(nsho_vals) / nshos
    if not reject_solution:        
        all_vals_array = np.array(all_vals)
        sho_nsho_array = np.array(sho_nsho)
        sortnshoby = all_vals_array.argsort()
        sorted_sho_nsho = sho_nsho_array[sortnshoby]
        all_vals_array.sort()
        # need to determine the median sho value and median nsho value
        # median sho        
        sho_vals.sort()
        left_center = math.floor((shos + 1.0) / 2.0)
        right_center = math.ceil((shos + 1.0) / 2.0)    
        median_sho_val = (sho_vals[left_center] + sho_vals[right_center]) / 2.0
        
        # median nsho        
        nsho_vals.sort()
        left_center = math.floor((nshos + 1.0) / 2.0)
        right_center = math.ceil((nshos + 1.0) / 2.0)
        median_nsho_val = (nsho_vals[left_center] + nsho_vals[right_center]) / 2.0        

        # we need to automatically reject solutions that are unlikely to give a beter solution, which will save time
        reject_solution = (max_sho_val <= max_nsho_val) or (min_sho_val <= min_nsho_val) or (mean_sho_val <= mean_nsho_val) or (median_sho_val <= median_nsho_val) or (median_sho_val <= mean_nsho_val)    
    
    if not reject_solution:                                       
        # establish the actual bucket bounds without using a loop, for referencing in map functions
        bucket_end = []
        bucket_end.append(min_sho_val)
        cool_end = min_sho_val + ((max_nsho_val - min_sho_val) * bucket_bounds[0])
        bucket_end.append(cool_end)
        temp_end = min_sho_val + ((max_nsho_val - min_sho_val) * (bucket_bounds[1] + bucket_bounds[0]))
        bucket_end.append(temp_end)
        tepid_end = min_sho_val + ((max_nsho_val - min_sho_val) * (bucket_bounds[2] + bucket_bounds[1] + bucket_bounds[0]))
        bucket_end.append(tepid_end)
        warm_end = min_sho_val + ((max_nsho_val - min_sho_val) * (bucket_bounds[3] + bucket_bounds[2] + bucket_bounds[1] + bucket_bounds[0]))
        bucket_end.append(warm_end)
        bucket_end.append(max_nsho_val)    
        bucket_end.append(1.00)                    
    
        bonus_points, red_hot_points, dead_cold_points, hsho_points, sum_actuals, full_buckets = 0.0, 0.0, 0.0, 0.0, 0.0, 0
        lin_bonus, ratio_bonus = 1.0, 0.0
        red_hots, hyp_hots, hot_shos, warm_shos, tepid_shos, temperate_shos, cool_shos = 0, 0, 0, 0, 0, 0, 0
        hots, warms, tepids, temperates, cools, dead_colds = 0, 0, 0, 0, 0, 0            
        high_shos = sum(map(lambda x : x > mean_nsho_val, sho_vals))
        high_nshos = sum(map(lambda x : x >= mean_nsho_val, nsho_vals))
        inspect_cutoff = high_shos - (high_nshos * (shos / nshos))

        if not SHUTOUT_PCT:
            total_games = 0            
            TOTAL_SHUTOUTS = len(sho_vals)
            total_games = len(nsho_vals) + len(sho_vals)
            SHUTOUT_PCT = TOTAL_SHUTOUTS / total_games

        dead_colds = sum(map(lambda x : x < bucket_end[0], nsho_vals))        
        full_buckets = full_buckets + (1 if dead_colds > 0 else 0)

        cool_shos = sum(map(lambda x : (x < bucket_end[1] and x >= bucket_end[0]), sho_vals))
        cools = sum(map(lambda x : (x < bucket_end[1] and x >= bucket_end[0]), nsho_vals)) + cool_shos
        full_buckets = full_buckets + (1 if (cools + cool_shos) > 0 else 0)

        temperate_shos = sum(map(lambda x : (x < bucket_end[2] and x >= bucket_end[1]), sho_vals))
        temperates = sum(map(lambda x : (x < bucket_end[2] and x >= bucket_end[1]), nsho_vals)) + temperate_shos
        full_buckets = full_buckets + (1 if (temperates + temperate_shos) > 0 else 0)

        tepid_shos = sum(map(lambda x : (x < bucket_end[3] and x >= bucket_end[2]), sho_vals))
        tepids = sum(map(lambda x : (x < bucket_end[3] and x >= bucket_end[2]), nsho_vals)) + tepid_shos
        full_buckets = full_buckets + (1 if (tepids + tepid_shos) > 0 else 0)

        warm_shos = sum(map(lambda x : (x < bucket_end[4] and x >= bucket_end[3]), sho_vals))
        warms = sum(map(lambda x : (x < bucket_end[4] and x >= bucket_end[3]), nsho_vals)) + warm_shos
        full_buckets = full_buckets + (1 if (warms + warm_shos) > 0 else 0)

        hot_shos = sum(map(lambda x : (x <= bucket_end[5] and x >= bucket_end[4]), sho_vals))
        hots = sum(map(lambda x : (x <= bucket_end[5] and x >= bucket_end[4]), nsho_vals)) + hot_shos
        full_buckets = full_buckets + (1 if (hots + hot_shos) > 0 else 0)

        red_hots = sum(map(lambda x : x > bucket_end[5], sho_vals))        
        full_buckets = full_buckets + (1 if red_hots > 0 else 0)
        lin_bonus, ratio_bonus, hyp_hots, sum_sabl_actual, sabls = calc_linearity(sorted_sho_nsho, red_hots)        
        shos_above_baseline = (sabls / TOTAL_SHUTOUTS) * sum_sabl_actual

        red_hot_mod = high_shos / high_nshos
        hsho_points = inspect_cutoff * 600000.0 * red_hot_mod * lin_bonus
        val_span = max_sho_val - min_nsho_val
        cool_points, temperate_points, tepid_points, warm_points, hot_points = 0.0, 0.0, 0.0, 0.0, 0.0
                     
        if static_bounds:                                    
            red_hot_points = red_hots * 30000000.0 * lin_bonus
            dead_cold_points = dead_colds * 300000.0 * lin_bonus
            bonus_points += dead_cold_points + red_hot_points + (15000000.0 * (hyp_hots ** ratio_bonus) * ratio_bonus * red_hot_mod * lin_bonus)                      
            bonus_points += hsho_points
            bonus_points += 10000000 * shos_above_baseline * lin_bonus            
        else:                     
            if full_buckets > 6:
                cool_points = ((1 - (cool_shos / cools)) * 30750000.0) + ((len(sho_vals) - cool_shos) * 100)
                temperate_points = (((temperate_shos / temperates) - SHUTOUT_PCT) * 2250000.0)
                temperate_points += (temperate_shos * 100) if (temperate_points > 0) else 0

                tepid_points = (((tepid_shos / tepids) - (temperate_shos / temperates)) * 6750000.0)
                tepid_points += (tepid_shos * 100) if (tepid_points > 0) else 0
                if (tepid_points > 0 and temperate_points <= 0): 
                    tepid_points = 0

                warm_points = (((warm_shos / warms) - (tepid_shos / tepids)) * 20250000.0)
                warm_points += (warm_shos * 100) if (warm_points > 0) else 0
                if (warm_points > 0 and tepid_points <= 0): 
                    warm_points = 0

                hot_points = (((hot_shos / hots) - (warm_shos / warms)) * 60750000.0)
                hot_points += (hot_shos * 100) if (hot_points > 0) else 0
                if (hot_points > 0 and warm_points <= 0): 
                    hot_points = 0

                bonus_points += cool_points + temperate_points + tepid_points + warm_points + hot_points

                # penalize the solution by how far we are from the determined "best" hot %
                bonus_points -= (ratio_bonus - (hot_shos / hots)) * 60750000.0
            
                sum_actuals = (hot_shos / hots) + (warm_shos / warms) + (tepid_shos / tepids) + (temperate_shos / temperates) + (cool_shos / cools)
                red_hot_points = (red_hots + sum_actuals) * 30000000.0
                dead_cold_points = dead_colds * 300000.0 * sum_actuals
   
        if full_buckets > 6 or static_bounds:             
            total_unexvar -= bonus_points                                  
     
    base_solver.debug_print("total unexvar {}".format(total_unexvar), debug2, run_id)        
    if total_unexvar < BEST_RESULT:
        BEST_RESULT = total_unexvar        
        MIN_SHO = min_sho_val
        MAX_NSHO = max_nsho_val         
        LAST_SPAN = val_span
        base_solver.debug_print("-" * 20, debug, run_id)
        actual, points = 0.0, 0.0        

        points = dead_cold_points
        base_solver.debug_print("{:.4f}-{:.4f} :: actual {:.4f}, points {}".format(0.0, bucket_end[0], 0.0, points), debug, ":::::")                                       
        base_solver.debug_print("dead cold: {} shutouts in {} games".format(0, dead_colds), debug, ":::::")    
        
        if static_bounds:
            actual = (cool_shos + temperate_shos) / (cools + temperates)            
            points = 0.0
        else:
            actual = cool_shos / cools        
            points = cool_points
        base_solver.debug_print("{:.4f}-{:.4f} :: actual {:.4f}, points {}".format(bucket_end[0], bucket_end[1], actual, points), debug, ":::::")                                       
        base_solver.debug_print("cool: {} shutouts in {} games".format(cool_shos, cools), debug, ":::::")                                                                    
        
        if static_bounds:
            actual = (cool_shos + temperate_shos + tepid_shos) / (cools + temperates + tepids)            
            points = 0.0
        else:
            actual = temperate_shos / temperates
            points = temperate_points
        base_solver.debug_print("{:.4f}-{:.4f} :: actual {:.4f}, points {}".format(bucket_end[1], bucket_end[2], actual, points), debug, ":::::")                                               
        base_solver.debug_print("temperate: {} shutouts in {} games".format(temperate_shos, temperates), debug, ":::::")                                                            
        
        if static_bounds:
            actual = (temperate_shos + tepid_shos + warm_shos) / (temperates + tepids + warms)    
            points = 0.0
        else:
            actual = tepid_shos / tepids
            points = tepid_points
        base_solver.debug_print("{:.4f}-{:.4f} :: actual {:.4f}, points {}".format(bucket_end[2], bucket_end[3], actual, points), debug, ":::::")                                               
        base_solver.debug_print("tepid: {} shutouts in {} games".format(tepid_shos, tepids), debug, ":::::")                                                            
        
        if static_bounds:
            actual = (tepid_shos + warm_shos + hot_shos) / (tepids + warms + hots)            
            points = 0.0
        else:
            actual = warm_shos / warms
            points = warm_points
        base_solver.debug_print("{:.4f}-{:.4f} :: actual {:.4f}, points {}".format(bucket_end[3], bucket_end[4], actual, points), debug, ":::::")                                               
        base_solver.debug_print("warm: {} shutouts in {} games".format(warm_shos, warms), debug, ":::::")                                                            
        
        if static_bounds:
            actual = (warm_shos + hot_shos) / (warms + hots)    
            points = 0.0
        else:
            actual = hot_shos / hots
            points = hot_points
        base_solver.debug_print("{:.4f}-{:.4f} :: actual {:.4f}, points {}".format(bucket_end[4], bucket_end[5], actual, points), debug, ":::::")                                               
        base_solver.debug_print("hot: {} shutouts in {} games".format(hot_shos, hots), debug, ":::::")                                                            

        points = red_hot_points        
        base_solver.debug_print("{:.4f}-{:.4f} :: actual {:.4f}, points {}".format(bucket_end[5], bucket_end[6], 1.00, points), debug, ":::::")                                               
        base_solver.debug_print("red hot: {} shutouts in {} games".format(red_hots, red_hots), debug, ":::::")                                                                    
        
        base_solver.debug_print("# full buckets = {}, bonus points = {:.2f}, hsho points = {:.2f}, inspecting {:.0f}, best {:.0f}, iteration # {}, SABL {:.2f}, best {:.2f}".format(full_buckets, bonus_points, hsho_points, inspect_cutoff, BEST_CUTOFF, CURRENT_ITERATION, shos_above_baseline, BEST_SABL), debug, ":::::")            
        base_solver.debug_print("Best Result so far - {:.0f}, {} red hots, linearity bonus = {:.4f}, {} hots at = {:.4f}, {:.2f} % high shos, {:.2f} % high nshos, {} dead colds".format(BEST_RESULT, red_hots, lin_bonus, hyp_hots, ratio_bonus, ((high_shos / len(sho_vals)) * 100), ((high_nshos / len(nsho_vals)) * 100), dead_colds), debug, ":::::")
        base_solver.debug_print("mean ratio {:.4f}, quarter mean ratio {:.4f}, last mean ratio = {:.4f}, quarter over last mean = {:.4f}".format((mean_sho_val / mean_nsho_val), quarter_mean_ratio, LAST_MEAN_RATIO, (quarter_mean_ratio / LAST_MEAN_RATIO)), debug, ":::::")        
        base_solver.debug_print("Shutouts above baseline % = {}, {:.2f}%, span = {:.4f}, quarter span = {:.4f}".format(sabls, (sabls / TOTAL_SHUTOUTS) * 100, val_span, quarter_span), debug, ":::::")        
        if red_hots >= MOST_RED_HOTS:            
            if type(stlat_list) == dict:
                mods_output = "\n".join("{},{},{},{},{},{}".format(stat.attr, stat.team, stat.stat, a, b, c) for stat, (a, b, c) in zip(mod_list, zip(*[iter(coefficients)] * 3)))
                base_solver.debug_print("-" * 20 + "\n" + mods_output, debug, run_id)
            else:
                terms_output = "\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(coefficients)] * 3)))
                base_solver.debug_print("-" * 20 + "\n" + terms_output, debug, run_id)
        base_solver.debug_print("-" * 20, debug, run_id)        
        base_solver.debug_print("Successful candidate at Iteration # {}, last candidate at {}, {} iterations between successful candidates".format(CURRENT_ITERATION, LAST_CANDIDATE, CURRENT_ITERATION - LAST_CANDIDATE), debug, datetime.datetime.now())           
        LAST_CANDIDATE = CURRENT_ITERATION
        MOST_RED_HOTS = red_hots
        BEST_CUTOFF = inspect_cutoff
        BEST_SABL = shos_above_baseline
        LAST_MEAN_RATIO = (mean_sho_val / mean_nsho_val) if ((mean_sho_val / mean_nsho_val) > LAST_MEAN_RATIO) else LAST_MEAN_RATIO
    endtime = datetime.datetime.now()
    base_solver.debug_print("func end: {}, run time {}".format(endtime, endtime-starttime), debug3, run_id)        
    if ((CURRENT_ITERATION % 100 == 0 and CURRENT_ITERATION < 10000) or CURRENT_ITERATION % 500 == 0):
        base_solver.debug_print("Best so far - {:.0f}, iteration # {}, {} red hots, {:.0f} net high shos, {:.2f} shutouts above baseline".format(BEST_RESULT, CURRENT_ITERATION, MOST_RED_HOTS, BEST_CUTOFF, BEST_SABL), debug, datetime.datetime.now())
    CURRENT_ITERATION += 1    
    current_time = time.process_time()
    if (current_time - LAST_CHECKTIME) > 100:
        LAST_CHECKTIME = current_time
        time.sleep(10)
    if (CURRENT_ITERATION % 25000 == 0):
        time.sleep(600)
        print("10 minute power nap")
    return total_unexvar


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--statfolder', help="path to stat folder")
    parser.add_argument('--gamefile', help="path to game file")
    parser.add_argument('--mod', help="mod to calculate for")
    parser.add_argument('--debug', help="print output", action='store_true')
    parser.add_argument('--debug2', help="print output", action='store_true')
    parser.add_argument('--debug3', help="print output", action='store_true')
    args = parser.parse_args()
    return args

def main():
    print(datetime.datetime.now())
    global BEST_RESULT    
    cmd_args = handle_args()
    bounds = [[-1, 9], [0, 3], [-1, 6]] * len(TIM_STLAT_LIST)
    nlc = NonlinearConstraint(constr_fn, 0.01, 0.99, keep_feasible=True)    
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    game_list = base_solver.get_games(cmd_args.gamefile)
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    args = (TIM_STLAT_LIST, None, stat_file_map, game_list, team_attrs, cmd_args.debug,
            cmd_args.debug2, cmd_args.debug3)
    # nlc = NonlinearConstraint(constr_f, 1.0, 1.0)
    result = differential_evolution(minimize_func, bounds, args=args, popsize=2, tol=0.1,
                                    mutation=(0.05, 1.99), recombination=0.5, workers=4, maxiter=1)
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(TIM_STLAT_LIST,
                                                                                   zip(*[iter(result.x)] * 3))))

    BEST_RESULT = 1000000000.0
    # now we want to take our stlat coefficients list and optimize the bounds for the best result
    coefficients = result.x
    bounds = [[0.001, 0.9]] * 4
    args = (coefficients, TIM_STLAT_LIST, None, stat_file_map, game_list, team_attrs, cmd_args.debug,
            cmd_args.debug2, cmd_args.debug3)
    
    # start_second_stage = input("Press enter to start optimizing the bounds")

    print("****** Starting Second Stage ******")
    results = differential_evolution(minimize_func, bounds, args=args, popsize=50, tol=0.1,
                                    mutation=(0.05, 1.99), recombination=0.7, workers=4, constraints=(nlc), maxiter=10)
    #now that we have our solution
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(TIM_STLAT_LIST,
                                                                                   zip(*[iter(coefficients)] * 3))))
    bucket_bounds = results.x

    BEST_RESULT = 1000000000.0                  
    
    print("Outputting final solution parameters.")    
    final_unexvar = minimize_func(bucket_bounds, *args)

    # start_bucket, end_bucket = 0.00, MIN_SHO
    # print("\n {} - {}".format(start_bucket, end_bucket))
    # for idx, interval in enumerate(bucket_bounds):
    #    start_bucket = end_bucket
    #    end_bucket = start_bucket + (bucket_bounds[idx] * (MAX_NSHO - MIN_SHO))                        
    #    print("\n {} - {}".format(start_bucket, end_bucket))
    # start_bucket, end_bucket = MAX_NSHO, 1.00
    # print("\n {} - {}".format(start_bucket, end_bucket))
    # result_fail_rate = minimize_func(result.x[:-5], TIM_STLAT_LIST, None, stat_file_map,
    #                                             game_list, team_attrs, False, False, False)
    # print("Result fail rate: {:.2f}%".format(result_fail_rate * 100.0))
    print(datetime.datetime.now())


if __name__ == "__main__":
    main()
