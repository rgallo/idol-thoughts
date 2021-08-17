import collections
import csv
import sys
import time
import random
import datetime
import json
import os
import re
import uuid
import math
import copy
from glob import glob

from helpers import StlatTerm, ParkTerm, get_weather_idx
from helpers import load_stat_data, load_stat_data_pid, adjust_by_pct, calculate_adjusted_stat_data
from helpers import DEFENSE_STLATS, defense_stars, BATTING_STLATS, batting_stars, BASERUNNING_STLATS, baserunning_stars
from batman import get_team_atbats, get_batman_mods

STAT_CACHE = {}
BALLPARK_CACHE = {}
GAME_CACHE = {}
BATTER_CACHE = {}
ATTRS_CACHE = {}
HITS_CACHE = {}
HOMERS_CACHE = {}
SEEDDOGS_CACHE = {}
KS_CACHE = {}
SHO_CACHE = {}
MEATBALLS_CACHE = {}
CHIPSBURGERS_CACHE = {}
CHIPSMEATBALLS_CACHE = {}
STEALS_CACHE = {}
SEEDPICKLES_CACHE = {}
DOGPICKLES_CACHE = {}
TRIFECTA_CACHE = {}
ADJUSTED_STAT_CACHE = {}

MIN_SEASON = 22
MAX_SEASON = 23

BEST_RESULT = 90000000000000000.0    
BEST_SEASON = 80000000000000.0
BEST_FAIL_RATE = 1.0
BEST_LINEAR_ERROR = 1.0
MIN_DAY = 1
MAX_DAY = 99
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
MAX_INTEREST = {}
BASELINE_ERROR = 1000000000.0
PASSED_GAMES = 0.25
REJECTS = 0
ALL_UNMOD_GAMES = 0
ALL_GAMES = 0
WORST_MOD = ""
PLUS_NAME = ""
ERROR_SPAN = {}
LAST_MAX = {}
LAST_MIN = {}
LAST_FAIL_EVENT = ""
BEST_AGG_FAIL_RATE = 0
LAST_BEST = 1000000000.0
LAST_UNMOD = 1000000000.0
LAST_SPAN = 1000000.0
LAST_BESTS = {}
PREVIOUS_LAST_BEST = 1000000000.0
BROAD_ERROR_THRESHOLD = 25000000.0
ERROR_THRESHOLD = 35.0
POS_HITS = 0
POS_HRS = 0
LAST_DAY_RANGE = 1
LAST_SEASON_RANGE = 1
FIRST_SOLUTION = False
EARLY_REJECT = False
EXPECTED_MOD_RATES = {}
ALL_MOD_GAMES = {}
LINE_JUMP_GAMES = {}
HAS_GAMES = {}
WORST_ERROR_GAME = {}
ACTIVE_DAYS = []
IDLE_DAYS = []
LAST_ITERATION_TIME = datetime.datetime.now()

ALLOWED_IN_BASE = {"AFFINITY_FOR_CROWS", "GROWTH", "EXTRA_STRIKE", "LOVE", "O_NO", "BASE_INSTINCTS", "TRAVELING", "HIGH_PRESSURE", "0", "H20", "AAA", "AA", "A", "ACIDIC", "FIERY", "PSYCHIC", "ELECTRIC", "SINKING_SHIP"}
ALLOWED_IN_BASE_BATMAN = {"AFFINITY_FOR_CROWS", "GROWTH", "EXTRA_STRIKE", "LOVE", "O_NO", "BASE_INSTINCTS", "TRAVELING", "HIGH_PRESSURE"}
FORCE_REGEN = {"AFFINITY_FOR_CROWS", "GROWTH", "TRAVELING", "SINKING_SHIP"}
DIRECT_MOD_SOLVES = {"psychic", "a", "acidic", "base_instincts", "electric", "fiery", "love"}
CALC_MOD_SUCCESS = {"psychic", "aa", "acidic", "aaa", "base_instincts", "electric", "fiery", "love", "high_pressure", "a", "0", "o_no", "h20"}

BIRD_WEATHER = get_weather_idx("Birds")
FLOOD_WEATHER = get_weather_idx("Flooding")


def get_pitcher_id_lookup(filename):
    with open(filename) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]        
    return {row["id"]: (row["name"], row["team"]) for row in filedata}
    #experimenting with not caring about if the pitcher id is actually identified as a rotation position in the stlats file
    #return {row["id"]: (row["name"], row["team"]) for row in filedata if row["position"] == "rotation"}

def get_player_id_lookup(filename):
    with open(filename) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    return {row["id"]: (row["name"], row["team"]) for row in filedata}

def get_games(filename):
    with open(filename) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True) if row]
    return filedata

def get_batters(filename):
    with open(filename) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    return filedata

def get_crimes(filename):
    with open(filename) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    return filedata

def pair_crimes_with_batter(crimes, team_stat_data, season, day):
    select_crimes = [crime for crime in crimes if int(crime["season"]) == season and int(crime["day"]) == day]
    stolen_bases = collections.defaultdict(lambda: {})
    for crime in select_crimes:        
        fulltext = crime["event_text"]
        fulltext = fulltext.replace("{","")
        fulltext = fulltext.replace("}","")
        splittext = fulltext.split(",")
        for line in splittext:
            if "steals" in line:
                parsedline = line.split(" steals ")
                criminal_name = parsedline[0]                
            #elif ("Grind Rail" in line and "Safe!" in line):
            #    parsedline = line.split(" hops ")
            #    criminal_name = parsedline[0]                
            else:
                continue
            criminal_name = criminal_name.replace("\"","")
            criminal_team = get_team_name(crime["batter_team_id"], season, day)
            for batter in team_stat_data[criminal_team]:                
                if team_stat_data[criminal_team][batter]["name"] == criminal_name:
                    #print("Criminal {} found! Guilty of a successful base steal because of text {}".format(criminal_name, line))
                    if batter not in stolen_bases:
                        stolen_bases[batter] = 0
                    stolen_bases[batter] += 1                    
    return stolen_bases

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
        if (len(games) == 2) and (games[0]["pitcher_is_home"] != games[1]["pitcher_is_home"]):            
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
        "homeInningsPitched": int(game["home"]["innings_pitched"]),
        "awayInningsPitched": int(game["away"]["innings_pitched"])
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

def calc_unexvar(atbat_failby, hit_failby, hr_failby, hit_real_val, hr_real_val, batman_unexvar):    
    batman_unexvar += (atbat_failby ** 2.0) + (hit_failby ** 2.0) + (hr_failby ** 2.0)
    if (-1 * hit_real_val) == hit_failby:
        batman_unexvar += 5000000.0
    if (-1 * hr_real_val) == hr_failby:
        batman_unexvar += 15000000.0
    return batman_unexvar

def calc_maxes(batman_max_err, batman_min_err, batman_max_val, batman_min_val, bat_atbat_failby, bat_hit_failby, bat_hr_failby, atbat_real_val, hit_real_val, hr_real_val):
    if bat_atbat_failby > batman_max_err["abs"]:
        batman_max_err["abs"] = bat_atbat_failby
        batman_max_val["abs"] = atbat_real_val
    if bat_hit_failby > batman_max_err["hits"]:
        batman_max_err["hits"] = bat_hit_failby
        batman_max_val["hits"] = hit_real_val
    if bat_hr_failby > batman_max_err["hrs"]:
        batman_max_err["hrs"] = bat_hr_failby
        batman_max_val["hrs"] = hr_real_val

    if bat_atbat_failby < batman_min_err["abs"]:
        batman_min_err["abs"] = bat_atbat_failby
        batman_min_val["abs"] = atbat_real_val
    if bat_hit_failby < batman_min_err["hits"]:
        batman_min_err["hits"] = bat_hit_failby
        batman_min_val["hits"] = hit_real_val
    if bat_hr_failby < batman_min_err["hrs"]:
        batman_min_err["hrs"] = bat_hr_failby
        batman_min_val["hrs"] = hr_real_val    

    return batman_max_err, batman_min_err, batman_max_val, batman_min_val

def track_errors(bat_atbat_failby, bat_hit_failby, bat_hr_failby, atbat_real_val, hit_real_val, hr_real_val, pos_error, zero_error, pos_counter, zero_counter):
    pos_error["abs"] += abs(bat_atbat_failby)
    pos_counter["abs"] += 1
    if hit_real_val > 0:
        pos_error["hits"] += abs(bat_hit_failby)
        pos_counter["hits"] += 1
    else:
        zero_error["hits"] += abs(bat_hit_failby)
        zero_counter["hits"] += 1
    if hr_real_val > 0:
        pos_error["hrs"] += abs(bat_hr_failby)
        pos_counter["hrs"] += 1
    else:
        zero_error["hrs"] += abs(bat_hr_failby)
        zero_counter["hrs"] += 1
    return pos_error, zero_error, pos_counter, zero_counter
                  
def check_margins(eventlist, bat_atbat_failby, bat_hit_failby, bat_hr_failby, stages, pass_within_four, pass_within_three, pass_within_two, pass_within_one, pass_exact):
    for event in eventlist:
        if event == "abs":
            check_fail = bat_atbat_failby             
        elif event == "hits":
            check_fail = bat_hit_failby
        else:
            check_fail = bat_hr_failby
        #print("stages for {} = {}".format(event, stages[event]))
        if abs(check_fail) < stages[event][0]:             
            pass_within_four[event] += 1
            #print("{} pass within {}, {:.4f}".format(event, stages[event][0], abs(check_fail)))
            if abs(check_fail) < stages[event][1]:
                pass_within_three[event] += 1
                if abs(check_fail) < stages[event][2]:
                    pass_within_two[event] += 1
                    if abs(check_fail) < stages[event][3]:
                        pass_within_one[event] += 1
                        if abs(check_fail) <= stages[event][4]:
                            pass_exact[event] += 1   
    return pass_within_four, pass_within_three, pass_within_two, pass_within_one, pass_exact
    
def check_rejects(min_condition, max_condition, eventlist, stages, batman_unexvar):    
    if FIRST_SOLUTION and (CURRENT_ITERATION > 1):
        for event in eventlist:
            #experiment with making this only care about max again
            #if abs(min_condition[event]) >= (MAX_INTEREST[event] - stages[event][4]):                                            
                #return True        
                    
            #elif max(abs(min_condition[event]), max_condition[event]) >= LAST_BESTS[event]:                            
            #    return True                
            
            if max(max_condition[event], abs(min_condition[event])) >= (LAST_BEST - stages[event][4]):                            
                return True                
                     
        if not (batman_unexvar == None):
            if batman_unexvar >= BEST_UNEXVAR_ERROR:                                        
                return True                                                             
    return False

def calc_linear_unex_error(vals, wins_losses, modname=None):    
    max_error_game = ""
    error, max_error, min_error, max_error_val, min_error_val, current_val = 0.0, 0.0, 150.0, 0.0, 0.0, 0.0    
    exponent = 4 if (modname in DIRECT_MOD_SOLVES or modname == "overall") else 6
    window_size, half_window = 100, 50
    #window_size = 300 if (modname == "unmod" or modname == "overall") else 100
    #half_window = 150 if (modname == "unmod" or modname == "overall") else 50
    wins = []
    win_threshold = False    
    idx = (window_size - 1)
    wins = wins_losses[:idx]    
    while (idx < len(vals)):                 
        wins.append(wins_losses[idx])                
        if len(wins) >= window_size:
            current_val = vals[idx - half_window] * 100.0
            total_wins = sum(wins[-window_size:])
            if (total_wins > 1):
                win_threshold = True            
            if win_threshold:
                actual_val = total_wins * (100.0 / window_size)
                current_error = max(abs(current_val - actual_val), 1.0) - 1.0
                if ((actual_val > 50.0) and (current_val < 50.0)) or ((actual_val < 50.0) and (current_val > 50.0)):
                    current_error *= 2.0
                error += current_error ** exponent                               
                if ((current_val - actual_val) > max_error):
                    max_error = (current_val - actual_val)
                    max_error_val = current_val                                
                if ((current_val - actual_val) < min_error):
                    min_error = (current_val - actual_val)
                    min_error_val = current_val                                       
        idx += 1    
    error += (max_error ** (exponent + 2)) + (abs(min_error ** (exponent + 2)))    
    error *= 0.01
    return error, max_error, min_error, max_error_val, min_error_val

def store_ev_by_team(ev_by_team, hometeam, awayteam, web_ev, mofo_ev):
    if hometeam not in ev_by_team:
        ev_by_team[hometeam] = {}
        ev_by_team[hometeam]["web_ev"] = 0
        ev_by_team[hometeam]["mofo_ev"] = 0
        ev_by_team[hometeam]["net_ev"] = 0
    ev_by_team[hometeam]["web_ev"] += web_ev
    ev_by_team[hometeam]["mofo_ev"] += mofo_ev
    ev_by_team[hometeam]["net_ev"] = ev_by_team[hometeam]["mofo_ev"] - ev_by_team[hometeam]["web_ev"]

    if awayteam not in ev_by_team:
        ev_by_team[awayteam] = {}
        ev_by_team[awayteam]["web_ev"] = 0
        ev_by_team[awayteam]["mofo_ev"] = 0
        ev_by_team[awayteam]["net_ev"] = 0
    ev_by_team[awayteam]["web_ev"] += web_ev
    ev_by_team[awayteam]["mofo_ev"] += mofo_ev
    ev_by_team[awayteam]["net_ev"] = ev_by_team[awayteam]["mofo_ev"] - ev_by_team[awayteam]["web_ev"]
    
    return ev_by_team

def game_ev_calculate(ev_set, game):
    net_payout, web_payout, dadbets, mismatches, season_ev, season_web_ev = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0    
    gameid = ev_set[game]
    #set winning mofoodds equal to the mofo odds for whichever team actually won the game (max odds if favorite; min odds otherwise)
    if gameid["favorite_won"]:
        winning_mofoodds = max(gameid["mofoodds"], 1.0 - gameid["mofoodds"])            
    else:
        winning_mofoodds = min(gameid["mofoodds"], 1.0 - gameid["mofoodds"])     
    #set winning webodds; we store webodds and mofoodds for the away team, so if winning mofoodds is the away odds we also want the away webodds
    winning_webodds = gameid["webodds"] if (winning_mofoodds == gameid["mofoodds"]) else (1.0 - gameid["webodds"])
    #dadbets only exist for the mofo underdog
    dadbet_mofoodds = min(gameid["mofoodds"], 1.0 - gameid["mofoodds"])
    #webodss for dadbets need to match, just as above, so get the matching webodds
    dadbet_webodds = gameid["webodds"] if (dadbet_mofoodds == gameid["mofoodds"]) else (1.0 - gameid["webodds"])
    payout = round(webodds_payout(winning_webodds, 1000.0))             
    mismatch = ((gameid["mofoodds"] > 0.5) and (gameid["webodds"] < 0.5)) or ((gameid["mofoodds"] < 0.5) and (gameid["webodds"] > 0.5))
    dadbet = (round(webodds_payout(dadbet_webodds, 1000.0)) * dadbet_mofoodds) > (round(webodds_payout((1.0 - dadbet_webodds), 1000.0)) * (1.0 - dadbet_mofoodds))
    #if mismatch:
        #print("mismatch! mofo odds {}, web odds {}".format(gameid["mofoodds"], gameid["webodds"]))
    if dadbet:
        if not gameid["favorite_won"]:
            net_payout += payout - 1000.0
            dadbets += payout - 1000.0
        else:
            net_payout -= 1000.0
            dadbets -= 1000.0
    elif gameid["favorite_won"]:
        if mismatch:                
            mismatches += payout - 1000.0                                    
        net_payout += payout - 1000.0
    else:
        if mismatch:
            mismatches -= 1000.0
        net_payout -= 1000.0
    if winning_webodds > 0.5:
        web_payout += payout - 1000.0
    else:
        web_payout -= 1000.0    
    #print("Winning webodds = {:.4f}, winning mofoodds = {:.4f}, mismatch = {}, dadbet = {}, web pay = {:.4f}, mofopay = {:.4f}".format(winning_webodds, winning_mofoodds, mismatch, dadbet, web_payout, net_payout))
    ev = net_payout / 1000.0
    mismatches = mismatches / 1000.0
    dadbets = dadbets / 1000.0
    web_ev = web_payout / 1000.0
    if gameid["season"] == MAX_SEASON:
        season_ev = ev
        season_web_ev = web_ev
    return ev, mismatches, dadbets, web_ev, season_ev, season_web_ev

