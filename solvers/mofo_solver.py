import argparse
import json
import os
import random
import re
import collections

import numpy as np
import math
from scipy.optimize import differential_evolution
import datetime
import time
import sys
from dotenv import load_dotenv

sys.path.append("..")
import requests
import numpy as np
from numba import njit, float64
from numba.typed import List
from solvers import base_solver
from helpers import parse_mods, adjust_by_pct, StlatTerm, ParkTerm
from solvers.mofo_ballpark_terms import BALLPARK_TERMS
from solvers.mofo_mod_terms import MOFO_MOD_TERMS
from solvers.mofo_solver_terms import MOFO_TERMS
from solvers.mofo_half_terms import MOFO_HALF_TERMS
import mofo
import helpers

#import tracemalloc
#tracemalloc.start()    

#from numba.core.unsafe.nrt import NRT_get_api
#from numba.core.runtime.nrt import rtsys
#from numba.core.registry import cpu_target
#cpu_target.target_context

def get_mofo_results(gameid, trace_mem, game, awayAttrs, homeAttrs, away_batters, away_active_batters, home_batters, home_active_batters, away_pitcher_stat_data, home_pitcher_stat_data, awayPitcher, homePitcher, terms, mods, ballpark, ballpark_mods, away_adj_def, away_adj_bat, away_adj_run, home_adj_def, home_adj_bat, home_adj_run, adjustments, awayMods, homeMods, away_shelled, away_defense, away_batting, away_running, awayPlayerAttrs, awaypitcherAttrs, home_shelled, home_defense, home_batting, home_running, homePlayerAttrs, homepitcherAttrs):   
    #if trace_mem:
    #    before = tracemalloc.take_snapshot()
    #    before = before.filter_traces((tracemalloc.Filter(True, "*dispatcher.py"),))
    #first, second, preall_mi_alloc, preall_mi_free = rtsys.get_allocation_stats()  
    away_game, home_game = game["away"], game["home"]          
    home_rbi, away_rbi = float(away_game["opposing_team_rbi"]), float(home_game["opposing_team_rbi"])              
    if int(away_game["weather"]) == int(helpers.get_weather_idx("Sun 2")) or int(away_game["weather"]) == int(helpers.get_weather_idx("Black Hole")):
        #print("Tripping our condition for Black Hole or Sun 2 on the real data")
        home_rbi, away_rbi = home_rbi % 10.0, away_rbi % 10.0         
    #if trace_mem:
    #    after = tracemalloc.take_snapshot()
    #    after = after.filter_traces((tracemalloc.Filter(True, "*dispatcher.py"),))        
    #    top_stats = after.compare_to(before, 'lineno')                            
    #    if top_stats[0].size_diff > 0:                        
    #        print("Increase from before hitting get mofo playerbased {}".format(top_stats[0]))                        

    #awayodds, homeodds, away_hits, home_hits, away_homers, home_homers, away_stolen_bases, home_stolen_bases, away_pitcher_ks, home_pitcher_ks, away_pitcher_era, home_pitcher_era = mofo.get_mofo_playerbased(trace_mem, mods, awayPitcher, homePitcher, awayAttrs, homeAttrs, int(away_game["weather"]), away_pitcher_stat_data, home_pitcher_stat_data, terms, away_batters, home_batters, awayMods, homeMods, away_adj_def, away_adj_bat, away_adj_run, home_adj_def, home_adj_bat, home_adj_run, adjustments, away_shelled, away_average_aa_impact, away_average_aaa_impact, away_high_pressure_mod, away_defense, away_batting, away_running, awayPlayerAttrs, awaypitcherAttrs, home_shelled, home_average_aa_impact, home_average_aaa_impact, home_high_pressure_mod, home_defense, home_batting, home_running, homePlayerAttrs, homepitcherAttrs, False)
    
    awayodds, homeodds, away_hits, home_hits, away_homers, home_homers, away_stolen_bases, home_stolen_bases, away_pitcher_ks, home_pitcher_ks, away_pitcher_era, home_pitcher_era = mofo.get_mofo_playerbased(gameid, trace_mem, mods, awayPitcher, homePitcher, awayAttrs, homeAttrs, int(away_game["weather"]), away_pitcher_stat_data, home_pitcher_stat_data, terms, away_batters, away_active_batters, home_batters, home_active_batters, awayMods, homeMods, away_adj_def, away_adj_bat, away_adj_run, home_adj_def, home_adj_bat, home_adj_run, adjustments, away_shelled, away_defense, away_batting, away_running, awayPlayerAttrs, awaypitcherAttrs, home_shelled, home_defense, home_batting, home_running, homePlayerAttrs, homepitcherAttrs, False)

    #if trace_mem:
    #    after_gmpb = tracemalloc.take_snapshot()
    #    after_gmpb = after_gmpb.filter_traces((tracemalloc.Filter(True, "*dispatcher.py"),))        
    #    top_stats = after_gmpb.compare_to(after, 'lineno')                            
    #    if top_stats[0].size_diff > 0:                        
    #        print("Increase from get mofo playerbased {}".format(top_stats[0]))
    #first, second, postall_mi_alloc, postall_mi_free = rtsys.get_allocation_stats()    
    #if ((postall_mi_alloc - preall_mi_alloc) - (postall_mi_free - preall_mi_free)) > 0:
    #    print("Leak prior to return get_mofo_results = {}".format(((postall_mi_alloc - preall_mi_alloc) - (postall_mi_free - preall_mi_free)))) 
    if awayodds == .5:
        return 1, 0, awayodds, homeodds, away_hits, home_hits, away_homers, home_homers, away_stolen_bases, home_stolen_bases, away_pitcher_ks, home_pitcher_ks, away_pitcher_era, home_pitcher_era
    if away_rbi == home_rbi and abs(awayodds - homeodds) <= 0.04:        
        return 1, 0, awayodds, homeodds, away_hits, home_hits, away_homers, home_homers, away_stolen_bases, home_stolen_bases, away_pitcher_ks, home_pitcher_ks, away_pitcher_era, home_pitcher_era
    fail = 0 if ((awayodds > .5 and away_rbi > home_rbi) or (awayodds < .5 and away_rbi < home_rbi)) else 1
    return 1, fail, awayodds, homeodds, away_hits, home_hits, away_homers, home_homers, away_stolen_bases, home_stolen_bases, away_pitcher_ks, home_pitcher_ks, away_pitcher_era, home_pitcher_era

