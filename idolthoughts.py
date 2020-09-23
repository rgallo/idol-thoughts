from __future__ import print_function
from __future__ import division

import requests
import json
import collections
import csv
from functools import reduce
from collections import namedtuple
import sys
import time
import os
import traceback

from airtable import Airtable
import argparse
import blaseball_stat_csv
from dotenv import load_dotenv
from discord_webhook import DiscordWebhook, DiscordEmbed
import math


MatchupData = namedtuple("MatchupData", ["pitchername", "pitcherid", "pitcherteam", "gameid", "so9", "era", "defemoji", "vsteam", 
                                         "offemoji", "defoff", "battingstars", "bng", "stardata", "ballcount", "strikecount",
                                         "pitcherteamnickname", "vsteamnickname", "winodds"])

MatchupPair = namedtuple("MatchupPair", ["awayMatchupData", "homeMatchupData"])

StarData = namedtuple("StarData", ["pitchingstars", "maxbatstars", "meanbatstars", "maxdefstars", "meandefstars", 
                                   "maxrunstars", "meanrunstars"])

PITCHING_STLATS = ["overpowerment", "ruthlessness", "unthwackability", "shakespearianism", "coldness"]
BATTING_STLATS = ["patheticism", "thwackability", "musclitude"]
DEFENSE_STLATS = ["omniscience", "tenaciousness", "watchfulness", "chasiness"]
BASERUNNING_STLATS = ["baseThirst"]

StlatData = namedtuple("StlatData", ["overpowerment", "ruthlessness", "unthwackability", "shakespearianism", "coldness",  # Pitching
                                     "minpatheticism", "meanthwackability", "meanmusclitude",  # Batting
                                     "meanomniscience", "meantenaciousness", "meanwatchfulness", "meanchasiness",  # Defense
                                     "meanbaseThirst"])  # Baserunning

BR_URL = "https://blaseball-reference.nyc3.digitaloceanspaces.com/public/json-data/pitching/{}/summary.json"

PLAYERNAME_SUBS = {
    "wyatt-owens": "emmett-owens",
    "peanut-bong": "dan-bong",
    "sexton-wheerer": "sexton-wheeler"
}

BNG_FLOOR = 100.0
BNG_CEILING = 994975
LAST_SEASON_STAT_CUTOFF = 11
DISCORD_SPLIT_LIMIT = 1900
DISCORD_RESULT_PER_BATCH = 5


def send_discord_message(title, message):
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL").split(";")
    webhook = DiscordWebhook(url=discord_webhook_url)
    webhook.add_embed(DiscordEmbed(title=title, description=message))
    return webhook.execute()


def get_formatted_so9(matchup_data, so9_pitchers):
    return "__{:.2f} SO9__".format(matchup_data.so9) if matchup_data.pitchername in so9_pitchers else "{:.2f} SO9".format(matchup_data.so9)


def get_formatted_bng(matchup_data, bng_pitchers):
    formatted_bng = "{:.2f}".format(matchup_data.bng) if matchup_data.bng <= 1000000 else "{:.2e}".format(matchup_data.bng)
    return "__{} BNG__".format(formatted_bng) if matchup_data.pitchername in bng_pitchers else "{} BNG".format(formatted_bng)

def get_formatted_odds(away_odds, home_odds):
    formatted_away_odds = "{:.2f}%".format(away_odds*100.0)
    formatted_home_odds = "{:.2f}%".format(home_odds*100.0)
    if away_odds > home_odds:
        formatted_away_odds = "__{}__".format(formatted_away_odds)
    elif home_odds > away_odds:
        formatted_home_odds = "__{}__".format(formatted_home_odds)
    return formatted_away_odds, formatted_home_odds


def get_output_line_from_matchup(matchup_data, odds, so9_pitchers, bng_pitchers):
    so9 = get_formatted_so9(matchup_data, so9_pitchers)
    bng = get_formatted_bng(matchup_data, bng_pitchers)
    formatstr = "{} **[{}](https://blaseball-reference.com/players/{}), {}** ({}, {:.2f} ERA, {}), ({:.2f} OppBat★, {:.2f} OppMaxBat), {:.2f} D/O^2, {}"
    return formatstr.format(chr(int(matchup_data.defemoji, 16)), matchup_data.pitchername, get_player_slug(matchup_data.pitchername),
                            matchup_data.pitcherteamnickname, so9, matchup_data.era, bng, matchup_data.battingstars, 
                            matchup_data.stardata.maxbatstars, matchup_data.defoff, odds)


