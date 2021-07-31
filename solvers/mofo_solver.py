import argparse
import json
import os
import random
import re
import collections

import numpy as np
from scipy.optimize import differential_evolution
import datetime
import sys
from dotenv import load_dotenv

sys.path.append("..")
import requests
from solvers import base_solver
from helpers import parse_mods, adjust_by_pct
from solvers.mofo_ballpark_terms import BALLPARK_TERMS
from solvers.mofo_mod_terms import MOFO_MOD_TERMS
from solvers.mofo_solver_terms import MOFO_TERMS
from solvers.mofo_half_terms import MOFO_HALF_TERMS
import mofo

#MOFO_STLAT_LIST = ("meantragicness", "meanpatheticism", "meanthwackability", "meandivinity", "meanmoxie",
#                   "meanmusclitude", "meanmartyrdom", "maxthwackability", "maxdivinity", "maxmoxie", "maxmusclitude",
#                   "maxmartyrdom", "meanlaserlikeness", "meanbasethirst", "meancontinuation", "meangroundfriction",
#                   "meanindulgence", "maxlaserlikeness", "maxbasethirst", "maxcontinuation", "maxgroundfriction",
#                   "maxindulgence", "unthwackability", "ruthlessness", "overpowerment", "shakespearianism", "coldness",
#                   "meanomniscience", "meantenaciousness", "meanwatchfulness", "meananticapitalism", "meanchasiness",
#                   "maxomniscience", "maxtenaciousness", "maxwatchfulness", "maxanticapitalism", "maxchasiness")


def get_mofo_results(game, season_team_attrs, team_stat_data, pitcher_stat_data, pitchers, terms, mods, ballpark, ballpark_mods, adjusted_stat_data, adjustments):    
    awayMods, homeMods = [], []
    game_attrs = base_solver.get_attrs_from_paired_game(season_team_attrs, game)
    #special_game_attrs = (game_attrs["home"].union(game_attrs["away"])) - base_solver.ALLOWED_IN_BASE
    #if special_game_attrs:        
    #    return 0, 0, 0, 0    
    awayAttrs, homeAttrs = game_attrs["away"], game_attrs["home"]    
    away_game, home_game = game["away"], game["home"]    
    home_rbi, away_rbi = float(away_game["opposing_team_rbi"]), float(home_game["opposing_team_rbi"])           
    awayPitcher, awayTeam = pitchers.get(away_game["pitcher_id"])    
    homePitcher, homeTeam = pitchers.get(home_game["pitcher_id"])        
    awayMods, homeMods = mofo.get_park_mods(ballpark, ballpark_mods)     
    awayodds, homeodds = mofo.get_mofo_playerbased(mods, awayPitcher, homePitcher, awayTeam, homeTeam, awayAttrs, homeAttrs, int(away_game["weather"]), team_stat_data, pitcher_stat_data, terms,
                           awayMods, homeMods, adjusted_stat_data, adjustments)        
    if awayodds == .5:
        return 1, 0, awayodds, homeodds
    if away_rbi == home_rbi and abs(awayodds - homeodds) <= 0.04:        
        return 1, 0, awayodds, homeodds 
    fail = 0 if ((awayodds > .5 and away_rbi > home_rbi) or (awayodds < .5 and away_rbi < home_rbi)) else 1
    return 1, fail, awayodds, homeodds

def get_season_team_attrs(team_attrs, season):
    attrs = []
    for _, season_team_attrs in team_attrs.get(str(season), {}).items():
        attrs.extend(season_team_attrs)
    return attrs

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
    parser.add_argument('--rec', default="0.7", help="recombination to use")
    parser.add_argument('--init', required=False, help="directory to use for init")
    parser.add_argument('--ev', help="solve for best ev instead of fail rate", action="store_true")
    parser.add_argument('--random', help="use random files instead of top", action='store_true')
    parser.add_argument('--worst', help="use worst files instead of top", action='store_true')
    args = parser.parse_args()
    return args


