from __future__ import division
from __future__ import print_function

import argparse
import collections
import csv
import json
import linecache
import math
import os
import random
import sys
from collections import namedtuple
from functools import reduce

import requests
from airtable import Airtable
from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv

import blaseball_stat_csv
from tim import RED_HOT, HOT, WARM, TEPID, TEMPERATE, COOL, DEAD_COLD, TIM_ERROR

MatchupData = namedtuple("MatchupData", ["pitchername", "pitcherid", "pitcherteam", "gameid", "so9", "era", "defemoji",
                                         "vsteam", "offemoji", "defoff", "battingstars", "tim", "timrank", "timcalc",
                                         "stardata", "ballcount", "strikecount", "pitcherteamnickname",
                                         "vsteamnickname", "winodds"])

MatchupPair = namedtuple("MatchupPair", ["awayMatchupData", "homeMatchupData"])

StarData = namedtuple("StarData", ["pitchingstars", "maxbatstars", "meanbatstars", "maxdefstars", "meandefstars", 
                                   "maxrunstars", "meanrunstars"])

PITCHING_STLATS = ["overpowerment", "ruthlessness", "unthwackability", "shakespearianism", "coldness"]
OFFENSE_STLATS = ["tragicness", "patheticism", "thwackability", "divinity", "moxie", "musclitude", "martyrdom",
                  "baseThirst"]
DEFENSE_STLATS = ["omniscience", "tenaciousness", "watchfulness", "chasiness"]

StlatData = namedtuple("StlatData", ["overpowerment", "ruthlessness", "unthwackability", "shakespearianism", "coldness",  # Pitching
                                     "meantragicness", "meanpatheticism", "meanthwackability", "meandivinity",  # Opponent
                                     "meanmoxie", "meanmusclitude", "meanmartyrdom"])

BR_PLAYERNAME_SUBS = {
    "wyatt-owens": "emmett-owens",
    "peanut-bong": "dan-bong"
}


BNG_FLOOR = 100.0
BNG_CEILING = 994975
LAST_SEASON_STAT_CUTOFF = 11
DISCORD_SPLIT_LIMIT = 1900
DISCORD_RESULT_PER_BATCH = 5

TIM_TIERS = (RED_HOT, HOT, WARM, TEPID, TEMPERATE, COOL, DEAD_COLD)


class PrintWebhook:
    def __init__(self, content=None, **kwargs):
        self.content = content
        self.embeds = []

    def add_embed(self, embed):
        self.embeds.append(embed)

    def execute(self):
        if self.content:
            print(self.content)
        for embed in self.embeds:
            print(embed)


class PrintEmbed:
    def __init__(self, description=None, **kwargs):
        self.description = description

    def __repr__(self):
        return "{}\n{}".format(discord_hr(), self.description)


def discord_hr(spaces=25, char=" "):
    return "~~-{}-~~".format(char * spaces)


def send_discord_message(title, message):
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL").split(";")
    webhook = DiscordWebhook(url=discord_webhook_url)
    webhook.add_embed(DiscordEmbed(title=title, description=message))
    return webhook.execute()


def get_formatted_odds(away_odds, home_odds):
    formatted_away_odds = "{:.2f}%".format(away_odds*100.0)
    formatted_home_odds = "{:.2f}%".format(home_odds*100.0)
    if away_odds > home_odds:
        formatted_away_odds = "__{}__".format(formatted_away_odds)
    elif home_odds > away_odds:
        formatted_home_odds = "__{}__".format(formatted_home_odds)
    return formatted_away_odds, formatted_home_odds


