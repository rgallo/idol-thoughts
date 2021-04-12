import argparse
import json
import os
import random
import re

import numpy as np
from scipy.optimize import differential_evolution
import datetime
import sys
from dotenv import load_dotenv

sys.path.append("..")
import requests
from solvers import base_solver
from solvers.mofo_ballpark_terms import BALLPARK_TERMS
from solvers.mofo_mod_terms import MOFO_MOD_TERMS
import mofo


MOFO_STLAT_LIST = ("meantragicness", "meanpatheticism", "meanthwackability", "meandivinity", "meanmoxie",
                   "meanmusclitude", "meanmartyrdom", "maxthwackability", "maxdivinity", "maxmoxie", "maxmusclitude",
                   "maxmartyrdom", "meanlaserlikeness", "meanbasethirst", "meancontinuation", "meangroundfriction",
                   "meanindulgence", "maxlaserlikeness", "maxbasethirst", "maxcontinuation", "maxgroundfriction",
                   "maxindulgence", "unthwackability", "ruthlessness", "overpowerment", "shakespearianism", "coldness",
                   "meanomniscience", "meantenaciousness", "meanwatchfulness", "meananticapitalism", "meanchasiness",
                   "maxomniscience", "maxtenaciousness", "maxwatchfulness", "maxanticapitalism", "maxchasiness")


def get_mofo_results(game, season_team_attrs, team_stat_data, pitcher_stat_data, pitchers, terms, special_cases, mods, ballpark, ballpark_mods):    
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
    awayMods, homeMods = mofo.get_mods(mods, game_attrs["away"], game_attrs["home"], awayTeam, homeTeam, awayPitcher, homePitcher, away_game["weather"], ballpark, ballpark_mods, team_stat_data, pitcher_stat_data)                          
    awayodds, homeodds = mofo.get_mofo(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, terms,
                           awayMods, homeMods)    
    if awayodds == .5:
        return 1, 1, awayodds, homeodds
    fail = 1 if ((awayodds < .5 and away_rbi > home_rbi) or (awayodds > .5 and away_rbi < home_rbi)) else 0
    return 1, fail, awayodds, homeodds


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--statfolder', help="path to stat folder")
    parser.add_argument('--ballparks', help="path to ballparks folder")
    parser.add_argument('--gamefile', help="path to game file")    
    parser.add_argument('--debug', help="print output", action='store_true')
    parser.add_argument('--debug2', help="print output", action='store_true')
    parser.add_argument('--debug3', help="print output", action='store_true')
    parser.add_argument('--output', required=False, help="file output directory")
    parser.add_argument('--workers', default="1", help="number of workers to use")
    parser.add_argument('--init', required=False, help="directory to use for init")
    parser.add_argument('--ev', help="solve for best ev instead of fail rate", action="store_true")
    parser.add_argument('--random', help="use random files instead of top", action='store_true')
    parser.add_argument('--worst', help="use worst files instead of top", action='store_true')
    args = parser.parse_args()
    return args


def get_init_values(init_dir, popsize, is_random, is_worst):
    pattern = re.compile(r'^Best so far - Linear fail ([-\.\d]*), fail rate ([-\.\d]*)%$', re.MULTILINE)
    results = []
    job_ids = {filename.rsplit("-", 1)[0] for filename in os.listdir(init_dir) if filename.endswith("details.txt")}
    if len(job_ids) < popsize:
        raise Exception("Population is set to {} and there are only {} solutions, find more solutions or decrease pop size".format(popsize, len(job_ids)))
    for job_id in job_ids:
        with open(os.path.join(init_dir, "{}-solution.json".format(job_id))) as solution_file, open(os.path.join(init_dir, "{}-details.txt".format(job_id))) as details_file:
            results.append((float(pattern.findall(details_file.read())[0][1]), json.load(solution_file)))
    if is_random:
        random.shuffle(results)
    else:
        results.sort(key=lambda x: x[0], reverse=is_worst)
    return np.array([result[1] for result in results[:popsize]])


