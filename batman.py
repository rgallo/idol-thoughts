from __future__ import division
from __future__ import print_function

import os
import math
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
            if not modterms is None:
                multiplier *= math.prod(modterms)                   
        total += term.calc(val) * multiplier        
    return total

def calc_pitcher_batter(terms, pitcher, pitcher_stat_data, team_pid_stat_data, batter, battingteam, pitchingmods, battingmods):
    pitcher = calc_pitcher(terms, pitcher, pitcher_stat_data, team_pid_stat_data, pitchingmods)
    batter = calc_batter(terms, team_pid_stat_data, batter, battingteam, battingmods)
    pitcher_batter = pitcher + batter
    return pitcher_batter

def calc_pitcher(terms, pitcher, pitcher_stat_data, team_pid_stat_data, mods):
    pitcher_data = pitcher_stat_data[pitcher]        
    termset = (
        ("unthwackability", pitcher_data["unthwackability"]),
        ("ruthlessness", pitcher_data["ruthlessness"]),
        ("overpowerment", pitcher_data["overpowerment"]),
        ("shakespearianism", pitcher_data["shakespearianism"]),
        ("coldness", pitcher_data["coldness"]))        
    return calc_team(terms, termset, mods, False)

def calc_batter(terms, team_pid_stat_data, batter, battingteam, mods):    
    batter_list_dict = [stlats for player_id, stlats in team_pid_stat_data[battingteam].items() if player_id == batter]
    batter_data = batter_list_dict[0]    
    termset = (        
        ("tragicness", batter_data["tragicness"]),
        ("patheticism", batter_data["patheticism"]),
        ("thwackability", batter_data["thwackability"]),
        ("divinity", batter_data["divinity"]),
        ("moxie", batter_data["moxie"]),
        ("musclitude", batter_data["musclitude"]),
        ("martyrdom", batter_data["martyrdom"]))
    return calc_team(terms, termset, mods, False)

def calc_everythingelse(terms, pitchingteam, battingteam, team_pid_stat_data, batter, pitchingmods, battingmods):    
    offense = calc_offense(terms, battingteam, team_pid_stat_data, batter, battingmods)
    defense = calc_defense(terms, pitchingteam, team_pid_stat_data, pitchingmods)
    everything_else = offense + defense
    return everything_else

def calc_offense(terms, battingteam, team_pid_stat_data, batter, mods):    
    batting_team_data = [stlats for player_id, stlats in team_pid_stat_data[battingteam].items() if (player_id != batter and not stlats.get("shelled", False))]
    termset = (            
        ("meanlaserlikeness", geomean([row["laserlikeness"] for row in batting_team_data])),
        ("meanbasethirst", geomean([row["baseThirst"] for row in batting_team_data])),
        ("meancontinuation", geomean([row["continuation"] for row in batting_team_data])),
        ("meangroundfriction", geomean([row["groundFriction"] for row in batting_team_data])),
        ("meanindulgence", geomean([row["indulgence"] for row in batting_team_data])),                    
        ("maxlaserlikeness", max([row["laserlikeness"] for row in batting_team_data])),
        ("maxbasethirst", max([row["baseThirst"] for row in batting_team_data])),
        ("maxcontinuation", max([row["continuation"] for row in batting_team_data])),
        ("maxgroundfriction", max([row["groundFriction"] for row in batting_team_data])),
        ("maxindulgence", max([row["indulgence"] for row in batting_team_data])))
    return calc_team(terms, termset, mods, False)

def calc_defense(terms, pitchingteam, team_pid_stat_data, mods):
    pitching_team_data = [stlats for player_id, stlats in team_pid_stat_data[pitchingteam].items()]    
    termset = (
        ("meanomniscience", geomean([row["omniscience"] for row in pitching_team_data])),
        ("meantenaciousness", geomean([row["tenaciousness"] for row in pitching_team_data])),
        ("meanwatchfulness", geomean([row["watchfulness"] for row in pitching_team_data])),
        ("meananticapitalism", geomean([row["anticapitalism"] for row in pitching_team_data])),
        ("meanchasiness", geomean([row["chasiness"] for row in pitching_team_data])),                
        ("maxomniscience", max([row["omniscience"] for row in pitching_team_data])),
        ("maxtenaciousness", max([row["tenaciousness"] for row in pitching_team_data])),
        ("maxwatchfulness", max([row["watchfulness"] for row in pitching_team_data])),
        ("maxanticapitalism", max([row["anticapitalism"] for row in pitching_team_data])),
        ("maxchasiness", max([row["chasiness"] for row in pitching_team_data])))                        
    return calc_team(terms, termset, mods, False)

