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

BEST_RESULT = 1000000000.0

ALLOWED_IN_BASE = {"AFFINITY_FOR_CROWS", "GROWTH", "TRAVELING"}
FORCE_REGEN = {"AFFINITY_FOR_CROWS", "GROWTH", "TRAVELING"}

BIRD_WEATHER = get_weather_idx("Birds")

TIM_STLAT_LIST = tim.TIM.OFFENSE_TERMS + tim.TIM.DEFENSE_TERMS

SHUTOUT_PCT = None
CURRENT_ITERATION = 1
MOST_RED_HOTS = 1

def get_bucket_idx(val, bucket_bounds):
    start_bucket, end_bucket = 0.00, 0.00    
    for idx, interval in enumerate(bucket_bounds):
        start_bucket = end_bucket
        end_bucket = min(((start_bucket + bucket_bounds[idx]) if (idx < 19) else 1.0), 1.0)
        if end_bucket >= val >= start_bucket:
            return idx            
    return -1


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
    bucket_bounds = parameters[-20:]
    coefficients = parameters[:-20]
    global BEST_RESULT
    global SHUTOUT_PCT
    global CURRENT_ITERATION
    global MOST_RED_HOTS
    stlat_list, mod_list, stat_file_map, game_list, team_attrs, debug, debug2, debug3 = data
    base_solver.debug_print("func start: {}".format(starttime), debug3, run_id)
    if type(stlat_list) == dict:  # mod mode
        terms = stlat_list
        mods = collections.defaultdict(lambda: {"opp": {}, "same": {}})
        for mod, (a, b, c) in zip(mod_list, zip(*[iter(coefficients)] * 3)):
            mods[mod.attr.lower()][mod.team.lower()][mod.stat.lower()] = StlatTerm(a, b, c)
    else:  # base mode
        terms = {stat: StlatTerm(a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(coefficients)] * 3))}
        mods = {}
    results = [[] for _ in range(20)]
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
                    away_bucket_idx = get_bucket_idx(awayTIM, bucket_bounds)
                    results[away_bucket_idx].append(awayShutout)
                    min_sho_val = awayTIM if awayTIM < min_sho_val and awayShutout else min_sho_val
                    max_sho_val = awayTIM if awayTIM > max_sho_val and awayShutout else max_sho_val
                    min_nsho_val = awayTIM if awayTIM < min_nsho_val and not awayShutout else min_nsho_val
                    max_nsho_val = awayTIM if awayTIM > max_nsho_val and not awayShutout else max_nsho_val
                if homeTIM >= 0:
                    home_bucket_idx = get_bucket_idx(homeTIM, bucket_bounds)
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
    # going to move to subtracting things we like to see from a big number RATHER than "erroring" with big number in multiple cases.
    total_unexvar = 1000000000.0   
    bonus_points = 0.0
    if (max_sho_val > max_nsho_val) and (min_sho_val > min_nsho_val) and (get_bucket_idx(max_sho_val, bucket_bounds) > 5):        
        full_buckets, previous_actual, previous_upper = 0, 0.0, 0.0
        for idx, bucket in enumerate(results):        
            lower_target = previous_upper
            upper_target = lower_target + bucket_bounds[idx]                        
            previous_upper = upper_target            
            if bucket:            
                full_buckets += 1
                actual = sum([val for val in bucket if val]) / len(bucket)            
                if previous_actual > actual:                    
                    bonus_points = 0.0
                    break
                base_solver.debug_print("bucket {:.2f}-{:.2f}: actual {}, points {}".format(lower_target, upper_target, actual, bonus_points), debug3, run_id)                
                # red hot SHO are the most valuable to the solution
                # non-red hots are worth something PROVIDED they are better than the best shutout percentage
                # each non-red-hot % worth anything is a % of a red hot equal to the difference between its success rate and the next-highest
                if actual == 1.0:
                    bonus_points += sum([val for val in bucket if val]) * 10000000.0
                else:
                    if previous_actual < actual and actual > SHUTOUT_PCT:                    
                        bonus_points += sum([val for val in bucket if val]) * (10000000.0 ** min((actual + (actual - previous_actual)), 0.75))                                    
                # 100 dead colds are worth 1 red hot
                if actual == 0.0 and previous_actual == 0.0:
                    bonus_points += len(bucket) * 10000.0
                previous_actual = actual                    
        # we want at least 7 different "temperatures" still to provide adequate granularity in our choices
        if full_buckets < 7:
            bonus_points = 0.0
    total_unexvar -= bonus_points
    base_solver.debug_print("total unexvar {}".format(total_unexvar), debug2, run_id)
    if (CURRENT_ITERATION % 100 == 0):
        base_solver.debug_print("iteration # {}".format(CURRENT_ITERATION), debug, datetime.datetime.now())
    if total_unexvar < BEST_RESULT:
        BEST_RESULT = total_unexvar 
        points, red_hots, full_buckets, previous_actual, previous_upper = 0, 0, 0, 0.0, 0.0
        base_solver.debug_print("-" * 20, debug, run_id)
        for idx, bucket in enumerate(results):        
            lower_target = previous_upper
            upper_target = lower_target + bucket_bounds[idx]                        
            previous_upper = upper_target            
            if bucket:
                full_buckets += 1
                actual = sum([val for val in bucket if val]) / len(bucket)            
                if previous_actual > actual:                    
                    points = 0.0                                
                # red hot SHO are the most valuable to the solution
                # non-red hots are worth something PROVIDED they are better than the best shutout percentage
                # each non-red-hot % worth anything is a % of a red hot equal to the difference between its success rate and the next-highest
                if actual == 1.0:
                    points = sum([val for val in bucket if val]) * 10000000.0
                    red_hots += sum([val for val in bucket if val])
                else:
                    if previous_actual < actual and actual > SHUTOUT_PCT:                    
                        points += sum([val for val in bucket if val]) * (10000000.0 ** min((actual + (actual - previous_actual)), 0.75))                                    
                # 100 dead colds are worth 1 red hot
                if actual == 0.0 and previous_actual == 0.0:
                    points = len(bucket) * 10000.0
                previous_actual = actual               
                base_solver.debug_print("bucket {:.2f}-{:.2f} :: actual {}, points {}".format(lower_target, upper_target, actual, points), debug, ":::::")                                       
                base_solver.debug_print("{} shutouts in {} games".format(sum([val for val in bucket if val]), len(bucket)), debug, ":::::")                          
                points = 0.0
        base_solver.debug_print("# full buckets = {}, bonus points = {:.2f}, iteration # {}".format(full_buckets, bonus_points, CURRENT_ITERATION), debug, ":::::")    
        base_solver.debug_print("min sho = {:.4f}, min nsho = {:.4f}, max sho = {:.4f}, max nsho = {:.4f}".format(min_sho_val, min_nsho_val, max_sho_val, max_nsho_val), debug, ":::::")
        base_solver.debug_print("Best Result so far - {}".format(BEST_RESULT), debug, ":::::")
        if red_hots >= MOST_RED_HOTS:
            MOST_RED_HOTS = red_hots
            if type(stlat_list) == dict:
                mods_output = "\n".join("{},{},{},{},{},{}".format(stat.attr, stat.team, stat.stat, a, b, c) for stat, (a, b, c) in zip(mod_list, zip(*[iter(coefficients)] * 3)))
                base_solver.debug_print("-" * 20 + "\n" + mods_output, debug, run_id)
            else:
                terms_output = "\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(coefficients)] * 3)))
                base_solver.debug_print("-" * 20 + "\n" + terms_output, debug, run_id)
        base_solver.debug_print("-" * 20, debug, run_id)        
    endtime = datetime.datetime.now()
    base_solver.debug_print("func end: {}, run time {}".format(endtime, endtime-starttime), debug3, run_id)
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
    cmd_args = handle_args()
    bounds = [[0, 9], [0, 3], [-6, 6]] * len(TIM_STLAT_LIST) + ([[0.01, 0.2]] * 20)
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    game_list = base_solver.get_games(cmd_args.gamefile)
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    args = (TIM_STLAT_LIST, None, stat_file_map, game_list, team_attrs, cmd_args.debug,
            cmd_args.debug2, cmd_args.debug3)
    result = differential_evolution(minimize_func, bounds, args=args, popsize=15, tol=0.0001,
                                    mutation=(0.05, 0.1), workers=-1, maxiter=100)
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(TIM_STLAT_LIST,
                                                                                   zip(*[iter(result.x[:-20])] * 3))))
    bucket_bounds = result.x[-20:]
    start_bucket, end_bucket = 0.00, 0.00
    for idx, interval in enumerate(bucket_bounds):
        start_bucket = end_bucket
        end_bucket = min(((start_bucket + bucket_bounds[idx]) if (idx < 19) else 1.0), 1.0)
        print("\n {} - {}".format(start_bucket, end_bucket))    
    result_fail_rate = minimize_func(result.x[:-20], TIM_STLAT_LIST, None, stat_file_map,
                                                 game_list, team_attrs, False, False, False)
    print("Result fail rate: {:.2f}%".format(result_fail_rate * 100.0))
    print(datetime.datetime.now())


if __name__ == "__main__":
    main()
