from __future__ import division
from __future__ import print_function

import collections
import copy
import datetime

import helpers
import math
import numpy as np
from helpers import StlatTerm, ParkTerm, geomean
import os

WEATHERS = ["Void", "Sunny", "Overcast", "Rainy", "Sandstorm", "Snowy", "Acidic", "Solar Eclipse",
            "Glitter", "Blooddrain", "Peanuts", "Birds", "Feedback", "Reverb"]

MODS_CALCED_DIFFERENTLY = {"aaa", "aa", "a", "fiery", "base_instincts", "o_no", "electric", "h20", "0", "acidic", "love", "high_pressure", "psychic"}

def instantiate_adjustments(terms, halfterms): 
    adjustments = {}    
    for stlat in halfterms:        
        for event in halfterms[stlat]:  
            val = halfterms[stlat][event]
            calced_val = terms[event].calc(abs(val))
            try:
                adjustments[event] = calced_val * (val / abs(val))
            except ZeroDivisionError:
                adjustments[event] = calced_val              
    return adjustments

def calc_team(terms, termset, mods, skip_mods=False):
    total = 0.0
    for termname, val in termset:
        term = terms[termname]        
        #reset to 1 for each new termname
        multiplier = 1.0 
        if not skip_mods:            
            modterms = (mods or {}).get(termname, [])             
            multiplier = sum(modterms) / len(modterms)
        total += term.calc(val) * multiplier
    return total

def calc_player(terms, stlatname, stlatvalue, mods, parkmods, bloodmods, skip_mods=False):    
    term = terms[stlatname]            
    multiplier = 1.0    
    if not skip_mods and stlatname in parkmods:  
        #if parkmods[stlatname] > 1.0:
        #    print("Parkmod {} = {}".format(stlatname, parkmods[stlatname]))        
        multiplier *= parkmods[stlatname]
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
    base_multiplier = log_transform(normalized_value, 100.0)    
    #forcing harmonic mean with quicker process time?
    multiplier = 1.0 / (2.0 * base_multiplier)
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
    base_multiplier = stlatterm
    #base_multiplier = log_transform(normalized_value, 100.0)    
    #forcing harmonic mean with quicker process time?
    if base_multiplier > 0.0:
        multiplier = 1.0 / (2.0 * base_multiplier)
    else:
        multiplier = 20000000000.0
    return multiplier

def log_transform(value, base):                
    try:
        denominator = (1.0 + (base ** (-1.0 * value)))        
        transformed_value = 1.0 / denominator
    except:                    
        transformed_value = 1.0 if (value > 0) else 0.0
    return transformed_value

def prob_adjust(prob, multiplier):    
    odds = prob / (1 - prob)
    new_odds = odds * (1 + multiplier)
    new_prob = new_odds / (1 + new_odds)
    return new_prob

def calc_defense(terms, player_mods, park_mods, player_stat_data, adjusted_stlats, bloodMods=None, overperform_pct=0):
    if overperform_pct > 0.01:                
        player_stat_data["omniscience"] += (adjusted_stlats["omniscience"] - player_stat_data["omniscience"]) * overperform_pct
        player_stat_data["watchfulness"] += (adjusted_stlats["watchfulness"] - player_stat_data["watchfulness"]) * overperform_pct 
        player_stat_data["chasiness"] += (adjusted_stlats["chasiness"] - player_stat_data["chasiness"]) * overperform_pct 
        player_stat_data["anticapitalism"] += (adjusted_stlats["anticapitalism"] - player_stat_data["anticapitalism"]) * overperform_pct 
        player_stat_data["tenaciousness"] += (adjusted_stlats["tenaciousness"] - player_stat_data["tenaciousness"]) * overperform_pct
    player_omni_base_hit = calc_player(terms, "omni_base_hit", player_stat_data["omniscience"], player_mods, park_mods, bloodMods, False)
    player_watch_attempt_steal = calc_player(terms, "watch_attempt_steal", player_stat_data["watchfulness"], player_mods, park_mods, bloodMods, False)
    player_chasi_triple = calc_player(terms, "chasi_triple", player_stat_data["chasiness"], player_mods, park_mods, bloodMods, False)
    player_chasi_double = calc_player(terms, "chasi_double", player_stat_data["chasiness"], player_mods, park_mods, bloodMods, False)
    player_anticap_base = calc_player(terms, "anticap_caught_steal_base", player_stat_data["anticapitalism"], player_mods, park_mods, bloodMods, False)
    player_anticap_home = calc_player(terms, "anticap_caught_steal_home", player_stat_data["anticapitalism"], player_mods, park_mods, bloodMods, False)
    player_tenacious_ra = calc_player(terms, "tenacious_runner_advances", player_stat_data["tenaciousness"], player_mods, park_mods, bloodMods, False)        
    return player_omni_base_hit, player_watch_attempt_steal, player_chasi_triple, player_chasi_double, player_anticap_base, player_anticap_home, player_tenacious_ra

def calc_batting(terms, player_mods, park_mods, player_stat_data, adjusted_stlats, bloodMods=None, overperform_pct=0):  
    if overperform_pct > 0.01:                
        player_stat_data["patheticism"] += (adjusted_stlats["patheticism"] - player_stat_data["patheticism"]) * overperform_pct
        player_stat_data["tragicness"] += (adjusted_stlats["tragicness"] - player_stat_data["tragicness"]) * overperform_pct
        player_stat_data["thwackability"] += (adjusted_stlats["thwackability"] - player_stat_data["thwackability"]) * overperform_pct
        player_stat_data["divinity"] += (adjusted_stlats["divinity"] - player_stat_data["divinity"]) * overperform_pct 
        player_stat_data["moxie"] += (adjusted_stlats["moxie"] - player_stat_data["moxie"]) * overperform_pct 
        player_stat_data["musclitude"] += (adjusted_stlats["musclitude"] - player_stat_data["musclitude"]) * overperform_pct 
        player_stat_data["martyrdom"] += (adjusted_stlats["martyrdom"] - player_stat_data["martyrdom"]) * overperform_pct        
    player_path_connect = calc_player(terms, "path_connect", player_stat_data["patheticism"], player_mods, park_mods, bloodMods, False)
    player_trag_ra = calc_player(terms, "trag_runner_advances", player_stat_data["tragicness"], player_mods, park_mods, bloodMods, False)
    player_thwack_base_hit = calc_player(terms, "thwack_base_hit", player_stat_data["thwackability"], player_mods, park_mods, bloodMods, False)
    player_div_homer = calc_player(terms, "div_homer", player_stat_data["divinity"], player_mods, park_mods, bloodMods, False)
    player_moxie_swing_correct = calc_player(terms, "moxie_swing_correct", player_stat_data["moxie"], player_mods, park_mods, bloodMods, False)
    player_muscl_foul_ball = calc_player(terms, "muscl_foul_ball", player_stat_data["musclitude"], player_mods, park_mods, bloodMods, False)
    player_muscl_triple = calc_player(terms, "muscl_triple", player_stat_data["musclitude"], player_mods, park_mods, bloodMods, False)
    player_muscl_double = calc_player(terms, "muscl_double", player_stat_data["musclitude"], player_mods, park_mods, bloodMods, False)
    player_martyr_sacrifice = calc_player(terms, "martyr_sacrifice", player_stat_data["martyrdom"], player_mods, park_mods, bloodMods, False)    
    return player_path_connect, player_trag_ra, player_thwack_base_hit, player_div_homer, player_moxie_swing_correct, player_muscl_foul_ball, player_muscl_triple, player_muscl_double, player_martyr_sacrifice

def calc_running(terms, player_mods, park_mods, player_stat_data, adjusted_stlats, bloodMods=None, overperform_pct=0):
    if overperform_pct > 0.01:                
        player_stat_data["laserlikeness"] += (adjusted_stlats["laserlikeness"] - player_stat_data["laserlikeness"]) * overperform_pct
        player_stat_data["baseThirst"] += (adjusted_stlats["baseThirst"] - player_stat_data["baseThirst"]) * overperform_pct 
        player_stat_data["continuation"] += (adjusted_stlats["continuation"] - player_stat_data["continuation"]) * overperform_pct 
        player_stat_data["groundFriction"] += (adjusted_stlats["groundFriction"] - player_stat_data["groundFriction"]) * overperform_pct 
        player_stat_data["indulgence"] += (adjusted_stlats["indulgence"] - player_stat_data["indulgence"]) * overperform_pct
    player_laser_attempt_steal = calc_player(terms, "laser_attempt_steal", player_stat_data["laserlikeness"], player_mods, park_mods, bloodMods, False)
    player_laser_caught_steal_base = calc_player(terms, "laser_caught_steal_base", player_stat_data["laserlikeness"], player_mods, park_mods, bloodMods, False)
    player_laser_caught_steal_home = calc_player(terms, "laser_caught_steal_home", player_stat_data["laserlikeness"], player_mods, park_mods, bloodMods, False)
    player_laser_runner_advances = calc_player(terms, "laser_runner_advances", player_stat_data["laserlikeness"], player_mods, park_mods, bloodMods, False)
    player_baset_attempt_steal = calc_player(terms, "baset_attempt_steal", player_stat_data["baseThirst"], player_mods, park_mods, bloodMods, False)
    player_baset_caught_steal_home = calc_player(terms, "baset_caught_steal_home", player_stat_data["baseThirst"], player_mods, park_mods, bloodMods, False)
    player_cont_triple = calc_player(terms, "cont_triple", player_stat_data["continuation"], player_mods, park_mods, bloodMods, False)
    player_cont_double = calc_player(terms, "cont_double", player_stat_data["continuation"], player_mods, park_mods, bloodMods, False)
    player_ground_triple = calc_player(terms, "ground_triple", player_stat_data["groundFriction"], player_mods, park_mods, bloodMods, False)
    player_indulg_runner_advances = calc_player(terms, "indulg_runner_advances", player_stat_data["indulgence"], player_mods, park_mods, bloodMods, False)     
    return player_laser_attempt_steal, player_laser_caught_steal_base, player_laser_caught_steal_home, player_laser_runner_advances, player_baset_attempt_steal, player_baset_caught_steal_home, player_cont_triple, player_cont_double, player_ground_triple, player_indulg_runner_advances

def calc_pitching(terms, pitcher_mods, park_mods, pitcher_stat_data, bloodMods=None):   
    player_unthwack_base_hit = calc_player(terms, "unthwack_base_hit", pitcher_stat_data["unthwackability"], pitcher_mods, park_mods, bloodMods, False)
    player_ruth_strike = calc_player(terms, "ruth_strike", pitcher_stat_data["ruthlessness"], pitcher_mods, park_mods, bloodMods, False)
    player_overp_homer = calc_player(terms, "overp_homer", pitcher_stat_data["overpowerment"], pitcher_mods, park_mods, bloodMods, False)
    player_overp_triple = calc_player(terms, "overp_triple", pitcher_stat_data["overpowerment"], pitcher_mods, park_mods, bloodMods, False)
    player_overp_double = calc_player(terms, "overp_double", pitcher_stat_data["overpowerment"], pitcher_mods, park_mods, bloodMods, False)
    player_shakes_runner_advances = calc_player(terms, "shakes_runner_advances", pitcher_stat_data["shakespearianism"], pitcher_mods, park_mods, bloodMods, False)
    #player_cold_clutch_factor = calc_player(terms, "cold_clutch_factor", pitcher_stat_data["coldness"], pitcher_mods, park_mods, bloodMods, False)
    player_cold_clutch_factor = 1.0
    return player_unthwack_base_hit, player_ruth_strike, player_overp_homer, player_overp_triple, player_overp_double, player_shakes_runner_advances, player_cold_clutch_factor

