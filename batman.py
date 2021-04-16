from __future__ import division
from __future__ import print_function

import os
import math
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

def calc_batman_intelligent(numerator, denominator, positive_term, negative_term, cutoff):
    batman_raw, batman = 0.0, 0.0
    if (numerator <= 0) or (positive_term <= 0) or (denominator < 0):
        return 0    
    if denominator == 0:
        return 1       
    #experimenting with not square rooting the denominator
    #denominator = denominator ** 0.5
    batman_raw = numerator / denominator
    if math.isnan(batman_raw):            
        return 1       
    #if we're not squaring the denominator, we need this to be smaller
    batman_raw -= (negative_term ** 2) / positive_term
    batman = logistic_transform(batman_raw)            
    if batman <= cutoff:
        return 0
    return batman

def get_team_atbats(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, battingteam, weather, ballpark, ballpark_mods, team_pid_stat_data, pitcher_stat_data, innings, flip_lineup, terms, special_cases, outs_pi=3, baseline=False):    
    factor_hitcut, factor_hrscut, factor_walkcut, factor_attempt, factor_runout, reverberation, repeating = special_cases["factors"][:7]    
    team_atbat_data = {} 
    batting_mods_by_Id = {}    
    atbats = 0.0
    batters = team_pid_stat_data.get(battingteam)                
    hits, hrs, walks, hits_hrs_walks, remainder = 0.0, 0.0, 0.0, 0.0, 0.0
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
    outs_pg = innings * outs_pi           
    previous_outs_pg = outs_pg
    prev_batter_id = ""
    current_outs = 0
    while current_outs < outs_pg:                        
        guaranteed_hhw = 0
        for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):            
            #if we have any remainder, it should go to the next batter, as they either will have gotten an extra atbat or not depending
            if current_outs >= outs_pg:      
                if (remainder > 0.0) and (outs_pg > innings * outs_pi):
                    team_atbat_data[batter_id] += (remainder / 2)
                    team_atbat_data[prev_batter_id] -= (remainder / 2)
                    remainder = 0.0
                break                
            if batter_id not in team_atbat_data:
                team_atbat_data[batter_id] = 0.0                        
            hits = calc_hits(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], factor_hitcut)
            hrs = calc_hrs(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], factor_hrscut)
            walks = calc_walks(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], factor_walkcut)
            hits_hrs_walks = hits + hrs + walks
            if hits_hrs_walks >= 1:
                hits_hrs_walks == 1        
            
            if not baseline:
                if (hits + walks) >= 1:
                    steal_attempt = calc_steal_attempt(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], factor_attempt)    
                    if steal_attempt > 0:
                        baserunners_out = calc_runner_out(pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, batting_mods_by_Id[batter_id], factor_runout) 
                        added_out = baserunners_out * steal_attempt
                        current_outs += added_out                
           
            outs_pg += hits_hrs_walks if not baseline else 0.0
            
            team_atbat_data[batter_id] += 1.0                      
            if team_pid_stat_data[battingteam][batter_id]["reverberating"] and not baseline:                        
                team_atbat_data[batter_id] += reverberation
                if hits_hrs_walks > 0.0:                    
                    outs_pg += hits_hrs_walks * reverberation
            if team_pid_stat_data[battingteam][batter_id]["repeating"] and not baseline:                        
                team_atbat_data[batter_id] += repeating
                if hits_hrs_walks > 0.0:
                    outs_pg += hits_hrs_walks * repeating
            if team_atbat_data[batter_id] >= (2.0 * innings):
                #print("Unrealistic number of atbats caught, {} in {} innings".format(team_atbat_data[batter_id], innings))
                return team_atbat_data            
            remainder = (outs_pg - current_outs)
            
            current_outs += 1
            prev_batter_id = batter_id
        #need to check if we added an out for each batter in the lineup; basically flooring this to always have at least one out through the lineup        
        if guaranteed_hhw >= active_batters:
            for line_order, (bat_id, curr_batt) in enumerate(ordered_active_batters):
                team_atbat_data[bat_id] = -500.0                    
            return team_atbat_data
        if (outs_pg - previous_outs_pg) >= active_batters:      
            #print("Pretty sure we never hit this; in atbats, getting more outs_pg - previous outs than active batters, but not entire lineup guaranteed hhw")
            current_outs += 1            
            remainder = (outs_pg - (current_outs - 1))
        previous_outs_pg = outs_pg    
    for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):
        if batter_id not in team_atbat_data:
            team_atbat_data[batter_id] = 0.0    
        if (lineup_order == 0) and (remainder > 0.0) and (outs_pg > innings * outs_pi):            
            team_atbat_data[batter_id] += (remainder / 2)            
        if (lineup_order == active_batters - 1) and (remainder > 0.0) and (outs_pg > innings * outs_pi):
            team_atbat_data[batter_id] -= (remainder / 2)            
    return team_atbat_data

def calc_steal_attempt(pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, factor_const):    
    crimes, cops = 0.0, 0.0
    pitcher_data = pitcher_stat_data[pitcher]            
    batter_list_dict = [stlats for player_id, stlats in team_pid_stat_data[battingteam].items() if player_id == batter]  
    batter_data = batter_list_dict[0]
    for playerid, stlats in team_pid_stat_data[pitchingteam].items():
        cops += calc_team(terms, (("watchfulness", stlats["watchfulness"]), ("tenaciousness", stlats["tenaciousness"])), defenseMods, False)                        
    crimes = calc_team(terms, (("basethirst", batter_data["baseThirst"]), ("laserlikeness", batter_data["laserlikeness"])), battingMods, False)            

    numerator = crimes - cops
    denominator = cops
    positive_term = crimes
    negative_term = cops
    walksperatbat = calc_batman_intelligent(numerator, denominator, positive_term, negative_term, float(factor_const))

    return walksperatbat

