from __future__ import division
from __future__ import print_function

import collections
import operator
import os
import time
from collections import namedtuple

import requests
from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv

import batman
import helpers
import k9
import tim
import mofo
from helpers import geomean, get_weather_idx
from helpers import PITCHING_STLATS, BATTING_STLATS, DEFENSE_STLATS, BASERUNNING_STLATS, INVERSE_STLATS


MatchupData = namedtuple("MatchupData", ["pitchername", "pitcherid", "pitcherteam", "gameid", "so9", "era", "defemoji",
                                         "vsteam", "offemoji", "defoff", "tim", "timrank", "timcalc",
                                         "stardata", "ballcount", "strikecount", "basecount", "pitcherteamnickname",
                                         "vsteamnickname", "websiteodds", "mofoodds", "k9", "weather"])

MatchupPair = namedtuple("MatchupPair", ["awayMatchupData", "homeMatchupData"])

StarData = namedtuple("StarData", ["pitchingstars", "maxbatstars", "meanbatstars", "maxdefstars", "meandefstars", 
                                   "maxrunstars", "meanrunstars"])

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
DISCORD_RESULT_PER_BATCH = 2


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


def webodds_payout(odds, amt):
    if odds == .5:
        return 2 * amt
    if odds < .5:
        return amt * (2 + (.0015 * ((100 * (.5 - odds)) ** 2.2)))
    else:
        return amt * (3.206 / (1 + ((.443 * (odds - .5)) ** .95)) - 1.206)


def get_ev(awayMatchupData, homeMatchupData, loser=False):
    op = operator.gt if not loser else operator.le
    mofoodds, webodds = (awayMatchupData.mofoodds, awayMatchupData.websiteodds) if op(awayMatchupData.mofoodds, homeMatchupData.mofoodds) else (homeMatchupData.mofoodds, homeMatchupData.websiteodds)
    payout = webodds_payout(webodds, 1.0)
    return payout * min(mofoodds, 0.8)


