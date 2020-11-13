import argparse
import collections
import csv
import datetime
import json
import math
import os
import re
import sys
import uuid
from glob import glob

from scipy.optimize import differential_evolution

sys.path.append("..")

from solvers import base_solver
from helpers import StlatTerm, get_weather_idx
from idolthoughts import load_stat_data, calc_stlat_stats
import tim

STAT_CACHE = {}
GAME_CACHE = {}

BEST_RESULT = 9999999999999999.0

ALLOWED_IN_BASE = {"AFFINITY_FOR_CROWS", "GROWTH", "TRAVELING"}
FORCE_REGEN = {"AFFINITY_FOR_CROWS", "GROWTH", "TRAVELING"}

BIRD_WEATHER = get_weather_idx("Birds")

TIM_STLAT_LIST = tim.TIM.OFFENSE_TERMS + tim.TIM.DEFENSE_TERMS

SHUTOUT_PCT = None


def floor_to_floor(val, floor):
    return math.floor(val / floor) * floor


def get_bucket_idx(val, floor):
    return int(floor_to_floor(val) * (1 / floor))


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
    floor = 0.05
    stlat_list, mod_list, stat_file_map, game_list, team_attrs, debug, debug2, debug3 = data
    base_solver.debug_print("func start: {}".format(starttime), debug3, run_id)
    if type(stlat_list) == dict:  # mod mode
        terms = stlat_list
        mods = collections.defaultdict(lambda: {"opp": {}, "same": {}})
        for mod, (a, b, c) in zip(mod_list, zip(*[iter(parameters)] * 3)):
            mods[mod.attr.lower()][mod.team.lower()][mod.stat.lower()] = StlatTerm(a, b, c)
    else:  # base mode
        terms = {stat: StlatTerm(a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(parameters)] * 3))}
        mods = {}
    results = [[] for _ in range(int(1 / floor) + 1)]
    tim_tier = tim.TIM("asdf", terms, None, None, None)
    min_sho_val, max_sho_val, min_nsho_val, max_nsho_val = 1.0, 0.0, 1.0, 0.0
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
                if awayTIM >= 0:
                    away_bucket_idx = get_bucket_idx(awayTIM, floor)
                    results[away_bucket_idx].append(awayShutout)
                    min_sho_val = awayTIM if awayTIM < min_sho_val and awayShutout else min_sho_val
                    max_sho_val = awayTIM if awayTIM > max_sho_val and awayShutout else max_sho_val
                    min_nsho_val = awayTIM if awayTIM < min_nsho_val and not awayShutout else min_nsho_val
                    max_nsho_val = awayTIM if awayTIM > max_nsho_val and not awayShutout else max_nsho_val
                if homeTIM >= 0:
                    home_bucket_idx = get_bucket_idx(homeTIM, floor)
                    results[home_bucket_idx].append(homeShutout)
                    min_sho_val = homeTIM if homeTIM < min_sho_val and homeShutout else min_sho_val
                    max_sho_val = homeTIM if homeTIM > max_sho_val and homeShutout else max_sho_val
                    min_nsho_val = homeTIM if homeTIM < min_nsho_val and not homeShutout else min_nsho_val
                    max_nsho_val = homeTIM if homeTIM > max_nsho_val and not homeShutout else max_nsho_val
        season_end = datetime.datetime.now()
        base_solver.debug_print("season {} end: {}, run time {}, average day run {}".format(season, season_end, season_end-season_start, (season_end-season_start)/season_days), debug3, run_id)
    if not SHUTOUT_PCT:
        total_games, total_shutouts = 0, 0
        for bucket in results:
            total_shutouts += sum([val for val in bucket if val])
            total_games += len(bucket)
        SHUTOUT_PCT = total_shutouts / total_games
    if (max_sho_val > max_nsho_val) and (min_sho_val > min_nsho_val):
        total_unexvar = 0.0
        full_buckets, total_sho_buckets, bonus_points, previous_actual, target_window, previous_upper = 0, 0, 0.0, 0.0, 0.0, 0.0        
        total_sho_buckets = get_bucket_idx(max_sho_val, floor) - get_bucket_idx(min_sho_val, floor) + 1
        for idx, bucket in enumerate(results):        
            lower_target = (idx * (floor * 100)) / 100.0
            upper_target = lower_target + floor
            lower_tim_target, upper_tim_target = 0.0, 0.0
            if lower_target < min_sho_val:
                lower_tim_target = 0.0               
            else:
                if lower_target > max_nsho_val:
                    lower_tim_target = 1.0
                else:
                    lower_tim_target = previous_upper                    
            if upper_target > max_nsho_val or lower_tim_target == 1.0:
                upper_tim_target = 1.0
            else:
                if upper_target < min_sho_val:
                    upper_tim_target = 0.0
                else:                                                     
                    upper_tim_target = min((lower_tim_target + (((max_nsho_val - min_sho_val) / (total_sho_buckets * (max_nsho_val - min_sho_val))))), 1.0)
            previous_upper = upper_tim_target
            target_window = max(upper_tim_target - lower_tim_target, target_window)
            if bucket:            
                full_buckets += 1
                actual = sum([val for val in bucket if val]) / len(bucket)            
                if previous_actual > actual:                    
                    unexvar = 9999999999999.0
                else:                    
                    if lower_tim_target <= actual <= upper_tim_target:
                        unexvar = 0.0            
                    else:
                        unexvar = ((actual - lower_tim_target if (actual < lower_tim_target) else upper_tim_target) * 100) ** 2
                base_solver.debug_print("bucket {:.2f}-{:.2f}: actual {}, unexvar {}".format(lower_target, upper_target, actual, unexvar), debug3, run_id)            
                total_unexvar += unexvar
                if actual == 1.0:
                    bonus_points += sum([val for val in bucket if val]) * 100
                else:
                    if previous_actual < actual and actual > SHUTOUT_PCT:                    
                        bonus_points += (sum([val for val in bucket if val]) * 10.0) * actual              
                if actual == 0.0:
                    bonus_points += len(bucket) if (upper_tim_target == 0.0) else -(sum([val for val in bucket if val]))
                previous_actual = actual            
        total_unexvar -= bonus_points
        if full_buckets < 7:
            total_unexvar = 9999999999999999.0
    else:
        total_unexvar = 9999999999999999.0
    base_solver.debug_print("total unexvar {}".format(total_unexvar), debug2, run_id)
    if total_unexvar < BEST_RESULT:
        BEST_RESULT = total_unexvar
        previous_actual, target_window, previous_upper = 0.0, 0.0 ,0.0
        base_solver.debug_print("-"*20, debug, run_id)
        for idx, bucket in enumerate(results):        
            lower_target = (idx * (floor * 100)) / 100.0
            upper_target = lower_target + floor
            lower_tim_target, upper_tim_target = 0.0, 0.0
            if lower_target < min_sho_val:
                lower_tim_target = 0.0               
            else:
                if lower_target > max_nsho_val:
                    lower_tim_target = 1.0
                else:
                    lower_tim_target = previous_upper                    
            if upper_target > max_nsho_val or lower_tim_target == 1.0:
                upper_tim_target = 1.0
            else:
                if upper_target < min_sho_val:
                    upper_tim_target = 0.0
                else:
                    # need to determine how many buckets we have to put sho into, knowing that one of them is going to be our only 100% case
                    # we do this by determining what our current bucket is the first time we come into this expression, then dividing our total range of sho by the number of remaining buckets                    
                    upper_tim_target = min((lower_tim_target + (((max_nsho_val - min_sho_val) / (total_sho_buckets * (max_nsho_val - min_sho_val))))), 1.0)
            previous_upper = upper_tim_target
            target_window = max(upper_tim_target - lower_tim_target, target_window)
            if bucket:            
                actual = sum([val for val in bucket if val]) / len(bucket)            
                if previous_actual > actual:                    
                    unexvar = 9999999999999.0
                else:                                 
                    if lower_tim_target <= actual <= upper_tim_target:
                        unexvar = 0.0            
                    else:
                        unexvar = ((actual - lower_tim_target if (actual < lower_tim_target) else upper_tim_target) * 100) ** 2                
                previous_actual = actual                            
                base_solver.debug_print("bucket {:.2f}-{:.2f} :: tim bucket {:.2f}-{:.2f} :: actual {}, unexvar {}".format(lower_target, upper_target, lower_tim_target, upper_tim_target, actual, unexvar), debug, ":::::")                                       
                base_solver.debug_print("{} shutouts in {} games".format(sum([val for val in bucket if val]), len(bucket)), debug, ":::::")                
        base_solver.debug_print("# full buckets = {}, total sho buckets = {}, bonus points = {:.2f}".format(full_buckets, total_sho_buckets, bonus_points), debug, run_id)    
        base_solver.debug_print("min sho = {:.4f}, min nsho = {:.4f}, max sho = {:.4f}, max nsho = {:.4f}".format(min_sho_val, min_nsho_val, max_sho_val, max_nsho_val), debug, run_id)
        if type(stlat_list) == dict:
            mods_output = "\n".join("{},{},{},{},{},{}".format(stat.attr, stat.team, stat.stat, a, b, c) for stat, (a, b, c) in zip(mod_list, zip(*[iter(parameters)] * 3)))
            base_solver.debug_print("Best so far - unexvar {}\n".format(total_unexvar) + mods_output, debug, run_id)
        else:
            terms_output = "\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(parameters)] * 3)))
            base_solver.debug_print("Best so far - unexvar {}\n".format(total_unexvar) + terms_output, debug, run_id)
        base_solver.debug_print("-" * 20, debug, run_id)        
    endtime = datetime.datetime.now()
    base_solver.debug_print("func end: {}, run time {}".format(endtime, endtime-starttime), debug3, run_id)
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
    cmd_args = handle_args()
    bounds = [[0, 9], [0, 3], [-6, 6]] * len(TIM_STLAT_LIST)
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    game_list = base_solver.get_games(cmd_args.gamefile)
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    args = (TIM_STLAT_LIST, None, stat_file_map, game_list, team_attrs, cmd_args.debug,
            cmd_args.debug2, cmd_args.debug3)
    result = differential_evolution(minimize_func, bounds, args=args, popsize=15, tol=0.0001,
                                    mutation=(0.05, 0.1), workers=-1, maxiter=100)
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(TIM_STLAT_LIST,
                                                                                   zip(*[iter(result.x)] * 3))))
    result_fail_rate = minimize_func(result.x, TIM_STLAT_LIST, None, None, stat_file_map,
                                                 game_list, team_attrs, False, False, False)
    print("Result fail rate: {:.2f}%".format(result_fail_rate * 100.0))
    print(datetime.datetime.now())


if __name__ == "__main__":
    main()
