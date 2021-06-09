from __future__ import division
from __future__ import print_function

import os
import math
import random
import statistics
import helpers
import collections
import copy

from helpers import StlatTerm, ParkTerm, geomean, load_terms

def calc_team(terms, termset, mods, skip_mods=False):
    total = 0.0
    for termname, val in termset:
        term = terms[termname]        
        #reset to 1 for each new termname
        multiplier = 1.0 
        if not skip_mods:            
            modterms = (mods or {}).get(termname, [])              
            if len(modterms) > 0:
                multiplier = statistics.harmonic_mean(modterms)                      
        total += term.calc(val) * multiplier        
    return total          

def calc_stlatmod(name, pitcher_data, batter_data, team_data, stlatterm): 
    if name == "walkingruthlessness":
        name = "ruthlessness"
    if name == "hitoverpowerment":
        name = "overpowerment"
    if name == "stealwatchfulness":
        name = "watchfulness"
    if name == "attemptlaserlikeness":
        name = "laserlikeness"
    if name in helpers.PITCHING_STLATS:
        value = pitcher_data[name]
    elif name in helpers.BATTING_STLATS:        
        value = batter_data[name]    
    else:         
        if name == "basethirst":
            stlatname = "baseThirst"
        elif name == "groundfriction":
            stlatname = "groundFriction"
        else:
            stlatname = name
        if stlatname in helpers.BASERUNNING_STLATS:
            value = batter_data[stlatname]    
        if stlatname in helpers.DEFENSE_STLATS:
            value = geomean([row[stlatname] for row in team_data])
    normalized_value = stlatterm.calc(value)
    base_multiplier = logistic_transform(normalized_value)
    multiplier = 2.0 * base_multiplier
    return multiplier

def valid_stlat(name, teamisbatting):        
    if name == "walkingruthlessness":
        name = "ruthlessness"
    if name == "hitoverpowerment":
        name = "overpowerment"
    if name == "stealwatchfulness":
        name = "watchfulness"
    if name == "attemptlaserlikeness":
        name = "laserlikeness"
    if name in helpers.PITCHING_STLATS:
        return True
    elif name in helpers.BATTING_STLATS and teamisbatting:        
        return True      
    else:
        if name == "basethirst":
            stlatname = "baseThirst"
        elif name == "groundfriction":
            stlatname = "groundFriction"
        else:
            stlatname = name
        if (stlatname in helpers.DEFENSE_STLATS) or ((stlatname in helpers.BASERUNNING_STLATS) and teamisbatting):
            return True        
    return False

def get_batman_mods(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, batter, battingteam, weather, ballpark, ballpark_mods, team_stat_data, pitcher_stat_data):    
    awayMods, homeMods = collections.defaultdict(lambda: []), collections.defaultdict(lambda: [])
    lowerAwayAttrs = [attr.lower() for attr in awayAttrs]
    lowerHomeAttrs = [attr.lower() for attr in homeAttrs]    
    bird_weather = helpers.get_weather_idx("Birds")    
    flood_weather = helpers.get_weather_idx("Flooding")    
    batter_list_dict = [stlats for player_id, stlats in team_stat_data[battingteam].items() if player_id == batter]
    batter_data = batter_list_dict[0]    
    batting_team_data = [stlats for player_id, stlats in team_stat_data[battingteam].items() if (not stlats.get("shelled", False))]
    pitching_team_data = [stlats for player_id, stlats in team_stat_data[pitchingteam].items()]
    if battingteam == homeTeam:        
        home_team_data = batting_team_data
        away_team_data = pitching_team_data
        hometeamisbatting, awayteamisbatting = True, False
    else:        
        away_team_data = batting_team_data
        home_team_data = pitching_team_data
        hometeamisbatting, awayteamisbatting = False, True
    for attr in mods:
        # Special case for Affinity for Crows
        if attr == "affinity_for_crows" and weather != bird_weather:
            continue
        if attr == "high_pressure" and weather != flood_weather:
            continue
        if attr in lowerAwayAttrs:            
            for name, stlatterm in mods[attr]["same"].items():
                if valid_stlat(name, awayteamisbatting):
                    multiplier = calc_stlatmod(name, pitcher_stat_data[pitcher], batter_data, away_team_data, stlatterm)
                    awayMods[name].append(multiplier)
            for name, stlatterm in mods[attr]["opp"].items():                
                if valid_stlat(name, hometeamisbatting):
                    multiplier = calc_stlatmod(name, pitcher_stat_data[pitcher], batter_data, home_team_data, stlatterm)
                    homeMods[name].append(multiplier)
        if attr in lowerHomeAttrs and attr != "traveling":
            for name, stlatterm in mods[attr]["same"].items():                
                if valid_stlat(name, hometeamisbatting):
                    multiplier = calc_stlatmod(name, pitcher_stat_data[pitcher], batter_data, home_team_data, stlatterm)
                    homeMods[name].append(multiplier)
            for name, stlatterm in mods[attr]["opp"].items():
                if valid_stlat(name, awayteamisbatting):
                    multiplier = calc_stlatmod(name, pitcher_stat_data[pitcher], batter_data, away_team_data, stlatterm)
                    awayMods[name].append(multiplier)    
    for ballparkstlat, stlatterms in ballpark_mods.items():        
        for playerstlat, stlatterm in stlatterms.items():
            if type(stlatterm) == ParkTerm:            
                value = ballpark[ballparkstlat]
                normalized_value = stlatterm.calc(value)
                base_multiplier = logistic_transform(normalized_value)
                if value > 0.5:
                    multiplier = 2.0 * base_multiplier
                elif value < 0.5:
                    multiplier = 2.0 - (2.0 * base_multiplier)                
                else:
                    multiplier = 1.0
                awayMods[playerstlat].append(multiplier)
                homeMods[playerstlat].append(multiplier)    
    return awayMods, homeMods