def send_matchup_data_to_discord_webhook(day, matchup_pairs, so9_pitchers, k9_pitchers, score_adjustments, screen=False):
    Webhook, Embed = (helpers.PrintWebhook, helpers.PrintEmbed) if screen else (DiscordWebhook, DiscordEmbed)
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL").split(";")
    notify_tim_rank, notify_role = os.getenv("NOTIFY_TIM_RANK"), os.getenv("NOTIFY_ROLE")
    siesta_notify_role = os.getenv("SIESTA_NOTIFY_ROLE")
    sortkey = lambda matchup_pair: (max(matchup_pair.awayMatchupData.timrank, matchup_pair.homeMatchupData.timrank),
                                    max(matchup_pair.awayMatchupData.k9, matchup_pair.homeMatchupData.k9),
                                    max(matchup_pair.awayMatchupData.mofoodds, matchup_pair.homeMatchupData.mofoodds))
    sorted_pairs = sorted(matchup_pairs, key=sortkey, reverse=True)
    batches = len(matchup_pairs)
    sun2weather, bhweather = get_weather_idx("Sun 2"), get_weather_idx("Black Hole")
    webhooks = [Webhook(url=discord_webhook_url,
                        content="__**Day {}**__".format(day) if not batch else helpers.discord_hr(10, char='-')) for batch in range(batches)]
    odds_mismatch, notify, picks_to_click, not_your_dad, bad_bets = [], [], [], [], []
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
        ev = get_ev(awayMatchupData, homeMatchupData)
        loser_ev = get_ev(awayMatchupData, homeMatchupData, loser=True)
        if ev >= 1.0:
            picks_to_click.append(result)
        if loser_ev >= 1.0 and loser_ev >= ev:
            not_your_dad.append(result)
        if ev <= 1.0 and loser_ev <= 1.0:
            bad_bets.append(result)
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
    if picks_to_click:
        p2c_description = "\n".join(["{} @ {} - EV: {} {}".format(
            "**{}**".format(result.awayMatchupData.pitcherteamnickname) if result.awayMatchupData.mofoodds > result.homeMatchupData.mofoodds else result.awayMatchupData.pitcherteamnickname,
            "**{}**".format(result.homeMatchupData.pitcherteamnickname) if result.homeMatchupData.mofoodds > result.awayMatchupData.mofoodds else result.homeMatchupData.pitcherteamnickname,
            "{:.2f}".format(get_ev(result.awayMatchupData, result.homeMatchupData)),
            ":sunny:" if result.awayMatchupData.weather == sun2weather else ":cyclone:" if result.awayMatchupData.weather == bhweather else ""
        ) for result in sorted(picks_to_click, key=lambda result: get_ev(result.awayMatchupData, result.homeMatchupData), reverse=True)])
        results.append(helpers.send_discord_message("__Picks To Click__", p2c_description, screen=screen))
        time.sleep(.5)
    if not_your_dad:
        linyd_description = "\n".join(["{} @ {} - EV: {:.2f}, MOFO: {:.2f}% {}".format(
            "**{}**".format(result.awayMatchupData.pitcherteamnickname) if result.awayMatchupData.mofoodds < result.homeMatchupData.mofoodds else result.awayMatchupData.pitcherteamnickname,
            "**{}**".format(result.homeMatchupData.pitcherteamnickname) if result.homeMatchupData.mofoodds < result.awayMatchupData.mofoodds else result.homeMatchupData.pitcherteamnickname,
            get_ev(result.awayMatchupData, result.homeMatchupData, loser=True),
            min(result.awayMatchupData.mofoodds, result.homeMatchupData.mofoodds) * 100.0,
            ":sunny:" if result.awayMatchupData.weather == sun2weather else ":cyclone:" if result.awayMatchupData.weather == bhweather else ""
        ) for result in sorted(not_your_dad, key=lambda result: get_ev(result.awayMatchupData, result.homeMatchupData, loser=True), reverse=True)])
        results.append(helpers.send_discord_message("__Look, I'm Not Your Dad__", linyd_description, screen=screen))
        time.sleep(.5)
    if odds_mismatch:
        odds_description = "\n".join(["{} @ {} - Website: {} {:.2f}%, MOFO: **{}** {:.2f}% {}".format(
            "**{}**".format(result.awayMatchupData.pitcherteamnickname) if result.awayMatchupData.mofoodds > result.homeMatchupData.mofoodds else result.awayMatchupData.pitcherteamnickname,
            "**{}**".format(result.homeMatchupData.pitcherteamnickname) if result.homeMatchupData.mofoodds > result.awayMatchupData.mofoodds else result.homeMatchupData.pitcherteamnickname,
            result.awayMatchupData.pitcherteamnickname if result.awayMatchupData.websiteodds > result.homeMatchupData.websiteodds else result.homeMatchupData.pitcherteamnickname,
            (max(result.awayMatchupData.websiteodds, result.homeMatchupData.websiteodds)) * 100.0,
            result.awayMatchupData.pitcherteamnickname if result.awayMatchupData.mofoodds > result.homeMatchupData.mofoodds else result.homeMatchupData.pitcherteamnickname,
            (max(result.awayMatchupData.mofoodds, result.homeMatchupData.mofoodds)) * 100.0,
            ":sunny:" if result.awayMatchupData.weather == sun2weather else ":cyclone:" if result.awayMatchupData.weather == bhweather else "")
                                      for result in sorted(odds_mismatch, key=lambda result: max(result.awayMatchupData.websiteodds, result.homeMatchupData.websiteodds), reverse=True)])
        results.append(helpers.send_discord_message("__Odds Mismatches__", odds_description, screen=screen))
        time.sleep(.5)
    if bad_bets:
        bb_description = "\n".join(["{} @ {} - EV: {} {}".format(
            result.awayMatchupData.pitcherteamnickname, result.homeMatchupData.pitcherteamnickname, "{:.2f}".format(get_ev(result.awayMatchupData, result.homeMatchupData)),
            ":sunny:" if result.awayMatchupData.weather == sun2weather else ":cyclone:" if result.awayMatchupData.weather == bhweather else ""
        ) for result in sorted(bad_bets, key=lambda result: get_ev(result.awayMatchupData, result.homeMatchupData), reverse=True)])
        results.append(helpers.send_discord_message("__Bad Bets__", bb_description, screen=screen))
        time.sleep(.5)
    if notify:
        notify_message = "<@&{}> __**FIRE PICKS**__\n".format(notify_role)
        notify_message += "\n".join(["{}, {} - **{}**".format(matchup_data.pitchername, matchup_data.pitcherteamnickname,
                                                            matchup_data.tim.name) for matchup_data in notify])
        results.append(Webhook(url=discord_webhook_url, content=notify_message).execute())
    if siesta_notify_role and day in (28, 73):
        siesta_notify_message = "<@&{}> Siesta coming up!".format(siesta_notify_role)
        siesta_notify_message += "\nRemember to get your bets in before all the current games end!"
        results.append(Webhook(url=discord_webhook_url, content=siesta_notify_message).execute())
    return results


def get_def_off_ratio(pitcher, defenseteamname, offenseteamname, team_stat_data, pitcher_stat_data):
    pitchingstars = pitcher_stat_data[pitcher]["pitchingStars"]
    meandefstars = geomean(team_stat_data[defenseteamname]["defenseStars"])
    meanbatstars = geomean(team_stat_data[offenseteamname]["battingStars"])
    meanrunstars = geomean(team_stat_data[offenseteamname]["baserunningStars"])
    return (pitchingstars+meandefstars)/((meanbatstars+meanrunstars) ** 2)


