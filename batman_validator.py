from __future__ import division
from __future__ import print_function

import argparse
import collections
import json

import helpers
import os
import mofo

from dotenv import load_dotenv
from solvers import base_solver

def setup_playerbased(homeTeamId, weather, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, ballparks, team_stat_data, pitcher_stat_data):
    terms_url = os.getenv("FOMO_TERMS")        
    terms, _ = helpers.load_terms(terms_url)
    halfterms_url = os.getenv("FOMO_HALF_TERMS")
    halfterms = helpers.load_half_terms(halfterms_url)
    mods_url = os.getenv("FOMO_MODS")
    mods = helpers.load_mods(mods_url)    
    ballpark_mods_url = os.getenv("FOMO_BALLPARK_TERMS")
    ballpark_mods = helpers.load_bp_terms(ballpark_mods_url)    
    ballpark = ballparks.get(homeTeamId, collections.defaultdict(lambda: 0.5))
    awayMods, homeMods = mofo.get_park_mods(ballpark, ballpark_mods)
    adjustments = mofo.instantiate_adjustments(terms, halfterms)
    return mods, terms, awayMods, homeMods, adjustments

def calculate(homeTeamId, awayPitcher, homePitcher, awayTeam, homeTeam, ballparks, team_stat_data, pitcher_stat_data, awayAttrs, homeAttrs,
              day, weather, skip_mods=False, runtime_solution=True):    
    mods, terms, awayMods, homeMods, adjustments = setup_playerbased(homeTeamId, weather, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, ballparks, team_stat_data, pitcher_stat_data)
    adjusted_stat_data = helpers.calculate_adjusted_stat_data(awayAttrs, homeAttrs, awayTeam, homeTeam, team_stat_data)    
    return mofo.get_mofo_playerbased(mods, awayPitcher, homePitcher, awayTeam, homeTeam, awayAttrs, homeAttrs, weather, team_stat_data, pitcher_stat_data, terms, awayMods, homeMods, adjusted_stat_data, adjustments, skip_mods=skip_mods, runtime_solution=runtime_solution)

