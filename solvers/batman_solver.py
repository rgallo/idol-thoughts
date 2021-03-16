import argparse
import json
import math
from scipy.optimize import differential_evolution
import datetime
import sys

sys.path.append("..")
from solvers import base_solver
from batman import get_batman


BATMAN_STLAT_LIST = ("tragicness", "patheticism", "thwackability", "divinity", "moxie", "musclitude", "martyrdom", 
                     "unthwackability", "ruthlessness", "overpowerment", "shakespearianism", "coldness", "meanomniscience",
                 "meantenaciousness", "meanwatchfulness", "meananticapitalism", "meanchasiness", "meantragicness",
                 "meanpatheticism", "meanthwackability", "meandivinity", "meanmoxie", "meanmusclitude", "meanmartyrdom",
                 "meanlaserlikeness", "meanbasethirst", "meancontinuation", "meangroundfriction", "meanindulgence",
                 "maxomniscience", "maxtenaciousness", "maxwatchfulness", "maxanticapitalism", "maxchasiness",
                 "maxthwackability", "maxdivinity", "maxmoxie", "maxmusclitude", "maxmartyrdom", "maxlaserlikeness",
                 "maxbasethirst", "maxcontinuation", "maxgroundfriction", "maxindulgence")

BATMAN_SPECIAL_CASES = ("exponent", "everythingelse")


def get_batman_results(eventofinterest, batter_perf_data, season_team_attrs, team_stat_data, pitcher_stat_data, pitcher, batter, lineup_size, terms, special_cases, game, mods):
    game_attrs = base_solver.get_attrs_from_paired_game(season_team_attrs, game)
    special_game_attrs = (game_attrs["home"].union(game_attrs["away"])) - base_solver.ALLOWED_IN_BASE
    games, fail_batman, fail_batman_by = 0, 2, 100
    if special_game_attrs:
        fail_batman, fail_batman_by = 0, 0
    else:                
        pitchingteam = batter_perf_data["pitcher_team_id"]
        battingteam = batter_perf_data["batter_team_id"]
        atbats, hits, homers, innings = int(batter_perf_data["at_bats"]), int(batter_perf_data["hits"]), int(batter_perf_data["home_runs"]), int(batter_perf_data["num_innings"])        
        print("Batter ID = {} At bats = {}, hits = {}, homers = {}, innings = {}".format(batter, atbats, hits, homers, innings))
        print("pitching team = {}".format(pitchingteam))
        #how many atbats in a 9 inning game
        atbats_in9 = (atbats / innings) * 9.0
        #how many atbats in a 9 inning game per a 9 player lineup (all estimations should be multiplied by (9.0 / actual lineup size))
        atbats_lineup = (atbats_in9 / lineup_size) * 9.0
        hits_per_atbat, homers_per_atbat = (hits / atbats), (homers / atbats)
        try:
            batman = get_batman(eventofinterest, pitcher, pitchingteam, batter, battingteam, team_stat_data, pitcher_stat_data, terms, {"factors": special_cases})            
        except ValueError:
            batman = -100000        
        fail_batman, fail_batman_by = 1, 0        
        if eventofinterest == "abs":
            if max(atbats_lineup - 1.0, 0.0) <= batman <= (atbats_lineup + 1.0):
                fail_batman -= 1
            fail_batman_by = batman - atbats_lineup
        elif eventofinterest == "hits":
            if max(hits_per_atbat - 1.0, 0.0) <= batman <= (hits_per_atbat + 1.0):
                fail_batman -= 1
            fail_batman_by = batman - hits_per_atbat
        elif eventofinterest == "hrs":
            if max(homers_per_atbat - 1.0, 0.0) <= batman <= (homers_per_atbat + 1.0):
                fail_batman -= 1
            fail_batman_by = batman - homers_per_atbat                
        games = 1
    return games, fail_k9, fail_batman_by


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--hits', help="solve for hits")
    parser.add_argument('--homers', help="solve for homers")    
    parser.add_argument('--statfolder', help="path to stat folder")
    parser.add_argument('--gamefile', help="path to game file")
    parser.add_argument('--batterfile', help="path to the batter file")    
    parser.add_argument('--debug', help="print output", action='store_true')
    parser.add_argument('--debug2', help="print output", action='store_true')
    parser.add_argument('--debug3', help="print output", action='store_true')
    args = parser.parse_args()
    return args


def main():
    print(datetime.datetime.now())
    cmd_args = handle_args()
    bounds = [[-5, 5], [0, 3], [0, 3]] * len(BATMAN_STLAT_LIST) + [[1, 3], [-2, 2]]
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    game_list = base_solver.get_games(cmd_args.gamefile)    
    batter_list = base_solver.get_batters(cmd_args.batterfile)    
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    if cmd_args.hits:
        eventofinterest = "hits"
    elif cmd_args.homers:
        eventofinterest = "hrs"
    else:
        eventofinterest = "abs"
    args = (eventofinterest, batter_list, get_batman_results, BATMAN_STLAT_LIST, BATMAN_SPECIAL_CASES, [], stat_file_map, game_list, team_attrs, 
            cmd_args.debug, cmd_args.debug2, cmd_args.debug3)
    result = differential_evolution(base_solver.minimize_batman_func, bounds, args=args, popsize=15, tol=0.0001, 
                                    mutation=(0.05, 1.99), recombination=0.7, workers=1, maxiter=10000)
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in
                    zip(BATMAN_STLAT_LIST, zip(*[iter(result.x[:-len(BATMAN_SPECIAL_CASES)])] * 3))))
    print("factors,{},{}".format(result.x[-2], result.x[-1]))
    result_fail_rate = base_solver.minimize_func(result.x, get_batman_results, BATMAN_STLAT_LIST, BATMAN_SPECIAL_CASES,
                                                    [], stat_file_map, game_list, team_attrs,
                                                    False, False, False)
    print("Result fail rate: {:.2f}%".format(result_fail_rate*100.0))
    print(datetime.datetime.now())    

if __name__ == "__main__":
    main()