def get_player_slug(playername):
    playerslug = playername.lower().replace(" ", "-")
    playerslug = BR_PLAYERNAME_SUBS.get(playerslug, playerslug)
    return playerslug


def get_all_pitcher_performance_stats(pitcher_ids, season):
    if not pitcher_ids:
        return {}
    url = ("https://api.blaseball-reference.com/v2/stats?group=pitching&type=season&season={}&gameType=R&playerIds={}"
           "").format(season, ",".join(pitcher_ids))
    try:
        response = requests.get(url)
        resjson = response.json()
        return {split["player"]["id"]: split["stat"] for split in resjson[0]["splits"]}
    except:
        return {}


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


def process_game(game, team_stat_data, pitcher_stat_data, pitcher_performance_stats, day, team_pid_stat_data):
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
    team_attributes = helpers.get_team_attributes()
    awayAttrs, homeAttrs = team_attributes[awayTeam], team_attributes[homeTeam]
    awayMOFO, homeMOFO = mofo.calculate(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, awayAttrs, homeAttrs, day, game["weather"])
    # noModAwayMOFO, noModHomeMOFO = mofo.calculate(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, awayAttrs, homeAttrs, day, game["weather"], skip_mods=True)
    # print("Away: {}, Modded MOFO: {}, Unmodded MOFO: {}".format(awayTeam, awayMOFO, noModAwayMOFO))
    # print("Home: {}, Modded MOFO: {}, Unmodded MOFO: {}".format(homeTeam, homeMOFO, noModHomeMOFO))
    awayK9 = k9.calculate(awayPitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data)
    homeK9 = k9.calculate(homePitcher, homeTeam, awayTeam, team_stat_data, pitcher_stat_data)
    # homeBatmans = batman.calculate(awayPitcher, awayTeam, homeTeam, team_pid_stat_data, pitcher_stat_data)
    # awayBatmans = batman.calculate(homePitcher, homeTeam, awayTeam, team_pid_stat_data, pitcher_stat_data)
    results.append(MatchupData(awayPitcher, awayPitcherId, awayTeam, gameId,
                               float(awayPitcherStats.get("strikeouts_per_9", -1.0)), float(awayPitcherStats.get("earned_run_average", -1.0)),
                               awayEmoji, homeTeam, homeEmoji,
                               get_def_off_ratio(awayPitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data),
                               awayTIM, awayTIMRank, awayTIMCalc, awayStarStats, game.get("homeBalls", 4),
                               game["homeStrikes"], game["homeBases"], game["awayTeamNickname"],
                               game["homeTeamNickname"], game["awayOdds"], awayMOFO, awayK9, game["weather"]))
    results.append(MatchupData(homePitcher, homePitcherId, homeTeam, gameId,
                               float(homePitcherStats.get("strikeouts_per_9", -1.0)), float(homePitcherStats.get("earned_run_average", -1.0)),
                               homeEmoji, awayTeam, awayEmoji,
                               get_def_off_ratio(homePitcher, homeTeam, awayTeam, team_stat_data, pitcher_stat_data),
                               homeTIM, homeTIMRank, homeTIMCalc, homeStarStats, game.get("awayBalls", 4),
                               game["awayStrikes"], game["awayBases"], game["homeTeamNickname"],
                               game["awayTeamNickname"], game["homeOdds"], homeMOFO, homeK9, game["weather"]))
    # return results, homeBatmans + awayBatmans
    return results, []


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


def get_payout_mult(player):
    return 5.0 if "CREDIT_TO_THE_TEAM" in player["attrs"] else 2.0 if "DOUBLE_PAYOUTS" in player["attrs"] else 1.0


