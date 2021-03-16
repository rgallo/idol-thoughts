import argparse
import json
import collections
import requests
from dotenv import load_dotenv
import sys
sys.path.append("..")

import mofonew as mofo
from idolthoughts import load_stat_data

from solvers import base_solver
from solvers.base_solver import pair_games, get_attrs_from_paired_games, get_schedule_from_paired_games, \
    get_pitcher_id_lookup, should_regen

def compare(season, mofo_list):
    mofogames = {}
    for game in mofo_list:
        teamname, gameid, othermofoodds, weather, homerbi, awayrbi = game
        if gameid not in mofogames:
            mofogames[gameid] = [teamname, 100-float(othermofoodds), float(othermofoodds), weather, homerbi, awayrbi]        
    mismatches = 0
    missing = 0
    moforight, webright, moforight_mismatch, webright_mismatch, totalgames, dadbets, webrightBHS, moforightBHS, bhsmismatches, mofoBHSmismatch, webBHSmismatch = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    mofomismatchpayouts, webmismatchpayouts, dadcash = 0.0, 0.0, 0.0
    games = requests.get("https://api.sibr.dev/chronicler/v1/games?order=desc&season={}".format(season-1)).json()["data"]
    bhsuns, flippedgames = 0, 0
    for game in games:
        gameid = game["gameId"]
        gamedata = game["data"]
        if not gamedata["finalized"]:
            continue
        if gameid not in mofogames:
            print("Game ID not in mofo games: {}".format(gameid))
            missing += 1
            continue
        else:
            totalgames += 1                
        changedAwayScore, changedHomeScore = 0.0, 0.0
        mofoteamname, mofoodds, othermofoodds, weather, homerbi, awayrbi = mofogames[gameid]        
        awayTeamName, homeTeamName = gamedata["awayTeamName"], gamedata["homeTeamName"]
        mofoIsAway = awayTeamName == mofoteamname
        awayOdds, homeOdds = gamedata["awayOdds"]*100.0, gamedata["homeOdds"]*100.0
        awayScore, homeScore = gamedata["awayScore"], gamedata["homeScore"]
        mofoCorrect = (mofoodds > 50 and ((mofoIsAway and awayScore > homeScore) or (not mofoIsAway and homeScore > awayScore))) or (mofoodds < 50 and ((mofoIsAway and awayScore < homeScore) or (not mofoIsAway and homeScore < awayScore)))
        webCorrect = (awayOdds > homeOdds and awayScore > homeScore) or (awayOdds < homeOdds and awayScore < homeScore)
        isdadbet = (min(mofoodds, othermofoodds) * webodds_payout((min(awayOdds, homeOdds)) / 100.0, 1)) > 1.0 and (min(mofoodds, othermofoodds) * webodds_payout((min(awayOdds, homeOdds)) / 100.0, 1)) > (max(mofoodds, othermofoodds) * webodds_payout((max(awayOdds, homeOdds)) / 100.0, 1))
        if isdadbet: 
            dadbets += 1
            if not mofoCorrect:
                dadcash += round(webodds_payout((min(awayOdds, homeOdds)) / 100.0, 1000))                
            else:
                dadcash -= 1000
        if mofoCorrect:
            moforight += 1            
        if webCorrect:
            webright += 1            
        if (mofoIsAway and ((awayOdds > 50 and mofoodds < 50) or (awayOdds < 50 and mofoodds > 50))) or (not mofoIsAway and ((homeOdds > 50 and mofoodds < 50) or (homeOdds < 50 and mofoodds > 50))):
            print("season {} day {}\nmofoteam: {}, awayteam: {}, hometeam: {}, mofo is away: {}\nmofoodds: {}, awayodds: {}, homeodds: {}\nawayscore: {}, homescore: {}".format(int(gamedata["season"])+1, int(gamedata["day"]+1), mofoteamname, awayTeamName, homeTeamName, mofoIsAway, mofoodds, awayOdds, homeOdds, awayScore, homeScore))
            mismatches += 1
            if mofoCorrect:
                moforight_mismatch += 1
                mofomismatchpayouts += round(webodds_payout((min(awayOdds, homeOdds)) / 100.0, 1000))
                print("Mofo correct\n----")
            else:
                webright_mismatch += 1
                webmismatchpayouts += round(webodds_payout((max(awayOdds, homeOdds)) / 100.0, 1000))
                print("web correct\n----")
        #checking Sun2 and BH
        if weather == 1 or weather == 14:
            print("Sun2/BH game unmodified score: {} - {}".format(awayScore, homeScore))
            if awayrbi >= 10 or homerbi >= 10:
                print("!!!!!! WEATHER TRIGGERED !!!!!!")
            bhsuns += 1            
            if (awayScore > homeScore and awayrbi < homerbi) or (homeScore > awayScore and homerbi < awayrbi):
                flippedgames += 1
                if (mofoIsAway and ((awayOdds > 50 and mofoodds < 50) or (awayOdds < 50 and mofoodds > 50))) or (not mofoIsAway and ((homeOdds > 50 and mofoodds < 50) or (homeOdds < 50 and mofoodds > 50))):
                    bhsmismatches += 1
                    if mofoCorrect:
                        mofoBHSmismatch += 1                                
                    else:
                        webBHSmismatch += 1
            if mofoCorrect:
                moforightBHS += 1
            if webCorrect:
                webrightBHS += 1                            
    print("missing games: {}, total counted games: {}".format(missing, len(mofogames)))
    #print("MOFO payout multiplier mismatches: {}".format(mofomismatchpayouts))
    #print("Web payout multiplier mismatches: {}".format(webmismatchpayouts))  
    print("BH/Sun2 flipped games: {}, total BH/Sun2 games: {}, {:.2f}% flipped".format(flippedgames, bhsuns, (flippedgames / bhsuns) * 100.0))
    print("BH/Sun2 flipped games mismatches: {}, MOFO correct: {} ({:.2f}%), Web correct: {} ({:.2f}%)".format(bhsmismatches, mofoBHSmismatch, (mofoBHSmismatch/bhsmismatches) * 100.0, webBHSmismatch, (webBHSmismatch/bhsmismatches)*100.0))
    print("BH/Sun2 games: {}, MOFO correct: {} ({:.2f}%), Web correct: {} ({:.2f}%)".format(bhsuns, moforightBHS, (moforightBHS/bhsuns) * 100.0, webrightBHS, (webrightBHS/bhsuns)*100.0))    
    print("MOFO mismatch profit margin: {:.4f} times maxbet per mismatch".format(((mofomismatchpayouts - webmismatchpayouts)/(mismatches)) / 1000.0))
    print("Dad cash: {:.4f} times maxbet per dadbet".format((dadcash / 1000.0) / dadbets))
    print("MOFO right: {}/{}, {:.2f}%".format(moforight, totalgames, (moforight/totalgames) * 100.0))
    print("Web right: {}/{}, {:.2f}%".format(webright, totalgames, (webright / totalgames) * 100.0))    
    print ("Total mismatches: {}, MOFO correct: {} ({:.2f}%), Web correct: {} ({:.2f}%)".format(mismatches, moforight_mismatch, (moforight_mismatch/mismatches) * 100.0, webright_mismatch, (webright_mismatch/mismatches)*100.0))


