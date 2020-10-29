import argparse
import collections
import csv
import os
import re
from glob import glob
import sys
from scipy.optimize import differential_evolution

sys.path.append("..")
from mofo import get_mofo
from helpers import StlatTerm
from idolthoughts import load_stat_data


STLAT_LIST = ("meantragicness", "meanpatheticism", "meanthwackability", "meandivinity", "meanmoxie", "meanmusclitude",
              "meanmartyrdom", "maxthwackability", "maxdivinity", "maxmoxie", "maxmusclitude", "maxmartyrdom",
              "meanlaserlikeness", "meanbasethirst", "meancontinuation", "meangroundfriction", "meanindulgence",
              "maxlaserlikeness", "maxbasethirst", "maxcontinuation", "maxgroundfriction", "maxindulgence",
              "unthwackability", "ruthlessness", "overpowerment", "shakespearianism", "coldness", "meanomniscience",
              "meantenaciousness", "meanwatchfulness", "meananticapitalism", "meanchasiness", "maxomniscience",
              "maxtenaciousness", "maxwatchfulness", "maxanticapitalism", "maxchasiness")


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


BEST_RESULT = 1.0


def func(parameters, *data):
    global BEST_RESULT
    stat_file_map, game_list, debug = data
    terms = {stat: StlatTerm(a, b, c) for stat, (a, b, c) in zip(STLAT_LIST, zip(*[iter(parameters)] * 3))}
    game_counter, fail_counter = 0, 0
    for season in (5,):
        pitchers, team_stat_data, pitcher_stat_data = None, None, None
        for day in range(1, 125):
            stat_filename = stat_file_map.get((season, day))
            if stat_filename:
                pitchers = get_pitcher_id_lookup(stat_filename)
                team_stat_data, pitcher_stat_data = load_stat_data(stat_filename)
            if not pitchers:
                raise Exception("No stat file found")
            awayMods, homeMods = [], []
            games = [row for row in game_list if row["season"] == str(season) and row["day"] == str(day)]
            paired_games = pair_games(games)
            for game in paired_games:
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
    return fail_rate


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--statfolder', help="path to stat folder")
    parser.add_argument('--gamefile', help="path to game file")
    parser.add_argument('--debug', help="print output", action='store_true')
    args = parser.parse_args()
    return args


def main():
    import datetime
    print(datetime.datetime.now())
    args = handle_args()
    bounds = [(0, 10), (0, 3), (-3, 3)] * len(STLAT_LIST)
    stat_file_map = get_stat_file_map(args.statfolder)
    game_list = get_games(args.gamefile)
    args = (stat_file_map, game_list, args.debug)
    result = differential_evolution(func, bounds, args=args, popsize=15, tol=0.001, mutation=0.075, workers=1, maxiter=1)
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(STLAT_LIST,
                                                                                   zip(*[iter(result.x)] * 3))))
    result_fail_rate = func(result.x, stat_file_map, game_list, False)
    print("Result fail rate: {:.2f}%".format(result_fail_rate*100.0))
    print(datetime.datetime.now())


if __name__ == "__main__":
    main()
