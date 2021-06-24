from __future__ import division
from __future__ import print_function

import collections
import statistics

import helpers
import math
from helpers import StlatTerm, ParkTerm, geomean
import os

WEATHERS = ["Void", "Sunny", "Overcast", "Rainy", "Sandstorm", "Snowy", "Acidic", "Solar Eclipse",
            "Glitter", "Blooddrain", "Peanuts", "Birds", "Feedback", "Reverb"]


def calc_team(terms, termset, mods, skip_mods=False):
    total = 0.0
    for termname, val in termset:
        term = terms[termname]        
        #reset to 1 for each new termname
        multiplier = 1.0 
        if not skip_mods:            
            modterms = (mods or {}).get(termname, [])             
            multiplier *= statistics.harmonic_mean(modterms)                
        total += term.calc(val) * multiplier
    return total

def calc_player(terms, stlatname, stlatvalue, mods, skip_mods=False):    
    term = terms[stlatname]            
    multiplier = 1.0
    if not skip_mods:            
        modterms = (mods or {}).get(stlatname, [])             
        if len(modterms) > 0:
            multiplier = statistics.harmonic_mean(modterms)                
    total = term.calc(stlatvalue) * multiplier
    return total

def team_defense(terms, pitcher, teamname, mods, team_stat_data, pitcher_stat_data, skip_mods=False):
    pitcher_data = pitcher_stat_data[pitcher]
    team_data = team_stat_data[teamname]
    termset = (
        ("unthwackability", pitcher_data["unthwackability"]),
        ("ruthlessness", pitcher_data["ruthlessness"]),
        ("overpowerment", pitcher_data["overpowerment"]),
        ("shakespearianism", pitcher_data["shakespearianism"]),
        ("coldness", pitcher_data["coldness"]),
        ("meanomniscience", geomean(team_data["omniscience"])),
        ("meantenaciousness", geomean(team_data["tenaciousness"])),
        ("meanwatchfulness", geomean(team_data["watchfulness"])),
        ("meananticapitalism", geomean(team_data["anticapitalism"])),
        ("meanchasiness", geomean(team_data["chasiness"])),
        ("maxomniscience", max(team_data["omniscience"])),
        ("maxtenaciousness", max(team_data["tenaciousness"])),
        ("maxwatchfulness", max(team_data["watchfulness"])),
        ("maxanticapitalism", max(team_data["anticapitalism"])),
        ("maxchasiness", max(team_data["chasiness"])))
    return calc_team(terms, termset, mods, skip_mods=skip_mods)


def team_offense(terms, teamname, mods, team_stat_data, skip_mods=False):
    team_data = team_stat_data[teamname]
    termset = (
            ("meantragicness", geomean(team_data["tragicness"])),
            ("meanpatheticism", geomean(team_data["patheticism"])),
            ("meanthwackability", geomean(team_data["thwackability"])),
            ("meandivinity", geomean(team_data["divinity"])),
            ("meanmoxie", geomean(team_data["moxie"])),
            ("meanmusclitude", geomean(team_data["musclitude"])),
            ("meanmartyrdom", geomean(team_data["martyrdom"])),
            ("maxthwackability", max(team_data["thwackability"])),
            ("maxdivinity", max(team_data["divinity"])),
            ("maxmoxie", max(team_data["moxie"])),
            ("maxmusclitude", max(team_data["musclitude"])),
            ("maxmartyrdom", max(team_data["martyrdom"])),
            ("meanlaserlikeness", geomean(team_data["laserlikeness"])),
            ("meanbasethirst", geomean(team_data["baseThirst"])),
            ("meancontinuation", geomean(team_data["continuation"])),
            ("meangroundfriction", geomean(team_data["groundFriction"])),
            ("meanindulgence", geomean(team_data["indulgence"])),
            ("maxlaserlikeness", max(team_data["laserlikeness"])),
            ("maxbasethirst", max(team_data["baseThirst"])),
            ("maxcontinuation", max(team_data["continuation"])),
            ("maxgroundfriction", max(team_data["groundFriction"])),
            ("maxindulgence", max(team_data["indulgence"])))
    return calc_team(terms, termset, mods, skip_mods=skip_mods)