def get_season_team_attrs(team_attrs, season):
    attrs = []
    for _, season_team_attrs in team_attrs.get(str(season), {}).items():
        attrs.extend(season_team_attrs)
    return attrs

def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--statfolder', help="path to stat folder")
    parser.add_argument('--ballparks', help="path to ballparks folder")
    parser.add_argument('--factors', help="path to shared factors file")
    parser.add_argument('--gamefile', help="path to game file")    
    parser.add_argument('--batters', help="path to batter performance file")
    parser.add_argument('--crimes', help="path to stolen bases performance file")    
    parser.add_argument('--debug', help="print output", action='store_true')
    parser.add_argument('--debug2', help="print output", action='store_true')
    parser.add_argument('--debug3', help="print output", action='store_true')
    parser.add_argument('--output', required=False, help="file output directory")
    parser.add_argument('--workers', default="1", help="number of workers to use")
    parser.add_argument('--rec', default="0.7", help="recombination to use")
    parser.add_argument('--init', required=False, help="directory to use for init")
    parser.add_argument('--popsize', default="25", help="population size to use")
    parser.add_argument('--ev', help="solve for best ev instead of fail rate", action="store_true")
    parser.add_argument('--focus', default="all", help="provide focus on a specific snack or all")
    parser.add_argument('--random', help="use random files instead of top", action='store_true')
    parser.add_argument('--worst', help="use worst files instead of top", action='store_true')
    parser.add_argument('--newterms', help="solve only new terms instead of all terms", action='store_true')
    parser.add_argument('--regen', help="generate new solution files using the parameters in the init set and write to output (instead of solving)", action='store_true')
    parser.add_argument('--terms', help="provide terms from file")
    args = parser.parse_args()
    return args