def sort_result_pairs(matchup_pairs, so9_pitchers, bng_pitchers):
    sorted_results = sorted(matchup_pairs, key=lambda res: max(res.awayMatchupData.so9, res.homeMatchupData.so9), reverse=True)
    if so9_pitchers and bng_pitchers:
        grouped_results = [res for res in sorted_results if (res.awayMatchupData.pitchername in so9_pitchers and res.awayMatchupData.pitchername in bng_pitchers) or (res.homeMatchupData.pitchername in so9_pitchers and res.homeMatchupData.pitchername in bng_pitchers)]
        grouped_results.extend([res for res in sorted_results if (res.awayMatchupData.pitchername in so9_pitchers and res.awayMatchupData.pitchername not in bng_pitchers) or (res.homeMatchupData.pitchername in so9_pitchers and res.homeMatchupData.pitchername not in bng_pitchers)])
        grouped_results.extend([res for res in sorted_results if (res.awayMatchupData.pitchername not in so9_pitchers and res.awayMatchupData.pitchername in bng_pitchers) or (res.homeMatchupData.pitchername not in so9_pitchers and res.homeMatchupData.pitchername in bng_pitchers)])
        grouped_results.extend([res for res in sorted_results if (res.awayMatchupData.pitchername not in so9_pitchers and res.awayMatchupData.pitchername not in bng_pitchers) or (res.homeMatchupData.pitchername not in so9_pitchers and res.homeMatchupData.pitchername not in bng_pitchers)])
        sorted_results = grouped_results
    return sorted_results


