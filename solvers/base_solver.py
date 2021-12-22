import collections
import csv
import sys
import time
import random
import datetime
import json
import pickle
import os
import re
import uuid
import math
import copy
from numba import njit
from numba.typed import List
import numpy as np
from glob import glob

from helpers import StlatTerm, ParkTerm, get_weather_idx
from helpers import load_stat_data, load_stat_data_pid, adjust_by_pct, calculate_adjusted_stat_data
from helpers import DEFENSE_STLATS, defense_stars, BATTING_STLATS, batting_stars, BASERUNNING_STLATS, baserunning_stars
from statistics import fmean, StatisticsError

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
MAX_EVENTS = {'hits': 8, 'homers': 4, 'steals': 10, 'seeddogs': 20.5, 'seedpickles': 36.0, 'dogpickles': 30.0, 'trifecta': 36.0, 'chips': 19, 'meatballs': 9, 'burgers': 12.5, 'chipsburgers': 16.3, 'chipsmeatballs': 9.6}
MASS_EVENTS = {'hits': 11, 'homers': 6, 'steals': 11, 'seeddogs': 26.5, 'seedpickles': 39.0, 'dogpickles': 38.0, 'trifecta': 51.5, 'chips': 28, 'meatballs': 13, 'chipsmeatballs': 14.0}
FACTORS = {'seeds': [(5830574836565810, 23488585391653400), (5840320966648320, 23843951898871800), (5867365910819690, 23478352355856100), (5875726754954620, 23257271570441200), (5887275009041410, 23623303302473700)], 'dogs': [(3676658406399890, 24346883945710400), (3679564589051610, 23957067508515900), (3719542502011940, 24254606789529400), (3725687079835050, 23121107410407000), (3728071289480220, 23241345775947300)], 'pickles': [(2935744361536850, 23798626074887400), (2937526145995710, 24145042947052900), (2938505633530020, 23852633168439800), (2938562061811530, 24062378271153000), (2944638154520360, 24170105359468000)], 'chips': [(3023815555939160, 23970835703185200), (3038428975346370, 22816467135385200), (3091133586829120, 24110827736918400), (3125868888744890, 24116919421779900), (3137437032080280, 23304051862095900)], 'meatballs': [(5551512075903060, 23286463514636600), (5599158011397710, 23724254656204400), (5634246801510820, 24210462288927100), (5460021306196550, 23792359281037600), (5565918178440090, 24442269826434000)], 'all': [22531386580342100, 22557419780824400, 22638975484864400, 22641685789292600, 22677488968449100]}
ADJUSTED_STAT_CACHE = {}
SORTED_BATTERS_CACHE = {}
CACHED_CALCED_STAT_DATA = {}
USE_CACHED_PARK_MODS = {}
IGNORE_BP_STATS = ['birds', 'model', 'renoCost', 'mysticism', 'filthiness', 'luxuriousness']

MIN_SEASON = 22
MAX_SEASON = 23

BEST_RESULT = 22687498004247900.0    
BEST_FAIL_RATE = 1.0
SOLUTIONS_TO_FILL = 0
MIN_DAY = 1
MAX_DAY = 99
BEST_FAILCOUNT = 10000000000.0
CURRENT_ITERATION = 1
LAST_CHECKTIME = datetime.datetime.now()
BEST_UNMOD = 1000000000000.0
WORST_MOD = ""
PLUS_NAME = ""
PREVIOUS_FOCUS = ""
LAST_BEST = 1000000000.0
CACHED_NONZERO_MEAN = {}
CACHED_SORTED_REAL = {}
EXPECTED_MOD_RATES = {}
HAS_GAMES = {}
FAILED_SOLUTIONS = []
LAST_ITERATION_TIME = datetime.datetime.now()

ALLOWED_IN_BASE = {"AFFINITY_FOR_CROWS", "GROWTH", "EXTRA_STRIKE", "LOVE", "O_NO", "BASE_INSTINCTS", "TRAVELING", "HIGH_PRESSURE", "0", "H20", "AAA", "AA", "A", "ACIDIC", "FIERY", "PSYCHIC", "ELECTRIC", "SINKING_SHIP"}
ALLOWED_IN_BASE = {"AFFINITY_FOR_CROWS", "GROWTH", "EXTRA_STRIKE", "LOVE", "O_NO", "BASE_INSTINCTS", "TRAVELING", "HIGH_PRESSURE", "0", "H20", "AAA", "AA", "ACIDIC", "FIERY", "PSYCHIC", "ELECTRIC", "SINKING_SHIP"}
ALLOWED_IN_BASE_BATMAN = {"AFFINITY_FOR_CROWS", "GROWTH", "EXTRA_STRIKE", "LOVE", "O_NO", "BASE_INSTINCTS", "TRAVELING", "HIGH_PRESSURE"}
FORCE_REGEN = {"AFFINITY_FOR_CROWS", "GROWTH", "TRAVELING", "SINKING_SHIP"}
DIRECT_MOD_SOLVES = {"psychic", "a", "acidic", "base_instincts", "electric", "fiery", "love"}
CALC_MOD_SUCCESS = {"psychic", "aa", "acidic", "aaa", "base_instincts", "electric", "fiery", "love", "high_pressure", "a", "0", "o_no", "h20"}
DIRECT_MOD_SOLVES = {"psychic", "acidic", "base_instincts", "electric", "fiery", "love"}
CALC_MOD_SUCCESS = {"psychic", "aa", "acidic", "aaa", "base_instincts", "electric", "fiery", "love", "high_pressure", "0", "o_no", "h20"}

BIRD_WEATHER = get_weather_idx("Birds")
FLOOD_WEATHER = get_weather_idx("Flooding")

def get_lists_from_loop(batter_order, team_stat_data, team, adjusted_stat_data, away_home):
    shelled, active_batters, average_aa_impact, average_aaa_impact, high_pressure_mod = List(), List(), List(), List(), List()    
    defense_data, batting_data, running_data, playerAttrs = List(), List(), List(), List()
    for playerid in batter_order:
        shelled.append(team_stat_data[team][playerid]["shelled"])        
        defense_data.append(List([team_stat_data[team][playerid]["omniscience"], team_stat_data[team][playerid]["watchfulness"], team_stat_data[team][playerid]["chasiness"], team_stat_data[team][playerid]["anticapitalism"], team_stat_data[team][playerid]["tenaciousness"]]))
        if not team_stat_data[team][playerid]["shelled"]:
            active_batters.append(playerid)
            average_aa_impact.append(0.0), average_aaa_impact.append(0.0), high_pressure_mod.append(0.0)                                 
            batting_data.append(List([team_stat_data[team][playerid]["patheticism"], team_stat_data[team][playerid]["tragicness"], team_stat_data[team][playerid]["thwackability"], team_stat_data[team][playerid]["divinity"], team_stat_data[team][playerid]["moxie"], team_stat_data[team][playerid]["musclitude"], team_stat_data[team][playerid]["martyrdom"]])) 
            running_data.append(List([team_stat_data[team][playerid]["laserlikeness"], team_stat_data[team][playerid]["baseThirst"], team_stat_data[team][playerid]["continuation"], team_stat_data[team][playerid]["groundFriction"], team_stat_data[team][playerid]["indulgence"]]))
            if len(team_stat_data[team][playerid]["attrs"]) > 0:
                playerAttrs.append(List(team_stat_data[team][playerid]["attrs"]))
            else:
                playerAttrs.append(List(["none", "none"]))    
    team_stat_data = List([defense_data, batting_data, running_data])    
    return shelled, active_batters, average_aa_impact, average_aaa_impact, high_pressure_mod, adjusted_stat_data[away_home], team_stat_data, playerAttrs

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
                if batter not in stolen_bases:
                    stolen_bases[batter] = 0
                if team_stat_data[criminal_team][batter]["name"] == criminal_name:
                    #print("Criminal {} found! Guilty of a successful base steal because of text {}".format(criminal_name, line))                    
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
        if (len(games) == 2) and (games[0]["pitcher_is_home"] != games[1]["pitcher_is_home"]) and (int(games[0]["innings_pitched"]) == 9 or int(games[0]["innings_pitched"]) == 8) and (int(games[1]["innings_pitched"]) == 9 or int(games[1]["innings_pitched"]) == 8):            
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

@njit(cache=True)
def get_factor_and_best(focused_values):
    best_all, best_focused, factor, max_value, min_all = 0.0, 0.0, 0.0, 0.0, 0.0
    for idx in range(0, len(focused_values)):
        (focused_result_int, all_result_int) = focused_values[idx]
        focused_result, all_result = float(focused_result_int), float(all_result_int)
        factor = (all_result / focused_result) if (all_result / focused_result) > factor else factor
        if all_result > best_all:
            best_all = float(all_result)
            best_focused = float(focused_result)
        if focused_result > max_value:
            max_value = float(focused_result)
            replacement_index = int(idx)
        if (min_all == 0.0) or (float(all_result) < min_all):
            min_all = float(all_result)
    return best_all, best_focused, max_value, replacement_index, min_all

def calc_linear_unex_error(vals, wins_losses, modname=None):    
    max_error_game = ""    
    exponent_check = modname == "psychic" or modname == "a" or modname == "acidic" or modname == "base_instincts" or modname == "electric" or modname == "fiery" or modname == "love" or modname == "overall"
    exponent = 4.0 if exponent_check else 6.0
    window_size, half_window = 100, 50        
    win_threshold = False    
    starting_size = (window_size - 1)
    wins = wins_losses[:starting_size]    
    numba_wins, numba_wins_losses, numba_vals = List(wins), List(wins_losses), List(vals)
    error, max_error, min_error, max_error_val, min_error_val = linear_unex_loop(numba_wins, window_size, half_window, numba_vals, numba_wins_losses, exponent)    
    del numba_wins, numba_wins_losses, numba_vals, wins
    return error, max_error, min_error, max_error_val, min_error_val

@njit(cache=True)
def linear_unex_loop(wins, window_size, half_window, vals, wins_losses, exponent):
    win_threshold = False
    error, max_error, min_error, max_error_val, min_error_val, current_val = 0.0, 0.0, 150.0, 0.0, 0.0, 0.0    
    for idx in range(window_size - 1, len(vals)):                 
        wins.append(wins_losses[idx])                        
        current_val = vals[idx - half_window] * 100.0
        total_wins = sum(wins)
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
        del wins[0]
    error += (max_error ** (exponent + 2)) + (abs(min_error ** (exponent + 2)))    
    return error, max_error, min_error, max_error_val, min_error_val

