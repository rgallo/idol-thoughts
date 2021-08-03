from __future__ import division
from __future__ import print_function

import argparse
import collections
import json

import helpers
import os
import mofo

from solvers import base_solver

def setup_playerbased(weather, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, ballparks, team_stat_data, pitcher_stat_data):
    terms_url = os.getenv("FOMO_TERMS")
    terms, _ = helpers.load_terms(terms_url)
    halfterms_url = os.getenv("FOMO_HALF_TERMS")
    halfterms = helpers.load_half_terms(halfterms_url)
    mods_url = os.getenv("FOMO_MODS")
    mods = helpers.load_mods(mods_url)    
    ballpark_mods_url = os.getenv("FOMO_BALLPARK_TERMS")
    ballpark_mods = helpers.load_bp_terms(ballpark_mods_url)
    homeTeamId = helpers.get_team_id(homeTeam)
    ballpark = ballparks.get(homeTeamId, collections.defaultdict(lambda: 0.5))
    awayMods, homeMods = mofo.get_park_mods(ballpark, ballpark_mods)
    adjustments = mofo.instantiate_adjustments(terms, halfterms)
    return mods, terms, awayMods, homeMods, adjustments

def calculate(awayPitcher, homePitcher, awayTeam, homeTeam, ballparks, team_stat_data, pitcher_stat_data, awayAttrs, homeAttrs,
              day, weather, skip_mods=False, runtime_solution=False):
    mods, terms, awayMods, homeMods, adjustments = setup_playerbased(weather, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, ballparks, team_stat_data, pitcher_stat_data)
    adjusted_stat_data = helpers.calculate_adjusted_stat_data(awayAttrs, homeAttrs, awayTeam, homeTeam, team_stat_data)
    return mofo.get_mofo_playerbased(mods, awayPitcher, homePitcher, awayTeam, homeTeam, awayAttrs, homeAttrs, weather, team_stat_data, pitcher_stat_data, terms, awayMods, homeMods, adjusted_stat_data, adjustments, skip_mods=skip_mods, runtime_solution=runtime_solution)