def logistic_transform(value):
    try:
       transformed_value = (1.0 / (1.0 + (2.0 ** (-1.0 * value))))
    except OverflowError:
       transformed_value = 1.0
    return transformed_value

def logistic_transform_bten(value):
    try:
       transformed_value = (1.0 / (1.0 + (100.0 ** (-1.0 * value))))
    except OverflowError:
       transformed_value = 1.0
    if transformed_value > 1.0:
        return 1.0
    return transformed_value

def setup(eventofinterest, weather, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, ballpark, ballpark_mods):
    if eventofinterest == "hits":
        terms_url = os.getenv("BATMAN_HIT_TERMS")
        mods_url = os.getenv("BATMAN_HIT_MODS")
        ballpark_mods_url = os.getenv("BATMAN_HIT_BALLPARK_TERMS")
    elif eventofinterest == "hrs":
        terms_url = os.getenv("BATMAN_HR_TERMS")
        mods_url = os.getenv("BATMAN_HR_MODS")
        ballpark_mods_url = os.getenv("BATMAN_HR_BALLPARK_TERMS")
    elif eventofinterest == "abs":
        terms_url = os.getenv("BATMAN_AB_TERMS")
        mods_url = os.getenv("BATMAN_AB_MODS")
        ballpark_mods_url = os.getenv("BATMAN_AB_BALLPARK_TERMS")
    else:
        raise ValueError("Unsupported event of interest type")
    
    terms, special_cases = load_terms(terms_url, ["factors"])
    mods = helpers.load_mods(mods_url)
    ballparks_url = os.getenv("BALLPARKS")
    ballparks = helpers.load_ballparks(ballparks_url)    
    ballpark_mods = helpers.load_bp_terms(ballpark_mods_url)
    homeTeamId = helpers.get_team_id(homeTeam)
    ballpark = ballparks.get(homeTeamId, collections.defaultdict(lambda: 0.5))

    awayMods, homeMods = get_batman_mods(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, batter, battingteam, weather, ballpark, ballpark_mods, team_pid_stat_data, pitcher_stat_data)    

    return terms, special_cases, awayMods, homeMods

def calc_batman_intelligent(numerator, denominator, cutoff):
    batman_raw, batman = 0.0, 0.0
    
    if denominator < 0:
        return 0    
    if denominator == 0:
        return 1       
    
    batman_raw = numerator / denominator
    if math.isnan(batman_raw):            
        return 1           
    
    batman = logistic_transform_bten(batman_raw)
    
    if batman <= cutoff:
        return 0    
    return batman