def calc_probs_from_stats(mods, weather, parkMods, team_stat_data, opp_stat_data, pitcher_stat_data, team_data, opp_data, pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, blood_calc=None, innings=9, outs=3):
    battingAttrs, opponentAttrs = teamAttrs, oppAttrs    
    pitcherAttrs = pitcher_data["attrs"]
    strike_out_chance, caught_out_chance, attempt_steal_chance, walk_chance, hit_modifier, sacrifice_chance, runner_advance_chance, homerun_multipliers, caught_steal_base_chance, caught_steal_home_chance = {}, {}, {}, {}, {}, {}, {}, {}, {}, {}
    single_chance, double_chance, triple_chance, homerun_chance, score_multiplier, average_on_base_position, steal_mod, caught_steal_outs, on_base_chance, high_pressure_mod = {}, {}, {}, {}, {}, {}, {}, {}, {}, {}

    blood_count = 12.0
    a_blood_multiplier = 1.0 / blood_count    

    omni_base_hit, watch_attempt_steal, chasi_triple, chasi_double, anticap_caught_steal_base, anticap_caught_steal_home, tenacious_runner_advances = opp_stat_data["omni_base_hit"], opp_stat_data["watch_attempt_steal"], opp_stat_data["chasi_triple"], opp_stat_data["chasi_double"], opp_stat_data["anticap_caught_steal_base"], opp_stat_data["anticap_caught_steal_home"], opp_stat_data["tenacious_runner_advances"]
    unthwack_base_hit, ruth_strike, overp_homer, overp_triple, overp_double, shakes_runner_advances, cold_clutch_factor = pitcher_stat_data["unthwack_base_hit"], pitcher_stat_data["ruth_strike"], pitcher_stat_data["overp_homer"], pitcher_stat_data["overp_triple"], pitcher_stat_data["overp_double"], pitcher_stat_data["shakes_runner_advances"], pitcher_stat_data["cold_clutch_factor"]    
        
    log_transform_base = math.e
    #log_transform_base = 10.0
    pitcher_homer_multiplier = -1.0 if "underhanded" in pitcherAttrs else 1.0  
    pitcher_hit_multiplier = 1.0
    score_mult_pitcher = 1.0
    if "magnify_2x" in pitcherAttrs:
        score_mult_pitcher *= 2.0
    if "magnify_3x" in pitcherAttrs:
        score_mult_pitcher *= 3.0
    if "magnify_4x" in pitcherAttrs:
        score_mult_pitcher *= 4.0
    if "magnify_5x" in pitcherAttrs:
        score_mult_pitcher *= 5.0
    #positive strike mod means fewer average strikes per strikeout; negative means more
    strike_mod, walk_buff, strike_to_walk, walk_to_strike, walk_mod, score_mod = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    if "fiery" in opponentAttrs:                
        strike_mod += mods["fiery"]["same"]["multiplier"]
    if "psychic" in opponentAttrs:
        walk_to_strike += mods["psychic"]["same"]["striketrick"]
    if "love" in opponentAttrs:
        strike_mod += mods["love"]["opp"]["strikeout"]
    if "acidic" in opponentAttrs:                
        score_mod += mods["acidic"]["same"]["multiplier"]
    if "electric" in battingAttrs:
        strike_mod -= mods["electric"]["same"]["multiplier"]
    if "psychic" in battingAttrs:
        strike_to_walk += mods["psychic"]["same"]["walktrick"]
    if "love" in battingAttrs:
        walk_buff += mods["love"]["opp"]["easypitch"]
    if "base_instincts" in battingAttrs:
        walk_mod += mods["base_instincts"]["same"]["multiplier"]
    if "a" in opponentAttrs:
        strike_mod += mods["fiery"]["same"]["multiplier"] * a_blood_multiplier
        strike_mod += mods["love"]["opp"]["strikeout"] * a_blood_multiplier
        walk_to_strike += mods["psychic"]["same"]["striketrick"] * a_blood_multiplier
        score_mod += mods["acidic"]["same"]["multiplier"] * a_blood_multiplier
    if "a" in battingAttrs:
        strike_mod -= mods["electric"]["same"]["multiplier"] * a_blood_multiplier
        walk_buff += mods["love"]["opp"]["easypitch"] * a_blood_multiplier
        walk_mod += mods["base_instincts"]["same"]["multiplier"] * a_blood_multiplier
        strike_to_walk += mods["psychic"]["same"]["walktrick"] * a_blood_multiplier        

    strike_log = ruth_strike - adjustments["ruth_strike"]
    strike_prob = log_transform(strike_log, log_transform_base)    
    try:
        test = 1 / (strike_prob - 1)
        strike_chance = prob_adjust(strike_prob, parkMods["plus_strike"])
    except (FloatingPointError, ZeroDivisionError):        
        strike_chance = strike_prob
    #clutch_log = (cold_clutch_factor - adjustments["cold_clutch_factor"]) / (cold_clutch_factor + adjustments["cold_clutch_factor"])
    #clutch_factor = log_transform(clutch_log, log_transform_base)            
    clutch_factor = 0.0
        
    for playerid in sorted_batters:                                                                    
        playerAttrs = team_data[playerid]["attrs"]
        homer_multiplier = pitcher_homer_multiplier
        hit_multiplier = pitcher_hit_multiplier
        homer_multiplier *= -1.0 if "subtractor" in playerAttrs else 1.0
        homer_multiplier *= -1.0 if "underachiever" in playerAttrs else 1.0
        hit_multiplier *= -1.0 if "subtractor" in playerAttrs else 1.0
        strike_count = 4.0 if (("extra_strike" in battingAttrs) or ("extra_strike" in playerAttrs)) else 3.0
        strike_count -= 1.0 if "flinch" in playerAttrs else 0.0
        ball_count = 3.0 if (("walk_in_the_park" in battingAttrs) or ("walk_in_the_park" in playerAttrs)) else 4.0            
        steal_mod[playerid] = 20.0 if ("blaserunning" in battingAttrs or "blaserunning" in playerAttrs) else 0.0        
        if "skipping" in playerAttrs:            
            average_strikes = (strike_count - 1.0) / 2.0
            average_balls = (ball_count - 1.0) / 2.0            
            strike_count -= average_strikes            
            strike_count = max(strike_count, 1.0)
            ball_count -= average_balls
        score_multiplier[playerid] = score_mult_pitcher
        if "magnify_2x" in playerAttrs:
            score_multiplier[playerid] *= 2.0
        if "magnify_3x" in playerAttrs:
            score_multiplier[playerid] *= 3.0
        if "magnify_4x" in playerAttrs:
            score_multiplier[playerid] *= 4.0
        if "magnify_5x" in playerAttrs:
            score_multiplier[playerid] *= 5.0
        path_connect, trag_runner_advances, thwack_base_hit, div_homer, moxie_swing_correct, muscl_foul_ball, muscl_triple, muscl_double, martyr_sacrifice = team_stat_data[playerid]["path_connect"], team_stat_data[playerid]["trag_runner_advances"], team_stat_data[playerid]["thwack_base_hit"], team_stat_data[playerid]["div_homer"], team_stat_data[playerid]["moxie_swing_correct"], team_stat_data[playerid]["muscl_foul_ball"], team_stat_data[playerid]["muscl_triple"], team_stat_data[playerid]["muscl_double"], team_stat_data[playerid]["martyr_sacrifice"]
        laser_attempt_steal, laser_caught_steal_base, laser_caught_steal_home, laser_runner_advances, baset_attempt_steal, baset_caught_steal_home, cont_triple, cont_double, ground_triple, indulg_runner_advances = team_stat_data[playerid]["laser_attempt_steal"], team_stat_data[playerid]["laser_caught_steal_base"], team_stat_data[playerid]["laser_caught_steal_home"], team_stat_data[playerid]["laser_runner_advances"], team_stat_data[playerid]["baset_attempt_steal"], team_stat_data[playerid]["baset_caught_steal_home"], team_stat_data[playerid]["cont_triple"], team_stat_data[playerid]["cont_double"], team_stat_data[playerid]["ground_triple"], team_stat_data[playerid]["indulg_runner_advances"]
        
        moxie_log = moxie_swing_correct - adjustments["moxie_swing_correct"]
        swing_correct_chance = log_transform(moxie_log, log_transform_base)        
        swing_strike_blood_factors = ((1.0 / outs) if ("h20" in battingAttrs or "h20" in playerAttrs) else 0.0) + ((strike_chance / (strike_count + ball_count)) if (("0" in battingAttrs or "0" in playerAttrs) and "skipping" not in playerAttrs) else 0.0)
        if "a" in battingAttrs and not blood_calc:
            swing_strike_blood_factors += ((1.0 / outs) * a_blood_multiplier) + (((strike_chance / (strike_count + ball_count)) * a_blood_multiplier) if "skipping" not in playerAttrs else 0.0)
        swing_strike_chance = (swing_correct_chance + swing_strike_blood_factors) * strike_chance        
        swing_ball_chance = ((1.0 - swing_correct_chance) * (1.0 - strike_chance)) - (((1.0 - strike_chance) ** ball_count) if "flinch" in playerAttrs else 0.0)

        connect_log = adjustments["path_connect"] - path_connect
        base_connect_prob = log_transform(connect_log, log_transform_base)        
        try:
            test = 1 / (base_connect_prob - 1)
            base_connect_chance = prob_adjust(base_connect_prob, parkMods["plus_contact_minus_hardhit"])
        except (FloatingPointError, ZeroDivisionError):            
            base_connect_chance = base_connect_prob
        connect_chance = base_connect_chance * swing_strike_chance

        base_hit_adjust = adjustments["thwack_base_hit"] - adjustments["unthwack_base_hit"] - adjustments["omni_base_hit"]
        base_hit_log = thwack_base_hit - unthwack_base_hit - omni_base_hit - base_hit_adjust
        base_hit = log_transform(base_hit_log, log_transform_base)
        base_hit_chance = base_hit * connect_chance                     

        strike_looking_chance = (1.0 - swing_correct_chance) * strike_chance
        strike_swinging_chance = (1.0 - connect_chance) + swing_ball_chance
        ball_chance = 1.0 - swing_ball_chance

        foul_ball_log = muscl_foul_ball - adjustments["muscl_foul_ball"]
        foul_ball_prob = log_transform(foul_ball_log, log_transform_base) 
        try:
            test = 1 / (foul_ball_prob - 1)
            foul_ball_chance = prob_adjust(foul_ball_prob, -parkMods["plus_hit_minus_foul"])
        except (FloatingPointError, ZeroDivisionError):            
            foul_ball_chance = foul_ball_prob
        foul_ball_chance *= (1.0 - base_hit) * connect_chance
        caught_out_prob = connect_chance - foul_ball_chance - base_hit_chance   
        try:
            test = 1 / (caught_out_prob - 1)
            caught_out_chance[playerid] = (prob_adjust(caught_out_prob, parkMods["plus_groundout_minus_hardhit"]) + prob_adjust(caught_out_prob, -parkMods["minus_doubleplay"])) / 2.0
        except (FloatingPointError, ZeroDivisionError):            
            caught_out_chance[playerid] = caught_out_prob

        #for each of these, we need to make sure nothing is actually counting as 0 or less probability, but rather skew them relative to each other
        if base_hit_chance <= 0 or foul_ball_chance <= 0 or caught_out_chance[playerid] <= 0:            
            base_hit_chance += abs(base_hit_chance) + abs(foul_ball_chance) + abs(caught_out_chance[playerid])
            foul_ball_chance += abs(base_hit_chance) + abs(foul_ball_chance) + abs(caught_out_chance[playerid])
            caught_out_chance[playerid] += abs(base_hit_chance) + abs(foul_ball_chance) + abs(caught_out_chance[playerid])                        
        all_zeros = base_hit_chance == 0 and foul_ball_chance == 0 and caught_out_chance[playerid] == 0
        caught_out_chance[playerid] += connect_chance if all_zeros else 0.0
        all_connect_events_prob = base_hit_chance + foul_ball_chance + caught_out_chance[playerid]        
        
        try:
            factor = connect_chance / all_connect_events_prob
            base_hit_chance *= factor
            foul_ball_chance *= factor
            caught_out_chance[playerid] *= factor             
        except (FloatingPointError, ZeroDivisionError):
            factor = 1.0

        if strike_looking_chance <= 0 or strike_swinging_chance <= 0 or connect_chance <= 0 or ball_chance <= 0:
            strike_looking_chance += abs(strike_looking_chance) + abs(strike_swinging_chance) + abs(connect_chance) + abs(ball_chance)
            strike_swinging_chance += abs(strike_looking_chance) + abs(strike_swinging_chance) + abs(connect_chance) + abs(ball_chance)
            connect_chance += abs(strike_looking_chance) + abs(strike_swinging_chance) + abs(connect_chance) + abs(ball_chance)
            ball_chance += abs(strike_looking_chance) + abs(strike_swinging_chance) + abs(connect_chance) + abs(ball_chance)
        all_pitch_events_prob = strike_looking_chance + strike_swinging_chance + connect_chance + ball_chance
        #just always do this rather than running an if?
        factor = 1.0 / all_pitch_events_prob
        strike_looking_chance *= factor
        strike_swinging_chance *= factor
        connect_chance *= factor
        ball_chance *= factor
            
                 
        #possibilites are any three of foul balls (only up to strikecount - 1), strike swinging, and strike looking
        #always need at least one strike to strike out
        #walks are ball count balls plus any combination above that does not include the final strike
        strikeout = (strike_looking_chance ** strike_count) + (strike_swinging_chance ** strike_count)
        walked = (ball_chance ** ball_count)
        if strike_count >= 2.0:
            strikeout += (foul_ball_chance ** (strike_count - 1.0)) * strike_looking_chance
            strikeout += (foul_ball_chance ** (strike_count - 1.0)) * strike_swinging_chance
            strikeout += (strike_looking_chance ** (strike_count - 1.0)) * strike_swinging_chance
            strikeout += (strike_swinging_chance ** (strike_count - 1.0)) * strike_looking_chance
            strikeout += (strike_looking_chance ** (strike_count - 1.0)) * strike_looking_chance
            strikeout += strike_looking_chance ** strike_count
            strikeout += strike_swinging_chance ** strike_count
            walked += (ball_chance ** ball_count) * strike_swinging_chance
            walked += (ball_chance ** ball_count) * strike_looking_chance
            walked += (ball_chance ** ball_count) * foul_ball_chance
        if strike_count >= 3.0:
            strikeout += (foul_ball_chance ** (strike_count - 2.0)) * strike_swinging_chance * strike_looking_chance
            strikeout += (foul_ball_chance ** (strike_count - 2.0)) * (strike_swinging_chance ** 2.0)
            strikeout += (foul_ball_chance ** (strike_count - 2.0)) * (strike_looking_chance ** 2.0)
            walked += (ball_chance ** ball_count) * (strike_swinging_chance ** 2.0)
            walked += (ball_chance ** ball_count) * (strike_looking_chance ** 2.0)
            walked += (ball_chance ** ball_count) * strike_looking_chance * strike_swinging_chance
            walked += (ball_chance ** ball_count) * foul_ball_chance * strike_swinging_chance
            walked += (ball_chance ** ball_count) * foul_ball_chance * strike_looking_chance
        if strike_count >= 4.0:
            strikeout += (foul_ball_chance ** (strike_count - 3.0)) * (strike_swinging_chance ** 2.0) * strike_looking_chance
            strikeout += (foul_ball_chance ** (strike_count - 3.0)) * strike_swinging_chance * (strike_looking_chance ** 2.0)
            strikeout += (foul_ball_chance ** (strike_count - 3.0)) * (strike_swinging_chance ** 3.0)
            strikeout += (foul_ball_chance ** (strike_count - 3.0)) * (strike_looking_chance ** 3.0)
            walked += (ball_chance ** ball_count) * (strike_swinging_chance ** 3.0)
            walked += (ball_chance ** ball_count) * (strike_looking_chance ** 3.0)
            walked += (ball_chance ** ball_count) * (strike_swinging_chance ** 2.0) * strike_looking_chance
            walked += (ball_chance ** ball_count) * strike_swinging_chance * (strike_looking_chance ** 2.0)
            walked += (ball_chance ** ball_count) * foul_ball_chance * (strike_swinging_chance ** 2.0)
            walked += (ball_chance ** ball_count) * foul_ball_chance * (strike_looking_chance ** 2.0)
            walked += (ball_chance ** ball_count) * foul_ball_chance * strike_swinging_chance * strike_looking_chance
            walked += (ball_chance ** ball_count) * (foul_ball_chance ** 2.0) * strike_swinging_chance
            walked += (ball_chance ** ball_count) * (foul_ball_chance ** 2.0) * strike_looking_chance
        
        corrected_strike_chance = strikeout
        corrected_strike_chance += strike_mod
        walked += walk_buff
        if "o_no" in battingAttrs or "o_no" in playerAttrs or ("a" in battingAttrs and not blood_calc):
            #probability of no balls happening is the probability that every strike is a strike AND every ball is swung at
            no_balls = ((strike_chance * (1.0 - swing_correct_chance)) + (strike_chance * swing_correct_chance * (1.0 - base_connect_chance))) * ((1.0 - swing_correct_chance) * (1.0 - strike_chance))          
            no_balls = min(no_balls, 1.0)
            #straight up for o_no; a blood needs no balls reduced by blood multiplier first since it only matters when a blood procced o_no                     
            if "a" in battingAttrs:                
                no_balls *= a_blood_multiplier
            #probability of a least one ball happening is 1 - probability of no balls happening
            corrected_strike_chance *= (1.0 - no_balls)
               
        #everything else is per pitch... connect per pitch, base hit per pitch, caught out per pitch, so each ball pitched is 1 / ball count % of a walk
        #psychic mind tricks can convert strikes to walks... so some % of strikes, called strike to walk, are removed from strike events and become walk events

        walked_psychic = walked + (corrected_strike_chance * strike_to_walk) - (walked * walk_to_strike)
        corrected_strike_chance += (walked * walk_to_strike) - (corrected_strike_chance * strike_to_walk)
        walked = walked_psychic
        if corrected_strike_chance < 0.0:            
            walked += abs(corrected_strike_chance) * 2.0
            corrected_strike_chance = abs(corrected_strike_chance) * 2.0
        if walked < 0.0:            
            corrected_strike_chance += abs(walked) * 2.0
            walked += abs(walked) * 2.0
        walk_chance[playerid] = walked
        strike_out_chance[playerid] = corrected_strike_chance

        if walk_chance[playerid] <= 0 or base_hit_chance <= 0 or strike_out_chance[playerid] <= 0 or caught_out_chance[playerid] <= 0:
            walk_chance[playerid] += abs(walk_chance[playerid]) + abs(base_hit_chance) + abs(strike_out_chance[playerid]) + abs(caught_out_chance[playerid])
            base_hit_chance += abs(walk_chance[playerid]) + abs(base_hit_chance) + abs(strike_out_chance[playerid]) + abs(caught_out_chance[playerid])
            strike_out_chance[playerid] += abs(walk_chance[playerid]) + abs(base_hit_chance) + abs(strike_out_chance[playerid]) + abs(caught_out_chance[playerid])
            caught_out_chance[playerid] += abs(walk_chance[playerid]) + abs(base_hit_chance) + abs(strike_out_chance[playerid]) + abs(caught_out_chance[playerid])
        #the sum of these events (which would be one or the other or the other etc.) must be one, as they are everything that can happen on a plate appearance
        all_macro_events_prob = walk_chance[playerid] + base_hit_chance + strike_out_chance[playerid] + caught_out_chance[playerid]        
        #if the sum is not one, correct all probabilities such that the sum will be equal to 1.0, which will preserve the relative probabilities for all events        
        #just always do this rather than running an if?
        factor = 1.0 / all_macro_events_prob
        walk_chance[playerid] *= factor
        strike_out_chance[playerid] *= factor
        base_hit_chance *= factor
        caught_out_chance[playerid] *= factor
        all_macro_events_prob = walk_chance[playerid] + base_hit_chance + strike_out_chance[playerid] + caught_out_chance[playerid]                             
        #if caught_out_chance[playerid] > 0.0000:
        #    print("Normalized to: strikeout {:.4f}, walked {:.4f}, base hit {:.4f}, caughtout {:.4f}".format(strike_out_chance[playerid], walk_chance[playerid], base_hit_chance, caught_out_chance[playerid]))

        attempt_steal_adjust = adjustments["baset_attempt_steal"] + adjustments["laser_attempt_steal"] - adjustments["watch_attempt_steal"]
        attempt_steal_log = baset_attempt_steal + laser_attempt_steal - watch_attempt_steal - attempt_steal_adjust
        attempt_steal_prob = log_transform(attempt_steal_log, log_transform_base)        
        try:
            test = 1 / (attempt_steal_prob - 1)
            attempt_steal_chance[playerid] = prob_adjust(attempt_steal_prob, -parkMods["minus_stealattempt"])        
        except (FloatingPointError, ZeroDivisionError):            
            attempt_steal_chance[playerid] = attempt_steal_prob

        caught_steal_base_adjust = adjustments["anticap_caught_steal_base"] - adjustments["laser_caught_steal_base"]
        caught_steal_base_log = anticap_caught_steal_base - laser_caught_steal_base - caught_steal_base_adjust
        caught_steal_base_prob = log_transform(caught_steal_base_log, log_transform_base)        
        try:
            test = 1 / (caught_steal_base_prob - 1)
            caught_steal_base_chance[playerid] = prob_adjust(caught_steal_base_prob, parkMods["minus_stealsuccess"])
        except (FloatingPointError, ZeroDivisionError):            
            caught_steal_base_chance[playerid] = caught_steal_base_prob
        
        caught_steal_home_adjust = adjustments["anticap_caught_steal_home"] + adjustments["baset_caught_steal_home"] + adjustments["laser_caught_steal_home"]
        caught_steal_home_log = anticap_caught_steal_home - baset_caught_steal_home - laser_caught_steal_home - caught_steal_home_adjust
        caught_steal_home_prob = log_transform(caught_steal_home_log, log_transform_base)    
        try:
            test = 1 / (caught_steal_home_prob - 1)
            caught_steal_home_chance[playerid] = prob_adjust(caught_steal_home_prob, parkMods["minus_stealsuccess"])
        except (FloatingPointError, ZeroDivisionError):            
            caught_steal_home_chance[playerid] = caught_steal_home_prob
        #if (1.0 + parkMods["minus_stealsuccess"]) < 0 or (1.0 - parkMods["minus_stealattempt"] < 0):
        #    print("Parkmod mulitplier coming back negative, steal success mult {:.4f}, steal attempt mult {:.4f}".format(1.0 + parkMods["minus_stealsuccess"], 1.0 - parkMods["minus_stealattempt"]))
        
        #homeruns needs to care about how many other runners are on base for how valuable they are, with a floor of "1x"
        homerun_adjust = adjustments["div_homer"] - adjustments["overp_homer"]
        homerun_log = div_homer - overp_homer - homerun_adjust
        homerun_prob = log_transform(homerun_log, log_transform_base)  
        try:
            test = 1 / (homerun_prob - 1)
            homerun_adjusted = (prob_adjust(homerun_prob, -parkMods["plus_hit_minus_homer"]) + prob_adjust(homerun_prob, -parkMods["plus_groundout_minus_hardhit"]) + prob_adjust(homerun_prob, -parkMods["plus_contact_minus_hardhit"]) + prob_adjust(homerun_prob, parkMods["plus_hardhit"]) + prob_adjust(homerun_prob, -parkMods["minus_homer"])) / 5.0
        except (FloatingPointError, ZeroDivisionError):            
            homerun_adjusted = homerun_prob
        homerun_chance[playerid] = homerun_adjusted * base_hit_chance
        homerun_multipliers[playerid] = homer_multiplier        

        triple_adjust = adjustments["muscl_triple"] + adjustments["ground_triple"] + adjustments["cont_triple"] - adjustments["overp_triple"] - adjustments["chasi_triple"]
        triple_log = muscl_triple + ground_triple + cont_triple - overp_triple - chasi_triple - triple_adjust
        triple_prob = log_transform(triple_log, log_transform_base)
        try:
            test = 1 / (triple_prob - 1)
            triple_adjusted = (prob_adjust(triple_prob, parkMods["plus_hit_minus_homer"]) + prob_adjust(triple_prob, parkMods["plus_hit_minus_foul"]) + prob_adjust(triple_prob, -parkMods["plus_groundout_minus_hardhit"]) + prob_adjust(triple_prob, -parkMods["plus_contact_minus_hardhit"]) + prob_adjust(triple_prob, parkMods["plus_hardhit"]) + prob_adjust(triple_prob, -parkMods["minus_hit"])) / 6.0        
        except (FloatingPointError, ZeroDivisionError):            
            triple_adjusted = triple_prob
        triple_chance[playerid] = triple_adjusted * base_hit_chance

        double_adjust = adjustments["muscl_double"] + adjustments["cont_double"] - adjustments["overp_double"] - adjustments["chasi_double"]
        double_log = muscl_double + cont_double - overp_double - chasi_double - double_adjust
        double_prob = log_transform(double_log, log_transform_base)
        try:
            test = 1 / (double_prob - 1)
            double_adjusted = (prob_adjust(double_prob, parkMods["plus_hit_minus_homer"]) + prob_adjust(double_prob, parkMods["plus_hit_minus_foul"]) + prob_adjust(double_prob, -parkMods["plus_groundout_minus_hardhit"]) + prob_adjust(double_prob, -parkMods["plus_contact_minus_hardhit"]) + prob_adjust(double_prob, parkMods["plus_hardhit"]) + prob_adjust(double_prob, -parkMods["minus_hit"])) / 6.0
        except (FloatingPointError, ZeroDivisionError):            
            double_adjusted = double_prob
        double_chance[playerid] = double_adjusted * base_hit_chance

        single_prob = base_hit_chance - triple_chance[playerid] - double_chance[playerid] - homerun_chance[playerid]
        try:
            test = 1 / (single_prob - 1)
            if single_prob < 0:
                single_adjusted = (prob_adjust(single_prob, -parkMods["plus_hit_minus_homer"]) + prob_adjust(single_prob, -parkMods["plus_hit_minus_foul"]) + prob_adjust(single_prob, parkMods["minus_hit"])) / 3.0             
            else:
                single_adjusted = (prob_adjust(single_prob, parkMods["plus_hit_minus_homer"]) + prob_adjust(single_prob, parkMods["plus_hit_minus_foul"]) + prob_adjust(single_prob, -parkMods["minus_hit"])) / 3.0
        except (FloatingPointError, ZeroDivisionError):            
            single_adjusted = single_prob
        single_chance[playerid] = single_adjusted

        if single_chance[playerid] <= 0 or triple_chance[playerid] <= 0 or double_chance[playerid] <= 0 or homerun_chance[playerid] <= 0:
            single_chance[playerid] += abs(single_chance[playerid]) + abs(triple_chance[playerid]) + abs(double_chance[playerid]) + abs(homerun_chance[playerid])
            triple_chance[playerid] += abs(single_chance[playerid]) + abs(triple_chance[playerid]) + abs(double_chance[playerid]) + abs(homerun_chance[playerid])
            double_chance[playerid] += abs(single_chance[playerid]) + abs(triple_chance[playerid]) + abs(double_chance[playerid]) + abs(homerun_chance[playerid])
            homerun_chance[playerid] += abs(single_chance[playerid]) + abs(triple_chance[playerid]) + abs(double_chance[playerid]) + abs(homerun_chance[playerid])
        #normalize these to sum to base hit chance
        all_base_hit_events_prob = single_chance[playerid] + triple_chance[playerid] + double_chance[playerid] + homerun_chance[playerid]        
        #just always do this rather than running an if?
        factor = base_hit_chance / all_base_hit_events_prob
        single_chance[playerid] *= factor
        triple_chance[playerid] *= factor
        double_chance[playerid] *= factor
        homerun_chance[playerid] *= factor                        

        on_base_chance[playerid] = min(single_chance[playerid] + double_chance[playerid] + triple_chance[playerid] + walk_chance[playerid], 1.0)
        
        hit_modifier[playerid] = hit_multiplier          

        #runners advancing is tricky, since we have to do this based on runners being on base already, but use the batter's martyrdom for sacrifices
        sacrifice_log = martyr_sacrifice - adjustments["martyr_sacrifice"]
        sacrifice_chance[playerid] = log_transform(sacrifice_log, log_transform_base) * caught_out_chance[playerid]        
        
        runner_advances_adjust = adjustments["laser_runner_advances"] + adjustments["indulg_runner_advances"] - adjustments["trag_runner_advances"] - adjustments["shakes_runner_advances"] - adjustments["shakes_runner_advances"]
        runner_advances_log = laser_runner_advances + indulg_runner_advances - trag_runner_advances - shakes_runner_advances - tenacious_runner_advances - runner_advances_adjust
        runner_advance_chance[playerid] = log_transform(runner_advances_log, log_transform_base)
        average_on_base_position[playerid] = {}
        average_on_base_position[playerid]["first"] = min(single_chance[playerid] + (walk_chance[playerid] * (1.0 - walk_mod)), 1.0)
        average_on_base_position[playerid]["second"] = min(double_chance[playerid] + (walk_chance[playerid] * walk_mod), 1.0)
        average_on_base_position[playerid]["third"] = min(triple_chance[playerid] + (walk_chance[playerid] * walk_mod), 1.0)                

        #need to approximate caught stealing outs for blood calcing        
        average_bases_to_steal = (2.0 * average_on_base_position[playerid]["first"]) + average_on_base_position[playerid]["second"]
        average_home_to_steal = average_on_base_position[playerid]["first"] + average_on_base_position[playerid]["second"] + average_on_base_position[playerid]["third"]
        caught_steal_outs[playerid] = min((caught_steal_base_chance[playerid] * attempt_steal_chance[playerid] * average_bases_to_steal) + (caught_steal_home_chance[playerid] * attempt_steal_chance[playerid] * average_home_to_steal), 1.0)

    if blood_calc:      
        if blood_calc == "high_pressure":
            previous_batter_obp = None
            for playerid in sorted_batters:
                if previous_batter_obp:
                    high_pressure_mod[playerid] = previous_batter_obp
                else:
                    first_batter = playerid                    
                previous_batter_obp = on_base_chance[playerid]                 
            high_pressure_mod[first_batter] = previous_batter_obp            
            return high_pressure_mod
        else:
            outs_per_lineup = sum(strike_out_chance.values()) + sum(caught_steal_outs.values()) + sum(caught_out_chance.values())            
            average_aaa_blood_impact, average_aa_blood_impact = {}, {}
            max_x = outs * innings   
            lineup_factor = (outs - outs_per_lineup) if (outs_per_lineup < outs) else 1.0
            if blood_calc == "aaa" or blood_calc == "a":            
                for playerid in triple_chance:
                    x = 0
                    average_aaa_blood_impact[playerid] = 0.0     
                    if outs_per_lineup < 0.1:
                        average_aaa_blood_impact[playerid] = 1.0
                    else:
                        while (x < max_x) and (average_aaa_blood_impact[playerid] < 1.0):                    
                            previous_blood_impact = average_aaa_blood_impact[playerid]
                            average_aaa_blood_impact[playerid] += ((triple_chance[playerid] * ((1.0 - triple_chance[playerid]) ** x)) * ((max_x - x) / max_x)) * lineup_factor                    
                            if (average_aaa_blood_impact[playerid] - previous_blood_impact) < 0.001:
                                break
                            x += outs_per_lineup * lineup_factor
                        average_aaa_blood_impact[playerid] = max(average_aaa_blood_impact[playerid], 1.0)
            if blood_calc == "aa" or blood_calc == "a":            
                for playerid in double_chance:
                    x = 0
                    average_aa_blood_impact[playerid] = 0.0
                    if outs_per_lineup < 0.1:
                        average_aa_blood_impact[playerid] = 1.0
                    else:
                        while (x < max_x) and (average_aa_blood_impact[playerid] < 1.0):                    
                            previous_blood_impact = average_aa_blood_impact[playerid]
                            average_aa_blood_impact[playerid] += ((double_chance[playerid] * ((1.0 - double_chance[playerid]) ** x)) * ((max_x - x) / max_x)) * lineup_factor                    
                            if (average_aa_blood_impact[playerid] - previous_blood_impact) < 0.001:
                                break
                            x += outs_per_lineup * lineup_factor
                        average_aa_blood_impact[playerid] = max(average_aa_blood_impact[playerid], 1.0)        
            if blood_calc == "aaa":
                return average_aaa_blood_impact
            if blood_calc == "aa":
                return average_aa_blood_impact
            if blood_calc == "a":
                return average_aa_blood_impact, average_aaa_blood_impact

    return runner_advance_chance, caught_out_chance, sacrifice_chance, score_mod, hit_modifier, homerun_multipliers, score_multiplier, attempt_steal_chance, walk_chance, strike_out_chance, caught_steal_base_chance, caught_steal_home_chance, homerun_chance, triple_chance, double_chance, single_chance, average_on_base_position, steal_mod, clutch_factor, walk_mod

