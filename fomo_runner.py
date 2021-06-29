from __future__ import division
from __future__ import print_function

import os
from collections import namedtuple

import requests
from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv

import helpers
import fomo

FOMOData = namedtuple("FOMOData", ["pitchername", "pitcherid", "pitcherteam", "gameid", "defemoji", "vsteam",
                                   "offemoji", "pitcherteamnickname", "vsteamnickname", "websiteodds", "fomoodds",
                                   "ishome"])

FOMOPair = namedtuple("FOMOPair", ["awayFOMOData", "homeFOMOData"])


def output_fomo_to_discord(day, best, worst, fomo_error, pitchers, bonus_players, bonus_multiplier, mismatches, unidolable, fax_teams, pitcher_data, screen=False):
    Webhook, Embed = (helpers.PrintWebhook, helpers.PrintEmbed) if screen else (DiscordWebhook, DiscordEmbed)
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL").split(";")
    notify_role = os.getenv("NOTIFY_ROLE")
    webhook = Webhook(url=discord_webhook_url, content="__**Day {}**__".format(day))
    pitcher_attrs = {player['id']: helpers.get_player_attrs(player) for player in pitcher_data}
    if bonus_players:
        desc = f"<@&{notify_role}>\n"
        desc += "\n".join(f"[:rotating_light: :rotating_light: "
                          f"{pitchers[bonus_player]} has a {bonus_multiplier}x payout, go idol! "
                          f":rotating_light: :rotating_light:](https://www.blaseball.com/player/{bonus_player})"
                          f"" for bonus_player in bonus_players)
        webhook.add_embed(Embed(title="Bonus Payouts!", description=desc))
    for title, pitchers in (("Best", best), ("Worst", worst)):
        desc = "\n".join(f"{helpers.get_emoji(pitcher.defemoji)} **[{pitcher.pitchername}]"
                         f"(https://www.blaseball.com/player/{pitcher.pitcherid}), {pitcher.pitcherteamnickname}** "
                         f"(FOMO {((pitcher.fomoodds - fomo_error) * 100.0):.2f}% - {((pitcher.fomoodds + fomo_error) * 100.0):.2f}%, "
                         f"Webodds {(pitcher.websiteodds * 100.0):.2f}%)"
                         f"{' :fax:' if (pitcher.ishome and helpers.get_team_id(pitcher.pitcherteam) in fax_teams) else ''}"
                         f"{' :gloves:' if 'UNDERHANDED' in pitcher_attrs.get(pitcher.pitcherid) else ''}"
                         f"" for pitcher in pitchers if pitcher.pitcherid not in unidolable)
        webhook.add_embed(Embed(title=f"{title} Pitchers:", description=desc))
    if mismatches:
        odds_description = "\n".join(["{} @ {} - Website: {} {:.2f}%, FOMO: **{}** {:.2f}%".format(
            "**{}**".format(result.awayFOMOData.pitcherteamnickname) if result.awayFOMOData.fomoodds > result.homeFOMOData.fomoodds else result.awayFOMOData.pitcherteamnickname,
            "**{}**".format(result.homeFOMOData.pitcherteamnickname) if result.homeFOMOData.fomoodds > result.awayFOMOData.fomoodds else result.homeFOMOData.pitcherteamnickname,
            result.awayFOMOData.pitcherteamnickname if result.awayFOMOData.websiteodds > result.homeFOMOData.websiteodds else result.homeFOMOData.pitcherteamnickname,
            (max(result.awayFOMOData.websiteodds, result.homeFOMOData.websiteodds)) * 100.0,
            result.awayFOMOData.pitcherteamnickname if result.awayFOMOData.fomoodds > result.homeFOMOData.fomoodds else result.homeFOMOData.pitcherteamnickname,
            (max(result.awayFOMOData.fomoodds, result.homeFOMOData.fomoodds)) * 100.0)
                                      for result in sorted(mismatches, key=lambda result: max(result.awayFOMOData.websiteodds, result.homeFOMOData.websiteodds), reverse=True)])
        webhook.add_embed(Embed(title="FOMO Mismatches", description=odds_description))
    return webhook.execute()