def player_batting(terms, mods, player_stat_data, skip_mods=False):    
    termset = (
            ("tragicness", player_stat_data["tragicness"]),
            ("patheticism", player_stat_data["patheticism"]),
            ("thwackability", player_stat_data["thwackability"]),
            ("divinity", player_stat_data["divinity"]),
            ("moxie", player_stat_data["moxie"]),
            ("musclitude", player_stat_data["musclitude"]),
            ("martyrdom", player_stat_data["martyrdom"])
            )
    return calc_team(terms, termset, mods, skip_mods=skip_mods)

def player_running(terms, mods, player_stat_data, skip_mods=False):    
    termset = (            
            ("laserlikeness", player_stat_data["laserlikeness"]),
            ("basethirst", player_stat_data["baseThirst"]),
            ("continuation", player_stat_data["continuation"]),
            ("groundfriction", player_stat_data["groundFriction"]),
            ("indulgence", player_stat_data["indulgence"])
            )
    return calc_team(terms, termset, mods, skip_mods=skip_mods)

def player_defense(terms, mods, player_stat_data, skip_mods=False):    
    termset = (
            ("omniscience", player_stat_data["omniscience"]),
            ("tenaciousness", player_stat_data["tenaciousness"]),
            ("watchfulness", player_stat_data["watchfulness"]),
            ("anticapitalism", player_stat_data["anticapitalism"]),
            ("chasiness", player_stat_data["chasiness"])
            )
    return calc_team(terms, termset, mods, skip_mods=skip_mods)

def player_pitching(terms, mods, player_stat_data, skip_mods=False):    
    termset = (
            ("unthwackability", player_stat_data["unthwackability"]),
            ("ruthlessness", player_stat_data["ruthlessness"]),
            ("overpowerment", player_stat_data["overpowerment"]),
            ("shakespearianism", player_stat_data["shakespearianism"]),
            ("coldness", player_stat_data["coldness"])
            )
    return calc_team(terms, termset, mods, skip_mods=skip_mods)

def calc_stlatmod(name, pitcher_data, team_data, stlatterm):    
    if name in helpers.PITCHING_STLATS:
        value = pitcher_data[name]        
    elif "mean" in name:        
        stlatname = name[4:]        
        if stlatname == "basethirst":
            stlatname = "baseThirst"
        if stlatname == "groundfriction":
            stlatname = "groundFriction"
        value = geomean(team_data[stlatname])
    else:
        stlatname = name[3:]
        if stlatname == "basethirst":
            stlatname = "baseThirst"
        if stlatname == "groundfriction":
            stlatname = "groundFriction"
        value = max(team_data[stlatname])
    normalized_value = stlatterm.calc(value)
    try:
        base_multiplier = (1.0 / (1.0 + (2.0 ** (-1.0 * normalized_value))))                
    except OverflowError:
        base_multiplier = 1.0
    multiplier = 2.0 * base_multiplier
    return multiplier

def calc_player_stlatmod(name, player_data, stlatterm):    
    if name in helpers.PITCHING_STLATS:
        if name not in player_data:
            return None
        if not player_data["ispitcher"]:
            return None
        value = player_data[name]        
    else:
        if player_data["ispitcher"]:
            return None
        stlatname = name
        if stlatname == "basethirst":
            stlatname = "baseThirst"
        if stlatname == "groundfriction":
            stlatname = "groundFriction"
        if (stlatname in helpers.BATTING_STLATS or stlatname in helpers.BASERUNNING_STLATS) and player_data["shelled"]:
            return None
        value = player_data[stlatname]    
    normalized_value = stlatterm.calc(value)
    try:
        base_multiplier = (1.0 / (1.0 + (2.0 ** (-1.0 * normalized_value))))                
    except OverflowError:
        base_multiplier = 1.0
    multiplier = 2.0 * base_multiplier
    return multiplier

