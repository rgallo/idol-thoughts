from __future__ import division
from __future__ import print_function

import argparse
import collections
import csv
import json
import linecache
import os
import random
import sys
import time
from collections import namedtuple

import requests
from airtable import Airtable
from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv

import k9
from blaseball_stat_csv import blaseball_stat_csv
import tim
import mofo
from helpers import geomean, get_weather_idx

MatchupData = namedtuple("MatchupData", ["pitchername", "pitcherid", "pitcherteam", "gameid", "so9", "era", "defemoji",
                                         "vsteam", "offemoji", "defoff", "tim", "timrank", "timcalc",
                                         "stardata", "ballcount", "strikecount", "basecount", "pitcherteamnickname",
                                         "vsteamnickname", "websiteodds", "mofoodds", "k9"])

MatchupPair = namedtuple("MatchupPair", ["awayMatchupData", "homeMatchupData"])

StarData = namedtuple("StarData", ["pitchingstars", "maxbatstars", "meanbatstars", "maxdefstars", "meandefstars", 
                                   "maxrunstars", "meanrunstars"])

PITCHING_STLATS = ["overpowerment", "ruthlessness", "unthwackability", "shakespearianism", "coldness", "suppression"]
BATTING_STLATS = ["divinity", "martyrdom", "moxie", "musclitude", "patheticism", "thwackability", "tragicness"]
DEFENSE_STLATS = ["anticapitalism", "chasiness", "omniscience", "tenaciousness", "watchfulness"]
BASERUNNING_STLATS = ["baseThirst", "continuation", "groundFriction", "indulgence", "laserlikeness"]
INVERSE_STLATS = ["tragicness", "patheticism"]  # These stlats are better for the target the smaller they are

StlatData = namedtuple("StlatData", ["overpowerment", "ruthlessness", "unthwackability", "shakespearianism", "coldness",  # Pitching
                                     "meantragicness", "meanpatheticism", "meanthwackability", "meandivinity",  # Opponent
                                     "meanmoxie", "meanmusclitude", "meanmartyrdom"])

ScoreAdjustment = namedtuple("ScoreAdjustment", ["score", "label"])

BR_PLAYERNAME_SUBS = {
    "wyatt-owens": "emmett-owens",
    "peanut-bong": "dan-bong"
}


BNG_FLOOR = 100.0
BNG_CEILING = 994975
LAST_SEASON_STAT_CUTOFF = 11
DISCORD_SPLIT_LIMIT = 1900
DISCORD_RESULT_PER_BATCH = 2


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


def send_discord_message(title, message, screen=False):
    Webhook, Embed = (PrintWebhook, PrintEmbed) if screen else (DiscordWebhook, DiscordEmbed)
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL").split(";")
    webhook = Webhook(url=discord_webhook_url)
    webhook.add_embed(Embed(title=title, description=message))
    return webhook.execute()


def get_formatted_odds(away_odds, home_odds):
    formatted_away_odds = "{:.2f}%".format(away_odds*100.0)
    formatted_home_odds = "{:.2f}%".format(home_odds*100.0)
    if away_odds < home_odds:
        formatted_away_odds = "~~{}~~".format(formatted_away_odds)
    elif home_odds < away_odds:
        formatted_home_odds = "~~{}~~".format(formatted_home_odds)
    return formatted_away_odds, formatted_home_odds


def get_output_line_from_matchup(matchup_data, websiteodds, mofoodds, so9_pitchers, k9_pitchers, higher_tim, lower_tim_rank, screen=False):
    so9 = "__{:.2f} SO9__".format(matchup_data.so9) if matchup_data.pitchername in so9_pitchers else "{:.2f} SO9".format(matchup_data.so9)
    k9 = "__{} K9__".format(matchup_data.k9) if matchup_data.pitchername in k9_pitchers else "{} K9".format(matchup_data.k9)
    tim = "__{}__".format(matchup_data.tim.name) if higher_tim else "~~{}~~".format(matchup_data.tim.name) if lower_tim_rank else matchup_data.tim.name
    formatstr = ("{} **{}, {}** ({}, {}, {}, {:.2f} ERA), "
                 "({:.2f}★ AOB, {:.2f}★ MOB), {:.2f} D/O^2, {} WebOdds, {} MOFO")
    name = matchup_data.pitchername if screen else ("[{}](https://blaseball-reference.com/players/{})"
                                                    "").format(matchup_data.pitchername, get_player_slug(matchup_data.pitchername))
    try:
        emoji = chr(int(matchup_data.defemoji, 16))
    except ValueError:
        emoji = matchup_data.defemoji
    return formatstr.format(emoji, name, matchup_data.pitcherteamnickname, tim, k9, so9, matchup_data.era,
                            matchup_data.stardata.meanbatstars, matchup_data.stardata.maxbatstars, matchup_data.defoff,
                            websiteodds, mofoodds)