def get_init_values(init_dir, popsize, is_random, is_worst, team_mod_terms, solve_for_ev, regen):        
    if solve_for_ev:
        pattern = re.compile(r'^Net EV = ([-\.\d]*), web EV = ([-\.\d]*), season EV = ([-\.\d]*), mismatches = ([-\.\d]*), dadbets = ([-\.\d]*)$', re.MULTILINE)
        is_worst = True
    else:
        pattern = re.compile(r'^Best so far - Linear fail ([-\.\d]*) \(([-\.\d]*)\% from best errors\), worst mod = ([^,]*), ([-\.\d]*), fail rate ([-\.\d]*)\%, expected ([-\.\d]*)\%$', re.MULTILINE)
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
            #if regen:
            #    params.extend([float(row[2]) * 100.0])        
            #else:
            if float(row[2]) < -1.0:
                params.extend([-1.0])
            else:
                params.extend([float(row[2])])        
        with open(os.path.join(init_dir, "{}-mods.csv".format(job_id))) as mod_file:            
            modsplitdata = [d.split(",") for d in mod_file.readlines()[1:] if d]
        for row in modsplitdata:            
            attr, team, stat = [val for val in row[:3]]                
            mods[attr.lower()][stat.lower()] = [float(row[3])]                      
        for modterm in team_mod_terms:                              
            if modterm.attr.lower() in mods:                                
                for stlatname in mods[modterm.attr.lower()]:                    
                    if stlatname == modterm.stat.lower():                                                                        
                        params.extend(mods[modterm.attr.lower()][stlatname])
            else:                   
                #print("Aha, we're generating too many nonsense values that's why")
                multiplier = random.uniform(0.0, 1.0)                
                params.extend(multiplier)        
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
        worst_value = 0.0
        count_results = 0
        for result in results:
            worst_value = max(result[0], worst_value)
            count_results += 1
            if count_results == popsize:
                break
        print("Highest result in the set = {}".format(worst_value))
    if regen:
        return results
    final_list = [result[1] for result in results[:popsize]]    
    return np.array(final_list)

