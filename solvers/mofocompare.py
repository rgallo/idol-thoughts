import argparse
import json
import collections
import requests
import os
from dotenv import load_dotenv
import sys
sys.path.append("..")

import mofo
import helpers
from idolthoughts import load_stat_data

from solvers import base_solver
from solvers.base_solver import pair_games, get_attrs_from_paired_games, get_schedule_from_paired_games, \
    get_pitcher_id_lookup, should_regen

def compare(byteam, season, mofo_list):
    mofogames = {}
    success_by_team = {}          
    mismatches, missing, unfinal = 0, 0, 0     
    moforight, webright, moforight_mismatch, webright_mismatch, totalgames, dadbets, webrightBHS, moforightBHS, bhsmismatches, mofoBHSmismatch, webBHSmismatch = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    mofomismatchpayouts, webmismatchpayouts, dadcash = 0.0, 0.0, 0.0
    games = requests.get("https://api.sibr.dev/chronicler/v1/games?order=desc&season={}".format(season-1)).json()["data"]
    for game in mofo_list:
        teamname, gameid, othermofoodds, weather, homerbi, awayrbi = game
        if gameid not in mofogames:
            mofogames[gameid] = [teamname, 100-float(othermofoodds), float(othermofoodds), weather, homerbi, awayrbi]  
    for game in mofogames:     
        gamefound = False
        for chrongame in games:
            if game == chrongame["gameId"]:
                gamefound = True
        if not gamefound:
            print("Game ID not in chronicler games: {}".format(game))        
    bhsuns, flippedgames = 0, 0
    for game in games:
        gameid = game["gameId"]
        gamedata = game["data"]
        if not gamedata["gameComplete"]:
            print("Game not complete! ID: {}".format(gameid))
            unfinal += 1
            continue
        if gameid not in mofogames:
            print("Game ID not in mofo games: {}".format(gameid))
            missing += 1
            continue            
        changedAwayScore, changedHomeScore = 0.0, 0.0
        mofoteamname, mofoodds, othermofoodds, weather, homerbi, awayrbi = mofogames[gameid]        
        awayTeamName, homeTeamName = gamedata["awayTeamName"], gamedata["homeTeamName"]
        #if awayTeamName == "Baltimore Crabs" or homeTeamName == "Baltimore Crabs":
         #   totalgames -= 1                
          #  continue
        mofoIsAway = awayTeamName == mofoteamname
        awayOdds, homeOdds = gamedata["awayOdds"]*100.0, gamedata["homeOdds"]*100.0
        awayScore, homeScore = gamedata["awayScore"], gamedata["homeScore"]
        #mofoCorrect = (mofoodds > 50 and ((mofoIsAway and awayScore > homeScore) or (not mofoIsAway and homeScore > awayScore))) or (mofoodds < 50 and ((mofoIsAway and awayScore < homeScore) or (not mofoIsAway and homeScore < awayScore)))
        #webCorrect = (awayOdds > homeOdds and awayScore > homeScore) or (awayOdds < homeOdds and awayScore < homeScore)
        if (awayrbi == homerbi):
            continue
        totalgames += 1                
        mofoCorrect = (mofoodds > 50 and ((mofoIsAway and awayrbi > homerbi) or (not mofoIsAway and homerbi > awayrbi))) or (mofoodds < 50 and ((mofoIsAway and awayrbi < homerbi) or (not mofoIsAway and homerbi < awayrbi)))
        webCorrect = (awayOdds > homeOdds and awayrbi > homerbi) or (awayOdds < homeOdds and awayrbi < homerbi)
        isdadbet = (min(mofoodds, othermofoodds) * webodds_payout((min(awayOdds, homeOdds)) / 100.0, 1)) > 1.0 and (min(mofoodds, othermofoodds) * webodds_payout((min(awayOdds, homeOdds)) / 100.0, 1)) > (max(mofoodds, othermofoodds) * webodds_payout((max(awayOdds, homeOdds)) / 100.0, 1))
        if isdadbet: 
            dadbets += 1
            if not mofoCorrect:
                dadcash += round(webodds_payout((min(awayOdds, homeOdds)) / 100.0, 1000))                
            else:
                dadcash -= 1000
        if awayTeamName not in success_by_team:
            success_by_team[awayTeamName] = {}
            success_by_team[awayTeamName]["games"] = 0
            success_by_team[awayTeamName]["webright"] = 0
            success_by_team[awayTeamName]["moforight"] = 0
        if homeTeamName not in success_by_team:
            success_by_team[homeTeamName] = {}
            success_by_team[homeTeamName]["games"] = 0
            success_by_team[homeTeamName]["webright"] = 0
            success_by_team[homeTeamName]["moforight"] = 0
        success_by_team[awayTeamName]["games"] += 1
        success_by_team[homeTeamName]["games"] += 1
        if mofoCorrect:
            moforight += 1                        
            success_by_team[awayTeamName]["moforight"] += 1
            success_by_team[homeTeamName]["moforight"] += 1
        if webCorrect:
            webright += 1            
            success_by_team[awayTeamName]["webright"] += 1
            success_by_team[homeTeamName]["webright"] += 1
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
    countgames = 0    
    for game in mofogames:     
        #print("Mofo game id = {}, game = {}".format(game, mofogames[game]))            
        countgames += 1    
    print("missing games: {}, unfinalized: {}, total counted games: {}".format(missing, unfinal, len(mofogames)))
    #print("MOFO payout multiplier mismatches: {}".format(mofomismatchpayouts))
    #print("Web payout multiplier mismatches: {}".format(webmismatchpayouts))
    print("Report for season {}".format(season))    
    ordered_success_by_team = dict(sorted(success_by_team.items(), key=lambda x: (x[1]["webright"]/x[1]["games"])-(x[1]["moforight"]/x[1]["games"])))
    if byteam:
        for team in ordered_success_by_team:
            mofo_success_rate = (ordered_success_by_team[team]["moforight"] / ordered_success_by_team[team]["games"]) * 100.0
            web_success_rate = (ordered_success_by_team[team]["webright"] / ordered_success_by_team[team]["games"]) * 100.0
            print("{} MOFO right {:.2f}%, Web right {:.2f}%".format(team, mofo_success_rate, web_success_rate))
    print("BH/Sun2 flipped games: {}, total BH/Sun2 games: {}, {:.2f}% flipped".format(flippedgames, bhsuns, (flippedgames / bhsuns) * 100.0))
    if bhsmismatches > 0:
        print("BH/Sun2 flipped games mismatches: {}, MOFO correct: {} ({:.2f}%), Web correct: {} ({:.2f}%)".format(bhsmismatches, mofoBHSmismatch, (mofoBHSmismatch/bhsmismatches) * 100.0, webBHSmismatch, (webBHSmismatch/bhsmismatches)*100.0))
    print("BH/Sun2 games: {}, MOFO correct: {} ({:.2f}%), Web correct: {} ({:.2f}%)".format(bhsuns, moforightBHS, (moforightBHS/bhsuns) * 100.0, webrightBHS, (webrightBHS/bhsuns)*100.0))    
    print("MOFO mismatch profit margin: {:.4f} times maxbet per mismatch".format(((mofomismatchpayouts - webmismatchpayouts)/(mismatches)) / 1000.0))
    if dadbets > 0:
        print("Dad cash: {:.4f} times maxbet per dadbet".format((dadcash / 1000.0) / dadbets))
    else:
        print("No dadbets")
    print("MOFO right: {}/{}, {:.2f}%".format(moforight, totalgames, (moforight/totalgames) * 100.0))
    print("Web right: {}/{}, {:.2f}%".format(webright, totalgames, (webright / totalgames) * 100.0))    
    print ("Total mismatches: {}, MOFO correct: {} ({:.2f}%), Web correct: {} ({:.2f}%)".format(mismatches, moforight_mismatch, (moforight_mismatch/mismatches) * 100.0, webright_mismatch, (webright_mismatch/mismatches)*100.0))