def calc_team_score(mods, weather, parkMods, away_home, team_stat_data, opp_stat_data, pitcher_stat_data, team_data, opp_data, pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, opp_score=None, innings=9, outs=3, runtime_solution=False):      
    battingAttrs = teamAttrs    
    reverb_weather, sun_weather, bh_weather = helpers.get_weather_idx("Reverb"), helpers.get_weather_idx("Sun 2"), helpers.get_weather_idx("Black Hole")
    runner_advance_chance, caught_out_chance, sacrifice_chance, score_mod, hit_modifier, homerun_multipliers, score_multiplier, attempt_steal_chance, walk_chance, strike_out_chance, caught_steal_base_chance, caught_steal_home_chance, homerun_chance, triple_chance, double_chance, single_chance, average_on_base_position, steal_mod, clutch_factor, walk_mod = calc_probs_from_stats(mods, weather, parkMods, team_stat_data, opp_stat_data, pitcher_stat_data, team_data, opp_data, pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, None, innings)        

    #run three "games" to get a more-representative average
    #total_innings = (innings * 10.0) if runtime_solution else (innings * 3.0)    
    replicates = 10
    total_innings = int(innings) * replicates
    current_innings, atbats_in_inning = 0, 0  
    current_outs = 0.0
    team_score = 100.0 if ("home_field" in battingAttrs and away_home == "home") else 0.0
    team_rbi = team_score
    inning_score, inning_rbi = 0.0, 0.0

    runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
    runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
    inning_outs, strikeouts = 0.0, 0.0
    batter_atbats = 0        
    last_player_out = ""
    stolen_bases, homers, hits = {}, {}, {}    
    loop_checker = {}
    loop_encountered, last_pass = False, False            
    
    while current_innings < total_innings:
        starting_lineup_inning_outs, starting_lineup_inning_score, starting_lineup_inning_rbi = inning_outs, inning_score, inning_rbi
        innings_since_lineup_start = 0
        for playerid in sorted_batters:
            batter_atbats += 1                        
            playerAttrs = team_data[playerid]["attrs"]
            base = 20.0 if (("extra_base" in battingAttrs) or ("extra_base" in playerAttrs)) else 25.0                   
            if base == 25.0:
                homerun_score = ((100.0 - (10.0 * score_mod)) * (1.0 + runners_on_first + runners_on_second + runners_on_third)) * homerun_chance[playerid]
                triple_runners_score = ((100.0 - (10.0 * score_mod)) * (runners_on_first + runners_on_second + runners_on_third)) * triple_chance[playerid]
                double_runners_score = ((100.0 - (10.0 * score_mod)) * (runners_on_second + runners_on_third)) * double_chance[playerid]    
                single_runners_score = ((100.0 - (10.0 * score_mod)) * runners_on_third) * single_chance[playerid]                               
                runners_advance_score = 100.0 * runners_on_third * sacrifice_chance[playerid]
                walking_score = 100.0 * ((runners_on_third * walk_chance[playerid]) + (runners_on_second * (walk_chance[playerid] * walk_mod)) + (runners_on_first * (walk_chance[playerid] * walk_mod)))
            else:
                homerun_score = ((100.0 - (10.0 * score_mod)) * (1.0 + runners_on_first + runners_on_second + runners_on_third + runners_on_fourth)) * homerun_chance[playerid]
                triple_runners_score = ((100.0 - (10.0 * score_mod)) * (runners_on_fourth + runners_on_second + runners_on_third)) * triple_chance[playerid]
                double_runners_score = ((100.0 - (10.0 * score_mod)) * (runners_on_fourth + runners_on_third)) * double_chance[playerid]    
                single_runners_score = ((100.0 - (10.0 * score_mod)) * runners_on_fourth) * single_chance[playerid]                               
                runners_advance_score = 100.0 * runners_on_fourth * sacrifice_chance[playerid]
                walking_score = 100.0 * ((runners_on_fourth * walk_chance[playerid]) + (runners_on_third * walk_chance[playerid] * walk_mod) + (runners_on_second * walk_chance[playerid] * walk_mod) + (runners_on_first * walk_chance[playerid] * walk_mod))                
                runners_on_fourth, runner_advance_fourth = calc_runners_on(runners_on_fourth, runner_advance_fourth, runners_on_third, runner_advance_third, runners_on_second, runner_advance_second, runners_on_first, runner_advance_first, single_chance[playerid], double_chance[playerid], triple_chance[playerid], homerun_chance[playerid], sacrifice_chance[playerid], caught_out_chance[playerid], walk_chance[playerid], walk_mod, 0.0, runner_advance_chance[playerid])
            runners_on_third, runner_advance_third = calc_runners_on(runners_on_third, runner_advance_third, runners_on_second, runner_advance_second, runners_on_first, runner_advance_first, 0.0, 0.0, single_chance[playerid], double_chance[playerid], triple_chance[playerid], homerun_chance[playerid], sacrifice_chance[playerid], caught_out_chance[playerid], walk_chance[playerid], walk_mod, average_on_base_position[playerid]["third"], runner_advance_chance[playerid])
            runners_on_second, runner_advance_second = calc_runners_on(runners_on_second, runner_advance_second, runners_on_first, runner_advance_first, 0.0, 0.0, 0.0, 0.0, single_chance[playerid], double_chance[playerid], triple_chance[playerid], homerun_chance[playerid], sacrifice_chance[playerid], caught_out_chance[playerid], walk_chance[playerid], walk_mod, average_on_base_position[playerid]["second"], runner_advance_chance[playerid])
            runners_on_first, runner_advance_first = calc_runners_on(runners_on_first, runner_advance_first, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, single_chance[playerid], double_chance[playerid], triple_chance[playerid], homerun_chance[playerid], sacrifice_chance[playerid], caught_out_chance[playerid], walk_chance[playerid], walk_mod, average_on_base_position[playerid]["first"], runner_advance_chance[playerid])
            player_rbi = runners_advance_score + walking_score + homerun_score + triple_runners_score + double_runners_score + single_runners_score
            player_score = (runners_advance_score + walking_score + (homerun_score * homerun_multipliers[playerid]) + ((triple_runners_score + double_runners_score + single_runners_score) * hit_modifier[playerid])) * score_multiplier[playerid]
            if playerid not in homers:
                homers[playerid] = 0.0
                hits[playerid] = 0.0
                stolen_bases[playerid] = 0.0
            homers[playerid] += homerun_chance[playerid]
            hits[playerid] += triple_chance[playerid] + double_chance[playerid] + single_chance[playerid]
            player_outs = strike_out_chance[playerid] + caught_out_chance[playerid]
            strikeouts += strike_out_chance[playerid]
            inning_outs += player_outs            
            if inning_outs >= outs:
                inning_outs = 0                
                current_innings += 1
                innings_since_lineup_start += 1                
                if playerid in loop_checker:
                    if not last_pass:
                        if (str(batter_atbats - atbats_in_inning) in loop_checker[playerid]) and (loop_checker[playerid][str(batter_atbats - atbats_in_inning)][2] == 1):                            
                            #this means that we have hit a loop point; our inning ended with the same player and had the same number of atbats
                            loop_encountered = True                        
                            inning_score, inning_rbi = 0.0, 0.0
                            runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
                            runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
                            break
                else:
                    loop_checker[playerid] = {}
                loop_checker[playerid][str(batter_atbats - atbats_in_inning)] = [team_score, current_innings, 1, team_rbi]
                inning_score += player_score
                atbats_in_inning = batter_atbats
                team_score += inning_score  
                team_rbi += inning_rbi
                if (away_home == "home") and (current_innings == 8):
                    if team_score > (opp_score / replicates):
                        #home team will only need 8 innings to win
                        total_innings = replicates * 8
                inning_score, inning_rbi = 0.0, 0.0
                runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
                runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
                if current_innings >= total_innings:                
                    break
            else:
                steal_runners_on_second = min(runners_on_second, 1.0)
                steal_runners_on_third = min(runners_on_third, 1.0)
                steal_runners_on_fourth = min(runners_on_fourth, 1.0)                          
                runners_on_first, runner_advance_first = min(runners_on_first, 1.0), min(runner_advance_first, 1.0)
                runners_on_second, runner_advance_second = min(runners_on_second, 1.0), min(runner_advance_second, 1.0)
                runners_on_third, runner_advance_third = min(runners_on_third, 1.0), min(runner_advance_third, 1.0)
                runners_on_fourth, runner_advance_fourth = min(runners_on_fourth, 1.0), min(runner_advance_fourth, 1.0)
                #since the inning is still live, now we need to calculate potential steals from the batter, taking their likely position on base and computing how much the runners on base positions change
                #stealing from first to second                                
                steal_base_success_rate = (1.0 - caught_steal_base_chance[playerid]) * attempt_steal_chance[playerid]
                steal_home_success_rate = (1.0 - caught_steal_home_chance[playerid]) * attempt_steal_chance[playerid]                
                #steal second
                steal_second_opportunities = average_on_base_position[playerid]["first"] * (1.0 - steal_runners_on_second) 
                #steal third
                steal_third_opportunities = (steal_second_opportunities * (1.0 - steal_runners_on_third)) + (average_on_base_position[playerid]["second"] * (1.0 - steal_runners_on_third))
                #adjust base position based on stealing bases
                runners_on_first -= (steal_second_opportunities * attempt_steal_chance[playerid])
                runner_advance_first -= (steal_second_opportunities * attempt_steal_chance[playerid]) * runner_advance_chance[playerid]
                runners_on_second += (steal_second_opportunities * steal_base_success_rate) - (steal_third_opportunities * attempt_steal_chance[playerid])
                runner_advance_second += ((steal_second_opportunities * steal_base_success_rate) - (steal_third_opportunities * attempt_steal_chance[playerid])) * runner_advance_chance[playerid]
                if base == 20.0:                    
                    #steal fourth
                    steal_fourth_opportunities = steal_third_opportunities * (1.0 - steal_runners_on_fourth)                    
                    steal_fourth_opportunities += average_on_base_position[playerid]["third"] * (1.0 - steal_runners_on_fourth)
                    #steal_home                    
                    steal_home_opportunities = steal_fourth_opportunities                    
                    #adjust third and fourth base
                    runners_on_third += (steal_third_opportunities * steal_base_success_rate) - (steal_fourth_opportunities * attempt_steal_chance[playerid])
                    runner_advance_third += ((steal_third_opportunities * steal_base_success_rate) - (steal_fourth_opportunities * attempt_steal_chance[playerid])) * runner_advance_chance[playerid]
                    runners_on_fourth += (steal_fourth_opportunities * steal_base_success_rate) - (steal_home_opportunities * attempt_steal_chance[playerid])
                    runner_advance_fourth += ((steal_fourth_opportunities * steal_base_success_rate) - (steal_home_opportunities * attempt_steal_chance[playerid])) * runner_advance_chance[playerid]
                else:
                    steal_fourth_opportunities = 0.0
                    #steal_home                    
                    steal_home_opportunities = steal_third_opportunities                    
                    steal_home_opportunities += average_on_base_position[playerid]["third"]
                    #adjust third base
                    runners_on_third += (steal_third_opportunities * steal_base_success_rate) - (steal_home_opportunities * attempt_steal_chance[playerid])
                    runner_advance_third += ((steal_third_opportunities * steal_base_success_rate) - (steal_home_opportunities * attempt_steal_chance[playerid])) * runner_advance_chance[playerid]
                steal_base_opportunities = steal_second_opportunities + steal_third_opportunities + steal_fourth_opportunities
                stolen_bases[playerid] += steal_base_opportunities * steal_base_success_rate
                stolen_bases[playerid] += steal_home_opportunities * steal_home_success_rate
                player_rbi += ((100.0 + steal_mod[playerid]) * (steal_home_opportunities * steal_home_success_rate)) + (steal_mod[playerid] * steal_base_opportunities * steal_base_success_rate)
                player_score += ((100.0 + steal_mod[playerid]) * (steal_home_opportunities * steal_home_success_rate)) + (steal_mod[playerid] * steal_base_opportunities * steal_base_success_rate)
                steal_outs = (steal_base_opportunities * caught_steal_base_chance[playerid] * attempt_steal_chance[playerid]) + (steal_home_opportunities * caught_steal_home_chance[playerid] * attempt_steal_chance[playerid])
                inning_outs += steal_outs
                player_outs += steal_outs
                if inning_outs >= outs:
                    inning_outs = 0.0                    
                    current_innings += 1
                    innings_since_lineup_start += 1                    
                    if playerid in loop_checker:       
                        if not last_pass:
                            if (str(batter_atbats - atbats_in_inning) in loop_checker[playerid]) and (loop_checker[playerid][str(batter_atbats - atbats_in_inning)][2] == 2):                                
                                #this means that we have hit a loop point; our inning ended with the same player and had the same number of atbats
                                loop_encountered = True                                 
                                inning_score, inning_rbi = 0.0, 0.0
                                runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
                                runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
                                break
                    else:
                        loop_checker[playerid] = {}
                    loop_checker[playerid][str(batter_atbats - atbats_in_inning)] = [team_score, current_innings, 2, team_rbi]
                    inning_score += player_score
                    atbats_in_inning = batter_atbats
                    team_score += inning_score      
                    team_rbi += inning_rbi
                    if (away_home == "home") and (current_innings == 8):
                        if team_score > (opp_score / replicates):
                            #home team will only need 8 innings to win
                            total_innings = replicates * 8
                    inning_score, inning_rbi = 0.0, 0.0
                    runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
                    runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
                    if current_innings >= total_innings:                
                        break
                else:
                    runners_on_first = max(min(runners_on_first, 1.0), 0.0)
                    runners_on_second = max(min(runners_on_second, 1.0), 0.0)
                    runners_on_third = max(min(runners_on_third, 1.0), 0.0)
                    runners_on_fourth = max(min(runners_on_fourth, 1.0), 0.0)
                    runner_advance_first = max(min(runner_advance_first, 1.0), 0.0)
                    runner_advance_second = max(min(runner_advance_second, 1.0), 0.0)
                    runner_advance_third = max(min(runner_advance_third, 1.0), 0.0)
                    runner_advance_fourth = max(min(runner_advance_fourth, 1.0), 0.0)
                    if ("reverberating" in playerAttrs) or ("repeating" in playerAttrs and weather == reverb_weather):
                        player_score *= 1.02
                        hits[playerid] += (triple_chance[playerid] + double_chance[playerid] + single_chance[playerid]) * 0.02
                        homers[playerid] += homerun_chance[playerid] * 0.02
                        player_rbi += ((100.0 + steal_mod[playerid]) * (steal_home_opportunities * steal_home_success_rate)) + (steal_mod[playerid] * steal_base_opportunities * steal_base_success_rate) * 0.02
                        player_rbi += (runners_advance_score + walking_score + homerun_score + triple_runners_score + double_runners_score + single_runners_score) * 0.02
                        stolen_bases[playerid] += ((steal_base_opportunities * steal_base_success_rate) + (steal_home_opportunities * steal_home_success_rate)) * 0.02
                        strikeouts += (strike_out_chance[playerid] * 0.02)
                        inning_outs += player_outs * 0.02         
                    if inning_outs >= outs:
                        inning_outs = 0.0                        
                        current_innings += 1
                        innings_since_lineup_start += 1                        
                        if playerid in loop_checker:         
                            if not last_pass:
                                if (str(batter_atbats - atbats_in_inning) in loop_checker[playerid]) and (loop_checker[playerid][str(batter_atbats - atbats_in_inning)][2] == 3):
                                    #this means that we have hit a loop point; our inning ended with the same player and had the same number of atbats to get there
                                    loop_encountered = True             
                                    inning_score, inning_rbi = 0.0, 0.0
                                    runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
                                    runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
                                    break
                        else:
                            loop_checker[playerid] = {}
                        loop_checker[playerid][str(batter_atbats - atbats_in_inning)] = [team_score, current_innings, 3, team_rbi]
                        inning_score += player_score
                        atbats_in_inning = batter_atbats
                        team_score += inning_score
                        team_rbi += inning_rbi
                        if (away_home == "home") and (current_innings == 8):
                            if team_score > (opp_score / replicates):
                                #home team will only need 8 innings to win
                                total_innings = replicates * 8
                        inning_score, inning_rbi = 0.0, 0.0
                        runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
                        runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
                        if current_innings >= total_innings:                
                            break
                    else:
                        inning_score += player_score
                        inning_rbi += player_rbi
            

        if (current_innings < total_innings):        
            if loop_encountered:
                loop_encountered, last_pass = False, True                
                lineup_score = team_score - loop_checker[playerid][str(batter_atbats - atbats_in_inning)][0]
                lineup_rbi = team_rbi - loop_checker[playerid][str(batter_atbats - atbats_in_inning)][3]
                #print("{} innings before loop started, current innings {}".format(loop_checker[playerid][str(batter_atbats - atbats_in_inning)][1], current_innings))
                innings_in_loop = current_innings - loop_checker[playerid][str(batter_atbats - atbats_in_inning)][1]
                #we will have not added the most-recent inning, but we know we get a loop of innings from there and can replicate that loop N times and be at the same state
                #as the inning where we detected the start of a new loop is our current inning, we need to make sure that gets included in our replicated loop count
                #check for home game 8 innings versus 9
                if away_home == "home":
                    presumptive_score = team_score + inning_score
                    eight_inning_score = presumptive_score * (8.0 / current_innings)
                    if eight_inning_score > (opp_score / replicates):
                        total_innings = replicates * 8
                current_innings -= 1
                full_lineup_count = math.floor((total_innings - current_innings) / innings_in_loop)                
                #print("Iterating through {} replicates of the loop of {} innings, current innings {}".format(full_lineup_count, innings_in_loop, current_innings))
                atbats_in_inning = batter_atbats
                team_score += lineup_score * full_lineup_count
                team_rbi += lineup_rbi * full_lineup_count
                current_innings += innings_in_loop * full_lineup_count                
                if runtime_solution:                    
                    for playerid in sorted_batters:
                        if playerid not in hits:
                            homers[playerid] = 0.0
                            hits[playerid] = 0.0
                            stolen_bases[playerid] = 0.0                        
                        hits[playerid] *= full_lineup_count + 1                 
                        homers[playerid] *= full_lineup_count + 1
                        stolen_bases[playerid] *= full_lineup_count + 1
                    strikeouts *= full_lineup_count + 1
                #print("Current innings now {}, out of total {}".format(current_innings, total_innings))            
            elif ((inning_outs - starting_lineup_inning_outs) < 1) and (innings_since_lineup_start == 0):
                #this means we have gone through the entire lineup and not even gotten one out
                #most likely this will continue, so we are just going to macro score these cases to save time
                #first, we need to determine how many innings remain
                #let's change how we do this; we should determine how many lineup runs it will take to get to a single inning
                outs_per_lineup_run = (inning_outs - starting_lineup_inning_outs)
                outs_per_lineup_run = max(outs_per_lineup_run, 0.0001)                                
                lineup_runs_per_inning = outs / outs_per_lineup_run                
                if away_home == "home":
                    presumptive_score = team_score + (inning_score * lineup_runs_per_inning)                    
                    eight_inning_score = presumptive_score * (8.0 / (current_innings + 1))                    
                    if eight_inning_score > (opp_score / replicates):
                        total_innings = replicates * 8                        
                remaining_innings = total_innings - current_innings
                #next, we need to determine how many passes through the lineup it will take at our current rate to complete the remaining innings
                remaining_outs = ((remaining_innings * outs) - inning_outs)
                #we need to have a fail case for accumulating ZERO outs in a lineup pass; a truly absurd number                
                lineup_passes = remaining_outs / outs_per_lineup_run
                #then, we need to take the amount of score we have accumulated in our pass through the lineup and multiply it by our lineup passes, including the pass we just did in our total
                try:
                    lineup_score = (inning_score - starting_lineup_inning_score) * (lineup_passes + 1)
                    lineup_rbi = (inning_rbi - starting_lineup_inning_rbi) * (lineup_passes + 1)
                except OverflowError:
                    lineup_score = 100000000000.0
                    lineup_rbi = 100000000000.0
                #increase team score by this amount
                team_score += lineup_score
                team_rbi += lineup_rbi
                #finish scoring for the team
                current_innings = total_innings
                #print("Shortcutting {} lineup passes".format(lineup_passes))
                #only update the hits homers and steals if we are generating runtime output
                if runtime_solution:                    
                    for playerid in sorted_batters:
                        if playerid not in hits:
                            homers[playerid] = 0.0
                            hits[playerid] = 0.0
                            stolen_bases[playerid] = 0.0
                        hits[playerid] *= lineup_passes + 1
                        homers[playerid] *= lineup_passes + 1
                        stolen_bases[playerid] *= lineup_passes + 1
                    strikeouts *= lineup_passes + 1
            #else:
            #    if ((runners_on_first + runners_on_second + runners_on_third + runners_on_fourth) == 0.0) and ((runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth) == 0.0):
            #        #this means we're going to replicate this result a number of times as we completed the lineup before accumulating whatever remains                    
            #        last_pass = True
            #        if away_home == "home":
            #            presumptive_score = team_score
            #            eight_inning_score = presumptive_score * (8.0 / current_innings)
            #            if eight_inning_score > (opp_score / 3.0):
            #                total_innings = 8 * 3
            #        remaining_innings = total_innings - current_innings
            #        total_iterations = math.floor(remaining_innings / current_innings)
            #        print("Discovered a replicate point at inning {}, {} innings remain, {} replicates".format(current_innings, remaining_innings, total_iterations))
            #        team_score *= total_iterations
            #        team_rbi *= total_iterations
            #        current_innings += current_innings * total_iterations
            #        print("Re-entering the loop at inning {}".format(current_innings))
            #        if runtime_solution:
            #            for playerid in sorted_batters:
            #                if playerid not in hits:
            #                    homers[playerid] = 0.0
            #                    hits[playerid] = 0.0
            #                    stolen_bases[playerid] = 0.0
            #                hits[playerid] *= total_iterations
            #                homers[playerid] *= total_iterations
            #                stolen_bases[playerid] *= total_iterations
            #            strikeouts *= total_iterations
    
    #need to re-enable this in the case of wanting to do sun/black hole weather handling
    if ((weather == sun_weather) or (weather == bh_weather)) and runtime_solution:                
        #print("Adjusting team score for {} weather: team score = {}, adjusted score = {}".format("Sun 2" if weather == sun_weather else "Black Hole", team_score, adjusted_score))
        team_score = team_score % 1000.0            
    if runtime_solution:
        for playerid in sorted_batters:
            if playerid not in hits:
                homers[playerid] = 0.0
                hits[playerid] = 0.0
                stolen_bases[playerid] = 0.0
            if homers[playerid] < 0 or hits[playerid] < 0 or stolen_bases[playerid] < 0:
                print("Player {} has invalid return values: homers {}, hits {}, steals {}".format(homers[playerid], hits[playerid], stolen_bases[playerid]))
        return team_score, stolen_bases, homers, hits, strikeouts, team_rbi

    return team_score, team_rbi