def calc_penalty(best_score, solved_score, max_score, exponent):
    #if solved_score < 0:
    #    print("Possible overflow error, best score = {}, solved score = {}, max score = {}, raising {:.4f} to the 8th".format(best_score, solved_score, max_score, ((best_score - solved_score) / max_score)))  
    penalty = (((best_score - solved_score) / max_score) * 100.0) ** exponent    
    return penalty

def calc_bonus(best_score, max_score):
    #return calc_penalty(best_score, 0.0, max_score, 6.0)    
    return 0.0

def calc_best_penalty(best_leader_score, solved_leader_score, solved_score, best_score, max_event, exponent):  
    #if solved_leader_score < 0 or best_leader_score < 0:
    #    print("Possible overflow error, best leader score = {}, solved leader score = {}, solved score = {}, best score = {}, max event = {}".format(best_leader_score, solved_leader_score, solved_score, best_score, max_event))    
    try:
        actual_leader_solved_score = (best_leader_score / solved_leader_score) * solved_score
    except (ValueError, FloatingPointError, ZeroDivisionError):
        #print("Correctly caught error in best penalty")
        solved_leader_score += 0.0001
        best_leader_score += 0.0001        
        actual_leader_solved_score = (best_leader_score / solved_leader_score) * solved_score
    return calc_penalty(best_score, actual_leader_solved_score, max_event, exponent)    

#different idea for potential use later - gather and evaluate all solved scores within a particular value that are less than or equal to the average of the solved score of a previous value and evaluate thier linear penalty accordingly

@njit(cache=True)
def calc_batman_linear_penalty(real_scores, real_values, sorted_real_values, mean_event, exponent):
    penalty = 0.0             
    for idx in range(0, len(real_scores)):                  
        scored_value, real_value = float(real_values[idx]), float(sorted_real_values[idx])
        if scored_value != real_value:
            penalty_value = max(scored_value, real_value)
            #relative_error = ((penalty_value / max_real) * 100.0) ** exponent
            relative_error = (((real_value - scored_value) / penalty_value) * 100.0) ** exponent
            penalty += relative_error * (penalty_value / mean_event)    
    return penalty

def sort_batman_linear_penalty(event, event_values, max_event):
    global CACHED_NONZERO_MEAN
    global CACHED_SORTED_REAL
    unsorted_real_values, unsorted_solved_values = list(event_values["real_values"]), list(event_values["solved_values"])    
    unsorted_values = zip(unsorted_solved_values, unsorted_real_values)    
    sorted_values = sorted(unsorted_values)        
    real_scores = List([element for element, _ in sorted_values])
    real_values = List([element for _, element in sorted_values])
    
    if event not in CACHED_SORTED_REAL:
        unsorted_real_values.sort()    
        nonzero_values = [val for val in unsorted_real_values if val > 0]
        sorted_real_values = List([element for element in unsorted_real_values])    
        nonzero_mean = min(float(sum(nonzero_values)) / float(len(nonzero_values)), 2.0)
        CACHED_NONZERO_MEAN[event] = nonzero_mean
        CACHED_SORTED_REAL[event] = sorted_real_values
    else:
        nonzero_mean, sorted_real_values = CACHED_NONZERO_MEAN[event], CACHED_SORTED_REAL[event]
    penalty = calc_batman_linear_penalty(real_scores, real_values, sorted_real_values, nonzero_mean, 6.0)
    del real_scores, real_values, unsorted_real_values, unsorted_solved_values, unsorted_values, sorted_values
    return penalty

def calc_snack(event, all_event_values, real_values, sorted_solved_values, score_earned, score_max, event_max, event_mass, perfect_score, score_method, *args):    
    best_keys, solved_keys = list(real_values.keys()), list(sorted_solved_values.keys())    
    best_leader, solved_leader = best_keys[0], solved_keys[0]
    best_score, solved_best_score = real_values[best_leader], real_values[solved_leader]
    score_earned += solved_best_score
    score_max += best_score    
    
    best_mass_score = real_values[best_keys[1]] + real_values[best_keys[2]]
    solved_mass_score = real_values[solved_keys[1]] + real_values[solved_keys[2]]
    best_mass_solved_score = sorted_solved_values[best_keys[1]] + sorted_solved_values[best_keys[2]]
    solved_mass_solved_score = sorted_solved_values[solved_keys[1]] + sorted_solved_values[solved_keys[2]]    
    
    if event in all_event_values:
        for key in best_keys:
            all_event_values[event]["real_values"].append(real_values[key])
            all_event_values[event]["solved_values"].append(sorted_solved_values[key])
    
    linear_penalty = 0.0
    
    scores = score_method(sorted_solved_values, solved_best_score, best_score, best_leader, solved_leader, event_max, event_mass, perfect_score, best_mass_score, best_mass_solved_score, solved_mass_score, solved_mass_solved_score, linear_penalty, *args)    

    del best_keys, solved_keys
                    
    return all_event_values, score_earned, score_max, *scores

def single_calc(sorted_solved_values, solved_best_score, best_score, best_leader, solved_leader, event_max, event_mass, perfect_score, best_mass_score, best_mass_solved_score, solved_mass_score, solved_mass_solved_score, linear_penalty, best_error):    
    if solved_best_score < best_score:
        best_error += calc_best_penalty(sorted_solved_values[best_leader], sorted_solved_values[solved_leader], solved_best_score, best_score, event_max, 6.0) * 100.0
    else:
        perfect_score += best_score
        best_error -= calc_bonus(best_score, event_max)         
    return perfect_score, best_error

def double_calc(sorted_solved_values, solved_best_score, best_score, best_leader, solved_leader, event_max, event_mass, perfect_score, best_mass_score, best_mass_solved_score, solved_mass_score, solved_mass_solved_score, linear_penalty, first_error, first_event, first_multiplier, second_error, second_event, second_multiplier):                         
    if solved_best_score < best_score:
        best_error = calc_best_penalty(sorted_solved_values[best_leader], sorted_solved_values[solved_leader], solved_best_score, best_score, event_max, 6.0) * 100.0 
    else:
        best_error = 0.0
        perfect_score += best_score
        bonus = calc_bonus(best_score, event_max)
        first_error -= bonus * ((first_event[best_leader] * first_multiplier) / best_score)
        second_error -= bonus * ((second_event[best_leader] * second_multiplier) / best_score)                 
    first_error += best_error * ((first_event[best_leader] * first_multiplier) / best_score)
    second_error += best_error * ((second_event[best_leader] * second_multiplier) / best_score)                                                
    return perfect_score, first_error, second_error

def triple_calc(sorted_solved_values, solved_best_score, best_score, best_leader, solved_leader, event_max, event_mass, perfect_score, best_mass_score, best_mass_solved_score, solved_mass_score, solved_mass_solved_score, linear_penalty, first_error, first_event, first_multiplier, second_error, second_event, second_multiplier, third_error, third_event, third_multiplier):                         
    if solved_best_score < best_score:
        best_error = calc_best_penalty(sorted_solved_values[best_leader], sorted_solved_values[solved_leader], solved_best_score, best_score, event_max, 6.0) * 100.0
    else:
        best_error = 0.0
        perfect_score += best_score
        bonus = calc_bonus(best_score, event_max)
        first_error -= bonus * ((first_event[best_leader] * first_multiplier) / best_score)
        second_error -= bonus * ((second_event[best_leader] * second_multiplier) / best_score)
        third_error -= bonus * ((third_event[best_leader] * third_multiplier) / best_score)    
    first_error += best_error * ((first_event[best_leader] * first_multiplier) / best_score)
    second_error += best_error * ((second_event[best_leader] * second_multiplier) / best_score)
    third_error += best_error * ((third_event[best_leader] * third_multiplier) / best_score)
    return perfect_score, first_error, second_error