def get_mofo_list(game_list, team_attrs, stat_file_map, season):
    mofo_list = []
    season_team_attrs = team_attrs.get(str(season), {})
    pitchers, team_stat_data, pitcher_stat_data, last_stat_filename = None, None, None, None
    for day in range(1, 125):
        games = [row for row in game_list if row["season"] == str(season) and row["day"] == str(day)]
        paired_games = pair_games(games)
        schedule = get_schedule_from_paired_games(paired_games, season, day)
        day_mods = get_attrs_from_paired_games(season_team_attrs, paired_games)
        stat_filename = stat_file_map.get((season, day))
        if stat_filename:
            last_stat_filename = stat_filename
            pitchers = get_pitcher_id_lookup(stat_filename)
            team_stat_data, pitcher_stat_data = load_stat_data(stat_filename, schedule, day, season_team_attrs)
        elif should_regen(day_mods):
            pitchers = get_pitcher_id_lookup(last_stat_filename)
            team_stat_data, pitcher_stat_data = load_stat_data(last_stat_filename, schedule, day, season_team_attrs)
        for game in paired_games:
            away_game, home_game = game["away"], game["home"]
            awayPitcher, awayTeam = pitchers.get(away_game["pitcher_id"])
            homePitcher, homeTeam = pitchers.get(home_game["pitcher_id"])
            #if len(season_team_attrs.get(awayTeam, []) + season_team_attrs.get(homeTeam, [])) > 0:
                #continue
            away_odds, home_odds = mofo.calculate(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data,
                                                  pitcher_stat_data, season_team_attrs.get(awayTeam, []),
                                                  season_team_attrs.get(homeTeam, []), day, away_game["weather"])            
            mofo_list.append([homeTeam, game["away"]["game_id"], away_odds*100.0, int(game["away"]["weather"]), float(game["away"]["opposing_team_rbi"]), float(game["home"]["opposing_team_rbi"])])
    return mofo_list

def webodds_payout(odds, amt):
    if odds == .5:
        return 2 * amt
    if odds < .5:
        return amt * (2 + (.0015 * ((100 * (.5 - odds)) ** 2.2)))
    else:
        return amt * (3.206 / (1 + ((.443 * (odds - .5)) ** .95)) - 1.206) 

def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--statfolder', help="path to stat folder")
    parser.add_argument('--gamefile', help="path to game file")
    parser.add_argument('--season', help="print output")
    args = parser.parse_args()
    return args


def main():
    cmd_args = handle_args()
    load_dotenv(dotenv_path="../.env")
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    game_list = base_solver.get_games(cmd_args.gamefile)
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    season = int(cmd_args.season)
    mofo_list = get_mofo_list(game_list, team_attrs, stat_file_map, season)    
    compare(season, mofo_list)
    # print("Result fail rate: {:.2f}%".format(result_fail_rate*100.0))


if __name__ == "__main__":
    main()