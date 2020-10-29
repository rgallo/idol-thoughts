import argparse
import collections
import csv
import json
import os
import re
from glob import glob
import sys
from scipy.optimize import differential_evolution
import datetime

sys.path.append("..")
from mofo import get_mofo
from helpers import StlatTerm, get_weather_idx
from idolthoughts import load_stat_data


STLAT_LIST = ("meantragicness", "meanpatheticism", "meanthwackability", "meandivinity", "meanmoxie", "meanmusclitude",
              "meanmartyrdom", "maxthwackability", "maxdivinity", "maxmoxie", "maxmusclitude", "maxmartyrdom",
              "meanlaserlikeness", "meanbasethirst", "meancontinuation", "meangroundfriction", "meanindulgence",
              "maxlaserlikeness", "maxbasethirst", "maxcontinuation", "maxgroundfriction", "maxindulgence",
              "unthwackability", "ruthlessness", "overpowerment", "shakespearianism", "coldness", "meanomniscience",
              "meantenaciousness", "meanwatchfulness", "meananticapitalism", "meanchasiness", "maxomniscience",
              "maxtenaciousness", "maxwatchfulness", "maxanticapitalism", "maxchasiness")

ALLOWED_IN_BASE = {"AFFINITY_FOR_CROWS", "GROWTH", "TRAVELING"}
FORCE_REGEN = {"AFFINITY_FOR_CROWS", "GROWTH", "TRAVELING"}

BEST_RESULT = 1.0

BIRD_WEATHER = get_weather_idx("Birds")


def get_pitcher_id_lookup(filename):
    with open(filename) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    return {row["id"]: (row["name"], row["team"]) for row in filedata if row["position"] == "rotation"}


def get_games(filename):
    with open(filename) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    return filedata


def pair_games(games):
    gamelist = collections.defaultdict(lambda: [])
    for game in games:
        gamelist[game["game_id"]].append(game)
    results = []
    for game_id, games in gamelist.items():
        if len(games) == 2 and games[0]["pitcher_is_home"] != games[1]["pitcher_is_home"]:
            results.append({("home" if game["pitcher_is_home"] == "True" else "away"): game for game in games})
    return results


def get_stat_file_map(stat_folder):
    filelist = [y for x in os.walk(stat_folder) for y in glob(os.path.join(x[0], '*.csv'))]
    results = {}
    for filepath in filelist:
        filename = filepath.split(os.sep)[-1]
        match = re.match(r'outputS([0-9]*)preD([0-9]*).csv', filename)
        if match:
            season, day = match.groups()
            results[(int(season), int(day))] = filepath
    return results


def get_schedule_from_paired_games(paired_games):
    return [{
        "homeTeamName": game["home"]["team_name"],
        "awayTeamName": game["away"]["team_name"],
        "weather": int(game["home"]["weather"]),
    } for game in paired_games]


def should_regen(day_mods):
    return any([d in day_mods for d in FORCE_REGEN])


def get_attrs_from_paired_game(season_team_attrs, games):
    attrs = set()
    for side in ("home", "away"):
        game = games[side]
        team_attrs = season_team_attrs.get(game.get("team_name"), [])
        for attr in team_attrs:
            if (attr == "TRAVELING" and side != "away") or (attr == "AFFINITY_FOR_CROWS" and int(game["weather"]) != BIRD_WEATHER):
                continue
            attrs.add(attr)
    return attrs


def get_attrs_from_paired_games(season_team_attrs, paired_games):
    attrs = set()
    for games in paired_games:
        attrs.update(get_attrs_from_paired_game(season_team_attrs, games))
    return attrs