def calc_runners_on(runners_on_base, runner_advance_base, runners_on_base_minus_one, runner_advance_base_minus_one, runners_on_base_minus_two, runner_advance_base_minus_two, runners_on_base_minus_three, runner_advance_base_minus_three, single_chance, double_chance, triple_chance, homerun_chance, sacrifice_chance, caught_out_chance, walk_chance, walk_mod, average_new_on_base, new_on_base_advance):

    advance_on_out = (runner_advance_base_minus_one * runners_on_base_minus_one * caught_out_chance)
    advance_on_out_advance = (runner_advance_base_minus_one * advance_on_out)
    single_base = (runners_on_base_minus_one - runners_on_base) * single_chance
    single_base_advance = (runner_advance_base_minus_one - runner_advance_base) * single_base
    sacrifice = (runners_on_base_minus_one - runners_on_base) * sacrifice_chance
    sacrifice_advance = (runner_advance_base_minus_one - runner_advance_base) * sacrifice
    double_base = (runners_on_base_minus_two - runners_on_base) * double_chance
    double_base_advance = (runner_advance_base_minus_two - runner_advance_base) * double_base
    triple_base = (runners_on_base_minus_three - runners_on_base) * triple_chance
    triple_base_advance = (runner_advance_base_minus_three - runner_advance_base) * triple_base
    walk_base = (runners_on_base_minus_one - runners_on_base) * walk_chance * (1.0 - walk_mod)
    walk_base_advance = (runner_advance_base_minus_one - runner_advance_base) * walk_base
    extra_walk_base = (runners_on_base_minus_two + runners_on_base_minus_three - runners_on_base) * walk_chance * walk_mod
    extra_walk_base_advance = (runner_advance_base_minus_two + runner_advance_base_minus_three - runner_advance_base) * extra_walk_base
    homerun = runners_on_base * homerun_chance
    homerun_advance = runner_advance_base * homerun
    new_advance = average_new_on_base * new_on_base_advance

    runners_on = max(runners_on_base + advance_on_out + single_base + sacrifice + double_base + triple_base - homerun + walk_base + extra_walk_base + average_new_on_base, 0.0)
    
    runner_advance = max(runner_advance_base + advance_on_out_advance + single_base_advance + sacrifice_advance + double_base_advance + triple_base_advance - homerun_advance + walk_base_advance + extra_walk_base_advance + new_advance, 0.0)
    
    return runners_on, runner_advance

