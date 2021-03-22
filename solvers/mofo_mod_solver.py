import argparse
import json
from scipy.optimize import differential_evolution
import datetime
import sys

sys.path.append("..")

from helpers import parse_terms

from solvers import base_solver
import mofo
from solvers.mofo_mod_terms import MOFO_MOD_TERMS


def get_mofo_mod_results(game, season_team_attrs, team_stat_data, pitcher_stat_data, pitchers, terms, special_cases, mods):
    game_attrs = base_solver.get_attrs_from_paired_game(season_team_attrs, game)
    special_game_attrs = (game_attrs["home"].union(game_attrs["away"])) - base_solver.ALLOWED_IN_BASE
    if not special_game_attrs:
        return 0, 0, 0, 0
    away_game, home_game = game["away"], game["home"]
    home_rbi, away_rbi = float(away_game["opposing_team_rbi"]), float(home_game["opposing_team_rbi"])
    if away_rbi == home_rbi:
        return 0, 0, 0, 0
    awayPitcher, awayTeam = pitchers.get(away_game["pitcher_id"])
    homePitcher, homeTeam = pitchers.get(home_game["pitcher_id"])
    awayMods, homeMods = mofo.get_mods(mods, game_attrs["away"], game_attrs["home"], away_game["weather"])
    awayodds, _ = mofo.get_mofo(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, terms,
                                awayMods, homeMods)
    homeodds = 1.0 - awayodds
    if awayodds == .5:
        return 0, 0, awayodds, homeodds
    return 1, 1 if ((awayodds < .5 and away_rbi > home_rbi) or (awayodds > .5 and away_rbi < home_rbi)) else 0, awayodds, homeodds


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
    bounds_lol = [modterm.bounds for modterm in MOFO_MOD_TERMS]
    bounds = [item for sublist in bounds_lol for item in sublist]
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    game_list = base_solver.get_games(cmd_args.gamefile)
    with open('team_attrs.json') as f_attrs:
        team_attrs = json.load(f_attrs)
    with open("base_mofo.csv") as f_mofo:
        mofo_base_terms, _ = parse_terms(f_mofo.read(), [])
    args = (get_mofo_mod_results, mofo_base_terms, None, MOFO_MOD_TERMS, stat_file_map, game_list, team_attrs,
            cmd_args.debug, cmd_args.debug2, cmd_args.debug3)
    result = differential_evolution(base_solver.minimize_func, bounds, args=args, popsize=15, tol=0.0001,
                                    mutation=(0.05, 1.99), recombination=0.7, workers=1, maxiter=1000)
    print("\n".join("{},{},{},{},{},{}".format(stat.attr, stat.team, stat.stat,
                                               a, b, c) for stat, (a, b, c) in zip(MOFO_MOD_TERMS, zip(*[iter(result.x)] * 3))))
    result_fail_rate = base_solver.minimize_func(result.x, get_mofo_mod_results, mofo_base_terms, None, MOFO_MOD_TERMS,
                                                 stat_file_map, game_list, team_attrs, cmd_args.mod, False, False,
                                                 False)
    print("Result fail rate: {:.2f}%".format(result_fail_rate*100.0))
    print(datetime.datetime.now())


if __name__ == "__main__":
    main()