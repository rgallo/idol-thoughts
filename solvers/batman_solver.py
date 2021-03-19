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
                 "meantenaciousness", "meanwatchfulness", "meananticapitalism", "meanchasiness", 
                 "meanlaserlikeness", "meanbasethirst", "meancontinuation", "meangroundfriction", "meanindulgence",
                 "maxomniscience", "maxtenaciousness", "maxwatchfulness", "maxanticapitalism", "maxchasiness",
                 "maxlaserlikeness", "maxbasethirst", "maxcontinuation", "maxgroundfriction", "maxindulgence")

BATMAN_ABS_STLAT_LIST = ("tragicness", "patheticism", "thwackability", "divinity", "moxie", "musclitude", "martyrdom", 
                     "unthwackability", "ruthlessness", "overpowerment", "shakespearianism", "coldness", "meanomniscience",
                 "meantenaciousness", "meanwatchfulness", "meananticapitalism", "meanchasiness", 
                 "meanlaserlikeness", "meanbasethirst", "meancontinuation", "meangroundfriction", "meanindulgence",
                 "maxomniscience", "maxtenaciousness", "maxwatchfulness", "maxanticapitalism", "maxchasiness",
                 "maxlaserlikeness", "maxbasethirst", "maxcontinuation", "maxgroundfriction", "maxindulgence")

BATMAN_SPECIAL_CASES = ("exponent", "everythingelse")

BATMAN_ABS_SPECIAL_CASES = ("exponent", "everythingelse", "reverberation", "repeating")


def get_batman_results(eventofinterest, batter_perf_data, season_team_attrs, team_stat_data, pitcher_stat_data, pitcher, batter, lineup_size, terms, special_cases, game, battingteam, pitchingteam, mods):
    game_attrs = base_solver.get_attrs_from_paired_game(season_team_attrs, game)
    special_game_attrs = (game_attrs["home"].union(game_attrs["away"])) - base_solver.ALLOWED_IN_BASE
    games, fail_batman, fail_batman_by, actual, real_val = 0, 100, 100, 0, 0
    if special_game_attrs:
        fail_batman, fail_batman_by, actual, real_val = 0, 0, 0, 0
    else:                        
        atbats, hits, homers, innings = int(batter_perf_data["at_bats"]), int(batter_perf_data["hits"]), int(batter_perf_data["home_runs"]), int(batter_perf_data["num_innings"])                
        #how many atbats in a 9 inning game
        atbats_in9 = math.ceil((atbats / innings) * 9.0)
        #how many atbats in a 9 inning game per a 9 player lineup (all estimations should be multiplied by (9.0 / actual lineup size))
        #atbats_lineup = (atbats_in9 / 9.0) * lineup_size               
        games, fail_batman, fail_batman_by = 1, 1, 0                
        if eventofinterest == "abs":                 
            batman = team_stat_data[battingteam][batter]["atbats"]
            if (atbats_in9 - 0.5) < batman < (atbats_in9 + 0.5):
                fail_batman -= 1
            fail_batman_by = batman - atbats_in9            
            real_val = atbats_in9
            actual = "Real vals {} in {} innings, {:.2f} in 9 innings, batman {:.2f} in 9 innings".format(atbats, innings, atbats_in9, batman)            
        else:
            try:
                batman = get_batman(eventofinterest, pitcher, pitchingteam, batter, battingteam, team_stat_data, pitcher_stat_data, terms, {"factors": special_cases})            
            except ValueError:
                batman = -10000      
            if math.isnan(batman):
                batman = -10000
            if eventofinterest == "hits":            
                if (hits - 0.5) < (batman * atbats) < (hits + 0.5):                
                    fail_batman -= 1
                fail_batman_by = (batman * atbats) - hits
                batman_val = (batman * atbats)
                real_val = hits
                actual = "{} hits, batman {:.4f}".format(hits, (batman * atbats))
            elif eventofinterest == "hrs":
                if (homers - 0.5) < (batman * atbats) < (homers + 0.5):
                    fail_batman -= 1
                fail_batman_by = (batman * atbats) - homers
                batman_val = (batman * atbats)
                real_val = homers
                actual = "{} hrs, batman {:.4f}".format(homers, (batman * atbats))        
    return games, fail_batman, fail_batman_by, actual, real_val


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--hits', help="solve for hits", action='store_true')
    parser.add_argument('--homers', help="solve for homers", action='store_true')    
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
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    game_list = base_solver.get_games(cmd_args.gamefile)    
    batter_list = base_solver.get_batters(cmd_args.batterfile)        
    stlatlist = BATMAN_STLAT_LIST
    special_cases = BATMAN_SPECIAL_CASES
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    if cmd_args.hits:
        eventofinterest = "hits"            
        bounds = [[-6, 6], [-1, 2], [0, 2]] * len(stlatlist) + [[1, 3], [0, 2]]
    elif cmd_args.homers:
        eventofinterest = "hrs"        
        bounds = [[-6, 6], [-1, 2], [0, 2]] * len(stlatlist) + [[1, 3], [0, 2]]
    else:
        eventofinterest = "abs"
        stlatlist = BATMAN_ABS_STLAT_LIST
        special_cases = BATMAN_ABS_SPECIAL_CASES
        bounds = [[-8, 8], [-1, 2], [0, 2]] * len(stlatlist) + [[1, 3], [0, 2], [0, 0.02], [0, 0.02]]
    args = (eventofinterest, batter_list, get_batman_results, stlatlist, special_cases, [], stat_file_map, game_list, team_attrs, 
            cmd_args.debug, cmd_args.debug2, cmd_args.debug3)
    result = differential_evolution(base_solver.minimize_batman_func, bounds, args=args, popsize=15, tol=0.0001, 
                                    mutation=(0.05, 1.99), recombination=0.7, workers=1, maxiter=10000)
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in
                    zip(BATMAN_STLAT_LIST, zip(*[iter(result.x[:-len(BATMAN_SPECIAL_CASES)])] * 3))))
    print("factors,{},{}".format(result.x[-2], result.x[-1]))
    result_fail_rate = base_solver.minimize_batman_func(result.x, eventofinterest, batter_list, get_batman_results, BATMAN_STLAT_LIST, BATMAN_SPECIAL_CASES,
                                                    [], stat_file_map, game_list, team_attrs,
                                                    False, False, False)
    print("Result fail rate: {:.2f}%".format(result_fail_rate*100.0))
    print(datetime.datetime.now())    

if __name__ == "__main__":
    main()