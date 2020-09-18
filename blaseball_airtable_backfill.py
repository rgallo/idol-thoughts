from __future__ import print_function
from __future__ import division

import sys
import time
from collections import namedtuple
import requests
from airtable import Airtable
import argparse
import os
from dotenv import load_dotenv


AirtableGame = namedtuple("AirtableGame", ["airtable_id", "pitcher_id", "game_id", "season", "day"])

def get_missing_games(airtable, column, column_empty_func):
    results = airtable.search(column, '')
    return [AirtableGame(result['id'], result['fields']['Pitcher ID'], result['fields']['Game ID'], result['fields']['Season'], result['fields']['Day']) for result in results if column_empty_func(result)]


def get_strikout_count(pitcher_id, game_id):
    game_results = requests.get("https://api.blaseball-reference.com/v1/events?gameId={}&pitcherId={}".format(game_id, pitcher_id)).json()
    if not game_results["count"]:
        return -1
    return len([res for res in game_results["results"] if res["event_type"] == "STRIKEOUT"])


def is_game_shutout_for_pitcher(pitcher_id, game_id):
    game_request = requests.get("https://api.blaseball-reference.com/v1/events?gameId={}&sortBy=event_index&sortDirection=desc".format(game_id))
    game_results = game_request.json()["results"]
    if not game_results:
        return None
    last_game_event = game_results[0]
    pitcher_is_home = (pitcher_id == last_game_event["pitcher_id"] and last_game_event["top_of_inning"]) or (pitcher_id != last_game_event["pitcher_id"] and not last_game_event["top_of_inning"])
    return (pitcher_is_home and not bool(last_game_event["away_score"])) or (not pitcher_is_home and not bool(last_game_event["home_score"]))


def did_pitcher_win(pitcher_id, game_id):
    game_request = requests.get("https://api.blaseball-reference.com/v1/events?gameId={}&sortBy=event_index&sortDirection=desc".format(game_id))
    game_results = game_request.json()["results"]
    if not game_results:
        return None
    last_game_event = game_results[0]
    away_score, home_score = last_game_event["away_score"], last_game_event["home_score"]
    pitcher_is_home = (pitcher_id == last_game_event["pitcher_id"] and last_game_event["top_of_inning"]) or (pitcher_id != last_game_event["pitcher_id"] and not last_game_event["top_of_inning"])
    return (pitcher_is_home and home_score > away_score) or (not pitcher_is_home and away_score > home_score)


def update_column(airtable, airtable_id, column, result):
    record = airtable.update(airtable_id, {column: result})


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--strikeouts', help="backfill strikeouts", action='store_true')
    parser.add_argument('--shutouts', help="backfill strikeouts", action='store_true')
    parser.add_argument('--wins', help="backfill wins", action='store_true')
    args = parser.parse_args()
    if not args.strikeouts and not args.shutouts and not args.wins:
        print("Nothing to do, that was easy")
        parser.print_help()
        sys.exit(-1)
    return args


def handle_backfill(airtable, column, column_empty_func, calc_func, is_valid_func, transform_result=lambda x: x):
    games = get_missing_games(airtable, column, column_empty_func)
    for game in games:
        result = calc_func(game.pitcher_id, game.game_id)
        if is_valid_func(result):
            update_column(airtable, game.airtable_id, column, transform_result(result))
        else:
            print("{} - couldn't find S{}D{}, pitcher_id: {}, game_id: {}".format(column, game.season, game.day, game.pitcher_id, game.game_id))
        time.sleep(2)


def main():
    args = handle_args()
    load_dotenv()
    airtable = Airtable(os.getenv("AIRTABLE_BASE_KEY"), os.getenv("AIRTABLE_TABLE_NAME"), os.getenv("AIRTABLE_API_KEY"))
    if args.strikeouts:
        handle_backfill(airtable, "Strikeouts", lambda result: "Pitcher ID" in result['fields'],
                        get_strikout_count, lambda count: count >= 0)
    if args.shutouts:
        handle_backfill(airtable, "Shutouts", lambda result: "Pitcher ID" in result['fields'] and ("Shutouts" not in result['fields'] or result['fields']['Shutouts'] not in (0, 1)),
                        is_game_shutout_for_pitcher, lambda is_shutout: is_shutout is not None, transform_result=lambda res: 1 if res else 0)
    if args.wins:
        handle_backfill(airtable, "Win", lambda result: "Pitcher ID" in result['fields'] and ("Win" not in result['fields'] or result['fields']['Win'] not in (0, 1)),
                        did_pitcher_win, lambda is_win: is_win is not None, transform_result=lambda res: 1 if res else 0)


if __name__ == "__main__":
    main()
