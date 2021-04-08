import collections
import csv
import sys
import time
import math
import statistics
import datetime
import json
import os
import re
import uuid
import copy
from glob import glob

from helpers import StlatTerm, ParkTerm, get_weather_idx
from idolthoughts import load_stat_data, load_stat_data_pid
from mofo import get_mods
from batman import get_team_atbats, get_batman_mods

STAT_CACHE = {}
BALLPARK_CACHE = {}
GAME_CACHE = {}
BATTER_CACHE = {}

BEST_RESULT = 8000000000000.0
BEST_FAIL_RATE = 1.0
BEST_LINEAR_ERROR = 1.0
EXACT_FAILS = 0
BEST_UNEXVAR_ERROR = -100.0
BEST_EXACT = 0.0
BEST_FAILCOUNT = 10000000000.0
CURRENT_ITERATION = 1
LAST_CHECKTIME = datetime.datetime.now()
BEST_QUARTER_FAIL = 1.0
TOTAL_GAME_COUNTER = 0
MAX_OBSERVED_DIFFERENCE = 0.0
BEST_UNMOD = 1000000000000.0
WORST_ERROR = 1000000000.0
MAX_INTEREST = 1000000000.0
BASELINE_ERROR = 1000000000.0
PASSED_GAMES = 0.25
REJECTS = 0
ALL_UNMOD_GAMES = 0
ALL_GAMES = 0
BEST_AGG_FAIL_RATE = 0
LAST_BEST = 1000000000.0
PREVIOUS_LAST_BEST = 1000000000.0
LAST_DAY_RANGE = 1
LAST_SEASON_RANGE = 1
MOD_BASELINE = False
EARLY_REJECT = False
BEST_MOD_RATES = {}
ALL_MOD_GAMES = {}
LINE_JUMP_GAMES = {}
HAS_GAMES = {}
LAST_ITERATION_TIME = datetime.datetime.now()

ALLOWED_IN_BASE = {"AFFINITY_FOR_CROWS", "GROWTH", "EXTRA_STRIKE", "LOVE", "O_NO", "BASE_INSTINCTS", "TRAVELING", "HIGH_PRESSURE"}
ALLOWED_IN_BASE_BATMAN = {"AFFINITY_FOR_CROWS", "GROWTH", "EXTRA_STRIKE", "LOVE", "O_NO", "BASE_INSTINCTS", "TRAVELING", "HIGH_PRESSURE"}
FORCE_REGEN = {"AFFINITY_FOR_CROWS", "GROWTH", "TRAVELING"}

BIRD_WEATHER = get_weather_idx("Birds")
FLOOD_WEATHER = get_weather_idx("Flooding")


def get_pitcher_id_lookup(filename):
    with open(filename) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    return {row["id"]: (row["name"], row["team"]) for row in filedata if row["position"] == "rotation"}

def get_player_id_lookup(filename):
    with open(filename) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    return {row["id"]: (row["name"], row["team"]) for row in filedata}

def get_games(filename):
    with open(filename) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    return filedata

def get_batters(filename):
    with open(filename) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    return filedata


def get_ballpark_map(ballpark_folder):
    filelist = [f for f in os.listdir(ballpark_folder) if os.path.isfile(os.path.join(ballpark_folder, f))]
    results = {}
    for filename in filelist:        
        match = re.match(r'stadiumsS([0-9]*)preD([0-9]*).json', filename)
        if match:
            season, day = match.groups()
            results[(int(season), int(day))] = os.path.join(ballpark_folder, filename)
    return results


def pair_games(games):
    gamelist = collections.defaultdict(lambda: [])
    for game in games:
        gamelist[game["game_id"]].append(game)
    results = []
    for game_id, games in gamelist.items():
        if len(games) == 2 and games[0]["pitcher_is_home"] != games[1]["pitcher_is_home"]:
            results.append({("home" if game["pitcher_is_home"] == "True" else "away"): game for game in games})
    return results


def get_stat_file_map(stat_folder):
    filelist = [y for x in os.walk(stat_folder) for y in glob(os.path.join(x[0], '*.csv'))]
    results = {}
    for filepath in filelist:        
        filename = filepath.split(os.sep)[-1]
        match = re.match(r'outputS([0-9]*)preD([0-9]*).csv', filename)
        if match:
            season, day = match.groups()
            results[(int(season), int(day))] = filepath
    return results


def get_team_name(team_id, season, day, team_lookup={}):
    if not team_lookup:
        with open('team_lookup.json') as f:
            team_lookup.update(json.load(f))    
    results = team_lookup[team_id]
    if len(results) == 1:        
        return results[0][2]
    last_result = results[0]    
    for result_season, result_day, team_name in results:
        if result_season > season or (result_season == season and result_day > day):            
            return last_result[2]
        last_result = [result_season, result_day, team_name]        
    return last_result[2]


def get_schedule_from_paired_games(paired_games, season, day):
    return [{
        "homeTeamName": get_team_name(game["home"]["team_id"], season, day),
        "awayTeamName": get_team_name(game["away"]["team_id"], season, day),
        "weather": int(game["home"]["weather"]),
    } for game in paired_games]


def should_regen(day_mods):
    return any([d in day_mods for d in FORCE_REGEN])


def get_attrs_from_game(season_team_attrs, game, side):
    attrs = set()
    team_attrs = season_team_attrs.get(get_team_name(game["team_id"], int(game["season"]), int(game["day"])), [])
    for attr in team_attrs:
        if (attr == "TRAVELING" and side != "away") or (
                attr == "AFFINITY_FOR_CROWS" and int(game["weather"]) != BIRD_WEATHER) or (
                attr == "HIGH_PRESSURE" and int(game["weather"]) != FLOOD_WEATHER):
            continue
        attrs.add(attr)
    return attrs


def get_attrs_from_paired_game(season_team_attrs, games):
    return {side: get_attrs_from_game(season_team_attrs, games[side], side) for side in ("home", "away")}


def get_attrs_from_paired_games(season_team_attrs, paired_games):
    attrs = set()
    for games in paired_games:
        attrs.update(get_attrs_from_paired_game(season_team_attrs, games))
    return attrs


def debug_print(s, debug, run_id):
    if debug:
        print("{} - {}".format(run_id, s))

def calc_linear_unex_error(vals, wins_losses, games):
    wins, idx = 0, 0
    high_val, low_val, high_ratio, low_ratio, error, max_error, min_error, max_error_val, max_error_ratio = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 150.0, 0.0, 0.0
    max_tracked_error, min_tracked_error = 0.0, 150.0
    high_val = vals[idx]
    major_errors = []
    error_shape = []
    while (high_ratio < 0.5 and idx < len(vals)):        
        wins += wins_losses[idx]
        idx += 1        
        high_ratio = (float(wins) / float(games))
    while (idx < len(vals)):        
        wins += wins_losses[idx]
        high_val = vals[idx] * 100.0
        high_ratio = (float(wins) / float(games)) * 100.0
        low_ratio = 100.0 - high_ratio
        low_val = 100.0 - high_val      
        if high_ratio >= 50.0000:                 
            if high_val < 50.0000:                
                error += ((high_ratio - high_val) + (100.0 - high_val)) ** 2                                            
                major_errors.append(int(high_ratio))           
            elif high_ratio < 85.0000:
                error += (high_ratio - high_val) ** 2
            max_error_val = high_val if (max(high_ratio, high_val) - min(high_ratio, high_val) + low_val > max_tracked_error) else max_error_val
            max_error_ratio = high_ratio if (max(high_ratio, high_val) - min(high_ratio, high_val) + low_val > max_tracked_error) else max_error_ratio            
            max_error = (max(high_ratio, high_val) - min(high_ratio, high_val)) if (max(high_ratio, high_val) - min(high_ratio, high_val) + low_val > max_tracked_error) else max_error
            if (max(high_ratio, high_val) - min(high_ratio, high_val) + low_val > max_tracked_error):
               error_shape.append((max_error / high_ratio) * 100.0)
            min_error = (max(high_ratio, high_val) - min(high_ratio, high_val)) if (max(high_ratio, high_val) - min(high_ratio, high_val) < min_error) else min_error            
            max_tracked_error = (max(high_ratio, high_val) - min(high_ratio, high_val) + low_val) if (max(high_ratio, high_val) - min(high_ratio, high_val) + low_val > max_tracked_error) else max_tracked_error
            min_tracked_error = (max(high_ratio, high_val) - min(high_ratio, high_val) + low_val) if (max(high_ratio, high_val) - min(high_ratio, high_val) + low_val < min_tracked_error) else min_tracked_error                
        if low_ratio <= 50.0000:            
            if low_val > 50.0000:                
                error += ((low_ratio - low_val) + low_val) ** 2
                major_errors.append(int(low_ratio))
            elif low_ratio > 15.0000:
                error += (low_ratio - low_val) ** 2
            max_error_val = low_val if (max(low_ratio, low_val) - min(low_ratio, low_val) + low_val > max_tracked_error) else max_error_val
            max_error_ratio = low_ratio if (max(low_ratio, low_val) - min(low_ratio, low_val) + low_val > max_tracked_error) else max_error_ratio            
            max_error = (max(low_ratio, low_val) - min(low_ratio, low_val)) if (max(low_ratio, low_val) - min(low_ratio, low_val) + low_val > max_tracked_error) else max_error
            if (max(low_ratio, low_val) - min(low_ratio, low_val) + low_val > max_tracked_error):
               error_shape.append((max_error / low_ratio) * 100.0)
            min_error = (max(low_ratio, low_val) - min(low_ratio, low_val)) if (max(low_ratio, low_val) - min(low_ratio, low_val) < min_error) else min_error            
            max_tracked_error = (max(low_ratio, low_val) - min(low_ratio, low_val) + low_ratio) if (max(low_ratio, low_val) - min(low_ratio, low_val) + low_val > max_tracked_error) else max_tracked_error
            min_tracked_error = (max(low_ratio, low_val) - min(low_ratio, low_val) + low_ratio) if (max(low_ratio, low_val) - min(low_ratio, low_val) + low_val < min_tracked_error) else min_tracked_error
        idx += 1
    return error, max_error, min_error, max_error_val, max_error_ratio, major_errors, error_shape


def write_file(outputdir, run_id, filename, content):
    with open(os.path.join(outputdir, "{}-{}".format(run_id, filename)), "w") as f:
        f.write(content)


def write_parameters(outputdir, run_id, filename, parameters):
    with open(os.path.join(outputdir, "{}-{}".format(run_id, filename)), "w") as f:
        json.dump(list(parameters), f)