def process_games(game_list, batter_list, stat_file_map, ballpark_file_map, season, dayrange):    
    solved_hits, solved_homers = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
    real_hits, real_homers = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
    solved_seeddogs, real_seeddogs = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
    season_hits, season_homers = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
    season_seeddogs = collections.defaultdict(lambda: {})
    solved_hits_score, solved_homers_score, solved_seeddogs_score, real_hits_score, real_homers_score, real_seeddogs_score = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    for day in dayrange:    
        games = [row for row in game_list if row["season"] == str(season) and row["day"] == str(day)]        
        pitchers, team_stat_data, pitcher_stat_data, last_stat_filename, ballparks = (None, ) * 5     
        paired_games = base_solver.pair_games(games)            
        schedule = base_solver.get_schedule_from_paired_games(paired_games, season, day)
        day_mods = base_solver.get_attrs_from_paired_games(season_team_attrs, paired_games)
        stat_filename = stat_file_map.get((season, day))
        if stat_filename:
            last_stat_filename = stat_filename
            pitchers = base_solver.get_pitcher_id_lookup(stat_filename)
            team_stat_data, pitcher_stat_data = helpers.load_stat_data_pid(stat_filename, schedule, day, season_team_attrs)
            stats_regened = False
        elif should_regen(day_mods):
            pitchers = base_solver.get_pitcher_id_lookup(last_stat_filename)
            team_stat_data, pitcher_stat_data = helpers.load_stat_data_pid(last_stat_filename, schedule, day, season_team_attrs)
            stats_regened = True
        elif stats_regened:
            pitchers = base_solver.get_pitcher_id_lookup(last_stat_filename)
            team_stat_data, pitcher_stat_data = helpers.load_stat_data_pid(last_stat_filename, schedule, day, season_team_attrs)
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
                ballparks = collections.defaultdict(lambda: collections.defaultdict(lambda: 0.5))
        #get all data stuff sorted        
        for game in paired_games:            
            batter_perf_data = [row for row in batter_list if row["season"] == str(season) and row["day"] == str(day) and row["game_id"] == game["away"]["game_id"]]            
            for batter in batter_perf_data:
                real_hits[batter] = int(batter["hits"])
                real_homers[batter] = int(batter["home_runs"])
                real_seeddogs[batter] = (int(batter["hits"]) * 1.5) + (int(batter["home_runs"]) * 4.0)
                if batter not in season_hits:
                    season_hits[batter] = 0
                    season_homers[batter] = 0
                    season_seeddogs[batter] = 0
                season_hits[batter] += int(batter["hits"])
                season_homers[batter] += int(batter["home_runs"])
                season_seeddogs[batter] += (int(batter["hits"]) * 1.5) + (int(batter["home_runs"]) * 4.0)                
            away_odds, home_odds, away_hits, home_hits, away_homers, home_homers, away_stolen_bases, home_stolen_bases = calculate(awayPitcher, homePitcher, awayTeam, homeTeam, ballparks, team_stat_data, pitcher_stat_data, awayAttrs, homeAttrs, day, weather, False, True)            
            solved_hits, solved_homers = {**solved_hits, **away_hits, **home_hits}, {**solved_homers, **away_homers, **home_homers}
        for playerid in solved_hits:
            solved_seeddogs[playerid] = (solved_hits[playerid] * 1.5) + (solved_homers[playerid] * 4.0)
        sorted_real_hits, sorted_real_homers = sorted(real_hits.items(), key=lambda k: k[1], reverse=True), sorted(real_homers.items(), key=lambda k: k[1], reverse=True)
        sorted_solved_hits, sorted_solved_homers = sorted(solved_hits.items(), key=lambda k: k[1], reverse=True), sorted(solved_homers.items(), key=lambda k: k[1], reverse=True)         
        sorted_solved_seeddogs, sorted_real_seeddogs = sorted(solved_seeddogs.items(), key=lambda k: k[1], reverse=True), sorted(real_seeddogs.items(), key=lambda k: k[1], reverse=True)
        
        for playerid in sorted_solved_hits:                    
            solved_hits_score += real_hits[playerid] * 1500.0
            break        
        for playerid in sorted_solved_homers:                    
            solved_homers_score += real_homers[playerid] * 4000.0
            break        
        for playerid in sorted_solved_seeddogs:                    
            solved_seeddogs_score += ((real_hits[playerid] * 1500.0) + (real_homers[playerid] * 4000.0))
            break
        
        for playerid in sorted_real_hits:                    
            real_hits_score += real_hits[playerid] * 1500.0
            break        
        for playerid in sorted_real_homers:                    
            real_homers_score += real_homers[playerid] * 4000.0
            break        
        for playerid in sorted_real_seeddogs:                    
            real_seeddogs_score += ((real_hits[playerid] * 1500.0) + (real_homers[playerid] * 4000.0))
            break

        solved_hits.clear()
        solved_homers.clear()
        solved_seeddogs.clear()
        real_hits.clear()
        real_homers.clear()
        real_seeddogs.clear()

    sorted_season_hits, sorted_season_homers = sorted(season_hits.items(), key=lambda k: k[1], reverse=True), sorted(season_homers.items(), key=lambda k: k[1], reverse=True)
    sorted_season_seeddogs = sorted(season_seeddogs.items(), key=lambda k: k[1], reverse=True)
    for playerid in sorted_season_hits:
        idle_seeds_score = season_hits[playerid] * 1500.0
        break
    if idle_seeds_score >= solved_hits_score:
        print("Seeds better off idling.")
    for playerid in sorted_season_homers:
        idle_dogs_score = season_homers[playerid] * 4000.0
        break
    if idle_dogs_score >= solved_homers_score:
        print("Dogs better off idling.")
    for playerid in sorted_season_seeddogs:
        idle_seeddogs_score = season_seeddogs[playerid] * 1000.0
        break
    if idle_seeddogs_score >= solved_seeddogs_score:
        print("Seeds + dogs better off idling.")
    seed_score = (solved_hits_score / real_hits_score) * 100.0
    dogs_score = (solved_homers_score / real_homers_score) * 100.0
    seed_dogs_score = (solved_seeddogs_score / real_seeddogs_score) * 100.0
    print("Hits report: Solved hits score = {:.0f}, max hits score = {.0f}, idle hits score = {:.0f}".format(solved_hits_score, real_hits_score, idle_seeds_score))
    print("Hrs report: Solved hrs score = {:.0f}, max hrs score = {.0f}, idle hrs score = {:.0f}".format(solved_homers_score, real_homers_score, idle_dogs_score))
    print("Seeds + Dogs report: Solved score = {:.0f}, max score = {.0f}, idle score = {:.0f}".format(solved_seeddogs_score, real_seeddogs_score, idle_seeddogs_score))    

    return seed_score, dogs_score, seed_dogs_score

def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--statfolder', help="path to stat folder")
    parser.add_argument('--ballparks', help="path to ballparks folder")
    parser.add_argument('--gamefile', help="path to game file")
    parser.add_argument('--batterfile', help="path to the batter file")          
    parser.add_argument('--output', required=False, help="file output directory")
    #parser.add_argument('--env', help="path to .env file, defaults to .env in same directory")
    args = parser.parse_args()
    return args

def main():
    cmd_args = handle_args()    
    game_list = base_solver.get_games(cmd_args.gamefile)
    batter_list = base_solver.get_batters(cmd_args.batterfile)
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    ballpark_file_map = base_solver.get_ballpark_map(cmd_args.ballparks)    
    dayrange = range(1, 100)    
    season = 23    
    seed_score, dogs_score, seed_dogs_score = process_games(game_list, batter_list, stat_file_map, ballpark_file_map, season, dayrange)
    print("Scores are in % of optimum earnings potential, defined as 100% of top earner, 50% of 2nd earner, 25% of 3rd earner, etc.")
    print("Seeds score = {:.2f}, dogs score = {:.2f}, seeds + dogs score = {:.2f}".format(seed_score, dogs_score, seed_dogs_score))
if __name__ == "__main__":
    main()