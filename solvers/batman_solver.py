import argparse
import json
import math
from scipy.optimize import differential_evolution
import datetime
import sys

sys.path.append("..")
from solvers import base_solver
from solvers.batman_ballpark_terms import BATMAN_BALLPARK_TERMS
from solvers.batman_mod_terms import BATMAN_MOD_TERMS
from batman import get_batman


BATMAN_STLAT_LIST = ("tragicness", "patheticism", "thwackability", "divinity", "moxie", "musclitude", "martyrdom", 
                     "unthwackability", "ruthlessness", "overpowerment", "shakespearianism", "coldness", "meanomniscience",
                 "meantenaciousness", "meanwatchfulness", "meananticapitalism", "meanchasiness",                  
                 "maxomniscience", "maxtenaciousness", "maxwatchfulness", "maxanticapitalism", "maxchasiness")

BATMAN_ABS_STLAT_LIST = ("tragicness", "patheticism", "thwackability", "divinity", "moxie", "musclitude", "martyrdom", 
                     "unthwackability", "ruthlessness", "overpowerment", "shakespearianism", "coldness", "meanomniscience",
                 "meantenaciousness", "meanwatchfulness", "meananticapitalism", "meanchasiness", 
                 "meanlaserlikeness", "meanbasethirst", "meancontinuation", "meangroundfriction", "meanindulgence",
                 "maxomniscience", "maxtenaciousness", "maxwatchfulness", "maxanticapitalism", "maxchasiness",
                 "maxlaserlikeness", "maxbasethirst", "maxcontinuation", "maxgroundfriction", "maxindulgence")

BATMAN_SPECIAL_CASES = ("exponent", "everythingelse")

BATMAN_ABS_SPECIAL_CASES = ("exponent", "everythingelse", "reverberation", "repeating")


def get_batman_results(eventofinterest, batter_perf_data, season_team_attrs, team_stat_data, pitcher_stat_data, pitcher, batter, lineup_size, terms, special_cases, game, battingteam, pitchingteam, pitchingmods, battingmods):
    game_attrs = base_solver.get_attrs_from_paired_game(season_team_attrs, game)
    awayAttrs, homeAttrs = game_attrs["away"], game_attrs["home"]
    special_game_attrs = (homeAttrs.union(awayAttrs)) - base_solver.ALLOWED_IN_BASE_BATMAN        
    games, fail_batman, fail_batman_by, actual, real_val = 0, 100, 100.0, 0, 0
    if special_game_attrs:
        fail_batman, fail_batman_by, actual, real_val = 0, 0, 0, 0
    else:                        
        atbats, hits, homers, innings = int(batter_perf_data["at_bats"]), int(batter_perf_data["hits"]), int(batter_perf_data["home_runs"]), int(batter_perf_data["num_innings"])                        
        games, fail_batman, fail_batman_by = 1, 1, 0.0               
        if eventofinterest == "abs":                 
            batman = team_stat_data[batter]
            if atbats - 0.5 < batman < atbats + 0.5:
                fail_batman -= 1
            fail_batman_by = batman - atbats            
            real_val = atbats
            actual = "Real vals {} in {} innings, batman {:.2f} in {} innings".format(atbats, innings, batman, innings)            
        else:
            try:                
                batman = get_batman(eventofinterest, pitcher, pitchingteam, batter, battingteam, team_stat_data, pitcher_stat_data, terms, pitchingmods, battingmods, {"factors": special_cases})            
            except ValueError:
                batman = -10000      
            if math.isnan(batman):
                batman = -10000            
            if eventofinterest == "hits":            
                if (hits - 0.25) < (batman * atbats) < (hits + 0.25):                
                    fail_batman -= 1
                fail_batman_by = (batman * atbats) - hits
                batman_val = (batman * atbats)
                real_val = hits
                actual = "{} hits, batman {:.4f}".format(hits, (batman * atbats))
            elif eventofinterest == "hrs":
                if (homers - 0.25) < (batman * atbats) < (homers + 0.25):
                    fail_batman -= 1
                fail_batman_by = (batman * atbats) - homers
                batman_val = (batman * atbats)
                real_val = homers
                actual = "{} hrs, batman {:.4f}".format(homers, (batman * atbats))        
    return games, fail_batman, fail_batman_by, actual, real_val

def parse_games(data):
    results = []
    splitdata = [d.split(",") for d in data.split("\n")[1:] if d]
    for row in splitdata:
        name = row[0].lower()                
        results.append(name)
    return results