def calc_runner_out(pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, factor_const):    
    crimes, cops = 0.0, 0.0
    pitcher_data = pitcher_stat_data[pitcher]            
    batter_list_dict = [stlats for player_id, stlats in team_pid_stat_data[battingteam].items() if player_id == batter]  
    batter_data = batter_list_dict[0]
    for playerid, stlats in team_pid_stat_data[pitchingteam].items():
        cops += calc_team(terms, (("anticapitalism", stlats["anticapitalism"]),), defenseMods, False)                        
    crimes = calc_team(terms, (("laserlikeness", batter_data["laserlikeness"]),), battingMods, False)            

    numerator = cops - crimes
    denominator = crimes
    positive_term = cops
    negative_term = crimes
    walksperatbat = calc_batman_intelligent(numerator, denominator, positive_term, negative_term, float(factor_const))

    return walksperatbat

def calc_walks(pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, factor_const):    
    pitcher_data = pitcher_stat_data[pitcher]            
    batter_list_dict = [stlats for player_id, stlats in team_pid_stat_data[battingteam].items() if player_id == batter]  
    batter_data = batter_list_dict[0]
    ruth = calc_team(terms, (("ruthlessness", pitcher_data["ruthlessness"]),), defenseMods, False)    
    moxie = calc_team(terms, (("moxie", batter_data["moxie"]),), battingMods, False)            

    numerator = moxie - ruth
    denominator = ruth
    positive_term = moxie
    negative_term = ruth
    walksperatbat = calc_batman_intelligent(numerator, denominator, positive_term, negative_term, float(factor_const))

    return walksperatbat

def calc_hits(pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, factor_const):
    team_omniscience, ballcount = 0.0, 0.0
    pitcher_data = pitcher_stat_data[pitcher]            
    batter_list_dict = [stlats for player_id, stlats in team_pid_stat_data[battingteam].items() if player_id == batter]  
    batter_data = batter_list_dict[0]
    ruth = calc_team(terms, (("ruthlessness", pitcher_data["ruthlessness"]),), defenseMods, False)    
    moxie = calc_team(terms, (("moxie", batter_data["moxie"]),), battingMods, False)        
    thwack = calc_team(terms, (("thwackability", batter_data["thwackability"]),), battingMods, False)        
    unthwack = calc_team(terms, (("unthwackability", pitcher_data["unthwackability"]),), defenseMods, False)    
    other_pitch = calc_team(terms, (("overpowerment", pitcher_data["overpowerment"]), ("coldness", pitcher_data["coldness"])), defenseMods, False)    
    other_bat = calc_team(terms, (("patheticism", batter_data["patheticism"]), ("divinity", batter_data["divinity"]), ("musclitude", batter_data["musclitude"]), ("martyrdom", batter_data["martyrdom"])), battingMods, False)
    for playerid, stlats in team_pid_stat_data[pitchingteam].items():
        team_omniscience += calc_team(terms, (("omniscience", stlats["omniscience"]),), defenseMods, False)            

    if ruth > 0.0:
        ballcount = (moxie / ruth)
    numerator = (thwack - unthwack) + other_bat - ballcount - ruth - other_pitch - team_omniscience
    denominator = unthwack + ballcount + ruth + other_pitch + team_omniscience
    positive_term = thwack + other_bat
    negative_term = unthwack + ballcount + ruth + other_pitch + team_omniscience
    hitsperatbat = calc_batman_intelligent(numerator, denominator, positive_term, negative_term, float(factor_const))

    return hitsperatbat

def calc_hrs(pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, factor_const):    
    ballcount = 0.0
    pitcher_data = pitcher_stat_data[pitcher]            
    batter_list_dict = [stlats for player_id, stlats in team_pid_stat_data[battingteam].items() if player_id == batter]  
    batter_data = batter_list_dict[0]
    ruth = calc_team(terms, (("ruthlessness", pitcher_data["ruthlessness"]),), defenseMods, False)    
    moxie = calc_team(terms, (("moxie", batter_data["moxie"]),), battingMods, False)        
    thwack = calc_team(terms, (("thwackability", batter_data["thwackability"]),), battingMods, False)        
    unthwack = calc_team(terms, (("unthwackability", pitcher_data["unthwackability"]),), defenseMods, False)   
    divinity = calc_team(terms, (("divinity", batter_data["divinity"]),), battingMods, False)        
    overpower = calc_team(terms, (("overpowerment", pitcher_data["overpowerment"]),), defenseMods, False)    
    other_pitch = calc_team(terms, (("coldness", pitcher_data["coldness"]),), defenseMods, False)    
    other_bat = calc_team(terms, (("patheticism", batter_data["patheticism"]), ("musclitude", batter_data["musclitude"]), ("martyrdom", batter_data["martyrdom"])), battingMods, False)   
    
    if ruth > 0.0:
        ballcount = (moxie / ruth)
    numerator = (divinity - overpower) + (thwack - unthwack) + other_bat - ballcount - ruth - other_pitch
    denominator = overpower + unthwack + ballcount + ruth + other_pitch
    positive_term = divinity + thwack + other_bat
    negative_term = overpower + unthwack + ballcount + ruth + other_pitch
    hrsperatbat = calc_batman_intelligent(numerator, denominator, positive_term, negative_term, float(factor_const))

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
