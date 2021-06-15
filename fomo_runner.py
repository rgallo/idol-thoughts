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

import helpers
import fomo
from helpers import geomean, get_weather_idx
from helpers import PITCHING_STLATS, BATTING_STLATS, DEFENSE_STLATS, BASERUNNING_STLATS, INVERSE_STLATS


FOMOPair = namedtuple("FOMOPair", ["awayFOMOData", "homeFOMOData"])


def get_formatted_odds(away_odds, home_odds):
    formatted_away_odds = "{:.2f}%".format(away_odds*100.0)
    formatted_home_odds = "{:.2f}%".format(home_odds*100.0)
    if away_odds < home_odds:
        formatted_away_odds = "~~{}~~".format(formatted_away_odds)
    elif home_odds < away_odds:
        formatted_home_odds = "~~{}~~".format(formatted_home_odds)
    return formatted_away_odds, formatted_home_odds

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


def get_team_attributes(attributes={}):
    if not attributes:
        attributes.update({team["fullName"]: (team["gameAttr"] + team["weekAttr"] + team["seasAttr"] + team["permAttr"]) for team in requests.get("https://www.blaseball.com/database/allTeams").json()})
    return attributes


FOMOData = namedtuple("FOMOData", ["pitchername", "pitcherid", "pitcherteam", "gameid", "defemoji", "vsteam",
                                   "offemoji", "pitcherteamnickname", "vsteamnickname", "websiteodds", "fomoodds"])


def process_fomo(game, team_stat_data, pitcher_stat_data, day):
    results = []
    gameId = game["id"]
    awayPitcher, homePitcher = game["awayPitcherName"], game["homePitcherName"]
    awayPitcherId, homePitcherId = game["awayPitcher"], game["homePitcher"]
    awayTeam, homeTeam = game["awayTeamName"], game["homeTeamName"]
    awayEmoji, homeEmoji = game['awayTeamEmoji'], game['homeTeamEmoji']
    awayAttrs, homeAttrs = get_team_attributes()[awayTeam], get_team_attributes()[homeTeam]
    awayFOMO, homeFOMO = fomo.calculate(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, awayAttrs, homeAttrs, day, game["weather"])
    results.append(FOMOData(awayPitcher, awayPitcherId, awayTeam, gameId, awayEmoji, homeTeam, homeEmoji,
                               game["awayTeamNickname"], game["homeTeamNickname"], game["awayOdds"], awayFOMO))
    results.append(FOMOData(homePitcher, homePitcherId, homeTeam, gameId, homeEmoji, awayTeam, awayEmoji,
                               game["homeTeamNickname"], game["awayTeamNickname"], game["homeOdds"], homeFOMO))
    return results


def sort_results(results, keyattr="fomoodds"):
    return sorted(results,
                  key=lambda pair: max(getattr(pair.awayFOMOData, keyattr), getattr(pair.homeFOMOData, keyattr)),
                  reverse=True)


def get_payout_bonuses(player_ids):
    credits_to_the_team, double_payouts = set(), set()
    player_data = requests.get("https://www.blaseball.com/database/players?ids={}".format(",".join(player_ids))).json()
    for player in player_data:
        all_attrs = player["permAttr"] + player["seasAttr"] + list(player["state"].get("itemModSources", {}).keys())
        if "CREDIT_TO_THE_TEAM" in all_attrs:
            credits_to_the_team.add(player["id"])
        if "DOUBLE_PAYOUTS" in all_attrs:
            double_payouts.add(player["id"])
    return credits_to_the_team, double_payouts


def print_pitcher(pitcher, fomo_error):
    print(f"{pitcher.pitchername} ({pitcher.pitcherteamnickname}, "
          f"FOMO {((pitcher.fomoodds - fomo_error) * 100.0):.2f}% - {((pitcher.fomoodds + fomo_error) * 100.0):.2f}%, "
          f"Webodds {(pitcher.websiteodds * 100.0):.2f}%")


def print_fomo(day, best, worst, fomo_error):
    print("Day {}".format(day))
    print("Best:")
    for pitcher in best:
        print_pitcher(pitcher, fomo_error)
    print("\nWorst:")
    for pitcher in worst:
        print_pitcher(pitcher, fomo_error)


def get_games_to_output(pair_results, fomo_error):
    best, worst = [], []
    webodds_sorted_results = sort_results(pair_results, "websiteodds")
    top_webodds_game_id = webodds_sorted_results[0].awayFOMOData.gameid
    fomo_sorted_results = sort_results(pair_results, "fomoodds")
    fomo_top_game = fomo_sorted_results[0]
    min_fomo = max(fomo_top_game.awayFOMOData.fomoodds, fomo_top_game.homeFOMOData.fomoodds) - fomo_error
    for pair in fomo_sorted_results:
        if (pair.awayFOMOData.gameid == top_webodds_game_id or max(pair.awayFOMOData.fomoodds, pair.homeFOMOData.fomoodds) > min_fomo):
            if pair.awayFOMOData.fomoodds >= .5:
                best.append(pair.awayFOMOData)
                worst.append(pair.homeFOMOData)
            else:
                best.append(pair.homeFOMOData)
                worst.append(pair.awayFOMOData)
    return best, worst


def main():
    args = helpers.handle_args()
    load_dotenv(dotenv_path=args.env)
    game_schedule, streamdata, season_number, day, all_pitcher_ids, team_stat_data, team_pid_stat_data, pitcher_stat_data = helpers.do_init(args)
    pair_results = []
    for game in game_schedule:
        awayFOMO, homeFOMO = process_fomo(game, team_stat_data, pitcher_stat_data, day)
        pair_results.append(FOMOPair(awayFOMO, homeFOMO))
    if pair_results:
        fomo_error = float(list(helpers.load_data(os.getenv("FOMO_ERROR")).keys())[0]) / 100.0
        best, worst = get_games_to_output(pair_results, fomo_error)
        if args.discord:
            output_fomo_to_discord(day, best, worst, fomo_error)
        if args.discordprint:
            output_fomo_to_discord(day, best, worst, fomo_error, screen=True)
        if args.print:
            print_fomo(day, best, worst, fomo_error)
    else:
        print("No results")
    if not args.justlooking:
        helpers.write_day(args.dayfile, season_number, day)


if __name__ == "__main__":
    main()