def send_matchup_data_to_discord_webhook(day, matchup_pairs, so9_pitchers, bng_pitchers, shame_results):
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL").split(";")
    sorted_pairs = sort_result_pairs(matchup_pairs, so9_pitchers, bng_pitchers)
    batches = math.ceil(len(matchup_pairs) / DISCORD_RESULT_PER_BATCH)
    webhooks = [DiscordWebhook(url=discord_webhook_url, content="__**Day {}**__{}".format(day, " (cont.)" if batch else "")) for batch in range(batches)]
    for idx, result in enumerate(matchup_pairs):
        awayMatchupData, homeMatchupData = result.awayMatchupData, result.homeMatchupData
        awayOdds, homeOdds = get_formatted_odds(awayMatchupData.winodds, homeMatchupData.winodds)
        description = "{}\n--- @ ---\n{}".format(get_output_line_from_matchup(awayMatchupData, awayOdds, so9_pitchers, bng_pitchers),
                                        get_output_line_from_matchup(homeMatchupData, homeOdds, so9_pitchers, bng_pitchers))
        for matchup_data in (awayMatchupData, homeMatchupData):
            if matchup_data.pitcherteam in shame_results:
                description += "\n:rotating_light::rotating_light: *{} Shame: -{}* :rotating_light::rotating_light:".format(matchup_data.pitcherteamnickname, shame_results[matchup_data.pitcherteam])
        embed = DiscordEmbed(description=description)
        webhooks[idx // DISCORD_RESULT_PER_BATCH].add_embed(embed)
    return [webhook.execute() for webhook in webhooks]


def geomean(numbers):
    correction = .001 if 0.0 in numbers else 0.0
    return (reduce(lambda x, y: x*y, [(n + correction) for n in numbers])**(1.0/len(numbers))) - correction


def get_stream_snapshot():
    snapshot = None
    response = requests.get("https://www.blaseball.com/events/streamData", stream=True)
    for line in response.iter_lines():
        snapshot = line
        break
    return json.loads(snapshot.decode("utf-8")[6:])


def get_def_off_ratio(pitcher, defenseteamname, offenseteamname, team_stat_data, pitcher_stat_data):
    pitchingstars = pitcher_stat_data[pitcher]["pitchingStars"]
    meandefstars = geomean(team_stat_data[defenseteamname]["defenseStars"])
    meanbatstars = geomean(team_stat_data[offenseteamname]["battingStars"])
    meanrunstars = geomean(team_stat_data[offenseteamname]["baserunningStars"])
    return (pitchingstars+meandefstars)/((meanbatstars+meanrunstars) ** 2)


def load_stat_data(filepath):
    filedata = {}
    with open(filepath) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    pitcherstardata = collections.defaultdict(lambda: {})
    teamstatdata = collections.defaultdict(lambda: collections.defaultdict(lambda: []))
    for row in filedata:
        if row["position"] == "rotation":
            for key in (PITCHING_STLATS + ["pitchingStars"]):
                pitcherstardata[row["name"]][key] = float(row[key])
        elif row["position"] == "lineup":
            if "SHELLED" not in row["permAttr"]:
                for key in (BATTING_STLATS + BASERUNNING_STLATS + ["battingStars", "baserunningStars"]):
                    teamstatdata[row["team"]][key].append(float(row[key]))
            for key in (DEFENSE_STLATS + ["defenseStars"]):
                    teamstatdata[row["team"]][key].append(float(row[key]))
    return teamstatdata, pitcherstardata

def get_player_slug(playername):
    playerslug = playername.lower().replace(" ", "-")
    playerslug = PLAYERNAME_SUBS.get(playerslug, playerslug)
    return playerslug


def get_pitcher_stats(pitchername, season):
    playerslug = get_player_slug(pitchername)
    requrl = BR_URL.format(playerslug)
    try:
        time.sleep(3)
        response = requests.get(requrl)
        resjson = response.json()
        return resjson["seasons"][str(season)]
    except:
        print("Error on {}, {}".format(pitchername, requrl))
        return {}


def calc_bng(stlatdata):
    factor = 13.30944112
    pitching = ((1.096087859+stlatdata.overpowerment) ** 18.26327946) * ((0.971743351+stlatdata.ruthlessness) ** 26.77231877) * 16.57479715 * (1.099229426 + stlatdata.unthwackability) * (0.948936632 + stlatdata.shakespearianism) * (0.90582522 + stlatdata.coldness)
    batting = ((3 - stlatdata.minpatheticism) ** 25.17059875) * (1+stlatdata.meanthwackability) * (1+stlatdata.meanmusclitude)
    defense = 25.85703303 * stlatdata.meanomniscience * stlatdata.meantenaciousness * stlatdata.meanwatchfulness * stlatdata.meanchasiness
    blaserunning = stlatdata.meanbaseThirst
    return factor * ((pitching / batting) + (defense / blaserunning))


def calc_star_max_mean_stats(pitcher, defenseteamname, offenseteamname, team_stat_data, pitcher_stat_data):
    pitchingstars = pitcher_stat_data[pitcher]["pitchingStars"]
    maxbatstars = max(team_stat_data[offenseteamname]["battingStars"])
    meanbatstars = geomean(team_stat_data[offenseteamname]["battingStars"])
    maxdefstars = max(team_stat_data[defenseteamname]["defenseStars"])
    meandefstars = geomean(team_stat_data[defenseteamname]["defenseStars"])
    maxrunstars = max(team_stat_data[offenseteamname]["baserunningStars"])
    meanrunstars = geomean(team_stat_data[offenseteamname]["baserunningStars"])
    return StarData(pitchingstars, maxbatstars, meanbatstars, maxdefstars, meandefstars, maxrunstars, meanrunstars)


def calc_stlat_stats(pitcher, defenseteamname, offenseteamname, team_stat_data, pitcher_stat_data):
    ["overpowerment", "ruthlessness", "unthwackability", "shakespearianism", "coldness",  # Pitching
                                     "minpatheticism", "meanthwackability", "meanmusclitude",  # Batting
                                     "meanomniscience", "meantenaciousness", "meanwatchfulness", "meanchasiness",  # Defense
                                     "meanbaseThirst"]  # Baserunning
    stlatdata = [pitcher_stat_data[pitcher][stlat] for stlat in ["overpowerment", "ruthlessness", "unthwackability", "shakespearianism", "coldness"]]
    stlatdata.extend((min(team_stat_data[offenseteamname]["patheticism"]), geomean(team_stat_data[offenseteamname]["thwackability"]), 
                     geomean(team_stat_data[offenseteamname]["musclitude"])))
    stlatdata.extend((geomean(team_stat_data[defenseteamname]["omniscience"]), geomean(team_stat_data[defenseteamname]["tenaciousness"]),
                      geomean(team_stat_data[defenseteamname]["watchfulness"]), geomean(team_stat_data[defenseteamname]["chasiness"])))
    stlatdata.append(geomean(team_stat_data[offenseteamname]["baseThirst"]))
    return StlatData(*stlatdata)


def get_dict_from_matchupdata(matchup, season_number, day):
    return {"Pitcher Name": matchup.pitchername, "Season": season_number, "Day": day,
            "SO9": matchup.so9, "ERA": matchup.era, "Opposing Team": matchup.vsteam,
            "D/O": matchup.defoff, "Batting Stars": matchup.battingstars,
            "Game ID": matchup.gameid, "Pitcher ID": matchup.pitcherid,
            "Pitching Stars": matchup.stardata.pitchingstars, "Max Batting": matchup.stardata.maxbatstars,
            "Mean Batting": matchup.stardata.meanbatstars, "Max Defense": matchup.stardata.maxdefstars, 
            "Mean Defense": matchup.stardata.meandefstars, "Max Baserunning": matchup.stardata.maxrunstars, 
            "Mean Baserunning": matchup.stardata.meanrunstars, "Ball Count": matchup.ballcount,
            "Strike Count": matchup.strikecount}

def insert_into_airtable(results, season_number, day):
    airtable = Airtable(os.getenv("AIRTABLE_BASE_KEY"), os.getenv("AIRTABLE_TABLE_NAME"), os.getenv("AIRTABLE_API_KEY"))
    airtable.batch_insert([get_dict_from_matchupdata(matchup, season_number, day) for matchup in results])


def process_game(game, season_number, day, team_stat_data, pitcher_stat_data):
    results = []
    gameId = game["id"]
    awayPitcher, homePitcher = game["awayPitcherName"], game["homePitcherName"]
    awayPitcherId, homePitcherId = game["awayPitcher"], game["homePitcher"]
    awayTeam, homeTeam = game["awayTeamName"], game["homeTeamName"]
    awayEmoji, homeEmoji = game['awayTeamEmoji'], game['homeTeamEmoji']
    stat_season_number = (season_number - 1) if day < LAST_SEASON_STAT_CUTOFF else season_number
    awayPitcherStats, homePitcherStats = get_pitcher_stats(awayPitcher, stat_season_number), get_pitcher_stats(homePitcher, stat_season_number)
    awayStarStats = calc_star_max_mean_stats(awayPitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data)
    homeStarStats = calc_star_max_mean_stats(homePitcher, homeTeam, awayTeam, team_stat_data, pitcher_stat_data)
    awayStlatStats = calc_stlat_stats(awayPitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data)
    homeStlatStats = calc_stlat_stats(homePitcher, homeTeam, awayTeam, team_stat_data, pitcher_stat_data)
    results.append(MatchupData(awayPitcher, awayPitcherId, awayTeam, gameId, awayPitcherStats.get("strikeoutsPerNine", -1.0), 
                                awayPitcherStats.get("earnedRunAverage", -1.0), awayEmoji, homeTeam, homeEmoji,
                                get_def_off_ratio(awayPitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data),
                                sum(team_stat_data[homeTeam]["battingStars"]), calc_bng(awayStlatStats), awayStarStats,
                                4, game["homeStrikes"], game["awayTeamNickname"], game["homeTeamNickname"], game["awayOdds"]))
    results.append(MatchupData(homePitcher, homePitcherId, homeTeam, gameId, homePitcherStats.get("strikeoutsPerNine", -1.0), 
                                homePitcherStats.get("earnedRunAverage", -1.0), homeEmoji, awayTeam, awayEmoji,
                                get_def_off_ratio(homePitcher, homeTeam, awayTeam, team_stat_data, pitcher_stat_data),
                                sum(team_stat_data[awayTeam]["battingStars"]), calc_bng(homeStlatStats), homeStarStats,
                                4, game["awayStrikes"], game["homeTeamNickname"], game["awayTeamNickname"], game["homeOdds"]))
    return results


def run_lineup_file_mode(filepath, team_stat_data, pitcher_stat_data):
    with open(filepath, "r") as json_file:
        json_data = json.load(json_file)
        for matchup in json_data:
            result = process_pitcher_vs_team(matchup["pitcherName"], matchup["pitcherTeam"], matchup["otherTeam"],
                                             matchup["seasonNumber"], team_stat_data, pitcher_stat_data)
            print("{} ({:.2f} SO9, {:.2f} ERA, {:.2f} BNG) vs. {} ({:.2f} Bat*, {:.2f} MaxBat), {:.2f} D/O^2".format(result.pitchername, result.so9, result.era, result.bng, result.vsteam, result.battingstars, result.stardata.maxbatstars, result.defoff))



def process_pitcher_vs_team(pitcherName, pitcherTeam, otherTeam, season_number, team_stat_data, pitcher_stat_data):
    pitcherStats = get_pitcher_stats(pitcherName, season_number)
    starStats = calc_star_max_mean_stats(pitcherName, pitcherTeam, otherTeam, team_stat_data, pitcher_stat_data)
    stlatStats = calc_stlat_stats(pitcherName, pitcherTeam, otherTeam, team_stat_data, pitcher_stat_data)
    return MatchupData(pitcherName, None, None, None, pitcherStats.get("strikeoutsPerNine", -1.0), 
                       pitcherStats.get("earnedRunAverage", -1.0), None, otherTeam, None,
                       get_def_off_ratio(pitcherName, pitcherTeam, otherTeam, team_stat_data, pitcher_stat_data),
                       sum(team_stat_data[otherTeam]["battingStars"]), calc_bng(stlatStats), starStats,
                       4, 3, None, None)


def sort_results(results, so9_pitchers=None, bng_pitchers=None):
    sorted_results = sorted(results, key=lambda res: res.so9, reverse=True)
    if so9_pitchers and bng_pitchers:
        grouped_results = [res for res in sorted_results if res.pitchername in so9_pitchers and res.pitchername in bng_pitchers]
        grouped_results.extend([res for res in sorted_results if res.pitchername in so9_pitchers and res.pitchername not in bng_pitchers])
        grouped_results.extend([res for res in sorted_results if res.pitchername not in so9_pitchers and res.pitchername in bng_pitchers])
        grouped_results.extend([res for res in sorted_results if res.pitchername not in so9_pitchers and res.pitchername not in bng_pitchers])
        sorted_results = grouped_results
    return sorted_results


def get_shame_results(today_schedule):
    allTeams = requests.get("https://blaseball.com/database/allTeams").json()
    shameable_teams = set([team['fullName'] for team in allTeams if 'SHAME_PIT' in team['seasAttr'] or 'SHAME_PIT' in team['permAttr']])
    return {game["awayTeamName"]: (game["homeScore"] - game["awayScore"]) for game in today_schedule if game['shame'] and game["awayTeamName"] in shameable_teams}
    

def outcome_matters(outcome):
    return "is now Unstable" not in outcome and "is now Flickering" not in outcome


def already_ran_for_day(filepath, season_number, day):
    if os.path.isfile(filepath):
        with open(filepath, "r") as f:
            file_season_number, file_day = (int(n) for n in f.read().split("-"))
            return file_season_number == season_number and file_day == day
    return False

def write_day(filepath, season_number, day):
    with open(filepath, "w") as f:
        f.write("{}-{}".format(season_number, day))


def discord_print_results(day, results, so9_pitchers, bng_pitchers, shame_results):
    output = []
    for result in sort_results(results, so9_pitchers, bng_pitchers):
        if result.pitchername in so9_pitchers or result.pitchername in bng_pitchers:
            so9 = "__{:.2f} SO9__".format(result.so9) if result.pitchername in so9_pitchers else "{:.2f} SO9".format(result.so9)
            formatted_bng = "{:.2f}".format(result.bng) if result.bng <= 1000000 else "{:.2e}".format(result.bng)
            bng = "__{} BNG__".format(formatted_bng) if result.pitchername in bng_pitchers else "{} BNG".format(formatted_bng)
            fmtstr = "{} **{}** ({}, {:.2f} ERA, {}) *vs.*\n {} **{}** ({:.2f} Bat★, {:.2f} MaxBat), {:.2f} D/O^2"
            outputstr = fmtstr.format(chr(int(result.defemoji, 16)), result.pitchername, so9, result.era, bng, chr(int(result.offemoji, 16)), result.vsteam, result.battingstars, result.stardata.maxbatstars, result.defoff)
            for team in (result.pitcherteam, result.vsteam):
                if team in shame_results:
                    outputstr += "\n:rotating_light::rotating_light: *{} Shame: -{}* :rotating_light::rotating_light:".format(team, shame_results[team])
            output.append(outputstr)
    title = "__**Day {}**__".format(day)
    message = "\n\n".join(output)
    print("{}\n{}".format(title, message))


def print_results(day, results, so9_pitchers, bng_pitchers, shame_results):
    print("Day {}".format(day))
    for result in sort_results(results, so9_pitchers, bng_pitchers):
        print("{} ({:.2f} SO9, {:.2f} ERA, {:.2f} BNG) vs. {} ({:.2f} Bat*, {:.2f} MaxBat), {:.2f} D/O^2".format(result.pitchername, result.so9, result.era, result.bng, result.vsteam, result.battingstars, result.stardata.maxbatstars, result.defoff))
        for team in (result.pitcherteam, result.vsteam):
            if team in shame_results:
                print("-- {} Shame: -{}".format(team, shame_results[team]))


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--print', help="print to screen", action='store_true')
    parser.add_argument('--discord', help="output to discord", action='store_true')
    parser.add_argument('--discordprint', help="print discord-formatted output to screen", action='store_true')
    parser.add_argument('--airtable', help="insert into airtable", action='store_true')
    parser.add_argument('--statfile', default='output.csv', help="stats filepath")
    parser.add_argument('--dayfile', default='lastday.txt', help="dayfile filepath")
    parser.add_argument('--today', help="run for today instead of tomorrow", action='store_true')
    parser.add_argument('--skipupdate', help="skip csv update, even if there should be one", action='store_true')
    parser.add_argument('--forceupdate', help="force csv update, even if it doesn't need it", action='store_true')
    parser.add_argument('--forcerun', help="force running for day, even if it was already run last", action='store_true')
    parser.add_argument('--lineupfile', help="json file with array of {pitcherName, pitcherTeam, awayTeam, seasonNumber} lineups, print mode only")
    parser.add_argument('--archive', help="move csv file if a new one is regenerated before writing", action='store_true')
    args = parser.parse_args()
    if not args.print and not args.discord and not args.airtable and not args.discordprint and not args.lineupfile:
        print("No output specified")
        parser.print_help()
        sys.exit(-1)
    return args


def main():
    args = handle_args()
    load_dotenv()
    streamdata = get_stream_snapshot()
    season_number = streamdata['value']['games']['season']['seasonNumber']  # 0-indexed
    day = streamdata['value']['games']['sim']['day'] + (1 if args.today else 2)  # 0-indexed, make 1-indexed and add another if tomorrow
    tomorrowgames = streamdata['value']['games'][('schedule' if args.today else 'tomorrowSchedule')]
    if not tomorrowgames:
        print("No games found for Season {} Day {}, exiting.".format(season_number+1, day))
        sys.exit(0)
    if already_ran_for_day(args.dayfile, season_number, day) and not args.forcerun:
        print("Already ran for Season {} Day {}, exiting.".format(season_number+1, day))
        sys.exit(0)
    outcomes = [outcome for game in streamdata['value']['games']['schedule'] if game["outcomes"] for outcome in game['outcomes'] if outcome_matters(outcome)]
    stat_file_exists = os.path.isfile(args.statfile)
    if (outcomes or not stat_file_exists or args.forceupdate or ((day == 1 and args.today) or day == 2)) and not args.skipupdate:
        if args.discord:
            message = "Generating new stat file, please stand by.\n\n{}".format("\n".join("`{}`".format(outcome) for outcome in outcomes))
            send_discord_message("Sorry!", message[:DISCORD_SPLIT_LIMIT])
        else:
            print("Generating new stat file, please stand by.")
        if args.archive and stat_file_exists:
            os.rename(args.statfile, args.statfile.replace(".csv", "S{}preD{}.csv".format(season_number+1, day)))
        blaseball_stat_csv.generate_file(args.statfile, False)
    team_stat_data, pitcher_stat_data = load_stat_data(args.statfile)
    if args.lineupfile:
        run_lineup_file_mode(args.lineupfile, team_stat_data, pitcher_stat_data)
        sys.exit(0)
    results, pair_results = [], []
    if not args.today: # can't check for targeted shame without both today and tomorrow schedules
        shame_results = get_shame_results(streamdata['value']['games']['schedule'])
    for game in tomorrowgames:
        awayMatchupData, homeMatchupData = process_game(game, season_number, day, team_stat_data, pitcher_stat_data)
        results.extend((awayMatchupData, homeMatchupData))
        pair_results.append(MatchupPair(awayMatchupData, homeMatchupData))
    if pair_results:
        so9_pitchers = {res.pitchername for res in sorted(results, key=lambda res: res.so9, reverse=True)[:5]}
        bng_pitchers = {res.pitchername for res in results if BNG_FLOOR <= res.bng <= BNG_CEILING}
        if args.discord:
            send_matchup_data_to_discord_webhook(day, pair_results, so9_pitchers, bng_pitchers, shame_results)
        if args.discordprint:
            discord_print_results(day, results, so9_pitchers, bng_pitchers, shame_results)
        if args.airtable:
            insert_into_airtable(results, season_number+1, day)
        if args.print:
            print_results(day, results, so9_pitchers, bng_pitchers, shame_results)
    else:
        print("No results")
    write_day(args.dayfile, season_number, day)


if __name__ == "__main__":
    main()