def solve_team_atbats(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, battingteam, weather, ballpark, ballpark_mods, team_pid_stat_data, pitcher_stat_data, innings, flip_lineup, terms, actual_hits, actual_hrs, actual_abs, special_cases, outs_pi=3, baseline=False):    
    factor_contactcut, factor_hitcut, factor_hrscut, factor_walkcut, factor_attempt, factor_runout, reverberation, repeating = special_cases["factors"][:8]    
    team_atbat_data = {} 
    batting_mods_by_Id = {}        
    batters = team_pid_stat_data.get(battingteam) 
    batters_correct_hits, batters_correct_hrs, batters_correct_abs = {}, {}, {}
    contacts, hits, hrs, walks, final_hits, final_hrs, final_walks, average_hits, average_hrs, average_abs = {}, {}, {}, {}, {}, {}, {}, {}, {}, {}
    ordered_active_batters = sorted([(k, v) for k,v in batters.items() if not v["shelled"]], key=lambda x: x[1]["turnOrder"], reverse=flip_lineup)    
    #need to create a dict of mods to pass into the calculations based on the active batter
    for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):
        defenseMods, battingMods = collections.defaultdict(lambda: []), collections.defaultdict(lambda: [])
        awayMods, homeMods = get_batman_mods(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, batter_id, battingteam, weather, ballpark, ballpark_mods, team_pid_stat_data, pitcher_stat_data)
        if homeTeam == battingteam:
            battingMods, defenseMods = homeMods, awayMods
        else:
            battingMods, defenseMods = awayMods, homeMods
        batting_mods_by_Id[batter_id] = battingMods
        batters_correct_hits[batter_id] = 0 
        batters_correct_hrs[batter_id] = 0 
        batters_correct_abs[batter_id] = 0
        batters_correct_games[batter_id] = 0
    active_batters = len(ordered_active_batters)        
    outs_pg = innings * outs_pi
    games = 0
    all_games = []
    current_outs, first_pass_outs = 0, 0
    sufficient_data = False
    while not sufficient_data:
        #start a new game, make sure we set our finals back to zero each time
        for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):          
            final_hits[batter_id] = 0.0
            final_hrs[batter_id] = 0.0
            final_walks[batter_id] = 0.0     
            final_abs[batter_id] = 0.0      
        while current_outs < outs_pg:
            for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):          
                if current_outs >= outs_pg:
                    break     
                is_reverberating, is_repeating, batter_up = False, False, True
                while is_reverberating or is_repeating or batter_up:
                    #within here, we also need to check if we never got any outs the first time through the lineup... if we didn't, we need to quit while we're ahead since this will go until a kill condition is hit                               
                    if batter_id not in contacts:
                        contacts[batter_id] = calc_contacts(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], 0.0)
                        hits[batter_id] = calc_hits(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], 0.0)
                        hrs[batter_id] = calc_hrs(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], 0.0)
                        walks[batter_id] = calc_walks(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], 0.0)                                                                
                
                    #check for contact with the ball
                    if contacts[batter_id] >= random.random():
                        #check for a homer
                        if hrs[batter_id] >= random.random():
                            final_hrs[batter_id] += 1.0
                        #check for a hit
                        elif hits[batter_id] >= random.random():                    
                            #if and only if we got a base hit, we can attempt to steal
                            final_hits[batter_id] += 1.0
                            steal_attempt = calc_steal_attempt(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], 0.0)    
                            #check if we try to steal
                            if steal_attempt >= random.random():
                                baserunners_out = calc_runner_out(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], 0.0) 
                                #check if we got caught stealing
                                if baserunners_out >= random.random():
                                    current_outs += 1.0
                    #check if batter was walked
                    elif walks[batter_id] >= random.random():
                        #batter walked, don't add an out                    
                        final_walks[batter_id] += 1.0
                    else:
                        #batter did not contact the ball for a hit or homer, nor did they get walked, so batter got out
                        current_outs += 1.0                

                    if team_pid_stat_data[battingteam][batter_id]["reverberating"]:                        
                        if reverberation >= random.random():
                            is_reverberating = True                        
                    if team_pid_stat_data[battingteam][batter_id]["repeating"]:                        
                        if repeating >= random.random():
                            is_repeating = True            
            
                    #regardless of what happened, batter got an atbat
                    final_abs[batter_id] += 1.0      
                    batter_up = False                    
        games += 1
        for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):
            if final_hits[batter_id] == actual_hits[batter_id]:
                batters_correct_hits[batter_id] += 1
                correct_hits = True
            if final_hrs[batter_id] == actual_hrs[batter_id]:
                batters_correct_hrs[batter_id] += 1
                correct_hrs = True
            if final_abs[batter_id] == actual_abs[batter_id]:
                batters_correct_abs[batter_id] += 1
                correct_abs = True
            if correct_hits and correct_hrs and correct_abs:
                batters_correct_games[batter_id] += 1
        all_games = batters_correct_games.values()        
        sufficient_data = min(all_games) >= 10        
        #in order to make sure solving doesn't take forever, we need to have a threshold at which we do not believe our data is going to be reasonably matched by the values we're testing
    #now that we've accumulated sufficient data to determine the probability of the events we are analyzing happening, we need to return the observed probability
    #the premise here is we should be seeing more events that are higher probability than lower probability, given the result of our calculations to determine the likelihood of the atomic events
    for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):        
        average_hits[batter_id] = batters_correct_hits[batter_id] / games
        average_hrs[batter_id] = batters_correct_hrs[batter_id] / games
        average_abs[batter_id] = batters_correct_abs[batter_id] / games
        average_perfects[batter_id] = batters_correct_games[batter_id] / games
    return average_hits, average_hrs, average_abs, average_perfects