def calc_stlatmod(name, pitcher_data, batter_data, team_data, stlatterm):    
    if name in helpers.PITCHING_STLATS:
        value = pitcher_data[name]
    elif name in helpers.BATTING_STLATS:        
        value = batter_data[name]    
    elif "mean" in name:        
        stlatname = name[4:]        
        if stlatname == "basethirst":
            stlatname = "baseThirst"
        if stlatname == "groundfriction":
            stlatname = "groundFriction"        
        value = geomean([row[stlatname] for row in team_data])
    else:
        stlatname = name[3:]
        if stlatname == "basethirst":
            stlatname = "baseThirst"
        if stlatname == "groundfriction":
            stlatname = "groundFriction"
        value = max([row[stlatname] for row in team_data])
    normalized_value = stlatterm.calc(value)
    base_multiplier = (1.0 / (1.0 + (2.0 ** (-1.0 * normalized_value))))                
    multiplier = 2.0 * base_multiplier
    return multiplier

def valid_stlat(name, teamisbatting):    
    if name in helpers.PITCHING_STLATS:
        return True
    elif name in helpers.BATTING_STLATS:        
        return True
    elif "mean" in name:        
        stlatname = name[4:]        
        if stlatname == "basethirst":
            stlatname = "baseThirst"
        if stlatname == "groundfriction":
            stlatname = "groundFriction"                
    else:
        stlatname = name[3:]
        if stlatname == "basethirst":
            stlatname = "baseThirst"
        if stlatname == "groundfriction":
            stlatname = "groundFriction"
    if (stlatname in helpers.DEFENSE_STLATS) or ((stlatname in helpers.BASERUNNING_STLATS) and teamisbatting):
        return True    
    return False

def get_batman_mods(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, batter, battingteam, weather, ballpark, ballpark_mods, team_stat_data, pitcher_stat_data):    
    awayMods, homeMods = collections.defaultdict(lambda: []), collections.defaultdict(lambda: [])
    lowerAwayAttrs = [attr.lower() for attr in awayAttrs]
    lowerHomeAttrs = [attr.lower() for attr in homeAttrs]    
    bird_weather = helpers.get_weather_idx("Birds")    
    batter_list_dict = [stlats for player_id, stlats in team_stat_data[battingteam].items() if player_id == batter]
    batter_data = batter_list_dict[0]
    batting_team_data = [stlats for player_id, stlats in team_stat_data[battingteam].items() if (player_id != batter and not stlats.get("shelled", False))]
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
                base_multiplier = (1.0 / (1.0 + (2.0 ** (-1.0 * normalized_value))))
                if value > 0.5:
                    multiplier = 2.0 * base_multiplier
                elif value < 0.5:
                    multiplier = 2.0 - (2.0 * base_multiplier)                
                else:
                    multiplier = 1.0
                awayMods[playerstlat].append(multiplier)
                homeMods[playerstlat].append(multiplier)    
    return awayMods, homeMods

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