def process_games(game_list, batter_list, crimes_list, stat_file_map, ballpark_file_map, team_attrs, season, dayrange):    
    solved_hits, solved_homers, solved_steals = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
    real_hits, real_homers = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
    solved_seeddogs, real_seeddogs = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
    real_seedpickles, real_dogpickles, real_trifecta = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
    solved_seedpickles, solved_dogpickles, solved_trifecta = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
    season_hits, season_homers = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
    season_seeddogs, season_steals = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
    season_seedpickles, season_dogpickles, season_trifecta = collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {}), collections.defaultdict(lambda: {})
    solved_hits_score, solved_homers_score, solved_seeddogs_score, solved_pickles_score, solved_seedpickles_score, solved_dogpickles_score, solved_trifecta_score = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    real_hits_score, real_homers_score, real_seeddogs_score, real_steals_score, real_seedpickles_score, real_dogpickles_score, real_trifecta_score = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    idle_seeds_score, idle_dogs_score, idle_seeddogs_score, idle_pickles_score, idle_seedpickles_score, idle_dogpickles_score, idle_trifecta_score = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    static_idle_hours = 8
    first_idle_day = 15
    static_active_hours = 24 - static_idle_hours
    idle_hours, active_hours = static_idle_hours, static_active_hours    
    active_days, idle_days = [], []
    for day in dayrange:
        if day == first_idle_day:
            idle_days.append(day)
            idle_hours -= 1
            active_hours = 0
        else:
            if active_hours > 0:
                active_days.append(day)
                active_hours -= 1            
            else:
                idle_days.append(day)
                idle_hours -= 1
                if idle_hours == 0:
                    idle_hours, active_hours = static_idle_hours, static_active_hours
    print("Active days = {}".format(active_days))
    print("Idle days = {}".format(idle_days))
    for day in dayrange:    
        games = [row for row in game_list if row["season"] == str(season) and row["day"] == str(day)]        
        if not games:
            print("No games found day {}".format(day))
            continue
        pitchers, team_stat_data, pitcher_stat_data, last_stat_filename, ballparks = (None, ) * 5     
        season_team_attrs = team_attrs.get(str(season), {})
        paired_games = base_solver.pair_games(games)            
        schedule = base_solver.get_schedule_from_paired_games(paired_games, season, day)
        day_mods = base_solver.get_attrs_from_paired_games(season_team_attrs, paired_games)
        stat_filename = stat_file_map.get((season, day))
        if stat_filename:
            last_stat_filename = stat_filename
            pitchers = base_solver.get_pitcher_id_lookup(stat_filename)
            team_stat_data, pitcher_stat_data = helpers.load_stat_data_pid(stat_filename, schedule, day, season_team_attrs)
            stats_regened = False
        elif base_solver.should_regen(day_mods):
            pitchers = base_solver.get_pitcher_id_lookup(last_stat_filename)
            team_stat_data, pitcher_stat_data = helpers.load_stat_data_pid(last_stat_filename, schedule, day, season_team_attrs)
            stats_regened = True
        elif stats_regened:
            pitchers = base_solver.get_pitcher_id_lookup(last_stat_filename)
            team_stat_data, pitcher_stat_data = helpers.load_stat_data_pid(last_stat_filename, schedule, day, season_team_attrs)
            stats_regened = False
        if not pitchers:
            print("No pitchers found for day {}".format(day))
            continue
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
        real_steals = base_solver.pair_crimes_with_batter(crimes_list, team_stat_data, season, day)
        if day > 1:
            sorted_season_hits, sorted_season_homers = dict(sorted(season_hits.items(), key=lambda k: k[1], reverse=True)), dict(sorted(season_homers.items(), key=lambda k: k[1], reverse=True))
            sorted_season_seeddogs, sorted_season_steals = dict(sorted(season_seeddogs.items(), key=lambda k: k[1], reverse=True)), dict(sorted(season_steals.items(), key=lambda k: k[1], reverse=True))
            sorted_season_seedpickles = dict(sorted(season_seedpickles.items(), key=lambda k: k[1], reverse=True))
            sorted_season_dogpickles = dict(sorted(season_dogpickles.items(), key=lambda k: k[1], reverse=True))
            sorted_season_trifecta = dict(sorted(season_trifecta.items(), key=lambda k: k[1], reverse=True))
        #get all data stuff sorted        
        for game in paired_games:                                     
            away_game, home_game = game["away"], game["home"]    
            game_attrs = base_solver.get_attrs_from_paired_game(season_team_attrs, game)                        
            awayAttrs, homeAttrs = game_attrs["away"], game_attrs["home"]                
            awayPitcher, awayTeam = pitchers.get(away_game["pitcher_id"])    
            homePitcher, homeTeam = pitchers.get(home_game["pitcher_id"])
            #try:
            game_away_val, game_home_val, away_hits, home_hits, away_homers, home_homers, away_stolen_bases, home_stolen_bases, away_pitcher_ks, home_pitcher_ks, away_pitcher_era, home_pitcher_era = calculate(game["home"]["team_id"], awayPitcher, homePitcher, awayTeam, homeTeam, ballparks, team_stat_data, pitcher_stat_data, awayAttrs, homeAttrs, day, int(away_game["weather"]), skip_mods=False, runtime_solution=True)            
            solved_hits, solved_homers, solved_steals = {**solved_hits, **away_hits, **home_hits}, {**solved_homers, **away_homers, **home_homers}, {**solved_steals, **away_stolen_bases, **home_stolen_bases}
            #except ValueError:
            #    #print("Missing values for some reason?")
            #    continue
            batter_perf_data = [row for row in batter_list if row["season"] == str(season) and row["day"] == str(day) and row["game_id"] == game["away"]["game_id"]]            
            for batter in batter_perf_data:                
                real_hits[batter["batter_id"]] = int(batter["hits"])
                real_homers[batter["batter_id"]] = int(batter["home_runs"])
                real_seeddogs[batter["batter_id"]] = (int(batter["hits"]) * 1.5) + (int(batter["home_runs"]) * 4.0)
                if batter["batter_id"] not in real_steals:
                    real_steals[batter["batter_id"]] = 0
                real_seedpickles[batter["batter_id"]] = (real_steals[batter["batter_id"]] * 3.0) + (real_hits[batter["batter_id"]] * 1.5)
                real_dogpickles[batter["batter_id"]] = (real_steals[batter["batter_id"]] * 3.0) + (real_homers[batter["batter_id"]] * 4.0)
                real_trifecta[batter["batter_id"]] = (real_steals[batter["batter_id"]] * 3.0) + (real_hits[batter["batter_id"]] * 1.5) + (real_homers[batter["batter_id"]] * 4.0)
                if batter["batter_id"] not in season_hits:
                    season_hits[batter["batter_id"]] = 0
                    season_homers[batter["batter_id"]] = 0
                    season_seeddogs[batter["batter_id"]] = 0
                season_hits[batter["batter_id"]] += int(batter["hits"])
                season_homers[batter["batter_id"]] += int(batter["home_runs"])
                season_seeddogs[batter["batter_id"]] += (int(batter["hits"]) * 1.5) + (int(batter["home_runs"]) * 4.0)
                if batter["batter_id"] not in season_steals:
                    season_steals[batter["batter_id"]] = 0
                    season_seedpickles[batter["batter_id"]] = 0
                    season_dogpickles[batter["batter_id"]] = 0
                    season_trifecta[batter["batter_id"]] = 0
                season_steals[batter["batter_id"]] += real_steals[batter["batter_id"]]
                season_seedpickles[batter["batter_id"]] += (real_steals[batter["batter_id"]] * 3.0) + (real_hits[batter["batter_id"]] * 1.5)
                season_dogpickles[batter["batter_id"]] += (real_steals[batter["batter_id"]] * 3.0) + (real_homers[batter["batter_id"]] * 4.0)
                season_trifecta[batter["batter_id"]] += (real_steals[batter["batter_id"]] * 3.0) + (real_hits[batter["batter_id"]] * 1.5) + (real_homers[batter["batter_id"]] * 4.0)
        for playerid in solved_hits:
            solved_seeddogs[playerid] = (solved_hits[playerid] * 1.5) + (solved_homers[playerid] * 4.0)
        for playerid in solved_steals:
            solved_seedpickles[playerid] = (solved_hits[playerid] * 1.5) + (solved_steals[playerid] * 3.0)
            solved_dogpickles[playerid] = (solved_homers[playerid] * 4.0) + (solved_steals[playerid] * 3.0)
            solved_trifecta[playerid] = (solved_hits[playerid] * 1.5) + (solved_homers[playerid] * 4.0) + (solved_steals[playerid] * 3.0)
        sorted_real_hits, sorted_real_homers = dict(sorted(real_hits.items(), key=lambda k: k[1], reverse=True)), dict(sorted(real_homers.items(), key=lambda k: k[1], reverse=True))
        sorted_real_steals, sorted_real_seedpickles = dict(sorted(real_steals.items(), key=lambda k: k[1], reverse=True)), dict(sorted(real_seedpickles.items(), key=lambda k: k[1], reverse=True))
        sorted_real_dogpickles, sorted_real_trifecta = dict(sorted(real_dogpickles.items(), key=lambda k: k[1], reverse=True)), dict(sorted(real_trifecta.items(), key=lambda k: k[1], reverse=True))
        sorted_solved_hits, sorted_solved_homers = dict(sorted(solved_hits.items(), key=lambda k: k[1], reverse=True)), dict(sorted(solved_homers.items(), key=lambda k: k[1], reverse=True))
        sorted_solved_seeddogs, sorted_real_seeddogs = dict(sorted(solved_seeddogs.items(), key=lambda k: k[1], reverse=True)), dict(sorted(real_seeddogs.items(), key=lambda k: k[1], reverse=True))
        sorted_solved_steals, sorted_solved_seedpickles = dict(sorted(solved_steals.items(), key=lambda k: k[1], reverse=True)), dict(sorted(solved_seedpickles.items(), key=lambda k: k[1], reverse=True))
        sorted_solved_dogpickles, sorted_solved_trifecta = dict(sorted(solved_dogpickles.items(), key=lambda k: k[1], reverse=True)), dict(sorted(solved_trifecta.items(), key=lambda k: k[1], reverse=True))
        
        if day > 1:                    
            if day in idle_days:
                if idle_idol_seeds in real_hits:                    
                    idle_seeds_score += real_hits[idle_idol_seeds] * 1500.0
                    solved_hits_score += real_hits[idle_idol_seeds] * 1500.0                    
                if idle_idol_dogs in real_homers:
                    idle_dogs_score += real_homers[idle_idol_dogs] * 4000.0                
                    solved_homers_score += real_homers[idle_idol_dogs] * 4000.0
                if idle_idol_seeddogs in real_hits:
                    idle_seeddogs_score += real_hits[idle_idol_seeddogs] * 1500.0
                    idle_seeddogs_score += real_homers[idle_idol_seeddogs] * 4000.0
                    solved_seeddogs_score += real_hits[idle_idol_seeddogs] * 1500.0
                    solved_seeddogs_score += real_homers[idle_idol_seeddogs] * 4000.0
                if idle_idol_pickles in real_steals:
                    idle_pickles_score += real_steals[idle_idol_pickles] * 3000.0
                    solved_pickles_score += real_steals[idle_idol_pickles] * 3000.0                    
                if idle_idol_seedpickles in real_steals:
                    idle_seedpickles_score += real_steals[idle_idol_seedpickles] * 3000.0
                    idle_seedpickles_score += real_hits[idle_idol_seedpickles] * 1500.0
                    solved_seedpickles_score += real_steals[idle_idol_seedpickles] * 3000.0                    
                    solved_seedpickles_score += real_hits[idle_idol_seedpickles] * 1500.0
                if idle_idol_dogpickles in real_steals:
                    idle_dogpickles_score += real_steals[idle_idol_dogpickles] * 3000.0
                    idle_dogpickles_score += real_homers[idle_idol_dogpickles] * 4000.0
                    solved_dogpickles_score += real_steals[idle_idol_dogpickles] * 3000.0                    
                    solved_dogpickles_score += real_homers[idle_idol_dogpickles] * 4000.0
                if idle_idol_trifecta in real_steals:
                    idle_trifecta_score += real_steals[idle_idol_trifecta] * 3000.0
                    idle_trifecta_score += real_hits[idle_idol_trifecta] * 1500.0
                    idle_trifecta_score += real_homers[idle_idol_trifecta] * 4000.0
                    solved_trifecta_score += real_steals[idle_idol_trifecta] * 3000.0                    
                    solved_trifecta_score += real_hits[idle_idol_trifecta] * 1500.0
                    solved_trifecta_score += real_homers[idle_idol_trifecta] * 4000.0
            else:
                for playerid in sorted_season_hits:
                    if playerid in solved_hits:
                        idle_idol_seeds = playerid
                        if idle_idol_seeds in real_hits:                    
                            idle_seeds_score += real_hits[idle_idol_seeds] * 1500.0                    
                        break       
                for playerid in sorted_season_homers:                
                    if playerid in solved_homers:
                        idle_idol_dogs = playerid
                        if idle_idol_dogs in real_homers:
                            idle_dogs_score += real_homers[idle_idol_dogs] * 4000.0                    
                        break
                for playerid in sorted_season_seeddogs:
                    if playerid in solved_hits:
                        idle_idol_seeddogs = playerid
                        if idle_idol_seeddogs in real_hits:                    
                            idle_seeddogs_score += real_hits[playerid] * 1500.0
                            idle_seeddogs_score += real_homers[playerid] * 4000.0                    
                        break               
                for playerid in sorted_season_steals:
                    if playerid in solved_steals:
                        idle_idol_pickles = playerid
                        if idle_idol_pickles in real_steals:
                            idle_pickles_score += real_steals[idle_idol_pickles] * 3000.0
                        break
                for playerid in sorted_season_seedpickles:
                    if playerid in solved_steals:
                        idle_idol_seedpickles = playerid
                        if idle_idol_seedpickles in real_steals:
                            idle_seedpickles_score += real_steals[idle_idol_seedpickles] * 3000.0
                            idle_seedpickles_score += real_hits[idle_idol_seedpickles] * 1500.0
                        break
                for playerid in sorted_season_dogpickles:
                    if playerid in solved_steals:
                        idle_idol_dogpickles = playerid
                        if idle_idol_dogpickles in real_steals:
                            idle_dogpickles_score += real_steals[idle_idol_dogpickles] * 3000.0
                            idle_dogpickles_score += real_homers[idle_idol_dogpickles] * 4000.0
                        break
                for playerid in sorted_season_trifecta:
                    if playerid in solved_steals:
                        idle_idol_trifecta = playerid
                        if idle_idol_trifecta in real_steals:
                            idle_trifecta_score += real_steals[idle_idol_trifecta] * 3000.0
                            idle_trifecta_score += real_hits[idle_idol_trifecta] * 1500.0
                            idle_trifecta_score += real_homers[idle_idol_trifecta] * 4000.0
                        break

            sorted_season_hits.clear(), sorted_season_homers.clear(), sorted_season_seeddogs.clear(), sorted_season_steals.clear() 
            sorted_season_seedpickles.clear(), sorted_season_dogpickles.clear(), sorted_season_trifecta.clear()
        
        if day in active_days:              
            active_seeds_idol = next(iter(sorted_solved_hits))
            if active_seeds_idol in real_hits:
                solved_hits_score += real_hits[active_seeds_idol] * 1500.0                        
            active_dogs_idol = next(iter(sorted_solved_homers))
            if active_dogs_idol in real_homers:
                solved_homers_score += real_homers[active_dogs_idol] * 4000.0         
            active_seeddogs_idol = next(iter(sorted_solved_seeddogs))            
            if active_seeddogs_idol in real_hits:
                solved_seeddogs_score += ((real_hits[active_seeddogs_idol] * 1500.0) + (real_homers[active_seeddogs_idol] * 4000.0))                
            active_pickles_idol = next(iter(sorted_solved_steals))            
            if active_pickles_idol in real_steals:
                solved_pickles_score += real_steals[active_pickles_idol] * 3000.0
            active_seedpickles_idol = next(iter(sorted_solved_seedpickles))            
            if active_seedpickles_idol in real_steals:
                solved_seedpickles_score += (real_hits[active_seedpickles_idol] * 1500.0) + (real_steals[active_seedpickles_idol] * 3000.0)
            active_dogpickles_idol = next(iter(sorted_solved_dogpickles))            
            if active_dogpickles_idol in real_steals:
                solved_dogpickles_score += (real_homers[active_dogpickles_idol] * 4000.0) + (real_steals[active_dogpickles_idol] * 3000.0)
            active_trifecta_idol = next(iter(sorted_solved_trifecta))            
            if active_trifecta_idol in real_steals:
                solved_trifecta_score += (real_hits[active_trifecta_idol] * 1500.0) + (real_homers[active_trifecta_idol] * 4000.0) + (real_steals[active_trifecta_idol] * 3000.0)
        
        #need to only count hitters we would've realistically picked
        for playerid in sorted_real_hits:
            if playerid in solved_hits:
                real_hits_score += real_hits[playerid] * 1500.0            
                break
        for playerid in sorted_real_homers:
            if playerid in solved_homers:
                real_homers_score += real_homers[playerid] * 4000.0            
                break
        for playerid in sorted_real_seeddogs:
            if playerid in sorted_solved_seeddogs:
                real_seeddogs_score += (real_hits[playerid] * 1500.0) + (real_homers[playerid] * 4000.0)
                break
        for playerid in sorted_real_steals:
            if playerid in solved_steals:
                real_steals_score += real_steals[playerid] * 3000.0
                break
        for playerid in sorted_real_seedpickles:
            if playerid in solved_steals:
                real_seedpickles_score += (real_hits[playerid] * 1500.0) + (real_steals[playerid] * 3000.0)
                break
        for playerid in sorted_real_dogpickles:
            if playerid in solved_steals:
                real_dogpickles_score += (real_homers[playerid] * 4000.0) + (real_steals[playerid] * 3000.0)
                break
        for playerid in sorted_real_trifecta:
            if playerid in solved_steals:
                real_trifecta_score += (real_hits[playerid] * 1500.0) + (real_homers[playerid] * 4000.0) + (real_steals[playerid] * 3000.0)
                break

        solved_hits.clear(), solved_homers.clear(), solved_seeddogs.clear(), solved_steals.clear(), solved_seedpickles.clear(), solved_dogpickles.clear(), solved_trifecta.clear()
        real_hits.clear(), real_homers.clear(), real_seeddogs.clear(), real_steals.clear(), real_seedpickles.clear(), real_dogpickles.clear(), real_trifecta.clear()        
        sorted_solved_hits.clear(), sorted_solved_homers.clear(), sorted_solved_seeddogs.clear(), sorted_solved_steals.clear(), sorted_solved_seedpickles.clear(), sorted_solved_dogpickles.clear(), sorted_solved_trifecta.clear()
        sorted_real_hits.clear(), sorted_real_homers.clear(), sorted_real_seeddogs.clear(), sorted_real_steals.clear(), sorted_real_seedpickles.clear(), sorted_real_dogpickles.clear(), sorted_real_trifecta.clear()        
    
    if idle_seeds_score >= solved_hits_score:
        print("Seeds better off idling.")
    if idle_dogs_score >= solved_homers_score:
        print("Dogs better off idling.")
    if idle_seeddogs_score >= solved_seeddogs_score:
        print("Seeds + dogs better off idling.")
    if idle_pickles_score >= solved_pickles_score:
        print("Pickles better off idling.")
    if idle_seedpickles_score >= solved_seedpickles_score:
        print("Seeds + pickles better off idling.")
    if idle_dogpickles_score >= solved_dogpickles_score:
        print("Dogs + pickles better off idling.")
    if idle_trifecta_score >= solved_trifecta_score:
        print("Trifecta better off idling.")
    
    seed_score = (solved_hits_score / idle_seeds_score) * 100.0
    dogs_score = (solved_homers_score / idle_dogs_score) * 100.0
    seed_dogs_score = (solved_seeddogs_score / idle_seeddogs_score) * 100.0
    pickles_score = (solved_pickles_score / idle_pickles_score) * 100.0
    seedpickles_score = (solved_seedpickles_score / idle_seedpickles_score) * 100.0
    dogpickles_score = (solved_dogpickles_score / idle_dogpickles_score) * 100.0
    trifecta_score = (solved_trifecta_score / idle_trifecta_score) * 100.0
    season_seeds_threshold = (idle_seeds_score / real_hits_score) * 100.0
    season_dogs_threshold = (idle_dogs_score / real_homers_score) * 100.0
    season_seeddogs_threshold = (idle_seeddogs_score / real_seeddogs_score) * 100.0
    season_pickles_threshold = (idle_pickles_score / real_steals_score) * 100.0
    season_seedpickles_threshold = (idle_seedpickles_score / real_seedpickles_score) * 100.0
    season_dogpickles_threshold = (idle_dogpickles_score / real_dogpickles_score) * 100.0
    season_trifecta_threshold = (idle_trifecta_score / real_trifecta_score) * 100.0
    print("Solved hits score = {:.0f}, max hits score = {:.0f}, idle hits score = {:.0f}".format(solved_hits_score, real_hits_score, idle_seeds_score))
    print("Solved hrs score = {:.0f}, max hrs score = {:.0f}, idle hrs score = {:.0f}".format(solved_homers_score, real_homers_score, idle_dogs_score))
    print("Solved seeds + dogs score = {:.0f}, max score = {:.0f}, idle score = {:.0f}".format(solved_seeddogs_score, real_seeddogs_score, idle_seeddogs_score))
    print("Solved pickles score = {:.0f}, max score = {:.0f}, idle score = {:.0f}".format(solved_pickles_score, real_steals_score, idle_pickles_score))
    print("Solved seeds + pickles score = {:.0f}, max score = {:.0f}, idle score = {:.0f}".format(solved_seedpickles_score, real_seedpickles_score, idle_seedpickles_score))
    print("Solved dogs + pickles score = {:.0f}, max score = {:.0f}, idle score = {:.0f}".format(solved_dogpickles_score, real_dogpickles_score, idle_dogpickles_score))
    print("Solved trifecta score = {:.0f}, max score = {:.0f}, idle score = {:.0f}".format(solved_trifecta_score, real_trifecta_score, idle_trifecta_score))

    return seed_score, dogs_score, seed_dogs_score, pickles_score, seedpickles_score, dogpickles_score, trifecta_score, season_seeds_threshold, season_dogs_threshold, season_seeddogs_threshold, season_pickles_threshold, season_seedpickles_threshold, season_dogpickles_threshold, season_trifecta_threshold