def print_results(day, results, score_adjustments, batman_data):
    print("Day {}".format(day))
    odds_mismatch, picks_to_click, not_your_dad = [], [], []
    sun2weather, bhweather = get_weather_idx("Sun 2"), get_weather_idx("Black Hole")
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
        payout = webodds_payout(result.websiteodds, 1.0)
        if payout * min(result.mofoodds, 0.8) >= 1.0:
            if result.mofoodds >= .5:
                picks_to_click.append(result)
            else:
                not_your_dad.append(result)
    if picks_to_click:
        print("Picks To Click")
        print("\n".join(["{} - EV: {:.2f} {}".format(
            result.pitcherteamnickname, webodds_payout(result.websiteodds, 1.0) * min(result.mofoodds, 0.8),
            "(Sun 2)" if result.weather == sun2weather else "(Black Hole)" if result.weather == bhweather else ""
        ) for result in sorted(picks_to_click, key=lambda result: webodds_payout(result.websiteodds, 1.0) * min(result.mofoodds, 0.8), reverse=True)]))
    if not_your_dad:
        print("Look, I'm Not Your Dad")
        print("\n".join(["{} - EV: {:.2f}, MOFO {:.2f}% {}".format(
            result.pitcherteamnickname, webodds_payout(result.websiteodds, 1.0) * min(result.mofoodds, 0.8), result.mofoodds * 100.0,
            "(Sun 2)" if result.weather == sun2weather else "(Black Hole)" if result.weather == bhweather else ""
        ) for result in sorted(not_your_dad, key=lambda result: webodds_payout(result.websiteodds, 1.0) * min(result.mofoodds, 0.8), reverse=True)]))
    if odds_mismatch:
        print("Odds Mismatches")
        print("\n".join(("{} vs {} - Website: {} {:.2f}%, MOFO: {} {:.2f}%".format(result.pitcherteamnickname, result.vsteamnickname, result.vsteamnickname, (1-result.websiteodds)*100.0, result.pitcherteamnickname, result.mofoodds*100.0)) for result in sorted(odds_mismatch, key=lambda result: result.websiteodds)))
    if batman_data["hits"]:
        batman_hits = "\n".join(("{}, {}: {:.2f} hits, {:.2f} at bats").format(row["name"], row["team"], row["hits"], row["abs"]) for row in batman_data["hits"])
        batman_homers = "\n".join(("{}, {}: {:.2f} homers, {:.2f} at bats").format(row["name"], row["team"], row["homers"], row["abs"]) for row in batman_data["homers"])
        batman_combined = "\n".join(("{}, {}: {:.2f} hits, {:.2f} homers, {:.2f} at bats, {:.0f} max earnings").format(row["name"], row["team"], row["hits"], row["homers"], row["abs"], ((row["hits"] * 1500) + (row["homers"]*4000)) * get_payout_mult(row)) for row in batman_data["combined"])
        print("BATMAN:\nHits:\n{}\nHomers:\n{}\nCombined:\n{}".format(batman_hits, batman_homers, batman_combined))
        print("\n".join(("{}, {}: {:.2f} hits, {:.2f} homers, {:.2f} at bats, {:.0f} max earnings").format(row["name"], row["team"], row["hits"], row["homers"], row["abs"], ((row["hits"] * 1500) + (row["homers"]*4000)) * get_payout_mult(row)) for row in batman_data["york"]))


def main():
    args = helpers.handle_args()
    load_dotenv(dotenv_path=args.env)
    game_schedule, streamdata, season_number, day, all_pitcher_ids, team_stat_data, team_pid_stat_data, pitcher_stat_data = helpers.do_init(args)
    stat_season_number = (season_number - 1) if day < helpers.LAST_SEASON_STAT_CUTOFF else season_number
    results, pair_results = [], []
    score_adjustments = get_score_adjustments(args.today, streamdata['value']['games']['schedule'],
                                              streamdata['value']['games']['tomorrowSchedule'])
    pitcher_performance_stats = get_all_pitcher_performance_stats(all_pitcher_ids, stat_season_number)
    all_batmans = []
    for game in game_schedule:
        (awayMatchupData, homeMatchupData), batmans = process_game(game, team_stat_data, pitcher_stat_data,
                                                        pitcher_performance_stats, day, team_pid_stat_data)
        results.extend((awayMatchupData, homeMatchupData))
        pair_results.append(MatchupPair(awayMatchupData, homeMatchupData))
        all_batmans.extend(batmans)
    batman_data = {
        "hits": sorted(all_batmans, key=lambda x: x["hits"], reverse=True)[:5],
        "homers": sorted(all_batmans, key=lambda x: x["homers"], reverse=True)[:5],
        "combined": sorted(all_batmans, key=lambda x: ((x["homers"]*4000) + (x["hits"]*1500) * get_payout_mult(x)), reverse=True)[:5],
        "york": [x for x in all_batmans if x["name"] == "York Silk"]
    }
    if pair_results:
        so9_pitchers = {res.pitchername for res in sorted(results, key=lambda res: res.so9, reverse=True)[:5]}
        k9_min = sorted(results, key=lambda res: res.k9, reverse=True)[min(len(results)-1, 4)].k9
        k9_pitchers = {res.pitchername for res in results if res.k9 >= k9_min}
        if args.discord:
            send_matchup_data_to_discord_webhook(day, pair_results, so9_pitchers, k9_pitchers, score_adjustments)
        if args.discordprint:
            send_matchup_data_to_discord_webhook(day, pair_results, so9_pitchers, k9_pitchers, score_adjustments, screen=True)
        if args.print:
            print_results(day, results, score_adjustments, batman_data)
    else:
        print("No results")
    if not args.justlooking:
        helpers.write_day(args.dayfile, season_number, day)


if __name__ == "__main__":
    main()
