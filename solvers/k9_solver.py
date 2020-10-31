import argparse
import json
from scipy.optimize import differential_evolution
import datetime
import sys

sys.path.append("..")
from solvers import base_solver
from k9 import get_k9


K9_STLAT_LIST = ("unthwackability", "ruthlessness", "overpowerment", "shakespearianism", "coldness", "meanomniscience",
                 "meantenaciousness", "meanwatchfulness", "meananticapitalism", "meanchasiness", "meantragicness",
                 "meanpatheticism", "meanthwackability", "meandivinity", "meanmoxie", "meanmusclitude", "meanmartyrdom",
                 "meanlaserlikeness", "meanbasethirst", "meancontinuation", "meangroundfriction", "meanindulgence",
                 "maxomniscience", "maxtenaciousness", "maxwatchfulness", "maxanticapitalism", "maxchasiness",
                 "maxthwackability", "maxdivinity", "maxmoxie", "maxmusclitude", "maxmartyrdom", "maxlaserlikeness",
                 "maxbasethirst", "maxcontinuation", "maxgroundfriction", "maxindulgence")

K9_SPECIAL_CASES = ("pitching", "everythingelse")


def get_k9_results(game, season_team_attrs, team_stat_data, pitcher_stat_data, pitchers, terms, special_cases, mods):
    game_attrs = base_solver.get_attrs_from_paired_game(season_team_attrs, game)
    special_game_attrs = (game_attrs["home"].union(game_attrs["away"])) - base_solver.ALLOWED_IN_BASE
    if special_game_attrs:
        return 0, 0
    away_game, home_game = game["away"], game["home"]
    awayPitcher, awayTeam = pitchers.get(away_game["pitcher_id"])
    homePitcher, homeTeam = pitchers.get(home_game["pitcher_id"])
    away_strikeouts, home_strikeouts = float(away_game["strikeouts"]), float(home_game["strikeouts"])
    away_innings, home_innings = float(away_game["innings_pitched"]), float(home_game["innings_pitched"])
    away_so9, home_so9 = (away_strikeouts / away_innings) * 9.0, (home_strikeouts / home_innings) * 9.0
    try:
        away_k9 = get_k9(awayPitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, terms, {"factors": special_cases})
    except ValueError:
        away_k9 = -100
    try:
        home_k9 = get_k9(awayPitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, terms, {"factors": special_cases})
    except ValueError:
        home_k9 = -100
    fail_k9 = 2
    if away_so9 - 1 < away_k9 < away_so9 + 1:
        fail_k9 -= 1
    if home_so9 - 1 < home_k9 < home_so9 + 1:
        fail_k9 -= 1
    return 2, fail_k9


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--statfolder', help="path to stat folder")
    parser.add_argument('--gamefile', help="path to game file")
    parser.add_argument('--debug', help="print output", action='store_true')
    parser.add_argument('--debug2', help="print output", action='store_true')
    parser.add_argument('--debug3', help="print output", action='store_true')
    args = parser.parse_args()
    return args


def main():
    print(datetime.datetime.now())
    cmd_args = handle_args()
    bounds = [[-3, 4]] * 3 * len(K9_STLAT_LIST) + [[-3, 4], [-2, 2]]
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    game_list = base_solver.get_games(cmd_args.gamefile)
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    args = (get_k9_results, K9_STLAT_LIST, K9_SPECIAL_CASES, [], stat_file_map, game_list, team_attrs,
            cmd_args.debug, cmd_args.debug2, cmd_args.debug3)
    result = differential_evolution(base_solver.minimize_func, bounds, args=args, popsize=15, tol=0.001,
                                    mutation=(0.05, 0.1), workers=1, maxiter=1)
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in
                    zip(K9_STLAT_LIST, zip(*[iter(result.x[:-len(K9_SPECIAL_CASES)])] * 3))))
    print("factors,{},{}".format(result.x[-2], result.x[-1]))
    result_fail_rate = base_solver.minimize_func(result.x, get_k9_results, K9_STLAT_LIST, K9_SPECIAL_CASES,
                                                 [], stat_file_map, game_list, team_attrs,
                                                 False, False, False)
    print("Result fail rate: {:.2f}%".format(result_fail_rate*100.0))
    print(datetime.datetime.now())


if __name__ == "__main__":
    main()