def get_output_line_from_matchup(matchup_data, odds, so9_pitchers, higher_tim, screen=False):
    so9 = "__{:.2f} SO9__".format(matchup_data.so9) if matchup_data.pitchername in so9_pitchers else "{:.2f} SO9".format(matchup_data.so9)
    tim = "__{}__".format(matchup_data.tim.name) if higher_tim else matchup_data.tim.name
    formatstr = ("{} **{}, {}** ({}, {}, {:.2f} ERA), "
                 "({:.2f} OppBat★, {:.2f} OppMaxBat), {:.2f} D/O^2, {}")
    name = matchup_data.pitchername if screen else ("[{}](https://blaseball-reference.com/players/{})"
                                                    "").format(matchup_data.pitchername, get_player_slug(matchup_data.pitchername))
    return formatstr.format(chr(int(matchup_data.defemoji, 16)), name,
                            matchup_data.pitcherteamnickname, tim, so9, matchup_data.era, matchup_data.battingstars,
                            matchup_data.stardata.maxbatstars, matchup_data.defoff, odds)


def send_matchup_data_to_discord_webhook(day, matchup_pairs, so9_pitchers, shame_results, screen=False):
    Webhook, Embed = (PrintWebhook, PrintEmbed) if screen else (DiscordWebhook, DiscordEmbed)
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL").split(";")
    sorted_pairs = sorted(matchup_pairs,
                          key=lambda matchup_pair: (max(matchup_pair.awayMatchupData.timrank,
                                                        matchup_pair.homeMatchupData.timrank),
                                                    max(matchup_pair.awayMatchupData.so9,
                                                        matchup_pair.homeMatchupData.so9)), reverse=True)
    batches = math.ceil(len(matchup_pairs) / DISCORD_RESULT_PER_BATCH)
    webhooks = [Webhook(url=discord_webhook_url,
                        content="__**Day {}**__{}".format(day, " (cont.)" if batch else "")) for batch in range(batches)]
    for idx, result in enumerate(sorted_pairs):
        awayMatchupData, homeMatchupData = result.awayMatchupData, result.homeMatchupData
        awayOdds, homeOdds = get_formatted_odds(awayMatchupData.winodds, homeMatchupData.winodds)
        awayHigherTIM = awayMatchupData.timrank > homeMatchupData.timrank or (awayMatchupData.timrank == homeMatchupData.timrank and awayMatchupData.timcalc > homeMatchupData.timcalc)
        homeHigherTIM = homeMatchupData.timrank > awayMatchupData.timrank or (homeMatchupData.timrank == awayMatchupData.timrank and homeMatchupData.timcalc > awayMatchupData.timcalc)
        color = awayMatchupData.tim.color if awayHigherTIM else homeMatchupData.tim.color
        description = "{0}\n{2} @ {2}\n{1}".format(get_output_line_from_matchup(awayMatchupData, awayOdds, so9_pitchers, awayHigherTIM, screen=screen),
                                                   get_output_line_from_matchup(homeMatchupData, homeOdds, so9_pitchers, homeHigherTIM, screen=screen),
                                                   discord_hr(10, char="-"))
        for matchup_data in (awayMatchupData, homeMatchupData):
            if matchup_data.pitcherteam in shame_results:
                description += ("\n:rotating_light::rotating_light: *{} Shame: -{}* :rotating_light::rotating_light:"
                                "").format(matchup_data.pitcherteamnickname, shame_results[matchup_data.pitcherteam])
        print(description)
        embed = Embed(description=description, color=color)
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
                for key in (OFFENSE_STLATS + ["battingStars", "baserunningStars"]):
                    teamstatdata[row["team"]][key].append(float(row[key]))
            for key in (DEFENSE_STLATS + ["defenseStars"]):
                    teamstatdata[row["team"]][key].append(float(row[key]))
    return teamstatdata, pitcherstardata


def get_player_slug(playername):
    playerslug = playername.lower().replace(" ", "-")
    playerslug = BR_PLAYERNAME_SUBS.get(playerslug, playerslug)
    return playerslug


def get_all_pitcher_performance_stats(pitcher_ids, season):
    url = ("https://api.blaseball-reference.com/v1/playerStats?category=pitching&season={}&playerIds={}"
           "").format(season, ",".join(pitcher_ids))
    response = requests.get(url)
    resjson = response.json()
    return {pitcher["player_id"]: pitcher for pitcher in resjson}