def calc_player_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, player_stat_data, adjusted_stat_data, overperform_pct=0):        
    playerMods = get_player_mods(mods, awayAttrs, homeAttrs, weather, away_home, player_stat_data)        
    calced_stlats = {}        
    flood_weather = helpers.get_weather_idx("Flooding")
    ovp_from_hp = (away_home == "away" and "high_presssure" in awayAttrs and weather == flood_weather) or (away_home == "home" and "high_presssure" in homeAttrs and weather == flood_weather)
    if ovp_from_hp:
        player_omni_base_hit, player_watch_attempt_steal, player_chasi_triple, player_chasi_double, player_anticap_caught_steal_base, player_anticap_caught_steal_home, player_tenacious_runner_advances = calc_defense(terms, playerMods, teamMods, player_stat_data, adjusted_stat_data, None, 0)
    else:
        player_omni_base_hit, player_watch_attempt_steal, player_chasi_triple, player_chasi_double, player_anticap_caught_steal_base, player_anticap_caught_steal_home, player_tenacious_runner_advances = calc_defense(terms, playerMods, teamMods, player_stat_data, adjusted_stat_data, None, overperform_pct)
    if not player_stat_data["shelled"]:        
        calced_stlats["path_connect"], calced_stlats["trag_runner_advances"], calced_stlats["thwack_base_hit"], calced_stlats["div_homer"], calced_stlats["moxie_swing_correct"], calced_stlats["muscl_foul_ball"], calced_stlats["muscl_triple"], calced_stlats["muscl_double"], calced_stlats["martyr_sacrifice"] = calc_batting(terms, playerMods, teamMods, player_stat_data, adjusted_stat_data, None, overperform_pct)
        calced_stlats["laser_attempt_steal"], calced_stlats["laser_caught_steal_base"], calced_stlats["laser_caught_steal_home"], calced_stlats["laser_runner_advances"], calced_stlats["baset_attempt_steal"], calced_stlats["baset_caught_steal_home"], calced_stlats["cont_triple"], calced_stlats["cont_double"], calced_stlats["ground_triple"], calced_stlats["indulg_runner_advances"] = calc_running(terms, playerMods, teamMods, player_stat_data, adjusted_stat_data, None, overperform_pct)    
        return calced_stlats, player_omni_base_hit, player_watch_attempt_steal, player_chasi_triple, player_chasi_double, player_anticap_caught_steal_base, player_anticap_caught_steal_home, player_tenacious_runner_advances
    return player_omni_base_hit, player_watch_attempt_steal, player_chasi_triple, player_chasi_double, player_anticap_caught_steal_base, player_anticap_caught_steal_home, player_tenacious_runner_advances