def main():
    print(datetime.datetime.now())
    cmd_args = handle_args()
    bounds_team_mods = [modterm.bounds for modterm in MOFO_MOD_TERMS]
    bounds_team = [item for sublist in bounds_team_mods for item in sublist]
    bounds_park_mods = [modterm.bounds for modterm in BALLPARK_TERMS]
    bounds_park = [item for sublist in bounds_park_mods for item in sublist]
    bounds_terms = ([(-8, 0), (0, 3), (0, 4)] * 2) + ([(0, 8), (0, 3), (0, 4)] * 20) + ([(0, 10), (0, 3), (0, 4)] * 5) + ([(0, 8), (0, 3), (0, 4)] * (len(MOFO_STLAT_LIST) - 27))
    bounds = bounds_terms + bounds_team + bounds_park
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    ballpark_file_map = base_solver.get_ballpark_map(cmd_args.ballparks)    
    game_list = base_solver.get_games(cmd_args.gamefile)
    solve_for_ev = cmd_args.ev
    with open('team_attrs.json') as f:
        team_attrs = json.load(f) 
   
    #establish our baseline    
    if not cmd_args.init:
        number_to_beat = None
    else:
        print("Using initial values. Checking master for number to beat.")
        load_dotenv(dotenv_path="../.env")
        github_token = os.getenv("GITHUB_TOKEN")
        params = []
        for url_prop in ("MOFO_TERMS", "MOFO_MODS", "MOFO_BALLPARK_TERMS"):
            url = os.getenv(url_prop)      
            terms = requests.get(url, headers={"Authorization": "token {}".format(github_token)}).text
            params.extend(",".join([",".join(line.split(",")[-3:]) for line in terms.split("\n")[1:] if line]).split(","))   
        baseline_parameters = [float(val) for val in params]
        try:
            number_to_beat = base_solver.minimize_func(baseline_parameters, get_mofo_results, MOFO_STLAT_LIST, None, MOFO_MOD_TERMS,
                                                     BALLPARK_TERMS, stat_file_map, ballpark_file_map, game_list,
                                                     team_attrs, None, solve_for_ev, cmd_args.debug, cmd_args.debug2, cmd_args.debug3, cmd_args.output)            
        except Exception as e:
            print(e)
            number_to_beat = None        

    print("Number to beat = {}".format(number_to_beat))
    #solver time
    workers = int(cmd_args.workers)        
    popsize = 25    
    init = get_init_values(cmd_args.init, popsize, cmd_args.random, cmd_args.worst) if cmd_args.init else 'latinhypercube'
    recombination = 0.7
    #recombination = 0.7 if (type(init) == str) else 0.4
    recombination = 0.5 if (workers > 2) else recombination
    args = (get_mofo_results, MOFO_STLAT_LIST, None, MOFO_MOD_TERMS, BALLPARK_TERMS, stat_file_map, ballpark_file_map,
            game_list, team_attrs, number_to_beat, solve_for_ev, cmd_args.debug, cmd_args.debug2, cmd_args.debug3, cmd_args.output)
    result = differential_evolution(base_solver.minimize_func, bounds, args=args, popsize=popsize, tol=0.0001,
                                    mutation=(0.01, 1.99), recombination=recombination, workers=workers, maxiter=10000,
                                    init=init)
    print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(MOFO_STLAT_LIST,
                                                                                   zip(*[iter(result.x)] * 3))))
    result_fail_rate = base_solver.minimize_func(result.x, get_mofo_results, MOFO_STLAT_LIST, None, MOFO_MOD_TERMS,
                                                 BALLPARK_TERMS, stat_file_map, ballpark_file_map, game_list,
                                                 team_attrs, None, False, False, False, cmd_args.output)
    print("Result fail rate: {:.2f}%".format(result_fail_rate*100.0))
    print(datetime.datetime.now())


if __name__ == "__main__":
    main()