def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--hits', help="solve for hits", action='store_true')
    parser.add_argument('--homers', help="solve for homers", action='store_true')    
    parser.add_argument('--statfolder', help="path to stat folder")
    parser.add_argument('--ballparks', help="path to ballparks folder")
    parser.add_argument('--gamefile', help="path to game file")    
    parser.add_argument('--batterfile', help="path to the batter file")      
    parser.add_argument('--debug', help="print output", action='store_true')
    parser.add_argument('--debug2', help="print output", action='store_true')
    parser.add_argument('--debug3', help="print output", action='store_true')
    parser.add_argument('--output', required=False, help="file output directory")
    parser.add_argument('--workers', default="1", help="number of workers to use")
    parser.add_argument('--init', required=False, help="directory to use for init")
    parser.add_argument('--random', help="use random files instead of top 15", action='store_true')
    args = parser.parse_args()
    return args


def get_init_values(init_dir, popsize, is_random):
    pattern = re.compile(r'^Best so far - fail rate (\d*.\d*)%, linear error (\d*.\d*)$', re.MULTILINE)
    results = []
    job_ids = {filename.rsplit("-", 1)[0] for filename in os.listdir(init_dir) if filename.endswith("details.txt")}
    if len(job_ids) < popsize:
        raise Exception("Population is set to {} and there are only {} solutions, find more solutions or decrease pop size".format(popsize, len(job_ids)))
    for job_id in job_ids:
        with open(os.path.join(init_dir, "{}-solution.json".format(job_id))) as solution_file, open(os.path.join(init_dir, "{}-details.txt".format(job_id))) as details_file:
            results.append((float(pattern.findall(details_file.read())[0][0]), json.load(solution_file)))
    if is_random:
        random.shuffle(results)
    else:
        results.sort(key=lambda x: x[0])
    return np.array([result[1] for result in results[:popsize]])


def main():
    print(datetime.datetime.now())
    cmd_args = handle_args()    
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    game_list = base_solver.get_games(cmd_args.gamefile)    
    workers = int(cmd_args.workers)
    batter_list = base_solver.get_batters(cmd_args.batterfile)    
    ballpark_file_map = base_solver.get_ballpark_map(cmd_args.ballparks)
    stlatlist = BATMAN_STLAT_LIST
    special_cases = BATMAN_SPECIAL_CASES
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    with open("sweptelsewheregames.csv") as f_swelsewhere:
        games_swept_elsewhere = parse_games(f_swelsewhere.read())    
    if cmd_args.hits:
        eventofinterest = "hits"            
        base_bounds = ([(-2, 8), (0, 3), (-2, 4)] * len(stlatlist)) + [(1, 3), (0, 2)]
    elif cmd_args.homers:
        eventofinterest = "hrs"        
        base_bounds = ([(-2, 8), (0, 3), (-2, 4)] * len(stlatlist)) + [(1, 3), (0, 2)]
    else:
        eventofinterest = "abs"
        stlatlist = BATMAN_ABS_STLAT_LIST
        special_cases = BATMAN_ABS_SPECIAL_CASES
        base_bounds = ([(-2, 8), (0, 3), (-2, 4)] * len(stlatlist)) + [(1, 3), (0, 2), (0, 0.02), (0, 0.02)]
    bounds_team_mods = [modterm.bounds for modterm in BATMAN_MOD_TERMS if modterm.stat.lower() in stlatlist]
    bounds_team = [item for sublist in bounds_team_mods for item in sublist]    
    modterms = [modterm for modterm in BATMAN_MOD_TERMS if modterm.stat.lower() in stlatlist]
    bounds_park_mods = [modterm.bounds for modterm in BATMAN_BALLPARK_TERMS if modterm.playerstat.lower() in stlatlist]
    bounds_park = [item for sublist in bounds_park_mods for item in sublist]
    parkterms = [modterm for modterm in BATMAN_BALLPARK_TERMS if modterm.playerstat.lower() in stlatlist]
    bounds = base_bounds + bounds_team + bounds_park            
    popsize = 25
    init = get_init_values(cmd_args.init, popsize, cmd_args.random) if cmd_args.init else 'latinhypercube'
    args = (eventofinterest, batter_list, get_batman_results, stlatlist, special_cases, modterms, parkterms, stat_file_map, ballpark_file_map, game_list, team_attrs, games_swept_elsewhere, 
            cmd_args.debug, cmd_args.debug2, cmd_args.debug3, cmd_args.output)
    result = differential_evolution(base_solver.minimize_batman_func, bounds, args=args, popsize=popsize, tol=0.0001, 
                                    mutation=(0.01, 1.99), recombination=0.7, workers=workers, maxiter=10000, init=init)
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