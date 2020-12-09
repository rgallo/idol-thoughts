import collections
import csv
import datetime
import os
import re
import uuid
from glob import glob

from helpers import StlatTerm, get_weather_idx
from idolthoughts import load_stat_data

STAT_CACHE = {}
GAME_CACHE = {}

BEST_RESULT = 10000000.0

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


def get_schedule_from_paired_games(paired_games):
    return [{
        "homeTeamName": game["home"]["team_name"],
        "awayTeamName": game["away"]["team_name"],
        "weather": int(game["home"]["weather"]),
    } for game in paired_games]


def should_regen(day_mods):
    return any([d in day_mods for d in FORCE_REGEN])


def get_attrs_from_game(season_team_attrs, game, side):
    attrs = set()
    team_attrs = season_team_attrs.get(game.get("team_name"), [])
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
    high_val, low_val, high_ratio, low_ratio, error, max_error, min_error = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0
    high_val = vals[idx]
    while (high_val < 0.5 and idx < len(vals)):        
        wins += wins_losses[idx]
        idx += 1
        high_val = vals[idx]
    while (idx < len(vals)):        
        wins += wins_losses[idx]
        high_val = vals[idx]        
        high_ratio = float(wins) / float(games)
        error += (high_ratio - high_val) ** 2
        max_error = max(high_ratio, high_val) - min(high_ratio, high_val) if max(high_ratio, high_val) - min(high_ratio, high_val) > max_error else max_error
        min_error = max(high_ratio, high_val) - min(high_ratio, high_val) if max(high_ratio, high_val) - min(high_ratio, high_val) < min_error else min_error            
        low_ratio = 1.0 - high_ratio
        low_val = 1.0 - high_val
        error += (low_ratio - low_val) ** 2        
        max_error = max(low_ratio, low_val) - min(low_ratio, low_val) if max(low_ratio, low_val) - min(low_ratio, low_val) > max_error else max_error
        min_error = max(low_ratio, low_val) - min(low_ratio, low_val) if max(low_ratio, low_val) - min(low_ratio, low_val) < min_error else min_error            
        idx += 1
    return error, max_error, min_error

def minimize_func(parameters, *data):
    run_id = uuid.uuid4()
    starttime = datetime.datetime.now()
    global BEST_RESULT
    calc_func, stlat_list, special_case_list, mod_list, stat_file_map, game_list, team_attrs, debug, debug2, debug3 = data
    debug_print("func start: {}".format(starttime), debug3, run_id)
    special_case_list = special_case_list or []
    if type(stlat_list) == dict:  # mod mode
        terms = stlat_list
        mods = collections.defaultdict(lambda: {"opp": {}, "same": {}})
        for mod, (a, b, c) in zip(mod_list, zip(*[iter(parameters)] * 3)):
            mods[mod.attr.lower()][mod.team.lower()][mod.stat.lower()] = StlatTerm(a, b, c)
    else:  # base mode
        terms = {stat: StlatTerm(a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(parameters[:(-len(special_case_list) or None)])] * 3))}
        mods = {}
    special_cases = parameters[-len(special_case_list):] if special_case_list else []
    game_counter, fail_counter = 0, 0
    all_vals = []
    win_loss = []
    for season in range(3, 12):
        season_start = datetime.datetime.now()
        debug_print("season {} start: {}".format(season, season_start), debug3, run_id)
        pitchers, team_stat_data, pitcher_stat_data, last_stat_filename = None, None, None, None
        season_team_attrs = team_attrs.get(str(season), {})
        season_days = 0
        for day in range(1, 125):
            cached_games = GAME_CACHE.get((season, day))
            if cached_games:
                games = cached_games
            else:
                games = [row for row in game_list if row["season"] == str(season) and row["day"] == str(day)]
                if not games:
                    continue
                GAME_CACHE[(season, day)] = games
            season_days += 1
            paired_games = pair_games(games)
            schedule = get_schedule_from_paired_games(paired_games)
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
            for game in paired_games:
                game_game_counter, game_fail_counter, game_away_val, game_home_val = calc_func(game, season_team_attrs, team_stat_data, pitcher_stat_data, pitchers, terms, special_cases, mods)
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
        season_end = datetime.datetime.now()
        debug_print("season {} end: {}, run time {}, average day run {}".format(season, season_end, season_end-season_start, (season_end-season_start)/season_days), debug3, run_id)
    fail_rate = fail_counter / game_counter
    # need to sort win_loss to match up with what will be the sorted set of vals
    # also need to only do this when solving MOFO
    if len(win_loss) > 0:
        sorted_win_loss = [x for _,x in sorted(zip(all_vals, win_loss))]
        all_vals.sort()
        linear_error, max_linear_error, min_linear_error = calc_linear_unex_error(all_vals, sorted_win_loss, game_counter)    
        linear_fail = (fail_rate * 100.0) + linear_error
    else:
        linear_fail = fail_rate
    if linear_fail < BEST_RESULT:
        BEST_RESULT = linear_fail
        debug_print("-"*20, debug, run_id)
        if type(stlat_list) == dict:
            mods_output = "\n".join("{},{},{},{},{},{}".format(stat.attr, stat.team, stat.stat, a, b, c) for stat, (a, b, c) in zip(mod_list, zip(*[iter(parameters)] * 3)))
            debug_print("Best so far - fail rate {:.4f}%\n".format(fail_rate * 100.0) + mods_output, debug, run_id)
        else:
            terms_output = "\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(parameters[:(-len(special_cases) or None)])] * 3)))
            special_case_output = "\n" + "\n".join("{},{}".format(name, val) for name, val in zip(special_case_list, special_cases)) if special_case_list else ""
            if len(win_loss) > 0:
                debug_print("Best so far - fail rate {:.4f}%, linear error {:.4f}, {} games\n".format(fail_rate * 100.0, linear_error, game_counter) + terms_output + special_case_output, debug, run_id)
                debug_print("Max linear error {:.4f}%, Min linear error {:.4f}%\n".format(max_linear_error * 100.0, min_linear_error * 100.0), debug, run_id)
            else:
                debug_print("Best so far - fail rate {:.4f}%\n".format(fail_rate * 100.0) + terms_output + special_case_output, debug, run_id)
        debug_print("-" * 20, debug, run_id)
    debug_print("run fail rate {:.4f}%".format(fail_rate * 100.0), debug2, run_id)
    endtime = datetime.datetime.now()
    debug_print("func end: {}, run time {}".format(endtime, endtime-starttime), debug3, run_id)
    return linear_fail
