import argparse
import collections
import csv
import datetime
import json
import math
import statistics
import os
import re
import sys
import uuid
from glob import glob
import numpy as np

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
MOST_RED_HOTS = 1
MIN_SHO = 0.0
MAX_NSHO = 0.0

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
    

def constr_f(x):
    return np.array(x[111] + x[112] + x[113] + x[114] + x[115])

def constr_fn(x):
    return np.array(x[0] + x[1] + x[2] + x[3] + x[4])

def calc_linearity(sho_vals, nsho_vals, red_hots):
    sho_idx, nsho_idx, linears, lin_denominator, hots = 0, 0, 0, 0, 0
    lin_points, current_ratio, past_ratio, last_ratio, best_ratio = 0.0, 0.0, 0.0, 0.0, 0.0
    window_start, window_end, move_idx, move_from_idx = 0, 499, 0, 0    
    window = []
    previous_ratios = [0.0] * 20
    while (sho_idx < len(sho_vals)):        
        if (sho_vals[sho_idx] <= nsho_vals[nsho_idx] or nsho_idx == (len(nsho_vals) - 1)):            
            window.append(1)
            sho_idx += 1            
        else:
            nsho_idx += 1   
            window.append(0)        
        if len(window) > 499:                       
            current_ratio = sum(window[window_start:window_end]) / 500.0                       
            for idx, val in enumerate(previous_ratios):
                move_idx = len(previous_ratios) - 1 - idx
                # print("move index = {}, value = {}".format(move_idx, previous_ratios[move_idx]), ":::::")
                move_from_idx = move_idx - 1
                # print("move from index = {}, value = {}".format(move_from_idx, previous_ratios[move_from_idx]), ":::::")
                if move_from_idx > -1:
                    previous_ratios[move_idx] = previous_ratios[move_from_idx]          
            previous_ratios[0] = current_ratio            
            if (len(window)) > 519:                                
                past_ratio = sum(previous_ratios[10:19])
                current_ratio = sum(previous_ratios[0:9])
                lin_denominator += 1                                  
                if current_ratio >= past_ratio:
                    linears += 1
            if (sho_idx == len(sho_vals) - 1):                                
                window_end = len(sho_vals) + len(nsho_vals) - red_hots - 1
                window_start = window_end
                target_shos = 0
                while target_shos < (red_hots * 10):
                    window_start -= 1	
                    last_ratio = sum(window[window_start:window_end]) / (window_end - window_start + 1)
                    if last_ratio >= best_ratio:
                        best_ratio = last_ratio
                        hots = sum(window[window_start:window_end])
                    else:
                        target_shos = (best_ratio * (window_end - window_start + 1)) - sum(window[window_start:window_end])
                        target_shos = target_shos / (1 - best_ratio)                            
            window_start += 1
            window_end += 1             
    # % of values that are linear with respect to the mean value of the front half of their window versus the back half
    if lin_denominator > 0:
        lin_points = float(linears) / float(lin_denominator)
    # best possible hot ratio, should favor solutions of equal red hots with better hot ratios    
    return lin_points, best_ratio, hots

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
    if len(parameters) > 5:
        coefficients = parameters
        bucket_bounds = [0.2, 0.2, 0.2, 0.2, 0.2]
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
    sum_sho_in_bucket = []
    sum_nsho_in_bucket = []
    tim_tier = tim.TIM("asdf", terms, None, None, None)
    sho_vals = []
    nsho_vals = []
    min_sho_val, max_sho_val, min_nsho_val, max_nsho_val, median_sho_val, median_nsho_val, mean_sho_val, mean_nsho_val, shos, nshos = 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0, 0    
    for season in range(3, 12):        
        season_start = datetime.datetime.now()
        base_solver.debug_print("season {} start: {}".format(season, season_start), debug3, run_id)
        pitchers, team_stat_data, pitcher_stat_data, last_stat_filename = None, None, None, None
        season_team_attrs = team_attrs.get(str(season), {})
        season_days = 0
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
                    if awayShutout:
                        sho_vals.append(awayTIM)    
                        mean_sho_val += math.log(awayTIM)
                    else:
                        nsho_vals.append(awayTIM)                                                
                        mean_nsho_val += math.log(awayTIM)
                if homeTIM > 0:
                    min_sho_val = homeTIM if homeTIM < min_sho_val and homeShutout else min_sho_val
                    max_sho_val = homeTIM if homeTIM > max_sho_val and homeShutout else max_sho_val
                    min_nsho_val = homeTIM if homeTIM < min_nsho_val and not homeShutout else min_nsho_val
                    max_nsho_val = homeTIM if homeTIM > max_nsho_val and not homeShutout else max_nsho_val  
                    if homeShutout:
                        sho_vals.append(homeTIM)                        
                        mean_sho_val += math.log(homeTIM)
                    else:
                        nsho_vals.append(homeTIM)   
                        mean_nsho_val += math.log(homeTIM)
    # need to determine the median sho value and median nsho value
    # median sho
    shos = len(sho_vals)
    sho_vals.sort()
    left_center = math.floor((shos + 1.0) / 2.0)
    right_center = math.ceil((shos + 1.0) / 2.0)    
    median_sho_val = (sho_vals[left_center] + sho_vals[right_center]) / 2.0
    mean_sho_val = math.exp(mean_sho_val / shos)
    # median nsho
    nshos = len(nsho_vals)
    nsho_vals.sort()
    left_center = math.floor((nshos + 1.0) / 2.0)
    right_center = math.ceil((nshos + 1.0) / 2.0)
    median_nsho_val = (nsho_vals[left_center] + nsho_vals[right_center]) / 2.0
    mean_nsho_val = math.exp(mean_nsho_val / nshos)    
        
    # pocket statistical information within each bucket
    min_shos = [0, min_sho_val, 0, 0, 0, 0, 0]
    mean_shos = [0, 0, 0, 0, 0, 0, 0]
    max_shos = [0, 0, 0, 0, 0, 0, max_sho_val]
    min_nshos = [min_nsho_val, 0, 0, 0, 0, 0, 0]
    mean_nshos = [0, 0, 0, 0, 0, 0, 0]
    max_nshos = [0, 0, 0, 0, 0, max_nsho_val, 0]
    lin_bonus, ratio_bonus = 1.0, 0.0
    hots = 0
    if (max_sho_val > max_nsho_val) and (min_sho_val > min_nsho_val) and (mean_sho_val > mean_nsho_val):                
        previous_idx, val_count, sum_log = 1, 0, 0.0                
        for idx, val in enumerate(sho_vals):            
            bucket_idx = get_bucket_idx(val, bucket_bounds, min_sho_val, max_nsho_val)
            if bucket_idx > previous_idx:
                max_shos[bucket_idx - 1] = sho_vals[idx - 1]
                min_shos[bucket_idx] = val
                if val_count > 0:
                    mean_shos[bucket_idx - 1] = math.exp(sum_log / val_count)
                val_count = 1
                sum_log = math.log(val)
                previous_idx = bucket_idx
            else:
                sum_log += math.log(val)
                val_count += 1
            results[bucket_idx].append(True)
        previous_idx, val_count, sum_log = 0, 0, 0.0                
        for idx, val in enumerate(nsho_vals):
            bucket_idx = get_bucket_idx(val, bucket_bounds, min_sho_val, max_nsho_val)
            if bucket_idx > previous_idx:
                max_nshos[bucket_idx - 1] = nsho_vals[idx - 1]
                min_nshos[bucket_idx] = val
                if val_count > 0:
                    mean_nshos[bucket_idx - 1] = math.exp(sum_log / val_count)
                val_count = 1
                sum_log = math.log(val)
                previous_idx = bucket_idx
            else:
                sum_log += math.log(val)
                val_count += 1
            results[bucket_idx].append(False)    
            if idx == (len(nsho_vals) - 1):
                sum_log += math.log(val)
                val_count += 1
                mean_nshos[bucket_idx] = math.exp(sum_log / val_count)
        if not SHUTOUT_PCT:
            total_games = 0            
            TOTAL_SHUTOUTS = len(sho_vals)
            total_games = len(nsho_vals) + len(sho_vals)
            SHUTOUT_PCT = TOTAL_SHUTOUTS / total_games
    # going to move to subtracting things we like to see from a big number RATHER than "erroring" with big number in multiple cases.        
    penalty_points = 100000000.0
    penalty = 1.0
    total_unexvar = 1000000000.0
    bonus_points, red_hot_points, dead_cold_points, full_buckets = 0.0, 0.0, 0.0, 0
    if (max_sho_val > max_nsho_val) and (min_sho_val > min_nsho_val) and (mean_sho_val > mean_nsho_val):                
        if static_bounds:            
            games, shutouts, prev_games, prev_shutouts, nextprev_games, nextprev_shutouts, red_hots, previous_actual, multiplier = 0, 0, 0, 0, 0, 0, 0, 0.0, 750000.0
            for idx, bucket in enumerate(results):               
                if bucket:            
                    full_buckets += 1
                    shutouts = sum([val for val in bucket if val])                                     
                    games = len(bucket)                      
                    if idx == 6:     
                        actual = shutouts / games
                        if actual == 1.0:
                            red_hots = shutouts                    
                            red_hot_points = red_hots * 30000000.0
                            lin_bonus, ratio_bonus, hots = calc_linearity(sho_vals, nsho_vals, red_hots)
                        else:
                            red_hot_points = 30000000.0 * actual                        
                    else:                    
                        actual = shutouts / games
                        if actual == 0.0 and idx == 0:
                            dead_cold_points = games * 300000.0
                    if idx > 1:
                        if (mean_nshos[idx - 1] > 0):
                            bucket_bonus = (mean_shos[idx - 1] - mean_nshos[idx - 1]) / (max_nsho_val - min_sho_val)                            
                        else:
                            bucket_bonus = 0
                        if idx == 2:                            
                            actual = ((prev_shutouts + shutouts) / (prev_games + games))
                        else:
                            if idx == 6:
                                actual = ((prev_shutouts + nextprev_shutouts) / (prev_games + nextprev_games))
                            else:
                                actual = ((prev_shutouts + nextprev_shutouts + shutouts) / (prev_games + nextprev_games + games))
                        # if actual > previous_actual:
                            # bonus_points += (actual + (actual - previous_actual) + bucket_bonus) * multiplier                               
                    if idx > 0 and games > 0:
                        previous_actual = actual
                    nextprev_games = prev_games
                    prev_games = games       
                    nextprev_shutouts = prev_shutouts
                    prev_shutouts = shutouts
                if idx > 1:
                    multiplier *= 3.0
        else:
            games, shutouts, red_hots, previous_actual, sum_actuals, multiplier = 0, 0, 0, 0.0, 0.0, 750000.0
            for idx, bucket in enumerate(results):               
                if bucket:            
                    full_buckets += 1
                    shutouts = sum([val for val in bucket if val])                    
                    games = len(bucket)
                    actual = shutouts / games
                    if actual == 1.0 and idx == 6:     
                        red_hots = shutouts                    
                        red_hot_points = (red_hots + sum_actuals) * 30000000.0                   
                    else:                    
                        if actual == 0.0 and idx == 0:
                            dead_cold_points = games * 300000.0 * sum_actuals
                        else:
                            if idx == 1:
                                bonus_points += 0                            
                            else:
                                if idx < 6:                            
                                    bonus_points += ((actual - previous_actual) * multiplier) + (shutouts * 100)
                                    sum_actuals += (actual - previous_actual)
                    previous_actual = actual                            
                    if idx == 6 and red_hot_points == 0:
                        red_hot_points = 10000000.0 * actual
                if idx > 0:
                    multiplier *= 3.0        
    if full_buckets > 6:
        if (red_hot_points) >= 30000000:        
            bonus_points += (dead_cold_points + red_hot_points + (15000000.0 * (hots ** ratio_bonus) * ratio_bonus))          
            total_unexvar -= bonus_points                   
            penalty = sum(sho_vals) - ((sum(nsho_vals) / len(nsho_vals)) * len(sho_vals))
            penalty = ((max_nsho_val * len(sho_vals)) - penalty) / max_nsho_val
            penalty_points = 60000 * (penalty / lin_bonus)
            total_unexvar += penalty_points
        else:
            bonus_points = red_hot_points
            total_unexvar -= bonus_points  
            total_unexvar += penalty_points
        if (MOST_RED_HOTS < red_hots) and (total_unexvar > BEST_RESULT):
            base_solver.debug_print("-" * 20, debug, run_id)        
            base_solver.debug_print("-" * 20, debug, run_id)        
            base_solver.debug_print("{} red hot solution rejected for fewer points, linearity = {}, penalty = {}; best has {} red hots".format(red_hots, lin_bonus, penalty, MOST_RED_HOTS), debug, run_id)    
            base_solver.debug_print("-" * 20, debug, run_id)        
            base_solver.debug_print("-" * 20, debug, run_id)        
        else:
            if (red_hots < MOST_RED_HOTS) and (total_unexvar < BEST_RESULT):                
                base_solver.debug_print("-" * 20, debug, run_id)        
                base_solver.debug_print("-" * 20, debug, run_id)        
                base_solver.debug_print("{} red hot solution accepted for more points; previous high was {} red hots".format(red_hots, MOST_RED_HOTS), debug, run_id)    
                base_solver.debug_print("-" * 20, debug, run_id)        
                base_solver.debug_print("-" * 20, debug, run_id)        
    base_solver.debug_print("total unexvar {}".format(total_unexvar), debug2, run_id)        
    if total_unexvar < BEST_RESULT:
        BEST_RESULT = total_unexvar 
        MIN_SHO = min_sho_val
        MAX_NSHO = max_nsho_val
        full_buckets, games, shutouts, prev_games, prev_shutouts, nextprev_games, nextprev_shutouts, previous_actual, previous_upper, sum_actuals, multiplier = 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 750000.0
        base_solver.debug_print("-" * 20, debug, run_id)
        for idx, bucket in enumerate(results):  
            points = 0.0
            if bucket:
                if static_bounds:
                    full_buckets += 1
                    shutouts = sum([val for val in bucket if val])                    
                    games = len(bucket)
                    if idx > 1:    
                        if (mean_nshos[idx - 1] > 0):
                            bucket_bonus = (mean_shos[idx - 1] - mean_nshos[idx - 1]) / (max_nsho_val - min_sho_val)
                        else:
                            bucket_bonus = 0
                        if idx == 2:
                            actual = ((prev_shutouts + shutouts) / (prev_games + games))    
                        else:
                            if idx == 6:
                                actual = ((prev_shutouts + nextprev_shutouts) / (prev_games + nextprev_games))    
                            else:
                                actual = ((prev_shutouts + nextprev_shutouts + shutouts) / (prev_games + nextprev_games + games))                            
                        if actual > previous_actual:
                            points = (actual + (actual - previous_actual) + bucket_bonus) * multiplier                        
                        # should print the previous bucket bounds with the actual points for this bucket
                        base_solver.debug_print("bucket {:.4f}-{:.4f} :: broad actual {:.4f}, bucket bonus {:.4f}, points {}".format(lower_target, upper_target, actual, bucket_bonus, points), debug, ":::::")                                       
                        # base_solver.debug_print("min sho = {:.4f}, min nsho = {:.4f}".format(min_shos[idx - 1], min_nshos[idx - 1]), debug, ":::::")                        
                        # base_solver.debug_print("mean sho = {:.4f}, mean nsho = {:.4f}".format(mean_shos[idx - 1], mean_nshos[idx - 1]), debug, ":::::")
                        # base_solver.debug_print("max sho = {:.4f}, max nsho = {:.4f}".format(max_shos[idx - 1], max_nshos[idx - 1]), debug, ":::::")                                                            
                        base_solver.debug_print("{} shutouts in {} games".format(prev_shutouts, prev_games), debug, ":::::")                                                            
                        previous_actual = actual
                    if idx == 6:     
                        actual = shutouts / games                    
                        if actual == 1.0:
                            red_hots = shutouts                    
                            points = red_hots * 30000000.0
                        else:
                            points = 30000000.0 * actual
                        previous_actual = actual
                    else:                    
                        if idx == 0:
                            actual = shutouts / games                    
                            if actual == 0.0:
                                points = games * 300000.0
                            previous_actual = actual
                    nextprev_games = prev_games
                    prev_games = games       
                    nextprev_shutouts = prev_shutouts
                    prev_shutouts = shutouts                          
                else:
                    full_buckets += 1
                    shutouts = sum([val for val in bucket if val])                    
                    games = len(bucket)
                    actual = shutouts / games
                    if actual == 1.0 and idx == 6:     
                        red_hots = shutouts                    
                        points = (red_hots + bonus_multiplier + sum_actuals) * 30000000.0                   
                    else:                    
                        if actual == 0.0 and idx == 0:
                            points = games * 300000.0 * sum_actuals
                        else:
                            if idx == 1:
                                points = 0                            
                            else:
                                if idx < 6:                            
                                    points = (actual - previous_actual) * multiplier
                                    sum_actuals += (actual - previous_actual)
                    previous_actual = actual  
            # set up bucket for printing        
            lower_target = previous_upper            
            if idx == 6:
                upper_target = 1.0                
            else:                
                if idx == 0:
                    upper_target = min_sho_val                    
                else:
                    upper_target = lower_target + (bucket_bounds[idx - 1] * (max_nsho_val - min_sho_val))
            previous_upper = upper_target                   
            # only print immediately afterward if we're not in the static bounds mode
            if static_bounds:
                # also print immediately if we're dead cold or red hot
                if (idx == 6) or (idx == 0):
                    base_solver.debug_print("bucket {:.4f}-{:.4f} :: actual {}, points {}".format(lower_target, upper_target, actual, points), debug, ":::::")                                       
                    base_solver.debug_print("{} shutouts in {} games".format(sum([val for val in bucket if val]), len(bucket)), debug, ":::::")
                if (idx > 1):                
                    multiplier *= 3.0
            else:
                base_solver.debug_print("bucket {:.4f}-{:.4f} :: actual {}, points {}".format(lower_target, upper_target, actual, points), debug, ":::::")                                       
                base_solver.debug_print("{} shutouts in {} games".format(sum([val for val in bucket if val]), len(bucket)), debug, ":::::")
                if idx > 0:
                    multiplier *= 3.0                                                  
        base_solver.debug_print("# full buckets = {}, bonus points = {:.2f}, penalty = {:.2f}, iteration # {}".format(full_buckets, bonus_points, penalty, CURRENT_ITERATION), debug, ":::::")            
        base_solver.debug_print("Best Result so far - {}, {} red hots, linearity bonus = {:.4f}, {} hots at = {:.4f}".format(BEST_RESULT, red_hots, lin_bonus, hots, ratio_bonus), debug, ":::::")
        if red_hots >= MOST_RED_HOTS:            
            if type(stlat_list) == dict:
                mods_output = "\n".join("{},{},{},{},{},{}".format(stat.attr, stat.team, stat.stat, a, b, c) for stat, (a, b, c) in zip(mod_list, zip(*[iter(coefficients)] * 3)))
                base_solver.debug_print("-" * 20 + "\n" + mods_output, debug, run_id)
            else:
                terms_output = "\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(coefficients)] * 3)))
                base_solver.debug_print("-" * 20 + "\n" + terms_output, debug, run_id)
        base_solver.debug_print("-" * 20, debug, run_id)        
        MOST_RED_HOTS = red_hots
    endtime = datetime.datetime.now()
    base_solver.debug_print("func end: {}, run time {}".format(endtime, endtime-starttime), debug3, run_id)    
    if (CURRENT_ITERATION % 100 == 0):
        base_solver.debug_print("Best so far - {}, iteration # {}, {} red hots".format(BEST_RESULT, CURRENT_ITERATION, MOST_RED_HOTS), debug, datetime.datetime.now())
    CURRENT_ITERATION += 1    
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
    global MIN_SHO_VAL
    global MAX_NSHO_VAL
    cmd_args = handle_args()
    bounds = [[0, 9], [0, 3], [-6, 6]] * len(TIM_STLAT_LIST)
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    game_list = base_solver.get_games(cmd_args.gamefile)
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    args = (TIM_STLAT_LIST, None, stat_file_map, game_list, team_attrs, cmd_args.debug,
            cmd_args.debug2, cmd_args.debug3)
    # nlc = NonlinearConstraint(constr_f, 1.0, 1.0)
    result = differential_evolution(minimize_func, bounds, args=args, popsize=20, tol=0.0001,
                                    mutation=(0.3, 1.5), recombination=0.5, workers=4, maxiter=1000)
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(TIM_STLAT_LIST,
                                                                                   zip(*[iter(result.x)] * 3))))
    # now we want to take our stlat coefficients list and optimize the bounds for the best result
    coefficients = result.x
    bounds = [[0.00001, 0.99990]] * 5
    args = (coefficients, TIM_STLAT_LIST, None, stat_file_map, game_list, team_attrs, cmd_args.debug,
            cmd_args.debug2, cmd_args.debug3)
    nlc = NonlinearConstraint(constr_fn, 1.0, 1.0)
    start_second_stage = input("Press enter to start optimizing the bounds")
    result = differential_evolution(minimize_func, bounds, args=args, popsize=20, tol=0.0001,
                                    mutation=(0.3, 1.5), recombination=0.5, workers=4, constraints=(nlc), maxiter=1000)
    #now that we have our solution
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(TIM_STLAT_LIST,
                                                                                   zip(*[iter(coefficients)] * 3))))
    bucket_bounds = result.x
    start_bucket, end_bucket = 0.00, MIN_SHO
    print("\n {} - {}".format(start_bucket, end_bucket))
    for idx, interval in enumerate(bucket_bounds):
        start_bucket = end_bucket
        end_bucket = start_bucket + (bucket_bounds[idx] * (MAX_NSHO - MIN_SHO))                        
        print("\n {} - {}".format(start_bucket, end_bucket))
    start_bucket, end_bucket = MAX_NSHO, 1.00
    print("\n {} - {}".format(start_bucket, end_bucket))
    # result_fail_rate = minimize_func(result.x[:-5], TIM_STLAT_LIST, None, stat_file_map,
    #                                             game_list, team_attrs, False, False, False)
    # print("Result fail rate: {:.2f}%".format(result_fail_rate * 100.0))
    print(datetime.datetime.now())


if __name__ == "__main__":
    main()