def get_tim(stlatdata):
    tier_length = len(TIM_TIERS)
    for idx, tier in enumerate(TIM_TIERS):
        calc, check = tier.check(stlatdata.unthwackability, stlatdata.ruthlessness, stlatdata.overpowerment,
                                 stlatdata.shakespearianism, stlatdata.coldness, stlatdata.meantragicness,
                                 stlatdata.meanpatheticism, stlatdata.meanthwackability, stlatdata.meandivinity,
                                 stlatdata.meanmoxie, stlatdata.meanmusclitude, stlatdata.meanmartyrdom)
        if check:
            return tier, tier_length-idx, calc
    return TIM_ERROR, -1, -1


def calc_star_max_mean_stats(pitcher, defenseteamname, offenseteamname, team_stat_data, pitcher_stat_data):
    pitchingstars = pitcher_stat_data[pitcher]["pitchingStars"]
    maxbatstars = max(team_stat_data[offenseteamname]["battingStars"])
    meanbatstars = geomean(team_stat_data[offenseteamname]["battingStars"])
    maxdefstars = max(team_stat_data[defenseteamname]["defenseStars"])
    meandefstars = geomean(team_stat_data[defenseteamname]["defenseStars"])
    maxrunstars = max(team_stat_data[offenseteamname]["baserunningStars"])
    meanrunstars = geomean(team_stat_data[offenseteamname]["baserunningStars"])
    return StarData(pitchingstars, maxbatstars, meanbatstars, maxdefstars, meandefstars, maxrunstars, meanrunstars)


def calc_stlat_stats(pitcher, offenseteamname, team_stat_data, pitcher_stat_data):
    stlatdata = [pitcher_stat_data[pitcher][stlat] for stlat in ["overpowerment", "ruthlessness", "unthwackability",
                                                                 "shakespearianism", "coldness"]]
    stlatdata.extend((geomean(team_stat_data[offenseteamname]["tragicness"]),
                      geomean(team_stat_data[offenseteamname]["patheticism"]),
                      geomean(team_stat_data[offenseteamname]["thwackability"]),
                      geomean(team_stat_data[offenseteamname]["divinity"]),
                      geomean(team_stat_data[offenseteamname]["moxie"]),
                      geomean(team_stat_data[offenseteamname]["musclitude"]),
                      geomean(team_stat_data[offenseteamname]["martyrdom"])))
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


def process_game(game, team_stat_data, pitcher_stat_data, pitcher_performance_stats):
    results = []
    gameId = game["id"]
    awayPitcher, homePitcher = game["awayPitcherName"], game["homePitcherName"]
    awayPitcherId, homePitcherId = game["awayPitcher"], game["homePitcher"]
    awayTeam, homeTeam = game["awayTeamName"], game["homeTeamName"]
    awayEmoji, homeEmoji = game['awayTeamEmoji'], game['homeTeamEmoji']
    awayPitcherStats = pitcher_performance_stats.get(awayPitcherId, {})
    homePitcherStats = pitcher_performance_stats.get(homePitcherId, {})
    awayStarStats = calc_star_max_mean_stats(awayPitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data)
    homeStarStats = calc_star_max_mean_stats(homePitcher, homeTeam, awayTeam, team_stat_data, pitcher_stat_data)
    awayStlatStats = calc_stlat_stats(awayPitcher, homeTeam, team_stat_data, pitcher_stat_data)
    homeStlatStats = calc_stlat_stats(homePitcher, awayTeam, team_stat_data, pitcher_stat_data)
    awayTIM, awayTIMRank, awayTIMCalc = get_tim(awayStlatStats)
    homeTIM, homeTIMRank, homeTIMCalc = get_tim(homeStlatStats)
    results.append(MatchupData(awayPitcher, awayPitcherId, awayTeam, gameId,
                               float(awayPitcherStats.get("k_per_9", -1.0)), float(awayPitcherStats.get("era", -1.0)),
                               awayEmoji, homeTeam, homeEmoji,
                               get_def_off_ratio(awayPitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data),
                               sum(team_stat_data[homeTeam]["battingStars"]), awayTIM, awayTIMRank, awayTIMCalc,
                               awayStarStats, 4, game["homeStrikes"], game["awayTeamNickname"],
                               game["homeTeamNickname"], game["awayOdds"]))
    results.append(MatchupData(homePitcher, homePitcherId, homeTeam, gameId,
                               float(homePitcherStats.get("k_per_9", -1.0)), float(homePitcherStats.get("era", -1.0)),
                               homeEmoji, awayTeam, awayEmoji,
                               get_def_off_ratio(homePitcher, homeTeam, awayTeam, team_stat_data, pitcher_stat_data),
                               sum(team_stat_data[awayTeam]["battingStars"]), homeTIM, homeTIMRank, homeTIMCalc,
                               homeStarStats, 4, game["awayStrikes"], game["homeTeamNickname"],
                               game["awayTeamNickname"], game["homeOdds"]))
    return results