def get_max_events(seasonrange, dayrange, stat_file_map, team_attrs, game_list, batter_list, crimes_list):
    maximum_events = {}
    maximum_events["hits"], maximum_events["homers"], maximum_events["steals"] = 0, 0, 0
    maximum_events["seeddogs"], maximum_events["seedpickles"], maximum_events["dogpickles"], maximum_events["trifecta"] = 0.0, 0.0, 0.0, 0.0
    maximum_events["chips"], maximum_events["meatballs"] = 0, 0
    maximum_events["burgers"], maximum_events["chipsburgers"], maximum_events["chipsmeatballs"] = 12.5, 0.0, 0.0    
    
    mass_event = {}
    mass_event["hits"], mass_event["homers"], mass_event["steals"] = 0, 0, 0
    mass_event["seeddogs"], mass_event["seedpickles"], mass_event["dogpickles"], mass_event["trifecta"] = 0.0, 0.0, 0.0, 0.0
    mass_event["chips"], mass_event["meatballs"], mass_event["chipsmeatballs"] = 0, 0, 0

    mass_event_list = "hits", "homers", "steals", "seeddogs", "seedpickles", "dogpickles", "trifecta", "chips", "meatballs", "chipsmeatballs"

    daily_performance = {}       
    
    for season in seasonrange:
        season_team_attrs = team_attrs.get(str(season), {})
        for day in dayrange:
            daily_performance[day] = {}
            daily_performance[day]["hits"], daily_performance[day]["homers"], daily_performance[day]["steals"] = [], [], []
            daily_performance[day]["seeddogs"], daily_performance[day]["seedpickles"], daily_performance[day]["dogpickles"], daily_performance[day]["trifecta"] = [], [], [], []
            daily_performance[day]["chips"], daily_performance[day]["meatballs"], daily_performance[day]["chipsmeatballs"] = [], [], []
            games = [row for row in game_list if row["season"] == str(season) and row["day"] == str(day)]
            paired_games = pair_games(games)            
            schedule = get_schedule_from_paired_games(paired_games, season, day)
            day_mods = get_attrs_from_paired_games(season_team_attrs, paired_games)
            stat_filename = stat_file_map.get((season, day))
            if stat_filename:
                last_stat_filename = stat_filename
                pitchers = get_pitcher_id_lookup(stat_filename)
                team_stat_data, pitcher_stat_data = load_stat_data_pid(stat_filename, schedule, day, team_attrs)
                stats_regened = False
            elif should_regen(day_mods):
                pitchers = get_pitcher_id_lookup(last_stat_filename)
                team_stat_data, pitcher_stat_data = load_stat_data_pid(last_stat_filename, schedule, day, team_attrs)
                stats_regened = True
            elif stats_regened:
                pitchers = get_pitcher_id_lookup(last_stat_filename)
                team_stat_data, pitcher_stat_data = load_stat_data_pid(last_stat_filename, schedule, day, team_attrs)
                stats_regened = False
            batter_perf_data = [row for row in batter_list if row["season"] == str(season) and row["day"] == str(day)]
            if crimes_list is not None:                
                daily_steals = pair_crimes_with_batter(crimes_list, team_stat_data, season, day)                
            pitcher_meatballs, pitcher_chipsmeatballs = {}, {}
            for batter in batter_perf_data:
                batter_hits = int(batter["hits"])
                maximum_events["hits"] = batter_hits if (batter_hits > maximum_events["hits"]) else maximum_events["hits"]
                daily_performance[day]["hits"].append(batter_hits)
                batter_homers = int(batter["home_runs"])
                maximum_events["homers"] = batter_homers if (batter_homers > maximum_events["homers"]) else maximum_events["homers"]
                daily_performance[day]["homers"].append(batter_homers)
                batter_steals = 0
                if batter["batter_id"] in daily_steals:
                    batter_steals = int(daily_steals[batter["batter_id"]])
                maximum_events["steals"] = batter_steals if (batter_steals > maximum_events["steals"]) else maximum_events["steals"]
                daily_performance[day]["steals"].append(batter_steals)
                batter_seeddogs = (batter_hits * 1.5) + (batter_homers * 4.0)
                batter_seedpickles = (batter_hits * 1.5) + (batter_steals * 3.0)
                batter_dogpickles = (batter_homers * 4.0) + (batter_steals * 3.0)
                batter_trifecta = (batter_hits * 1.5) + (batter_homers * 4.0) + (batter_steals * 3.0)
                daily_performance[day]["seeddogs"].append(batter_seeddogs)
                daily_performance[day]["seedpickles"].append(batter_seedpickles)
                daily_performance[day]["dogpickles"].append(batter_dogpickles)
                daily_performance[day]["trifecta"].append(batter_trifecta)
                maximum_events["seeddogs"] = batter_seeddogs if (batter_seeddogs > maximum_events["seeddogs"]) else maximum_events["seeddogs"]
                maximum_events["seedpickles"] = batter_seedpickles if (batter_seedpickles > maximum_events["seedpickles"]) else maximum_events["seedpickles"]
                maximum_events["dogpickles"] = batter_dogpickles if (batter_dogpickles > maximum_events["dogpickles"]) else maximum_events["dogpickles"]
                maximum_events["trifecta"] = batter_trifecta if (batter_trifecta > maximum_events["trifecta"]) else maximum_events["trifecta"]                
                if batter["pitcher_id"] not in pitcher_meatballs:
                    pitcher_meatballs[batter["pitcher_id"]] = 0
                    pitcher_chipsmeatballs[batter["pitcher_id"]] = 0
                pitcher_meatballs[batter["pitcher_id"]] += int(batter["home_runs"])
                pitcher_chipsmeatballs[batter["pitcher_id"]] += int(batter["home_runs"])            
            for game in games:                
                pitcher_ks = int(game["strikeouts"])
                pitcher_chipsburgers = 0.0
                if float(game["opposing_team_abs_rbi"]) == 0.0:                    
                    pitcher_chipsburgers = 12.5 + (pitcher_ks * 0.2)
                if game["pitcher_id"] not in pitcher_chipsmeatballs:
                    pitcher_chipsmeatballs[game["pitcher_id"]] = 0
                if game["pitcher_id"] not in pitcher_meatballs:
                    pitcher_meatballs[game["pitcher_id"]] = 0
                    pitcher_chipsmeatballs[game["pitcher_id"]] = 0
                pitcher_chipsmeatballs[game["pitcher_id"]] += int(game["strikeouts"]) * 0.2
                daily_performance[day]["chips"].append(pitcher_ks)
                daily_performance[day]["meatballs"].append(pitcher_meatballs[game["pitcher_id"]])
                daily_performance[day]["chipsmeatballs"].append(pitcher_chipsmeatballs[game["pitcher_id"]])
                maximum_events["chips"] = pitcher_ks if (pitcher_ks > maximum_events["chips"]) else maximum_events["chips"]
                maximum_events["meatballs"] = pitcher_meatballs[game["pitcher_id"]] if (pitcher_meatballs[game["pitcher_id"]] > maximum_events["meatballs"]) else maximum_events["meatballs"]
                maximum_events["chipsburgers"] = pitcher_chipsburgers if (pitcher_chipsburgers > maximum_events["chipsburgers"]) else maximum_events["chipsburgers"]
                maximum_events["chipsmeatballs"] = pitcher_chipsmeatballs[game["pitcher_id"]] if (pitcher_chipsmeatballs[game["pitcher_id"]] > maximum_events["chipsmeatballs"]) else maximum_events["chipsmeatballs"]

            for event in mass_event_list:
                if len(daily_performance[day][event]) == 0:
                    continue
                #print("{} Performance for day {}, unsorted: {}".format(event, day, daily_performance[day][event]))
                daily_performance[day][event].sort(reverse=True)
                #print("{} Performance for day {}, sorted: {}".format(event, day, daily_performance[day][event]))
                if len(daily_performance[day][event]) > 2:
                    #daily_mass_event = daily_performance[day][event][0] + daily_performance[day][event][1] + daily_performance[day][event][2]
                    daily_mass_event = daily_performance[day][event][1] + daily_performance[day][event][2]
                elif len(daily_performance[day][event]) > 1:
                    #daily_mass_event = daily_performance[day][event][0] + daily_performance[day][event][1]
                    daily_mass_event = daily_performance[day][event][1]
                else:
                    #daily_mass_event = daily_performance[day][event][0]
                    daily_mass_event = 0.0
                mass_event[event] = daily_mass_event if (daily_mass_event > mass_event[event]) else mass_event[event]           

    return maximum_events, mass_event

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

def calc_half_term(terms, half_stlats, stlat, event):
    val = half_stlats[stlat][event]
    calced_val = terms[event].calc(abs(val))
    try:
        adjustment = calced_val * (val / abs(val))
    except ZeroDivisionError:
        adjustment = calced_val    
    return adjustment

def write_file(outputdir, run_id, filename, content):
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
    with open(os.path.join(outputdir, "{}-{}".format(run_id, filename)), "w") as f:
        f.write(content)