def get_team_atbats(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, battingteam, weather, ballpark, ballpark_mods, team_pid_stat_data, pitcher_stat_data, innings, flip_lineup, terms, iterations, special_cases, outs_pi=3, baseline=False):    
    factor_contactcut, factor_hitcut, factor_hrscut, factor_walkcut, factor_attempt, factor_runout, reverberation, repeating = special_cases["factors"][:8]    
    team_atbat_data = {} 
    batting_mods_by_Id = {}        
    batters = team_pid_stat_data.get(battingteam) 
    contacts, hits, hrs, walks, final_hits, final_hrs, final_walks, average_hits, average_hrs, average_abs = {}, {}, {}, {}, {}, {}, {}, {}, {}, {}
    ordered_active_batters = sorted([(k, v) for k,v in batters.items() if not v["shelled"]], key=lambda x: x[1]["turnOrder"], reverse=flip_lineup)    
    #need to create a dict of mods to pass into the calculations based on the active batter
    for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):
        defenseMods, battingMods = collections.defaultdict(lambda: []), collections.defaultdict(lambda: [])
        awayMods, homeMods = get_batman_mods(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, batter_id, battingteam, weather, ballpark, ballpark_mods, team_pid_stat_data, pitcher_stat_data)
        if homeTeam == battingteam:
            battingMods, defenseMods = homeMods, awayMods
        else:
            battingMods, defenseMods = awayMods, homeMods
        batting_mods_by_Id[batter_id] = battingMods
    active_batters = len(ordered_active_batters)
    #outs_pg = innings * outs_pi              
    #we're experimenting with actually running a large aggregate case here, so we need to chew through a large pile of "games" to determine the average case for this game
    #try 100 games worth of outs and see how godawful slow that is to solve
    iterations = min(iterations, 100.0)
    outs_pg = innings * outs_pi * iterations
    current_outs, first_pass_outs = 0, 0
    first_pass = False
    while current_outs < outs_pg:     
        if first_pass and (first_pass_outs == 0):
            #will only be true if we got no outs on our first pass... meaning we won't get any outs on subsequent passes and that's infinite baybee
            for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):
                if batter_id not in team_atbat_data:
                    team_atbat_data[batter_id] = 0.0
                    final_hits[batter_id] = 0.0
                    final_hrs[batter_id] = 0.0            
                average_abs[batter_id] = team_atbat_data[batter_id] * innings
                average_hits[batter_id] = final_hits[batter_id] * innings
                average_hrs[batter_id] = final_hrs[batter_id] * innings
            return average_abs, average_hits, average_hrs             
        for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):            
            #within here, we also need to check if we never got any outs the first time through the lineup... if we didn't, we need to quit while we're ahead since this will go until a kill condition is hit
            if current_outs >= outs_pg:
                break                
            if batter_id not in team_atbat_data:
                team_atbat_data[batter_id] = 0.0
                contacts[batter_id] = 0.0
                hits[batter_id] = 0.0
                hrs[batter_id] = 0.0
                walks[batter_id] = 0.0                
                final_hits[batter_id] = 0.0
                final_hrs[batter_id] = 0.0
                final_walks[batter_id] = 0.0                       

            if not baseline:
                contacts[batter_id] += calc_contacts(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], factor_contactcut)
                hits[batter_id] += calc_hits(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], factor_hitcut)
                hrs[batter_id] += calc_hrs(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], factor_hrscut)
                walks[batter_id] += calc_walks(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], factor_walkcut)

            if not baseline:
                if (contacts[batter_id] >= 1.0) and not ((hrs[batter_id] >= 1.0) or (walks[batter_id] >= 1.0)):
                    #we made contact this time and we're not being walked (walk takes precedence) or hitting a homer
                    if hits[batter_id] >= 1.0:                    
                        #if and only if we got a base hit, we can attempt to steal
                        steal_attempt = calc_steal_attempt(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], factor_attempt)    
                        if steal_attempt > 0.0:
                            baserunners_out = calc_runner_out(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], factor_runout) 
                            added_out = baserunners_out * steal_attempt
                            current_outs += added_out                                              
            
            if walks[batter_id] >= 1.0:
                #batter walked, don't add an out
                walks[batter_id] -= 1.0
                final_walks[batter_id] += 1.0
            elif contacts[batter_id] >= 1.0:
                #we made contact with the ball; now we need to determine if it is a base hit or a home run
                if hrs[batter_id] >= 1.0:
                    #batter hit a home run, don't add an out
                    hrs[batter_id] -= 1.0    
                    final_hrs[batter_id] += 1.0
                #check if it is a base hit
                elif hits[batter_id] >= 1.0:                   
                    hits[batter_id] -= 1.0
                    final_hits[batter_id] += 1.0
                #if we made contact with the ball, but we didn't get a base hit or a home run, assume we got an out in this atbat since we're doing all pitches in aggregate
                else:
                    current_outs += 1
                #always acknowledge the contact regardless
                contacts[batter_id] -= 1.0
            else:
                #batter got out somehow
                current_outs += 1

            if team_pid_stat_data[battingteam][batter_id]["reverberating"] and not baseline:                        
                team_atbat_data[batter_id] += reverberation       
                contacts[batter_id] += contacts[batter_id] * reverberation
                hits[batter_id] += hits[batter_id] * reverberation
                hrs[batter_id] += hrs[batter_id] * reverberation
                walks[batter_id] += walks[batter_id] * reverberation
            if team_pid_stat_data[battingteam][batter_id]["repeating"] and not baseline:                        
                team_atbat_data[batter_id] += repeating
                contacts[batter_id] += contacts[batter_id] * repeating
                hits[batter_id] += hits[batter_id] * repeating
                hrs[batter_id] += hrs[batter_id] * repeating
                walks[batter_id] += walks[batter_id] * repeating
            
            #regardless of what happened, batter got an atbat
            team_atbat_data[batter_id] += 1.0                                           
            last_batter = batter_id

            #need to catch this super early
            if team_atbat_data[batter_id] >= (2.0 * iterations * innings):
                #print("Unrealistic number of atbats caught, {} in {} innings".format(team_atbat_data[batter_id], innings))
                break                        
        if not first_pass:
            first_pass_outs = current_outs
            first_pass = True
        #need to catch this super early
        if team_atbat_data[last_batter] >= (2.0 * iterations * innings):
            #print("Unrealistic number of atbats caught, {} in {} innings".format(team_atbat_data[batter_id], innings))
            break
            
    #deal with fractional problems.... ignore this in the case where we're doing a big aggregate check
    #for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):
    #    if batter_id not in team_atbat_data:
    #        team_atbat_data[batter_id] = 0.0
    #        hits[batter_id] = 0.0
    #        hrs[batter_id] = 0.0
    #        walks[batter_id] = 0.0        
    #    if lineup_order > 0:
    #        team_atbat_data[batter_id] += max(walks[previous_batter], hrs[previous_batter], hits[previous_batter])
    #    else:
    #        first_batter = batter_id   
    #    final_hits[batter_id] += hits[batter_id]
    #    final_hrs[batter_id] += hrs[batter_id]
    #    previous_batter = batter_id
    #team_atbat_data[first_batter] += max(walks[previous_batter], hrs[previous_batter], hits[previous_batter])
    for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):
        if batter_id not in team_atbat_data:
            team_atbat_data[batter_id] = 0.0
            final_hits[batter_id] = 0.0
            final_hrs[batter_id] = 0.0            
        average_abs[batter_id] = team_atbat_data[batter_id] / iterations
        average_hits[batter_id] = final_hits[batter_id] / iterations        
        average_hrs[batter_id] = final_hrs[batter_id] / iterations                
    return average_abs, average_hits, average_hrs