def run_lineup_file_mode(filepath, team_stat_data, pitcher_stat_data, stat_season_number):
    with open(filepath, "r") as json_file:
        json_data = json.load(json_file)
        all_pitcher_ids = [matchup["pitcherId"] for matchup in json_data]
        pitcher_performance_stats = get_all_pitcher_performance_stats(all_pitcher_ids, stat_season_number)
        for matchup in json_data:
            result = process_pitcher_vs_team(matchup["pitcherName"], matchup["pitcherId"], matchup["pitcherTeam"],
                                             matchup["otherTeam"], team_stat_data, pitcher_stat_data,
                                             pitcher_performance_stats)
            print(("{} ({}, {:.2f} SO9, {:.2f} ERA) vs. {} ({:.2f} Bat*, {:.2f} MaxBat), {:.2f} D/O^2"
                   "").format(result.pitchername, result.tim.name, result.so9, result.era, result.vsteam,
                              result.battingstars, result.stardata.maxbatstars, result.defoff))


def process_pitcher_vs_team(pitcherName, pitcherId, pitcherTeam, otherTeam, team_stat_data, pitcher_stat_data,
                            pitcher_performance_stats):
    pitcherStats = pitcher_performance_stats.get(pitcherId, {})
    starStats = calc_star_max_mean_stats(pitcherName, pitcherTeam, otherTeam, team_stat_data, pitcher_stat_data)
    stlatStats = calc_stlat_stats(pitcherName, otherTeam, team_stat_data, pitcher_stat_data)
    tim, timRank, timCalc = get_tim(stlatStats)
    return MatchupData(pitcherName, None, None, None, float(pitcherStats.get("k_per_9", -1.0)),
                       float(pitcherStats.get("era", -1.0)), None, otherTeam, None,
                       get_def_off_ratio(pitcherName, pitcherTeam, otherTeam, team_stat_data, pitcher_stat_data),
                       sum(team_stat_data[otherTeam]["battingStars"]), tim, timRank, timCalc, starStats,
                       4, 3, None, None, None)


def sort_results(results):
    return sorted(results, key=lambda result: (result.timrank, result.so9), reverse=True)


def get_shame_results(today_schedule):
    allTeams = requests.get("https://blaseball.com/database/allTeams").json()
    shameable_teams = set([team['fullName'] for team in allTeams if 'SHAME_PIT' in team['seasAttr'] or 'SHAME_PIT' in team['permAttr']])
    return {game["awayTeamName"]: (game["homeScore"] - game["awayScore"]) for game in today_schedule if game['shame'] and game["awayTeamName"] in shameable_teams}


def outcome_matters(outcome):
    return all(s not in outcome for s in ("is now Unstable", "is now Flickering", "Red Hot"))


def already_ran_for_day(filepath, season_number, day):
    if os.path.isfile(filepath):
        with open(filepath, "r") as f:
            file_season_number, file_day = (int(n) for n in f.read().split("-"))
            return file_season_number == season_number and file_day == day
    return False


def write_day(filepath, season_number, day):
    with open(filepath, "w") as f:
        f.write("{}-{}".format(season_number, day))