def webodds_payout(odds, amt):
    if odds == .5:
        return 2 * amt
    if odds < .5:
        return amt * (2 + (.0015 * ((100 * (.5 - odds)) ** 2.2)))
    else:
        return amt * (3.206 / (1 + ((.443 * (odds - .5)) ** .95)) - 1.206)

def write_file(outputdir, run_id, filename, content):
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
    with open(os.path.join(outputdir, "{}-{}".format(run_id, filename)), "w") as f:
        f.write(content)

def write_final(outputdir, filename, content):
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
    with open(os.path.join(outputdir, filename), "w") as f:
        f.write(content)


def write_parameters(outputdir, run_id, filename, parameters):
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
    with open(os.path.join(outputdir, "{}-{}".format(run_id, filename)), "w") as f:
        json.dump(list(parameters), f)


#for mofo and k9
def minimize_func(parameters, *data):
    run_id = uuid.uuid4()
    starttime = datetime.datetime.now()
    global BEST_RESULT
    global BEST_SEASON
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
    global EXPECTED_MOD_RATES        
    global ALL_MOD_GAMES
    global ALL_UNMOD_GAMES    
    global WORST_ERROR_GAME
    global MAX_ERROR_GAMES
    global ERROR_THRESHOLD
    global ALL_GAMES
    global WORST_MOD
    global LAST_UNMOD
    global PLUS_NAME
    global HAS_GAMES
    global WORST_ERROR
    global LAST_ITERATION_TIME
    global PASSED_GAMES    
    global LINE_JUMP_GAMES    
    global PREVIOUS_LAST_BEST
    global BEST_AGG_FAIL_RATE
    global LAST_BEST
    global LAST_SPAN
    global LAST_DAY_RANGE
    global LAST_SEASON_RANGE
    global REJECTS
    global EARLY_REJECT
    global MIN_DAY
    global MAX_DAY
    global BROAD_ERROR_THRESHOLD
    global ACTIVE_DAYS
    global IDLE_DAYS
    calc_func, stlat_list, special_case_list, mod_list, ballpark_list, stat_file_map, ballpark_file_map, game_list, team_attrs, number_to_beat, solve_for_ev, final_solution, solved_terms, solved_halfterms, solved_mods, solved_ballpark_mods, batter_list, crimes_list, solve_batman_too, debug, debug2, debug3, outputdir = data    
    debug_print("func start: {}".format(starttime), debug3, run_id)
    if number_to_beat is not None:
        BEST_RESULT = number_to_beat if (number_to_beat < BEST_RESULT) else BEST_RESULT
    special_case_list = special_case_list or []            
    park_mod_list_size = len(ballpark_list) * 3
    team_mod_list_size = len(mod_list)
    special_cases_count = len(special_case_list)
    total_parameters = len(parameters)
    base_mofo_list_size = total_parameters - special_cases_count - park_mod_list_size - team_mod_list_size
    terms = solved_terms if solved_terms else collections.defaultdict(lambda: {})    
    if base_mofo_list_size > 0:
        for stat, (a, b, c) in zip(stlat_list, zip(*[iter(parameters[:base_mofo_list_size])] * 3)):
            use_a = 0.0 if (math.isnan(a)) else a            
            use_b = 0.0 if (math.isnan(b)) else b            
            use_c = 0.0 if (math.isnan(c)) else c
            terms[stat] = StlatTerm(use_a, use_b, use_c)        
    mods = solved_mods if solved_mods else collections.defaultdict(lambda: {"opp": {}, "same": {}})    
    ballpark_mods = solved_ballpark_mods if solved_ballpark_mods else collections.defaultdict(lambda: {"bpterm": {}})
    half_stlats = solved_halfterms if solved_halfterms else collections.defaultdict(lambda: {})
    mod_mode = True
    if team_mod_list_size > 0:
        for mod, a in zip(mod_list, parameters[(base_mofo_list_size + special_cases_count):(total_parameters-park_mod_list_size)]):                  
            use_a = 0.0 if (math.isnan(a)) else a                      
            mods[mod.attr.lower()][mod.team.lower()][mod.stat.lower()] = use_a
    if park_mod_list_size > 0:
        for bp, (a, b, c) in zip(ballpark_list, zip(*[iter(parameters[-park_mod_list_size:])] * 3)):   
            use_a = 0.0 if (math.isnan(a)) else a            
            use_b = 0.0 if (math.isnan(b)) else b            
            use_c = 0.0 if (math.isnan(c)) else c
            ballpark_mods[bp.ballparkstat.lower()][bp.playerstat.lower()] = ParkTerm(use_a, use_b, use_c)                   
    if special_cases_count > 0:
        for halfterm, a in zip(special_case_list, parameters[base_mofo_list_size:-(team_mod_list_size + park_mod_list_size)]):        
            use_a = 0.0 if (math.isnan(a)) else a            
            half_stlats[halfterm.stat.lower()][halfterm.event.lower()] = use_a        
    game_counter, fail_counter, season_game_counter, half_fail_counter, pass_exact, pass_within_one, pass_within_two, pass_within_three, pass_within_four = 0, 0, 0, 1000000000, 0, 0, 0, 0, 0
    quarter_fail = 100.0
    linear_fail = 100.0
    batman_error = 0.0
    linear_error, check_fail_rate, web_margin, early_linear, last_linear, worstmod_linear_error, unmod_linear_error = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    max_linear_error, min_linear_error, unmod_max_linear_error, unmod_min_linear_error, max_error_value, min_error_value = 0.0, 150.0, 0.0, 150.0, 0.0, 0.0
    max_error_mod, min_error_mod = "", ""
    love_rate, instinct_rate, ono_rate, wip_rate, exk_rate, exb_rate, unmod_rate = 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0
    k9_max_err, k9_min_err, ljg_passed, ev_neg_count, lastlin_games = 0, 0, 0, 0, 1
    season_ev, season_web_ev, max_team_ev, min_team_ev, max_run_span = 0.0, 0.0, -1000.0, 1000.0, 1000.0
    mod_fails, mod_games, mod_rates, mod_web_fails = {}, {}, {}, {}
    multi_mod_fails, multi_mod_games, multi_mod_web_fails, mvm_fails, mvm_games, mvm_web_fails, ljg_fail_savings = 0, 0, 0, 0, 0, 0, 0
    unmod_fails, unmod_games, unmod_rate, unmod_web_fails = 0, 0, 0.0, 0
    reject_solution, viability_unchecked, new_pass, addfails, stats_regened, early_linear_checked = False, True, False, False, False, True
    line_jumpers, reorder_failsfirst, reorder_keys, ev_set, ev_by_team, games_by_mod, vals_by_mod = {}, {}, {}, {}, {}, {}, {}
    all_vals, win_loss, gameids, early_vals, early_sorted, pos_vals = [], [], [], [], [], []
    worst_vals, worst_win_loss, worst_gameids, overall_vals, overall_win_loss, overall_gameids, remove_list = [], [], [], [], [], [], []
    awayAttrs, homeAttrs = [], []

    if solve_batman_too:
        solved_hits, solved_homers = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})        
        solved_seeddogs, real_seeddogs = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})        
        solved_ks, solved_era, solved_meatballs = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
        solved_chipsmeatballs = collections.defaultdict(lambda: {})
        seeds_score, seeds_score_earned, seeds_score_max = 0.0, 0.0, 0.0
        dogs_score, dogs_score_earned, dogs_score_max = 0.0, 0.0, 0.0
        seeddogs_score, seeddogs_score_earned, seeddogs_score_max = 0.0, 0.0, 0.0
        chips_score, chips_score_earned, chips_score_max = 0.0, 0.0, 0.0
        burgers_score, burgers_score_earned, burgers_score_max = 0.0, 0.0, 0.0
        meatballs_score, meatballs_score_earned, meatballs_score_max = 0.0, 0.0, 0.0
        chipsburgers_score, chipsburgers_score_earned, chipsburgers_score_max = 0.0, 0.0, 0.0
        chipsmeatballs_score, chipsmeatballs_score_earned, chipsmeatballs_score_max = 0.0, 0.0, 0.0
        hitters, sluggers, seeddogers, chips_pitchers, sho_pitchers = 0, 0, 0, 0, 0
        if crimes_list is not None:
            solved_steals, solved_seedpickles = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
            solved_dogpickles, solved_trifecta = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})            
            pickles_score, pickles_score_earned, pickles_score_max = 0.0, 0.0, 0.0
            seedpickles_score, seedpickles_score_earned, seedpickles_score_max = 0.0, 0.0, 0.0
            dogpickles_score, dogpickles_score_earned, dogpickles_score_max = 0.0, 0.0, 0.0
            trifecta_score, trifecta_score_earned, trifecta_score_max = 0.0, 0.0, 0.0
            thieves = 0

    adjustments = {}
    for stlat in half_stlats:
        for event in half_stlats[stlat]:                        
            adjustments[event] = terms[event].calc(half_stlats[stlat][event])    

    if ALL_GAMES > 0:       
        games_available = ALL_GAMES - len(LINE_JUMP_GAMES)
    else:
        games_available = 1188    

    if solve_for_ev and (ALL_GAMES > 0):
        fail_threshold = BEST_FAILCOUNT            
    LINE_JUMP_GAMES.clear()    

    seasonrange = reversed(range(MIN_SEASON, MAX_SEASON + 1))
    dayrange = range(MIN_DAY, MAX_DAY + 1)
    days_to_solve = 50 if solve_for_ev else 99      

    for season in seasonrange:
        if reject_solution:            
            break
        # if (season in HAS_GAMES and not HAS_GAMES[season]) or season < 12:
        if (season in HAS_GAMES and not HAS_GAMES[season]):
            print("Season {} has no games".format(season))
            continue
        season_start = datetime.datetime.now()
        debug_print("season {} start: {}".format(season, season_start), debug3, run_id)
        pitchers, team_stat_data, pitcher_stat_data, last_stat_filename, ballparks = (None, ) * 5
        season_team_attrs = team_attrs.get(str(season), {})
        season_days = 0       
        if (CURRENT_ITERATION == 1) and (season == MAX_SEASON):
            for day in dayrange:                
                games = [row for row in game_list if row["season"] == str(season) and row["day"] == str(day)]
                if not games:
                    print("Found no games for day {}".format(day))
                    if day == 1:
                        MAX_DAY = 0
                    #else:
                    #    MAX_DAY -= 2
                    #    season_days -= 2
                    break
                else:
                    MAX_DAY = day
                    season_days += 1
            if not MAX_DAY == 0:
                MIN_DAY = (MAX_DAY - (days_to_solve - 1)) if ((MAX_DAY - (days_to_solve - 1)) > 0) else 1        
        if season == MAX_SEASON:
            if MAX_DAY == 0:                
                continue
            else:
                dayrange = range(MIN_DAY, MAX_DAY + 1)
        elif season == (MAX_SEASON - 1):
            if MAX_DAY == 0:
                dayrange = range((100 - days_to_solve), 100)
            elif MAX_DAY >= days_to_solve:
                continue
            else:                
                previous_season_start_day = 100 - (days_to_solve - ((MAX_DAY + 1) - MIN_DAY))
                dayrange = range(previous_season_start_day, 100)
        else:
            continue
            
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
                    print("No games found day {}".format(day))
                    GAME_CACHE[(season, day)] = []                    
                    continue                            
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
                    team_stat_data, pitcher_stat_data = load_stat_data_pid(stat_filename, schedule, day, season_team_attrs)
                    stats_regened = False
                elif should_regen(day_mods):
                    pitchers = get_pitcher_id_lookup(last_stat_filename)
                    team_stat_data, pitcher_stat_data = load_stat_data_pid(last_stat_filename, schedule, day, season_team_attrs)
                    stats_regened = True
                elif stats_regened:
                    pitchers = get_pitcher_id_lookup(last_stat_filename)
                    team_stat_data, pitcher_stat_data = load_stat_data_pid(last_stat_filename, schedule, day, season_team_attrs)
                    stats_regened = False
                STAT_CACHE[(season, day)] = (team_stat_data, pitcher_stat_data, pitchers)                
            if not pitchers:
                print("Failed to have pitchers for day {}".format(day))
                raise Exception("No stat file found")
            #print("Pitchers for season {} day {}: = {}".format(season, day, pitchers))            
            cached_ballparks = BALLPARK_CACHE.get((season, day))
            if cached_ballparks is None:
                ballpark_filename = ballpark_file_map.get((season, day))
                if CURRENT_ITERATION > 1:
                    print("Ballparks not cached, season {}, day {}".format(season, day))
                if (CURRENT_ITERATION == 1) and not ballpark_filename:
                    for backday in reversed(range(1, day)):
                        ballpark_filename = ballpark_file_map.get((season, backday))
                        if ballpark_filename:
                            break
                    if not ballpark_filename:
                        ballpark_filename = ballpark_file_map.get((season-1, 73))
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
            if solve_batman_too:                
                using_cached_batters = True
                real_hits = HITS_CACHE.get((season, day))                
                if CURRENT_ITERATION > 1 and not real_hits:
                    print("Missing cached hits for day {}".format(day))                    
                if not real_hits:                    
                    batter_perf_data = [row for row in batter_list if row["season"] == str(season) and row["day"] == str(day)]                                    
                    using_cached_batters = False
                    if not batter_perf_data:                            
                        HITS_CACHE[(season, day)] = []
                        HOMERS_CACHE[(season, day)] = []
                        SEEDDOGS_CACHE[(season, day)] = []
                        SHO_CACHE[(season, day)] = []
                        KS_CACHE[(season, day)] = []
                        MEATBALLS_CACHE[(season, day)] = []
                        CHIPSBURGERS_CACHE[(season, day)] = []
                        CHIPSMEATBALLS_CACHE[(season, day)] = []
                        continue
                    real_hits, real_homers, real_seeddogs, real_meatballs, real_ks, real_chipsmeatballs, real_chipsburgers = {}, {}, {}, {}, {}, {}, {}
                    real_sho = []                    
                    if crimes_list is not None:
                        real_seedpickles, real_dogpickles, real_trifecta = {}, {}, {}
                        real_steals = pair_crimes_with_batter(crimes_list, team_stat_data, season, day)                        
                    for batter in batter_perf_data:                
                        real_hits[batter["batter_id"]] = int(batter["hits"])
                        real_homers[batter["batter_id"]] = int(batter["home_runs"])
                        real_seeddogs[batter["batter_id"]] = (int(batter["hits"]) * 1.5) + (int(batter["home_runs"]) * 4.0)
                        if crimes_list is not None:
                            if batter["batter_id"] not in real_steals:
                                real_steals[batter["batter_id"]] = 0
                            real_seedpickles[batter["batter_id"]] = (real_steals[batter["batter_id"]] * 3.0) + (real_hits[batter["batter_id"]] * 1.5)
                            real_dogpickles[batter["batter_id"]] = (real_steals[batter["batter_id"]] * 3.0) + (real_homers[batter["batter_id"]] * 4.0)
                            real_trifecta[batter["batter_id"]] = (real_steals[batter["batter_id"]] * 3.0) + (real_hits[batter["batter_id"]] * 1.5) + (real_homers[batter["batter_id"]] * 4.0)
                        if batter["pitcher_id"] not in real_meatballs:
                            real_meatballs[batter["pitcher_id"]] = 0
                            real_chipsmeatballs[batter["pitcher_id"]] = 0
                        real_meatballs[batter["pitcher_id"]] += int(batter["home_runs"])
                        real_chipsmeatballs[batter["pitcher_id"]] += int(batter["home_runs"])
                    sorted_real_hits, sorted_real_homers = dict(sorted(real_hits.items(), key=lambda k: k[1], reverse=True)), dict(sorted(real_homers.items(), key=lambda k: k[1], reverse=True))
                    sorted_real_seeddogs = dict(sorted(real_seeddogs.items(), key=lambda k: k[1], reverse=True))
                    HITS_CACHE[(season, day)] = copy.deepcopy(sorted_real_hits)
                    HOMERS_CACHE[(season, day)] = copy.deepcopy(sorted_real_homers)
                    SEEDDOGS_CACHE[(season, day)] = copy.deepcopy(sorted_real_seeddogs)                    
                    if crimes_list is not None:
                        sorted_real_steals, sorted_real_seedpickles = dict(sorted(real_steals.items(), key=lambda k: k[1], reverse=True)), dict(sorted(real_seedpickles.items(), key=lambda k: k[1], reverse=True))
                        sorted_real_dogpickles, sorted_real_trifecta = dict(sorted(real_dogpickles.items(), key=lambda k: k[1], reverse=True)), dict(sorted(real_trifecta.items(), key=lambda k: k[1], reverse=True))
                        STEALS_CACHE[(season, day)] = copy.deepcopy(sorted_real_steals)
                        SEEDPICKLES_CACHE[(season, day)] = copy.deepcopy(sorted_real_seedpickles)
                        DOGPICKLES_CACHE[(season, day)] = copy.deepcopy(sorted_real_dogpickles)
                        TRIFECTA_CACHE[(season, day)] = copy.deepcopy(sorted_real_trifecta)
                else:
                    #if we have a cache of hits, we'll have the other caches too
                    real_homers = HOMERS_CACHE.get((season, day))
                    real_seeddogs = SEEDDOGS_CACHE.get((season, day))   
                    real_sho = SHO_CACHE.get((season, day))
                    real_ks = KS_CACHE.get((season, day))
                    real_meatballs = MEATBALLS_CACHE.get((season, day))
                    real_chipsburgers = CHIPSBURGERS_CACHE.get((season, day))
                    real_chipsmeatballs = CHIPSMEATBALLS_CACHE.get((season, day))
                    if crimes_list is not None:
                        real_steals = STEALS_CACHE.get((season, day))
                        real_seedpickles = SEEDPICKLES_CACHE.get((season, day))
                        real_dogpickles = DOGPICKLES_CACHE.get((season, day))
                        real_trifecta = TRIFECTA_CACHE.get((season, day))
            for game in paired_games:
                if game["away"]["game_id"] in LINE_JUMP_GAMES:
                    print("Should never see this at this point; no games are being line jumped")
                    continue
                homePitcher, homePitcherTeam = pitchers.get(game["home"]["pitcher_id"])
                if int(pitcher_stat_data[homePitcher]["innings"]) > 9:
                    #print("Skipping game because of extra innings")
                    continue
                if int(pitcher_stat_data[homePitcher]["innings"]) < 8:
                    #print("Skipping game because of too few innings")
                    continue                
                if game["away"]["game_id"] in ATTRS_CACHE:
                    awayAttrs = ATTRS_CACHE[game["away"]["game_id"]][game["away"]["team_id"]]
                    homeAttrs = ATTRS_CACHE[game["away"]["game_id"]][game["home"]["team_id"]]
                else:                          
                    awayAttrs.clear(), homeAttrs.clear()
                    game_attrs = get_attrs_from_paired_game(season_team_attrs, game)
                    for attr in game_attrs["away"]:
                        if attr.lower() != "":
                            awayAttrs.append(attr.lower())
                    for attr in game_attrs["home"]:
                        if attr.lower() != "":
                            homeAttrs.append(attr.lower())                    
                    ATTRS_CACHE[game["away"]["game_id"]] = {}
                    ATTRS_CACHE[game["away"]["game_id"]][game["away"]["team_id"]] = copy.deepcopy(awayAttrs)
                    ATTRS_CACHE[game["away"]["game_id"]][game["home"]["team_id"]] = copy.deepcopy(homeAttrs)                                        
                gamehomeTeam = get_team_name(game["home"]["team_id"], season, day)
                gameawayTeam = get_team_name(game["away"]["team_id"], season, day)     
                if not using_cached_batters:
                    if float(game["home"]["opposing_team_rbi"]) == 0.0:
                        real_sho.append(game["home"]["pitcher_id"])
                        real_chipsburgers[game["home"]["pitcher_id"]] = int(game["home"]["strikeouts"])
                    if float(game["away"]["opposing_team_rbi"]) == 0.0:
                        real_sho.append(game["away"]["pitcher_id"])
                        real_chipsburgers[game["away"]["pitcher_id"]] = int(game["away"]["strikeouts"])
                    real_ks[game["home"]["pitcher_id"]] = int(game["home"]["strikeouts"])
                    real_ks[game["away"]["pitcher_id"]] = int(game["away"]["strikeouts"])
                    if game["home"]["pitcher_id"] not in real_chipsmeatballs:
                        real_chipsmeatballs[game["home"]["pitcher_id"]] = 0.0
                    real_chipsmeatballs[game["home"]["pitcher_id"]] += int(game["home"]["strikeouts"]) * 0.2
                    if game["away"]["pitcher_id"] not in real_chipsmeatballs:
                        real_chipsmeatballs[game["away"]["pitcher_id"]] = 0.0
                    real_chipsmeatballs[game["away"]["pitcher_id"]] += int(game["away"]["strikeouts"]) * 0.2
                if game["away"]["game_id"] in ADJUSTED_STAT_CACHE:                    
                    adjusted_stat_data = ADJUSTED_STAT_CACHE[game["away"]["game_id"]]
                else:
                    adjusted_stat_data = calculate_adjusted_stat_data(awayAttrs, homeAttrs, gameawayTeam, gamehomeTeam, team_stat_data)
                    ADJUSTED_STAT_CACHE[game["away"]["game_id"]] = adjusted_stat_data
                ballpark = ballparks.get(game["home"]["team_id"], collections.defaultdict(lambda: 0.5))
                if solve_batman_too:
                    #try:
                    game_game_counter, game_fail_counter, game_away_val, game_home_val, away_hits, home_hits, away_homers, home_homers, away_stolen_bases, home_stolen_bases, away_pitcher_ks, home_pitcher_ks, away_pitcher_era, home_pitcher_era = calc_func(game, awayAttrs, homeAttrs, team_stat_data, pitcher_stat_data, pitchers, terms, mods, ballpark, ballpark_mods, adjusted_stat_data, adjustments, True)          
                    solved_hits, solved_homers = {**solved_hits, **away_hits, **home_hits}, {**solved_homers, **away_homers, **home_homers}
                    if crimes_list is not None:
                        solved_steals = {**solved_steals, **away_stolen_bases, **home_stolen_bases}
                    solved_ks[game["away"]["pitcher_id"]], solved_ks[game["home"]["pitcher_id"]] = away_pitcher_ks, home_pitcher_ks
                    solved_era[game["away"]["pitcher_id"]], solved_era[game["home"]["pitcher_id"]] = away_pitcher_era, home_pitcher_era
                    total_away_homers, total_home_homers = sum(away_homers.values()), sum(home_homers.values())
                    solved_meatballs[game["away"]["pitcher_id"]], solved_meatballs[game["home"]["pitcher_id"]] = total_home_homers, total_away_homers
                    #except ValueError:
                    #    print("Missing values for some reason? Day {}, Game {}".format(day, game["away"]["game_id"]))
                    #    batter_remove_data = [row for row in batter_list if row["season"] == str(season) and row["day"] == str(day) and row["game_id"] == game["away"]["game_id"]]
                    #    for batter in batter_remove_data:
                    #        if batter["batter_id"] in HITS_CACHE[(season, day)]:
                    #            HITS_CACHE[(season, day)].pop(batter["batter_id"])
                    #            HOMERS_CACHE[(season, day)].pop(batter["batter_id"])
                    #            SEEDDOGS_CACHE[(season, day)].pop(batter["batter_id"])
                    #    continue                    
                else:
                    game_game_counter, game_fail_counter, game_away_val, game_home_val = calc_func(game, season_team_attrs, team_stat_data, pitcher_stat_data, pitchers, terms, mods, ballpark, ballpark_mods, adjusted_stat_data, adjustments, False)                
                if not is_cached and game_game_counter:
                    good_game_list.extend([game["home"], game["away"]])
                    HAS_GAMES[season] = True
                elif game_game_counter == 0:
                    print("Game being omitted somehow, {}".format(game))
                game_counter += game_game_counter                
                if game_game_counter == 1:   
                    ev_set[game["away"]["game_id"]] = {}
                    ev_set[game["away"]["game_id"]]["mofoodds"] = game_away_val
                    ev_set[game["away"]["game_id"]]["webodds"] = float(game["away"]["webodds"])
                    ev_set[game["away"]["game_id"]]["season"] = season
                    all_vals.append(game_away_val)                       
                    gameids.append(game["away"]["game_id"])
                    if game_fail_counter == 0:
                        ev_set[game["away"]["game_id"]]["favorite_won"] = True
                    else:
                        ev_set[game["away"]["game_id"]]["favorite_won"] = False
                    if (game_away_val > 0.5 and game_fail_counter == 0) or (game_away_val < 0.5 and game_fail_counter == 1):                        
                        win_loss.append(1)
                        win_loss.append(0)                
                    else:                        
                        win_loss.append(0)
                        win_loss.append(1)
                    gameids.append(game["home"]["game_id"])
                    all_vals.append(game_home_val)                      
                    game_ev, game_mismatch, game_dadbets, game_web_ev, season_ev, season_web_ev = game_ev_calculate(ev_set, game["away"]["game_id"])    
                    if solve_for_ev:
                        game_fail_counter = -game_ev   
                        web_margin -= game_web_ev                                                
                        ev_by_team = store_ev_by_team(ev_by_team, gamehomeTeam, gameawayTeam, game_web_ev, game_ev) 
                        hometeam_ev = ev_by_team[gamehomeTeam]["mofo_ev"] - ev_by_team[gamehomeTeam]["web_ev"] 
                        awayteam_ev = ev_by_team[gameawayTeam]["mofo_ev"] - ev_by_team[gameawayTeam]["web_ev"]
                        max_team_ev, min_team_ev = -1000.0, 1000.0
                        for team in ev_by_team:
                            max_team_ev = ev_by_team[team]["net_ev"] if (ev_by_team[team]["net_ev"] > max_team_ev) else max_team_ev
                            min_team_ev = ev_by_team[team]["net_ev"] if (ev_by_team[team]["net_ev"] < min_team_ev) else min_team_ev                        
                        max_run_span = min_team_ev if (min_team_ev < max_run_span) else max_run_span
                        #game_fail_counter = 1 if (game_ev < 0) else 0            
                    fail_counter += game_fail_counter                                             
                    if solve_for_ev:
                        if game_game_counter > 0:
                            if game_fail_counter > 0:
                                line_jumpers[game["away"]["game_id"]] = game      
                            else:
                                ljg_passed += PASSED_GAMES
                                if ljg_passed >= 1:
                                    line_jumpers[game["away"]["game_id"]] = game                
                                    ljg_passed -= 1
                        ev_neg_count = fail_counter - web_margin if ((fail_counter - web_margin) > ev_neg_count) else ev_neg_count            
                        if CURRENT_ITERATION > 1:                        
                            if ev_neg_count > BEST_FAILCOUNT:
                                reject_solution = True           
                                #print("rejecting solution, game ev = {:.4f}, web ev = {:.4f}, difference = {:.4f}, best difference = {:4f}".format(fail_counter, web_margin, (fail_counter - web_margin), BEST_FAILCOUNT))
                                LINE_JUMP_GAMES.clear()
                                LINE_JUMP_GAMES = line_jumpers                    
                                LAST_BEST = BEST_FAILCOUNT
                                REJECTS += 1
                                break                           
                            if max_run_span < LAST_SPAN:
                                reject_solution = True                        
                                REJECTS += 1                                        
                                #print("Solution rejected for too large a span. {:.2f} this run, {:.2f} last best, {} games".format((max_team_ev - min_team_ev), LAST_SPAN, game_counter))
                                break
                                                   
                    if mod_mode:                        
                        awayMods, homeMods = 0, 0
                        lowerAwayAttrs = awayAttrs
                        lowerHomeAttrs = homeAttrs
                        allAttrs_lol = [lowerAwayAttrs, lowerHomeAttrs]
                        allAttrs_set = set().union(*allAttrs_lol)                        
                        allModAttrs_set = allAttrs_set.intersection(CALC_MOD_SUCCESS)
                        modAttrs = list(allModAttrs_set)
                        for name in modAttrs:  
                            if name.upper() in FORCE_REGEN:
                                continue
                            if name not in mod_games:
                                mod_fails[name] = 0
                                mod_games[name] = 0
                                mod_web_fails[name] = 0
                            if name not in games_by_mod:
                                games_by_mod[name] = {}
                                vals_by_mod[name] = {}
                            mod_fails[name] += game_fail_counter
                            mod_games[name] += game_game_counter                            
                            if game["away"]["game_id"] not in games_by_mod[name]:
                                games_by_mod[name][game["away"]["game_id"]] = game
                                vals_by_mod[name][game["away"]["game_id"]] = {}
                                vals_by_mod[name][game["away"]["game_id"]]["mofo_away"] = game_away_val
                                vals_by_mod[name][game["away"]["game_id"]]["mofo_home"] = game_home_val
                                if (game_away_val > 0.5 and game_fail_counter == 0) or (game_away_val < 0.5 and game_fail_counter == 1):
                                    vals_by_mod[name][game["away"]["game_id"]]["away_win"] = 1
                                    vals_by_mod[name][game["away"]["game_id"]]["home_win"] = 0
                                else:
                                    vals_by_mod[name][game["away"]["game_id"]]["away_win"] = 0
                                    vals_by_mod[name][game["away"]["game_id"]]["home_win"] = 1
                            if solve_for_ev:
                                mod_web_fails[name] -= game_web_ev
                            if name in DIRECT_MOD_SOLVES:
                                if name in lowerAwayAttrs:
                                    awayMods += 1  
                                if name in lowerHomeAttrs:
                                    homeMods += 1
                        if reject_solution:
                            break                       
                        if (homeMods > 1) or (awayMods > 1):
                            multi_mod_fails += game_fail_counter
                            multi_mod_games += game_game_counter
                            if solve_for_ev:
                                multi_mod_web_fails -= game_web_ev
                        if awayMods > 0 and homeMods > 0:
                            mvm_fails += game_fail_counter
                            mvm_games += game_game_counter  
                            if solve_for_ev:
                                mvm_web_fails -= game_web_ev
                        elif awayMods == 0 and homeMods == 0:
                            unmod_fails += game_fail_counter  
                            unmod_games += game_game_counter  
                            if "unmod" not in games_by_mod:
                                games_by_mod["unmod"] = {}                                
                                vals_by_mod["unmod"] = {}
                            games_by_mod["unmod"][game["away"]["game_id"]] = game
                            vals_by_mod["unmod"][game["away"]["game_id"]] = {}
                            vals_by_mod["unmod"][game["away"]["game_id"]]["mofo_away"] = game_away_val
                            vals_by_mod["unmod"][game["away"]["game_id"]]["mofo_home"] = game_home_val
                            if (game_away_val > 0.5 and game_fail_counter == 0) or (game_away_val < 0.5 and game_fail_counter == 1):
                                vals_by_mod["unmod"][game["away"]["game_id"]]["away_win"] = 1
                                vals_by_mod["unmod"][game["away"]["game_id"]]["home_win"] = 0
                            else:
                                vals_by_mod["unmod"][game["away"]["game_id"]]["away_win"] = 0
                                vals_by_mod["unmod"][game["away"]["game_id"]]["home_win"] = 1
                            if solve_for_ev:
                                unmod_web_fails -= game_web_ev                                            
            if solve_batman_too:
                #seeddogs has to be determined sometime and requires going through all of the players anyway, unfortunately
                for playerid in solved_hits:
                    solved_seeddogs[playerid] = (solved_hits[playerid] * 1.5) + (solved_homers[playerid] * 4.0)
                    if crimes_list is not None:
                        solved_seedpickles[playerid] = (solved_hits[playerid] * 1.5) + (solved_steals[playerid] * 3.0)
                        solved_dogpickles[playerid] = (solved_homers[playerid] * 4.0) + (solved_steals[playerid] * 3.0)
                        solved_trifecta[playerid] = (solved_hits[playerid] * 1.5) + (solved_homers[playerid] * 4.0) + (solved_steals[playerid] * 3.0)
                for playerid in solved_ks:
                    #for chipsburgers, we would still be prioritizing lowest SHO chance, above all else, so it's a sort by solved era lowest to highest                    
                    solved_chipsmeatballs[playerid] = (solved_ks[playerid] * 0.2) + solved_meatballs[playerid]
                #need to sort real and solved events                
                sorted_solved_hits, sorted_solved_homers = dict(sorted(solved_hits.items(), key=lambda k: k[1], reverse=True)), dict(sorted(solved_homers.items(), key=lambda k: k[1], reverse=True))
                sorted_solved_seeddogs, sorted_solved_meatballs = dict(sorted(solved_seeddogs.items(), key=lambda k: k[1], reverse=True)), dict(sorted(solved_meatballs.items(), key=lambda k: k[1], reverse=True))
                sorted_solved_ks, sorted_solved_era = dict(sorted(solved_ks.items(), key=lambda k: k[1], reverse=True)), dict(sorted(solved_era.items(), key=lambda k: k[1], reverse=False))
                sorted_solved_chipsmeatballs = dict(sorted(solved_chipsmeatballs.items(), key=lambda k: k[1], reverse=True))
                if crimes_list is not None:                    
                    sorted_solved_steals = dict(sorted(solved_steals.items(), key=lambda k: k[1], reverse=True)) 
                    sorted_solved_seedpickles = dict(sorted(solved_seedpickles.items(), key=lambda k: k[1], reverse=True))
                    sorted_solved_dogpickles = dict(sorted(solved_dogpickles.items(), key=lambda k: k[1], reverse=True))
                    sorted_solved_trifecta = dict(sorted(solved_trifecta.items(), key=lambda k: k[1], reverse=True))

                if not using_cached_batters:
                    remove_list.clear()                                                            
                    for batter in HITS_CACHE[(season, day)]:
                        if batter not in solved_hits:                            
                            remove_list.append(batter)                                                 
                    if len(remove_list) > 0:
                        pre_removal_hits_leader = next(iter(HITS_CACHE[(season, day)]))
                        pre_removal_homers_leader = next(iter(HOMERS_CACHE[(season, day)]))
                        pre_removal_seeddogs_leader = next(iter(SEEDDOGS_CACHE[(season, day)]))                        
                        for batter in remove_list:
                            HITS_CACHE[(season, day)].pop(batter)
                            HOMERS_CACHE[(season, day)].pop(batter)
                            SEEDDOGS_CACHE[(season, day)].pop(batter)
                            if crimes_list is not None:
                                if batter in STEALS_CACHE[(season, day)]:
                                    STEALS_CACHE[(season, day)].pop(batter)
                                    SEEDPICKLES_CACHE[(season, day)].pop(batter)
                                    DOGPICKLES_CACHE[(season, day)].pop(batter)
                                    TRIFECTA_CACHE[(season, day)].pop(batter)
                        for batter in batter_perf_data:
                            if (batter["batter_id"] in remove_list) and (batter["pitcher_id"] in real_meatballs):                                 
                                real_meatballs[batter["pitcher_id"]] -= int(batter["home_runs"])
                                real_chipsmeatballs[batter["pitcher_id"]] -= int(batter["home_runs"])
                        if real_hits[pre_removal_hits_leader] != real_hits[next(iter(HITS_CACHE[(season, day)]))]:
                            print("Hits leader changed value from not being a solver option: Previous {}, new {}".format(real_hits[pre_removal_hits_leader], real_hits[next(iter(HITS_CACHE[(season, day)]))]))
                        if real_homers[pre_removal_homers_leader] != real_homers[next(iter(HOMERS_CACHE[(season, day)]))]:
                            print("Homers leader changed value from not being a solver option: Previous {}, new {}".format(real_homers[pre_removal_homers_leader], real_homers[next(iter(HOMERS_CACHE[(season, day)]))]))
                        if real_seeddogs[pre_removal_seeddogs_leader] != real_seeddogs[next(iter(SEEDDOGS_CACHE[(season, day)]))]:
                            print("Seeddogs leader changed value from not being a solver option: Previous {}, new {}".format(real_seeddogs[pre_removal_seeddogs_leader], real_seeddogs[next(iter(SEEDDOGS_CACHE[(season, day)]))]))
                    sorted_real_ks, sorted_real_chipsmeatballs = dict(sorted(real_ks.items(), key=lambda k: k[1], reverse=True)), dict(sorted(real_chipsmeatballs.items(), key=lambda k: k[1], reverse=True))
                    sorted_real_meatballs = dict(sorted(real_meatballs.items(), key=lambda k: k[1], reverse=True))
                    MEATBALLS_CACHE[(season, day)] = copy.deepcopy(sorted_real_meatballs)                   
                    KS_CACHE[(season, day)] = copy.deepcopy(sorted_real_ks)                    
                    CHIPSMEATBALLS_CACHE[(season, day)] = copy.deepcopy(sorted_real_chipsmeatballs)
                    if len(real_sho) > 0:
                        SHO_CACHE[(season, day)] = copy.deepcopy(real_sho)
                        sorted_real_chipsburgers = dict(sorted(real_chipsburgers.items(), key=lambda k: k[1], reverse=True))
                        CHIPSBURGERS_CACHE[(season, day)] = copy.deepcopy(sorted_real_chipsburgers)
                    else:
                        if CURRENT_ITERATION == 1:
                            print("No shutouts on day {}".format(day))
                        SHO_CACHE[(season, day)] = []
                        CHIPSBURGERS_CACHE[(season, day)] = []
                    remove_list.clear()
                    for pitcher in MEATBALLS_CACHE[(season, day)]:
                        if pitcher not in solved_ks:
                            remove_list.append(pitcher)
                    if len(remove_list) > 0:
                        for pitcher in remove_list:
                            MEATBALLS_CACHE[(season, day)].pop(pitcher)
                            CHIPSMEATBALLS_CACHE[(season, day)].pop(pitcher)
                    real_hits = copy.deepcopy(HITS_CACHE.get((season, day)))
                    real_homers = copy.deepcopy(HOMERS_CACHE.get((season, day)))
                    real_seeddogs = copy.deepcopy(SEEDDOGS_CACHE.get((season, day)))
                    real_ks = copy.deepcopy(KS_CACHE.get((season, day)))
                    real_sho = copy.deepcopy(SHO_CACHE.get((season, day)))
                    real_meatballs = copy.deepcopy(MEATBALLS_CACHE.get((season, day)))
                    real_chipsburgers = copy.deepcopy(CHIPSBURGERS_CACHE.get((season, day)))
                    real_chipsmeatballs = copy.deepcopy(CHIPSMEATBALLS_CACHE.get((season, day)))
                    if crimes_list is not None:
                        real_steals = copy.deepcopy(STEALS_CACHE.get((season, day)))
                        real_seedpickles = copy.deepcopy(SEEDPICKLES_CACHE.get((season, day)))
                        real_dogpickles = copy.deepcopy(DOGPICKLES_CACHE.get((season, day)))
                        real_trifecta = copy.deepcopy(TRIFECTA_CACHE.get((season, day)))

                best_seeds_score = real_hits[next(iter(real_hits))]
                best_dogs_score = real_homers[next(iter(real_homers))]
                best_seeddogs_player = next(iter(real_seeddogs))
                best_seeddogs_score = ((real_hits[best_seeddogs_player] * 1.5) + (real_homers[best_seeddogs_player] * 4.0))
                best_chips_score = real_ks[next(iter(real_ks))]                
                best_meatballs_score = real_meatballs[next(iter(real_meatballs))]
                best_chipsmeatballs_player = next(iter(real_chipsmeatballs))
                best_chipsmeatballs_score = (real_ks[best_chipsmeatballs_player] * 0.2) + real_meatballs[best_chipsmeatballs_player]
                if crimes_list is not None:
                    best_pickles_score = real_steals[next(iter(real_steals))]
                    best_seedpickles_player = next(iter(real_seedpickles))
                    best_seedpickles_score = (real_hits[best_seedpickles_player] * 1.5) + (real_steals[best_seedpickles_player] * 3.0)
                    best_dogpickles_player = next(iter(real_dogpickles))
                    best_dogpickles_score = (real_homers[best_dogpickles_player] * 4.0) + (real_steals[best_dogpickles_player] * 3.0)
                    best_trifecta_player = next(iter(real_trifecta))
                    best_trifecta_score = (real_hits[best_trifecta_player] * 1.5) + (real_homers[best_trifecta_player] * 4.0) + (real_steals[best_trifecta_player] * 3.0)

                    for solved_steals_leader in sorted_solved_steals:
                        if solved_steals_leader in real_steals:
                            solved_pickles_score = real_steals[solved_steals_leader]                            
                            pickles_score_earned += solved_pickles_score * 3.0
                            pickles_score_max += best_pickles_score * 3.0   
                            thieves += 1
                            break

                    for solved_seedpickles_leader in sorted_solved_seedpickles:
                        if solved_seedpickles_leader in real_steals:
                            solved_seedpickles_score = (real_hits[solved_seedpickles_leader] * 1.5) + (real_steals[solved_seedpickles_leader] * 3.0)
                            seedpickles_score_earned += solved_seedpickles_score
                            seedpickles_score_max += best_seedpickles_score                               
                            break

                    for solved_dogpickles_leader in sorted_solved_dogpickles:
                        if solved_dogpickles_leader in real_steals:
                            solved_dogpickles_score = (real_homers[solved_dogpickles_leader] * 4.0) + (real_steals[solved_dogpickles_leader] * 3.0)
                            dogpickles_score_earned += solved_dogpickles_score
                            dogpickles_score_max += best_dogpickles_score                               
                            break

                    for solved_trifecta_leader in sorted_solved_trifecta:
                        if solved_trifecta_leader in real_steals:
                            solved_trifecta_score = (real_hits[solved_trifecta_leader] * 1.5) + (real_homers[solved_trifecta_leader] * 4.0) + (real_steals[solved_trifecta_leader] * 3.0)
                            trifecta_score_earned += solved_trifecta_score
                            trifecta_score_max += best_trifecta_score                               
                            break

                if len(real_sho) > 0:
                    best_burgers_score = 12.5
                    best_chipsburgers_player = next(iter(real_chipsburgers))
                    best_chipsburgers_score = (real_ks[best_chipsburgers_player] * 0.2) + 12.5
                    sho_pitchers += 1
                else:
                    best_burgers_score, best_chipsburgers_score = 0.0, 0.0
                #in this case, we need to not penalize the solution just because a batter was queued up by the stlats data that didn't end up performing
                #the solution is still potentially good, but we need to find the top hitter among those we solved for that actually got batstats to compare against the batstat leader
                #for the solution to be good, we need the best hitters and sluggers to be consistently identified from the stlats data
                #solved_hits_leader = next(iter(sorted_solved_hits))
                for solved_hits_leader in sorted_solved_hits:
                    if solved_hits_leader in real_hits:
                        solved_seeds_score = real_hits[solved_hits_leader]                        
                        seeds_score_earned += solved_seeds_score * 1.5
                        seeds_score_max += best_seeds_score * 1.5   
                        hitters += 1
                        break               
                    
                #solved_homers_leader = next(iter(sorted_solved_homers))
                for solved_homers_leader in sorted_solved_homers:
                    if solved_homers_leader in real_homers:
                        solved_dogs_score = real_homers[solved_homers_leader]
                        dogs_ratio = solved_dogs_score / best_dogs_score
                        dogs_score_earned += solved_dogs_score * 4.0
                        dogs_score_max += best_dogs_score * 4.0                        
                        sluggers += 1
                        break                

                #solved_seeddogs_player = next(iter(sorted_solved_seeddogs))
                for solved_seeddogs_player in sorted_solved_seeddogs:
                    if solved_seeddogs_player in real_hits:
                        solved_seeddogs_score = ((real_hits[solved_seeddogs_player] * 1.5) + (real_homers[solved_seeddogs_player] * 4.0))                                 
                        seeddogs_score_earned += solved_seeddogs_score
                        seeddogs_score_max += best_seeddogs_score                        
                        seeddogers += 1
                        break

                chips_pitchers += 1
                solved_ks_leader = next(iter(sorted_solved_ks))                
                solved_chips_score = real_ks[solved_ks_leader]
                chips_score_earned += solved_chips_score * 0.2
                chips_score_max += best_chips_score * 0.2

                solved_meatballs_leader = next(iter(sorted_solved_meatballs))
                solved_meatballs_score = real_meatballs[solved_meatballs_leader]
                meatballs_score_earned += solved_meatballs_score
                meatballs_score_max += best_meatballs_score

                solved_chipsmeatballs_leader = next(iter(sorted_solved_chipsmeatballs))
                solved_chipsmeatballs_score = (real_ks[solved_chipsmeatballs_leader] * 0.2) + real_meatballs[solved_chipsmeatballs_leader]
                chipsmeatballs_score_earned += solved_chipsmeatballs_score
                chipsmeatballs_score_max += best_chipsmeatballs_score

                solved_burgers_leader = next(iter(sorted_solved_era))
                if len(real_sho) > 0:
                    burgers_score_max += best_burgers_score
                    chipsburgers_score_max += best_chipsburgers_score
                    if solved_burgers_leader in real_sho:
                        burgers_score_earned += 12.5
                        chipsburgers_score_earned += 12.5 + (real_ks[solved_burgers_leader] * 0.2)
                
                solved_hits.clear(), solved_homers.clear(), solved_seeddogs.clear(), solved_ks.clear(), solved_era.clear(), solved_meatballs.clear(), solved_chipsmeatballs.clear() 
                sorted_solved_hits.clear(), sorted_solved_homers.clear(), sorted_solved_seeddogs.clear(), sorted_solved_ks.clear(), sorted_solved_era.clear()
                sorted_solved_meatballs.clear(), sorted_solved_chipsmeatballs.clear()
                if crimes_list is not None:
                    solved_steals.clear(), solved_seedpickles.clear(), solved_dogpickles.clear(), solved_trifecta.clear(), sorted_solved_steals.clear() 
                    sorted_solved_seedpickles.clear(), sorted_solved_dogpickles.clear(), sorted_solved_trifecta.clear()
            if not is_cached:
                GAME_CACHE[(season, day)] = good_game_list
        if season not in HAS_GAMES:
            HAS_GAMES[season] = False
        season_end = datetime.datetime.now()
        
    if not reject_solution:
        fail_rate = fail_counter / game_counter       
    else:
        fail_rate = 1.0   
    if len(win_loss) == 0:
        TOTAL_GAME_COUNTER = game_counter if (game_counter > TOTAL_GAME_COUNTER) else TOTAL_GAME_COUNTER         
            
    fail_points, linear_points = 10000000000.0, 10000000000.0    
    max_fail_rate, expected_average = 0.0, 0.25
    longest_modname = 0
    #new_worstmod_linear_error = max(worstmod_linear_error, unmod_linear_error)    
    new_worstmod_linear_error, unmod_linear_error, linear_error = 0.0, 0.0, 0.0     
    max_mod_unmod, max_error_game, new_plusname = "", "", ""
    new_worstmod = WORST_MOD
    best_plusname = PLUS_NAME
    max_mod_rates, mod_vals, mod_win_loss, mod_gameids, errors, mod_pos_vals, sorted_win_loss = [], [], [], [], [], [], []
    other_errors, linear_by_mod = {}, {}
    linear_fail = 9000000000000000.0    
    season_fail = 100000000.0
    calculate_solution = True
    batman_score, correction_adjustment = 1.0, 1.0
    if solve_batman_too:
        pickles_penalty, seedpickles_penalty, dogpickles_penalty, trifecta_penalty = 0.0, 0.0, 0.0, 0.0                
        seeds_score = seeds_score_earned / seeds_score_max
        dogs_score = dogs_score_earned / dogs_score_max
        seeddogs_score = seeddogs_score_earned / seeddogs_score_max
        chips_score = chips_score_earned / chips_score_max
        meatballs_score = meatballs_score_earned / meatballs_score_max
        chipsmeatballs_score = chipsmeatballs_score_earned / chipsmeatballs_score_max
        burgers_score, chipsburgers_score = 0.0, 0.0
        if burgers_score_max > 0.0:
            burgers_score = burgers_score_earned / burgers_score_max         
            chipsburgers_score = chipsburgers_score_earned / chipsburgers_score_max         
        if crimes_list is not None:
            pickles_score = pickles_score_earned / pickles_score_max
            seedpickles_score = seedpickles_score_earned / seedpickles_score_max
            dogpickles_score = dogpickles_score_earned / dogpickles_score_max
            trifecta_score = trifecta_score_earned / trifecta_score_max
            sum_max_earnings = max(seeds_score_max, dogs_score_max, seeddogs_score_max, pickles_score_max, seedpickles_score_max, dogpickles_score_max, trifecta_score_max, chips_score_max, meatballs_score_max, chipsmeatballs_score_max, burgers_score_max, chipsburgers_score_max)
            single_bats_earnings = max(seeds_score_max, dogs_score_max, pickles_score_max)
            pickles_penalty = (((1.0 - pickles_score) * 100.0) ** 6.0) * thieves * 100.0 * (single_bats_earnings / sum_max_earnings)
            seedpickles_penalty = (((1.0 - seedpickles_score) * 100.0) ** 6.0) * thieves * 100.0 * (seedpickles_score_max / sum_max_earnings)
            dogpickles_penalty = (((1.0 - dogpickles_score) * 100.0) ** 6.0) * thieves * 100.0 * (dogpickles_score_max / sum_max_earnings)
            trifecta_penalty = (((1.0 - trifecta_score) * 100.0) ** 6.0) * thieves * 100.0 * (trifecta_score_max / sum_max_earnings)
        else:
            sum_max_earnings = max(seeds_score_max, dogs_score_max, seeddogs_score_max, chips_score_max, meatballs_score_max, chipsmeatballs_score_max, burgers_score_max, chipsburgers_score_max)        
            single_bats_earnings = max(seeds_score_max, dogs_score_max)
        #print("Pitcher earnings (% of max possible) - Chips {:.2f}%, Burgers {:.2f}%, Meatballs {:.2f}%, Chips+Burgers {:.2f}%, Chips+Meatballs {:.2f}%".format(chips_score * 100.0, burgers_score * 100.0, meatballs_score * 100.0, chipsburgers_score * 100.0, chipsmeatballs_score * 100.0))
        #each of these scores is how close to maximum value we achieved, so 4.0 - these is a multiplier that punishes our solution the farther it is from optimum earnings, minimum 1.0        
        #batman_score = (((2.0 - seeds_score) ** 4.0) + ((2.0 - dogs_score) ** 4.0) + ((2.0 - seeddogs_score) ** 4.0)) / 3.0
        #correction_adjustment = (((1.0 + seeds_score) ** 4.0) + ((1.0 + dogs_score) ** 4.0) + ((1.0 + seeddogs_score) ** 4.0)) / 48.0
        if CURRENT_ITERATION == 1:
            print("Max BATMAN earnings = seeds {:.0f}, dogs {:.0f}, seeds+dogs {:.0f}".format(seeds_score_max, dogs_score_max, seeddogs_score_max))
            if crimes_list is not None:
                print("Max ENOCH earnings = pickles {:.0f}, seeds+pickes {:.0f}, dogs+pickles {:.0f}, trifecta {:.0f}".format(pickles_score_max, seedpickles_score_max, dogpickles_score_max, trifecta_score_max))
            print("Max pitching earnings = chips {:.0f}, burgers {:.0f}, meatballs {:.0f}, chips+burgers {:.0f}, chips+meatballs {:.0f}".format(chips_score_max, burgers_score_max, meatballs_score_max, chipsburgers_score_max, chipsmeatballs_score_max))
            print("{} Shutout pitchers, {} pitchers, {} batters".format(sho_pitchers, chips_pitchers, hitters))        
        seeds_penalty = (((1.0 - seeds_score) * 100.0) ** 6.0) * hitters * 100.0 * (single_bats_earnings / sum_max_earnings)
        dogs_penalty = (((1.0 - dogs_score) * 100.0) ** 6.0) * sluggers * 100.0 * (single_bats_earnings / sum_max_earnings)
        seeddogs_penalty = (((1.0 - seeddogs_score) * 100.0) ** 6.0) * seeddogers * 100.0 * (seeddogs_score_max / sum_max_earnings)
        #chips is the sole indicator of if we're hitting strikeouts leaders correctly, which should inform the correct solution... therefore, should be weighted as equally-important to the final solution as the highest-snack earner
        chips_penalty = (((1.0 - chips_score) * 100.0) ** 6.0) * chips_pitchers * 100.0
        #shutouts are more-diffuclt to predict, but earn a lot... we don't want to be forcing solutions to give us a bunch of shutouts first, so we need to penalize these less as they are just harder to predict period
        burgers_penalty = (((1.0 - burgers_score) * 100.0) ** 4.0) * sho_pitchers * 100.0 * (burgers_score_max / sum_max_earnings)
        chipsburgers_penalty = (((1.0 - chipsburgers_score) * 100.0) ** 4.0) * sho_pitchers * 100.0 * (chipsburgers_score_max / sum_max_earnings)
        meatballs_penalty = (((1.0 - meatballs_score) * 100.0) ** 6.0) * chips_pitchers * 100.0 * (meatballs_score_max / sum_max_earnings)
        chipsmeatballs_penalty = (((1.0 - chipsmeatballs_score) * 100.0) ** 6.0) * chips_pitchers * 100.0 * (chipsmeatballs_score_max / sum_max_earnings)
        batman_error = seeds_penalty + dogs_penalty + seeddogs_penalty + chips_penalty + burgers_penalty + chipsburgers_penalty + meatballs_penalty + chipsmeatballs_penalty + pickles_penalty + seedpickles_penalty + dogpickles_penalty + trifecta_penalty
        #print("Batman error = {:.0f}".format(batman_error))        
        linear_error += batman_error   
        
    if (game_counter < ALL_GAMES) and (CURRENT_ITERATION > 1) and not reject_solution:
        print("Somehow ended up with fewer games. Games = {}, all games = {}".format(game_counter, ALL_GAMES))
        reject_solution = True
    if not reject_solution:
        if len(win_loss) > 0:        
            #Remember to negate ev is when we can pass it through and make better results when EV is bigger
            expected_val, mismatches, dadbets, web_ev, current_mofo_ev, current_web_ev = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            if solve_for_ev:                
                for thisgame in ev_set:
                    game_expected_val, game_mismatches, game_dadbets, game_web_ev, game_season_ev, game_season_web_ev = game_ev_calculate(ev_set, solve_for_ev)                    
                    expected_val += game_expected_val
                    mismatches += game_mismatches
                    dadbets += game_dadbets
                    web_ev += game_web_ev
                    current_mofo_ev += game_season_ev
                    current_web_ev += game_season_web_ev
                    debug_print("Net EV = {:.4f}, web = {:.4f}, mismatches = {:.4f}, dadbets = {:.4f}".format(expected_val, web_ev, mismatches, dadbets), debug2, "::::::::  ")  
                sorted_win_loss = [x for _,x in sorted(zip(all_vals, win_loss))]
                sorted_gameids = [x for _,x in sorted(zip(all_vals, gameids))]
                all_vals.sort()
                linear_error, max_linear_error, min_linear_error, max_error_value, min_error_value, errors, max_error_game, other_errors = calc_linear_unex_error(all_vals, sorted_win_loss, sorted_gameids, ERROR_THRESHOLD)  
            else:                
                for val in all_vals:
                    if val >= 0.5:
                        pos_vals.append(val)
                expected_average = sum(pos_vals) / len(pos_vals)                
                sorted_vals_by_mod = sorted(vals_by_mod, key=lambda k: len(vals_by_mod[k]))
                modcount = len(DIRECT_MOD_SOLVES)
                for modname in sorted_vals_by_mod:   
                    longest_modname = len(modname) if (len(modname) > longest_modname) else longest_modname
                    if modname == "unmod":
                        unmod_rate = (unmod_fails / unmod_games) * 100.0
                    else:
                        mod_rates[modname] = (mod_fails[modname] / mod_games[modname]) * 100.0
                    if (len(mod_vals) >= 150):                        
                        mod_vals.clear()
                        mod_win_loss.clear()
                        mod_gameids.clear()                                        
                        new_plusname = ""
                    for thisgame in vals_by_mod[modname]:
                        mod_vals.append(vals_by_mod[modname][thisgame]["mofo_away"])
                        mod_vals.append(vals_by_mod[modname][thisgame]["mofo_home"])                        
                        mod_win_loss.append(vals_by_mod[modname][thisgame]["away_win"])
                        mod_win_loss.append(vals_by_mod[modname][thisgame]["home_win"])
                        mod_gameids.append(thisgame)
                        mod_gameids.append(thisgame)       
                        if thisgame not in overall_gameids:
                            overall_vals.append(vals_by_mod[modname][thisgame]["mofo_away"])
                            overall_vals.append(vals_by_mod[modname][thisgame]["mofo_home"])
                            overall_win_loss.append(vals_by_mod[modname][thisgame]["away_win"])
                            overall_win_loss.append(vals_by_mod[modname][thisgame]["home_win"])
                            overall_gameids.append(thisgame)
                            overall_gameids.append(thisgame)
                    if len(mod_vals) < 150:                        
                        new_plusname = modname
                        linear_by_mod[modname] = 0.0
                        continue
                    sorted_win_loss.clear()
                    for _,x in sorted(zip(mod_vals, mod_win_loss)):
                        sorted_win_loss.append(x)
                    #sorted_win_loss = [x for _,x in sorted(zip(mod_vals, mod_win_loss))]                    
                    mod_vals.sort()                        
                    mod_linear_error, mod_max_linear_error, mod_min_linear_error, mod_max_error_value, mod_min_error_value = calc_linear_unex_error(mod_vals, sorted_win_loss, modname)                    
                    mod_pos_vals.clear()                    
                    for val in mod_vals:
                        if val >= 0.5:
                            mod_pos_vals.append(val)                    
                    if modname == "unmod":
                        unmod_linear_error = mod_linear_error                        
                        mod_rate = unmod_rate
                    elif not new_plusname == "":
                        mod_rate = (mod_rates[modname] + mod_rates[new_plusname]) / 2.0                        
                    else:
                        mod_rate = mod_rates[modname]
                    mod_expected_average = 100.0 - ((sum(mod_pos_vals) / len(mod_pos_vals)) * 100.0)
                    EXPECTED_MOD_RATES[modname] = mod_expected_average
                    if not new_plusname == "":
                        EXPECTED_MOD_RATES[new_plusname] = mod_expected_average                    
                    linear_error_reduction = (1.0 - (abs(mod_rate - mod_expected_average) / 100.0)) * (100.0 - mod_expected_average)    
                    #include batman modifier before subtraction, to make sure large batman errors don't inflate a large negative number
                    mod_linear_error = (mod_linear_error * batman_score) - ((linear_error_reduction ** 2.0) * correction_adjustment)
                    mod_linear_error *= modcount if modname not in DIRECT_MOD_SOLVES else 1.0
                    mod_linear_error *= 0.1
                    linear_by_mod[modname] = mod_linear_error
                    linear_error += mod_linear_error
                    if mod_linear_error > new_worstmod_linear_error:                        
                        new_worstmod_linear_error = mod_linear_error
                        new_worstmod = modname
                        if not new_plusname == "":
                            best_plusname = new_plusname
                        else:
                            best_plusname = ""                    
                    if mod_max_linear_error > max_linear_error:
                        max_linear_error = mod_max_linear_error
                        max_error_value = mod_max_error_value
                        max_error_mod = modname
                    if mod_min_linear_error < min_linear_error:
                        min_linear_error = mod_min_linear_error                    
                        min_error_value = mod_min_error_value
                        min_error_mod = modname
                    if modname not in DIRECT_MOD_SOLVES:
                        if mod_max_linear_error > unmod_max_linear_error:
                            unmod_max_linear_error = mod_max_linear_error
                            unmod_max_error_value = mod_max_error_value
                            unmod_max_error_mod = modname
                        if mod_min_linear_error < unmod_min_linear_error:
                            unmod_min_linear_error = mod_min_linear_error
                            unmod_min_error_value = mod_min_error_value
                            unmod_min_error_mod = modname
                sorted_win_loss.clear()
                for _,x in sorted(zip(overall_vals, overall_win_loss)):
                    sorted_win_loss.append(x)
                #sorted_win_loss = [x for _,x in sorted(zip(overall_vals, overall_win_loss))]                
                overall_vals.sort()                    
                overall_linear_error, overall_max_linear_error, overall_min_linear_error, overall_max_error_value, overall_min_error_value = calc_linear_unex_error(overall_vals, sorted_win_loss, "overall")                  
                overall_linear_error += (overall_linear_error * modcount * batman_score) - (((expected_average * 100.0) ** 2.0) * correction_adjustment)
                overall_linear_error *= 0.1
                linear_error += overall_linear_error
                linear_by_mod["overall"] = overall_linear_error
                if overall_linear_error > new_worstmod_linear_error:  
                    new_worstmod_linear_error = overall_linear_error
                    new_worstmod = "overall"                   
                    best_plusname = ""                                   
                
            major_errors = 0.0                       
            linear_points = linear_error
            if not mod_mode:
                fail_points = ((fail_rate * 1000.0) ** 2) * 2.5        
                linear_fail = fail_points + linear_points
            else:   
                for name in mod_games:
                    if mod_games[name] > 0:
                        if solve_for_ev:
                            mod_rates[name] = ((mod_fails[name] - mod_web_fails[name]) / mod_games[name]) * 100.0
                        if abs(mod_rates[name] - 25.0) > max_fail_rate:
                            max_fail_rate = mod_rates[name]
                            max_mod_unmod = name
                        #if name not in EXPECTED_MOD_RATES:
                        #    EXPECTED_MOD_RATES[name] = 10000000.0  
                        #if "error" not in BEST_MOD_RATES:
                        #    BEST_MOD_RATES["error"] = 10000000.0
                        if name not in ALL_MOD_GAMES:
                            ALL_MOD_GAMES[name] = mod_games[name]
                        #max_mod_rates = EXPECTED_MOD_RATES.values()
                        #if not solve_for_ev:
                        #    if mod_rates[name] > max(BEST_UNMOD, max(max_mod_rates)):
                        #        print("Failed for mod rate reasons; shouldn't be seeing this if everything is working properly")
                        #        calculate_solution = False
                if unmod_games > 0:
                    ALL_UNMOD_GAMES = unmod_games
                    if solve_for_ev:
                        unmod_rate = ((unmod_fails - unmod_web_fails) / unmod_games) * 100.0
                    else:
                        unmod_rate = (unmod_fails / unmod_games) * 100.0                    
                    if unmod_rate > max_fail_rate:
                        max_fail_rate = unmod_rate
                        max_mod_unmod = "unmod"                    
                    #if not solve_for_ev:
                    #    if unmod_rate > max(BEST_UNMOD, max(max_mod_rates)):
                    #        print("Failed for unmod rate reasons; shouldn't be seeing this if everything is working properly")
                    #        calculate_solution = False                        
                all_rates = []
                if calculate_solution or solve_for_ev:                                                               
                    mod_error, aggregate_fail_rate = 0.0, 0.25
                    for name in mod_rates:
                        all_rates.append(mod_rates[name] / 100.0)                        
                    all_rates.append(unmod_rate / 100.0)
                    #all_rates.append(fail_rate)                    
                    for rate in all_rates:
                        if abs(rate - 0.25) > abs(aggregate_fail_rate - 0.25):
                            aggregate_fail_rate = rate
                        mod_error += abs(rate - 0.25)
                    #if game_counter > 800:
                    #    aggregate_fail_rate = max(all_rates)         
                    #else: 
                    #    aggregate_fail_rate = fail_rate
                    fail_points = ((aggregate_fail_rate * 1000.0) ** 2.0)
                    if not solve_for_ev:
                        #if fail_rate <= BEST_FAIL_RATE:
                        #linear_fail = linear_points + (unmod_rate * 100.0)
                        #now that we're capturing linearity for each submod, should be able to just use linear points
                        linear_fail = linear_points                        
                        debug_print("Aggregate fail rate = {:.4f}, fail points = {}, linear points = {}, total = {}, Best = {}".format(aggregate_fail_rate, int(fail_points), int(linear_points), int(linear_fail), int(BEST_RESULT)), debug2, ":::")                        
                        #else:
                        #    linear_fail = linear_points * fail_rate
                        #    debug_print("Did not meet linearity requirement to calculate. Aggregate fail rate = {:.4f}, fail points = {}, linear points = {}".format(aggregate_fail_rate, int(fail_points), int(linear_points)), debug2, ":::")                                                    
                if solve_for_ev:                    
                    linear_points *= 0.000000001
                    season_fail = current_web_ev - current_mofo_ev                      
                    if MAX_DAY < 25:
                        season_fail_per_day = (season_fail / MAX_DAY)
                        previous_fail_per_day = (web_ev - expected_val) / (50 - MAX_DAY)
                        #weight seasonal fail as if IT had the majority of days
                        linear_fail = (previous_fail_per_day * MAX_DAY) + (season_fail_per_day * (50 - MAX_DAY))
                    else:
                        linear_fail = web_ev - expected_val
                    max_span, min_span, team_span = -1000.0, 1000.0, 0.0
                    for team in ev_by_team:
                        net_ev = (ev_by_team[team]["mofo_ev"] - ev_by_team[team]["web_ev"])
                        max_span = net_ev if (net_ev > max_span) else max_span
                        min_span = net_ev if (net_ev < min_span) else min_span
                        if net_ev < 0:
                            team_span += net_ev                                       
                    if not (team_span < 0):
                        team_span = -1 * min_span                        
                    linear_fail = linear_fail + (team_span * min_span)
                #else:
                #    for newgame in games_by_mod[max_mod_unmod]:                                      
                #        line_jumpers[newgame] = games_by_mod[max_mod_unmod][newgame]
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
    elif not solve_for_ev:        
        #failed due to a unmod linearity
        #print("Solution rejected: best unmod linear error = {:.2f}, current = {:.2f}".format(LAST_BEST, unmod_linear_error))        
        if worstmod_linear_error >= LAST_BEST:
            fail_adds = worstmod_linear_error - LAST_BEST
        elif unmod_linear_error >= LAST_UNMOD:
            fail_adds = unmod_linear_error - LAST_UNMOD
        linear_fail = BEST_RESULT + fail_adds           
    if (linear_fail < BEST_RESULT):
        BEST_RESULT = linear_fail    
        BEST_SEASON = season_fail
        ALL_GAMES = game_counter            
        LINE_JUMP_GAMES.clear()
        #if best_plusname != "":
        #    for newgame in games_by_mod[best_plusname]:
        #        if newgame not in LINE_JUMP_GAMES:
        #            if type(games_by_mod[best_plusname][newgame]) != dict:
        #                print("game is somehow not a dict; failed to push to line jump; game id {}, plus mod {}".format(newgame, best_plusname))
        #            else:
        #                LINE_JUMP_GAMES[newgame] = games_by_mod[best_plusname][newgame]        
        PLUS_NAME = best_plusname
        #for newgame in games_by_mod[new_worstmod]:
        #    if newgame not in LINE_JUMP_GAMES:
        #        if type(games_by_mod[new_worstmod][newgame]) != dict:
        #            print("game is somehow not a dict; failed to push to line jump; game id {}, worst mod {}".format(newgame, new_worstmod))
        #        else:
        #            LINE_JUMP_GAMES[newgame] = games_by_mod[new_worstmod][newgame]                 
        WORST_MOD = new_worstmod
        #if WORST_MOD != "unmod":
        #    for newgame in games_by_mod["unmod"]:
        #        if newgame not in LINE_JUMP_GAMES:
        #            if type(games_by_mod["unmod"][newgame]) != dict:
        #                print("game is somehow not a dict; failed to push to line jump; game id {}, unmod and not worstmod".format(newgame))
        #            else:
        #                LINE_JUMP_GAMES[newgame] = games_by_mod["unmod"][newgame]
        LAST_UNMOD = unmod_linear_error
        #WORST_ERROR_GAME.clear()           
        #WORST_ERROR_GAME[max_error_game] = {}
        #WORST_ERROR_GAME[max_error_game]["mofo"] = max_error_value
        #WORST_ERROR_GAME[max_error_game]["actual"] = max_error_value - max_linear_error                        
        ERROR_THRESHOLD = max_linear_error          
        if solve_for_ev:                                
            LAST_SPAN = (max_run_span * 1.05) if (max_run_span < 0) else (max_run_span * 0.95)                   
        if len(win_loss) > 0:
            BEST_FAIL_RATE = fail_rate
            BEST_AGG_FAIL_RATE = aggregate_fail_rate
            if solve_for_ev:
                BEST_FAILCOUNT = ev_neg_count
                LAST_BEST = BEST_FAILCOUNT
            else:                
                LAST_BEST = new_worstmod_linear_error
            PREVIOUS_LAST_BEST = LAST_BEST
            PASSED_GAMES = (abs(BEST_AGG_FAIL_RATE) / 2.0)
            BEST_LINEAR_ERROR = linear_points
            if mod_mode:                                             
                BEST_UNMOD = unmod_rate if (abs(unmod_rate - 25.0) < abs(BEST_UNMOD - 25.0)) else BEST_UNMOD                                
                #BEST_MOD_RATES["error"] = (max_linear_error - min_linear_error) if ((max_linear_error - min_linear_error) < BEST_MOD_RATES["error"]) else BEST_MOD_RATES["error"]
        debug_print("-"*20, debug, run_id)
        if len(win_loss) > 0:        
            terms_output = "name,a,b,c"
            for stat, stlatterm in terms.items():                
                terms_output += "\n{},{},{},{}".format(stat, stlatterm.a, stlatterm.b, stlatterm.c)                
            half_output = "name,event,a"            
            for stat in half_stlats:
                for event in half_stlats[stat]:
                    half_output += "\n{},{},{}".format(stat, event, half_stlats[stat][event])            
            mods_output = "identifier,team,name,a"
            for attr in mods:                                
                for team in mods[attr]:
                    for stat in mods[attr][team]:
                        mods_output += "\n{},{},{},{}".format(attr, team, stat, mods[attr][team][stat])            
            ballpark_mods_output = "ballparkstlat,playerstlat,a,b,c"
            for bpstat in ballpark_mods:                
                for playerstat in ballpark_mods[bpstat]:                    
                    bpterm = ballpark_mods[bpstat][playerstat]
                    if type(bpterm) == dict:
                        continue
                    ballpark_mods_output +="\n{},{},{},{},{}".format(bpstat, playerstat, bpterm.a, bpterm.b, bpterm.c)            
            if outputdir:
                if final_solution:                    
                    write_final(outputdir, "MOFOCoefficients.csv", terms_output)
                    write_final(outputdir, "MOFOHalfTerms.csv", half_output)
                    write_final(outputdir, "MOFOTeamModsCorrection.csv", mods_output)
                    write_final(outputdir, "MOFOBallparkCoefficients.csv", ballpark_mods_output)
                    write_parameters(outputdir, run_id, "solution.json", parameters)
                else:
                    write_file(outputdir, run_id, "terms.csv", terms_output)
                    write_file(outputdir, run_id, "halfterms.csv", half_output)
                    write_file(outputdir, run_id, "mods.csv",  mods_output)
                    write_file(outputdir, run_id, "ballparkmods.csv", ballpark_mods_output)
                    write_parameters(outputdir, run_id, "solution.json", parameters)
            debug_print("Best so far - fail rate {:.4f}%\n".format(fail_rate * 100.0) + terms_output + "\n" + mods_output + "\n" + ballpark_mods_output, debug2, run_id)
            detailtext = "{} games".format(game_counter)
            detailtext += "\n{:.2f}% Unmodded,".format(unmod_rate) + (" " * (longest_modname - 8))
            detailtext += " {}{:.2f}% expected, {} games, error {:.0f}".format(("" if EXPECTED_MOD_RATES["unmod"] >= 10 else " "), EXPECTED_MOD_RATES["unmod"], unmod_games, linear_by_mod["unmod"])
            for name in mod_rates:
                detailtext += "\n{:.2f}% {},".format(mod_rates[name], name) + (" " * (longest_modname - len(name)))    
                detailtext += " {}{:.2f}% expected,  {} games, error {:.0f}".format(("" if EXPECTED_MOD_RATES[name] >= 10 else " "), EXPECTED_MOD_RATES[name], mod_games[name], linear_by_mod[name])   
            if multi_mod_games > 0:
                if solve_for_ev:
                    detailtext += "\n{:.2f}% multimod fail rate, {} games".format(((multi_mod_fails - multi_mod_web_fails) / multi_mod_games) * 100.0, multi_mod_games)
                else:
                    detailtext += "\n{:.2f}% multimod fail rate, {} games".format((multi_mod_fails / multi_mod_games) * 100.0, multi_mod_games)
            if mvm_games > 0:
                if solve_for_ev:
                    detailtext += "\n{:.2f}% mod vs mod fail rate, {} games".format(((mvm_fails - mvm_web_fails) / mvm_games) * 100.0, mvm_games)            
                else:
                    detailtext += "\n{:.2f}% mod vs mod fail rate, {} games".format((mvm_fails / mvm_games) * 100.0, mvm_games)            
            detailtext += "\nBest so far - Linear fail {:.0f}, worst mod = {}, {:.0f}, fail rate {:.2f}%".format(linear_fail, WORST_MOD, LAST_BEST, fail_rate * 100.0)
            if solve_for_ev:
                detailtext += "\nNet EV = {:.4f}, web EV = {:.4f}, season EV = {:.4f}, mismatches = {:.4f}, dadbets = {:.4f}".format(expected_val, web_ev, (-1 * BEST_SEASON), mismatches, dadbets)                        
            detailtext += "\nMax linear error {:.2f}% ({:.2f} actual, {:.2f} calculated) - {}".format(max_linear_error, (max_error_value - max_linear_error), max_error_value, max_error_mod)            
            detailtext += "\nMin linear error {:.2f}% ({:.2f} actual, {:.2f} calculated) - {}".format(min_linear_error, (min_error_value - min_linear_error), min_error_value, min_error_mod)              
            detailtext += "\nUnmod Max linear error {:.2f}% ({:.2f} actual, {:.2f} calculated) - {}".format(unmod_max_linear_error, (unmod_max_error_value - unmod_max_linear_error), unmod_max_error_value, unmod_max_error_mod)            
            detailtext += "\nUnmod Min linear error {:.2f}% ({:.2f} actual, {:.2f} calculated) - {}".format(unmod_min_linear_error, (unmod_min_error_value - unmod_min_linear_error), unmod_min_error_value, unmod_min_error_mod)              
            detailtext += "\nOverall linear error {:.0f}, max {:.2f}% ({:.2f} actual, {:.2f} calculated), min {:.2f}% ({:.2f} actual, {:.2f} calculated)".format(overall_linear_error, overall_max_linear_error, (overall_max_error_value - overall_max_linear_error), overall_max_error_value, overall_min_linear_error, (overall_min_error_value - overall_min_linear_error), overall_min_error_value)                        
            #if len(errors) > 0 and not solve_for_ev:
            #    errors_output = ", ".join(map(str, errors))
            #    detailtext += "\nMajor errors at: " + errors_output
            #elif not solve_for_ev:
            #    detailtext += "\nNo major errors"
            detailtext += "\nBATMAN error = {:.0f}, total = {:.0f}, fail rate {:.2f}%, expected {:.2f}%".format(batman_error, linear_fail, fail_rate * 100.0, (1.0 - expected_average) * 100.0)
            if solve_batman_too:
                thresholds = {}
                thresholds["seeds"], thresholds["dogs"], thresholds["seeddogs"], thresholds["pickles"], thresholds["seedpickles"], thresholds["dogpickles"], thresholds["trifecta"] = 0.4902, 0.1897, 0.4886, 0.3649, 0.3906, 0.3681, 0.4327
                detailtext += "\nBATMAN earnings (% of max possible) - Seeds {:.2f}%{}, Dogs {:.2f}%{}, Seeds+Dogs {:.2f}%{}".format(seeds_score * 100.0, ("!" if seeds_score > thresholds["seeds"] else ""), dogs_score * 100.0, ("!" if dogs_score > thresholds["dogs"] else ""), seeddogs_score * 100.0, ("!" if seeddogs_score > thresholds["seeddogs"] else ""))
                if crimes_list is not None:
                    detailtext += "\nENOCH earnings (% of max possible) - Pickles {:.2f}%{}, Seeds+Pickles {:.2f}%{}, Dogs+Pickles {:.2f}%{}, Trifecta {:.2f}%{}".format(pickles_score * 100.0, ("!" if pickles_score > thresholds["pickles"] else ""), seedpickles_score * 100.0, ("!" if seedpickles_score > thresholds["seedpickles"] else ""), dogpickles_score * 100.0, ("!" if dogpickles_score > thresholds["dogpickles"] else ""), trifecta_score * 100.0, ("!" if trifecta_score > thresholds["trifecta"] else ""))
                detailtext += "\nPitcher earnings (% of max possible) - Chips {:.2f}%, Burgers {:.2f}%, Meatballs {:.2f}%, Chips+Burgers {:.2f}%, Chips+Meatballs {:.2f}%".format(chips_score * 100.0, burgers_score * 100.0, meatballs_score * 100.0, chipsburgers_score * 100.0, chipsmeatballs_score * 100.0)                
            debug_print(detailtext, debug, run_id)
            if outputdir:
                write_file(outputdir, run_id, "details.txt", detailtext)
            if sys.platform == "darwin":  # MacOS
                os.system("""osascript -e 'display notification "Fail rate {:.4f}%" with title "New solution found!"'""".format(fail_rate * 100.0))                        
            debug_print("Iteration #{}".format(CURRENT_ITERATION), debug, run_id)
            if solve_for_ev and outputdir:
                reportbyteam = "EV report by Team\n"
                sorted_net_ev_by_team = {}
                lowest_ev = 100000.0
                while len(sorted_net_ev_by_team) < len(ev_by_team):
                    for team in ev_by_team:                    
                        if team not in sorted_net_ev_by_team:
                            if (ev_by_team[team]["mofo_ev"] - ev_by_team[team]["web_ev"]) < lowest_ev:
                                lowest_ev = (ev_by_team[team]["mofo_ev"] - ev_by_team[team]["web_ev"])
                    for team in ev_by_team:                    
                        if ((ev_by_team[team]["mofo_ev"] - ev_by_team[team]["web_ev"]) == lowest_ev) and (team not in sorted_net_ev_by_team):
                            sorted_net_ev_by_team[team] = {}
                            sorted_net_ev_by_team[team]["mofo_ev"] = ev_by_team[team]["mofo_ev"]
                            sorted_net_ev_by_team[team]["web_ev"] = ev_by_team[team]["web_ev"]
                            lowest_ev = 100000.0
                            break
                for team in sorted_net_ev_by_team:
                    reportbyteam += "Net = "
                    if (ev_by_team[team]["mofo_ev"] - ev_by_team[team]["web_ev"]) >= 0:
                        reportbyteam += " "
                    reportbyteam += "{:.4f} for {}: MOFO EV = {:.4f}, Web EV = {:.4f}\n".format((ev_by_team[team]["mofo_ev"] - ev_by_team[team]["web_ev"]), team, ev_by_team[team]["mofo_ev"], ev_by_team[team]["web_ev"])                
                write_file(os.path.join(outputdir, "TeamReports"), run_id, "team-report.txt", reportbyteam)
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
 
    if (CURRENT_ITERATION % 100 == 0 and CURRENT_ITERATION < 1000) or (CURRENT_ITERATION % 500 == 0):
        if len(win_loss) > 0:
            now = datetime.datetime.now()
            if solve_for_ev:
                debug_print("Best so far - {:.2f}, iteration # {}, fail rate {:.2f}, linear error {:.4f}, {} rejects since last check-in, {:.2f} seconds".format(BEST_RESULT, CURRENT_ITERATION, (BEST_FAIL_RATE * 100.0), BEST_LINEAR_ERROR, REJECTS, (now-LAST_ITERATION_TIME).total_seconds()), debug, now)
            else:  
                worstmod_report = WORST_MOD + (" " + PLUS_NAME if (PLUS_NAME != "") else "")
                debug_print("Best so far - {:.2f}, iteration # {}, fail rate {:.2f}, max linear fail {:.2f}, worst mod {}, {} rejects since last check-in, {:.2f} seconds".format(BEST_RESULT, CURRENT_ITERATION, (BEST_AGG_FAIL_RATE * 100.0), ERROR_THRESHOLD, worstmod_report, REJECTS, (now-LAST_ITERATION_TIME).total_seconds()), debug, now)                
            REJECTS = 0
            LAST_ITERATION_TIME = now
        else:
            debug_print("Best so far - {:.4f}, iteration # {}".format(BEST_RESULT, CURRENT_ITERATION), debug, datetime.datetime.now())
    CURRENT_ITERATION += 1           
    now = datetime.datetime.now()    
    if CURRENT_ITERATION % 25 == 0:
        time.sleep(10)
    #if (((now - LAST_CHECKTIME).total_seconds()) > 1800) and (workers > 1):    
    if (((now - LAST_CHECKTIME).total_seconds()) > 225):    
    #if CURRENT_ITERATION % 100 == 0:    
        #print("{} Taking our state-mandated 3 minute long rest per half hour of work".format(datetime.datetime.now()))
        sleeptime, sleepmins = 0.0, 0.0   
        time.sleep(45)        
        LAST_CHECKTIME = datetime.datetime.now()        
        #print("{} BACK TO WORK".format(datetime.datetime.now()))       
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
    global ALL_GAMES
    global ERROR_SPAN
    global WORST_ERROR
    global LAST_MAX
    global LAST_MIN
    global LAST_BEST
    global LAST_BESTS
    global MAX_INTEREST
    global POS_HITS
    global POS_HRS
    global BASELINE_ERROR
    global REJECTS
    global EXACT_FAILS
    global LAST_ITERATION_TIME
    global LINE_JUMP_GAMES
    global LAST_DAY_RANGE
    global LAST_SEASON_RANGE
    global LAST_FAIL_EVENT
    global FIRST_SOLUTION
    eventofinterest, batter_list, calc_func, stlat_list, special_case_list, mod_list, ballpark_list, stat_file_map, ballpark_file_map, game_list, team_attrs, games_swept, establish_baseline, debug, debug2, debug3, outputdir = data
    debug_print("func start: {}".format(starttime), debug3, run_id)             
    park_mod_list_size = len(ballpark_list) * 3
    team_mod_list_size = len(mod_list) * 3
    special_cases_count = len(special_case_list)       
    base_batman_list_size = len(parameters) - special_cases_count - park_mod_list_size - team_mod_list_size        
    mods = collections.defaultdict(lambda: {"opp": {}, "same": {}})
    ballpark_mods = collections.defaultdict(lambda: {"bpterm": {}})
    mod_mode = True            
    line_jumpers, inter_line_jumpers = {}, {}
    
    #special_cases = parameters[base_batman_list_size:-(team_mod_list_size + park_mod_list_size)] if special_case_list else []    
    if CURRENT_ITERATION == 1 and establish_baseline:   
        baseline = True
        if eventofinterest == "abs":
            baseline_parameters = ([0, 0, 1] * len(stlat_list)) + [0, 0, 0, 0, 0, 0, 0, 0] + ([0, 0, 1] * len(mod_list)) + ([0, 0, 1] * len(ballpark_list))            
        else:
            print("Establishing baseline for not-at-bats")
            baseline_parameters = ([0, 0, 1] * len(stlat_list)) + [0,] + ([0, 0, 1] * len(mod_list)) + ([0, 0, 1] * len(ballpark_list))
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
    bat_counter, pos_hit_counter, pos_hr_counter = 0, 0, 0
    batman_max_err, batman_min_err, batman_max_val, batman_min_val, pos_error, zero_error, pos_counter, zero_counter = {}, {}, {}, {}, {}, {}, {}, {}
    pass_exact, pass_within_one, pass_within_two, pass_within_three, pass_within_four = {}, {}, {}, {}, {}
    jump_errors = {}
    eventlist = ["abs", "hits", "hrs"]    
    if FIRST_SOLUTION:
        sum_error_span, sum_max_interest = 0.0, 0.0         
        for event in eventlist:
            sum_error_span += ERROR_SPAN[event]
            sum_max_interest += MAX_INTEREST[event]
        span_over_max = sum_error_span / sum_max_interest
        iterations = max(int((250.0 / (10.0 ** span_over_max))), 1)
    else:
        iterations = 1
    for event in eventlist:
        pos_error[event] = 0.0
        zero_error[event] = 0.0
        pos_counter[event] = 0
        zero_counter[event] = 0
        pass_exact[event] = 0 
        pass_within_one[event] = 0
        pass_within_two[event] = 0
        pass_within_three[event] = 0
        pass_within_four[event] = 0
        batman_max_err[event] = 0.0        
        batman_min_err[event] = 0.0        
        batman_max_val[event] = None
        batman_min_val[event] = None
    batman_unexvar = 0.0
    good_batter_perf_data, abs_batter_perf_data, good_bats_perf_data = [], [], []                                
    fail_rate, pos_fail_rate, zero_avg_error, pos_avg_error, over_unexvar, under_unexvar = 1.0, 1.0, 100.0, 100.0, 0.0, 0.0
    max_err_actual, min_err_actual = "", ""
    reject_solution, viability_unchecked, stats_regened = False, True, False
    max_atbats, max_hits, max_homers = 0, 0, 0
    atbats_team_stat_data, hits_team_stat_data, hrs_team_stat_data = {}, {}, {}
    stages = {}    
    stages["abs"] = [1.0, 0.75, 0.5, 0.25, 0.1]
    stages["hrs"] = [0.6, 0.45, 0.3, 0.15, 0.075]
    stages["hits"] = [1.0, 0.75, 0.5, 0.25, 0.1]    
    if CURRENT_ITERATION > 1:
        max_iter_interest = MAX_INTEREST        
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
        hits_team_stat_data.clear()
        hrs_team_stat_data.clear()
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
            if (batter_perf["batter_id"] not in atbats_team_stat_data):                                  
                flip_lineup = (battingteam == "San Francisco Lovers") and (season == 13) and (day > 27)                                                                        
                atbats_team_stat_data, hits_team_stat_data, hrs_team_stat_data = get_team_atbats(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, pitchername, pitchingteam, 
                                                                                                 battingteam, away_game["weather"], ballpark, ballpark_mods, team_stat_data, 
                                                                                                 pitcher_stat_data, int(batter_perf["num_innings"]), flip_lineup, terms, iterations, 
                                                                                                 {"factors": special_cases}, 3, baseline)                                                            
            bat_bat_counter, bat_atbat_failby, bat_hit_failby, bat_hr_failby, atbat_real_val, hit_real_val, hr_real_val = calc_func(batter_perf, season_team_attrs, atbats_team_stat_data, 
                                                                                                                                    hits_team_stat_data, hrs_team_stat_data, batter_perf["batter_id"], game)                                                                                                                 
            
            bat_counter += bat_bat_counter     
            pos_hit_counter += 1 if (hit_real_val > 0) else 0
            pos_hr_counter += 1 if (hr_real_val > 0) else 0

            if bat_bat_counter > 0:                                                       
                batman_max_err, batman_min_err, batman_max_val, batman_min_val = calc_maxes(batman_max_err, batman_min_err, batman_max_val, batman_min_val, bat_atbat_failby, bat_hit_failby, bat_hr_failby, atbat_real_val, hit_real_val, hr_real_val)                
                pos_error, zero_error, pos_counter, zero_counter = track_errors(bat_atbat_failby, bat_hit_failby, bat_hr_failby, atbat_real_val, hit_real_val, hr_real_val, pos_error, zero_error, pos_counter, zero_counter)                
           
            if bat_bat_counter > 0:            
                pass_within_four, pass_within_three, pass_within_two, pass_within_one, pass_exact = check_margins(eventlist, bat_atbat_failby, bat_hit_failby, bat_hr_failby, stages, pass_within_four, pass_within_three, pass_within_two, pass_within_one, pass_exact)                            
                
                batman_unexvar = calc_unexvar(bat_atbat_failby, bat_hit_failby, bat_hr_failby, hit_real_val, hr_real_val, batman_unexvar)

                reject_solution = check_rejects(batman_min_err, batman_max_err, eventlist, stages, batman_unexvar)            
                                
                if reject_solution:                                                                
                    REJECTS += 1                                                                            
                    break                 

                jump_errors["abs"] = bat_atbat_failby                            
                jump_errors["hits"] = bat_hit_failby            
                jump_errors["hrs"] = bat_hr_failby 
                
                for event in eventlist:
                    if jump_errors[event] >= (LAST_BESTS[event] / 2):
                        line_jumpers[game["away"]["game_id"]] = game
                        break
    
    seasonrange = reversed(range(14, 15))
    dayrange = range(63, 83)    

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
                    stats_regened = False
                elif should_regen(day_mods):
                    players = get_player_id_lookup(stat_filename)
                    team_stat_data, pitcher_stat_data = load_stat_data_pid(stat_filename, schedule, day, season_team_attrs)
                    stats_regened = True
                elif stats_regened:
                    players = get_player_id_lookup(stat_filename)
                    team_stat_data, pitcher_stat_data = load_stat_data_pid(stat_filename, schedule, day, season_team_attrs)
                    stats_regened = False
                STAT_CACHE[(season, day)] = (team_stat_data, pitcher_stat_data, players)
            if not players:
                raise Exception("No stat file found")
            cached_ballparks = BALLPARK_CACHE.get((season, day))
            if cached_ballparks is None:
                ballpark_filename = ballpark_file_map.get((season, day))
                if CURRENT_ITERATION > 1:
                    print("Ballparks not cached, season {}, day {}".format(season, day))
                if (CURRENT_ITERATION == 1) and not ballpark_filename:
                    for backday in reversed(range(1, day)):
                        ballpark_filename = ballpark_file_map.get((season, backday))
                        if ballpark_filename:
                            break
                    if not ballpark_filename:
                        ballpark_filename = ballpark_file_map.get((season-1, 73))
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
                    hits_team_stat_data.clear()
                    hrs_team_stat_data.clear()
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
                        away_game, home_game = game["away"], game["home"]
                        awayPitcher, awayTeam = players.get(away_game["pitcher_id"])
                        homePitcher, homeTeam = players.get(home_game["pitcher_id"])                                                
                        previous_batting_team = battingteam                                             
                        if CURRENT_ITERATION > 1:
                            if ((int(batter_perf["num_innings"]) < 8) or (int(batter_perf["at_bats"]) < 3)):
                                print("Illegal batter in cached data! {} innings and {} at bats".format(batter_perf["num_innings"], batter_perf["at_bats"]))                                                  
                        if (batter_perf["batter_id"] not in atbats_team_stat_data):                                  
                            flip_lineup = (battingteam == "San Francisco Lovers") and (season == 13) and (day > 27)                                                                        
                            atbats_team_stat_data, hits_team_stat_data, hrs_team_stat_data = get_team_atbats(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, pitchername, pitchingteam, 
                                                                                                                battingteam, away_game["weather"], ballpark, ballpark_mods, team_stat_data, 
                                                                                                                pitcher_stat_data, int(batter_perf["num_innings"]), flip_lineup, terms, iterations,  
                                                                                                                {"factors": special_cases}, 3, baseline)      
                        #print("Batter perf = {}".format(batter_perf))
                        bat_bat_counter, bat_atbat_failby, bat_hit_failby, bat_hr_failby, atbat_real_val, hit_real_val, hr_real_val = calc_func(batter_perf, season_team_attrs, atbats_team_stat_data, 
                                                                                                                                                hits_team_stat_data, hrs_team_stat_data, batter_perf["batter_id"], game)
                        minimum_atbats += int(batter_perf["at_bats"]) + bat_atbat_failby
                        previous_innings = max(int(batter_perf["num_innings"]), previous_innings)                            
                        if atbat_real_val == 1:
                            omit_from_good_abs = True
                            print("{} atbat {} season {}, day {}, opponent {}, batter {}".format(atbat_real_val, battingteam, season, day, pitchingteam, players[batter_perf["batter_id"]][0]))       
                            continue
                        if (CURRENT_ITERATION == 1) and (bat_atbat_failby > 0):                                
                            omit_from_good_abs = True                                      
                            print("Omitting {}, season {}, day {}, opponent {}, batter {}".format(battingteam, season, day, pitchingteam, players[batter_perf["batter_id"]][0]))                                    
                            continue
                        if not iscached_batters:                           
                            if ((int(batter_perf["num_innings"]) < 8) or (int(batter_perf["at_bats"]) < 3)):
                                print("omitting batter from hits or homers calculations due to having insufficient data")                                    
                                omit_from_good_abs = True
                                continue                            
                        if not iscached_batters and not omit_from_good_abs:
                            abs_batter_perf_data.extend([batter_perf])                                                    
                        if omit_from_good_abs:
                            print("Making sure we don't accumulate data from omitted sources")
                            continue
                        bat_counter += bat_bat_counter    
                        pos_hit_counter += 1 if (hit_real_val > 0) else 0
                        pos_hr_counter += 1 if (hr_real_val > 0) else 0
                                                                        
                        if bat_bat_counter > 0:                      
                            pass_within_four, pass_within_three, pass_within_two, pass_within_one, pass_exact = check_margins(eventlist, bat_atbat_failby, bat_hit_failby, bat_hr_failby, stages, pass_within_four, pass_within_three, pass_within_two, pass_within_one, pass_exact)                            
                            
                            batman_unexvar = calc_unexvar(bat_atbat_failby, bat_hit_failby, bat_hr_failby, hit_real_val, hr_real_val, batman_unexvar)

                            batman_max_err, batman_min_err, batman_max_val, batman_min_val = calc_maxes(batman_max_err, batman_min_err, batman_max_val, batman_min_val, bat_atbat_failby, bat_hit_failby, bat_hr_failby, atbat_real_val, hit_real_val, hr_real_val)                
                            pos_error, zero_error, pos_counter, zero_counter = track_errors(bat_atbat_failby, bat_hit_failby, bat_hr_failby, atbat_real_val, hit_real_val, hr_real_val, pos_error, zero_error, pos_counter, zero_counter)

                            if CURRENT_ITERATION > 1:                                            
                                reject_solution = check_rejects(batman_min_err, batman_max_err, eventlist, stages, None)
                                
                                if reject_solution:                                                                
                                    LINE_JUMP_GAMES[game["away"]["game_id"]] = game                                           
                                    REJECTS += 1                                                                            
                                    break                           

                                jump_errors["abs"] = bat_atbat_failby                            
                                jump_errors["hits"] = bat_hit_failby            
                                jump_errors["hrs"] = bat_hr_failby 
                
                                for event in eventlist:
                                    if (jump_errors[event] >= (LAST_MAX[event] - stages[event][3])) or (jump_errors[event] <= (LAST_MIN[event] + stages[event][3])):
                                        line_jumpers[game["away"]["game_id"]] = game
                                        break
                                    
                
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
                        BATTER_CACHE[(season, day, game["away"]["game_id"])] = good_batter_perf_data                                  

            if not is_cached:
                GAME_CACHE[(season, day)] = good_game_list            
        if season not in HAS_GAMES:
            HAS_GAMES[season] = False
        season_end = datetime.datetime.now()   

    zero_avg_error, pos_avg_error = {}, {}
    if not reject_solution:                
        for event in eventlist:
            if event == "abs":            
                zero_avg_error[event] = 0.0                  
            else:
                zero_avg_error[event] = zero_error[event] / zero_counter[event]              
            pos_avg_error[event] = pos_error[event] / pos_counter[event]        
    else:
        for event in eventlist:
            zero_avg_error[event] = 1.0
            pos_avg_error[event] = 1.0
    # need to sort win_loss to match up with what will be the sorted set of vals
    # also need to only do this when solving MOFO
    #use_zero_error = zero_avg_error if (zero_avg_error > 0 or pos_avg_error < 0.5) else (pos_avg_error * 2)    
    if reject_solution:        
        unexvar_plus = 0
        for event in eventlist:
            unexvar_plus += (max(batman_max_err[event], abs(batman_min_err[event])) ** 2) * (ALL_GAMES - bat_counter)            
            if not (event == "abs") and (CURRENT_ITERATION > 1):
                if abs(batman_min_err[event]) >= (MAX_INTEREST[event] - stages[event][4]):
                    if event == "hits":
                        unexvar_plus += 5000000.0 * (POS_HITS - pos_hit_counter)
                    if event == "hrs":
                        unexvar_plus += 15000000.0 * (POS_HRS - pos_hr_counter)
        linear_fail = (batman_unexvar + unexvar_plus) * 100.0
    elif not reject_solution:       
        linear_fail = batman_unexvar
    if not reject_solution:        
        worst_exact = 100.0
        for event in eventlist:            
            pass_exact[event] = (pass_exact[event] / bat_counter) * 100.0
            pass_within_one[event] = (pass_within_one[event] / bat_counter) * 100.0
            pass_within_two[event] = (pass_within_two[event] / bat_counter) * 100.0
            pass_within_three[event] = (pass_within_three[event] / bat_counter) * 100.0
            pass_within_four[event] = (pass_within_four[event] / bat_counter) * 100.0            
            worst_exact = pass_exact[event] if (pass_exact[event] < worst_exact) else worst_exact
        if CURRENT_ITERATION > 1:
            for event in eventlist:
                if abs(batman_min_err[event]) == MAX_INTEREST[event]:
                    worst_exact = 0.0
            linear_fail *= max((100.0 - worst_exact), 1.0)
        else:
            linear_fail *= 100.0
            
    if (linear_fail < BEST_RESULT) and not reject_solution:        
        BEST_RESULT = linear_fail
        BEST_EXACT = worst_exact        
        #ALL_GAMES = bat_counter if (bat_counter > ALL_GAMES) else ALL_GAMES        
        for event in eventlist:
            ERROR_SPAN[event] = batman_max_err[event] - batman_min_err[event]                                
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
        detailtext = "::: Pass Rates over {} batters :::\n".format(bat_counter)
        for event in eventlist:
            detailtext += "\nRates for {}".format(event)
            detailtext += "\nExact (+/- {:.2f}) = {:.4f}".format(stages[event][4], pass_exact[event])
            detailtext += "\n+/- {:.2f} = {:.4f}".format(stages[event][3], pass_within_one[event])
            detailtext += "\n+/- {:.2f} = {:.4f}".format(stages[event][2], pass_within_two[event])
            detailtext += "\n+/- {:.2f} = {:.4f}".format(stages[event][1], pass_within_three[event])
            detailtext += "\n+/- {:.2f} = {:.4f}".format(stages[event][0], pass_within_four[event])
            detailtext += "\nmax underestimate {:.4f}, max overestimate {:.4f}".format(batman_min_err[event], batman_max_err[event])            
            detailtext += "\nactual val underest {}".format(batman_min_val[event])
            detailtext += "\nactual val overest {}".format(batman_max_val[event])            
            detailtext += "\nzero average error {:.4f}, pos average error {:.4f}\n".format(zero_avg_error[event], pos_avg_error[event])            
        debug_print(detailtext, debug, run_id)
        if outputdir:
            write_file(outputdir, run_id, eventofinterest + "details.txt", detailtext)                
        debug_print("Optimizing: abs, hits, hrs, unexvar = {:.0f} iteration #{}".format(batman_unexvar, CURRENT_ITERATION), debug, run_id)               
        debug_print("-" * 20 + "\n", debug, run_id)      
        if CURRENT_ITERATION == 1:            
            total_batters = 0
            check_max_hits = 0
            check_max_homers = 0
            check_max_atbats = 0
            #validate batter cache data            
            seasonrange = reversed(range(14, 15))
            dayrange = range(63, 83)
            for season in seasonrange:
                for day in dayrange:
                    cache_games = GAME_CACHE.get((season, day))
                    #print("cached games = {}".format(cache_games))
                    paired_games = pair_games(cache_games)
                    for game in paired_games:
                        #print("game = {}".format(game))
                        performance_data = BATTER_CACHE.get((season, day, game["away"]["game_id"]))
                        #print("cached batters = {}".format(performance_data))
                        for thisbatter_perf in performance_data:           
                            #print("batter = {}".format(thisbatter_perf))
                            total_batters += 1
                            hits = int(thisbatter_perf["hits"])
                            homers = int(thisbatter_perf["home_runs"])
                            atbats = int(thisbatter_perf["at_bats"])
                            check_max_hits = hits if (hits > check_max_hits) else check_max_hits
                            check_max_homers = homers if (homers > check_max_homers) else check_max_homers
                            check_max_atbats = atbats if (atbats > check_max_atbats) else check_max_atbats
                            POS_HITS += 1 if (hits > 0) else 0
                            POS_HRS += 1 if (homers > 0) else 0
            print("Maximums in cached data: hits = {}, homers = {}, atbats = {}, batters = {}".format(check_max_hits, check_max_homers, check_max_atbats, total_batters))
            MAX_INTEREST["hits"] = check_max_hits                            
            MAX_INTEREST["hrs"] = check_max_homers        
            #atbats is different, since we'll never fail by the total, so instead we set the largest underestimate
            MAX_INTEREST["abs"] = abs(batman_min_err["abs"])
            ALL_GAMES = total_batters
            batman_unexvar *= (total_batters / bat_counter)                                    
        #WORST_ERROR = abs(batman_max_err) + abs(batman_min_err)                  
        check_for_pos = True        
        LAST_BEST = 0.0
        for event in eventlist:
            LAST_MIN[event] = batman_min_err[event]
            LAST_MAX[event] = batman_max_err[event] if (batman_max_err[event] <= MAX_INTEREST[event]) else (batman_max_err[event] - MAX_INTEREST[event])
            LAST_BESTS[event] = max(LAST_MAX[event], abs(LAST_MIN[event]), 1.0)
            LAST_BEST = LAST_BESTS[event] if (LAST_BESTS[event] > LAST_BEST) else LAST_BEST
            if LAST_MAX[event] == 0:
                check_for_pos = False
        LINE_JUMP_GAMES.clear()           
        if CURRENT_ITERATION > 1 and FIRST_SOLUTION:                                    
            LINE_JUMP_GAMES = line_jumpers         
        #make sure we've gotten a single solution where all overestimates are a positive number before we start rejecting aggressively.
        if not FIRST_SOLUTION:
            FIRST_SOLUTION = check_for_pos        
        BEST_UNEXVAR_ERROR = batman_unexvar                         
    if ((CURRENT_ITERATION % 100 == 0 and CURRENT_ITERATION < 10000) or (CURRENT_ITERATION % 500 == 0 and CURRENT_ITERATION < 250000) or (CURRENT_ITERATION % 5000 == 0 and CURRENT_ITERATION < 1000000) or (CURRENT_ITERATION % 50000 == 0)):
        now = datetime.datetime.now()  
        reporttext = ""
        total_span, report_max_interest = 0.0, 0.0
        for event in eventlist:
            total_span += ERROR_SPAN[event]
            if FIRST_SOLUTION:                                                         
                report_max_interest += MAX_INTEREST[event]
        if FIRST_SOLUTION:                                         
            report_over_max = total_span / report_max_interest
            report_iterations = min(max(int((500.0 / (10.0 ** report_over_max))), 1), 100)
            reporttext += "{:.4f} total span, future solves at {} iterations".format(total_span, report_iterations)
        else:
            reporttext += "{} total span, future solves at 1 iteration".format(total_span)
        debug_print("{}, iteration #{}, {} rejects since last check-in, {:.2f} seconds".format(reporttext, CURRENT_ITERATION, REJECTS, (now-LAST_ITERATION_TIME).total_seconds()), debug, now)
        REJECTS = 0
        LAST_ITERATION_TIME = now          
    if CURRENT_ITERATION < 100:
        now = datetime.datetime.now()   
        reporttext = ""
        total_span, report_max_interest = 0.0, 0.0
        for event in eventlist:
            total_span += ERROR_SPAN[event]
            if FIRST_SOLUTION:                                                         
                report_max_interest += MAX_INTEREST[event]
        if FIRST_SOLUTION:                                         
            report_over_max = total_span / report_max_interest
            report_iterations = min(max(int((250.0 / (10.0 ** report_over_max))), 1), 100)
            reporttext += "{:.4f} total span, future solves at {} iterations".format(total_span, report_iterations)
        else:
            reporttext += "{} total span, future solves at 1 iteration".format(total_span)
        debug_print("{}, iteration #{}, {} rejects since last check-in, {:.2f} seconds".format(reporttext, CURRENT_ITERATION, REJECTS, (now-LAST_ITERATION_TIME).total_seconds()), debug, now)
        REJECTS = 0
        LAST_ITERATION_TIME = now          
    CURRENT_ITERATION += 1   
    now = datetime.datetime.now()        
    if ((now - LAST_CHECKTIME).total_seconds()) > 10800:
        print("Taking our state-mandated two minute long rest per three hours of work")
        time.sleep(120)          
        LAST_CHECKTIME = datetime.datetime.now()        
        print("BACK TO WORK")
    debug_print("run fail rate {:.4f}%".format(fail_rate * 100.0), debug2, run_id)
    endtime = datetime.datetime.now()
    debug_print("func end: {}, run time {}".format(endtime, endtime-starttime), debug3, run_id)
    return linear_fail