def calc_steal_attempt(pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, factor_const):    
    crimes = 0.0
    team_cops = []
    pitcher_data = pitcher_stat_data[pitcher]            
    batter_list_dict = [stlats for player_id, stlats in team_pid_stat_data[battingteam].items() if player_id == batter]  
    batter_data = batter_list_dict[0]
    for playerid, stlats in team_pid_stat_data[pitchingteam].items():
        cop = calc_team(terms, (("watchfulness", stlats["watchfulness"]), ("tenaciousness", stlats["tenaciousness"])), defenseMods, False)                        
        team_cops.append(cop)
    cops = geomean(team_cops)
    crimes = calc_team(terms, (("basethirst", batter_data["baseThirst"]), ("attemptlaserlikeness", batter_data["laserlikeness"])), battingMods, False)            

    positive_term = crimes
    negative_term = cops
    numerator = (positive_term - negative_term) * 2.0
    denominator = positive_term + negative_term

    walksperatbat = calc_batman_intelligent(numerator, denominator, float(factor_const))

    return walksperatbat

def calc_runner_out(pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, factor_const):    
    crimes = 0.0
    team_cops = []
    pitcher_data = pitcher_stat_data[pitcher]            
    batter_list_dict = [stlats for player_id, stlats in team_pid_stat_data[battingteam].items() if player_id == batter]  
    batter_data = batter_list_dict[0]
    for playerid, stlats in team_pid_stat_data[pitchingteam].items():
        cop = calc_team(terms, (("anticapitalism", stlats["anticapitalism"]), ("stealwatchfulness", stlats["watchfulness"])), defenseMods, False)
        team_cops.append(cop)
    cops = geomean(team_cops)
    cold = calc_team(terms, (("coldness", pitcher_data["coldness"]),), defenseMods, False)   
    crimes = calc_team(terms, (("laserlikeness", batter_data["laserlikeness"]),), battingMods, False)            

    positive_term = cops + cold
    #laserlikeness is opposing 3 stlats here, so count it triple to be "fair"
    negative_term = crimes * 3.0
    numerator = (positive_term - negative_term) * 2.0
    denominator = positive_term + negative_term
    
    walksperatbat = calc_batman_intelligent(numerator, denominator, float(factor_const))

    return walksperatbat