def write_to_file(outputdir, filename, content):
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
    with open(os.path.join(outputdir, "{}".format(filename)), "a") as f:
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
    global CURRENT_ITERATION
    global BEST_FAIL_RATE    
    global BEST_FAILCOUNT    
    global BEST_UNMOD    
    global LAST_CHECKTIME        
    global EXPECTED_MOD_RATES                    
    global MAX_ERROR_GAMES       
    global WORST_MOD    
    global PLUS_NAME
    global HAS_GAMES    
    global LAST_ITERATION_TIME                   
    global LAST_BEST            
    global MIN_DAY
    global MAX_DAY        
    global FAILED_SOLUTIONS    
    global MAX_EVENTS
    global MASS_EVENTS
    global FACTORS
    global PREVIOUS_FOCUS
    global SOLUTIONS_TO_FILL
    calc_func, stlat_list, special_case_list, mod_list, ballpark_list, stat_file_map, ballpark_file_map, game_list, team_attrs, number_to_beat, solve_for_ev, final_solution, solved_terms, solved_halfterms, solved_mods, solved_ballpark_mods, batter_list, crimes_list, solve_batman_too, popsize, focus, debug, debug2, debug3, outputdir, factorsdir, solution_regen = data    
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
        terms = {stat: StlatTerm(a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(parameters[:base_mofo_list_size])] * 3))}
        
    mods = solved_mods if solved_mods else {mod.attr.lower(): {modteam.team.lower(): {modstat.stat.lower(): a for modstat, a in zip(mod_list, parameters[(base_mofo_list_size + special_cases_count):(total_parameters-park_mod_list_size)]) if modstat.team == modteam.team and modstat.attr == mod.attr} for modteam in mod_list} for mod in mod_list}
    ballpark_mods = solved_ballpark_mods if solved_ballpark_mods else {bp.ballparkstat.lower(): {parkterm.playerstat.lower(): ParkTerm(a, b, c) for parkterm, (a, b, c) in zip(ballpark_list, zip(*[iter(parameters[-park_mod_list_size:])] * 3)) if bp.ballparkstat == parkterm.ballparkstat} for bp in ballpark_list}
    half_stlats = solved_halfterms if solved_halfterms else {halfterm.stat.lower(): {halfevent.event.lower(): a for halfevent, a in zip(special_case_list, parameters[base_mofo_list_size:-(team_mod_list_size + park_mod_list_size)]) if halfterm.stat == halfevent.stat} for halfterm in special_case_list}
    
    mod_mode = True
    
    game_counter, fail_counter, season_game_counter, half_fail_counter, pass_exact, pass_within_one, pass_within_two, pass_within_three, pass_within_four = 0, 0, 0, 1000000000, 0, 0, 0, 0, 0
    quarter_fail = 100.0
    linear_fail = 100.0    
    batman_solved_error, batman_best_error, enoch_solved_error, enoch_best_error, pitcher_solved_error, pitcher_best_error, all_seeds_error = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    seeds_error, dogs_error, pickles_error, chips_error, meatballs_error = 0.0, 0.0, 0.0, 0.0, 0.0
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
    ev_set, ev_by_team, games_by_mod, vals_by_mod = {}, {}, {}, {}
    all_vals, win_loss, gameids, early_vals, early_sorted = [], [], [], [], []
    worst_vals, worst_win_loss, worst_gameids, overall_vals, overall_win_loss, overall_gameids, remove_list, steals_remove_list = [], [], [], [], [], [], [], []
    awayAttrs, homeAttrs = [], []    
    cachedAwayMods, cachedHomeMods = List(), List()
    cachedParkAwayMods, cachedParkHomeMods = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
    previous_ballparks = collections.defaultdict(lambda: collections.defaultdict(lambda: 0.5))
    pitching_terms = List([terms["unthwack_base_hit"], terms["ruth_strike"], terms["overp_homer"], terms["overp_triple"], terms["overp_double"], terms["shakes_runner_advances"]])
    defense_terms = List([terms["omni_base_hit"], terms["watch_attempt_steal"], terms["chasi_triple"], terms["chasi_double"], terms["anticap_caught_steal_base"], terms["anticap_caught_steal_home"], terms["tenacious_runner_advances"]])
    batting_terms = List([terms["path_connect"], terms["trag_runner_advances"], terms["thwack_base_hit"], terms["div_homer"], terms["moxie_swing_correct"], terms["muscl_foul_ball"], terms["muscl_triple"], terms["muscl_double"], terms["martyr_sacrifice"]])
    running_terms = List([terms["laser_attempt_steal"], terms["laser_caught_steal_base"], terms["laser_caught_steal_home"], terms["laser_runner_advances"], terms["baset_attempt_steal"], terms["baset_caught_steal_home"], terms["cont_triple"], terms["cont_double"], terms["ground_triple"], terms["indulg_runner_advances"]])    
    list_terms = List([pitching_terms, defense_terms, batting_terms, running_terms])  

    if CURRENT_ITERATION == 1:
        factor_write_file = open(factorsdir, "wb")
        pickle.dump(FACTORS, factor_write_file)
        factor_write_file.close()

    if solve_batman_too:
        solved_hits, solved_homers = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})                   
        solved_ks, solved_era, solved_meatballs = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})        
        seeds_score, seeds_score_earned, seeds_score_max = 0.0, 0.0, 0.0
        dogs_score, dogs_score_earned, dogs_score_max = 0.0, 0.0, 0.0
        seeddogs_score, seeddogs_score_earned, seeddogs_score_max = 0.0, 0.0, 0.0
        chips_score, chips_score_earned, chips_score_max = 0.0, 0.0, 0.0
        burgers_score, burgers_score_earned, burgers_score_max = 0.0, 0.0, 0.0
        meatballs_score, meatballs_score_earned, meatballs_score_max = 0.0, 0.0, 0.0
        chipsburgers_score, chipsburgers_score_earned, chipsburgers_score_max = 0.0, 0.0, 0.0
        chipsmeatballs_score, chipsmeatballs_score_earned, chipsmeatballs_score_max = 0.0, 0.0, 0.0
        hitters, sluggers, seeddogers, chips_pitchers, sho_pitchers = 0, 0, 0, 0, 0  
        perfect_seeds, perfect_dogs, perfect_seeddogs, perfect_chips, perfect_meatballs, perfect_chipsmeatballs = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        qualified_events = ["hits", "homers", "chips", "meatballs"]
        
        burger_penalty = 0.0
        if crimes_list is not None:
            solved_steals = collections.defaultdict(lambda: {})            
            pickles_score, pickles_score_earned, pickles_score_max = 0.0, 0.0, 0.0
            seedpickles_score, seedpickles_score_earned, seedpickles_score_max = 0.0, 0.0, 0.0
            dogpickles_score, dogpickles_score_earned, dogpickles_score_max = 0.0, 0.0, 0.0
            trifecta_score, trifecta_score_earned, trifecta_score_max = 0.0, 0.0, 0.0
            thieves = 0
            perfect_pickles, perfect_seedpickles, perfect_dogpickles, perfect_trifecta = 0.0, 0.0, 0.0, 0.0
            qualified_events.append("steals")
            #all_event_values["steals"] = {}
        all_event_values = {event: {"real_values": [], "solved_values": []} for event in qualified_events}        

    adjustments = {event: calc_half_term(terms, half_stlats, stlat, event) for stlat in half_stlats for event in half_stlats[stlat]}    

    seasonrange = reversed(range(MIN_SEASON, MAX_SEASON + 1))    
    dayrange = range(MIN_DAY, MAX_DAY + 1)    
    days_to_solve = 50 if solve_for_ev else 99          

    if solve_batman_too and (("hits" not in MAX_EVENTS) or ("hits" not in MASS_EVENTS)):
        maxseasonrange, maxdayrange = copy.deepcopy(seasonrange), copy.deepcopy(dayrange)
        MAX_EVENTS, MASS_EVENTS = get_max_events(maxseasonrange, maxdayrange, stat_file_map, team_attrs, game_list, batter_list, crimes_list)

    if solve_batman_too and CURRENT_ITERATION == 1:
        print("Maximum events = {}".format(MAX_EVENTS))
        print("Mass events = {}".format(MASS_EVENTS))

    #non_calcfunc_time, calcfunc_time = 0.0, 0.0
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
            daily_games = 0
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
                    if crimes_list is not None:
                        for batter in real_steals:
                            if batter not in real_hits:
                                real_hits[batter], real_homers[batter] = 0, 0
                                real_seeddogs[batter] = 0.0
                                real_seedpickles[batter] = real_steals[batter] * 3.0
                                real_dogpickles[batter] = real_steals[batter] * 3.0
                                real_trifecta[batter] = real_steals[batter] * 3.0
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
                #non_calcfunc_time_one = time.time()
                homePitcher, homePitcherTeam = pitchers.get(game["home"]["pitcher_id"])                        
                if game["away"]["game_id"] in ATTRS_CACHE:
                    awayAttrs = ATTRS_CACHE[game["away"]["game_id"]][game["away"]["team_id"]]
                    homeAttrs = ATTRS_CACHE[game["away"]["game_id"]][game["home"]["team_id"]]
                else:                          
                    awayAttrs.clear(), homeAttrs.clear()
                    game_attrs = get_attrs_from_paired_game(season_team_attrs, game)
                    awayAttrs, homeAttrs = List(["none", "none"]) if len(game_attrs["away"]) == 0 else List([attr.lower() for attr in game_attrs["away"]]), List(["none", "none"]) if len(game_attrs["home"]) == 0 else List([attr.lower() for attr in game_attrs["home"]])                                        
                    ATTRS_CACHE[game["away"]["game_id"]] = {}
                    ATTRS_CACHE[game["away"]["game_id"]][game["away"]["team_id"]] = List(["none", "none"]) if len(game_attrs["away"]) == 0 else List([attr.lower() for attr in game_attrs["away"]])
                    ATTRS_CACHE[game["away"]["game_id"]][game["home"]["team_id"]] = List(["none", "none"]) if len(game_attrs["home"]) == 0 else List([attr.lower() for attr in game_attrs["home"]])
                gamehomeTeam = get_team_name(game["home"]["team_id"], season, day)
                gameawayTeam = get_team_name(game["away"]["team_id"], season, day)     
                if not using_cached_batters:
                    if float(game["home"]["opposing_team_abs_rbi"]) == 0.0:
                        real_sho.append(game["home"]["pitcher_id"])
                        real_chipsburgers[game["home"]["pitcher_id"]] = int(game["home"]["strikeouts"])
                    if (float(game["away"]["opposing_team_abs_rbi"]) == 0.0) and ("home_field" not in homeAttrs):
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
                    sorted_batters = SORTED_BATTERS_CACHE[game["away"]["game_id"]]
                    (away_shelled, away_active_batters, away_average_aa_impact, away_average_aaa_impact, away_high_pressure_mod, adjusted_stat_data_away, away_team_stat_data, awayPlayerAttrs) = CACHED_CALCED_STAT_DATA[game["away"]["game_id"]]["away"]
                    (home_shelled, home_active_batters, home_average_aa_impact, home_average_aaa_impact, home_high_pressure_mod, adjusted_stat_data_home, home_team_stat_data, homePlayerAttrs) = CACHED_CALCED_STAT_DATA[game["away"]["game_id"]]["home"]
                else:
                    adjusted_stat_data, sorted_batters = calculate_adjusted_stat_data(awayAttrs, homeAttrs, gameawayTeam, gamehomeTeam, team_stat_data)
                    away_shelled, away_active_batters, away_average_aa_impact, away_average_aaa_impact, away_high_pressure_mod, adjusted_stat_data_away, away_team_stat_data, awayPlayerAttrs = get_lists_from_loop(sorted_batters["away"], team_stat_data, gameawayTeam, adjusted_stat_data, "away")
                    home_shelled, home_active_batters, home_average_aa_impact, home_average_aaa_impact, home_high_pressure_mod, adjusted_stat_data_home, home_team_stat_data, homePlayerAttrs = get_lists_from_loop(sorted_batters["home"], team_stat_data, gamehomeTeam, adjusted_stat_data, "home")
                    ADJUSTED_STAT_CACHE[game["away"]["game_id"]] = adjusted_stat_data
                    SORTED_BATTERS_CACHE[game["away"]["game_id"]] = sorted_batters
                    CACHED_CALCED_STAT_DATA[game["away"]["game_id"]] = {}
                    CACHED_CALCED_STAT_DATA[game["away"]["game_id"]]["away"] = (away_shelled, away_active_batters, away_average_aa_impact, away_average_aaa_impact, away_high_pressure_mod, adjusted_stat_data_away, away_team_stat_data, awayPlayerAttrs)
                    CACHED_CALCED_STAT_DATA[game["away"]["game_id"]]["home"] = (home_shelled, home_active_batters, home_average_aa_impact, home_average_aaa_impact, home_high_pressure_mod, adjusted_stat_data_home, home_team_stat_data, homePlayerAttrs)
                ballpark = ballparks.get(game["home"]["team_id"], collections.defaultdict(lambda: 0.5))
                use_cached_mods = USE_CACHED_PARK_MODS.get((season, day, game["home"]["team_id"]))
                if use_cached_mods is None:
                    if CURRENT_ITERATION > 1:
                        print("ParkMods boolean not cached somehow")
                    if game["home"]["team_id"] in previous_ballparks:
                        use_cached_mods = True                        
                        for bpstat, val in ballpark.items():
                            if bpstat in IGNORE_BP_STATS:
                                continue
                            if val != previous_ballparks[game["home"]["team_id"]][bpstat]:
                                #print("Cannot re-use previous mods for team id {} as of season {} day {}; stat {}, new val {}, old val {}".format(game["home"]["team_id"], season, day, bpstat, val, previous_ballparks[game["home"]["team_id"]][bpstat]))
                                use_cached_mods = False
                                break
                    else:
                        use_cached_mods = False
                    USE_CACHED_PARK_MODS[(season, day, game["home"]["team_id"])] = use_cached_mods
                if use_cached_mods:
                    cachedAwayMods, cachedHomeMods = cachedParkAwayMods[game["home"]["team_id"]], cachedParkHomeMods[game["home"]["team_id"]]
                    #print("Confirming cache is correct: \nPrevious ballpark {} \ncurrent ballpark {}".format(previous_ballparks[game["home"]["team_id"]], ballpark))
                else:
                    #print("Not cached")
                    cachedAwayMods, cachedHomeMods = List(), List()
                previous_ballparks[game["home"]["team_id"]] = ballpark
                if solve_batman_too:                                        
                    game_game_counter, game_fail_counter, game_away_val, game_home_val, away_hits, home_hits, away_homers, home_homers, away_stolen_bases, home_stolen_bases, away_pitcher_ks, home_pitcher_ks, away_pitcher_era, home_pitcher_era, awayParkMods, homeParkMods = calc_func(game, awayAttrs, homeAttrs, team_stat_data, sorted_batters, pitcher_stat_data, pitchers, list_terms, mods, ballpark, ballpark_mods, adjusted_stat_data, adjustments, True, cachedAwayMods, cachedHomeMods, away_shelled, away_active_batters, away_average_aa_impact, away_average_aaa_impact, away_high_pressure_mod, adjusted_stat_data_away, away_team_stat_data, awayPlayerAttrs, home_shelled, home_active_batters, home_average_aa_impact, home_average_aaa_impact, home_high_pressure_mod, adjusted_stat_data_home, home_team_stat_data, homePlayerAttrs)                           
                    cachedParkAwayMods[game["home"]["team_id"]], cachedParkHomeMods[game["home"]["team_id"]] = awayParkMods, homeParkMods
                    solved_hits, solved_homers = {**solved_hits, **away_hits, **home_hits}, {**solved_homers, **away_homers, **home_homers}
                    if crimes_list is not None:
                        solved_steals = {**solved_steals, **away_stolen_bases, **home_stolen_bases}
                    solved_ks[game["away"]["pitcher_id"]], solved_ks[game["home"]["pitcher_id"]] = away_pitcher_ks, home_pitcher_ks
                    solved_era[game["away"]["pitcher_id"]], solved_era[game["home"]["pitcher_id"]] = away_pitcher_era, home_pitcher_era
                    total_away_homers, total_home_homers = sum(away_homers.values()), sum(home_homers.values())
                    solved_meatballs[game["away"]["pitcher_id"]], solved_meatballs[game["home"]["pitcher_id"]] = total_home_homers, total_away_homers                                  
                else:
                    game_game_counter, game_fail_counter, game_away_val, game_home_val = calc_func(game, season_team_attrs, team_stat_data, pitcher_stat_data, pitchers, terms, mods, ballpark, ballpark_mods, adjusted_stat_data, adjustments, False)                
                if not is_cached and game_game_counter:
                    good_game_list.extend([game["home"], game["away"]])
                    HAS_GAMES[season] = True
                elif game_game_counter == 0:
                    print("Game being omitted somehow, {}".format(game))
                game_counter += game_game_counter                
                if game_game_counter == 1:   
                    daily_games += 1
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
                    
                    fail_counter += game_fail_counter                                                                
                                                   
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
                            #if solve_for_ev:
                            #    mod_web_fails[name] -= game_web_ev
                            if name in DIRECT_MOD_SOLVES:
                                if name in lowerAwayAttrs:
                                    awayMods += 1  
                                if name in lowerHomeAttrs:
                                    homeMods += 1
                        #if reject_solution:
                        #    break                       
                        if (homeMods > 1) or (awayMods > 1):
                            multi_mod_fails += game_fail_counter
                            multi_mod_games += game_game_counter
                            #if solve_for_ev:
                            #    multi_mod_web_fails -= game_web_ev
                        if awayMods > 0 and homeMods > 0:
                            mvm_fails += game_fail_counter
                            mvm_games += game_game_counter  
                            #if solve_for_ev:
                            #    mvm_web_fails -= game_web_ev
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
                            #if solve_for_ev:
                            #    unmod_web_fails -= game_web_ev  
                #non_calcfunc_time += (non_calcfunc_time_two - non_calcfunc_time_one) + (time.time() - non_calcfunc_time_three)
                #calcfunc_time += calcfunc_time_end - calcfunc_time_start
                #print("Non-calcfunc time = {}\nCalcfunc time     = {}".format(non_calcfunc_time, calcfunc_time))
            if solve_batman_too:               
                if not using_cached_batters:
                    remove_list.clear(), steals_remove_list.clear()                                                          
                    for batter in HITS_CACHE[(season, day)]:                        
                        if batter not in solved_hits:                                                        
                            remove_list.append(batter)      
                    for batter in STEALS_CACHE[(season, day)]:
                        if batter not in solved_steals:
                            steals_remove_list.append(batter)
                    if len(remove_list) > 0:
                        pre_removal_hits_leader = next(iter(HITS_CACHE[(season, day)]))
                        pre_removal_homers_leader = next(iter(HOMERS_CACHE[(season, day)]))
                        pre_removal_seeddogs_leader = next(iter(SEEDDOGS_CACHE[(season, day)]))                        
                        for batter in remove_list:
                            if batter in HITS_CACHE[(season, day)]:
                                HITS_CACHE[(season, day)].pop(batter)
                                HOMERS_CACHE[(season, day)].pop(batter)
                                SEEDDOGS_CACHE[(season, day)].pop(batter)
                            if crimes_list is not None:
                                if batter in STEALS_CACHE[(season, day)]:
                                    STEALS_CACHE[(season, day)].pop(batter)
                                    SEEDPICKLES_CACHE[(season, day)].pop(batter)
                                    DOGPICKLES_CACHE[(season, day)].pop(batter)
                                    TRIFECTA_CACHE[(season, day)].pop(batter)
                        if crimes_list is not None:
                            for batter in steals_remove_list:
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
                    real_hits = copy.copy(HITS_CACHE.get((season, day)))
                    real_homers = copy.copy(HOMERS_CACHE.get((season, day)))
                    real_seeddogs = copy.copy(SEEDDOGS_CACHE.get((season, day)))
                    real_ks = copy.copy(KS_CACHE.get((season, day)))
                    real_sho = copy.copy(SHO_CACHE.get((season, day)))
                    real_meatballs = copy.copy(MEATBALLS_CACHE.get((season, day)))
                    real_chipsburgers = copy.copy(CHIPSBURGERS_CACHE.get((season, day)))
                    real_chipsmeatballs = copy.copy(CHIPSMEATBALLS_CACHE.get((season, day)))
                    if crimes_list is not None:
                        real_steals = copy.copy(STEALS_CACHE.get((season, day)))
                        real_seedpickles = copy.copy(SEEDPICKLES_CACHE.get((season, day)))
                        real_dogpickles = copy.copy(DOGPICKLES_CACHE.get((season, day)))
                        real_trifecta = copy.copy(TRIFECTA_CACHE.get((season, day)))                

                #seeddogs has to be determined sometime and requires going through all of the players anyway, unfortunately  
                new_solved_hits = {k: v for k, v in solved_hits.items() if k in real_hits}
                new_solved_homers = {k: v for k, v in solved_homers.items() if k in real_homers}
                new_solved_steals = {k: v for k, v in solved_steals.items() if k in real_steals}                
                solved_hits_keys, solved_steals_keys = new_solved_hits.keys(), new_solved_steals.keys()
                solved_hits_keys_set, solved_steals_keys_set = set(solved_hits_keys), set(solved_steals_keys)                
                all_batters_keys_set = solved_hits_keys_set.union(solved_steals_keys_set)                
                unified_solved_batters = list(all_batters_keys_set)                
                solved_seeddogs = {playerid: ((solved_hits[playerid] * 1.5) + (solved_homers[playerid] * 4.0)) for playerid in unified_solved_batters}
                if crimes_list is not None:
                    solved_seedpickles = {playerid: ((solved_hits[playerid] * 1.5) + (solved_steals[playerid] * 3.0)) for playerid in unified_solved_batters}
                    solved_dogpickles = {playerid: ((solved_homers[playerid] * 4.0) + (solved_steals[playerid] * 3.0)) for playerid in unified_solved_batters}
                    solved_trifecta = {playerid: ((solved_hits[playerid] * 1.5) + (solved_homers[playerid] * 4.0) + (solved_steals[playerid] * 3.0)) for playerid in unified_solved_batters}                
                
                unified_solved_batters.clear()

                new_solved_ks = {k: v for k, v in solved_ks.items() if k in real_ks}
                new_solved_meatballs = {k: v for k, v in solved_meatballs.items() if k in real_ks}
                solved_chipsmeatballs = {playerid: ((solved_ks[playerid] * 0.2) + solved_meatballs[playerid]) for playerid in new_solved_ks}
                            
                sorted_solved_hits, sorted_solved_homers = dict(sorted(new_solved_hits.items(), key=lambda k: k[1], reverse=True)), dict(sorted(new_solved_homers.items(), key=lambda k: k[1], reverse=True))
                sorted_solved_seeddogs, sorted_solved_meatballs = dict(sorted(solved_seeddogs.items(), key=lambda k: k[1], reverse=True)), dict(sorted(new_solved_meatballs.items(), key=lambda k: k[1], reverse=True))
                sorted_solved_ks, sorted_solved_era = dict(sorted(new_solved_ks.items(), key=lambda k: k[1], reverse=True)), dict(sorted(solved_era.items(), key=lambda k: k[1], reverse=False))
                sorted_solved_chipsmeatballs = dict(sorted(solved_chipsmeatballs.items(), key=lambda k: k[1], reverse=True))
                if crimes_list is not None:                    
                    sorted_solved_steals = dict(sorted(new_solved_steals.items(), key=lambda k: k[1], reverse=True)) 
                    sorted_solved_seedpickles = dict(sorted(solved_seedpickles.items(), key=lambda k: k[1], reverse=True))
                    sorted_solved_dogpickles = dict(sorted(solved_dogpickles.items(), key=lambda k: k[1], reverse=True))
                    sorted_solved_trifecta = dict(sorted(solved_trifecta.items(), key=lambda k: k[1], reverse=True))                                              

                if crimes_list is not None:
                    all_event_values, pickles_score_earned, pickles_score_max, perfect_pickles, pickles_error = calc_snack("steals", all_event_values, real_steals, sorted_solved_steals, pickles_score_earned, pickles_score_max, MAX_EVENTS["steals"], MASS_EVENTS["steals"], perfect_pickles, single_calc, pickles_error)

                    all_event_values, seedpickles_score_earned, seedpickles_score_max, perfect_seedpickles, pickles_error, seeds_error = calc_snack("seedpickles", all_event_values, real_seedpickles, sorted_solved_seedpickles, seedpickles_score_earned, seedpickles_score_max, MAX_EVENTS["seedpickles"], MASS_EVENTS["seedpickles"], perfect_seedpickles, double_calc, pickles_error, real_steals, 3.0, seeds_error, real_hits, 1.5)

                    all_event_values, dogpickles_score_earned, dogpickles_score_max, perfect_dogpickles, pickles_error, dogs_error = calc_snack("dogpickles", all_event_values, real_dogpickles, sorted_solved_dogpickles, dogpickles_score_earned, dogpickles_score_max, MAX_EVENTS["dogpickles"], MASS_EVENTS["dogpickles"], perfect_dogpickles, double_calc, pickles_error, real_steals, 3.0, dogs_error, real_homers, 4.0)

                    all_event_values, trifecta_score_earned, trifecta_score_max, perfect_trifecta, pickles_error, batman_best_error = calc_snack("trifecta", all_event_values, real_trifecta, sorted_solved_trifecta, trifecta_score_earned, trifecta_score_max, MAX_EVENTS["trifecta"], MASS_EVENTS["trifecta"], perfect_trifecta, triple_calc, pickles_error, real_steals, 3.0, seeds_error, real_hits, 1.5, dogs_error, real_homers, 4.0) 
                    
                    thieves += 1                    

                if len(real_sho) > 0:
                    best_burgers_score = 12.5
                    best_chipsburgers_player = next(iter(real_chipsburgers))
                    best_chipsburgers_score = (real_ks[best_chipsburgers_player] * 0.2) + 12.5
                    sho_pitchers += 1
                else:
                    best_burgers_score, best_chipsburgers_score = 0.0, 0.0
                
                all_event_values, seeds_score_earned, seeds_score_max, perfect_seeds, seeds_error = calc_snack("hits", all_event_values, real_hits, sorted_solved_hits, seeds_score_earned, seeds_score_max, MAX_EVENTS["hits"], MASS_EVENTS["hits"], perfect_seeds, single_calc, seeds_error)

                all_event_values, dogs_score_earned, dogs_score_max, perfect_dogs, dogs_error = calc_snack("homers", all_event_values, real_homers, sorted_solved_homers, dogs_score_earned, dogs_score_max, MAX_EVENTS["homers"], MASS_EVENTS["homers"], perfect_dogs, single_calc, dogs_error)                                                                          

                all_event_values, seeddogs_score_earned, seeddogs_score_max, perfect_seeddogs, seeds_error, dogs_error = calc_snack("seeddogs", all_event_values, real_seeddogs, sorted_solved_seeddogs, seeddogs_score_earned, seeddogs_score_max, MAX_EVENTS["seeddogs"], MASS_EVENTS["seeddogs"], perfect_seeddogs, double_calc, seeds_error, real_hits, 1.5, dogs_error, real_homers, 4.0)

                hitters += 1

                all_event_values, chips_score_earned, chips_score_max, perfect_chips, chips_error = calc_snack("chips", all_event_values, real_ks, sorted_solved_ks, chips_score_earned, chips_score_max, MAX_EVENTS["chips"], MASS_EVENTS["chips"], perfect_chips, single_calc, chips_error)

                all_event_values, meatballs_score_earned, meatballs_score_max, perfect_meatballs, meatballs_error = calc_snack("meatballs", all_event_values, real_meatballs, sorted_solved_meatballs, meatballs_score_earned, meatballs_score_max, MAX_EVENTS["meatballs"], MASS_EVENTS["meatballs"], perfect_meatballs, single_calc, meatballs_error)

                all_event_values, chipsmeatballs_score_earned, chipsmeatballs_score_max, perfect_chipsmeatballs, chips_error, meatballs_error = calc_snack("chipsmeatballs", all_event_values, real_chipsmeatballs, sorted_solved_chipsmeatballs, chipsmeatballs_score_earned, chipsmeatballs_score_max, MAX_EVENTS["chipsmeatballs"], MASS_EVENTS["chipsmeatballs"], perfect_chipsmeatballs, double_calc, chips_error, real_ks, 0.2, meatballs_error, real_meatballs, 1.0)

                chips_pitchers += 1
                
                if len(real_sho) > 0:
                    burgers_score_max += best_burgers_score
                    chipsburgers_score_max += best_chipsburgers_score
                    solved_burgers_leader = next(iter(sorted_solved_era))
                    if solved_burgers_leader in real_sho:
                        pitcher_burgers_score = 12.5
                        pitcher_chipsburgers_score = pitcher_burgers_score + (real_ks[solved_burgers_leader] * 0.2)
                        burgers_score_earned += pitcher_burgers_score
                        chipsburgers_score_earned += pitcher_chipsburgers_score  
                        burger_penalty += calc_penalty(best_chipsburgers_score, pitcher_chipsburgers_score, MAX_EVENTS["chipsburgers"], 6.0)
                    else:
                        pitcher_burgers_score = 0.0
                        pitcher_chipsburgers_score = (pitcher_burgers_score + real_ks[solved_burgers_leader] * 0.2) / best_chipsburgers_score
                        burgers_fail_metric = len(real_sho) / daily_games
                        chipsburgers_score_earned += real_ks[solved_burgers_leader] * 0.2
                        max_chipsburgers_random = ((burgers_fail_metric * 12.5) + (best_chipsburgers_score - 12.5)) / best_chipsburgers_score
                        burger_penalty += calc_penalty(burgers_fail_metric, pitcher_burgers_score, 1.0, 6.0) 
                        burger_penalty += calc_penalty(max_chipsburgers_random, pitcher_chipsburgers_score, 1.0, 6.0)
                
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
            
    batman_linearity_error = {}

    for event in all_event_values:
        #print("Checking {}".format(event))
        batman_linearity_error[event] = sort_batman_linear_penalty(event, all_event_values[event], MAX_EVENTS[event])

    del solved_hits, solved_homers, solved_seeddogs, solved_ks, solved_era, solved_meatballs, solved_chipsmeatballs, sorted_solved_hits, sorted_solved_homers, sorted_solved_seeddogs, sorted_solved_ks, sorted_solved_era, sorted_solved_meatballs, sorted_solved_chipsmeatballs
    if crimes_list is not None:
        del solved_steals, solved_seedpickles, solved_dogpickles, solved_trifecta, sorted_solved_steals, sorted_solved_seedpickles, sorted_solved_dogpickles, sorted_solved_trifecta

    #max_individual_event = max(MAX_EVENTS["hits"], MAX_EVENTS["homers"], MAX_EVENTS["steals"], MAX_EVENTS["chips"], MAX_EVENTS["meatballs"])

    #try just linearity instead
    linear_correction = len(all_event_values["hits"]["real_values"]) / len(all_event_values["chips"]["real_values"])
    #print("Correcting for {} hitters vs {} pitchers; {} thieves".format(len(all_event_values["hits"]["real_values"]), len(all_event_values["chips"]["real_values"]), len(all_event_values["steals"]["real_values"])))
    seeds_error = batman_linearity_error["hits"]
    dogs_error = batman_linearity_error["homers"]
    pickles_error = batman_linearity_error["steals"]
    chips_error = batman_linearity_error["chips"] * linear_correction
    meatballs_error = batman_linearity_error["meatballs"] * linear_correction    

    all_event_values.clear()
    del all_event_values    
            
    fail_points, linear_points = 10000000000.0, 10000000000.0    
    max_fail_rate, expected_average = 0.0, 0.25
    longest_modname = 0
    #new_worstmod_linear_error = max(worstmod_linear_error, unmod_linear_error)    
    new_worstmod_linear_error, unmod_linear_error, linear_error = 0.0, 0.0, 0.0     
    max_mod_unmod, max_error_game, new_plusname = "", "", ""
    new_worstmod = WORST_MOD
    best_plusname = PLUS_NAME
    max_mod_rates, mod_win_loss, mod_gameids, errors, sorted_win_loss, mod_vals = [], [], [], [], [], []
    other_errors, linear_by_mod = {}, {}
    linear_fail = 9000000000000000.0    
    season_fail = 100000000.0
    calculate_solution = True
    batman_score, correction_adjustment = 1.0, 1.0
    if solve_batman_too:        
        pickles_penalty, seedpickles_penalty, dogpickles_penalty, trifecta_penalty = 0.0, 0.0, 0.0, 0.0                
        #combine seed and dog events together into one        
        seeds_score = seeds_score_earned / seeds_score_max
        dogs_score = dogs_score_earned / dogs_score_max        
        seeddogs_score = seeddogs_score_earned / seeddogs_score_max
        chips_score = chips_score_earned / chips_score_max        
        meatballs_score = meatballs_score_earned / meatballs_score_max
        allpitchresults_score = (chips_score + seeds_score + dogs_score + meatballs_score) / 4.0        
        chipsmeatballs_score = chipsmeatballs_score_earned / chipsmeatballs_score_max
        burgers_score, chipsburgers_score = 0.0, 0.0
        if burgers_score_max > 0.0:
            burgers_score = burgers_score_earned / burgers_score_max         
            chipsburgers_score = chipsburgers_score_earned / chipsburgers_score_max         
        if crimes_list is not None:
            pickles_score = pickles_score_earned / pickles_score_max
            allhitspickles_score = ((seedpickles_score_earned / seedpickles_score_max) + (dogpickles_score_earned / dogpickles_score_max)) / 2.0            
            seedpickles_score = seedpickles_score_earned / seedpickles_score_max
            dogpickles_score = dogpickles_score_earned / dogpickles_score_max
            trifecta_score = trifecta_score_earned / trifecta_score_max                                    
        if CURRENT_ITERATION == 1:
            print("Max BATMAN earnings = seeds {:.0f}, dogs {:.0f}, seeds+dogs {:.0f}".format(seeds_score_max, dogs_score_max, seeddogs_score_max))
            if crimes_list is not None:
                print("Max ENOCH earnings = pickles {:.0f}, seeds+pickes {:.0f}, dogs+pickles {:.0f}, trifecta {:.0f}".format(pickles_score_max, seedpickles_score_max, dogpickles_score_max, trifecta_score_max))
            print("Max pitching earnings = chips {:.0f}, burgers {:.0f}, meatballs {:.0f}, chips+burgers {:.0f}, chips+meatballs {:.0f}".format(chips_score_max, burgers_score_max, meatballs_score_max, chipsburgers_score_max, chipsmeatballs_score_max))
            print("{} Shutout pitchers, {} pitchers, {} batters".format(sho_pitchers, chips_pitchers, hitters))                                  
        best_error = seeds_error + dogs_error + pickles_error + chips_error + meatballs_error + burger_penalty
        weighted_multiplier, unweighted_multiplier, pickles_multiplier = 3.0, 0.7, 1.0
        errors = {}
        errors["all"] = seeds_error + dogs_error + pickles_error + chips_error + meatballs_error + burger_penalty        
        errors["seeds"] = seeds_error
        errors["dogs"] = dogs_error
        errors["pickles"] = pickles_error
        errors["chips"] = chips_error
        errors["meatballs"] = meatballs_error
        weighted_best_error = errors["all"]
        linear_error += weighted_best_error                
    
    if not reject_solution:
        if len(win_loss) > 0:        
            #Remember to negate ev is when we can pass it through and make better results when EV is bigger
            expected_val, mismatches, dadbets, web_ev, current_mofo_ev, current_web_ev = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0   
            pos_vals = [val for val in all_vals if val >= 0.5]
            #for val in all_vals:
            #    if val >= 0.5:
            #        pos_vals.append(val)
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
                sorted_win_loss = [val for _, val in sorted(zip(mod_vals, mod_win_loss))]
                #for _,x in sorted(zip(mod_vals, mod_win_loss)):
                #    sorted_win_loss.append(x)
                #sorted_win_loss = [x for _,x in sorted(zip(mod_vals, mod_win_loss))]                    
                mod_vals.sort()                        
                mod_linear_error, mod_max_linear_error, mod_min_linear_error, mod_max_error_value, mod_min_error_value = calc_linear_unex_error(mod_vals, sorted_win_loss, modname)                
                mod_pos_vals = [val for val in mod_vals if val >= 0.5]                            
                if modname == "unmod":
                    unmod_linear_error = mod_linear_error                        
                    mod_rate = unmod_rate
                elif not new_plusname == "":
                    mod_rate = (mod_rates[modname] + mod_rates[new_plusname]) / 2.0                        
                else:
                    mod_rate = mod_rates[modname]
                mod_expected_average = 100.0 - ((sum(mod_pos_vals) / len(mod_pos_vals)) * 100.0)
                mod_pos_vals.clear()
                EXPECTED_MOD_RATES[modname] = mod_expected_average
                if not new_plusname == "":
                    EXPECTED_MOD_RATES[new_plusname] = mod_expected_average                    
                linear_error_reduction = (1.0 - (abs(mod_rate - mod_expected_average) / 100.0)) * (100.0 - mod_expected_average)    
                #include batman modifier before subtraction, to make sure large batman errors don't inflate a large negative number                
                mod_linear_error *= modcount if modname not in DIRECT_MOD_SOLVES else 1.0
                #mod_linear_error *= 0.1
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
            sorted_win_loss = [val for _, val in sorted(zip(overall_vals, overall_win_loss))]
            #for _,x in sorted(zip(overall_vals, overall_win_loss)):
            #    sorted_win_loss.append(x)
            #sorted_win_loss = [x for _,x in sorted(zip(overall_vals, overall_win_loss))]                
            overall_vals.sort()                    
            overall_linear_error, overall_max_linear_error, overall_min_linear_error, overall_max_error_value, overall_min_error_value = calc_linear_unex_error(overall_vals, sorted_win_loss, "overall")
            #overall_linear_error *= 0.1
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
                        if abs(mod_rates[name] - 25.0) > max_fail_rate:
                            max_fail_rate = mod_rates[name]
                            max_mod_unmod = name                                                                     
                if unmod_games > 0:                                       
                    unmod_rate = (unmod_fails / unmod_games) * 100.0                    
                    if unmod_rate > max_fail_rate:
                        max_fail_rate = unmod_rate
                        max_mod_unmod = "unmod"                                                                               
                if calculate_solution or solve_for_ev:                                                               
                    mod_error, aggregate_fail_rate = 0.0, 0.25
                    all_rates = [(mod_rates[name] / 100.0) for name in mod_rates]
                    #for name in mod_rates:
                    #    all_rates.append(mod_rates[name] / 100.0)                        
                    all_rates.append(unmod_rate / 100.0)                                   
                    for rate in all_rates:
                        if abs(rate - 0.25) > abs(aggregate_fail_rate - 0.25):
                            aggregate_fail_rate = rate
                        mod_error += abs(rate - 0.25)                    
                    fail_points = ((aggregate_fail_rate * 1000.0) ** 2.0)                    
                    linear_fail = linear_points     
    
    minimum_focused_error, min_factors_alls = 0.0, 0.0
    if solution_regen:
        publish_solution = True        
        if CURRENT_ITERATION == 1:
            factor_file = open(factorsdir, "rb")        
            FACTORS = pickle.load(factor_file)        
            factor_file.close()                
        for possible_focus in FACTORS:
            if possible_focus == "all":
                max_all = max(FACTORS["all"])
                max_all_idx = FACTORS["all"].index(max_all)
                continue
            focused_values = List(FACTORS[possible_focus])
            possible_result, possible_focused, possible_factor, possible_replacement_index, possible_min_all = get_factor_and_best(focused_values)
            focused_result = errors[possible_focus] * (possible_result / possible_focused)
            if (focused_result < minimum_focused_error) or (minimum_focused_error == 0.0):
                minimum_focused_error = focused_result           
    else:        
        factor_file = open(factorsdir, "rb")        
        FACTORS = pickle.load(factor_file)        
        factor_file.close()
        publish_solution = False
        #print("Testing that this part works correctly: factors = {}".format(FACTORS))
        last_possible_result, max_focused_error = 0.0, 0.0
        for possible_focus in FACTORS:
            if possible_focus == "all":
                max_all = max(FACTORS["all"])
                max_all_idx = FACTORS["all"].index(max_all)                
                if linear_points < max_all:
                    publish_solution = True
                #print("Checking linear points {}, max_all {}, publish solution {}, logic check = {}".format(linear_points, max_all, publish_solution, linear_points < max_all))
                continue
            #print("Possible focus = {}".format(possible_focus))
            focused_values = List(FACTORS[possible_focus])
            possible_result, possible_focused, possible_factor, possible_replacement_index, possible_min_all = get_factor_and_best(focused_values)                                    
            focused_result = errors[possible_focus] * (possible_result / possible_focused)
            if (focused_result < minimum_focused_error) or (minimum_focused_error == 0.0):
                minimum_focused_error = focused_result
            if (errors[possible_focus] < possible_focused) and (linear_points < possible_result):
                publish_solution = True                
            if possible_result >= last_possible_result:
                focused_result = possible_focused
                last_possible_result = possible_result
                focus = possible_focus  
            if (min_factors_alls == 0.0) or (min_factors_alls > possible_min_all):
                min_factors_alls = possible_min_all
        if max_all > min_factors_alls:
            focus = "all"
        if focus == "all":                        
            BEST_RESULT = min(FACTORS["all"])
            if linear_fail < BEST_RESULT:
                BEST_RESULT = linear_fail                                                                   
        else:
            if CURRENT_ITERATION == 1:
                BEST_RESULT = 24276626267281400.0

    if CURRENT_ITERATION == 1: 
        SOLUTIONS_TO_FILL = popsize
        print("All Factors = {}".format(FACTORS))
        FAILED_SOLUTIONS = [BEST_RESULT] * popsize
    elif focus != PREVIOUS_FOCUS:  
        SOLUTIONS_TO_FILL = popsize
        print("Previous focus = {}, current focus = {}".format(PREVIOUS_FOCUS, focus))
        for idx in range(0, len(FAILED_SOLUTIONS)):
            FAILED_SOLUTIONS[idx] = BEST_RESULT

    population_member = CURRENT_ITERATION % popsize    
    #publish_solution = linear_fail < FAILED_SOLUTIONS[population_member]    
    #if ((linear_fail < BEST_RESULT) and publish_solution and focus == "all") or (publish_solution and focus != "all") or solution_regen:     
    if publish_solution or solution_regen:
        #if focus == "all":
            #BEST_RESULT = linear_fail                
        reported_focus = []        
        if not solution_regen:
            factor_file = open(factorsdir, "rb")        
            FACTORS = pickle.load(factor_file)
            factor_file.close()        
            factor_write_file = open(factorsdir, "wb")
            for pot_focus in FACTORS:
                if pot_focus == "all":
                    max_all = max(FACTORS["all"])
                    max_all_idx = FACTORS["all"].index(max_all)
                    if linear_points < max_all:
                        FACTORS["all"][max_all_idx] = linear_points
                        pickle.dump(FACTORS, factor_write_file)
                        max_all = max(FACTORS["all"])
                    continue
                focused_values = List(FACTORS[pot_focus])
                possible_result, possible_focused, possible_factor, possible_replacement_index, possible_min_all = get_factor_and_best(focused_values)                
                if (errors[pot_focus] < possible_focused) and (linear_points < possible_result):
                    reported_focus.append(pot_focus)
                    FACTORS[pot_focus][possible_replacement_index] = (int(errors[pot_focus]), int(linear_points))                        
                    pickle.dump(FACTORS, factor_write_file)
                    if pot_focus == focus:       
                        focused_values = List(FACTORS[focus])
                        new_result, new_focused, new_best_focus, new_replacement_index, possible_min_all = get_factor_and_best(focused_values)
                focused_result = errors[pot_focus] * (possible_result / possible_focused)
                if (focused_result < minimum_focused_error) or (minimum_focused_error == 0.0):
                    minimum_focused_error = focused_result
                focused_error = possible_factor * (possible_result / possible_focused)
                max_focused_error = max(max_focused_error, focused_error, possible_result)
            factor_write_file.close()         
            if focus != "all":
                BEST_RESULT = min(minimum_focused_error, BEST_RESULT)                
        PLUS_NAME = best_plusname
        WORST_MOD = new_worstmod                                          
        if len(win_loss) > 0:
            BEST_FAIL_RATE = fail_rate            
            if solve_for_ev:
                BEST_FAILCOUNT = ev_neg_count
                LAST_BEST = BEST_FAILCOUNT
            else:                
                LAST_BEST = new_worstmod_linear_error                               
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
            detailtext = "{} games, pop member {}".format(game_counter, population_member)
            detailtext += "\n{}{:.2f}% Unmodded,".format(("" if unmod_rate >= 10 else " "), unmod_rate) + (" " * (longest_modname - 8))
            detailtext += " {}{:.2f}% expected, {} games, error {:.0f}".format(("" if EXPECTED_MOD_RATES["unmod"] >= 10 else " "), EXPECTED_MOD_RATES["unmod"], unmod_games, linear_by_mod["unmod"])
            for name in mod_rates:
                detailtext += "\n{}{:.2f}% {},".format(("" if mod_rates[name] >= 10 else " "), mod_rates[name], name) + (" " * (longest_modname - len(name)))    
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
            #if solution_regen:
            #    override_failure = (seeds_error / regen_overrides["seeds"]) if (regen_overrides["seeds"] <= seeds_error) else 0
            #    override_failure += (dogs_error / regen_overrides["dogs"]) if (regen_overrides["dogs"] <= dogs_error) else 0
            #    override_failure += (pickles_error / regen_overrides["pickles"]) if (regen_overrides["pickles"] <= pickles_error) else 0
            #    override_failure += (chips_error / regen_overrides["chips"]) if (regen_overrides["chips"] <= chips_error) else 0
            #    override_failure += (meatballs_error / regen_overrides["meatballs"]) if (regen_overrides["meatballs"] <= meatballs_error) else 0
            #    linear_fail = override_failure * 10000.0
            detailtext += "\nBest so far - Linear fail {:.0f} ({:.2f}% from best errors), worst mod = {}, {:.0f}, fail rate {:.2f}%, expected {:.2f}%".format(max(minimum_focused_error, linear_points), (best_error / linear_points) * 100.0, WORST_MOD, LAST_BEST, fail_rate * 100.0, (1.0 - expected_average) * 100.0)
            detailtext += "\nBest so far - modified    {:.0f}".format(linear_fail)
            #if solve_for_ev:
            #    detailtext += "\nNet EV = {:.4f}, web EV = {:.4f}, season EV = {:.4f}, mismatches = {:.4f}, dadbets = {:.4f}".format(expected_val, web_ev, (-1 * BEST_SEASON), mismatches, dadbets)                        
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
            detailtext += "\nSeeds     = {:.0f}".format(seeds_error)
            detailtext += "\nDogs      = {:.0f}".format(dogs_error)
            detailtext += "\nMeatballs = {:.0f}".format(meatballs_error)
            detailtext += "\nPickles   = {:.0f}".format(pickles_error)
            detailtext += "\nChips     = {:.0f}".format(chips_error)
            detailtext += "\nBurgers   = {:.0f}".format(burger_penalty)
            if solve_batman_too:
                thresholds = {}
                thresholds["seeds"], thresholds["dogs"], thresholds["seeddogs"], thresholds["pickles"], thresholds["seedpickles"], thresholds["dogpickles"], thresholds["trifecta"] = 0.4902, 0.1897, 0.4886, 0.3649, 0.3906, 0.3681, 0.4327
                detailtext += "\nBATMAN earnings (% of max possible) -  Seeds {:.2f}%{} ({:.2f}% Perfect), Dogs {:.2f}%{} ({:.2f}% Perfect), Seeds+Dogs {:.2f}%{} ({:.2f}% Perfect)".format(seeds_score * 100.0, ("!" if seeds_score > thresholds["seeds"] else ""), (perfect_seeds / seeds_score_max) * 100.0, dogs_score * 100.0, ("!" if dogs_score > thresholds["dogs"] else ""), (perfect_dogs / dogs_score_max) * 100.0, seeddogs_score * 100.0, ("!" if seeddogs_score > thresholds["seeddogs"] else ""), (perfect_seeddogs / seeddogs_score_max) * 100.0)
                if crimes_list is not None:
                    detailtext += "\nENOCH earnings (% of max possible) - Pickles {:.2f}%{} ({:.2f}% Perfect), Seeds+Pickles {:.2f}%{} ({:.2f}% Perfect), Dogs+Pickles {:.2f}%{} ({:.2f}% Perfect), Trifecta {:.2f}%{} ({:.2f}% Perfect)".format(pickles_score * 100.0, ("!" if pickles_score > thresholds["pickles"] else ""), (perfect_pickles / pickles_score_max) * 100.0, seedpickles_score * 100.0, ("!" if seedpickles_score > thresholds["seedpickles"] else ""), (perfect_seedpickles / seedpickles_score_max) * 100.0, dogpickles_score * 100.0, ("!" if dogpickles_score > thresholds["dogpickles"] else ""), (perfect_dogpickles / dogpickles_score_max) * 100.0, trifecta_score * 100.0, ("!" if trifecta_score > thresholds["trifecta"] else ""), (perfect_trifecta / trifecta_score_max) * 100.0)
                detailtext += "\nPitcher earnings (% of max possible) - Chips {:.2f}% ({:.2f}% Perfect), Burgers {:.2f}%, Meatballs {:.2f}% ({:.2f}% Perfect), Chips+Burgers {:.2f}%, Chips+Meatballs {:.2f}% ({:.2f}% Perfect)".format(chips_score * 100.0, (perfect_chips / chips_score_max) * 100.0, burgers_score * 100.0, meatballs_score * 100.0, (perfect_meatballs / meatballs_score_max) * 100.0, chipsburgers_score * 100.0, chipsmeatballs_score * 100.0, (perfect_chipsmeatballs / chipsmeatballs_score_max) * 100.0)                    
                if not solution_regen:
                    detailtext += "\n{}-all factors: {}".format(run_id, FACTORS)
                    #if len(reported_focus) > 0:
                    #    for report_focus in reported_focus:
                    #        detailtext += "\n{}-factors '{}': {}".format(run_id, report_focus, FACTORS[report_focus])
                detailtext += "\n{}-details,{},{},{},{},{},{}".format(run_id, int(seeds_error), int(dogs_error), int(pickles_error), int(chips_error), int(meatballs_error), int(linear_points))   
            debug_print(detailtext, debug, run_id)
            if outputdir:
                write_file(outputdir, run_id, "details.txt", detailtext)
                if solution_regen:
                    solutiontext = "{}-details,{},{},{},{},{},{}\n".format(run_id, int(seeds_error), int(dogs_error), int(pickles_error), int(chips_error), int(meatballs_error), int(linear_points))
                    write_to_file(outputdir, "solutions.txt", solutiontext)
            if sys.platform == "darwin":  # MacOS
                os.system("""osascript -e 'display notification "Fail rate {:.4f}%" with title "New solution found!"'""".format(fail_rate * 100.0))                        
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
        debug_print("-" * 20 + "\n", debug, run_id) 
        
    if focus != "all":
        focused_fail = max(minimum_focused_error, linear_points)
        if SOLUTIONS_TO_FILL > 0:
            FAILED_SOLUTIONS[population_member] = focused_fail
            SOLUTIONS_TO_FILL -= 1
        else:
            FAILED_SOLUTIONS[population_member] = min(focused_fail, FAILED_SOLUTIONS[population_member])
    else:
        if SOLUTIONS_TO_FILL > 0:
            FAILED_SOLUTIONS[population_member] = linear_fail
            SOLUTIONS_TO_FILL -= 1
        else:
            FAILED_SOLUTIONS[population_member] = min(linear_fail, FAILED_SOLUTIONS[population_member])

    #if CURRENT_ITERATION % 500 == 0:
    #    gc.collect()
    #    time.sleep(10)

    if (CURRENT_ITERATION % 10 == 0 and CURRENT_ITERATION <= 50) or (CURRENT_ITERATION % 100 == 0 and CURRENT_ITERATION < 1000) or (CURRENT_ITERATION % 500 == 0):
        if len(win_loss) > 0:                        
            worstmod_report = WORST_MOD + (" " + PLUS_NAME if (PLUS_NAME != "") else "")                                                             
            try:         
                solutions_to_evaluate = FAILED_SOLUTIONS[:]
                if focus == "all":
                    if min(solutions_to_evaluate) == BEST_RESULT:
                        solutions_to_evaluate.remove(BEST_RESULT)
                #else:
                #    while min(solutions_to_evaluate) < BEST_RESULT:
                #        remove_value = min(solutions_to_evaluate)
                #        solutions_to_evaluate.remove(remove_value)
                average_fail = (fmean(solutions_to_evaluate) / BEST_RESULT) * 100
                max_fail = (max(solutions_to_evaluate) / BEST_RESULT) * 100.0
                min_fail = (min(solutions_to_evaluate) / BEST_RESULT) * 100.0
                best_pop_member = solutions_to_evaluate.index(min(solutions_to_evaluate))
                solutions_text = "avg {:.2f}%, max {:.2f}%, min {:.2f}%, {} best at {}".format(average_fail, max_fail, min_fail, focus, best_pop_member)
            except (ZeroDivisionError, FloatingPointError, StatisticsError):
                solutions_text = ""                                    
            now = datetime.datetime.now()                
            debug_print("Best so far - {:.2f}, iteration #{}, {}, {:.2f} seconds".format(BEST_RESULT, CURRENT_ITERATION, solutions_text, (now-LAST_ITERATION_TIME).total_seconds()), debug, now)   
            LAST_ITERATION_TIME = now
        else:
            debug_print("Best so far - {:.4f}, iteration # {}".format(BEST_RESULT, CURRENT_ITERATION), debug, datetime.datetime.now())
    CURRENT_ITERATION += 1           
    now = datetime.datetime.now()          
    debug_print("run fail rate {:.4f}%".format(fail_rate * 100.0), debug2, run_id)
    endtime = datetime.datetime.now()
    debug_print("func end: {}, run time {}".format(endtime, endtime-starttime), debug3, run_id)
    PREVIOUS_FOCUS = focus
    return_value = focused_fail if (focus != "all") else linear_fail                 
    #return return_value
    #return BEST_RESULT
    return linear_fail
    