def print_results(day, results, shame_results):
    print("Day {}".format(day))
    for result in sort_results(results):
        print(("{} ({}, {:.2f} SO9, {:.2f} ERA) vs. {} ({:.2f} Bat*, {:.2f} MaxBat), {:.2f} D/O^2"
               "").format(result.pitchername, result.tim.name, result.so9, result.era, result.vsteam,
                          result.battingstars, result.stardata.maxbatstars, result.defoff))
        for team in (result.pitcherteam, result.vsteam):
            if team in shame_results:
                print("-- {} Shame: -{}".format(team, shame_results[team]))


def load_test_data(testfile):
    filename, linenumber = testfile, None
    if ":" in testfile:
        filename, linenumber = testfile.split(":")
    else:
        with open(filename) as f:
            for i, l in enumerate(f):
                pass
        linenumber = random.randint(1, i + 1)
    print("Loading test data from {}, line {}".format(filename, linenumber))
    return json.loads(linecache.getline(filename, int(linenumber)))


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
    parser.add_argument('--forcerun', help="force running for day, even if it was already run last",
                        action='store_true')
    parser.add_argument('--lineupfile', help="json file with array of{pitcherName, pitcherTeam, awayTeam, seasonNumber}"
                                             " lineups, print mode only")
    parser.add_argument('--archive', help="move csv file if a new one is regenerated before writing",
                        action='store_true')
    parser.add_argument('--testfile', help="path to file with test data in jsonl format, pass optional line number as "
                                           "filename:n, otherwise random line is used")
    args = parser.parse_args()
    if not args.print and not args.discord and not args.airtable and not args.discordprint and not args.lineupfile:
        print("No output specified")
        parser.print_help()
        sys.exit(-1)
    return args


def main():
    args = handle_args()
    load_dotenv()
    if args.testfile:
        streamdata = load_test_data(args.testfile)
    else:
        streamdata = get_stream_snapshot()
    season_number = streamdata['value']['games']['season']['seasonNumber']  # 0-indexed
    day = streamdata['value']['games']['sim']['day'] + (1 if args.today else 2)  # 0-indexed, make 1-indexed and add another if tomorrow
    stat_season_number = (season_number - 1) if day < LAST_SEASON_STAT_CUTOFF else season_number
    tomorrowgames = streamdata['value']['games'][('schedule' if args.today else 'tomorrowSchedule')]
    if not tomorrowgames and not args.lineupfile:
        print("No games found for Season {} Day {}, exiting.".format(season_number+1, day))
        sys.exit(0)
    if already_ran_for_day(args.dayfile, season_number, day) and not args.forcerun and not args.lineupfile:
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
        run_lineup_file_mode(args.lineupfile, team_stat_data, pitcher_stat_data, stat_season_number)
        sys.exit(0)
    results, pair_results = [], []
    shame_results = {}
    if not args.today:  # can't check for targeted shame without both today and tomorrow schedules
        shame_results = get_shame_results(streamdata['value']['games']['schedule'])
    all_pitcher_ids = []
    for game in tomorrowgames:
        all_pitcher_ids.extend((game["awayPitcher"], game["homePitcher"]))
    pitcher_performance_stats = get_all_pitcher_performance_stats(all_pitcher_ids, stat_season_number)
    for game in tomorrowgames:
        awayMatchupData, homeMatchupData = process_game(game, team_stat_data, pitcher_stat_data,
                                                        pitcher_performance_stats)
        results.extend((awayMatchupData, homeMatchupData))
        pair_results.append(MatchupPair(awayMatchupData, homeMatchupData))
    if pair_results:
        so9_pitchers = {res.pitchername for res in sorted(results, key=lambda res: res.so9, reverse=True)[:5]}
        if args.discord:
            send_matchup_data_to_discord_webhook(day, pair_results, so9_pitchers, shame_results)
        if args.discordprint:
            send_matchup_data_to_discord_webhook(day, pair_results, so9_pitchers, shame_results, screen=True)
        if args.airtable:
            insert_into_airtable(results, season_number+1, day)
        if args.print:
            print_results(day, results, shame_results)
    else:
        print("No results")
    write_day(args.dayfile, season_number, day)


if __name__ == "__main__":
    main()