def get_player_mods(mods, awayAttrs, homeAttrs, playerMods, weather, away_home, player_stat_data):            
    lowerAwayAttrs = [attr.lower() for attr in awayAttrs]
    lowerHomeAttrs = [attr.lower() for attr in homeAttrs]    
    bird_weather = helpers.get_weather_idx("Birds")    
    flood_weather = helpers.get_weather_idx("Flooding")   
    for attr in lowerAwayAttrs:    
        if attr == "affinity_for_crows" and weather != bird_weather:
            continue
        if attr == "high_pressure" and weather != flood_weather:
            continue                
        if attr in mods:            
            if away_home == "away":
                for name, stlatterm in mods[attr]["same"].items():                
                    multiplier = calc_player_stlatmod(name, player_stat_data, stlatterm)
                    if multiplier is not None:
                        playerMods[name].append(multiplier)
            if away_home == "home":
                for name, stlatterm in mods[attr]["opp"].items():                
                    multiplier = calc_player_stlatmod(name, player_stat_data, stlatterm)
                    if multiplier is not None:
                        playerMods[name].append(multiplier)

    for attr in lowerHomeAttrs:
        if attr == "affinity_for_crows" and weather != bird_weather:
            continue
        if attr == "high_pressure" and weather != flood_weather:
            continue                
        if attr in mods and attr != "traveling":
            if away_home == "home":
                for name, stlatterm in mods[attr]["same"].items():                
                    multiplier = calc_player_stlatmod(name, player_stat_data, stlatterm)
                    if multiplier is not None:
                        playerMods[name].append(multiplier)
            if away_home == "away":
                for name, stlatterm in mods[attr]["opp"].items():                
                    multiplier = calc_player_stlatmod(name, player_stat_data, stlatterm)
                    if multiplier is not None:
                        playerMods[name].append(multiplier)
    return playerMods

def get_park_mods(ballpark, ballpark_mods):
    awayMods, homeMods = collections.defaultdict(lambda: []), collections.defaultdict(lambda: [])    
    for ballparkstlat, stlatterms in ballpark_mods.items():        
        for playerstlat, stlatterm in stlatterms.items():
            if type(stlatterm) == ParkTerm:            
                value = ballpark[ballparkstlat]                
                normalized_value = stlatterm.calc(value)
                try:
                    base_multiplier = (1.0 / (1.0 + (2.0 ** (-1.0 * normalized_value))))
                except OverflowError:
                    base_multiplier = 1.0
                if value > 0.5:
                    multiplier = 2.0 * base_multiplier
                elif value < 0.5:
                    multiplier = 2.0 - (2.0 * base_multiplier)                
                else:
                    multiplier = 1.0
                if ballparkstlat != "hype":
                    awayMods[playerstlat].append(multiplier)
                homeMods[playerstlat].append(multiplier)
    return awayMods, homeMods

def setup_playerbased(weather, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, team_stat_data, pitcher_stat_data):
    terms_url = os.getenv("MOFO_TERMS")
    terms, _ = helpers.load_terms(terms_url)
    mods_url = os.getenv("MOFO_MODS")
    mods = helpers.load_mods(mods_url)
    ballparks_url = os.getenv("BALLPARKS")
    ballparks = helpers.load_ballparks(ballparks_url)
    ballpark_mods_url = os.getenv("MOFO_BALLPARK_TERMS")
    ballpark_mods = helpers.load_bp_terms(ballpark_mods_url)
    homeTeamId = helpers.get_team_id(homeTeam)
    ballpark = ballparks.get(homeTeamId, collections.defaultdict(lambda: 0.5))
    awayMods, homeMods = get_park_mods(ballpark, ballpark_mods)
    return mods, terms, awayMods, homeMods


def calculate_playerbased(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, awayAttrs, homeAttrs,
              day, weather, skip_mods=False):    
    mods, terms, awayMods, homeMods = setup_playerbased(weather, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, team_stat_data, pitcher_stat_data)
    return get_mofo_playerbased(mods, awayPitcher, homePitcher, awayTeam, homeTeam, awayAttrs, homeAttrs, team_stat_data, pitcher_stat_data, terms, awayMods,
                    homeMods, skip_mods=skip_mods)

