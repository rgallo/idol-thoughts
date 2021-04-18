import argparse
import json
import math
import numpy as np
from scipy.optimize import differential_evolution
import datetime
import os
import sys
import re

sys.path.append("..")
from solvers import base_solver
from solvers.batman_abs_terms import BATMAN_ABS_TERMS
from solvers.batman_hrs_terms import BATMAN_HRS_TERMS
from solvers.batman_hits_terms import BATMAN_HITS_TERMS
from solvers.batman_ballpark_terms import BATMAN_BALLPARK_TERMS
from solvers.batman_mod_terms import BATMAN_MOD_TERMS
from batman import get_batman

BATMAN_HITS_SPECIAL_CASES = ("cutoff",)

BATMAN_HRS_SPECIAL_CASES = ("cutoff",)

BATMAN_ABS_SPECIAL_CASES = ("hitcutoff", "hrcutoff", "walkcutoff", "attemptcutoff", "runoutcutoff", "reverberation", "repeating")                                                                                                                                

def get_batman_results(batter_perf_data, season_team_attrs, atbats_team_stat_data, hits_team_stat_data, hrs_team_stat_data, batter, game):
    game_attrs = base_solver.get_attrs_from_paired_game(season_team_attrs, game)
    awayAttrs, homeAttrs = game_attrs["away"], game_attrs["home"]
    special_game_attrs = (homeAttrs.union(awayAttrs)) - base_solver.ALLOWED_IN_BASE_BATMAN        
    batters, atbatfailby, hitfailby, hrfailby, ab_real_val, hit_real_val, hr_real_val = 0, 100.0, 100.0, 100.0, 0, 0, 0
    if special_game_attrs:
        atbatfailby, hitfailby, hrfailby = 0, 0, 0
        return batters, atbatfailby, hitfailby, hrfailby, ab_real_val, hit_real_val, hr_real_val
    else:                        
        ab_real_val, hit_real_val, hr_real_val = int(batter_perf_data["at_bats"]), int(batter_perf_data["hits"]), int(batter_perf_data["home_runs"])              
        batters = 1        
        atbatfailby = atbats_team_stat_data[batter] - ab_real_val          
        hitfailby = hits_team_stat_data[batter] - hit_real_val                
        hrfailby = hrs_team_stat_data[batter] - hr_real_val        
        #print("Atbat = {:.4f} vs {}, hit = {:.4f} vs {}, hr = {:.4f} vs {}".format(atbats_team_stat_data[batter], ab_real_val, hits_team_stat_data[batter], hit_real_val, hrs_team_stat_data[batter], hr_real_val))
    return batters, atbatfailby, hitfailby, hrfailby, ab_real_val, hit_real_val, hr_real_val           

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


def get_init_values(init_dir, eventofinterest, popsize, is_random):
    pattern = re.compile(r'^max underestimate (-?[\d\.]*), max overestimate (-?[\d\.]*), unexvar (-?[\d\.]*)$', re.MULTILINE)
    results = []
    job_ids = {filename.rsplit("-", 1)[0] for filename in os.listdir(init_dir) if filename.endswith("details.txt")}
    if len(job_ids) < popsize:
        raise Exception("Population is set to {} and there are only {} solutions, find more solutions or decrease pop size".format(popsize, len(job_ids)))
    for job_id in job_ids:
        with open(os.path.join(init_dir, "{}-".format(job_id) + eventofinterest + "solution.json")) as solution_file, open(os.path.join(init_dir, "{}-".format(job_id) + eventofinterest + "details.txt")) as details_file:
            underestimate, overestimate, unexvar = pattern.findall(details_file.read())[0]            
            results.append((max(abs(float(underestimate)), abs(float(overestimate))), json.load(solution_file)))
    if is_random:
        random.shuffle(results)
    else:
        results.sort(key=lambda x: x[0], reverse=False)
    return np.array([result[1] for result in results[:popsize]])


def main():
    print(datetime.datetime.now())
    cmd_args = handle_args()    
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    game_list = base_solver.get_games(cmd_args.gamefile)    
    workers = int(cmd_args.workers)
    batter_list = base_solver.get_batters(cmd_args.batterfile)    
    ballpark_file_map = base_solver.get_ballpark_map(cmd_args.ballparks)    
    establish_baseline = False    
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    with open("sweptelsewheregames.csv") as f_swelsewhere:
        games_swept_elsewhere = parse_games(f_swelsewhere.read())                
    establish_baseline = True
    stlatlist = [stlatterm.stat.lower() for stlatterm in BATMAN_ABS_TERMS]          
    bounds_terms_base = [stlatterm.bounds for stlatterm in BATMAN_ABS_TERMS]        
    bounds_terms = [item for sublist in bounds_terms_base for item in sublist]    
    special_cases = BATMAN_ABS_SPECIAL_CASES                
    base_bounds = bounds_terms + [[0, 0.1], [0, 0.1], [0, 0.1], [0, 0.25], [0, 0.1], [0, 0.02], [0, 0.02]]        
    bounds_team_mods = [modterm.bounds for modterm in BATMAN_MOD_TERMS if modterm.stat.lower() in stlatlist]
    bounds_team = [item for sublist in bounds_team_mods for item in sublist]    
    modterms = [modterm for modterm in BATMAN_MOD_TERMS if modterm.stat.lower() in stlatlist]
    bounds_park_mods = [modterm.bounds for modterm in BATMAN_BALLPARK_TERMS if modterm.playerstat.lower() in stlatlist]
    bounds_park = [item for sublist in bounds_park_mods for item in sublist]
    parkterms = [modterm for modterm in BATMAN_BALLPARK_TERMS if modterm.playerstat.lower() in stlatlist]
    bounds = base_bounds + bounds_team + bounds_park                
    popsize = 25
    init = get_init_values(cmd_args.init, eventofinterest, popsize, cmd_args.random) if cmd_args.init else 'latinhypercube'
    recombination = 0.7
    #recombination = 0.7 if (type(init) == str) else 0.4
    #recombination = 0.5 if (workers > 2) else recombination        
    args = ("abs", batter_list, get_batman_results, stlatlist, special_cases, modterms, parkterms, stat_file_map, ballpark_file_map, game_list, team_attrs, games_swept_elsewhere, establish_baseline, 
            cmd_args.debug, cmd_args.debug2, cmd_args.debug3, cmd_args.output)
    result = differential_evolution(base_solver.minimize_batman_func, bounds, args=args, popsize=popsize, tol=0.0001, 
                                    mutation=(0.01, 1.99), recombination=recombination, workers=workers, maxiter=10000, init=init)
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in
                    zip(stlatlist, zip(*[iter(result.x[:-len(special_cases)])] * 3))))
    print("factors,{},{}".format(result.x[-2], result.x[-1]))
    result_fail_rate = base_solver.minimize_batman_func(result.x, eventofinterest, batter_list, get_batman_results, BATMAN_STLAT_LIST, BATMAN_SPECIAL_CASES,
                                                    [], stat_file_map, game_list, team_attrs,
                                                    False, False, False)
    print("Result fail rate: {:.2f}%".format(result_fail_rate*100.0))
    print(datetime.datetime.now())    

if __name__ == "__main__":
    main()