def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--statfolder', help="path to stat folder")
    parser.add_argument('--ballparks', help="path to ballparks folder")
    parser.add_argument('--gamefile', help="path to game file")
    parser.add_argument('--batterfile', help="path to the batter file")  
    parser.add_argument('--crimefile', help="path to the crime file")  
    parser.add_argument('--output', required=False, help="file output directory")
    parser.add_argument('--env', help="path to .env file, defaults to .env in same directory")
    args = parser.parse_args()
    return args

def main():
    cmd_args = handle_args()    
    load_dotenv(dotenv_path=cmd_args.env)
    game_list = base_solver.get_games(cmd_args.gamefile)
    batter_list = base_solver.get_batters(cmd_args.batterfile)
    crimes_list = base_solver.get_crimes(cmd_args.crimefile)
    stat_file_map = base_solver.get_stat_file_map(cmd_args.statfolder)
    ballpark_file_map = base_solver.get_ballpark_map(cmd_args.ballparks)        
    with open('team_attrs.json') as f:
        team_attrs = json.load(f)
    dayrange = range(1, 100)    
    season = 23    
    seed_score, dogs_score, seed_dogs_score, pickles_score, seedpickles_score, dogpickles_score, trifecta_score, season_seeds_threshold, season_dogs_threshold, season_seeddogs_threshold, season_pickles_threshold, season_seedpickles_threshold, season_dogpickles_threshold, season_trifecta_threshold = process_games(game_list, batter_list, crimes_list, stat_file_map, ballpark_file_map, team_attrs, season, dayrange)
    print("Scores are in % of optimum earnings potential, defined as % of top idle earner for the season")
    print("Scores:     Seeds = {:.2f}%, dogs = {:.2f}%, seeds + dogs = {:.2f}%, pickles = {:.2f}%, seeds + pickles = {:.2f}%, dogs + pickles = {:.2f}%, trifecta = {:.2f}%".format(seed_score, dogs_score, seed_dogs_score, pickles_score, seedpickles_score, dogpickles_score, trifecta_score))
    print("Thresholds: Seeds = {:.2f}%, dogs = {:.2f}%, seeds + dogs = {:.2f}%, pickles = {:.2f}%, seeds + pickles = {:.2f}%, dogs + pickles = {:.2f}%, trifecta = {:.2f}%".format(season_seeds_threshold, season_dogs_threshold, season_seeddogs_threshold, season_pickles_threshold, season_seedpickles_threshold, season_dogpickles_threshold, season_trifecta_threshold))
if __name__ == "__main__":
    main()