def calc_defense(terms, player_mods, player_stat_data):   
    player_omniscience = calc_player(terms, "omniscience", player_stat_data["omniscience"], player_mods, False)
    player_watchfulness = calc_player(terms, "watchfulness", player_stat_data["watchfulness"], player_mods, False)
    player_chasiness = calc_player(terms, "chasiness", player_stat_data["chasiness"], player_mods, False)
    player_anticapitalism = calc_player(terms, "anticapitalism", player_stat_data["anticapitalism"], player_mods, False)
    player_tenaciousness = calc_player(terms, "tenaciousness", player_stat_data["tenaciousness"], player_mods, False)        
    return player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness

def calc_batting(terms, player_mods, player_stat_data):            
    player_patheticism = calc_player(terms, "patheticism", player_stat_data["patheticism"], player_mods, False)
    player_tragicness = calc_player(terms, "tragicness", player_stat_data["tragicness"], player_mods, False)
    player_thwackability = calc_player(terms, "thwackability", player_stat_data["thwackability"], player_mods, False)
    player_divinity = calc_player(terms, "divinity", player_stat_data["divinity"], player_mods, False)
    player_moxie = calc_player(terms, "moxie", player_stat_data["moxie"], player_mods, False)
    player_musclitude = calc_player(terms, "musclitude", player_stat_data["musclitude"], player_mods, False)
    player_martyrdom = calc_player(terms, "martyrdom", player_stat_data["martyrdom"], player_mods, False)    
    return player_patheticism, player_tragicness, player_thwackability, player_divinity, player_moxie, player_musclitude, player_martyrdom

def calc_running(terms, player_mods, player_stat_data):            
    player_laserlikeness = calc_player(terms, "laserlikeness", player_stat_data["laserlikeness"], player_mods, False)
    player_basethirst = calc_player(terms, "basethirst", player_stat_data["baseThirst"], player_mods, False)
    player_continuation = calc_player(terms, "continuation", player_stat_data["continuation"], player_mods, False)
    player_groundfriction = calc_player(terms, "groundfriction", player_stat_data["groundFriction"], player_mods, False)
    player_indulgence = calc_player(terms, "indulgence", player_stat_data["indulgence"], player_mods, False)     
    return player_laserlikeness, player_basethirst, player_continuation, player_groundfriction, player_indulgence

def calc_pitching(terms, pitcher_mods, pitcher_stat_data):            
    player_unthwackability = calc_player(terms, "unthwackability", pitcher_stat_data["unthwackability"], pitcher_mods, False)
    player_ruthlessness = calc_player(terms, "ruthlessness", pitcher_stat_data["ruthlessness"], pitcher_mods, False)
    player_overpowerment = calc_player(terms, "overpowerment", pitcher_stat_data["overpowerment"], pitcher_mods, False)
    player_shakespearianism = calc_player(terms, "shakespearianism", pitcher_stat_data["shakespearianism"], pitcher_mods, False)
    player_coldness = calc_player(terms, "coldness", pitcher_stat_data["coldness"], pitcher_mods, False)
    return player_unthwackability, player_ruthlessness, player_overpowerment, player_shakespearianism, player_coldness