def main():
    print(datetime.datetime.now())
    cmd_args = handle_args()         
    if cmd_args.newterms:        
        solved_terms, solved_halfterms = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
        solved_ballpark_mods = collections.defaultdict(lambda: {"bpterm": {}})
        with open(os.path.join(cmd_args.terms, "test_terms_file.csv")) as terms_file:            
            termsplitdata = [d.split(",") for d in terms_file.readlines()[1:] if d]
        for row in termsplitdata:
            name = row[0].lower()        
            solved_terms[name] = StlatTerm(float(row[1]), float(row[2]), float(row[3]))
        with open(os.path.join(cmd_args.terms, "test_halfterms_file.csv")) as half_terms_file:            
            halftermsplitdata = [d.split(",") for d in half_terms_file.readlines()[1:] if d]
        for row in halftermsplitdata:
            name, event = row[0].lower(), row[1].lower()
            solved_halfterms[name][event] = float(row[2])
        with open(os.path.join(cmd_args.terms, "test_ballpark_file.csv")) as ballpark_terms_file:            
            ballparktermsplitdata = [d.split(",") for d in ballpark_terms_file.readlines()[1:] if d]
        for row in ballparktermsplitdata:
            bpstlat, stlat = row[0], row[1]
            solved_ballpark_mods[bpstlat][stlat] = ParkTerm(float(row[2]), float(row[3]), float(row[4]))
        solved_mods = None
        mofo_base_terms, bounds_mofo_terms, mofo_base_half_terms, bounds_half_terms, mofo_ballpark_terms, bounds_park_mods = [], [], [], [], [], []
        for term in MOFO_TERMS:
            if term.stat not in solved_terms:
                mofo_base_terms.append(term.stat)
                bounds_mofo_terms.append(term.bounds)
        for halfterm in MOFO_HALF_TERMS:            
            if halfterm.stat in solved_halfterms:
                if halfterm.event in solved_halfterms[halfterm.stat]:
                    continue            
            mofo_base_half_terms.append(halfterm)
            bounds_half_terms.append(halfterm.bounds)        
        for parksterm in BALLPARK_TERMS:            
            if parksterm.ballparkstat in solved_ballpark_mods:
                if parksterm.playerstat in solved_ballpark_mods[parksterm.ballparkstat]:                    
                    continue
            mofo_ballpark_terms.append(parksterm)
            bounds_park_mods.append(parksterm.bounds)
    else:
        solved_terms, solved_halfterms, solved_mods, solved_ballpark_mods = None, None, None, None
        mofo_base_terms = [term.stat for term in MOFO_TERMS] 
        mofo_base_half_terms = [halfterm for halfterm in MOFO_HALF_TERMS]            
        mofo_ballpark_terms = [parksterm for parksterm in BALLPARK_TERMS]
        bounds_mofo_terms = [term.bounds for term in MOFO_TERMS]    
        bounds_park_mods = [parksterm.bounds for parksterm in mofo_ballpark_terms]
        bounds_half_terms = [halfterm.bounds for halfterm in mofo_base_half_terms]
    bounds_park = [item for sublist in bounds_park_mods for item in sublist] if len(bounds_park_mods) > 0 else []
    bounds_terms = [item for sublist in bounds_mofo_terms for item in sublist] if len(bounds_mofo_terms) > 0 else []
    half_terms = [item for sublist in bounds_half_terms for item in sublist] if len(bounds_half_terms) > 0 else []
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    ballpark_file_map = base_solver.get_ballpark_map(cmd_args.ballparks)    
    game_list = base_solver.get_games(cmd_args.gamefile)
    solve_batman_too = False
    batter_list, crimes_list = None, None
    if cmd_args.batters:
        solve_batman_too = True
        batter_list = base_solver.get_batters(cmd_args.batters)
    if cmd_args.crimes:
        crimes_list = base_solver.get_crimes(cmd_args.crimes)
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
                                                     team_attrs, None, solve_for_ev, False, cmd_args.debug, cmd_args.debug2, cmd_args.debug3, cmd_args.output, cmd_args.factors)            
        except Exception as e:
            print(e)
            number_to_beat = None        

    print("Number to beat = {}".format(number_to_beat))    
    #solver time
    workers = int(cmd_args.workers)            
    #init = get_init_values(cmd_args.init, popsize, cmd_args.random, cmd_args.worst, team_mod_terms, solve_for_ev) if cmd_args.init else 'latinhypercube'
    #experimenting with sobol instead of latinhypercube
    popsize = int(cmd_args.popsize)    
    #init = get_init_values(cmd_args.init, popsize, cmd_args.random, cmd_args.worst, team_mod_terms, solve_for_ev, cmd_args.regen) if cmd_args.init else 'halton'    
    init = get_init_values(cmd_args.init, popsize, cmd_args.random, cmd_args.worst, team_mod_terms, solve_for_ev, cmd_args.regen) if cmd_args.init else 'sobol'    
    if cmd_args.regen:
        for new_result in init:
            new_result_params = new_result[1]            
            new_value = base_solver.minimize_func(new_result_params, get_mofo_results, mofo_base_terms, MOFO_HALF_TERMS, team_mod_terms, BALLPARK_TERMS, stat_file_map, ballpark_file_map, game_list, team_attrs, None, solve_for_ev, False, solved_terms, solved_halfterms, solved_mods, solved_ballpark_mods, batter_list, crimes_list, solve_batman_too, popsize, "all", cmd_args.debug, False, False, cmd_args.output, cmd_args.factors, cmd_args.regen)
            print("Regenerated solution: old value {:.0f}, new value {:.0f}".format(new_result[0], new_value))
        print("All files regenerated using new parameters")
    else:
        #print(len(init), ",".join(str(len(s)) for s in init))    
        recombination = float(cmd_args.rec)    
        print("Using recombination of {}".format(recombination))
        #if (workers > 2 and solve_for_ev) or (type(init) != str and not solve_for_ev):
        #    recombination = 0.5
        args = (get_mofo_results, mofo_base_terms, mofo_base_half_terms, team_mod_terms, mofo_ballpark_terms, stat_file_map, ballpark_file_map,
                game_list, team_attrs, number_to_beat, solve_for_ev, False, solved_terms, solved_halfterms, solved_mods, solved_ballpark_mods, batter_list, crimes_list, solve_batman_too, popsize, cmd_args.focus, cmd_args.debug, cmd_args.debug2, cmd_args.debug3, cmd_args.output, cmd_args.factors, cmd_args.regen)
        np.seterr(divide='raise', over='raise', invalid='raise')
        #with np.errstate(over='raise'):
        #result = differential_evolution(base_solver.minimize_func, bounds, args=args, popsize=popsize, tol=0.1,
        #                            mutation=0.9, recombination=recombination, workers=workers, maxiter=2,
        #                            init='latinhypercube')
        result = differential_evolution(base_solver.minimize_func, bounds, args=args, popsize=popsize, tol=0.0001,
                                    mutation=(0.1, 1.9), recombination=recombination, workers=workers, maxiter=10000,
                                    init=init)
        #print("\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(mofo_base_terms, zip(*[iter(result.x)] * 3))))

        result_fail_rate = base_solver.minimize_func(result.x, get_mofo_results, mofo_base_terms, mofo_base_half_terms, team_mod_terms,
                                                    mofo_ballpark_terms, stat_file_map, ballpark_file_map, game_list,
                                                    team_attrs, None, solve_for_ev, True, solved_terms, solved_halfterms, solved_mods, solved_ballpark_mods, batter_list, crimes_list, solve_batman_too, popsize, "all", cmd_args.debug, False, False, cmd_args.output, cmd_args.factors, cmd_args.regen)
        #screw it, final file output stuff in here to try and make sure it actually happens
        park_mod_list_size = len(mofo_ballpark_terms) * 3
        team_mod_list_size = len(team_mod_terms)
        special_cases_count = len(mofo_base_half_terms)
        base_mofo_list_size = len(mofo_base_terms) * 3
        total_parameters = len(result.x)    
    
        terms = solved_terms if solved_terms else collections.defaultdict(lambda: {})    
        if base_mofo_list_size > 0:
            for stat, (a, b, c) in zip(mofo_base_terms, zip(*[iter(result.x[:base_mofo_list_size])] * 3)):
                use_a = 0.0 if (math.isnan(a)) else a            
                use_b = 0.0 if (math.isnan(b)) else b            
                use_c = 0.0 if (math.isnan(c)) else c
                terms[stat] = StlatTerm(use_a, use_b, use_c)        
        mods = solved_mods if solved_mods else collections.defaultdict(lambda: {"opp": {}, "same": {}})    
        ballpark_mods = solved_ballpark_mods if solved_ballpark_mods else collections.defaultdict(lambda: {"bpterm": {}})
        half_stlats = solved_halfterms if solved_halfterms else collections.defaultdict(lambda: {})
        mod_mode = True
        if team_mod_list_size > 0:
            for mod, a in zip(team_mod_terms, result.x[(base_mofo_list_size + special_cases_count):(total_parameters-park_mod_list_size)]):                  
                use_a = 0.0 if (math.isnan(a)) else a                      
                mods[mod.attr.lower()][mod.team.lower()][mod.stat.lower()] = use_a
        if park_mod_list_size > 0:
            for bp, (a, b, c) in zip(mofo_ballpark_terms, zip(*[iter(result.x[-park_mod_list_size:])] * 3)):   
                use_a = 0.0 if (math.isnan(a)) else a            
                use_b = 0.0 if (math.isnan(b)) else b            
                use_c = 0.0 if (math.isnan(c)) else c
                ballpark_mods[bp.ballparkstat.lower()][bp.playerstat.lower()] = ParkTerm(use_a, use_b, use_c)                   
        if special_cases_count > 0:
            for halfterm, a in zip(mofo_base_half_terms, result.x[base_mofo_list_size:-(team_mod_list_size + park_mod_list_size)]):        
                use_a = 0.0 if (math.isnan(a)) else a            
                half_stlats[halfterm.stat.lower()][halfterm.event.lower()] = use_a       

        terms_output = "name,a,b,c"
        for stat, stlatterm in terms.items():                
            if type(stlatterm) == dict:
                continue
            terms_output += "\n{},{},{},{}".format(stat, stlatterm.a, stlatterm.b, stlatterm.c)                
        half_output = "name,event,a"            
        for stat in half_stlats:
            for event in half_stlats[stat]:
                halfstat = half_stlats[stat][event]
                if type(halfstat) == dict:
                    continue
                half_output += "\n{},{},{}".format(stat, event, half_stlats[stat][event])            
        mods_output = "identifier,team,name,a"
        for attr in mods:                                
            for team in mods[attr]:
                for stat in mods[attr][team]:
                    modterm = mods[attr][team][stat]
                    if type(modterm) == dict:
                        continue
                    mods_output += "\n{},{},{},{}".format(attr, team, stat, modterm)            
        ballpark_mods_output = "ballparkstlat,playerstlat,a,b,c"
        for bpstat in ballpark_mods:                
            for playerstat in ballpark_mods[bpstat]:                    
                bpterm = ballpark_mods[bpstat][playerstat]
                if type(bpterm) == dict:
                    continue
                ballpark_mods_output +="\n{},{},{},{},{}".format(bpstat, playerstat, bpterm.a, bpterm.b, bpterm.c)

        outputdir = cmd_args.output
        if solve_for_ev:
            base_solver.write_final(outputdir, "MOFOCoefficients.csv", terms_output)
            base_solver.write_final(outputdir, "MOFOTeamModsCorrection.csv", mods_output)
            base_solver.write_final(outputdir, "MOFOBallparkCoefficients.csv", ballpark_mods_output)
        else:
            base_solver.write_final(outputdir, "FOMOCoefficients.csv", terms_output)
            base_solver.write_final(outputdir, "FOMOHalfTerms.csv", half_output)
            base_solver.write_final(outputdir, "FOMOTeamModsCorrection.csv", mods_output)
            base_solver.write_final(outputdir, "FOMOBallparkCoefficients.csv", ballpark_mods_output)
        print("Result fail rate: {:.2f}%".format(result_fail_rate*100.0))        
        print("Solve complete")
        print(datetime.datetime.now())


if __name__ == "__main__":
    main()