def add_score_adjustments(description, matchup_data, score_adjustments):
    new_description = description
    if matchup_data.pitcherteam in score_adjustments:
        for score_adjustment in score_adjustments[matchup_data.pitcherteam]:
            new_description += ("\n:rotating_light::rotating_light: *{} {}: {}{}* :rotating_light::rotating_light:"
                                "").format(matchup_data.pitcherteamnickname, score_adjustment.label,
                                           "+" if score_adjustment.score > 0 else "", score_adjustment.score)
    return new_description


def send_matchup_data_to_discord_webhook(day, matchup_pairs, so9_pitchers, k9_pitchers, score_adjustments, screen=False):
    Webhook, Embed = (PrintWebhook, PrintEmbed) if screen else (DiscordWebhook, DiscordEmbed)
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL").split(";")
    notify_tim_rank, notify_role = os.getenv("NOTIFY_TIM_RANK"), os.getenv("NOTIFY_ROLE")
    sortkey = lambda matchup_pair: (max(matchup_pair.awayMatchupData.timrank, matchup_pair.homeMatchupData.timrank),
                                    max(matchup_pair.awayMatchupData.k9, matchup_pair.homeMatchupData.k9),
                                    max(matchup_pair.awayMatchupData.mofoodds, matchup_pair.homeMatchupData.mofoodds))
    sorted_pairs = sorted(matchup_pairs, key=sortkey, reverse=True)
    batches = len(matchup_pairs)
    webhooks = [Webhook(url=discord_webhook_url,
                        content="__**Day {}**__".format(day) if not batch else discord_hr(10, char='-')) for batch in range(batches)]
    odds_mismatch, notify = [], []
    for idx, result in enumerate(sorted_pairs):
        awayMatchupData, homeMatchupData = result.awayMatchupData, result.homeMatchupData
        awayOdds, homeOdds = get_formatted_odds(awayMatchupData.websiteodds, homeMatchupData.websiteodds)
        awayMOFOOdds, homeMOFOOdds = get_formatted_odds(awayMatchupData.mofoodds, homeMatchupData.mofoodds)
        awayHigherTIMRank = awayMatchupData.timrank > homeMatchupData.timrank
        awayHigherTIM = awayHigherTIMRank or (awayMatchupData.timrank == homeMatchupData.timrank and awayMatchupData.timcalc > homeMatchupData.timcalc)
        homeHigherTIMRank = homeMatchupData.timrank > awayMatchupData.timrank
        homeHigherTIM = homeHigherTIMRank or (homeMatchupData.timrank == awayMatchupData.timrank and homeMatchupData.timcalc > awayMatchupData.timcalc)
        awayOutput = get_output_line_from_matchup(awayMatchupData, awayOdds, awayMOFOOdds, so9_pitchers, k9_pitchers,
                                                  awayHigherTIM, homeHigherTIMRank, screen=screen)
        awayOutput = add_score_adjustments(awayOutput, awayMatchupData, score_adjustments)
        homeOutput = get_output_line_from_matchup(homeMatchupData, homeOdds, homeMOFOOdds, so9_pitchers, k9_pitchers,
                                                  homeHigherTIM, awayHigherTIMRank, screen=screen)
        homeOutput = add_score_adjustments(homeOutput, homeMatchupData, score_adjustments)
        if (awayMatchupData.mofoodds < .5 < awayMatchupData.websiteodds) or (awayMatchupData.mofoodds > .5 > awayMatchupData.websiteodds) or (.495 <= awayMatchupData.websiteodds < .505):
            odds_mismatch.append(result)
        if notify_tim_rank and notify_role:
            if awayMatchupData.timrank >= int(notify_tim_rank):
                notify.append(awayMatchupData)
            if homeMatchupData.timrank >= int(notify_tim_rank):
                notify.append(homeMatchupData)
        webhooks[(idx * 2) // DISCORD_RESULT_PER_BATCH].add_embed(Embed(description=awayOutput, color=awayMatchupData.tim.color))
        webhooks[(idx * 2) // DISCORD_RESULT_PER_BATCH].add_embed(Embed(description=homeOutput, color=homeMatchupData.tim.color))
    results = []
    for webhook in webhooks:
        results.append(webhook.execute())
        time.sleep(.5)
    if odds_mismatch:
        odds_description = "\n".join(["{} @ {} - Website: {} {:.2f}%, MOFO: **{}** {:.2f}%".format(
            "**{}**".format(result.awayMatchupData.pitcherteamnickname) if result.awayMatchupData.mofoodds > result.homeMatchupData.mofoodds else result.awayMatchupData.pitcherteamnickname,
            "**{}**".format(result.homeMatchupData.pitcherteamnickname) if result.homeMatchupData.mofoodds > result.awayMatchupData.mofoodds else result.homeMatchupData.pitcherteamnickname,
            result.awayMatchupData.pitcherteamnickname if result.awayMatchupData.websiteodds > result.homeMatchupData.websiteodds else result.homeMatchupData.pitcherteamnickname,
            (max(result.awayMatchupData.websiteodds, result.homeMatchupData.websiteodds)) * 100.0,
            result.awayMatchupData.pitcherteamnickname if result.awayMatchupData.mofoodds > result.homeMatchupData.mofoodds else result.homeMatchupData.pitcherteamnickname,
            (max(result.awayMatchupData.mofoodds, result.homeMatchupData.mofoodds)) * 100.0)
                                      for result in odds_mismatch])
        results.append(send_discord_message("__Odds Mismatches__", odds_description, screen=screen))
    if notify:
        notify_message = "<@&{}> __**FIRE PICKS**__\n".format(notify_role)
        notify_message += "\n".join(["{}, {} - **{}**".format(matchup_data.pitchername, matchup_data.pitcherteamnickname,
                                                            matchup_data.tim.name) for matchup_data in notify])
        results.append(Webhook(url=discord_webhook_url, content=notify_message).execute())
    return results


def get_blaseball_snapshot():
    snapshot = None
    response = requests.get("https://www.blaseball.com/events/streamData", stream=True)
    for line in response.iter_lines():
        snapshot = line
        break
    try:
        json_snapshot = json.loads(snapshot.decode("utf-8")[6:])
    except json.decoder.JSONDecodeError:
        return None
    return json_snapshot


def get_testing_snapshot():
    snapshot = None
    with requests.get("https://api-test.sibr.dev/replay/v1/replay?from=2020-10-19T22:45:00Z", stream=True) as response:
        for line in response.iter_lines():
            if line and line.decode("utf-8").startswith("data"):
                snapshot = line
                break
    try:
        json_snapshot = json.loads(snapshot.decode("utf-8")[5:])
    except json.decoder.JSONDecodeError:
        return None
    return json_snapshot


def get_stream_snapshot():
    json_snapshot = None
    retries = 0
    while json_snapshot is None and retries < 5:
        if retries:
            time.sleep(2)  # Sleep after first time
        json_snapshot = get_blaseball_snapshot()
        retries += 1
    if not json_snapshot:
        raise Exception("Unable to get stream snapshot")
    return json_snapshot


def get_def_off_ratio(pitcher, defenseteamname, offenseteamname, team_stat_data, pitcher_stat_data):
    pitchingstars = pitcher_stat_data[pitcher]["pitchingStars"]
    meandefstars = geomean(team_stat_data[defenseteamname]["defenseStars"])
    meanbatstars = geomean(team_stat_data[offenseteamname]["battingStars"])
    meanrunstars = geomean(team_stat_data[offenseteamname]["baserunningStars"])
    return (pitchingstars+meandefstars)/((meanbatstars+meanrunstars) ** 2)


def get_team_attributes(attributes={}):
    if not attributes:
        attributes.update({team["fullName"]: (team["gameAttr"] + team["weekAttr"] + team["seasAttr"] + team["permAttr"]) for team in requests.get("https://www.blaseball.com/database/allTeams").json()})
    return attributes


def adjust_by_pct(row, pct, stlats, star_func):
    new_row = row.copy()
    original_stars = star_func(row)
    new_stars = original_stars
    while new_stars < original_stars * (1.0 + pct):
        for stlat in stlats:
            if stlat in INVERSE_STLATS and stlat != "tragicness":
                new_row[stlat] = max(float(new_row[stlat]) - .01, .01)
            elif stlat not in INVERSE_STLATS:
                new_row[stlat] = float(new_row[stlat]) + .01
        new_stars = star_func(new_row)
    return new_row


def adjust_stlats(row, game, day, team_attrs=None):
    new_row = row.copy()
    if game:
        team = row["team"]
        current_team_attrs = (team_attrs if team_attrs is not None else get_team_attributes()).get(team, {})
        if "GROWTH" in current_team_attrs:
            growth_pct = .05 * min(day / 99, 1.0)
            new_row = adjust_by_pct(new_row, growth_pct, PITCHING_STLATS, blaseball_stat_csv.pitching_stars)
            new_row = adjust_by_pct(new_row, growth_pct, BATTING_STLATS, blaseball_stat_csv.batting_stars)
            new_row = adjust_by_pct(new_row, growth_pct, BASERUNNING_STLATS, blaseball_stat_csv.baserunning_stars)
            new_row = adjust_by_pct(new_row, growth_pct, DEFENSE_STLATS, blaseball_stat_csv.defense_stars)
        if "TRAVELING" in current_team_attrs and team == game["awayTeamName"]:
            new_row = adjust_by_pct(new_row, 0.05, PITCHING_STLATS, blaseball_stat_csv.pitching_stars)
            new_row = adjust_by_pct(new_row, 0.05, BATTING_STLATS, blaseball_stat_csv.batting_stars)
            new_row = adjust_by_pct(new_row, 0.05, BASERUNNING_STLATS, blaseball_stat_csv.baserunning_stars)
            new_row = adjust_by_pct(new_row, 0.05, DEFENSE_STLATS, blaseball_stat_csv.defense_stars)
        bird_weather = get_weather_idx("Birds")
        if "AFFINITY_FOR_CROWS" in current_team_attrs and game["weather"] == bird_weather:
            new_row = adjust_by_pct(new_row, 0.50, PITCHING_STLATS, blaseball_stat_csv.pitching_stars)
            new_row = adjust_by_pct(new_row, 0.50, BATTING_STLATS, blaseball_stat_csv.batting_stars)
    return new_row


def load_stat_data(filepath, schedule=None, day=None, team_attrs=None):
    with open(filepath) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    games = {}
    if schedule:
        games.update({game["homeTeamName"]: game for game in schedule})
        games.update({game["awayTeamName"]: game for game in schedule})
    pitcherstatdata = collections.defaultdict(lambda: {})
    teamstatdata = collections.defaultdict(lambda: collections.defaultdict(lambda: []))
    for row in filedata:
        team = row["team"]
        if games:
            game = games.get(team)
            new_row = adjust_stlats(row, game, day, team_attrs)
        else:
            new_row = row
        if new_row["position"] == "rotation":
            for key in (PITCHING_STLATS + ["pitchingStars"]):
                pitcherstatdata[new_row["name"]][key] = float(new_row[key])
        elif new_row["position"] == "lineup":
            if "SHELLED" not in new_row["permAttr"]:
                for key in (BATTING_STLATS + BASERUNNING_STLATS + ["battingStars", "baserunningStars"]):
                    teamstatdata[team][key].append(float(new_row[key]))
            for key in (DEFENSE_STLATS + ["defenseStars"]):
                teamstatdata[team][key].append(float(new_row[key]))
    return teamstatdata, pitcherstatdata


def get_player_slug(playername):
    playerslug = playername.lower().replace(" ", "-")
    playerslug = BR_PLAYERNAME_SUBS.get(playerslug, playerslug)
    return playerslug


def get_all_pitcher_performance_stats(pitcher_ids, season):
    if not pitcher_ids:
        return {}
    url = ("https://api.blaseball-reference.com/v1/playerStats?category=pitching&season={}&playerIds={}"
           "").format(season, ",".join(pitcher_ids))
    response = requests.get(url)
    resjson = response.json()
    return {pitcher["player_id"]: pitcher for pitcher in resjson}


def calc_star_max_mean_stats(pitcher, defenseteamname, offenseteamname, team_stat_data, pitcher_stat_data):
    pitchingstars = pitcher_stat_data[pitcher]["pitchingStars"]
    maxbatstars = max(team_stat_data[offenseteamname]["battingStars"])
    meanbatstars = geomean(team_stat_data[offenseteamname]["battingStars"])
    maxdefstars = max(team_stat_data[defenseteamname]["defenseStars"])
    meandefstars = geomean(team_stat_data[defenseteamname]["defenseStars"])
    maxrunstars = max(team_stat_data[offenseteamname]["baserunningStars"])
    meanrunstars = geomean(team_stat_data[offenseteamname]["baserunningStars"])
    return StarData(pitchingstars, maxbatstars, meanbatstars, maxdefstars, meandefstars, maxrunstars, meanrunstars)


def calc_stlat_stats(pitcher, pitcherteamname, offenseteamname, team_stat_data, pitcher_stat_data):
    stlatdata = {stlat: pitcher_stat_data[pitcher][stlat] for stlat in PITCHING_STLATS}
    for stlat in DEFENSE_STLATS:
        stlatdata["mean{}".format(stlat.lower())] = geomean(team_stat_data[pitcherteamname][stlat])
        stlatdata["max{}".format(stlat.lower())] = max(team_stat_data[pitcherteamname][stlat])
    for stlat in BATTING_STLATS + BASERUNNING_STLATS:
        stlatdata["mean{}".format(stlat.lower())] = geomean(team_stat_data[offenseteamname][stlat])
        stlatdata["max{}".format(stlat.lower())] = max(team_stat_data[offenseteamname][stlat])
    for stlat in INVERSE_STLATS:  # change this if there are any non-batting inverse stlats
        stlatdata["min{}".format(stlat.lower())] = min(team_stat_data[offenseteamname][stlat])
    return stlatdata


def get_dict_from_matchupdata(matchup, season_number, day):
    return {"Pitcher Name": matchup.pitchername, "Season": season_number, "Day": day,
            "SO9": matchup.so9, "ERA": matchup.era, "Opposing Team": matchup.vsteam,
            "D/O": matchup.defoff, "Game ID": matchup.gameid, "Pitcher ID": matchup.pitcherid,
            "Pitching Stars": matchup.stardata.pitchingstars, "Max Batting": matchup.stardata.maxbatstars,
            "Mean Batting": matchup.stardata.meanbatstars, "Max Defense": matchup.stardata.maxdefstars,
            "Mean Defense": matchup.stardata.meandefstars, "Max Baserunning": matchup.stardata.maxrunstars,
            "Mean Baserunning": matchup.stardata.meanrunstars, "Ball Count": matchup.ballcount,
            "Strike Count": matchup.strikecount, "Base Count": matchup.basecount}


def insert_into_airtable(results, season_number, day):
    airtable = Airtable(os.getenv("AIRTABLE_BASE_KEY"), os.getenv("AIRTABLE_TABLE_NAME"), os.getenv("AIRTABLE_API_KEY"))
    airtable.batch_insert([get_dict_from_matchupdata(matchup, season_number, day) for matchup in results])


def process_game(game, team_stat_data, pitcher_stat_data, pitcher_performance_stats, day):
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
    awayStlatStats = calc_stlat_stats(awayPitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data)
    homeStlatStats = calc_stlat_stats(homePitcher, homeTeam, awayTeam, team_stat_data, pitcher_stat_data)
    homeTIM, homeTIMRank, homeTIMCalc = tim.calculate(homeStlatStats)
    awayTIM, awayTIMRank, awayTIMCalc = tim.calculate(awayStlatStats)
    awayAttrs, homeAttrs = get_team_attributes()[awayTeam], get_team_attributes()[homeTeam]
    awayMOFO, homeMOFO = mofo.calculate(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, awayAttrs, homeAttrs, day, game["weather"])
    awayK9 = k9.calculate(awayPitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data)
    homeK9 = k9.calculate(homePitcher, homeTeam, awayTeam, team_stat_data, pitcher_stat_data)
    results.append(MatchupData(awayPitcher, awayPitcherId, awayTeam, gameId,
                               float(awayPitcherStats.get("k_per_9", -1.0)), float(awayPitcherStats.get("era", -1.0)),
                               awayEmoji, homeTeam, homeEmoji,
                               get_def_off_ratio(awayPitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data),
                               awayTIM, awayTIMRank, awayTIMCalc, awayStarStats, game.get("homeBalls", 4),
                               game["homeStrikes"], game["homeBases"], game["awayTeamNickname"],
                               game["homeTeamNickname"], game["awayOdds"], awayMOFO, awayK9))
    results.append(MatchupData(homePitcher, homePitcherId, homeTeam, gameId,
                               float(homePitcherStats.get("k_per_9", -1.0)), float(homePitcherStats.get("era", -1.0)),
                               homeEmoji, awayTeam, awayEmoji,
                               get_def_off_ratio(homePitcher, homeTeam, awayTeam, team_stat_data, pitcher_stat_data),
                               homeTIM, homeTIMRank, homeTIMCalc, homeStarStats, game.get("awayBalls", 4),
                               game["awayStrikes"], game["awayBases"], game["homeTeamNickname"],
                               game["awayTeamNickname"], game["homeOdds"], homeMOFO, homeK9))
    return results


def run_lineup_file_mode(filepath, team_stat_data, pitcher_stat_data, stat_season_number):
    with open(filepath, "r") as json_file:
        json_data = json.load(json_file)
        all_pitcher_ids = [matchup["awayPitcherId"] for matchup in json_data] + [matchup["homePitcherId"] for matchup in json_data]
        pitcher_performance_stats = get_all_pitcher_performance_stats(all_pitcher_ids, stat_season_number)
        fmtstr = ("{} ({}, {} K9, {:.2f} SO9, {:.2f} ERA) vs. {} ({:.2f} OppMeanBat*, {:.2f} OppMaxBat),"
                  " {:.2f} D/O^2, {:.2f}% MOFO")
        for matchup in json_data:
            awayMOFO, homeMOFO = mofo.calculate(matchup["awayPitcherName"], matchup["homePitcherName"],
                                                matchup["awayTeam"], matchup["homeTeam"], team_stat_data,
                                                pitcher_stat_data)
            awayresult = process_pitcher_vs_team(matchup["awayPitcherName"], matchup["awayPitcherId"],
                                                 matchup["awayTeam"], matchup["homeTeam"], team_stat_data,
                                                 pitcher_stat_data, pitcher_performance_stats)
            print(fmtstr.format(awayresult.pitchername, awayresult.tim.name, awayresult.k9, awayresult.so9,
                                awayresult.era, awayresult.vsteam, awayresult.stardata.meanbatstars,
                                awayresult.stardata.maxbatstars, awayresult.defoff, awayMOFO*100.0))
            homeresult = process_pitcher_vs_team(matchup["homePitcherName"], matchup["homePitcherId"],
                                                 matchup["homeTeam"], matchup["awayTeam"], team_stat_data,
                                                 pitcher_stat_data, pitcher_performance_stats)
            print(fmtstr.format(homeresult.pitchername, homeresult.tim.name, homeresult.k9, homeresult.so9,
                                homeresult.era, homeresult.vsteam, homeresult.stardata.meanbatstars,
                                homeresult.stardata.maxbatstars, homeresult.defoff, homeMOFO*100.0))


def process_pitcher_vs_team(pitcherName, pitcherId, pitcherTeam, otherTeam, team_stat_data, pitcher_stat_data,
                            pitcher_performance_stats):
    pitcherStats = pitcher_performance_stats.get(pitcherId, {})
    starStats = calc_star_max_mean_stats(pitcherName, pitcherTeam, otherTeam, team_stat_data, pitcher_stat_data)
    stlatStats = calc_stlat_stats(pitcherName, pitcherTeam, otherTeam, team_stat_data, pitcher_stat_data)
    timTier, timRank, timCalc = tim.calculate(stlatStats)
    pitcherk9 = k9.calculate(pitcherName, pitcherTeam, otherTeam, team_stat_data, pitcher_stat_data)
    return MatchupData(pitcherName, None, None, None, float(pitcherStats.get("k_per_9", -1.0)),
                       float(pitcherStats.get("era", -1.0)), None, otherTeam, None,
                       get_def_off_ratio(pitcherName, pitcherTeam, otherTeam, team_stat_data, pitcher_stat_data),
                       timTier, timRank, timCalc, starStats, 4, 3, 4, None, None, None, -1, pitcherk9)


def sort_results(results):
    return sorted(results, key=lambda result: (result.timrank, result.k9, result.mofoodds), reverse=True)


def get_score_adjustments(is_today, today_schedule, tomorrow_schedule):
    score_adjustments = collections.defaultdict(lambda: [])
    allTeams = requests.get("https://blaseball.com/database/allTeams").json()
    teamAttrs = {team['fullName']: (team['gameAttr'] + team['weekAttr'] + team['seasAttr'] + team['permAttr']) for team in allTeams}
    if not is_today:  # can't check for targeted shame without both today and tomorrow schedules
        shameable_teams = set([team for team, attrs in teamAttrs.items() if 'SHAME_PIT' in attrs])
        if shameable_teams:
            for game in today_schedule:
                if game['shame'] and game["awayTeamName"] in shameable_teams:
                    score_adjustments[game["awayTeamName"]].append(ScoreAdjustment(game["awayScore"] - game["homeScore"], "Shame"))
    hfa_teams = set([team for team, attrs in teamAttrs.items() if 'HOME_FIELD' in attrs])
    if hfa_teams:
        for game in tomorrow_schedule:
            if game["homeTeamName"] in hfa_teams:
                score_adjustments[game["homeTeamName"]].append(ScoreAdjustment(1, "Home Field Advantage"))
    return score_adjustments


def outcome_matters(outcome):
    return all(s not in outcome for s in ("is now Unstable", "is now Flickering", "Red Hot", "is now Repeating",
                                          "Black Hole swallowed a Win", "Sun 2 set a Win upon"))


def already_ran_for_day(filepath, season_number, day):
    if os.path.isfile(filepath):
        with open(filepath, "r") as f:
            file_season_number, file_day = (int(n) for n in f.read().split("-"))
            return file_season_number == season_number and file_day == day
    return False


def write_day(filepath, season_number, day):
    with open(filepath, "w") as f:
        f.write("{}-{}".format(season_number, day))


def print_results(day, results, score_adjustments):
    print("Day {}".format(day))
    odds_mismatch = []
    for result in sort_results(results):
        print(("{} ({}, {} K9, {:.2f} SO9, {:.2f} ERA) vs. {} ({:.2f} OppMeanBat*, {:.2f} OppMaxBat), {:.2f} D/O^2, {:.2f}% WSO, {:.2f}% MOFO"
               "").format(result.pitchername, result.tim.name, result.k9, result.so9, result.era, result.vsteam,
                          result.stardata.meanbatstars, result.stardata.maxbatstars, result.defoff,
                          result.websiteodds*100.0, result.mofoodds*100.0))
        for team in (result.pitcherteam, result.vsteam):
            if team in score_adjustments:
                for score_adjustment in score_adjustments[team]:
                    print("-- {} {}: {}{}".format(team, score_adjustment.label,
                                                  "+" if score_adjustment.score > 0 else "",
                                                  score_adjustment.score))
        if (result.mofoodds > .5 and result.websiteodds < .5) or (.495 <= result.websiteodds < .505 and result.mofoodds >= .5):
            odds_mismatch.append(result)
    if odds_mismatch:
        print("Odds Mismatches")
        print("\n".join(("{} vs {} - Website: {} {:.2f}%, MOFO: {} {:.2f}%".format(result.pitcherteamnickname, result.vsteamnickname, result.vsteamnickname, (1-result.websiteodds)*100.0, result.pitcherteamnickname, result.mofoodds*100.0)) for result in odds_mismatch))


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
    parser.add_argument('--env', help="path to .env file, defaults to .env in same directory")
    args = parser.parse_args()
    if not args.print and not args.discord and not args.airtable and not args.discordprint and not args.lineupfile:
        print("No output specified")
        parser.print_help()
        sys.exit(-1)
    return args


def main():
    args = handle_args()
    load_dotenv(dotenv_path=args.env)
    if args.testfile:
        streamdata = load_test_data(args.testfile)
    else:
        streamdata = get_stream_snapshot()
    season_number = streamdata['value']['games']['season']['seasonNumber']  # 0-indexed
    day = streamdata['value']['games']['sim']['day'] + (1 if args.today else 2)  # 0-indexed, make 1-indexed and add another if tomorrow
    if already_ran_for_day(args.dayfile, season_number, day) and not args.forcerun and not args.lineupfile:
        print("Already ran for Season {} Day {}, exiting.".format(season_number+1, day))
        sys.exit(0)
    today_schedule = streamdata['value']['games']['schedule']
    games_complete = False
    retry_count = int(os.getenv("RETRY_COUNT", 10))
    show_waiting_message = int(os.getenv("SHOW_WAITING_MESSAGE", 1))
    sleep_interval = int(os.getenv("WAIT_INTERVAL", 30))
    if not args.today and not args.forcerun and not args.testfile and retry_count > 0:
        first_try = True
        for _ in range(retry_count):
            games_complete = all([game["finalized"] for game in today_schedule])
            is_postseason = any([game["isPostseason"] for game in today_schedule])
            keep_trying = (not games_complete or (is_postseason and not args.today and not streamdata['value']['games']['tomorrowSchedule']))
            if keep_trying and first_try:
                total_seconds = sleep_interval * retry_count
                if show_waiting_message:
                    message = "Waiting up to {} minute{} {}for current games to end."
                    message = message.format(total_seconds // 60, "" if total_seconds // 60 == 1 else "s",
                                             "{} seconds ".format(total_seconds % 60) if total_seconds % 60 else "")
                    if args.discord:
                        send_discord_message("Sorry!", message)
                    else:
                        print(message)
                first_try = False
            elif not keep_trying:
                break
            time.sleep(sleep_interval)
            streamdata = get_stream_snapshot()
            today_schedule = streamdata['value']['games']['schedule']
        if not games_complete:
            message = "Running even though games aren't complete, watch out!"
            if args.discord:
                send_discord_message("Warning!", message)
            else:
                print(message)
    stat_season_number = (season_number - 1) if day < LAST_SEASON_STAT_CUTOFF else season_number
    game_schedule = today_schedule if args.today else streamdata['value']['games']['tomorrowSchedule']
    if not game_schedule and not args.lineupfile:
        print("No games found for Season {} Day {}, exiting.".format(season_number+1, day))
        sys.exit(0)
    all_pitcher_ids = []
    for game in game_schedule:
        all_pitcher_ids.extend((game["awayPitcher"], game["homePitcher"]))
    all_pitcher_ids = [pid for pid in all_pitcher_ids if pid]
    if not all_pitcher_ids and not args.lineupfile:
        print("No pitchers assigned to games on Season {} Day {}, exiting.".format(season_number + 1, day))
        sys.exit(0)
    outcomes = [outcome for game in streamdata['value']['games']['schedule'] if game["outcomes"] for outcome in game['outcomes'] if outcome_matters(outcome)]
    stat_file_exists = os.path.isfile(args.statfile)
    if (outcomes or not stat_file_exists or args.forceupdate or ((day == 1 and args.today) or day == 2)) and not args.skipupdate:
        if args.discord:
            message = "Generating new stat file, please stand by.\n\n{}".format("\n".join("`{}`".format(outcome) for outcome in outcomes))
            send_discord_message("Sorry!", message[:DISCORD_SPLIT_LIMIT])
        else:
            print("Generating new stat file, please stand by.")
        blaseball_stat_csv.generate_file(args.statfile, False, args.archive, False)
    team_stat_data, pitcher_stat_data = load_stat_data(args.statfile, game_schedule, day)
    if args.lineupfile:
        run_lineup_file_mode(args.lineupfile, team_stat_data, pitcher_stat_data, stat_season_number)
        sys.exit(0)
    results, pair_results = [], []
    score_adjustments = get_score_adjustments(args.today, streamdata['value']['games']['schedule'],
                                              streamdata['value']['games']['tomorrowSchedule'])
    pitcher_performance_stats = get_all_pitcher_performance_stats(all_pitcher_ids, stat_season_number)
    for game in game_schedule:
        awayMatchupData, homeMatchupData = process_game(game, team_stat_data, pitcher_stat_data,
                                                        pitcher_performance_stats, day)
        results.extend((awayMatchupData, homeMatchupData))
        pair_results.append(MatchupPair(awayMatchupData, homeMatchupData))
    if pair_results:
        so9_pitchers = {res.pitchername for res in sorted(results, key=lambda res: res.so9, reverse=True)[:5]}
        k9_min = sorted(results, key=lambda res: res.k9, reverse=True)[min(len(results)-1, 4)].k9
        k9_pitchers = {res.pitchername for res in results if res.k9 >= k9_min}
        if args.discord:
            send_matchup_data_to_discord_webhook(day, pair_results, so9_pitchers, k9_pitchers, score_adjustments)
        if args.discordprint:
            send_matchup_data_to_discord_webhook(day, pair_results, so9_pitchers, k9_pitchers, score_adjustments, screen=True)
        if args.airtable:
            insert_into_airtable(results, season_number+1, day)
        if args.print:
            print_results(day, results, score_adjustments)
    else:
        print("No results")
    write_day(args.dayfile, season_number, day)


if __name__ == "__main__":
    main()
