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

BEST_RESULT = 1.0

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


def get_attrs_from_paired_game(season_team_attrs, games):
    attrs = set()
    for side in ("home", "away"):
        game = games[side]
        team_attrs = season_team_attrs.get(game.get("team_name"), [])
        for attr in team_attrs:
            if (attr == "TRAVELING" and side != "away") or (attr == "AFFINITY_FOR_CROWS" and int(game["weather"]) != BIRD_WEATHER):
                continue
            attrs.add(attr)
    return attrs


def get_attrs_from_paired_games(season_team_attrs, paired_games):
    attrs = set()
    for games in paired_games:
        attrs.update(get_attrs_from_paired_game(season_team_attrs, games))
    return attrs


def debug_print(s, debug, run_id):
    if debug:
        print("{} - {}".format(run_id, s))


def get_minimize_func(calc_func):
    def minimize_func(parameters, *data):
        run_id = uuid.uuid4()
        starttime = datetime.datetime.now()
        global BEST_RESULT
        stlat_list, stat_file_map, game_list, team_attrs, mod, debug, debug2, debug3 = data
        debug_print("func start: {}".format(starttime), debug3, run_id)
        terms = {stat: StlatTerm(a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(parameters)] * 3))}
        game_counter, fail_counter = 0, 0
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
                    game_game_counter, game_fail_counter = calc_func(game, mod, season_team_attrs, team_stat_data, pitcher_stat_data, pitchers, terms)
                    game_counter += game_game_counter
                    fail_counter += game_fail_counter
            season_end = datetime.datetime.now()
            debug_print("season {} end: {}, run time {}, average day run {}".format(season, season_end, season_end-season_start, (season_end-season_start)/season_days), debug3, run_id)
        fail_rate = fail_counter / game_counter
        if fail_rate < BEST_RESULT:
            BEST_RESULT = fail_rate
            debug_print("-"*20, debug, run_id)
            debug_print("Best so far - fail rate {:.2f}%\n".format(fail_rate * 100.0) + "\n".join("{},{},{},{}".format(stat, a, b, c) for stat, (a, b, c) in zip(stlat_list, zip(*[iter(parameters)] * 3))), debug, run_id)
            debug_print("-" * 20, debug, run_id)
        debug_print("run fail rate {:.2f}%".format(fail_rate * 100.0), debug2, run_id)
        endtime = datetime.datetime.now()
        debug_print("func end: {}, run time {}".format(endtime, endtime-starttime), debug3, run_id)
        return fail_rate
    return minimize_func
