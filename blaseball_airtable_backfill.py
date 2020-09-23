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

RBI_CACHE = {}

AirtableGame = namedtuple("AirtableGame", ["airtable_id", "pitcher_id", "game_id", "season", "day"])

def get_missing_games(airtable, column, column_empty_func):
    results = airtable.search(column, '')
    return [AirtableGame(result['id'], result['fields']['Pitcher ID'], result['fields']['Game ID'], result['fields']['Season'], result['fields']['Day']) for result in results if column_empty_func(result)]


def get_strikout_count(pitcher_id, game_id):
    game_results = requests.get("https://api.blaseball-reference.com/v1/events?gameId={}&pitcherId={}".format(game_id, pitcher_id)).json()
    if not game_results["count"]:
        return -1
    return len([res for res in game_results["results"] if res["event_type"] == "STRIKEOUT"])


def pitcher_team_earned_runs_shutout(pitcher_id, game_id):
    if (pitcher_id, game_id) in RBI_CACHE:
        return RBI_CACHE[(pitcher_id, game_id)]
    game_request = requests.get("https://api.blaseball-reference.com/v1/events?gameId={}".format(game_id))
    game_results = game_request.json()["results"]
    if not game_results:
        RBI_CACHE[(pitcher_id, game_id)] = (None, None)
        return None, None
    pitchers = set([event['pitcher_id'] for event in game_results])
    if pitcher_id not in pitchers or len(pitchers) != 2:
        RBI_CACHE[(pitcher_id, game_id)] = (None, None)
        return None, None
    pitcher_team_rbi = sum([event["runs_batted_in"] for event in game_results if event['pitcher_id'] != pitcher_id])
    other_team_rbi = sum([event["runs_batted_in"] for event in game_results if event['pitcher_id'] == pitcher_id])
    RBI_CACHE[(pitcher_id, game_id)] = (pitcher_team_rbi, not other_team_rbi)
    # Get other side and cache it while we're here
    other_pitcher_id = (pitchers - {pitcher_id}).pop()
    RBI_CACHE[(other_pitcher_id, game_id)] = (other_team_rbi, not pitcher_team_rbi)
    return (pitcher_team_rbi, not other_team_rbi)


def update_column(airtable, airtable_id, column, result):
    record = airtable.update(airtable_id, {column: result})


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--strikeouts', help="backfill strikeouts", action='store_true')
    parser.add_argument('--shutouts', help="backfill strikeouts", action='store_true')
    parser.add_argument('--earnedruns', help="backfill earned runs", action='store_true')
    args = parser.parse_args()
    if not args.strikeouts and not args.shutouts and not args.earnedruns:
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
                        lambda pid, gid: pitcher_team_earned_runs_shutout(pid, gid)[1], lambda is_shutout: is_shutout is not None, transform_result=lambda res: 1 if res else 0)
    if args.earnedruns:
        handle_backfill(airtable, "Pitcher Team Earned Runs", lambda result: "Pitcher ID" in result['fields'],
                        lambda pid, gid: pitcher_team_earned_runs_shutout(pid, gid)[0], lambda result: result is not None)


if __name__ == "__main__":
    main()