def calc_pitcher_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, player_stat_data):       
    playerMods = get_player_mods(mods, awayAttrs, homeAttrs, weather, away_home, player_stat_data)    
    calced_stlats = {}    
    calced_stlats["unthwack_base_hit"], calced_stlats["ruth_strike"], calced_stlats["overp_homer"], calced_stlats["overp_triple"], calced_stlats["overp_double"], calced_stlats["shakes_runner_advances"], calced_stlats["cold_clutch_factor"] = calc_pitching(terms, playerMods, teamMods, player_stat_data)
    return calced_stlats

def calc_team_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, away_home, team_stat_data, pitcher_stat_data, adjusted_stat_data, blood_impact=None, second_blood_impact=None):
    team_stlats, team_defense, batter_order = {}, {}, {}
    team_defense["omni_base_hit"], team_defense["watch_attempt_steal"], team_defense["chasi_triple"], team_defense["chasi_double"], team_defense["anticap_caught_steal_base"], team_defense["anticap_caught_steal_home"], team_defense["tenacious_runner_advances"] = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    lineup = 0
    blood_count = 12.0
    a_blood_factor = 1.0 / blood_count
    
    for playerid in team_stat_data:        
        if (blood_impact and not second_blood_impact) or not blood_impact:
            overperform_pct = 0
            if blood_impact and not second_blood_impact:
                if playerid in blood_impact:
                    overperform_pct = blood_impact[playerid]        
                else:
                    overperform_pct = 0
        elif blood_impact and second_blood_impact:
            overperform_pct = (blood_impact[playerid] * a_blood_factor) + (second_blood_impact[playerid] * a_blood_factor)
        if not team_stat_data[playerid]["shelled"]:
            batter_order[playerid] = team_stat_data[playerid]["turnOrder"]
            team_stlats[playerid] = {}                                    
            team_stlats[playerid], player_omni_base_hit, player_watch_attempt_steal, player_chasi_triple, player_chasi_double, player_anticap_caught_steal_base, player_anticap_caught_steal_home, player_tenacious_runner_advances = calc_player_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, away_home, team_stat_data[playerid], adjusted_stat_data[away_home][playerid], overperform_pct)                  
        else:
            player_omni_base_hit, player_watch_attempt_steal, player_chasi_triple, player_chasi_double, player_anticap_caught_steal_base, player_anticap_caught_steal_home, player_tenacious_runner_advances = calc_player_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, away_home, team_stat_data[playerid], adjusted_stat_data[away_home][playerid], overperform_pct)
        lineup += 1
        team_defense["omni_base_hit"] += player_omni_base_hit
        team_defense["watch_attempt_steal"] += player_watch_attempt_steal
        team_defense["chasi_triple"] += player_chasi_triple
        team_defense["chasi_double"] += player_chasi_double
        team_defense["anticap_caught_steal_base"] += player_anticap_caught_steal_base
        team_defense["anticap_caught_steal_home"] += player_anticap_caught_steal_home
        team_defense["tenacious_runner_advances"] += player_tenacious_runner_advances
    sorted_batters = dict(sorted(batter_order.items(), key=lambda item: item[1]))
    team_defense["omni_base_hit"] = team_defense["omni_base_hit"] / lineup
    team_defense["watch_attempt_steal"] = team_defense["watch_attempt_steal"] / lineup
    team_defense["chasi_triple"] = team_defense["chasi_triple"] / lineup
    team_defense["chasi_double"] = team_defense["chasi_double"] / lineup
    team_defense["anticap_caught_steal_base"] = team_defense["anticap_caught_steal_base"] / lineup
    team_defense["anticap_caught_steal_home"] = team_defense["anticap_caught_steal_home"] / lineup
    team_defense["tenacious_runner_advances"] = team_defense["tenacious_runner_advances"] / lineup    
    pitcherStlats = calc_pitcher_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, away_home, pitcher_stat_data)

    return team_stlats, team_defense, sorted_batters, pitcherStlats