def func(parameters, *data):
    print("func start: {}".format(datetime.datetime.now()))
    global BEST_RESULT
    stat_file_map, game_list, team_attrs, mod, debug = data
    terms = {stat: StlatTerm(a, b, c) for stat, (a, b, c) in zip(STLAT_LIST, zip(*[iter(parameters)] * 3))}
    game_counter, fail_counter = 0, 0
    for season in range(3, 12):
        pitchers, team_stat_data, pitcher_stat_data, last_stat_filename = None, None, None, None
        season_team_attrs = team_attrs.get(str(season), {})
        for day in range(1, 125):
            games = [row for row in game_list if row["season"] == str(season) and row["day"] == str(day)]
            if not games:
                continue
            paired_games = pair_games(games)
            schedule = get_schedule_from_paired_games(paired_games)
            day_mods = get_attrs_from_paired_games(season_team_attrs, paired_games)
            stat_filename = stat_file_map.get((season, day))
            if stat_filename:
                last_stat_filename = stat_filename
                pitchers = get_pitcher_id_lookup(stat_filename)
                team_stat_data, pitcher_stat_data = load_stat_data(stat_filename, schedule, day, season_team_attrs)
            elif should_regen(day_mods):
                pitchers = get_pitcher_id_lookup(last_stat_filename)
                team_stat_data, pitcher_stat_data = load_stat_data(last_stat_filename, schedule, day, season_team_attrs)
            if not pitchers:
                raise Exception("No stat file found")
            awayMods, homeMods = [], []
            for game in paired_games:
                game_attrs = get_attrs_from_paired_game(season_team_attrs, game)
                special_game_attrs = game_attrs - ALLOWED_IN_BASE
                if not mod and special_game_attrs:
                    continue
                if mod and (len(special_game_attrs) > 1 or special_game_attrs.pop() != mod):
                    continue
                away_game, home_game = game["away"], game["home"]
                away_rbi, home_rbi = float(away_game["pitcher_team_rbi"]), float(home_game["pitcher_team_rbi"])
                if away_rbi == home_rbi:
                    continue
                awayPitcher, awayTeam = pitchers.get(away_game["pitcher_id"])
                homePitcher, homeTeam = pitchers.get(home_game["pitcher_id"])
                awayodds, _ = get_mofo(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data,
                                       terms, awayMods, homeMods)
                if awayodds == .5:
                    continue
                game_counter += 1
                if (awayodds < .5 and away_rbi > home_rbi) or (awayodds > .5 and away_rbi < home_rbi):
                    fail_counter += 1
    fail_rate = fail_counter / game_counter
    if debug:
        if fail_rate < BEST_RESULT:
            BEST_RESULT = fail_rate
            print("-"*20)
            print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(STLAT_LIST, zip(*[iter(parameters)] * 3))))
            print("Best so far - fail rate {:.2f}%".format(fail_rate * 100.0))
            print("-" * 20)
        print("- fail rate {:.2f}%".format(fail_rate * 100.0))
    print("func end: {}".format(datetime.datetime.now()))
    return fail_rate


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--statfolder', help="path to stat folder")
    parser.add_argument('--gamefile', help="path to game file")
    parser.add_argument('--mod', help="mod to calculate for")
    parser.add_argument('--debug', help="print output", action='store_true')
    args = parser.parse_args()
    return args


def main():
    print(datetime.datetime.now())
    cmd_args = handle_args()
    bounds = [(0, 10), (0, 3), (-3, 3)] * len(STLAT_LIST)
    stat_file_map = get_stat_file_map(cmd_args.statfolder)
    game_list = get_games(cmd_args.gamefile)
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    args = (stat_file_map, game_list, team_attrs, cmd_args.mod, cmd_args.debug)
    result = differential_evolution(func, bounds, args=args, popsize=15, tol=0.001, mutation=0.075, workers=1, maxiter=1)
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(STLAT_LIST,
                                                                                   zip(*[iter(result.x)] * 3))))
    result_fail_rate = func(result.x, stat_file_map, game_list, team_attrs, cmd_args.mod, False)
    print("Result fail rate: {:.2f}%".format(result_fail_rate*100.0))
    print(datetime.datetime.now())


if __name__ == "__main__":
    main()