def calc_team_score(team_stat_data, opp_stat_data, pitcher_stat_data, adjustments):
    team_score = 0.0
        
    unthwack_adjust, ruth_adjust, overp_adjust, shakes_adjust, cold_adjust, path_adjust, trag_adjust, thwack_adjust, div_adjust, moxie_adjust, muscl_adjust, martyr_adjust, omni_adjust, watch_adjust, tenacious_adjust, chasi_adjust, anticap_adjust, laser_adjust, basethirst_adjust, groundfriction_adjust, continuation_adjust, indulgence_adjust, max_thwack, max_moxie, max_ruth = adjustments

    omniscience, watchfulness, chasiness, anticap, tenaciousness = opp_stat_data["omniscience"], opp_stat_data["watchfulness"], opp_stat_data["chasiness"], opp_stat_data["anticapitalism"], opp_stat_data["tenaciousness"]
    unthwackability, ruthlessness, overpowerment, shakespearianism, coldness = pitcher_stat_data["unthwackability"], pitcher_stat_data["ruthlessness"], pitcher_stat_data["overpowerment"], pitcher_stat_data["shakespearianism"], pitcher_stat_data["coldness"]

    omni, watch, anti, chasi, tenacious = (omniscience - omni_adjust), (watchfulness - watch_adjust), (anticap - anticap_adjust), (chasiness - chasi_adjust), (tenaciousness - tenacious_adjust)
    unthwack, overp, shakes, cold = (unthwackability - unthwack_adjust), (overpowerment - overp_adjust), (shakespearianism - shakes_adjust), (coldness - cold_adjust)

    strike_chance = (ruthlessness - ruth_adjust) / (max_ruth - ruth_adjust)
    
    for playerid in team_stat_data:                
        patheticism, tragicness, thwackability, divinity, moxie, musclitude, martyrdom = team_stat_data[playerid]["patheticism"], team_stat_data[playerid]["tragicness"], team_stat_data[playerid]["thwackability"], team_stat_data[playerid]["divinity"], team_stat_data[playerid]["moxie"], team_stat_data[playerid]["musclitude"], team_stat_data[playerid]["martyrdom"]
        laserlikeness, basethirst, continuation, groundfriction, indulgence = team_stat_data[playerid]["laserlikeness"], team_stat_data[playerid]["basethirst"], team_stat_data[playerid]["continuation"], team_stat_data[playerid]["groundfriction"], team_stat_data[playerid]["indulgence"]
            
        path, tragic, thwack, div, muscl, martyr = (patheticism - path_adjust), (tragicness - trag_adjust), (thwackability - thwack_adjust), (divinity - div_adjust), (musclitude - muscl_adjust), (martyrdom - martyr_adjust)
        laser, baset, cont, ground, indulg = (laserlikeness - laser_adjust), (basethirst - basethirst_adjust), (continuation - continuation_adjust), (groundfriction - groundfriction_adjust), (indulgence - indulgence_adjust)                        

        base_hit_chance = (max((thwack - unthwack - path - omni), 0.0) / (max_thwack - thwack_adjust)) * strike_chance                  
        walk_chance = ((moxie - moxie_adjust) / (max_moxie - moxie_adjust)) * (1.0 - strike_chance)  
            
        base_steal_score = (baset + laser - watch - anti) * min((base_hit_chance + walk_chance), 1.0)
        on_base_score = (laser + cont + indulg - tragic - cold - tenacious) * min(base_hit_chance + walk_chance, 1.0)
        hit_score = max((ground + muscl + martyr - overp - chasi - shakes), 0.0) * base_hit_chance
        homerun_score = max((thwack + div - path - overp - unthwack), 0.0) * strike_chance
        team_score += base_steal_score + on_base_score + hit_score + homerun_score

    return team_score

def calc_player_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, player_stat_data):
    playerMods = get_player_mods(mods, awayAttrs, homeAttrs, teamMods, weather, away_home, player_stat_data)
    calced_stlats = {}
    player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness = calc_defense(terms, playerMods, player_stat_data)
    if not player_stat_data["shelled"]:
        calced_stlats["patheticism"], calced_stlats["tragicness"], calced_stlats["thwackability"], calced_stlats["divinity"], calced_stlats["moxie"], calced_stlats["musclitude"], calced_stlats["martyrdom"] = calc_batting(terms, playerMods, player_stat_data)
        calced_stlats["laserlikeness"], calced_stlats["basethirst"], calced_stlats["continuation"], calced_stlats["groundfriction"], calced_stlats["indulgence"] = calc_running(terms, playerMods, player_stat_data)    
        return calced_stlats, player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness
    return player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness

def calc_pitcher_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, player_stat_data):
    playerMods = get_player_mods(mods, awayAttrs, homeAttrs, teamMods, weather, away_home, player_stat_data)
    calced_stlats = {}    
    calced_stlats["unthwackability"], calced_stlats["ruthlessness"], calced_stlats["overpowerment"], calced_stlats["shakespearianism"], calced_stlats["coldness"] = calc_pitching(terms, playerMods, player_stat_data)
    return calced_stlats
    
