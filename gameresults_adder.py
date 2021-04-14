import csv
import sys
import os
import argparse
import time

import requests
from blaseball_mike.models import SimulationData

COLUMNS = ["pitcher_id", "team_id", "game_id", "season", "day", "weather", "opposing_team_rbi", "strikeouts",
           "innings_pitched", "pitcher_is_home", "strike_count", "ball_count", "base_count", "webodds"]


def get_games(season, day):
    games, gameids = [], []
    resp = requests.get("https://api.sibr.dev/chronicler/v1/games?season={}&day={}".format(season-1, day-1)).json()
    data = resp["data"]
    for game in data:
        gameids.append(game["gameId"])
        game_data = game["data"]
        games.append({
            "pitcher_id": game_data["awayPitcher"],
            "team_id": game_data["awayTeam"],
            "game_id": game_data["id"],
            "season": game_data["season"] + 1,
            "day": game_data["day"] + 1,
            "weather": game_data["weather"],
            "pitcher_is_home": False,
            "strike_count": game_data["awayStrikes"],
            "ball_count": game_data["awayBalls"],
            "base_count": game_data["awayBases"],
            "webodds": game_data["awayOdds"]
        })
        games.append({
            "pitcher_id": game_data["homePitcher"],
            "team_id": game_data["homeTeam"],
            "game_id": game_data["id"],
            "season": game_data["season"] + 1,
            "day": game_data["day"] + 1,
            "weather": game_data["weather"],
            "pitcher_is_home": True,
            "strike_count": game_data["homeStrikes"],
            "ball_count": game_data["homeBalls"],
            "base_count": game_data["homeBases"],
            "webodds": game_data["homeOdds"]
        })
    return games, gameids


def check_file_for_data(output, season, day):
    with open(output) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    for row in filedata:
        if int(row["season"]) == season and int(row["day"]) == day:
            return True
    return False


def write_headers(output):
    with open(output, "w") as f:
        f.write("{}\n".format(",".join(COLUMNS)))


def get_game_stats(game_id):
    time.sleep(2)
    game_request = requests.get("https://api.blaseball-reference.com/v1/events?gameId={}".format(game_id))
    game_results = game_request.json().get("results")
    pitchers = set([event['pitcher_id'] for event in game_results])
    if len(pitchers) != 2:
        return None
    result = {
        True: {"opposing_team_rbi": 0.0, "strikeouts": 0.0, "innings_pitched": set()},
        False: {"opposing_team_rbi": 0.0, "strikeouts": 0.0, "innings_pitched": set()},
    }
    for event in game_results:
        event_result = result[True] if event["top_of_inning"] else result[False]
        event_result["opposing_team_rbi"] += max(float(event["runs_batted_in"]), 0.0)
        event_result["strikeouts"] += 1 if event["event_type"] == "STRIKEOUT" else 0
        event_result["innings_pitched"].add(event["inning"])
    result[True]["innings_pitched"] = len(result[True]["innings_pitched"])
    result[False]["innings_pitched"] = len(result[False]["innings_pitched"])
    return result


def write_rows(output, games, game_stats):
    with open(output, "a") as f:
        for game in games:
            game_id = game["game_id"]
            if not game_stats.get(game_id):
                continue
            game.update(game_stats[game_id][game["pitcher_is_home"]])
            f.write("\n{}".format(",".join('"{}"'.format(game[col]) for col in COLUMNS)))


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', help="path to file")
    args = parser.parse_args()
    return args


def main():
    args = handle_args()
    sim = SimulationData.load()
    season, day = sim.season, sim.day
    if day < 1:
        sys.exit("Too early")
    if not os.path.exists(args.output):
        write_headers(args.output)
    if check_file_for_data(args.output, season, day):
        sys.exit("Data already in file")
    games, gameids = get_games(season, day)
    game_stats = {gameid: get_game_stats(gameid) for gameid in gameids}
    write_rows(args.output, games, game_stats)


if __name__ == "__main__":
    main()
