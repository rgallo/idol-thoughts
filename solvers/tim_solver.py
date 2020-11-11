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


def floor_to_five(val):
    return math.floor(val / .05) * .05


def get_bucket_idx(val):
    return int(floor_to_five(val) * 20)


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
    results = [[] for _ in range(21)]
    tim_tier = tim.TIM("asdf", terms, None, None, None)
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
                    away_bucket_idx = get_bucket_idx(awayTIM)
                    results[away_bucket_idx].append(awayShutout)
                if homeTIM >= 0:
                    home_bucket_idx = get_bucket_idx(homeTIM)
                    results[home_bucket_idx].append(homeShutout)
        season_end = datetime.datetime.now()
        base_solver.debug_print("season {} end: {}, run time {}, average day run {}".format(season, season_end, season_end-season_start, (season_end-season_start)/season_days), debug3, run_id)
    total_unexvar = 0.0
    empty_buckets, max_unexvar = 0, 0.0
    for idx, bucket in enumerate(results):
        if bucket:
            lower_target = (idx * 5.0) / 100.0
            upper_target = lower_target + .05
            actual = sum([val for val in bucket if val]) / len(bucket)
            if not lower_target <= actual < upper_target:
                target = upper_target if actual > upper_target else lower_target
                unexvar = ((abs(target - actual) - target)*100) ** 2
            else:
                unexvar = 0.0
            max_unexvar = max(max_unexvar, unexvar)
            base_solver.debug_print("bucket {:.2f}-{:.2f}: actual {}, unexvar {}".format(lower_target, upper_target, actual, unexvar), debug3, run_id)
            total_unexvar += unexvar
        else:
            empty_buckets += 1
    total_unexvar += ((max_unexvar + 2500) * empty_buckets)
    base_solver.debug_print("total unexvar {}".format(total_unexvar), debug2, run_id)
    if total_unexvar < BEST_RESULT:
        BEST_RESULT = total_unexvar
        base_solver.debug_print("-"*20, debug, run_id)
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
    bounds = [[0, 9], [0, 3], [-6, 2]] * len(TIM_STLAT_LIST)
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    game_list = base_solver.get_games(cmd_args.gamefile)
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    args = (TIM_STLAT_LIST, None, stat_file_map, game_list, team_attrs, cmd_args.debug,
            cmd_args.debug2, cmd_args.debug3)
    result = differential_evolution(minimize_func, bounds, args=args, popsize=15, tol=0.001,
                                    mutation=(0.05, 0.1), workers=1, maxiter=1)
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(TIM_STLAT_LIST,
                                                                                   zip(*[iter(result.x)] * 3))))
    result_fail_rate = minimize_func(result.x, TIM_STLAT_LIST, None, None, stat_file_map,
                                                 game_list, team_attrs, False, False, False)
    print("Result fail rate: {:.2f}%".format(result_fail_rate * 100.0))
    print(datetime.datetime.now())


if __name__ == "__main__":
    main()