def get_mofo_playerbased(mods, awayPitcher, homePitcher, awayTeam, homeTeam, awayAttrs, homeAttrs, weather, team_stat_data, pitcher_stat_data, terms, awayMods, homeMods, adjustments, skip_mods=False):          
    polarity_plus, polarity_minus = helpers.get_weather_idx("Polarity +"), helpers.get_weather_idx("Polarity -")
    if weather == polarity_plus or weather == polarity_minus:
        return .5, .5
    
    away_team_stlats, home_team_stlats, away_team_defense, home_team_defense = {}, {}, {}, {}
    away_lineup, home_lineup = 0, 0
    away_team_defense["omniscience"], away_team_defense["watchfulness"], away_team_defense["chasiness"], away_team_defense["anticapitalism"], away_team_defense["tenaciousness"] = 0.0, 0.0, 0.0, 0.0, 0.0
    home_team_defense["omniscience"], home_team_defense["watchfulness"], home_team_defense["chasiness"], home_team_defense["anticapitalism"], home_team_defense["tenaciousness"] = 0.0, 0.0, 0.0, 0.0, 0.0

    for playerid in team_stat_data[awayTeam]:
        if not team_stat_data[awayTeam][playerid]["shelled"]:
            away_team_stlats[playerid] = {}
            away_team_stlats[playerid], player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness = calc_player_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, "away", team_stat_data[awayTeam][playerid])        
        else:
            player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness = calc_player_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, "away", team_stat_data[awayTeam][playerid])        
        away_lineup += 1
        away_team_defense["omniscience"] += player_omniscience
        away_team_defense["watchfulness"] += player_watchfulness
        away_team_defense["chasiness"] += player_chasiness
        away_team_defense["anticapitalism"] += player_anticapitalism
        away_team_defense["tenaciousness"] += player_tenaciousness
    away_team_defense["omniscience"] = away_team_defense["omniscience"] / away_lineup
    away_team_defense["watchfulness"] = away_team_defense["watchfulness"] / away_lineup
    away_team_defense["chasiness"] = away_team_defense["chasiness"] / away_lineup
    away_team_defense["anticapitalism"] = away_team_defense["anticapitalism"] / away_lineup
    away_team_defense["tenaciousness"] = away_team_defense["tenaciousness"] / away_lineup
    awayPitcherStlats = calc_pitcher_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, "away", pitcher_stat_data[awayPitcher])

    for playerid in team_stat_data[homeTeam]:
        if not team_stat_data[homeTeam][playerid]["shelled"]:
            home_team_stlats[playerid] = {}
            home_team_stlats[playerid], player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness = calc_player_stlats(terms, mods, awayAttrs, homeAttrs, homeMods, weather, "home", team_stat_data[homeTeam][playerid])
        else:
            player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness = calc_player_stlats(terms, mods, awayAttrs, homeAttrs, homeMods, weather, "home", team_stat_data[homeTeam][playerid])
        home_lineup += 1
        home_team_defense["omniscience"] += player_omniscience
        home_team_defense["watchfulness"] += player_watchfulness
        home_team_defense["chasiness"] += player_chasiness
        home_team_defense["anticapitalism"] += player_anticapitalism
        home_team_defense["tenaciousness"] += player_tenaciousness
    home_team_defense["omniscience"] = home_team_defense["omniscience"] / home_lineup
    home_team_defense["watchfulness"] = home_team_defense["watchfulness"] / home_lineup
    home_team_defense["chasiness"] = home_team_defense["chasiness"] / home_lineup
    home_team_defense["anticapitalism"] = home_team_defense["anticapitalism"] / home_lineup
    home_team_defense["tenaciousness"] = home_team_defense["tenaciousness"] / home_lineup
    homePitcherStlats = calc_pitcher_stlats(terms, mods, awayAttrs, homeAttrs, homeMods, weather, "home", pitcher_stat_data[homePitcher])   
    
    away_score = calc_team_score(away_team_stlats, home_team_defense, homePitcherStlats, adjustments)
    home_score = calc_team_score(home_team_stlats, away_team_defense, awayPitcherStlats, adjustments)   

    numerator = away_score - home_score
    denominator = abs(away_score + home_score)
    if not denominator:
        return .5, .5    
    away_formula = numerator / denominator    
    try:
        away_odds = (1 / (1 + (100 ** (-1 * away_formula))))
    except OverflowError:
        away_odds = 1.0
    return away_odds, 1.0 - away_odds

