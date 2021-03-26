import collections
import csv
import time
import math
import datetime
import json
import os
import re
import uuid
from glob import glob

from helpers import StlatTerm, get_weather_idx
from idolthoughts import load_stat_data
from mofonew import get_mods

STAT_CACHE = {}
GAME_CACHE = {}

BEST_RESULT = 10000000000.0
BEST_FAIL_RATE = 1.0
BEST_LINEAR_ERROR = 1.0
BEST_EXACT = 10000000000.0
CURRENT_ITERATION = 1
LAST_CHECKTIME = 0.0
BEST_QUARTER_FAIL = 1.0
TOTAL_GAME_COUNTER = 0
MAX_OBSERVED_DIFFERENCE = 0.0
BEST_LOVE = 10000000000.0
BEST_INSTINCT = 10000000000.0
BEST_ONO = 10000000000.0
BEST_WIP = 10000000000.0
BEST_EXK = 10000000000.0
BEST_EXB = 10000000000.0
BASE_LOVE = 10000000000.0
BASE_INSTINCT = 10000000000.0
BASE_ONO = 10000000000.0
BASE_WIP = 10000000000.0
BASE_EXK = 10000000000.0
BASE_EXB = 10000000000.0
WORST_ERROR = 1000000000
MOD_BASELINE = False
HAS_GAMES = {}

ALLOWED_IN_BASE = {"AFFINITY_FOR_CROWS", "GROWTH", "TRAVELING"}
FORCE_REGEN = {"AFFINITY_FOR_CROWS", "GROWTH", "TRAVELING"}

BIRD_WEATHER = get_weather_idx("Birds")


def get_pitcher_id_lookup(filename):
    with open(filename) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    return {row["id"]: (row["name"], row["team"]) for row in filedata if row["position"] == "rotation"}


def get_games(filename):
    with open(filename) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    return filedata


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
                attr == "AFFINITY_FOR_CROWS" and int(game["weather"]) != BIRD_WEATHER):
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