def blood_impact_calc(terms, mods, weather, away_home, teamMods, calc_team_data, calc_opp_data, calc_pitcher_data, team_stat_data, opp_stat_data, opp_pitcher_data, team_pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjusted_stat_data, adjustments, innings=9):
    if away_home == "away":
        awayAttrs, homeAttrs = teamAttrs, oppAttrs
    else:
        awayAttrs, homeAttrs = oppAttrs, teamAttrs
    if "aa" in teamAttrs:
        average_aa_impact = calc_probs_from_stats(mods, weather, teamMods, calc_team_data, calc_opp_data, calc_pitcher_data, team_stat_data, opp_stat_data, opp_pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, "aa", innings)
        team_stlats, team_defense, batter_order, pitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data, team_pitcher_data, adjusted_stat_data, average_aa_impact)
    if "aaa" in teamAttrs:
        average_aaa_impact = calc_probs_from_stats(mods, weather, teamMods, calc_team_data, calc_opp_data, calc_pitcher_data, team_stat_data, opp_stat_data, opp_pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, "aaa", innings)
        team_stlats, team_defense, batter_order, pitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data, team_pitcher_data, adjusted_stat_data, average_aaa_impact)
    if "a" in teamAttrs:
        average_aa_impact, average_aaa_impact = calc_probs_from_stats(mods, weather, teamMods, calc_team_data, calc_opp_data, calc_pitcher_data, team_stat_data, opp_stat_data, opp_pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, "a", innings)
        team_stlats, team_defense, batter_order, pitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data, team_pitcher_data, adjusted_stat_data, average_aa_impact, average_aaa_impact)
    if "high_pressure" in teamAttrs:
        high_pressure_mod = calc_probs_from_stats(mods, weather, teamMods, calc_team_data, calc_opp_data, calc_pitcher_data, team_stat_data, opp_stat_data, opp_pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, "high_pressure", innings)
        team_stlats, team_defense, batter_order, pitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data, team_pitcher_data, adjusted_stat_data, high_pressure_mod)
    return team_stlats, team_defense, batter_order, pitcherStlats
    