#for mofo and k9
def minimize_func(parameters, *data):
    run_id = uuid.uuid4()
    starttime = datetime.datetime.now()
    global BEST_RESULT
    global CURRENT_ITERATION
    global BEST_FAIL_RATE
    global BEST_LINEAR_ERROR
    global BEST_EXACT
    global BEST_FAILCOUNT    
    global BEST_UNMOD    
    global LAST_CHECKTIME
    global BEST_QUARTER_FAIL
    global TOTAL_GAME_COUNTER
    global MAX_OBSERVED_DIFFERENCE
    global BEST_MOD_RATES        
    global ALL_MOD_GAMES
    global ALL_UNMOD_GAMES
    global ALL_GAMES
    global HAS_GAMES
    global WORST_ERROR
    global LAST_ITERATION_TIME
    global PASSED_GAMES    
    global LINE_JUMP_GAMES    
    global PREVIOUS_LAST_BEST
    global BEST_AGG_FAIL_RATE
    global LAST_BEST
    global LAST_DAY_RANGE
    global LAST_SEASON_RANGE
    global REJECTS
    global EARLY_REJECT
    calc_func, stlat_list, special_case_list, mod_list, ballpark_list, stat_file_map, ballpark_file_map, game_list, team_attrs, debug, debug2, debug3, outputdir = data
    debug_print("func start: {}".format(starttime), debug3, run_id)
    special_case_list = special_case_list or []            
    park_mod_list_size = len(ballpark_list) * 3
    team_mod_list_size = len(mod_list) * 3
    special_cases_count = len(special_case_list)
    base_mofo_list_size = len(parameters) - special_cases_count - park_mod_list_size - team_mod_list_size
    terms = {stat: StlatTerm(a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(parameters[:base_mofo_list_size])] * 3))}
    mods = collections.defaultdict(lambda: {"opp": {}, "same": {}})
    ballpark_mods = collections.defaultdict(lambda: {"bpterm": {}})
    mod_mode = True        
    for mod, (a, b, c) in zip(mod_list, zip(*[iter(parameters[(base_mofo_list_size + special_cases_count):-park_mod_list_size])] * 3)):                
        mods[mod.attr.lower()][mod.team.lower()][mod.stat.lower()] = StlatTerm(a, b, c)      
    for bp, (a, b, c) in zip(ballpark_list, zip(*[iter(parameters[-park_mod_list_size:])] * 3)):        
        ballpark_mods[bp.ballparkstat.lower()][bp.playerstat.lower()] = ParkTerm(a, b, c)           
    special_cases = parameters[base_mofo_list_size:-(team_mod_list_size + park_mod_list_size)] if special_case_list else []
    game_counter, fail_counter, season_game_counter, half_fail_counter, pass_exact, pass_within_one, pass_within_two, pass_within_three, pass_within_four = 0, 0, 0, 1000000000, 0, 0, 0, 0, 0
    quarter_fail = 100.0
    linear_fail = 100.0
    linear_error, check_fail_rate = 0.0, 0.0
    love_rate, instinct_rate, ono_rate, wip_rate, exk_rate, exb_rate, unmod_rate = 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0
    k9_max_err, k9_min_err, ljg_passed = 0, 0, 0
    mod_fails, mod_games, mod_rates = {}, {}, {}
    reorder_keys = {}
    multi_mod_fails, multi_mod_games, mvm_fails, mvm_games, ljg_fail_savings = 0, 0, 0, 0, 0
    unmod_fails, unmod_games, unmod_rate = 0, 0, 0.0
    reject_solution, viability_unchecked, new_pass, addfails = False, True, False, False
    line_jumpers = {}
    reorder_failsfirst = {}
    all_vals = []
    win_loss = []  
    early_vals = []
    
    #let some games jump the line        
    if EARLY_REJECT:
        fail_threshold = LAST_BEST
    else:
        fail_threshold = min(LAST_BEST, len(LINE_JUMP_GAMES) * BEST_FAIL_RATE)
    for gameid in LINE_JUMP_GAMES:   
        if reject_solution:
            break
        current_best_mod_rates = BEST_MOD_RATES.values()            
        game = LINE_JUMP_GAMES[gameid]
        season = int(game["away"]["season"])
        day = int(game["away"]["day"])
        pitchers, team_stat_data, pitcher_stat_data, last_stat_filename = None, None, None, None
        season_team_attrs = team_attrs.get(str(season), {})
        season_days = 0                
        cached_games = GAME_CACHE.get((season, day))                            
        games = cached_games
        season_days += 1
        paired_games = pair_games(games)
        schedule = get_schedule_from_paired_games(paired_games, season, day)
        day_mods = get_attrs_from_paired_games(season_team_attrs, paired_games)
        cached_stats = STAT_CACHE.get((season, day))
        team_stat_data, pitcher_stat_data, pitchers = cached_stats                        
        cached_ballparks = BALLPARK_CACHE.get((season, day))          
        ballparks = cached_ballparks          
        ballpark = ballparks.get(game["home"]["team_id"], collections.defaultdict(lambda: 0.5))
        game_attrs = get_attrs_from_paired_game(season_team_attrs, game)
        awayAttrs, homeAttrs = game_attrs["away"], game_attrs["home"]                
        special_game_attrs = (homeAttrs.union(awayAttrs)) - ALLOWED_IN_BASE    
        game_game_counter, game_fail_counter, game_away_val, game_home_val = calc_func(game, season_team_attrs, team_stat_data, pitcher_stat_data, pitchers, terms, special_cases, mods, ballpark, ballpark_mods)                        
        game_counter += game_game_counter
        fail_counter += game_fail_counter  
        if game_game_counter > 0:    
            reorder_keys[game["away"]["game_id"]] = game                                
            if game_fail_counter > 0:
                line_jumpers[game["away"]["game_id"]] = game                
            else:                
                new_pass = True
                ljg_passed += PASSED_GAMES
                if ljg_passed >= 1.0:
                    line_jumpers[game["away"]["game_id"]] = game                
                    ljg_passed -= 1               
        if fail_counter >= fail_threshold:                                          
            reject_solution = True                        
            REJECTS += 1                                        
            break
        if game_game_counter == 1:
            all_vals.append(game_away_val)   
            if (game_away_val > 0.5 and game_fail_counter == 0) or (game_away_val < 0.5 and game_fail_counter == 1):
                win_loss.append(1)
                win_loss.append(0)
            else:
                win_loss.append(0)
                win_loss.append(1)
            all_vals.append(game_home_val)
            if mod_mode:
                game_attrs = get_attrs_from_paired_game(season_team_attrs, game)                        
                awayAttrs = game_attrs["away"]
                homeAttrs = game_attrs["home"]
                awayMods, homeMods = 0, 0
                lowerAwayAttrs = [attr.lower() for attr in awayAttrs]
                lowerHomeAttrs = [attr.lower() for attr in homeAttrs]
                for name in lowerAwayAttrs:  
                    if name.upper() in FORCE_REGEN:
                        continue
                    if name not in mod_games:
                        mod_fails[name] = 0
                        mod_games[name] = 0
                    mod_fails[name] += game_fail_counter
                    mod_games[name] += game_game_counter                    
                    check_fail_rate = (mod_fails[name] / ALL_MOD_GAMES[name]) * 100.0
                    if check_fail_rate > max(BEST_UNMOD, max(current_best_mod_rates)):                             
                        reject_solution = True
                        REJECTS += 1     
                        break
                    awayMods += 1                          
                if check_fail_rate > max(BEST_UNMOD, max(current_best_mod_rates)):
                    break
                if awayMods > 1:
                    multi_mod_fails += game_fail_counter
                    multi_mod_games += game_game_counter
                for name in lowerHomeAttrs:
                    if name.upper() in FORCE_REGEN:
                        continue
                    if name not in mod_games:
                        mod_fails[name] = 0
                        mod_games[name] = 0
                    mod_fails[name] += game_fail_counter
                    mod_games[name] += game_game_counter
                    check_fail_rate = (mod_fails[name] / ALL_MOD_GAMES[name]) * 100.0
                    if check_fail_rate > max(BEST_UNMOD, max(current_best_mod_rates)):                        
                        reject_solution = True
                        REJECTS += 1     
                        break
                    homeMods += 1  
                if check_fail_rate > max(BEST_UNMOD, max(current_best_mod_rates)):
                    break
                if homeMods > 1:
                    multi_mod_fails += game_fail_counter
                    multi_mod_games += game_game_counter
                if awayMods > 0 and homeMods > 0:
                    mvm_fails += game_fail_counter
                    mvm_games += game_game_counter  
                elif awayMods == 0 and homeMods == 0:
                    unmod_fails += game_fail_counter  
                    unmod_games += game_game_counter
                    check_fail_rate = (unmod_fails / ALL_UNMOD_GAMES) * 100.0
                    if check_fail_rate > max(BEST_UNMOD, max(current_best_mod_rates)):                        
                        reject_solution = True
                        REJECTS += 1
                        break    
                if check_fail_rate > max(BEST_UNMOD, max(current_best_mod_rates)):
                    break                 
    
    if CURRENT_ITERATION > 1:        
        if not reject_solution:                        
            LAST_BEST = fail_counter     
            EARLY_REJECT = False
            #print("No rejects from within line-jump games, {} games in set, {} games evaluated, {} max fails, {} this run".format(len(LINE_JUMP_GAMES), game_counter, int(fail_threshold), fail_counter))    
        else:     
            #print("Rejected from within line-jump games, {} games in set, {} games evaluated, {} max fails, {} this run, {} last best".format(len(LINE_JUMP_GAMES), game_counter, int(fail_threshold), fail_counter, int(LAST_BEST)))                    
            if fail_counter >= fail_threshold:
                EARLY_REJECT = True
                LAST_BEST = fail_counter
                #print("Next set should have {} games".format(game_counter))
                LINE_JUMP_GAMES.clear()
                LINE_JUMP_GAMES = reorder_keys            
            else:
                EARLY_REJECT = False
    seasonrange = reversed(range(12, 15))
    dayrange = range(1, 125)
    if not reject_solution:
        #if LAST_SEASON_RANGE == 0:
            #if LAST_DAY_RANGE == 1:
             #   LAST_DAY_RANGE = 0
            #else:
             #   LAST_DAY_RANGE = 1    

        if LAST_SEASON_RANGE == 0:
            seasonrange = range(12, 15)            
        else:
            seasonrange = reversed(range(12, 15))            
        #if LAST_DAY_RANGE == 0:
         #   dayrange = range(1, 125)
        #else:
         #   dayrange = reversed(range(1, 125))

        LAST_SEASON_RANGE = 1 if (LAST_SEASON_RANGE == 0) else 0    

    for season in seasonrange:
        if reject_solution:            
            break
        # if (season in HAS_GAMES and not HAS_GAMES[season]) or season < 12:
        if (season in HAS_GAMES and not HAS_GAMES[season]):
            continue
        season_start = datetime.datetime.now()
        debug_print("season {} start: {}".format(season, season_start), debug3, run_id)
        pitchers, team_stat_data, pitcher_stat_data, last_stat_filename, ballparks = (None, ) * 5
        season_team_attrs = team_attrs.get(str(season), {})
        season_days = 0        
        for day in dayrange:            
            if reject_solution:                
                break
            is_cached = False
            cached_games = GAME_CACHE.get((season, day))
            if cached_games:
                games = cached_games
                is_cached = True
            else:
                if type(cached_games) == list:                    
                    continue
                games = [row for row in game_list if row["season"] == str(season) and row["day"] == str(day)]
                if not games:
                    GAME_CACHE[(season, day)] = []                    
                    continue                
            season_days += 1
            paired_games = pair_games(games)
            schedule = get_schedule_from_paired_games(paired_games, season, day)
            day_mods = get_attrs_from_paired_games(season_team_attrs, paired_games)            
            cached_stats = STAT_CACHE.get((season, day))
            if cached_stats:
                team_stat_data, pitcher_stat_data, pitchers = cached_stats
            else:
                stat_filename = stat_file_map.get((season, day))
                if stat_filename:
                    last_stat_filename = stat_filename
                    pitchers = get_pitcher_id_lookup(stat_filename)
                    team_stat_data, pitcher_stat_data = load_stat_data(stat_filename, schedule, day, season_team_attrs)
                elif should_regen(day_mods):
                    pitchers = get_pitcher_id_lookup(last_stat_filename)
                    team_stat_data, pitcher_stat_data = load_stat_data(last_stat_filename, schedule, day, season_team_attrs)
                STAT_CACHE[(season, day)] = (team_stat_data, pitcher_stat_data, pitchers)
            if not pitchers:
                raise Exception("No stat file found")
            cached_ballparks = BALLPARK_CACHE.get((season, day))
            if cached_ballparks is None:
                ballpark_filename = ballpark_file_map.get((season, day))
                if CURRENT_ITERATION > 1:
                    print("Ballparks not cached, season {}, day {}".format(season, day))
                if ballpark_filename:
                    with open(ballpark_filename) as f:
                        ballparks = json.load(f)
                else:
                    if ballparks is None:  # this should use the previous value of ballparks by default, use default if not
                        ballparks = collections.defaultdict(lambda: collections.defaultdict(lambda: 0.5))
                BALLPARK_CACHE[(season, day)] = ballparks
            else:
                ballparks = cached_ballparks                
            good_game_list = []
            for game in paired_games:
                if game["away"]["game_id"] in LINE_JUMP_GAMES:
                    continue
                ballpark = ballparks.get(game["home"]["team_id"], collections.defaultdict(lambda: 0.5))
                game_game_counter, game_fail_counter, game_away_val, game_home_val = calc_func(game, season_team_attrs, team_stat_data, pitcher_stat_data, pitchers, terms, special_cases, mods, ballpark, ballpark_mods)                
                if not is_cached and game_game_counter:
                    good_game_list.extend([game["home"], game["away"]])
                    HAS_GAMES[season] = True
                game_counter += game_game_counter
                fail_counter += game_fail_counter  
                if game_game_counter > 0:
                    if game_fail_counter > 0:
                        line_jumpers[game["away"]["game_id"]] = game      
                    else:
                        ljg_passed += PASSED_GAMES
                        if ljg_passed >= 1:
                            line_jumpers[game["away"]["game_id"]] = game                
                            ljg_passed -= 1
                if fail_counter >= BEST_FAILCOUNT:                                      
                    reject_solution = True           
                    #print("Rejecting for fail count reasons")                    
                    #prior_games = len(LINE_JUMP_GAMES)
                    #for gameid in line_jumpers:
                        #newgame = line_jumpers[gameid]                        
                        #if newgame["away"]["game_id"] not in LINE_JUMP_GAMES:
                            #LINE_JUMP_GAMES[newgame["away"]["game_id"]] = newgame  
                    #added_games = len(LINE_JUMP_GAMES) - prior_games
                    #LAST_BEST += added_games if (added_games > 0) else 0
                    LINE_JUMP_GAMES.clear()
                    LINE_JUMP_GAMES = line_jumpers                    
                    LAST_BEST = BEST_FAILCOUNT
                    #LINE_JUMP_GAMES[game["away"]["game_id"]] = game
                    #LAST_BEST += 1
                    REJECTS += 1
                    break                
                if game_game_counter == 1:
                    all_vals.append(game_away_val)   
                    if (game_away_val > 0.5 and game_fail_counter == 0) or (game_away_val < 0.5 and game_fail_counter == 1):
                        win_loss.append(1)
                        win_loss.append(0)
                    else:
                        win_loss.append(0)
                        win_loss.append(1)
                    all_vals.append(game_home_val)
                    if mod_mode:
                        game_attrs = get_attrs_from_paired_game(season_team_attrs, game)                        
                        awayAttrs = game_attrs["away"]
                        homeAttrs = game_attrs["home"]
                        awayMods, homeMods = 0, 0
                        lowerAwayAttrs = [attr.lower() for attr in awayAttrs]
                        lowerHomeAttrs = [attr.lower() for attr in homeAttrs]
                        for name in lowerAwayAttrs:  
                            if name.upper() in FORCE_REGEN:
                                continue
                            if name not in mod_games:
                                mod_fails[name] = 0
                                mod_games[name] = 0
                            mod_fails[name] += game_fail_counter
                            mod_games[name] += game_game_counter
                            if CURRENT_ITERATION > 1:
                                current_best_mod_rates = BEST_MOD_RATES.values()                                
                                check_fail_rate = (mod_fails[name] / ALL_MOD_GAMES[name]) * 100.0
                                if check_fail_rate > max(BEST_UNMOD, max(current_best_mod_rates)):
                                    reject_solution = True 
                                    #print("Rejecting for mod reasons")
                                    #LINE_JUMP_GAMES[game["away"]["game_id"]] = game
                                    LINE_JUMP_GAMES.clear()
                                    LINE_JUMP_GAMES = line_jumpers
                                    LAST_BEST += (fail_counter - LAST_BEST)
                                    REJECTS += 1     
                                    break
                            awayMods += 1  
                        if reject_solution:
                            break
                        if awayMods > 1:
                            multi_mod_fails += game_fail_counter
                            multi_mod_games += game_game_counter
                        for name in lowerHomeAttrs:
                            if name.upper() in FORCE_REGEN:
                                continue
                            if name not in mod_games:
                                mod_fails[name] = 0
                                mod_games[name] = 0
                            mod_fails[name] += game_fail_counter
                            mod_games[name] += game_game_counter
                            if CURRENT_ITERATION > 1:
                                current_best_mod_rates = BEST_MOD_RATES.values()                                
                                check_fail_rate = (mod_fails[name] / ALL_MOD_GAMES[name]) * 100.0
                                if check_fail_rate > max(BEST_UNMOD, max(current_best_mod_rates)):
                                    reject_solution = True     
                                    #print("Rejecting for mod reasons")
                                    #LINE_JUMP_GAMES[game["away"]["game_id"]] = game
                                    LINE_JUMP_GAMES.clear()
                                    LINE_JUMP_GAMES = line_jumpers
                                    LAST_BEST += (fail_counter - LAST_BEST)
                                    REJECTS += 1     
                                    break
                            homeMods += 1      
                        if reject_solution:
                            break
                        if homeMods > 1:
                            multi_mod_fails += game_fail_counter
                            multi_mod_games += game_game_counter
                        if awayMods > 0 and homeMods > 0:
                            mvm_fails += game_fail_counter
                            mvm_games += game_game_counter  
                        elif awayMods == 0 and homeMods == 0:
                            unmod_fails += game_fail_counter  
                            unmod_games += game_game_counter                          
                            if CURRENT_ITERATION > 1:
                                current_best_mod_rates = BEST_MOD_RATES.values()
                                check_fail_rate = (unmod_fails / ALL_UNMOD_GAMES) * 100.0
                                if check_fail_rate > max(BEST_UNMOD, max(current_best_mod_rates)):
                                    reject_solution = True     
                                    #print("Rejecting for unmod reasons")
                                    #LINE_JUMP_GAMES[game["away"]["game_id"]] = game
                                    LINE_JUMP_GAMES.clear()
                                    LINE_JUMP_GAMES = line_jumpers
                                    LAST_BEST += (fail_counter - LAST_BEST)
                                    REJECTS += 1
                                    break                        
                elif game_game_counter == 2:                    
                    k9_max_err = game_away_val if (game_away_val > k9_max_err) else k9_max_err
                    k9_max_err = game_home_val if (game_home_val > k9_max_err) else k9_max_err
                    k9_min_err = game_away_val if (game_away_val < k9_min_err) else k9_min_err
                    k9_min_err = game_home_val if (game_home_val < k9_min_err) else k9_min_err                    
                    if (k9_max_err - k9_min_err) > WORST_ERROR:
                        reject_solution = True
                        #print("Rejecting solution, game away err = {}, game home err = {}, worst error = {}".format(game_away_val, game_home_val, WORST_ERROR))
                        break
                    if abs(game_away_val) <= 4:             
                        pass_within_four += 1
                        if abs(game_away_val) <= 3:                                                
                            pass_within_three += 1
                            if abs(game_away_val) <= 2:                                                
                                pass_within_two += 1
                                if abs(game_away_val) <= 1:
                                    pass_within_one += 1
                                    if game_away_val == 0:
                                        pass_exact += 1                   
                    if abs(game_home_val) <= 4:  
                        pass_within_four += 1
                        if abs(game_home_val) <= 3:                                                
                            pass_within_three += 1
                            if abs(game_home_val) <= 2:                                                
                                pass_within_two += 1
                                if abs(game_home_val) <= 1:
                                    pass_within_one += 1
                                    if abs(game_home_val) == 0:
                                        pass_exact += 1         
            if not is_cached:
                GAME_CACHE[(season, day)] = good_game_list
        if season not in HAS_GAMES:
            HAS_GAMES[season] = False
        season_end = datetime.datetime.now()
        # debug_print("season {} end: {}, run time {}, average day run {}".format(season, season_end, season_end-season_start, (season_end-season_start)/season_days), debug3, run_id)    
        
    if not reject_solution:
        fail_rate = fail_counter / game_counter        
        #print("Fail rate = {:.4f}, Best fail rate = {:.4f}".format(fail_rate, BEST_FAIL_RATE))
        #LAST_BEST = PREVIOUS_LAST_BEST
    else:
        fail_rate = 1.0   
        #if early_reject:
            #LINE_JUMP_GAMES.clear()
            #LINE_JUMP_GAMES = line_jumpers
        #if CURRENT_ITERATION > 1 and new_pass and (len(reorder_keys) > 0):        
            #only push to the end if we've passed the game game twice in a row
            #if len(PREVIOUS_LINE_JUMP_GAMES) > 0:
                #for pgameid in PREVIOUS_LINE_JUMP_GAMES:
                    #oldgame = PREVIOUS_LINE_JUMP_GAMES[pgameid]
                    #if oldgame["away"]["game_id"] in reorder_keys:                                     
                        #del LINE_JUMP_GAMES[pgameid]                    
                        #LINE_JUMP_GAMES[oldgame["away"]["game_id"]] = oldgame            
                #PREVIOUS_LINE_JUMP_GAMES.clear()
            #PREVIOUS_LINE_JUMP_GAMES = reorder_keys 
        #reorder_failsfirst = line_jumpers
        #for gameid in LINE_JUMP_GAMES:
            #game = LINE_JUMP_GAMES[gameid]
            #if game["away"]["game_id"] not in reorder_failsfirst:
                #reorder_failsfirst[game["away"]["game_id"]] = game
        #LINE_JUMP_GAMES.clear()
        #LINE_JUMP_GAMES = reorder_failsfirst
    if len(win_loss) == 0:
        TOTAL_GAME_COUNTER = game_counter if (game_counter > TOTAL_GAME_COUNTER) else TOTAL_GAME_COUNTER                
    # need to sort win_loss to match up with what will be the sorted set of vals
    # also need to only do this when solving MOFO        
    fail_points, linear_points = 10000000000.0, 10000000000.0    
    max_fail_rate = 0.0
    max_mod_rates = []
    linear_fail = 900000000000.0
    calculate_solution = True
    if (game_counter < ALL_GAMES) and (CURRENT_ITERATION > 1) and not reject_solution:
        print("Somehow ended up with fewer games. Games = {}, all games = {}".format(game_counter, ALL_GAMES))
        reject_solution = True
    if not reject_solution:
        if len(win_loss) > 0:                  
            sorted_win_loss = [x for _,x in sorted(zip(all_vals, win_loss))]
            all_vals.sort()
            linear_error, max_linear_error, min_linear_error, max_error_value, max_error_ratio, errors, shape = calc_linear_unex_error(all_vals, sorted_win_loss, game_counter)
            linear_points = (linear_error + ((max_linear_error + max(max_error_ratio, max_error_value)) ** 2) + ((min_linear_error * 10000) ** 2) + (sum(errors) ** 2) + (sum(shape) ** 2)) * 2.5
            if not mod_mode:
                fail_points = ((fail_rate * 1000.0) ** 2) * 2.5        
                linear_fail = fail_points + linear_points
            else:   
                for name in mod_games:
                    if mod_games[name] > 0:
                        mod_rates[name] = (mod_fails[name] / mod_games[name]) * 100.0
                        max_fail_rate = mod_rates[name] if (mod_rates[name] > max_fail_rate) else max_fail_rate
                        if name not in BEST_MOD_RATES:
                            BEST_MOD_RATES[name] = 10000000.0                        
                        if name not in ALL_MOD_GAMES:
                            ALL_MOD_GAMES[name] = mod_games[name]
                        max_mod_rates = BEST_MOD_RATES.values()
                        if mod_rates[name] > max(BEST_UNMOD, max(max_mod_rates)):
                            print("Failed for mod rate reasons; shouldn't be seeing this if everything is working properly")
                            calculate_solution = False
                if unmod_games > 0:
                    ALL_UNMOD_GAMES = unmod_games
                    unmod_rate = (unmod_fails / unmod_games) * 100.0
                    max_fail_rate = unmod_rate if (unmod_rate > max_fail_rate) else max_fail_rate                                                          
                    if unmod_rate > max(BEST_UNMOD, max(max_mod_rates)):
                        print("Failed for unmod rate reasons; shouldn't be seeing this if everything is working properly")
                        calculate_solution = False                        

                if calculate_solution:                                           
                    all_rates = []
                    for name in mod_rates:
                        all_rates.append(mod_rates[name] / 100.0) 
                    all_rates.append(unmod_rate / 100.0)
                    all_rates.append(fail_rate)
                    aggregate_fail_rate = max(all_rates)                    
                    fail_points = ((aggregate_fail_rate * 1000.0) ** 2.0) * 2.5                                                                                   
                    if linear_points <= fail_points:
                        linear_fail = fail_points + linear_points           
                        debug_print("Aggregate fail rate = {:.4f}, fail points = {}, linear points = {}, total = {}, Best = {}".format(aggregate_fail_rate, int(fail_points), int(linear_points), int(linear_fail), int(BEST_RESULT)), debug2, ":::")                        
                    else:
                        linear_fail = BEST_RESULT + aggregate_fail_rate
                        debug_print("Did not meet linearity requirement to calculate. Aggregate fail rate = {:.4f}, fail points = {}, linear points = {}".format(aggregate_fail_rate, int(fail_points), int(linear_points)), debug2, ":::")                        
                    
                    #if (linear_fail >= BEST_RESULT) and (fail_rate < BEST_FAIL_RATE):
                     #   print("Failed due to linearity points; {:.4f} in shape, {:.4f} in errors".format(sum(shape), sum(errors)))
                    #elif (linear_fail < BEST_RESULT):
                     #   print("PASSING; {:.4f} in shape, {:.4f} in errors".format(sum(shape), sum(errors)))
        elif game_counter == TOTAL_GAME_COUNTER and TOTAL_GAME_COUNTER > 0:        
            pass_exact = (pass_exact / game_counter) * 100.0
            pass_within_one = (pass_within_one / game_counter) * 100.0
            pass_within_two = (pass_within_two / game_counter) * 100.0
            pass_within_three = (pass_within_three / game_counter) * 100.0
            pass_within_four = (pass_within_four / game_counter) * 100.0
            if fail_rate < BEST_EXACT:
                BEST_EXACT = fail_rate
                debug_print("Fail rate = {:.4f}".format(fail_rate), debug, "::::::::")
            linear_fail = (k9_max_err - k9_min_err) * ((fail_rate * 100) - pass_exact - (pass_within_one / 4.0) - (pass_within_two / 8.0) - (pass_within_three / 16.0) - (pass_within_four / 32.0))
    if linear_fail < BEST_RESULT:
        BEST_RESULT = linear_fail           
        ALL_GAMES = game_counter        
        LINE_JUMP_GAMES.clear()        
        LINE_JUMP_GAMES = line_jumpers                  
        if len(win_loss) > 0:
            BEST_FAIL_RATE = fail_rate
            BEST_AGG_FAIL_RATE = aggregate_fail_rate
            BEST_FAILCOUNT = (game_counter / 2) if (linear_points > fail_points) else fail_counter
            LAST_BEST = (game_counter / 2) if (linear_points > fail_points) else fail_counter
            PREVIOUS_LAST_BEST = LAST_BEST
            PASSED_GAMES = (BEST_AGG_FAIL_RATE / 2.0)
            BEST_LINEAR_ERROR = linear_points
            if mod_mode:     
                for name in mod_rates:
                    BEST_MOD_RATES[name] = mod_rates[name] if (mod_rates[name] < BEST_MOD_RATES[name]) else BEST_MOD_RATES[name]                      
                BEST_UNMOD = unmod_rate if (unmod_rate < BEST_UNMOD) else BEST_UNMOD                
        debug_print("-"*20, debug, run_id)
        if len(win_loss) > 0:
            terms_output = "\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(parameters[:(base_mofo_list_size)])] * 3)))  
            mods_output = "\n".join("{},{},{},{},{},{}".format(modstat.attr, modstat.team, modstat.stat, a, b, c) for modstat, (a, b, c) in zip(mod_list, zip(*[iter(parameters[(((base_mofo_list_size) + special_cases_count)):-(park_mod_list_size)])] * 3)))            
            ballpark_mods_output = "\n".join("{},{},{},{},{}".format(bpstat.ballparkstat, bpstat.playerstat, a, b, c) for bpstat, (a, b, c) in zip(ballpark_list, zip(*[iter(parameters[-(park_mod_list_size):])] * 3)))
            if outputdir:
                write_file(outputdir, run_id, "terms.csv", "name,a,b,c\n" + terms_output)
                write_file(outputdir, run_id, "mods.csv", "identifier,team,name,a,b,c\n" + mods_output)
                write_file(outputdir, run_id, "ballparkmods.csv", "ballparkstlat,playerstlat,a,b,c\n" + ballpark_mods_output)
                write_parameters(outputdir, run_id, "solution.json", parameters)
            debug_print("Best so far - fail rate {:.4f}%\n".format(fail_rate * 100.0) + terms_output + "\n" + mods_output + "\n" + ballpark_mods_output, debug2, run_id)
            detailtext = "{} games".format(game_counter)
            detailtext += "\n{:.4f}% Unmodded fail rate, Best {:.4f}%".format(unmod_rate, BEST_UNMOD)
            for name in mod_rates:
                detailtext += "\n{:.4f}% {} fail rate, Best {:.4f}%".format(mod_rates[name], name, BEST_MOD_RATES[name])            
            if multi_mod_games > 0:
                detailtext += "\n{:.4f}% multimod fail rate, {} games".format((multi_mod_fails / multi_mod_games) * 100.0, multi_mod_games)
            if mvm_games > 0:
                detailtext += "\n{:.4f}% mod vs mod fail rate, {} games".format((mvm_fails / mvm_games) * 100.0, mvm_games)            
            detailtext += "\nBest so far - Linear fail {:.4f}, fail rate {:.4f}%".format(linear_fail, fail_rate * 100.0)
            detailtext += "\nMax linear error {:.4f}% ({:.4f} actual, {:.4f} calculated), Min linear error {:.4f}%".format(max_linear_error, max_error_ratio, max_error_value, min_linear_error)
            debug_print(detailtext, debug, run_id)
            if outputdir:
                write_file(outputdir, run_id, "details.txt", detailtext)
            if sys.platform == "darwin":  # MacOS
                os.system("""osascript -e 'display notification "Fail rate {:.4f}%" with title "New solution found!"'""".format(fail_rate * 100.0))
            if len(errors) > 0:
                errors_output = ", ".join(map(str, errors))
                debug_print("Major errors at: " + errors_output, debug, run_id)
            else:
                debug_print("No major errors", debug, run_id)
            if len(shape) > 0:
                shape_output = ", ".join(map(str, shape))
                debug_print("Notable errors: " + shape_output, debug, run_id)
            else:
                debug_print("Somehow no errors", debug, run_id)            
            debug_print("Fail error points = {:.4f}, Linearity error points = {:.4f}, total = {:.4f}".format(fail_points, linear_points, linear_fail), debug, run_id)
            debug_print("Iteration #{}".format(CURRENT_ITERATION), debug, run_id)
        else:
            terms_output = "\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(parameters[:(-len(special_cases) or None)])] * 3)))
            special_case_output = "\n" + "\n".join("{},{}".format(name, val) for name, val in zip(special_case_list, special_cases)) if special_case_list else ""
            if len(win_loss) > 0:
                debug_print("Best so far - fail rate {:.4f}%, linear error {:.4f}, {} games\n".format(fail_rate * 100.0, linear_error, game_counter) + terms_output + special_case_output, debug, run_id)
                debug_print("Max linear error {:.4f}% ({:.4f} actual, {:.4f} calculated), Min linear error {:.4f}%".format(max_linear_error, max_error_ratio, max_error_value, min_linear_error), debug, run_id)
                if len(errors) > 0:
                    errors_output = ", ".join(map(str, errors))
                    debug_print("Major errors at: " + errors_output, debug, run_id)
                else:
                    debug_print("No major errors", debug, run_id)
                if len(shape) > 0:
                    shape_output = ", ".join(map(str, shape))
                    debug_print("Notable errors: " + shape_output, debug, run_id)
                else:
                    debug_print("Somehow no errors", debug, run_id)
                debug_print("{} games".format(game_counter), debug, run_id)
                debug_print("Fail error points = {:.4f}, Linearity error points = {:.4f}, total = {:.4f}".format(fail_points, linear_points, linear_fail), debug, run_id)            
            else:
                debug_print("::: Pass Rates over {} games, fail counter {} :::".format(game_counter, fail_counter), debug, run_id)
                debug_print("Exact = {:.4f}".format(pass_exact), debug, run_id)
                debug_print("+/- 1 = {:.4f}".format(pass_within_one), debug, run_id)
                debug_print("+/- 2 = {:.4f}".format(pass_within_two), debug, run_id)
                debug_print("+/- 3 = {:.4f}".format(pass_within_three), debug, run_id)
                debug_print("+/- 4 = {:.4f}".format(pass_within_four), debug, run_id)
                debug_print("min error {}, max error {}".format(k9_min_err, k9_max_err), debug, run_id)
                debug_print("Best so far - fail rate {:.4f}%\n".format(fail_rate * 100.0) + terms_output + special_case_output, debug, run_id)      
                WORST_ERROR = (k9_max_err - k9_min_err)
        debug_print("-" * 20 + "\n", debug, run_id)            
    if ((CURRENT_ITERATION % 100 == 0 and CURRENT_ITERATION < 10000) or (CURRENT_ITERATION % 500 == 0 and CURRENT_ITERATION < 250000) or (CURRENT_ITERATION % 5000 == 0)):
        if len(win_loss) > 0:
            now = datetime.datetime.now()
            debug_print("Best so far - {:.2f}, iteration # {}, fail rate {:.2f}, linear error {:.4f}, {} rejects since last check-in, {:.2f} seconds".format(BEST_RESULT, CURRENT_ITERATION, (BEST_FAIL_RATE * 100.0), BEST_LINEAR_ERROR, REJECTS, (now-LAST_ITERATION_TIME).total_seconds()), debug, now)
            REJECTS = 0
            LAST_ITERATION_TIME = now
        else:
            debug_print("Best so far - {:.4f}, iteration # {}".format(BEST_RESULT, CURRENT_ITERATION), debug, datetime.datetime.now())
    CURRENT_ITERATION += 1           
    now = datetime.datetime.now()        
    if ((now - LAST_CHECKTIME).total_seconds()) > 3600:
        print("Taking our state-mandated minute long rest per hour of work")
        time.sleep(60)          
        LAST_CHECKTIME = datetime.datetime.now()        
        print("BACK TO WORK")        
    debug_print("run fail rate {:.4f}%".format(fail_rate * 100.0), debug2, run_id)
    endtime = datetime.datetime.now()
    debug_print("func end: {}, run time {}".format(endtime, endtime-starttime), debug3, run_id)
    return linear_fail

