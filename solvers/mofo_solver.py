import argparse
import json
from scipy.optimize import differential_evolution
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
        return 0, 0
    away_game, home_game = game["away"], game["home"]
    home_rbi, away_rbi = float(away_game["opposing_team_rbi"]), float(home_game["opposing_team_rbi"])
    if away_rbi == home_rbi:
        return 0, 0
    awayPitcher, awayTeam = pitchers.get(away_game["pitcher_id"])
    homePitcher, homeTeam = pitchers.get(home_game["pitcher_id"])
    awayodds, _ = get_mofo(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, terms,
                           awayMods, homeMods)
    if awayodds == .5:
        return 0, 0
    return 1, 1 if ((awayodds < .5 and away_rbi > home_rbi) or (awayodds > .5 and away_rbi < home_rbi)) else 0


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
    bounds = [(0, 10), (0, 3), (-3, 3)] * len(MOFO_STLAT_LIST)
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    game_list = base_solver.get_games(cmd_args.gamefile)
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    args = (get_mofo_results, MOFO_STLAT_LIST, None, None, stat_file_map, game_list, team_attrs, cmd_args.debug,
            cmd_args.debug2, cmd_args.debug3)
    result = differential_evolution(base_solver.minimize_func, bounds, args=args, maxiter=10, popsize=15, tol=0.001,
                                    mutation=(0.05, 0.1), init=(7.141835759, 0.503611539, -0.134217004, 6.03116067, 0.531907372, -1.96850269, 6.330924488, 1.688350172, 1.868637302, 5.33410044, 1.393253982, 1.670149138, 8.517448711, 0.834762894, 1.895665368, 5.211592108, 1.455262552, -2.961974444, 5.225000491, 0.725241067, 2.323357219, 8.754798405, 1.828420628, 1.564051697, 1.615697518, 1.329302839, 1.005876184, 2.484814126, 0.342809525, -2.863533186, 8.367209349, 2.3383441, -2.829429781, 4.534922831, 0.271221196, -2.316739796, 9.742195951, 1.546922195, -1.126472164, 1.695064764, 0.889938636, 0.863982259, 8.34822847, 2.000915556, 1.06657584, 2.626088412, 1.592548105, 2.385444421, 3.18217294, 0.599029008, 1.248676183, 8.889518938, 1.583091375, -0.566306861, 8.482056868, 1.503685653, -1.642106236, 6.993114218, 1.680567368, -2.136884855, 4.249528268, 0.473084595, 2.162069786, 3.480568672, 1.416297739, -1.455887403, 1.745518254, 2.588207284, 2.309943752, 8.827172927, 0.932838482, 2.7667274, 4.217588037, 0.050821976, -1.903501566, 1.04042001, 1.809579481, 2.669060547, 3.703538684, 0.674617722, -0.570112055, 1.854276484, 1.607250927, 2.58613989, 0.640313352, 1.102861087, 2.168676787, 2.31169723, 2.12725658, -2.537657604, 5.27465895, 0.432909418, -0.852764063, 6.112073675, 2.042758542, -1.083810921, 2.083457367, 2.365646867, 0.599744892, 3.321554752, 0.769805978, -0.624342065, 8.722576947, 2.018623797, -0.98550069, 7.170114458, 2.813589853, 1.007559189, 8.131811478, 0.630769677, -0.225363637), workers=-1)
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(MOFO_STLAT_LIST,
                                                                                   zip(*[iter(result.x)] * 3))))
    result_fail_rate = base_solver.minimize_func(result.x, get_mofo_results, MOFO_STLAT_LIST, None, None, stat_file_map,
                                                 game_list, team_attrs, False, False, False)
    print("Result fail rate: {:.2f}%".format(result_fail_rate*100.0))
    print(datetime.datetime.now())


if __name__ == "__main__":
    main()