def get_mofo_playerbased(mods, awayPitcher, homePitcher, awayTeam, homeTeam, awayAttrs, homeAttrs, weather, team_stat_data, pitcher_stat_data, terms, awayMods, homeMods, adjusted_stat_data, adjustments, skip_mods=False, runtime_solution=False):            
    polarity_plus, polarity_minus, flood_weather = helpers.get_weather_idx("Polarity +"), helpers.get_weather_idx("Polarity -"), helpers.get_weather_idx("Flooding")
    if weather == polarity_plus or weather == polarity_minus:
        if not runtime_solution:
            return .5, .5    

    away_team_stlats, away_team_defense, away_batter_order, awayPitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, "away", team_stat_data[awayTeam], pitcher_stat_data[awayPitcher], adjusted_stat_data)
    home_team_stlats, home_team_defense, home_batter_order, homePitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, homeMods, weather, "home", team_stat_data[homeTeam], pitcher_stat_data[homePitcher], adjusted_stat_data)

    if "aaa" in awayAttrs or "aa" in awayAttrs or "a" in awayAttrs or ("high_pressure" in awayAttrs and weather == flood_weather):
        away_team_stlats, away_team_defense, away_batter_order, awayPitcherStlats = blood_impact_calc(terms, mods, weather, "away", awayMods, away_team_stlats, home_team_defense, homePitcherStlats, team_stat_data[awayTeam], team_stat_data[homeTeam], pitcher_stat_data[homePitcher], pitcher_stat_data[awayPitcher], awayAttrs, homeAttrs, away_batter_order, adjusted_stat_data, adjustments, innings=9)
    if "aaa" in homeAttrs or "aa" in homeAttrs or "a" in homeAttrs or ("high_pressure" in homeAttrs and weather == flood_weather):
        home_team_stlats, home_team_defense, home_batter_order, homePitcherStlats = blood_impact_calc(terms, mods, weather, "home", homeMods, home_team_stlats, away_team_defense, awayPitcherStlats, team_stat_data[homeTeam], team_stat_data[awayTeam], pitcher_stat_data[awayPitcher], pitcher_stat_data[homePitcher], homeAttrs, awayAttrs, home_batter_order, adjusted_stat_data, adjustments, innings=9)
    
    if runtime_solution:
        away_score, away_stolen_bases, away_homers, away_hits, home_pitcher_ks, away_rbi = calc_team_score(mods, weather, awayMods, "away", away_team_stlats, home_team_defense, homePitcherStlats, team_stat_data[awayTeam], team_stat_data[homeTeam], pitcher_stat_data[homePitcher], awayAttrs, homeAttrs, away_batter_order, adjustments, opp_score=None, innings=9, outs=3, runtime_solution=runtime_solution)
        home_score, home_stolen_bases, home_homers, home_hits, away_pitcher_ks, home_rbi = calc_team_score(mods, weather, homeMods, "home", home_team_stlats, away_team_defense, awayPitcherStlats, team_stat_data[homeTeam], team_stat_data[awayTeam], pitcher_stat_data[awayPitcher], homeAttrs, awayAttrs, home_batter_order, adjustments, opp_score=away_score, innings=9, outs=3, runtime_solution=runtime_solution)        
    else:            
        away_score = calc_team_score(mods, weather, awayMods, "away", away_team_stlats, home_team_defense, homePitcherStlats, team_stat_data[awayTeam], team_stat_data[homeTeam], pitcher_stat_data[homePitcher], awayAttrs, homeAttrs, away_batter_order, adjustments)
        home_score = calc_team_score(mods, weather, homeMods, "home", home_team_stlats, away_team_defense, awayPitcherStlats, team_stat_data[homeTeam], team_stat_data[awayTeam], pitcher_stat_data[awayPitcher], homeAttrs, awayAttrs, home_batter_order, adjustments)   

    if away_score < 0:
        away_score += abs(away_score) * 2.0
        home_score += abs(away_score) * 2.0
    if home_score < 0:
        away_score += abs(home_score) * 2.0
        home_score += abs(home_score) * 2.0

    numerator = away_score - home_score
    denominator = away_score + home_score
    away_pitcher_era, home_pitcher_era = home_rbi, away_rbi
    if not denominator:
        if not runtime_solution:
            return .5, .5    
        else:
            return .5, .5, away_hits, home_hits, away_homers, home_homers, away_stolen_bases, home_stolen_bases, away_pitcher_ks, home_pitcher_ks, away_pitcher_era, home_pitcher_era
    away_formula = numerator / denominator        
    #log_transform_base = math.e
    log_transform_base = 10.0
    away_odds = log_transform(away_formula, log_transform_base)
    if runtime_solution:        
        if weather == polarity_plus or weather == polarity_minus:
            return .5, .5, away_hits, home_hits, away_homers, home_homers, away_stolen_bases, home_stolen_bases, away_pitcher_ks, home_pitcher_ks, away_pitcher_era, home_pitcher_era
        return away_odds, 1.0 - away_odds, away_hits, home_hits, away_homers, home_homers, away_stolen_bases, home_stolen_bases, away_pitcher_ks, home_pitcher_ks, away_pitcher_era, home_pitcher_era
    return away_odds, 1.0 - away_odds

def get_player_mods(mods, awayAttrs, homeAttrs, weather, away_home, player_stat_data):     
    playerMods = collections.defaultdict(lambda: [])
    return playerMods
    #lowerAwayAttrs, lowerHomeAttrs = awayAttrs, homeAttrs    
    #playerAttrs = player_stat_data["attrs"]
    #allAttrs_lol = [lowerAwayAttrs, lowerHomeAttrs, playerAttrs]
    #allAttrs_set = set().union(*allAttrs_lol)
    #modAttrs_set = set(mods.keys())
    #allModAttrs_set = allAttrs_set.intersection(modAttrs_set) - MODS_CALCED_DIFFERENTLY
    #allAttrs = list(allAttrs_set)   
    #modAttrs = list(allModAttrs_set)        
    ##applied_mods = []
    #bird_weather = helpers.get_weather_idx("Birds")    
    #flood_weather = helpers.get_weather_idx("Flooding")       

    #for attr in modAttrs:        
    #    if attr == "affinity_for_crows" and weather != bird_weather:
    #        continue
    #    if attr == "high_pressure" and weather != flood_weather:
    #        continue    
    #    if away_home == "home" and attr == "traveling":
    #        continue
    #    if attr in mods:            
    #        if (away_home == "home" and attr in lowerHomeAttrs) or (away_home == "away" and attr in lowerAwayAttrs) or (attr in playerAttrs):
    #            for name, stlatterm in mods[attr]["same"].items():                
    #                multiplier = calc_player_stlatmod(name, player_stat_data, stlatterm)
    #                if multiplier is not None:
    #                    playerMods[name].append(multiplier)                        
    #        if (away_home == "away" and attr in lowerHomeAttrs) or (away_home == "home" and attr in lowerAwayAttrs):
    #            for name, stlatterm in mods[attr]["opp"].items():                
    #                multiplier = calc_player_stlatmod(name, player_stat_data, stlatterm)
    #                if multiplier is not None:
    #                    playerMods[name].append(multiplier)                           
    #return playerMods

def get_park_mods(ballpark, ballpark_mods):
    awayMods, homeMods = collections.defaultdict(lambda: []), collections.defaultdict(lambda: [])  
    logbase = math.e
    for ballparkstlat, stlatterms in ballpark_mods.items():        
        for playerstlat, stlatterm in stlatterms.items():
            if type(stlatterm) == ParkTerm:            
                value = ballpark[ballparkstlat]                
                adjusted_value = value
                if ballparkstlat != "hype":
                    adjusted_value -= 0.5                    
                    normalized_value = stlatterm.calc(abs(adjusted_value))
                    base_multiplier = (log_transform(normalized_value, logbase) - 0.5) * 2.0
                    if base_multiplier == 0.0:             
                        multiplier = 0.0
                    else:
                        if adjusted_value < 0:
                            base_multiplier *= -1
                        multiplier = base_multiplier
                else:                    
                    normalized_value = stlatterm.calc(value)
                    base_multiplier = log_transform(normalized_value, logbase) * 2.0
                #forcing harmonic mean with quicker process time?  
                    if base_multiplier <= 0.00001:             
                        multiplier = 0.0
                    else:
                        multiplier = 1.0 / base_multiplier
                if ballparkstlat != "hype":                                                    
                    awayMods[playerstlat] = multiplier                                           
                homeMods[playerstlat] = multiplier
    return awayMods, homeMods

def setup_playerbased(weather, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, team_stat_data, pitcher_stat_data):
    terms_url = os.getenv("MOFO_TERMS")
    terms, _ = helpers.load_terms(terms_url)
    halfterms_url = os.getenv("MOFO_HALF_TERMS")
    halfterms = helpers.load_half_terms(halfterms_url)
    mods_url = os.getenv("MOFO_MODS")
    mods = helpers.load_mods(mods_url)
    ballparks_url = os.getenv("BALLPARKS")
    ballparks = helpers.load_ballparks(ballparks_url)
    ballpark_mods_url = os.getenv("MOFO_BALLPARK_TERMS")
    ballpark_mods = helpers.load_bp_terms(ballpark_mods_url)
    homeTeamId = helpers.get_team_id(homeTeam)
    ballpark = ballparks.get(homeTeamId, collections.defaultdict(lambda: 0.5))
    awayMods, homeMods = get_park_mods(ballpark, ballpark_mods)
    adjustments = instantiate_adjustments(terms, halfterms)
    return mods, terms, awayMods, homeMods, adjustments

def calculate_playerbased(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, awayAttrs, homeAttrs,
              day, weather, skip_mods=False):    
    mods, terms, awayMods, homeMods, adjustments = setup_playerbased(weather, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, team_stat_data, pitcher_stat_data)
    adjusted_stat_data = helpers.calculate_adjusted_stat_data(awayAttrs, homeAttrs, awayTeam, homeTeam, team_stat_data)
    return get_mofo_playerbased(mods, awayPitcher, homePitcher, awayTeam, homeTeam, awayAttrs, homeAttrs, weather, team_stat_data, pitcher_stat_data, terms, awayMods, homeMods, adjusted_stat_data, adjustments, skip_mods=skip_mods)

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
                base_multiplier = log_transform(normalized_value, 100.0)
                #forcing harmonic mean with quicker process time?
                if value > 0.5:
                    multiplier = 1.0 / (2.0 * base_multiplier)
                elif value < 0.5:
                    multiplier = 1.0 / (2.0 - (2.0 * base_multiplier))
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
    away_odds = log_transform(away_formula, 100.0)    
    return away_odds, 1.0 - away_odds