#for batman
def minimize_batman_func(parameters, *data):
    run_id = uuid.uuid4()
    starttime = datetime.datetime.now()
    global BEST_RESULT
    global CURRENT_ITERATION
    global BEST_FAIL_RATE    
    global BEST_UNEXVAR_ERROR
    global BEST_EXACT
    global LAST_CHECKTIME
    global BEST_QUARTER_FAIL    
    global MAX_OBSERVED_DIFFERENCE    
    global HAS_GAMES
    global WORST_ERROR
    global MAX_INTEREST
    global BASELINE_ERROR
    global REJECTS
    global EXACT_FAILS
    global LAST_ITERATION_TIME
    global LINE_JUMP_GAMES
    global LAST_DAY_RANGE
    global LAST_SEASON_RANGE
    eventofinterest, batter_list, calc_func, stlat_list, special_case_list, mod_list, ballpark_list, stat_file_map, ballpark_file_map, game_list, team_attrs, games_swept, establish_baseline, debug, debug2, debug3, outputdir = data
    debug_print("func start: {}".format(starttime), debug3, run_id)             
    park_mod_list_size = len(ballpark_list) * 3
    team_mod_list_size = len(mod_list) * 3
    special_cases_count = len(special_case_list)    
    base_batman_list_size = len(parameters) - special_cases_count - park_mod_list_size - team_mod_list_size        
    mods = collections.defaultdict(lambda: {"opp": {}, "same": {}})
    ballpark_mods = collections.defaultdict(lambda: {"bpterm": {}})
    mod_mode = True            
    #special_cases = parameters[base_batman_list_size:-(team_mod_list_size + park_mod_list_size)] if special_case_list else []    
    if CURRENT_ITERATION == 1 and establish_baseline:   
        baseline = True
        if eventofinterest == "abs":
            baseline_parameters = ([0, 0, 1] * len(stlat_list)) + [1, 1, 0, 0, 0] + ([0, 0, 1] * len(mod_list)) + ([0, 0, 1] * len(ballpark_list))            
        else:
            baseline_parameters = ([0, 0, 1] * len(stlat_list)) + [1, 0] + ([0, 0, 1] * len(mod_list)) + ([0, 0, 1] * len(ballpark_list))
        terms = {stat: StlatTerm(a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(baseline_parameters[:base_batman_list_size])] * 3))}        
        for mod, (a, b, c) in zip(mod_list, zip(*[iter(baseline_parameters[(base_batman_list_size + special_cases_count):-park_mod_list_size])] * 3)):                
            mods[mod.attr.lower()][mod.team.lower()][mod.stat.lower()] = StlatTerm(a, b, c)                     
        for bp, (a, b, c) in zip(ballpark_list, zip(*[iter(baseline_parameters[-park_mod_list_size:])] * 3)):        
            ballpark_mods[bp.ballparkstat.lower()][bp.playerstat.lower()] = ParkTerm(a, b, c)
        special_cases = baseline_parameters[base_batman_list_size:-(team_mod_list_size + park_mod_list_size)]             
    else:
        baseline = False
        terms = {stat: StlatTerm(a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(parameters[:base_batman_list_size])] * 3))}        
        for mod, (a, b, c) in zip(mod_list, zip(*[iter(parameters[(base_batman_list_size + special_cases_count):-park_mod_list_size])] * 3)):                
            mods[mod.attr.lower()][mod.team.lower()][mod.stat.lower()] = StlatTerm(a, b, c)                     
        for bp, (a, b, c) in zip(ballpark_list, zip(*[iter(parameters[-park_mod_list_size:])] * 3)):        
            ballpark_mods[bp.ballparkstat.lower()][bp.playerstat.lower()] = ParkTerm(a, b, c)
        special_cases = parameters[base_batman_list_size:-(team_mod_list_size + park_mod_list_size)]
    bat_counter, fail_counter, zero_counter, bat_pos_counter, fail_pos_counter, fail_zero_counter, pass_exact, pass_within_one, pass_within_two, pass_within_three, pass_within_four = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0    
    zero_fail_counter, pos_fail_counter = 0.0, 0.0
    batman_max_err, batman_min_err = 0.0, 100000.0        
    batman_unexvar = 0.0
    good_batter_perf_data, abs_batter_perf_data, good_bats_perf_data = [], [], []                                
    fail_rate, pos_fail_rate, zero_avg_error, pos_avg_error, final_exponent = 1.0, 1.0, 100.0, 100.0, 1.0
    max_err_actual, min_err_actual = "", ""
    reject_solution, viability_unchecked = False, True
    max_atbats, max_hits, max_homers = 0, 0, 0
    atbats_team_stat_data = {}    
    #let some games jump the line
    for gameid in LINE_JUMP_GAMES:
        game = LINE_JUMP_GAMES[gameid]
        if reject_solution:
            break                      
        season = int(game["away"]["season"])
        day = int(game["away"]["day"])
        pitchers, team_stat_data, pitcher_stat_data, last_stat_filename = None, None, None, None
        season_team_attrs = team_attrs.get(str(season), {})
        season_days = 0                
        cached_games = GAME_CACHE.get((season, day))                            
        games = cached_games
        season_days += 1
        paired_games = pair_games(games)
        schedule = get_schedule_from_paired_games(paired_games, season, day)
        day_mods = get_attrs_from_paired_games(season_team_attrs, paired_games)
        cached_stats = STAT_CACHE.get((season, day))
        team_stat_data, pitcher_stat_data, players = cached_stats                        
        cached_ballparks = BALLPARK_CACHE.get((season, day))          
        ballparks = cached_ballparks          
        ballpark = ballparks.get(game["home"]["team_id"], collections.defaultdict(lambda: 0.5))
        game_attrs = get_attrs_from_paired_game(season_team_attrs, game)
        awayAttrs, homeAttrs = game_attrs["away"], game_attrs["home"]                
        special_game_attrs = (homeAttrs.union(awayAttrs)) - ALLOWED_IN_BASE_BATMAN   
        cached_batters = BATTER_CACHE.get((season, day, game["away"]["game_id"]))
        batter_perf_data = cached_batters                    
        last_lineup_id, previous_batting_team = "", ""
        lineup_size = 0
        atbats_team_stat_data.clear()
        for batter_perf in batter_perf_data:         
            if reject_solution:
                break              
            battingteam = get_team_name(batter_perf["batter_team_id"], season, day)
            pitchingteam = get_team_name(batter_perf["pitcher_team_id"], season, day)                                       
            pitchername = players[batter_perf["pitcher_id"]][0]                                    
            batter_list_dict = [stlats for player_id, stlats in team_stat_data[battingteam].items() if player_id == batter_perf["batter_id"]]
            if not batter_list_dict:
                continue                                       
            away_game, home_game = game["away"], game["home"]
            awayPitcher, awayTeam = players.get(away_game["pitcher_id"])
            homePitcher, homeTeam = players.get(home_game["pitcher_id"])                                                
            previous_batting_team = battingteam                        
            if (eventofinterest == "abs"):                            
                if (batter_perf["batter_id"] not in atbats_team_stat_data):                                  
                    flip_lineup = (battingteam == "San Francisco Lovers") and (season == 13) and (day > 27)                                                                        
                    atbats_team_stat_data = get_team_atbats(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, pitchername, pitchingteam, battingteam, away_game["weather"], ballpark, ballpark_mods, team_stat_data, pitcher_stat_data, int(batter_perf["num_innings"]), flip_lineup, terms, {"factors": special_cases}, 3, baseline)                                                            
                bat_bat_counter, bat_fail_counter, batman_fail_by, actual_result, real_val = calc_func(eventofinterest, batter_perf, season_team_attrs, atbats_team_stat_data, pitcher_stat_data, pitchername, 
                                                                            batter_perf["batter_id"], lineup_size, terms, special_cases, game, battingteam, pitchingteam, None, None)                                                                                                     
            else:                                                                               
                awayMods, homeMods = get_batman_mods(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, pitchername, pitchingteam, batter_perf["batter_id"], battingteam, away_game["weather"], ballpark, ballpark_mods, team_stat_data, pitcher_stat_data)                        
                if homeTeam == battingteam:
                    battingMods, defenseMods = homeMods, awayMods
                else:
                    battingMods, defenseMods = awayMods, homeMods
                bat_bat_counter, bat_fail_counter, batman_fail_by, actual_result, real_val = calc_func(eventofinterest, batter_perf, season_team_attrs, team_stat_data, pitcher_stat_data, pitchername, 
                                                                            batter_perf["batter_id"], lineup_size, terms, special_cases, game, battingteam, pitchingteam, defenseMods, battingMods)       
            bat_counter += bat_bat_counter
            fail_counter += bat_fail_counter                                                                  
            max_hits = int(batter_perf["hits"]) if (int(batter_perf["hits"]) > max_hits) else max_hits
            max_homers = int(batter_perf["home_runs"]) if (int(batter_perf["home_runs"]) > max_homers) else max_homers
            max_atbats = int(batter_perf["at_bats"]) if (int(batter_perf["at_bats"]) > max_atbats) else max_atbats            

            #if eventofinterest == "abs" and abs(batman_fail_by) > 11:
             #   print("failed by {:.4f}, batman calc value {:.2f}, actual value = {:.2f}".format(batman_fail_by, batman_fail_by + real_val, real_val))
            #if eventofinterest == "hits" and abs(batman_fail_by) > 6:
             #   print("failed by {:.4f}, actual {}, batman hits per atbat value {:.4f}, actual hits per atbat value = {:.4f}".format(batman_fail_by, real_val, (batman_fail_by + real_val) / (int(batter_perf["at_bats"])), real_val / (int(batter_perf["at_bats"]))))
            #if eventofinterest == "hrs" and abs(batman_fail_by) > 4:
             #   print("failed by {:.4f}, actual {}, batman hrs per atbat value {:.4f}, actual hrs per atbat value = {:.4f}".format(batman_fail_by, real_val, (batman_fail_by + real_val) / (int(batter_perf["at_bats"])), real_val / (int(batter_perf["at_bats"]))))

            if bat_bat_counter > 0:                    
                if batman_fail_by > batman_max_err:
                    batman_max_err = batman_fail_by
                    max_err_actual = actual_result
                if batman_fail_by < batman_min_err:
                    batman_min_err = batman_fail_by
                    if CURRENT_ITERATION > 1:
                        if (real_val == abs(batman_fail_by)) and (real_val > 0) and (not eventofinterest == "abs"):
                            reject_solution = True
                            REJECTS += 1                            
                            break                                             
                    min_err_actual = actual_result            
            if abs(batman_min_err) >= MAX_INTEREST:
                reject_solution = True
                REJECTS += 1                
                break                                             
            elif max(abs(batman_max_err), abs(batman_min_err)) > WORST_ERROR:
                reject_solution = True
                REJECTS += 1                
                break                            
            if eventofinterest == "abs":
                stagefour, stagethree, stagetwo, stageone, stageexact = 1.0, 0.75, 0.5, 0.25, 0.1
            elif eventofinterest == "hrs":
                stagefour, stagethree, stagetwo, stageone, stageexact = 1.0, 0.75, 0.5, 0.25, 0.1
            else:
                stagefour, stagethree, stagetwo, stageone, stageexact = 1.0, 0.75, 0.5, 0.25, 0.1
            if bat_bat_counter > 0:            
                if (abs(batman_fail_by) < stagefour) and (real_val > 0):             
                    pass_within_four += 1
                    if abs(batman_fail_by) < stagethree:                                                
                        pass_within_three += 1
                        if abs(batman_fail_by) < stagetwo:                                                
                            pass_within_two += 1
                            if abs(batman_fail_by) < stageone:
                                pass_within_one += 1
                                if abs(batman_fail_by) <= stageexact:
                                    pass_exact += 1      
                if real_val > 0:                
                    if abs(batman_fail_by) > stageexact:                                
                        pos_fail_counter += abs(batman_fail_by)
                        fail_pos_counter += bat_fail_counter
                        batman_unexvar += batman_fail_by ** 2.0                                    
                    bat_pos_counter += bat_bat_counter
                elif (real_val == 0):
                    if abs(batman_fail_by) > stageexact:
                        zero_fail_counter += abs(batman_fail_by)  
                        fail_zero_counter += bat_fail_counter                            
                        batman_unexvar += batman_fail_by ** 2.0                                    
                    zero_counter += bat_bat_counter

    seasonrange = reversed(range(12, 15))
    dayrange = range(1, 125)

    if not reject_solution:
        #if LAST_SEASON_RANGE == 0:
         #   if LAST_DAY_RANGE == 1:
          #      LAST_DAY_RANGE = 0
           # else:
            #    LAST_DAY_RANGE = 1    

        if LAST_SEASON_RANGE == 0:
            seasonrange = range(12, 15)            
        else:
            seasonrange = reversed(range(12, 15))                        
        #if LAST_DAY_RANGE == 0:
         #   dayrange = range(1, 125)
        #else:
         #   dayrange = reversed(range(1, 125))

    for season in seasonrange:
        if reject_solution:
            break
        # if (season in HAS_GAMES and not HAS_GAMES[season]) or season < 12:
        if (season in HAS_GAMES and not HAS_GAMES[season]):
            continue
        season_start = datetime.datetime.now()
        debug_print("season {} start: {}".format(season, season_start), debug3, run_id)
        pitchers, team_stat_data, pitcher_stat_data, last_stat_filename = None, None, None, None
        season_team_attrs = team_attrs.get(str(season), {})
        season_days = 0        
        for day in dayrange:            
            #day_start = datetime.datetime.now()
            if reject_solution:
                break
            is_cached = False
            cached_games = GAME_CACHE.get((season, day))
            if cached_games:
                games = cached_games
                is_cached = True
            else:
                if type(cached_games) == list:
                    continue
                games = [row for row in game_list if row["season"] == str(season) and row["day"] == str(day)]
                if not games:
                    GAME_CACHE[(season, day)] = []
                    continue                
            season_days += 1
            paired_games = pair_games(games)
            schedule = get_schedule_from_paired_games(paired_games, season, day)
            day_mods = get_attrs_from_paired_games(season_team_attrs, paired_games)
            cached_stats = STAT_CACHE.get((season, day))
            if cached_stats:
                team_stat_data, pitcher_stat_data, players = cached_stats
            else:
                stat_filename = stat_file_map.get((season, day))
                if stat_filename:
                    last_stat_filename = stat_filename
                    players = get_player_id_lookup(stat_filename)
                    team_stat_data, pitcher_stat_data = load_stat_data_pid(stat_filename, schedule, day, season_team_attrs)                                                            
                elif should_regen(day_mods):
                    players = get_player_id_lookup(stat_filename)
                    team_stat_data, pitcher_stat_data = load_stat_data_pid(stat_filename, schedule, day, season_team_attrs)
                STAT_CACHE[(season, day)] = (team_stat_data, pitcher_stat_data, players)
            if not players:
                raise Exception("No stat file found")
            cached_ballparks = BALLPARK_CACHE.get((season, day))
            if cached_ballparks is None:
                ballpark_filename = ballpark_file_map.get((season, day))
                if CURRENT_ITERATION > 1:
                    print("Ballparks not cached, season {}, day {}".format(season, day))
                if ballpark_filename:
                    with open(ballpark_filename) as f:
                        ballparks = json.load(f)
                else:
                    if ballparks is None:  # this should use the previous value of ballparks by default, use default if not
                        ballparks = collections.defaultdict(lambda: collections.defaultdict(lambda: 0.5))
                BALLPARK_CACHE[(season, day)] = ballparks
            else:
                ballparks = cached_ballparks  
            good_game_list = []
            for game in paired_games:       
                if reject_solution:
                    break
                if game["away"]["game_id"] in LINE_JUMP_GAMES:
                    continue
                ballpark = ballparks.get(game["home"]["team_id"], collections.defaultdict(lambda: 0.5))
                game_attrs = get_attrs_from_paired_game(season_team_attrs, game)
                awayAttrs, homeAttrs = game_attrs["away"], game_attrs["home"]                
                special_game_attrs = (homeAttrs.union(awayAttrs)) - ALLOWED_IN_BASE_BATMAN                
                if (game["away"]["game_id"] in games_swept):
                    print("Game id {} swept away!".format(game["away"]["game_id"]))
                    continue
                if not is_cached and not special_game_attrs:
                    good_game_list.extend([game["home"], game["away"]])
                    HAS_GAMES[season] = True
                if not special_game_attrs:                    
                    cached_batters = BATTER_CACHE.get((season, day, game["away"]["game_id"]))
                    iscached_batters = False
                    if cached_batters:                        
                        batter_perf_data = cached_batters
                        iscached_batters = True
                    else:              
                        if type(cached_batters) == list:
                            continue
                        if CURRENT_ITERATION > 1:
                            print("Somehow not cached, not list season {}, day {}".format(season, day))
                        batter_perf_data = [row for row in batter_list if row["season"] == str(season) and row["day"] == str(day) and row["game_id"] == game["away"]["game_id"]]                    
                        if not batter_perf_data:                        
                            BATTER_CACHE[(season, day, game["away"]["game_id"])] = []
                            continue
                    good_batter_perf_data = []
                    good_bats_perf_data = []
                    abs_batter_perf_data = []
                    last_lineup_id, previous_batting_team = "", ""
                    previous_innings, minimum_atbats, lineup_size = 0, 0, 0
                    omit_from_good_abs = False
                    atbats_team_stat_data.clear()
                    for batter_perf in batter_perf_data:    
                        if reject_solution:
                            break          
                        battingteam = get_team_name(batter_perf["batter_team_id"], season, day)
                        pitchingteam = get_team_name(batter_perf["pitcher_team_id"], season, day)                           
                        if not iscached_batters:            
                            if (minimum_atbats < previous_innings * 3) and not (previous_batting_team == battingteam) and not omit_from_good_abs:
                                print("team did not achieve the requisite number of atbats for their minimum number of outs: {} at bats, {} outs".format(minimum_atbats, previous_innings * 3))
                                omit_from_good_abs = True
                            if not (previous_batting_team == battingteam) and not (previous_batting_team == ""):                                
                                if not omit_from_good_abs:                                      
                                    for bperf in abs_batter_perf_data:
                                        good_batter_perf_data.extend([bperf])  
                                else:                                    
                                    print("Catching omission IN the loop; Omitting {}, season {}, day {}, opponent {}".format(previous_batting_team, season, day, battingteam))                            
                                abs_batter_perf_data = []
                                omit_from_good_abs = False
                            elif omit_from_good_abs:                           
                                continue                                                                                                
                        pitchername = players[batter_perf["pitcher_id"]][0]                        
                        if previous_batting_team != battingteam:
                            minimum_atbats = 0         
                            previous_innings = 0
                        batter_list_dict = [stlats for player_id, stlats in team_stat_data[battingteam].items() if player_id == batter_perf["batter_id"]]
                        if not batter_list_dict:                            
                            continue      
                        if not iscached_batters:
                            if (eventofinterest == "hits") or (eventofinterest == "hrs"):
                                if ((int(batter_perf["num_innings"]) < 8) or (int(batter_perf["at_bats"]) < 3)):
                                    print("omitting batter from hits or homers calculations due to having insufficient data")                                    
                                    continue
                                else:
                                    good_bats_perf_data.extend([batter_perf])   
                        away_game, home_game = game["away"], game["home"]
                        awayPitcher, awayTeam = players.get(away_game["pitcher_id"])
                        homePitcher, homeTeam = players.get(home_game["pitcher_id"])                                                
                        previous_batting_team = battingteam                                             
                        if ((eventofinterest == "hits") or (eventofinterest == "hrs")) and (CURRENT_ITERATION > 1):
                            if ((int(batter_perf["num_innings"]) < 8) or (int(batter_perf["at_bats"]) < 3)):
                                print("Illegal batter in cached data! {} innings and {} at bats".format(batter_perf["num_innings"], batter_perf["at_bats"]))
                        if (eventofinterest == "abs"):                            
                            if (batter_perf["batter_id"] not in atbats_team_stat_data):                                  
                                flip_lineup = (battingteam == "San Francisco Lovers") and (season == 13) and (day > 27)                                                                        
                                atbats_team_stat_data = get_team_atbats(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, pitchername, pitchingteam, battingteam, away_game["weather"], ballpark, ballpark_mods, team_stat_data, pitcher_stat_data, int(batter_perf["num_innings"]), flip_lineup, terms, {"factors": special_cases}, 3, baseline)                                                            
                            bat_bat_counter, bat_fail_counter, batman_fail_by, actual_result, real_val = calc_func(eventofinterest, batter_perf, season_team_attrs, atbats_team_stat_data, pitcher_stat_data, pitchername, 
                                                                                        batter_perf["batter_id"], lineup_size, terms, special_cases, game, battingteam, pitchingteam, None, None)                              
                            minimum_atbats += int(batter_perf["at_bats"]) + batman_fail_by
                            previous_innings = max(int(batter_perf["num_innings"]), previous_innings)                            
                            if real_val == 1:
                                omit_from_good_abs = True
                                print("{} atbat {} season {}, day {}, opponent {}, batter {}".format(real_val, battingteam, season, day, pitchingteam, players[batter_perf["batter_id"]][0]))       
                                continue
                            if (CURRENT_ITERATION == 1) and (batman_fail_by > 0):                                
                                omit_from_good_abs = True                                      
                                print("Omitting {}, season {}, day {}, opponent {}, batter {}".format(battingteam, season, day, pitchingteam, players[batter_perf["batter_id"]][0]))                                    
                                continue
                            if not iscached_batters and not omit_from_good_abs:
                                abs_batter_perf_data.extend([batter_perf])                            
                        else:                                                                               
                            awayMods, homeMods = get_batman_mods(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, pitchername, pitchingteam, batter_perf["batter_id"], battingteam, away_game["weather"], ballpark, ballpark_mods, team_stat_data, pitcher_stat_data)                        
                            if homeTeam == battingteam:
                                battingMods, defenseMods = homeMods, awayMods
                            else:
                                battingMods, defenseMods = awayMods, homeMods
                            bat_bat_counter, bat_fail_counter, batman_fail_by, actual_result, real_val = calc_func(eventofinterest, batter_perf, season_team_attrs, team_stat_data, pitcher_stat_data, pitchername, 
                                                                                        batter_perf["batter_id"], lineup_size, terms, special_cases, game, battingteam, pitchingteam, defenseMods, battingMods)       
                        bat_counter += bat_bat_counter
                        fail_counter += bat_fail_counter        
                        max_hits = int(batter_perf["hits"]) if (int(batter_perf["hits"]) > max_hits) else max_hits
                        max_homers = int(batter_perf["home_runs"]) if (int(batter_perf["home_runs"]) > max_homers) else max_homers
                        max_atbats = int(batter_perf["at_bats"]) if (int(batter_perf["at_bats"]) > max_atbats) else max_atbats                                             

                        #if eventofinterest == "abs" and abs(batman_fail_by) > 11:
                         #   print("failed by {:.4f}, batman calc value {:.2f}, actual value = {:.2f}".format(batman_fail_by, batman_fail_by + real_val, real_val))
                        #if eventofinterest == "hits" and abs(batman_fail_by) > 6:
                         #   print("failed by {:.4f}, actual {}, batman hits per atbat value {:.4f}, actual hits per atbat value = {:.4f}".format(batman_fail_by, real_val, (batman_fail_by + real_val) / (int(batter_perf["at_bats"])), real_val / (int(batter_perf["at_bats"]))))
                        #if eventofinterest == "hrs" and abs(batman_fail_by) > 4:
                         #   print("failed by {:.4f}, actual {}, batman hrs per atbat value {:.4f}, actual hrs per atbat value = {:.4f}".format(batman_fail_by, real_val, (batman_fail_by + real_val) / (int(batter_perf["at_bats"])), real_val / (int(batter_perf["at_bats"]))))                        

                        if bat_bat_counter > 0:
                            if batman_fail_by > batman_max_err:
                                batman_max_err = batman_fail_by
                                max_err_actual = actual_result
                            if batman_fail_by < batman_min_err:
                                batman_min_err = batman_fail_by
                                if CURRENT_ITERATION > 1:
                                    if (real_val == abs(batman_fail_by)) and (real_val > 0) and (not eventofinterest == "abs"):
                                        reject_solution = True
                                        REJECTS += 1
                                        LINE_JUMP_GAMES[game["away"]["game_id"]] = game                           
                                        break                                                                                 
                                min_err_actual = actual_result                 
                        if abs(batman_min_err) >= MAX_INTEREST:
                            reject_solution = True
                            REJECTS += 1
                            LINE_JUMP_GAMES[game["away"]["game_id"]] = game                           
                            break                                             
                        elif max(abs(batman_max_err), abs(batman_min_err)) > WORST_ERROR:
                            reject_solution = True
                            REJECTS += 1
                            LINE_JUMP_GAMES[game["away"]["game_id"]] = game                           
                            break                                                  
                        elif (eventofinterest == "abs") and (max(abs(batman_max_err), abs(batman_min_err)) >= (WORST_ERROR - 0.5)):
                            #experimenting with adding games to the jump for being close to the worst error
                            LINE_JUMP_GAMES[game["away"]["game_id"]] = game                           
                        if eventofinterest == "abs":
                            stagefour, stagethree, stagetwo, stageone, stageexact = 1.0, 0.75, 0.5, 0.25, 0.1
                        elif eventofinterest == "hrs":
                            stagefour, stagethree, stagetwo, stageone, stageexact = 1.0, 0.75, 0.5, 0.25, 0.1
                        else:
                            stagefour, stagethree, stagetwo, stageone, stageexact = 1.0, 0.75, 0.5, 0.25, 0.1
                        if bat_bat_counter > 0:
                            if (abs(batman_fail_by) < stagefour) and (real_val > 0):             
                                pass_within_four += 1
                                if abs(batman_fail_by) < stagethree:                                                
                                    pass_within_three += 1
                                    if abs(batman_fail_by) < stagetwo:                                                
                                        pass_within_two += 1
                                        if abs(batman_fail_by) < stageone:
                                            pass_within_one += 1
                                            if abs(batman_fail_by) <= stageexact:
                                                pass_exact += 1      
                            if real_val > 0:                
                                if abs(batman_fail_by) > stageexact:                                
                                    pos_fail_counter += abs(batman_fail_by)
                                    fail_pos_counter += bat_fail_counter
                                    batman_unexvar += batman_fail_by ** 2.0                                    
                                bat_pos_counter += bat_bat_counter
                            elif (real_val == 0):
                                if abs(batman_fail_by) > stageexact:
                                    zero_fail_counter += abs(batman_fail_by)  
                                    fail_zero_counter += bat_fail_counter                            
                                    batman_unexvar += batman_fail_by ** 2.0                                    
                                zero_counter += bat_bat_counter                                
                
                    if not iscached_batters:                               
                        if (minimum_atbats < previous_innings * 3) and not omit_from_good_abs:
                            print("team did not achieve the requisite number of atbats for their minimum number of outs: {} at bats, {} outs".format(minimum_atbats, previous_innings * 3))
                            omit_from_good_abs = True                                                       
                        if not omit_from_good_abs:                                      
                            for bperf in abs_batter_perf_data:
                                good_batter_perf_data.extend([bperf])  
                        else:
                            print("Catching omission out of the loop; Omitting {}, season {}, day {}, opponent {}".format(battingteam, season, day, pitchingteam))                            
                        abs_batter_perf_data = []
                        omit_from_good_abs = False                        
                    if not iscached_batters:  
                        if eventofinterest == "abs":
                            BATTER_CACHE[(season, day, game["away"]["game_id"])] = good_batter_perf_data                        
                        else:
                            BATTER_CACHE[(season, day, game["away"]["game_id"])] = good_bats_perf_data                        
            #day_end = datetime.datetime.now()
            #if CURRENT_ITERATION > 1:
             #   print("{:.2f} seconds for 1 day, season {} day {}".format((day_end - day_start).total_seconds(), season, day))
            if not is_cached:
                GAME_CACHE[(season, day)] = good_game_list            
        if season not in HAS_GAMES:
            HAS_GAMES[season] = False
        season_end = datetime.datetime.now()
        # debug_print("season {} end: {}, run time {}, average day run {}".format(season, season_end, season_end-season_start, (season_end-season_start)/season_days), debug3, run_id)      
    if not reject_solution:
        #print("Possible solution! {:.4f} error span, max = {:.4f}, min = {:.4f}".format(batman_max_err - batman_min_err, batman_max_err, batman_min_err))
        if eventofinterest == "abs" or zero_counter == 0:            
            zero_avg_error = 0.0  
            zero_fail_rate = 0.0
        else:
            zero_avg_error = zero_fail_counter / zero_counter
            zero_fail_rate = fail_zero_counter / zero_counter
        if bat_pos_counter > 0:
            pos_avg_error = pos_fail_counter / bat_pos_counter
            pos_fail_rate = fail_pos_counter / bat_pos_counter                
        else:
            pos_avg_error = 0
            pos_fail_rate = 0
        fail_rate = fail_counter / bat_counter        
    else:
        fail_rate, pos_fail_rate, zero_fail_rate = 1.0, 1.0, 1.0
    # need to sort win_loss to match up with what will be the sorted set of vals
    # also need to only do this when solving MOFO
    #use_zero_error = zero_avg_error if (zero_avg_error > 0 or pos_avg_error < 0.5) else (pos_avg_error * 2)
    use_zero_error = zero_avg_error
    linear_fail = 9000000000000.0
    fail_points = 9000000000000.0    
    if not reject_solution:        
        pass_exact = (pass_exact / bat_pos_counter) * 100.0
        pass_within_one = (pass_within_one / bat_pos_counter) * 100.0
        pass_within_two = (pass_within_two / bat_pos_counter) * 100.0
        pass_within_three = (pass_within_three / bat_pos_counter) * 100.0
        pass_within_four = (pass_within_four / bat_pos_counter) * 100.0
        if (pass_exact > 0.0) or (CURRENT_ITERATION == 1):            
            if pass_exact > BEST_EXACT:
                debug_print("Fail rate = {:.4f}, Pos fail rate = {:.4f}, zero fail rate = {:.4f}, pass exact = {:.4f}, max err = {:.4f}, min err = {:.4f}, pavgerr = {:.4f}, zavgerr = {:.4f}".format(fail_rate, pos_fail_rate, zero_fail_rate, pass_exact, batman_max_err, batman_min_err, pos_avg_error, use_zero_error), debug, "::::::::")
            if batman_max_err >= batman_min_err:                             
                fail_points = (zero_fail_rate * 100.0 * use_zero_error) + (pos_fail_rate * 100.0 * pos_avg_error) + ((100.0 - pass_exact) * (pos_avg_error + use_zero_error))
                #print("Candidate for success! {:.4f} error span, pos fail rate = {:.2f}, fail rate = {:.2f}, zero error = {:.4f}, pos error = {:.4f}".format(max(abs(batman_max_err), abs(batman_min_err)), pos_fail_rate, fail_rate, zero_avg_error, pos_avg_error))                                                        
                linear_fail = (max(abs(batman_max_err), abs(batman_min_err)) * 400.0) + fail_points
        else:
            debug_print("Rejected for insufficient exact. Pass exact = {:.4f}, max err = {:.4f}, min err = {:.4f}".format(pass_exact, batman_max_err, batman_min_err), debug, "::::::::")
            EXACT_FAILS += 1
            linear_fail = BEST_RESULT + EXACT_FAILS
    if linear_fail < BEST_RESULT:
        BEST_RESULT = linear_fail
        BEST_EXACT = pass_exact
        BEST_FAIL_RATE = pos_fail_rate        
        BEST_UNEXVAR_ERROR = batman_unexvar 
        LAST_SEASON_RANGE = 1 if (LAST_SEASON_RANGE == 0) else 0
        EXACT_FAILS = 0
        maxevent = 0    
        if eventofinterest == "abs":
            maxevent = max_atbats
        if eventofinterest == "hits":
            maxevent = max_hits
        if eventofinterest == "hrs":
            maxevent = max_homers
        if CURRENT_ITERATION == 1:
            BASELINE_ERROR = max(abs(batman_max_err), abs(batman_min_err))
        LINE_JUMP_GAMES.clear()
        terms_output = "\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(parameters[:(base_batman_list_size)])] * 3)))            
        special_case_output = "\n" + "\n".join("{},{}".format(name, val) for name, val in zip(special_case_list, special_cases))
        mods_output = "\n".join("{},{},{},{},{},{}".format(modstat.attr, modstat.team, modstat.stat, a, b, c) for modstat, (a, b, c) in zip(mod_list, zip(*[iter(parameters[(((base_batman_list_size) + special_cases_count)):-(park_mod_list_size)])] * 3)))            
        ballpark_mods_output = "\n".join("{},{},{},{},{}".format(bpstat.ballparkstat, bpstat.playerstat, a, b, c) for bpstat, (a, b, c) in zip(ballpark_list, zip(*[iter(parameters[-(park_mod_list_size):])] * 3)))
        if outputdir:
            write_file(outputdir, run_id, eventofinterest + "terms.csv", "name,a,b,c\n" + terms_output + "\n" + special_case_output)
            write_file(outputdir, run_id, eventofinterest + "mods.csv", "identifier,team,name,a,b,c\n" + mods_output)
            write_file(outputdir, run_id, eventofinterest + "ballparkmods.csv", "ballparkstlat,playerstlat,a,b,c\n" + ballpark_mods_output)
            write_parameters(outputdir, run_id, eventofinterest + "solution.json", parameters)
        debug_print("\n" + terms_output + special_case_output + "\n" + mods_output + "\n" + ballpark_mods_output, debug2, run_id)   
        detailtext = "::: Pass Rates over {} batters, fail counter {} :::".format(bat_counter, fail_counter)
        detailtext += "\nExact (+/- {:.2f}) = {:.4f}".format(stageexact, pass_exact)
        detailtext += "\n+/- {:.2f} = {:.4f}".format(stageone, pass_within_one)
        detailtext += "\n+/- {:.2f} = {:.4f}".format(stagetwo, pass_within_two)
        detailtext += "\n+/- {:.2f} = {:.4f}".format(stagethree, pass_within_three)
        detailtext += "\n+/- {:.2f} = {:.4f}".format(stagefour, pass_within_four)
        detailtext += "\nmax underestimate {:.4f}, max overestimate {:.4f}, unexvar {:.4f}".format(batman_min_err, batman_max_err, batman_unexvar)
        detailtext += "\nactual val underest {}".format(min_err_actual)
        detailtext += "\nactual val overest {}".format(max_err_actual)
        detailtext += "\nmaximum {} = {}".format(eventofinterest, maxevent)
        detailtext += "\nzero average error {:.4f}, pos average error {:.4f}".format(zero_avg_error, pos_avg_error)
        detailtext += "\nBest so far - fail rate {:.4f}%, pos fail rate {:.4f}%, zero fail rate {:.4f}% ".format(fail_rate * 100.0, pos_fail_rate * 100.0, zero_fail_rate * 100.0)
        debug_print(detailtext, debug, run_id)
        if outputdir:
            write_file(outputdir, run_id, eventofinterest + "details.txt", detailtext)                
        debug_print("Optimizing: {}, iteration #{}".format(eventofinterest, CURRENT_ITERATION), debug, run_id)               
        debug_print("-" * 20 + "\n", debug, run_id)      
        if CURRENT_ITERATION == 1:
            total_batters = 0
            check_max_hits = 0
            check_max_homers = 0
            check_max_atbats = 0
            #validate batter cache data
            for season in range(12, 15):
                for day in range(1, 125):
                    cache_games = GAME_CACHE.get((season, day))
                    paired_games = pair_games(cache_games)
                    for game in paired_games:
                        performance_data = BATTER_CACHE.get((season, day, game["away"]["game_id"]))
                        for thisbatter_perf in performance_data:                        
                            total_batters += 1
                            hits = int(thisbatter_perf["hits"])
                            homers = int(thisbatter_perf["home_runs"])
                            atbats = int(thisbatter_perf["at_bats"])
                            check_max_hits = hits if (hits > check_max_hits) else check_max_hits
                            check_max_homers = homers if (homers > check_max_homers) else check_max_homers
                            check_max_atbats = atbats if (atbats > check_max_atbats) else check_max_atbats
            print("Maximums in cached data: hits = {}, homers = {}, atbats = {}, batters = {}".format(check_max_hits, check_max_homers, check_max_atbats, total_batters))
            if eventofinterest == "hits":
                MAX_INTEREST = check_max_hits
            elif eventofinterest == "hrs":
                MAX_INTEREST = check_max_homers
            else:
                MAX_INTEREST = check_max_atbats       
        if abs(batman_min_err) < MAX_INTEREST:
            WORST_ERROR = max(abs(batman_max_err), abs(batman_min_err))
    if ((CURRENT_ITERATION % 100 == 0 and CURRENT_ITERATION < 10000) or (CURRENT_ITERATION % 500 == 0 and CURRENT_ITERATION < 250000) or (CURRENT_ITERATION % 5000 == 0 and CURRENT_ITERATION < 1000000) or (CURRENT_ITERATION % 50000 == 0)):
        now = datetime.datetime.now()        
        debug_print("Error Span - {:.4f}, fail rate = {:.2f}, pass exact = {:.4f}, optimizing: {}, iteration # {}, {} rejects since last check-in, {:.2f} seconds".format(WORST_ERROR, (BEST_FAIL_RATE * 100), BEST_EXACT, eventofinterest, CURRENT_ITERATION, REJECTS, (now-LAST_ITERATION_TIME).total_seconds()), debug, now)
        REJECTS = 0
        LAST_ITERATION_TIME = now          
    if CURRENT_ITERATION < 100:
        now = datetime.datetime.now()        
        debug_print("Error Span - {:.4f}, fail rate = {:.2f}, pass exact = {:.4f}, optimizing: {}, iteration # {}, {} rejects since last check-in, {:.2f} seconds".format(WORST_ERROR, (BEST_FAIL_RATE * 100), BEST_EXACT, eventofinterest, CURRENT_ITERATION, REJECTS, (now-LAST_ITERATION_TIME).total_seconds()), debug, now)        
        REJECTS = 0
        LAST_ITERATION_TIME = now          
    CURRENT_ITERATION += 1   
    now = datetime.datetime.now()        
    if ((now - LAST_CHECKTIME).total_seconds()) > 3600:
        print("Taking our state-mandated minute long rest per hour of work")
        time.sleep(60)          
        LAST_CHECKTIME = datetime.datetime.now()        
        print("BACK TO WORK")
    debug_print("run fail rate {:.4f}%".format(fail_rate * 100.0), debug2, run_id)
    endtime = datetime.datetime.now()
    debug_print("func end: {}, run time {}".format(endtime, endtime-starttime), debug3, run_id)
    return linear_fail