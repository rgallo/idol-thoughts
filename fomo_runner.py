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
                                   "offemoji", "pitcherteamnickname", "vsteamnickname", "websiteodds", "fomoodds"])

FOMOPair = namedtuple("FOMOPair", ["awayFOMOData", "homeFOMOData"])


def output_fomo_to_discord(day, best, worst, fomo_error, pitchers, bonus_players, bonus_multiplier, screen=False):
    Webhook, Embed = (helpers.PrintWebhook, helpers.PrintEmbed) if screen else (DiscordWebhook, DiscordEmbed)
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL").split(";")
    notify_role = os.getenv("NOTIFY_ROLE")
    webhook = Webhook(url=discord_webhook_url, content="__**Day {}**__".format(day))
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
                         f"Webodds {(pitcher.websiteodds * 100.0):.2f}%)" for pitcher in pitchers)
        webhook.add_embed(Embed(title=f"{title} Pitchers:", description=desc))
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
          f"Webodds {(pitcher.websiteodds * 100.0):.2f}%)")


def print_fomo(day, best, worst, fomo_error, pitchers, bonus_players, bonus_multiplier):
    print("Day {}".format(day))
    if bonus_players:
        for bonus_player in bonus_players:
            print(f"---{pitchers[bonus_player]} has a {bonus_multiplier}x payout, go idol!---")
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
        if (pair.awayFOMOData.gameid == top_webodds_game_id or (max(pair.awayFOMOData.fomoodds, pair.homeFOMOData.fomoodds) + fomo_error) > min_fomo):
            if pair.awayFOMOData.fomoodds >= .5:
                best.append(pair.awayFOMOData)
                worst.append(pair.homeFOMOData)
            else:
                best.append(pair.homeFOMOData)
                worst.append(pair.awayFOMOData)
    return best, worst


def get_bonus_players(player_ids):
    players, bonus = None, 0
    credits_to_the_team, double_payouts = get_payout_bonuses(player_ids)
    if credits_to_the_team & double_payouts:
        players, bonus = credits_to_the_team & double_payouts, 10
    elif credits_to_the_team:
        players, bonus = credits_to_the_team, 5
    elif double_payouts:
        players, bonus = double_payouts, 2
    return players, bonus


def main():
    args = helpers.handle_args()
    load_dotenv(dotenv_path=args.env)
    game_schedule, streamdata, season_number, day, all_pitcher_ids, team_stat_data, team_pid_stat_data, pitcher_stat_data = helpers.do_init(args)
    pair_results, pitchers = [], {}
    for game in game_schedule:
        awayFOMO, homeFOMO = process_fomo(game, team_stat_data, pitcher_stat_data, day)
        pitchers.update({awayFOMO.pitcherid: awayFOMO.pitchername, homeFOMO.pitcherid: homeFOMO.pitchername})
        pair_results.append(FOMOPair(awayFOMO, homeFOMO))
    if pair_results:
        bonus_playerids, bonus_multiplier = get_bonus_players(pitchers.keys())
        fomo_error = float(list(helpers.load_data(os.getenv("FOMO_ERROR")).keys())[0]) / 100.0
        best, worst = get_games_to_output(pair_results, fomo_error)
        if args.discord:
            output_fomo_to_discord(day, best, worst, fomo_error, pitchers, bonus_playerids, bonus_multiplier)
        if args.discordprint:
            output_fomo_to_discord(day, best, worst, fomo_error, pitchers, bonus_playerids, bonus_multiplier, screen=True)
        if args.print:
            print_fomo(day, best, worst, fomo_error, pitchers, bonus_playerids, bonus_multiplier)
    else:
        print("No results")
    if not args.justlooking:
        helpers.write_day(args.dayfile, season_number, day)


if __name__ == "__main__":
    main()
