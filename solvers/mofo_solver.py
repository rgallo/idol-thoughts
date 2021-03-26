import argparse
import json
from scipy.optimize import differential_evolution
from solvers.mofo_ballpark_terms import BALLPARK_TERMS
import datetime
import sys

sys.path.append("..")
from solvers import base_solver
from mofo import get_mofo


MOFO_STLAT_LIST = ("meantragicness", "meanpatheticism", "meanthwackability", "meandivinity", "meanmoxie",
                   "meanmusclitude", "meanmartyrdom", "maxthwackability", "maxdivinity", "maxmoxie", "maxmusclitude",
                   "maxmartyrdom", "meanlaserlikeness", "meanbasethirst", "meancontinuation", "meangroundfriction",
                   "meanindulgence", "maxlaserlikeness", "maxbasethirst", "maxcontinuation", "maxgroundfriction",
                   "maxindulgence", "unthwackability", "ruthlessness", "overpowerment", "shakespearianism", "coldness",
                   "meanomniscience", "meantenaciousness", "meanwatchfulness", "meananticapitalism", "meanchasiness",
                   "maxomniscience", "maxtenaciousness", "maxwatchfulness", "maxanticapitalism", "maxchasiness")


def get_mofo_results(game, season_team_attrs, team_stat_data, pitcher_stat_data, pitchers, terms, special_cases, mods):
    awayMods, homeMods = [], []
    game_attrs = base_solver.get_attrs_from_paired_game(season_team_attrs, game)
    special_game_attrs = (game_attrs["home"].union(game_attrs["away"])) - base_solver.ALLOWED_IN_BASE
    if special_game_attrs:
        return 0, 0, 0, 0
    away_game, home_game = game["away"], game["home"]
    home_rbi, away_rbi = float(away_game["opposing_team_rbi"]), float(home_game["opposing_team_rbi"])
    if away_rbi == home_rbi:
        return 0, 0, 0, 0
    awayPitcher, awayTeam = pitchers.get(away_game["pitcher_id"])
    homePitcher, homeTeam = pitchers.get(home_game["pitcher_id"])
    awayodds, _ = get_mofo(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, terms,
                           awayMods, homeMods)
    homeodds = 1.0 - awayodds
    if awayodds == .5:
        return 0, 0, awayodds, homeodds
    fail = 1 if ((awayodds < .5 and away_rbi > home_rbi) or (awayodds > .5 and away_rbi < home_rbi)) else 0
    return 1, fail, awayodds, homeodds


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
    bounds = [(-2, 8), (0, 3), (-2, 4)] * len(MOFO_STLAT_LIST) + [(-8, 8), (0, 3), (-2, 4)] * len(BALLPARK_TERMS)
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    game_list = base_solver.get_games(cmd_args.gamefile)
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    args = (get_mofo_results, MOFO_STLAT_LIST, None, None, BALLPARK_TERMS, stat_file_map, game_list, team_attrs, cmd_args.debug,
            cmd_args.debug2, cmd_args.debug3)
    result = differential_evolution(base_solver.minimize_func, bounds, args=args, popsize=15, tol=0.0001,
                                    mutation=(0.05, 1.99), recombination=0.7, workers=1, maxiter=500)
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(MOFO_STLAT_LIST,
                                                                                   zip(*[iter(result.x)] * 3))))
    result_fail_rate = base_solver.minimize_func(result.x, get_mofo_results, MOFO_STLAT_LIST, None, None, stat_file_map,
                                                 game_list, team_attrs, False, False, False)
    print("Result fail rate: {:.2f}%".format(result_fail_rate*100.0))
    print(datetime.datetime.now())


if __name__ == "__main__":
    main()