def get_init_values(init_dir, popsize, is_random, is_worst, team_mod_terms, solve_for_ev):        
    if solve_for_ev:
        pattern = re.compile(r'^Net EV = ([-\.\d]*), web EV = ([-\.\d]*), season EV = ([-\.\d]*), mismatches = ([-\.\d]*), dadbets = ([-\.\d]*)$', re.MULTILINE)
        is_worst = True
    else:
        pattern = re.compile(r'^Best so far - Linear fail ([-\.\d]*), worst mod = ([^,]*), ([-\.\d]*), fail rate ([-\.\d]*)\%$', re.MULTILINE)
    results = []
    mods = collections.defaultdict(lambda: {"opp": {}, "same": {}})
    job_ids = {filename.rsplit("-", 1)[0] for filename in os.listdir(init_dir) if filename.endswith("details.txt")}
    if len(job_ids) < popsize:
        raise Exception("Population is set to {} and there are only {} solutions, find more solutions or decrease pop size".format(popsize, len(job_ids)))
    for job_id in job_ids:
        params = []
        with open(os.path.join(init_dir, "{}-terms.csv".format(job_id))) as terms_file:            
            termsplitdata = [d.split(",") for d in terms_file.readlines()[1:] if d]
        for row in termsplitdata:
            params.extend([float(row[1]), float(row[2]), float(row[3])])
        with open(os.path.join(init_dir, "{}-halfterms.csv".format(job_id))) as halfterms_file:            
            halftermsplitdata = [d.split(",") for d in halfterms_file.readlines()[1:] if d]
        for row in halftermsplitdata:
            params.extend([float(row[2])])
        with open(os.path.join(init_dir, "{}-mods.csv".format(job_id))) as mod_file:            
            modsplitdata = [d.split(",") for d in mod_file.readlines()[1:] if d]
        for row in modsplitdata:            
            attr, team, stat = [val for val in row[:3]]                
            mods[attr][stat] = [float(row[3])]    
        for modterm in team_mod_terms:                    
            if modterm.attr in mods:                                
                for stlatname in mods[modterm.attr]:                    
                    if stlatname == modterm.stat:                                                                        
                        params.extend(mods[modterm.attr][stlatname])
            else:                   
                multiplier = random.uniform(0.0, 10.0) - 5.0
                additive = random.uniform(0.0, 1.0)
                exponent = random.uniform(1.0, 1.5)
                params.extend([multiplier, additive, multiplier])        
        with open(os.path.join(init_dir, "{}-ballparkmods.csv".format(job_id))) as park_file:            
            parksplitdata = [d.split(",") for d in park_file.readlines()[1:] if d]
        for row in parksplitdata:
            params.extend([float(row[2]), float(row[3]), float(row[4])])        
        with open(os.path.join(init_dir, "{}-details.txt".format(job_id))) as details_file:                            
            results.append((float(pattern.findall(details_file.read())[0][0]), params))               
    if is_random:
        random.shuffle(results)
    else:
        results.sort(key=lambda x: x[0], reverse=is_worst)       
    final_list = [result[1] for result in results[:popsize]]        
    return np.array(final_list)