def get_mofo_list(game_list, team_attrs, stat_file_map, ballpark_file_map, season, startday=1, endday=125, is_early=False):
    mofo_list = []
    season_team_attrs = team_attrs.get(str(season), {})
    stats_regened = False
    pitchers, team_stat_data, pitcher_stat_data, last_stat_filename = None, None, None, None    
    terms_url = os.getenv("MOFO_TERMS")
    terms, _ = helpers.load_terms(terms_url)
    mods_url = os.getenv("MOFO_MODS")
    mods = helpers.load_mods(mods_url)        
    ballpark_mods_url = os.getenv("MOFO_BALLPARK_TERMS")
    ballpark_mods = helpers.load_bp_terms(ballpark_mods_url)  
    for day in range(startday, endday):
        games = [row for row in game_list if row["season"] == str(season) and row["day"] == str(day)]
        if not len(games) > 0:
            print("No games on day {}".format(day))
            continue       
        if len(games) > 24:
            print("{} games on day {}".format(len(games), day))
        if len(games) < 24 and day < 100:
            print("Missing {} games from {}".format((24 - len(games)) / 2, day))
        paired_games = pair_games(games)
        schedule = get_schedule_from_paired_games(paired_games, season, day)
        day_mods = get_attrs_from_paired_games(season_team_attrs, paired_games)
        stat_day = max(day-1, 1) if is_early else day
        stat_filename = stat_file_map.get((season, stat_day))
        if stat_filename:
            last_stat_filename = stat_filename
            pitchers = get_pitcher_id_lookup(stat_filename)
            team_stat_data, pitcher_stat_data = load_stat_data(stat_filename, schedule, day, season_team_attrs)
            stats_regened = False
        elif should_regen(day_mods):
            pitchers = get_pitcher_id_lookup(last_stat_filename)
            team_stat_data, pitcher_stat_data = load_stat_data(last_stat_filename, schedule, day, season_team_attrs)
            stats_regened = True
        elif stats_regened:
            pitchers = get_pitcher_id_lookup(last_stat_filename)
            team_stat_data, pitcher_stat_data = load_stat_data(last_stat_filename, schedule, day, season_team_attrs)
            stats_regened = False
          
        ballpark_filename = ballpark_file_map.get((season, day))        
        if not ballpark_filename:
            for backday in reversed(range(1, day)):
                ballpark_filename = ballpark_file_map.get((season, backday))
                if ballpark_filename:
                    break
            if not ballpark_filename:
                ballpark_filename = ballpark_file_map.get((season-1, 73))
        if ballpark_filename:
            with open(ballpark_filename) as f:
                ballparks = json.load(f)
        else:
            if ballparks is None:  # this should use the previous value of ballparks by default, use default if not
                print("!!!!!!catching ballparks is none!!!!!")
                ballparks = collections.defaultdict(lambda: collections.defaultdict(lambda: 0.5))
            
        for game in paired_games:
            away_game, home_game = game["away"], game["home"]            
            awayPitcher, awayTeam = pitchers.get(away_game["pitcher_id"])
            homePitcher, homeTeam = pitchers.get(home_game["pitcher_id"])
            homeTeamId = helpers.get_team_id(homeTeam)
            ballpark = ballparks.get(homeTeamId, collections.defaultdict(lambda: 0.5))
            #print("{} at {}".format(awayTeam, homeTeam))
            #if len(season_team_attrs.get(awayTeam, []) + season_team_attrs.get(homeTeam, [])) > 0:
                #continue
            away_mods, home_mods = mofo.get_mods(mods, season_team_attrs.get(awayTeam, []), season_team_attrs.get(homeTeam, []), 
                                                 awayTeam, homeTeam, awayPitcher, homePitcher, away_game["weather"], ballpark, 
                                                 ballpark_mods, team_stat_data, pitcher_stat_data)            
            away_odds, home_odds = mofo.get_mofo(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data,
                                                  pitcher_stat_data, terms, away_mods, home_mods)               
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
    parser.add_argument('--ballparks', help="path to ballparks folder")
    parser.add_argument('--season', help="print output")
    parser.add_argument('--byteam', help="show success rates by team", action='store_true')
    parser.add_argument('--start', help="start day")  
    parser.add_argument('--end', help="end day")
    parser.add_argument('--early', action="store_true", help="use early idol predictions")
    args = parser.parse_args()
    return args


def main():
    cmd_args = handle_args()
    load_dotenv(dotenv_path="../.env")
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    game_list = base_solver.get_games(cmd_args.gamefile)
    ballpark_file_map = base_solver.get_ballpark_map(cmd_args.ballparks)    
    byteam = cmd_args.byteam
    startday, endday = 1, 125
    if cmd_args.start:
        startday = int(cmd_args.start)
    if cmd_args.end:
        endday = int(cmd_args.end)
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    season = int(cmd_args.season)
    mofo_list = get_mofo_list(game_list, team_attrs, stat_file_map, ballpark_file_map, season, startday, endday, cmd_args.early)
    compare(byteam, season, mofo_list)
    # print("Result fail rate: {:.2f}%".format(result_fail_rate*100.0))


if __name__ == "__main__":
    main()