def get_team_attributes(attributes={}):
    if not attributes:
        attributes.update({team["fullName"]: (team["gameAttr"] + team["weekAttr"] + team["seasAttr"] + team["permAttr"]) for team in requests.get("https://www.blaseball.com/database/allTeams").json()})
    return attributes


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
                            game["awayTeamNickname"], game["homeTeamNickname"], game["awayOdds"], awayFOMO, False))
    results.append(FOMOData(homePitcher, homePitcherId, homeTeam, gameId, homeEmoji, awayTeam, awayEmoji,
                            game["homeTeamNickname"], game["awayTeamNickname"], game["homeOdds"], homeFOMO, True))
    return results


def sort_results(results, keyattr="fomoodds"):
    return sorted(results,
                  key=lambda pair: max(getattr(pair.awayFOMOData, keyattr), getattr(pair.homeFOMOData, keyattr)),
                  reverse=True)


def get_payout_bonuses(player_data):
    credits_to_the_team, double_payouts = set(), set()
    for player in player_data:
        all_attrs = helpers.get_player_attrs(player)
        if "CREDIT_TO_THE_TEAM" in all_attrs:
            credits_to_the_team.add(player["id"])
        if "DOUBLE_PAYOUTS" in all_attrs:
            double_payouts.add(player["id"])
    return credits_to_the_team, double_payouts


def print_pitcher(pitcher, fomo_error):
    print(f"{pitcher.pitchername} ({pitcher.pitcherteamnickname}, "
          f"FOMO {((pitcher.fomoodds - fomo_error) * 100.0):.2f}% - {((pitcher.fomoodds + fomo_error) * 100.0):.2f}%, "
          f"Webodds {(pitcher.websiteodds * 100.0):.2f}%)")


def print_fomo(day, best, worst, fomo_error, pitchers, bonus_players, bonus_multiplier, mismatches, unidolable):
    print("Day {}".format(day))
    if bonus_players:
        for bonus_player in bonus_players:
            print(f"---{pitchers[bonus_player]} has a {bonus_multiplier}x payout, go idol!---")
    print("Best:")
    for pitcher in best:
        if pitcher.pitcherid not in unidolable:
            print_pitcher(pitcher, fomo_error)
    print("\nWorst:")
    for pitcher in worst:
        if pitcher.pitcherid not in unidolable:
            print_pitcher(pitcher, fomo_error)
    if mismatches:
        print("\nOdds Mismatches:")
        print("\n".join(["{} @ {} - Website: {} {:.2f}%, FOMO: {} {:.2f}%".format(result.awayFOMOData.pitcherteamnickname, result.homeFOMOData.pitcherteamnickname,
            result.awayFOMOData.pitcherteamnickname if result.awayFOMOData.websiteodds > result.homeFOMOData.websiteodds else result.homeFOMOData.pitcherteamnickname,
            (max(result.awayFOMOData.websiteodds, result.homeFOMOData.websiteodds)) * 100.0,
            result.awayFOMOData.pitcherteamnickname if result.awayFOMOData.fomoodds > result.homeFOMOData.fomoodds else result.homeFOMOData.pitcherteamnickname,
            (max(result.awayFOMOData.fomoodds, result.homeFOMOData.fomoodds)) * 100.0)
            for result in sorted(mismatches, key=lambda result: max(result.awayFOMOData.websiteodds, result.homeFOMOData.websiteodds), reverse=True)]))