def minimize_func(parameters, *data):
    run_id = uuid.uuid4()
    starttime = datetime.datetime.now()
    global BEST_RESULT
    global CURRENT_ITERATION
    global BEST_FAIL_RATE
    global BEST_LINEAR_ERROR
    global BEST_EXACT
    global LAST_CHECKTIME
    global BEST_QUARTER_FAIL
    global TOTAL_GAME_COUNTER
    global MAX_OBSERVED_DIFFERENCE
    global BEST_LOVE
    global BEST_INSTINCT
    global BEST_ONO
    global BEST_WIP
    global BEST_EXK
    global BEST_EXB
    global BASE_LOVE
    global BASE_INSTINCT
    global BASE_ONO
    global BASE_WIP
    global BASE_EXK
    global BASE_EXB
    global HAS_GAMES
    global WORST_ERROR    
    global MOD_BASELINE
    calc_func, stlat_list, special_case_list, mod_list, stat_file_map, game_list, team_attrs, debug, debug2, debug3 = data
    debug_print("func start: {}".format(starttime), debug3, run_id)
    special_case_list = special_case_list or []
    mod_mode = True
    terms = {stat: StlatTerm(a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(parameters[:(-(len(special_case_list) + len(mod_list)) or None)])] * 3))}    
    mods = collections.defaultdict(lambda: {"opp": {}, "same": {}})
    for mod, a in zip(mod_list, zip(*[iter(parameters[-len(mod_list):])])):
        mods[mod.attr.lower()][mod.team.lower()][mod.stat.lower()] = a            
    special_cases = parameters[-len(special_case_list):] if special_case_list else []
    game_counter, fail_counter, pass_exact, pass_within_one, pass_within_two, pass_within_three, pass_within_four = 0, 0, 0, 0, 0, 0, 0
    quarter_fail = 100.0
    linear_fail = 100.0
    linear_error = 0.0
    love_rate, instinct_rate, ono_rate, wip_rate, exk_rate, exb_rate = 100.0, 100.0, 100.0, 100.0, 100.0, 100.0
    k9_max_err, k9_min_err = 0, 0
    paired_game_count = 0
    mod_fails = [0] * 6
    mod_games = [0] * 6
    multi_mod_fails, multi_mod_games, mvm_fails, mvm_games = 0, 0, 0, 0
    reject_solution, viability_unchecked = False, True
    all_vals = []
    win_loss = []    
    for season in range(11, 15):
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
        for day in range(1, 125):
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
            good_game_list = []
            for game in paired_games:
                paired_game_count += 1
                game_game_counter, game_fail_counter, game_away_val, game_home_val = calc_func(game, season_team_attrs, team_stat_data, pitcher_stat_data, pitchers, terms, special_cases, mods)
                if not is_cached and game_game_counter:
                    good_game_list.extend([game["home"], game["away"]])
                    HAS_GAMES[season] = True
                game_counter += game_game_counter
                fail_counter += game_fail_counter                
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
                            if name == "love":
                                mod_fails[0] += game_fail_counter
                                mod_games[0] += game_game_counter
                                awayMods += 1
                            if name == "base_instincts":
                                mod_fails[1] += game_fail_counter
                                mod_games[1] += game_game_counter
                                awayMods += 1
                            if name == "o_no":
                                mod_fails[2] += game_fail_counter
                                mod_games[2] += game_game_counter
                                awayMods += 1
                            if name == "walk_in_the_park":
                                mod_fails[3] += game_fail_counter
                                mod_games[3] += game_game_counter
                                awayMods += 1
                            if name == "extra_strike":
                                mod_fails[4] += game_fail_counter
                                mod_games[4] += game_game_counter
                                awayMods += 1
                            if name == "extra_base":
                                mod_fails[5] += game_fail_counter
                                mod_games[5] += game_game_counter
                                awayMods += 1
                            if awayMods > 1:
                                multi_mod_fails += game_fail_counter
                                multi_mod_games += game_game_counter
                        for name in lowerHomeAttrs:
                            if name == "love":
                                mod_fails[0] += game_fail_counter
                                mod_games[0] += game_game_counter
                                homeMods += 1
                            if name == "base_instincts":
                                mod_fails[1] += game_fail_counter
                                mod_games[1] += game_game_counter
                                homeMods += 1
                            if name == "o_no":
                                mod_fails[2] += game_fail_counter
                                mod_games[2] += game_game_counter
                                homeMods += 1
                            if name == "walk_in_the_park":
                                mod_fails[3] += game_fail_counter
                                mod_games[3] += game_game_counter
                                homeMods += 1
                            if name == "extra_strike":
                                mod_fails[4] += game_fail_counter
                                mod_games[4] += game_game_counter
                                homeMods += 1
                            if name == "extra_base":
                                mod_fails[5] += game_fail_counter
                                mod_games[5] += game_game_counter
                                homeMods += 1
                            if homeMods > 1:
                                multi_mod_fails += game_fail_counter
                                multi_mod_games += game_game_counter
                        if awayMods > 0 and homeMods > 0:
                            mvm_fails += game_fail_counter
                            mvm_games += game_game_counter
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
    else:
        fail_rate = 1.0
    if len(win_loss) == 0:
        TOTAL_GAME_COUNTER = game_counter if (game_counter > TOTAL_GAME_COUNTER) else TOTAL_GAME_COUNTER                
    # need to sort win_loss to match up with what will be the sorted set of vals
    # also need to only do this when solving MOFO        
    fail_points, linear_points = 10000000000.0, 10000000000.0    
    linear_fail = 90000000000.0
    if not reject_solution:
        if len(win_loss) > 0:            
            sorted_win_loss = [x for _,x in sorted(zip(all_vals, win_loss))]
            all_vals.sort()
            linear_error, max_linear_error, min_linear_error, max_error_value, max_error_ratio, errors, shape = calc_linear_unex_error(all_vals, sorted_win_loss, game_counter)
            linear_points = (linear_error + ((max_linear_error + max(max_error_ratio, max_error_value)) ** 2) + ((min_linear_error * 10000) ** 2) + (sum(shape) ** 2)) * 2.5
            if not mod_mode:
                fail_points = ((fail_rate * 1000.0) ** 2) * 2.5        
                linear_fail = fail_points + linear_points
            else:        
                love_rate = (mod_fails[0] / mod_games[0]) * 100.0
                instinct_rate = (mod_fails[1] / mod_games[1]) * 100.0
                ono_rate = (mod_fails[2] / mod_games[2]) * 100.0
                #currently no new data available for WIP or EXB
                #wip_rate = (mod_fails[3] / mod_games[3]) * 100.0
                exk_rate = (mod_fails[4] / mod_games[4]) * 100.0
                #exb_rate = (mod_fails[5] / mod_games[5]) * 100.0              
                #tolerance = (max(BEST_LOVE, BEST_INSTINCT, BEST_ONO, BEST_WIP, BEST_EXK, BEST_EXB) - min(BEST_LOVE, BEST_INSTINCT, BEST_ONO, BEST_WIP, BEST_EXK, BEST_EXB)) / 2.0                
                tolerance = min(BEST_LOVE, BEST_INSTINCT, BEST_ONO, BEST_EXK) / 10.0
                #if (love_rate <= BEST_LOVE) or (instinct_rate <= BEST_INSTINCT) or (ono_rate <= BEST_ONO) or (wip_rate <= BEST_WIP) or (exk_rate <= BEST_EXK) or (exb_rate <= BEST_EXB):
                if not MOD_BASELINE:
                    BASE_LOVE = love_rate
                    BASE_INSTINCT = instinct_rate
                    BASE_ONO = ono_rate
                    BASE_WIP = wip_rate
                    BASE_EXK = exk_rate
                    BASE_EXB = exb_rate                    
                    MOD_BASELINE = True                
                if (love_rate <= BASE_LOVE) and (instinct_rate <= BASE_INSTINCT) and (ono_rate <= BASE_ONO) and (exk_rate <= BASE_EXK):                    
                    if (love_rate <= BEST_LOVE) or (instinct_rate <= BEST_INSTINCT) or (ono_rate <= BEST_ONO) or (exk_rate <= BEST_EXK) or (fail_rate <= BEST_EXACT):                        
                        if (love_rate <= BEST_LOVE + tolerance) and (instinct_rate <= BEST_INSTINCT + tolerance) and (ono_rate <= BEST_ONO + tolerance) and (exk_rate <= BEST_EXK + tolerance) and (fail_rate <= BEST_EXACT):
                                #linear_fail = (love_rate + instinct_rate + ono_rate + wip_rate + exk_rate + exb_rate) / 6.0
                            fail_points = ((fail_rate * 1000.0) ** 2) * 2.5
                            linear_fail = fail_points + linear_points
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
        if len(win_loss) > 0:
            BEST_FAIL_RATE = fail_rate
            BEST_LINEAR_ERROR = linear_error
            if mod_mode:                
                debug_print("last best Love fail rate {:.4f}%".format(BEST_LOVE), debug, run_id)
                BEST_LOVE = love_rate if (love_rate < BEST_LOVE) else BEST_LOVE
                BEST_INSTINCT = instinct_rate if (instinct_rate < BEST_INSTINCT) else BEST_INSTINCT
                BEST_ONO = ono_rate if (ono_rate < BEST_ONO) else BEST_ONO
                BEST_WIP = wip_rate if (wip_rate < BEST_WIP) else BEST_WIP
                BEST_EXK = exk_rate if (exk_rate < BEST_EXK) else BEST_EXK
                BEST_EXB = exb_rate if (exb_rate < BEST_EXB) else BEST_EXB
        debug_print("-"*20, debug, run_id)
        if type(stlat_list) == dict:
            terms_output = "\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(parameters[:(-(len(special_cases) + len(mod_list)) or None)])] * 3)))
            mods_output = "\n".join("{},{},{},{}".format(stat.attr, stat.team, stat.stat, a) for stat, a in zip(mod_list, parameters[-len(mod_list):]))
            debug_print("Best so far - fail rate {:.4f}%\n".format(fail_rate * 100.0) + terms_output + "\n" + mods_output, debug, run_id)
            debug_print("{} games, {} paired games".format(game_counter, paired_game_count), debug, run_id)
            debug_print("{:.4f}% Love fail rate, Best {:.4f}%".format(love_rate, BEST_LOVE), debug, run_id)
            debug_print("{:.4f}% Base Instincts fail rate, Best {:.4f}%".format(instinct_rate, BEST_INSTINCT), debug, run_id)
            debug_print("{:.4f}% O No fail rate, Best {:.4f}%".format(ono_rate, BEST_ONO), debug, run_id)
            #debug_print("{:.4f}% Walk in the Park fail rate, Best {:.4f}%".format(wip_rate, BEST_WIP), debug, run_id)
            debug_print("{:.4f}% Extra Strike fail rate, Best {:.4f}%".format(exk_rate, BEST_EXK), debug, run_id)            
            if multi_mod_games > 0:
                debug_print("{:.4f}% multimod fail rate, {} games".format((multi_mod_fails / multi_mod_games) * 100.0, multi_mod_games), debug, run_id)            
            if mvm_games > 0:
                debug_print("{:.4f}% mod vs mod fail rate, {} games".format((mvm_fails / mvm_games) * 100.0, mvm_games), debug, run_id)
            #debug_print("{:.4f}% Extra Base fail rate, Best {:.4f}%".format(exb_rate, BEST_EXB), debug, run_id)                        
            debug_print("Best so far - fail rate {:.4f}%, linear error {:.4f}".format(fail_rate * 100.0, linear_error), debug, run_id)
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
            debug_print("Fail error points = {:.4f}, Linearity error points = {:.4f}, total = {:.4f}".format(fail_points, linear_points, linear_fail), debug, run_id)
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
            debug_print("Best so far - {:.2f}, iteration # {}, fail rate {:.2f}, linear error {:.4f}".format(BEST_RESULT, CURRENT_ITERATION, (BEST_FAIL_RATE * 100.0), BEST_LINEAR_ERROR), debug, datetime.datetime.now())
        else:
            debug_print("Best so far - {:.4f}, iteration # {}".format(BEST_RESULT, CURRENT_ITERATION), debug, datetime.datetime.now())
    CURRENT_ITERATION += 1   
    current_runtime = time.process_time()
    if ((current_runtime - LAST_CHECKTIME) >= 600):
        #debug_print("2 minute power nap, been working for {:.2f} minutes".format((current_runtime - LAST_CHECKTIME) / 60.0), debug, datetime.datetime.now())
        time.sleep(60)  
        #debug_print("Waking back up", debug, datetime.datetime.now())
        LAST_CHECKTIME = time.process_time()
    debug_print("run fail rate {:.4f}%".format(fail_rate * 100.0), debug2, run_id)
    endtime = datetime.datetime.now()
    debug_print("func end: {}, run time {}".format(endtime, endtime-starttime), debug3, run_id)
    return linear_fail