def get_mods(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, weather, ballpark, ballpark_mods, team_stat_data, pitcher_stat_data):
    awayMods, homeMods = collections.defaultdict(lambda: []), collections.defaultdict(lambda: [])
    lowerAwayAttrs = [attr.lower() for attr in awayAttrs]
    lowerHomeAttrs = [attr.lower() for attr in homeAttrs]    
    bird_weather = helpers.get_weather_idx("Birds")    
    flood_weather = helpers.get_weather_idx("Flooding")    
    for attr in mods:
        # Special case for Affinity for Crows and High Pressure
        if attr == "affinity_for_crows" and weather != bird_weather:
            continue
        if attr == "high_pressure" and weather != flood_weather:
            continue        
        if attr in lowerAwayAttrs:            
            for name, stlatterm in mods[attr]["same"].items():
                multiplier = calc_stlatmod(name, pitcher_stat_data[awayPitcher], team_stat_data[awayTeam], stlatterm)
                awayMods[name].append(multiplier)
            for name, stlatterm in mods[attr]["opp"].items():
                multiplier = calc_stlatmod(name, pitcher_stat_data[homePitcher], team_stat_data[homeTeam], stlatterm)
                homeMods[name].append(multiplier)
        if attr in lowerHomeAttrs and attr != "traveling":
            for name, stlatterm in mods[attr]["same"].items():
                multiplier = calc_stlatmod(name, pitcher_stat_data[homePitcher], team_stat_data[homeTeam], stlatterm)
                homeMods[name].append(multiplier)
            for name, stlatterm in mods[attr]["opp"].items():
                multiplier = calc_stlatmod(name, pitcher_stat_data[awayPitcher], team_stat_data[awayTeam], stlatterm)
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
                if ballparkstlat != "hype":
                    awayMods[playerstlat].append(multiplier)
                homeMods[playerstlat].append(multiplier)
    return awayMods, homeMods


def setup(weather, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, team_stat_data, pitcher_stat_data):
    terms_url = os.getenv("MOFO_TERMS")
    terms, _ = helpers.load_terms(terms_url)
    mods_url = os.getenv("MOFO_MODS")
    mods = helpers.load_mods(mods_url)
    ballparks_url = os.getenv("BALLPARKS")
    ballparks = helpers.load_ballparks(ballparks_url)
    ballpark_mods_url = os.getenv("MOFO_BALLPARK_TERMS")
    ballpark_mods = helpers.load_bp_terms(ballpark_mods_url)
    homeTeamId = helpers.get_team_id(homeTeam)
    ballpark = ballparks.get(homeTeamId, collections.defaultdict(lambda: 0.5))
    awayMods, homeMods = get_mods(mods, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, weather, ballpark, ballpark_mods, team_stat_data, pitcher_stat_data)
    return terms, awayMods, homeMods


def calculate(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, awayAttrs, homeAttrs,
              day, weather, skip_mods=False):
    terms, awayMods, homeMods = setup(weather, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, team_stat_data, pitcher_stat_data)
    return get_mofo(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, terms, awayMods,
                    homeMods, skip_mods=skip_mods)


def get_mofo(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, terms, awayMods, homeMods,
             skip_mods=False):
    away_offense = abs(team_offense(terms, awayTeam, awayMods, team_stat_data, skip_mods=skip_mods))
    away_defense = abs(team_defense(terms, awayPitcher, awayTeam, awayMods, team_stat_data, pitcher_stat_data,
                                    skip_mods=skip_mods))
    home_offense = abs(team_offense(terms, homeTeam, homeMods, team_stat_data, skip_mods=skip_mods))
    home_defense = abs(team_defense(terms, homePitcher, homeTeam, homeMods, team_stat_data, pitcher_stat_data,
                                    skip_mods=skip_mods))
    numerator = (away_offense - home_defense) - (home_offense - away_defense)
    denominator = abs((away_offense - home_defense) + (home_offense - away_defense))
    if not denominator:
        return .5, .5    
    away_formula = numerator / denominator    
    try:
        away_odds = (1 / (1 + (100 ** (-1 * away_formula))))
    except OverflowError:
        away_odds = 1.0
    return away_odds, 1.0 - away_odds