def main():
    print(datetime.datetime.now())
    cmd_args = handle_args()        
    mofo_base_terms = [term.stat for term in MOFO_TERMS]
    bounds_park_mods = [modterm.bounds for modterm in BALLPARK_TERMS]
    bounds_park = [item for sublist in bounds_park_mods for item in sublist]
    bounds_mofo_terms = [term.bounds for term in MOFO_TERMS]
    bounds_terms = [item for sublist in bounds_mofo_terms for item in sublist]
    bounds_half_terms = [halfterm.bounds for halfterm in MOFO_HALF_TERMS]
    half_terms = [item for sublist in bounds_half_terms for item in sublist]    
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    ballpark_file_map = base_solver.get_ballpark_map(cmd_args.ballparks)    
    game_list = base_solver.get_games(cmd_args.gamefile)
    current_season = 1
    for row in game_list:
        current_season = int(row["season"]) if (int(row["season"]) > current_season) else current_season    
    previous_season = current_season - 1    
    solve_for_ev = cmd_args.ev
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)    
    team_mod_terms = [modterm for modterm in MOFO_MOD_TERMS if modterm.attr in (get_season_team_attrs(team_attrs, current_season) + get_season_team_attrs(team_attrs, previous_season))]    
    bounds_team_mods = [modterm.bounds for modterm in team_mod_terms]
    bounds_team = [item for sublist in bounds_team_mods for item in sublist]
    bounds = bounds_terms + half_terms + bounds_team + bounds_park      
    
    #establish our baseline    
    if not cmd_args.init or not solve_for_ev:
        number_to_beat = None
    else:
        print("Using initial values. Checking master for number to beat.")
        load_dotenv(dotenv_path="../.env")
        github_token = os.getenv("GITHUB_TOKEN")
        params, modterms = [], []        
        mofourl = os.getenv("MOFO_TERMS")      
        mofoterms = requests.get(mofourl, headers={"Authorization": "token {}".format(github_token)}).text
        params.extend(",".join([",".join(line.split(",")[-3:]) for line in mofoterms.split("\n")[1:] if line]).split(","))           
        modurl = os.getenv("MOFO_MODS")      
        teamterms = requests.get(modurl, headers={"Authorization": "token {}".format(github_token)}).text                    
        teamlines = teamterms.split("\n")[1:]                
        for line in teamlines:   
            splitteamline = line.split(",")
            modterms.append(splitteamline[0])                 
        for modterm in team_mod_terms:            
            if modterm.attr in modterms:
                for line in teamterms.split("\n")[1:]:
                    splitline = line.split(",")
                    if (splitline[0] == modterm.attr) and (splitline[2] == modterm.stat):
                        params.extend(splitline[-3:])
            else:
                params.extend([0,0,1])        
        parkurl = os.getenv("MOFO_BALLPARK_TERMS")      
        parkterms = requests.get(parkurl, headers={"Authorization": "token {}".format(github_token)}).text
        params.extend(",".join([",".join(line.split(",")[-3:]) for line in parkterms.split("\n")[1:] if line]).split(","))   
        baseline_parameters = [float(val) for val in params]
        try:
            number_to_beat = base_solver.minimize_func(baseline_parameters, get_mofo_results, mofo_base_terms, None, team_mod_terms,
                                                     BALLPARK_TERMS, stat_file_map, ballpark_file_map, game_list,
                                                     team_attrs, None, solve_for_ev, False, cmd_args.debug, cmd_args.debug2, cmd_args.debug3, cmd_args.output)            
        except Exception as e:
            print(e)
            number_to_beat = None        

    print("Number to beat = {}".format(number_to_beat))    
    #solver time
    workers = int(cmd_args.workers)        
    popsize = 25     
    #init = get_init_values(cmd_args.init, popsize, cmd_args.random, cmd_args.worst, team_mod_terms, solve_for_ev) if cmd_args.init else 'latinhypercube'
    #experimenting with sobol instead of latinhypercube
    init = get_init_values(cmd_args.init, popsize, cmd_args.random, cmd_args.worst, team_mod_terms, solve_for_ev) if cmd_args.init else 'sobol'
    #print(len(init), ",".join(str(len(s)) for s in init))
    recombination = float(cmd_args.rec)    
    print("Using recombination of {}".format(recombination))
    #if (workers > 2 and solve_for_ev) or (type(init) != str and not solve_for_ev):
    #    recombination = 0.5
    args = (get_mofo_results, mofo_base_terms, MOFO_HALF_TERMS, team_mod_terms, BALLPARK_TERMS, stat_file_map, ballpark_file_map,
            game_list, team_attrs, number_to_beat, solve_for_ev, False, cmd_args.debug, cmd_args.debug2, cmd_args.debug3, cmd_args.output)
    result = differential_evolution(base_solver.minimize_func, bounds, args=args, popsize=popsize, tol=0.0001,
                                    mutation=(0.2, 1.8), recombination=recombination, workers=workers, maxiter=10000,
                                    init=init)
    #print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(mofo_base_terms, zip(*[iter(result.x)] * 3))))

    result_fail_rate = base_solver.minimize_func(result.x, get_mofo_results, mofo_base_terms, MOFO_HALF_TERMS, team_mod_terms,
                                                 BALLPARK_TERMS, stat_file_map, ballpark_file_map, game_list,
                                                 team_attrs, None, solve_for_ev, True, cmd_args.debug, False, False, cmd_args.output)
    #screw it, final file output stuff in here to try and make sure it actually happens
    park_mod_list_size = len(BALLPARK_TERMS) * 3
    team_mod_list_size = len(team_mod_terms)
    special_cases_count = len(MOFO_HALF_TERMS)
    base_mofo_list_size = len(mofo_base_terms) * 3
    terms_output = "\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(mofo_base_terms, zip(*[iter(result.x[:(base_mofo_list_size)])] * 3)))  
    half_output = "\n".join("{},{},{}".format(halfterm.stat, halfterm.event, a) for halfterm, a in zip(MOFO_HALF_TERMS, parameters[base_mofo_list_size:-(team_mod_list_size + park_mod_list_size)]))
    #need to set unused mods to 0, 0, 1
    mods_output = "identifier,team,name,a"
    for mod, a in zip(team_mod_terms, result.x[(base_mofo_list_size + special_cases_count):-park_mod_list_size]):                
        mods_output += "\n{},{},{},{}".format(mod.attr, mod.team, mod.stat, a)        
    #mods_output = "\n".join("{},{},{},{},{},{}".format(modstat.attr, modstat.team, modstat.stat, a, b, c) for modstat, (a, b, c) in zip(mod_list, zip(*[iter(parameters[(((base_mofo_list_size) + special_cases_count)):-(park_mod_list_size)])] * 3)))            
    ballpark_mods_output = "\n".join("{},{},{},{},{}".format(bpstat.ballparkstat, bpstat.playerstat, a, b, c) for bpstat, (a, b, c) in zip(BALLPARK_TERMS, zip(*[iter(result.x[-(park_mod_list_size):])] * 3)))

    outputdir = cmd_args.output
    if solve_for_ev:
        base_solver.write_final(outputdir, "MOFOCoefficients.csv", "name,a,b,c\n" + terms_output)
        base_solver.write_final(outputdir, "MOFOTeamModsCorrection.csv", mods_output)
        base_solver.write_final(outputdir, "MOFOBallparkCoefficients.csv", "ballparkstlat,playerstlat,a,b,c\n" + ballpark_mods_output)
    else:
        base_solver.write_final(outputdir, "FOMOCoefficients.csv", "name,a,b,c\n" + terms_output)
        base_solver.write_final(outputdir, "FOMOHalfTerms.csv", "name,event,a\n" + half_output)
        base_solver.write_final(outputdir, "FOMOTeamModsCorrection.csv", mods_output)
        base_solver.write_final(outputdir, "FOMOBallparkCoefficients.csv", "ballparkstlat,playerstlat,a,b,c\n" + ballpark_mods_output)
    print("Result fail rate: {:.2f}%".format(result_fail_rate*100.0))
    print("Solve complete")
    print(datetime.datetime.now())


if __name__ == "__main__":
    main()