def calc_walks(pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, factor_const):    
    pitcher_data = pitcher_stat_data[pitcher]            
    batter_list_dict = [stlats for player_id, stlats in team_pid_stat_data[battingteam].items() if player_id == batter]  
    batter_data = batter_list_dict[0]
    walkruth = calc_team(terms, (("walkingruthlessness", pitcher_data["ruthlessness"]),), defenseMods, False)    
    moxie = calc_team(terms, (("moxie", batter_data["moxie"]),), battingMods, False)            

    positive_term = moxie
    negative_term = walkruth
    numerator = (positive_term - negative_term) * 2.0
    denominator = positive_term + negative_term
    
    walksperatbat = calc_batman_intelligent(numerator, denominator, float(factor_const))

    return walksperatbat

def calc_hits(pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, factor_const):    
    team_omniscience = []
    pitcher_data = pitcher_stat_data[pitcher]            
    batter_list_dict = [stlats for player_id, stlats in team_pid_stat_data[battingteam].items() if player_id == batter]  
    batter_data = batter_list_dict[0]    
    thwack = calc_team(terms, (("thwackability", batter_data["thwackability"]),), battingMods, False)        
    muscl = calc_team(terms, (("musclitude", batter_data["musclitude"]),), battingMods, False)
    unthwack = calc_team(terms, (("unthwackability", pitcher_data["unthwackability"]),), defenseMods, False)           
    overpower = calc_team(terms, (("hitoverpowerment", pitcher_data["overpowerment"]),), defenseMods, False)    
    for playerid, stlats in team_pid_stat_data[pitchingteam].items():
        player_omni = calc_team(terms, (("omniscience", stlats["omniscience"]),), defenseMods, False)  
        team_omniscience.append(player_omni)
    omniscience = geomean(team_omniscience)
   
    #thwack appears to matter against both unthwack AND omni, so try counting it double here and let muscl just go against overpower 1 on 1
    positive_term = (thwack * 2.0) + muscl
    negative_term = unthwack + omniscience + overpower
    numerator = (positive_term - negative_term) * 2.0
    denominator = positive_term + negative_term
    
    hitsperatbat = calc_batman_intelligent(numerator, denominator, float(factor_const))

    return hitsperatbat