def get_games_to_output(pair_results, fomo_error, unidolable, fax_teams):
    best, worst = [], []
    webodds_sorted_results = sort_results(pair_results, "websiteodds")
    top_webodds_game_id = webodds_sorted_results[0].awayFOMOData.gameid
    fomo_sorted_results = sort_results(pair_results, "fomoodds")
    fomo_top_game = fomo_sorted_results[0]
    min_fomo = max(fomo_top_game.awayFOMOData.fomoodds, fomo_top_game.homeFOMOData.fomoodds) - fomo_error
    output_enough = False
    gameids = set()
    for idx, pair in enumerate(fomo_sorted_results):
        if (pair.awayFOMOData.gameid == top_webodds_game_id or (max(pair.awayFOMOData.fomoodds, pair.homeFOMOData.fomoodds) + fomo_error) > min_fomo):
            if pair.awayFOMOData.pitcherid not in unidolable and pair.homeFOMOData.pitcherid not in unidolable and not (pair.homeFOMOData.ishome and helpers.get_team_id(pair.homeFOMOData.pitcherteam) in fax_teams):
                output_enough = True
            gameids.add(pair.awayFOMOData.gameid)
            if pair.awayFOMOData.fomoodds >= .5:
                best.append(pair.awayFOMOData)
                worst.append(pair.homeFOMOData)
            else:
                best.append(pair.homeFOMOData)
                worst.append(pair.awayFOMOData)
    if not output_enough:
        for pair in fomo_sorted_results:
            if pair.awayFOMOData.gameid not in gameids and pair.awayFOMOData.pitcherid not in unidolable and pair.homeFOMOData.pitcherid not in unidolable and not (pair.homeFOMOData.ishome and helpers.get_team_id(pair.homeFOMOData.pitcherteam) in fax_teams):
                if pair.awayFOMOData.fomoodds >= .5:
                    best.append(pair.awayFOMOData)
                    worst.append(pair.homeFOMOData)
                else:
                    best.append(pair.homeFOMOData)
                    worst.append(pair.awayFOMOData)
                break
    return best, worst


def get_bonus_players(player_data):
    players, bonus = None, 0
    credits_to_the_team, double_payouts = get_payout_bonuses(player_data)
    if credits_to_the_team & double_payouts:
        players, bonus = credits_to_the_team & double_payouts, 10
    elif credits_to_the_team:
        players, bonus = credits_to_the_team, 5
    elif double_payouts:
        players, bonus = double_payouts, 2
    return players, bonus


def get_unidolable(player_data):
    return [player["id"] for player in player_data if any(attr in ("NON_IDOLIZED", "COFFEE_EXIT", "STATIC", "LEGENDARY") for attr in helpers.get_player_attrs(player))]


def get_fax_teams():
    ballparks_url = os.getenv("BALLPARKS")
    ballparks = helpers.load_ballparks(ballparks_url)
    return {teamid for teamid, attrs in ballparks.items() if "FAX_MACHINE" in attrs["mods"]}


def main():
    args = helpers.handle_args()
    load_dotenv(dotenv_path=args.env)
    game_schedule, streamdata, season_number, day, all_pitcher_ids, team_stat_data, team_pid_stat_data, pitcher_stat_data = helpers.do_init(args)
    pair_results, pitchers = [], {}
    fax_teams = get_fax_teams()
    for game in game_schedule:
        awayFOMO, homeFOMO = process_fomo(game, team_stat_data, pitcher_stat_data, day)
        pitchers.update({awayFOMO.pitcherid: awayFOMO.pitchername, homeFOMO.pitcherid: homeFOMO.pitchername})
        pair_results.append(FOMOPair(awayFOMO, homeFOMO))
    if pair_results:
        mismatches = [pair for pair in pair_results if (pair.awayFOMOData.fomoodds < .5 < pair.awayFOMOData.websiteodds) or (pair.awayFOMOData.fomoodds > .5 > pair.awayFOMOData.websiteodds) or (.495 <= pair.awayFOMOData.websiteodds < .505)]
        player_data = requests.get("https://www.blaseball.com/database/players?ids={}".format(",".join(pitchers.keys()))).json()
        bonus_playerids, bonus_multiplier = get_bonus_players(player_data)
        unidolable = get_unidolable(player_data)
        fomo_error = float(list(helpers.load_data(os.getenv("FOMO_ERROR")).keys())[0]) / 100.0
        best, worst = get_games_to_output(pair_results, fomo_error, unidolable, fax_teams)
        if args.discord:
            output_fomo_to_discord(day, best, worst, fomo_error, pitchers, bonus_playerids, bonus_multiplier, mismatches, unidolable, fax_teams, player_data)
        if args.discordprint:
            output_fomo_to_discord(day, best, worst, fomo_error, pitchers, bonus_playerids, bonus_multiplier, mismatches, unidolable, fax_teams, player_data, screen=True)
        if args.print:
            print_fomo(day, best, worst, fomo_error, pitchers, bonus_playerids, bonus_multiplier, mismatches, unidolable)
    else:
        print("No results")
    if not args.justlooking:
        helpers.write_day(args.dayfile, season_number, day)


if __name__ == "__main__":
    main()