def get_team_atbats(pitcher, pitchingteam, battingteam, team_pid_stat_data, pitcher_stat_data, innings, flip_lineup, terms, pitchingmods, battingmods, special_cases, outs_pi=3):    
    factor_exp, factor_const, reverberation, repeating = special_cases
    team_atbat_data = {}
    atbats, temp_factor = 0.0, 1.0
    batters = team_pid_stat_data.get(battingteam)        
    active_batters = len(batters)
    hits_hrs_walks = 0.0
    ordered_active_batters = sorted([(k, v) for k,v in batters.items() if not v["shelled"]], key=lambda x: x[1]["turnOrder"], reverse=flip_lineup)    
    outs_pg = innings * outs_pi           
    previous_outs_pg = outs_pg
    current_outs = 0
    while current_outs < outs_pg:        
        #need to check if we added an out for each batter in the lineup; basically flooring this to always have at least one out through the lineup
        if (outs_pg - previous_outs_pg) >= active_batters:            
            current_outs += 1
        previous_outs_pg = outs_pg
        for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):            
            #if we have any remainder, it should go to the next batter, as they either will have gotten an extra atbat or not depending
            if current_outs >= outs_pg:      
                if (outs_pg > (current_outs - 1)) and (outs_pg > innings * outs_pi):
                    team_atbat_data[batter_id] += (outs_pg - (current_outs - 1))
                break                
            if batter_id not in team_atbat_data:
                team_atbat_data[batter_id] = 0.0            
            pitcher_batter = calc_pitcher_batter(terms, pitcher, pitcher_stat_data, team_pid_stat_data, batter_id, battingteam, pitchingmods, battingmods)            
            everythingelse = calc_everythingelse(terms, pitchingteam, battingteam, team_pid_stat_data, batter_id, pitchingmods, battingmods)
            temp_factor = factor_exp if (pitcher_batter > 0) else 1.0            
            hits_hrs_walks = ((pitcher_batter ** float(temp_factor)) + everythingelse) * (float(factor_const) / 1000.0)
            if math.isnan(hits_hrs_walks):
                for line_order, (bat_id, curr_batt) in enumerate(ordered_active_batters):
                    team_atbat_data[bat_id] = -10000.0
                return team_atbat_data            
            if hits_hrs_walks > 1.0:
                hits_hrs_walks = 1.0
            if hits_hrs_walks > 0:
                outs_pg += hits_hrs_walks                      
            team_atbat_data[batter_id] += 1.0          
            if team_pid_stat_data[battingteam][batter_id]["reverberating"]:                        
                team_atbat_data[batter_id] += reverberation
                if hits_hrs_walks > 0.0:                    
                    outs_pg += hits_hrs_walks * reverberation
            if team_pid_stat_data[battingteam][batter_id]["repeating"]:                        
                team_atbat_data[batter_id] += repeating
                if hits_hrs_walks > 0.0:
                    outs_pg += hits_hrs_walks * repeating
            current_outs += 1                      
    for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):
        if batter_id not in team_atbat_data:
            team_atbat_data[batter_id] = 0.0    
    return team_atbat_data


def get_batman(eventofinterest, pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, defenseMods, battingMods, special_cases, outs_pi=3):       
    if eventofinterest == "abs":                
        atbats_data = get_team_atbats(pitcher, pitchingteam, battingteam, team_pid_stat_data, pitcher_stat_data, 9.0, False, terms, defenseMods, battingMods, special_cases, outs_pi)
        batman = atbats_data[batter]
    else:        
        factor_exp, factor_const = special_cases["factors"][:2]
        everythingelse = calc_defense(terms, pitchingteam, team_pid_stat_data, defenseMods)
        pitcher_batter = calc_pitcher_batter(terms, pitcher, pitcher_stat_data, team_pid_stat_data, batter, battingteam, defenseMods, battingMods)
        factor_exp = factor_exp if (pitcher_batter > 0) else 1.0
        batman = ((pitcher_batter ** float(factor_exp)) + everythingelse) * (float(factor_const) / 1000.0)
        batman = max(batman, 0.0)
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
    results = []
    for batter_id, batter in batters.items():
        if batter.get("shelled", False):
            continue
        name = batter["name"]
        batman_atbats = calculatePitcherVsBatter("abs", weather, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, ballpark, ballpark_mods)
        batman_hits = calculatePitcherVsBatter("hits", weather, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, ballpark, ballpark_mods)
        batman_homers = calculatePitcherVsBatter("hrs", weather, awayAttrs, homeAttrs, awayTeam, homeTeam, pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data, ballpark, ballpark_mods)
        at_bats = batman_atbats
        hits = batman_hits * at_bats
        homers = batman_homers * at_bats
        results.append({"name": name, "team": battingteam, "hits": hits, "homers": homers, "abs": at_bats,
                        "attrs": batter["attrs"]})
    return results