def calc_contacts(pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, factor_const):   
    pitcher_data = pitcher_stat_data[pitcher]            
    batter_list_dict = [stlats for player_id, stlats in team_pid_stat_data[battingteam].items() if player_id == batter]  
    batter_data = batter_list_dict[0]
    ruth = calc_team(terms, (("ruthlessness", pitcher_data["ruthlessness"]),), defenseMods, False)                
    path = calc_team(terms, (("patheticism", (1.0 - batter_data["patheticism"])),), battingMods, False)               
   
    positive_term = path
    negative_term = ruth
    numerator = (positive_term - negative_term) * 2.0
    denominator = positive_term + negative_term
    
    hitsperatbat = calc_batman_intelligent(numerator, denominator, float(factor_const))

    return hitsperatbat

def calc_hrs(pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, factor_const):    
    ballcount = 0.0
    pitcher_data = pitcher_stat_data[pitcher]            
    batter_list_dict = [stlats for player_id, stlats in team_pid_stat_data[battingteam].items() if player_id == batter]  
    batter_data = batter_list_dict[0]    
    divinity = calc_team(terms, (("divinity", batter_data["divinity"]),), battingMods, False)        
    overpower = calc_team(terms, (("overpowerment", pitcher_data["overpowerment"]),), defenseMods, False)            
    
    positive_term = divinity
    negative_term = overpower
    numerator = (positive_term - negative_term) * 2.0
    denominator = positive_term + negative_term
    
    hrsperatbat = calc_batman_intelligent(numerator, denominator, float(factor_const))

    return hrsperatbat

def get_batman(eventofinterest, pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, special_cases):             
    factor_const = special_cases["factors"][0]
    if eventofinterest == "hits":        
        batman = calc_hits(pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, factor_const)
    else:        
        batman = calc_hrs(pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, factor_const)    
    return batman


def calculatePitcherVsBatter(eventofinterest, weather, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, ballpark, ballpark_mods):
    terms, special_cases, awayMods, homeMods = setup(eventofinterest, weather, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, ballpark, ballpark_mods)
    if homeTeam == battingteam:
        battingMods, defenseMods = homeMods, awayMods
    else:
        battingMods, defenseMods = awayMods, homeMods
    return get_batman(eventofinterest, pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, special_cases)


def calculate(weather, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, battingteam, team_pid_stat_data, pitcher_stat_data, ballpark, ballpark_mods):
    batters = team_pid_stat_data.get(battingteam)
    batting_lineup_size = len([bid for bid, batter in batters.items() if not batter.get("shelled", False)])    
    atbats_data = {}
    results = []
    for batter_id, batter in batters.items():
        if batter.get("shelled", False):
            continue
        if (batter_id not in atbats_data):
            terms_url = os.getenv("BATMAN_AB_TERMS")
            mods_url = os.getenv("BATMAN_AB_MODS")
            ballpark_mods_url = os.getenv("BATMAN_AB_BALLPARK_TERMS")
            terms, special_cases = load_terms(terms_url, ["factors"])
            mods = helpers.load_mods(mods_url)
            ballparks_url = os.getenv("BALLPARKS")
            ballparks = helpers.load_ballparks(ballparks_url)    
            ballpark_mods = helpers.load_bp_terms(ballpark_mods_url)
            homeTeamId = helpers.get_team_id(homeTeam)
            ballpark = ballparks.get(homeTeamId, collections.defaultdict(lambda: 0.5))            
            atbats_data = get_team_atbats(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, battingteam, weather, ballpark, ballpark_mods, team_pid_stat_data, pitcher_stat_data, 9.0, False, terms, {"factors": special_cases}, outs_pi)
        name = batter["name"]
        batman_atbats = atbats_data[batter_id]

        #hits        
        batman_hits = calculatePitcherVsBatter("hits", weather, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, ballpark, ballpark_mods)

        #hrs
        batman_homers = calculatePitcherVsBatter("hrs", weather, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, ballpark, ballpark_mods)
        at_bats = batman_atbats
        hits = batman_hits * at_bats
        homers = batman_homers * at_bats
        results.append({"name": name, "team": battingteam, "hits": hits, "homers": homers, "abs": at_bats,
                        "attrs": batter["attrs"]})
    return results
