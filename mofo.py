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
BLOOD_LIST_DEFENSE = ["PSYCHIC"]
BLOOD_LIST_PITCHING = ["LOVE", "PSYCHIC"]
BLOOD_LIST_OFFENSE = ["LOVE", "PSYCHIC"]

MODS_CALCED_DIFFERENTLY = {"aaa", "aa", "a", "fiery", "base_instincts", "o_no", "electric", "h20", "0", "acidic"}

def instantiate_adjustments(terms, halfterms): 
    adjustments = {}
    for stlat in halfterms:
        for event in halfterms[stlat]:        
            adjustments[event] = terms[stlat].calc(halfterms[stlat][event])    
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
    multiplier, numerator, denominator = 1.0, 0.0, 0.0    
    if not skip_mods:            
        modterms = (mods or {}).get(stlatname, [])          
        parkmodterms = (parkmods or {}).get(stlatname, []) 
        bloodmodterms  = (bloodmods or {}).get(stlatname, [])          
        if len(modterms) > 0:
            numerator += len(modterms)
            denominator += sum(modterms)            
        if len(parkmodterms) > 0:
            numerator += len(parkmodterms)
            denominator += sum(parkmodterms)
        if len(bloodmodterms) > 0:
            numerator += len(bloodmodterms)
            denominator += sum(bloodmodterms)    
        if denominator > 0.0:
            multiplier *= (numerator / denominator)
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
        transformed_value = (1.0 / (1.0 + (base ** (-1.0 * value))))
    except:                    
        transformed_value = 1.0 if (value > 0) else 0.0
    return transformed_value

def calc_defense(terms, player_mods, park_mods, player_stat_data, adjusted_stlats, bloodMods=None, overperform_pct=0):
    if overperform_pct > 0.01:                
        player_stat_data["omniscience"] += (adjusted_stlats["omniscience"] - player_stat_data["omniscience"]) * overperform_pct
        player_stat_data["watchfulness"] += (adjusted_stlats["watchfulness"] - player_stat_data["watchfulness"]) * overperform_pct 
        player_stat_data["chasiness"] += (adjusted_stlats["chasiness"] - player_stat_data["chasiness"]) * overperform_pct 
        player_stat_data["anticapitalism"] += (adjusted_stlats["anticapitalism"] - player_stat_data["anticapitalism"]) * overperform_pct 
        player_stat_data["tenaciousness"] += (adjusted_stlats["tenaciousness"] - player_stat_data["tenaciousness"]) * overperform_pct
    player_omniscience = calc_player(terms, "omniscience", player_stat_data["omniscience"], player_mods, park_mods, bloodMods, False)
    player_watchfulness = calc_player(terms, "watchfulness", player_stat_data["watchfulness"], player_mods, park_mods, bloodMods, False)
    player_chasiness = calc_player(terms, "chasiness", player_stat_data["chasiness"], player_mods, park_mods, bloodMods, False)
    player_anticapitalism = calc_player(terms, "anticapitalism", player_stat_data["anticapitalism"], player_mods, park_mods, bloodMods, False)
    player_tenaciousness = calc_player(terms, "tenaciousness", player_stat_data["tenaciousness"], player_mods, park_mods, bloodMods, False)        
    return player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness

def calc_batting(terms, player_mods, park_mods, player_stat_data, adjusted_stlats, bloodMods=None, overperform_pct=0):  
    if overperform_pct > 0.01:                
        player_stat_data["patheticism"] += (adjusted_stlats["patheticism"] - player_stat_data["patheticism"]) * overperform_pct
        player_stat_data["tragicness"] += (adjusted_stlats["tragicness"] - player_stat_data["tragicness"]) * overperform_pct
        player_stat_data["thwackability"] += (adjusted_stlats["thwackability"] - player_stat_data["thwackability"]) * overperform_pct
        player_stat_data["divinity"] += (adjusted_stlats["divinity"] - player_stat_data["divinity"]) * overperform_pct 
        player_stat_data["moxie"] += (adjusted_stlats["moxie"] - player_stat_data["moxie"]) * overperform_pct 
        player_stat_data["musclitude"] += (adjusted_stlats["musclitude"] - player_stat_data["musclitude"]) * overperform_pct 
        player_stat_data["martyrdom"] += (adjusted_stlats["martyrdom"] - player_stat_data["martyrdom"]) * overperform_pct        
    player_patheticism = calc_player(terms, "patheticism", player_stat_data["patheticism"], player_mods, park_mods, bloodMods, False)
    player_tragicness = calc_player(terms, "tragicness", player_stat_data["tragicness"], player_mods, park_mods, bloodMods, False)
    player_thwackability = calc_player(terms, "thwackability", player_stat_data["thwackability"], player_mods, park_mods, bloodMods, False)
    player_divinity = calc_player(terms, "divinity", player_stat_data["divinity"], player_mods, park_mods, bloodMods, False)
    player_moxie = calc_player(terms, "moxie", player_stat_data["moxie"], player_mods, park_mods, bloodMods, False)
    player_musclitude = calc_player(terms, "musclitude", player_stat_data["musclitude"], player_mods, park_mods, bloodMods, False)
    player_martyrdom = calc_player(terms, "martyrdom", player_stat_data["martyrdom"], player_mods, park_mods, bloodMods, False)    
    return player_patheticism, player_tragicness, player_thwackability, player_divinity, player_moxie, player_musclitude, player_martyrdom

def calc_running(terms, player_mods, park_mods, player_stat_data, adjusted_stlats, bloodMods=None, overperform_pct=0):
    if overperform_pct > 0.01:                
        player_stat_data["laserlikeness"] += (adjusted_stlats["laserlikeness"] - player_stat_data["laserlikeness"]) * overperform_pct
        player_stat_data["baseThirst"] += (adjusted_stlats["baseThirst"] - player_stat_data["baseThirst"]) * overperform_pct 
        player_stat_data["continuation"] += (adjusted_stlats["continuation"] - player_stat_data["continuation"]) * overperform_pct 
        player_stat_data["groundFriction"] += (adjusted_stlats["groundFriction"] - player_stat_data["groundFriction"]) * overperform_pct 
        player_stat_data["indulgence"] += (adjusted_stlats["indulgence"] - player_stat_data["indulgence"]) * overperform_pct
    player_laserlikeness = calc_player(terms, "laserlikeness", player_stat_data["laserlikeness"], player_mods, park_mods, bloodMods, False)
    player_basethirst = calc_player(terms, "basethirst", player_stat_data["baseThirst"], player_mods, park_mods, bloodMods, False)
    player_continuation = calc_player(terms, "continuation", player_stat_data["continuation"], player_mods, park_mods, bloodMods, False)
    player_groundfriction = calc_player(terms, "groundfriction", player_stat_data["groundFriction"], player_mods, park_mods, bloodMods, False)
    player_indulgence = calc_player(terms, "indulgence", player_stat_data["indulgence"], player_mods, park_mods, bloodMods, False)     
    return player_laserlikeness, player_basethirst, player_continuation, player_groundfriction, player_indulgence

def calc_pitching(terms, pitcher_mods, park_mods, pitcher_stat_data, bloodMods=None):   
    player_unthwackability = calc_player(terms, "unthwackability", pitcher_stat_data["unthwackability"], pitcher_mods, park_mods, bloodMods, False)
    player_ruthlessness = calc_player(terms, "ruthlessness", pitcher_stat_data["ruthlessness"], pitcher_mods, park_mods, bloodMods, False)
    player_overpowerment = calc_player(terms, "overpowerment", pitcher_stat_data["overpowerment"], pitcher_mods, park_mods, bloodMods, False)
    player_shakespearianism = calc_player(terms, "shakespearianism", pitcher_stat_data["shakespearianism"], pitcher_mods, park_mods, bloodMods, False)
    player_coldness = calc_player(terms, "coldness", pitcher_stat_data["coldness"], pitcher_mods, park_mods, bloodMods, False)
    return player_unthwackability, player_ruthlessness, player_overpowerment, player_shakespearianism, player_coldness

def calc_probs_from_stats(mods, weather, team_stat_data, opp_stat_data, pitcher_stat_data, team_data, opp_data, pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, blood_calc=None, innings=9, outs=3):
    battingAttrs = [attr.lower() for attr in teamAttrs]
    opponentAttrs = [attr.lower() for attr in oppAttrs]
    pitcherAttrs = [attr.lower() for attr in pitcher_data["attrs"].split(";")]    
    strike_out_chance, caught_out_chance, attempt_steal_chance, walk_chance, hit_modifier, sacrifice_chance, runner_advance_chance, homerun_multipliers, caught_steal_base_chance, caught_steal_home_chance = {}, {}, {}, {}, {}, {}, {}, {}, {}, {}
    single_chance, double_chance, triple_chance, homerun_chance, score_multiplier, average_on_base_position, steal_mod, caught_steal_outs = {}, {}, {}, {}, {}, {}, {}, {}

    blood_count = 12.0
    a_blood_multiplier = 1.0 / blood_count    

    omniscience, watchfulness, chasiness, anticap, tenaciousness = opp_stat_data["omniscience"], opp_stat_data["watchfulness"], opp_stat_data["chasiness"], opp_stat_data["anticapitalism"], opp_stat_data["tenaciousness"]
    unthwackability, ruthlessness, overpowerment, shakespearianism, coldness = pitcher_stat_data["unthwackability"], pitcher_stat_data["ruthlessness"], pitcher_stat_data["overpowerment"], pitcher_stat_data["shakespearianism"], pitcher_stat_data["coldness"]    
        
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
    strike_mod, walk_mod, score_mod = 1.0, 0.0, 0.0
    if "fiery" in opponentAttrs:                
        strike_mod += mods["fiery"]["same"]["multiplier"]
    if "acidic" in opponentAttrs:                
        score_mod += mods["acidic"]["same"]["multiplier"]
    if "electric" in battingAttrs:
        strike_mod -= mods["electric"]["same"]["multiplier"]
    if "base_instincts" in battingAttrs:
        walk_mod += mods["base_instincts"]["same"]["multiplier"]
    if "a" in opponentAttrs:
        strike_mod += mods["fiery"]["same"]["multiplier"] * a_blood_multiplier
        score_mod += mods["acidic"]["same"]["multiplier"] * a_blood_multiplier
    if "a" in battingAttrs:
        strike_mod -= mods["electric"]["same"]["multiplier"] * a_blood_multiplier
        walk_mod += mods["base_instincts"]["same"]["multiplier"] * a_blood_multiplier            

    strike_log = (ruthlessness - adjustments["ruth_strike"])
    strike_chance = log_transform(strike_log, 100.0)
    clutch_log = (coldness - adjustments["cold_clutch_factor"])
    clutch_factor = log_transform(clutch_log, 100.0)    
    playerAttrs = []
        
    for playerid in sorted_batters:                                                      
        playerAttrs = [attr.lower() for attr in team_data[playerid]["attrs"].split(";")]
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
        patheticism, tragicness, thwackability, divinity, moxie, musclitude, martyrdom = team_stat_data[playerid]["patheticism"], team_stat_data[playerid]["tragicness"], team_stat_data[playerid]["thwackability"], team_stat_data[playerid]["divinity"], team_stat_data[playerid]["moxie"], team_stat_data[playerid]["musclitude"], team_stat_data[playerid]["martyrdom"]
        laserlikeness, basethirst, continuation, groundfriction, indulgence = team_stat_data[playerid]["laserlikeness"], team_stat_data[playerid]["basethirst"], team_stat_data[playerid]["continuation"], team_stat_data[playerid]["groundfriction"], team_stat_data[playerid]["indulgence"]
        
        moxie_log = (moxie - adjustments["moxie_swing_correct"])
        swing_correct_chance = log_transform(moxie_log, 100.0)        
        swing_strike_blood_factors = ((1.0 / outs) if ("h20" in battingAttrs or "h20" in playerAttrs) else 0.0) + ((strike_chance / (strike_count + ball_count)) if (("0" in battingAttrs or "0" in playerAttrs) and "skipping" not in playerAttrs) else 0.0)
        if "a" in battingAttrs and not blood_calc:
            swing_strike_blood_factors += ((1.0 / outs) * a_blood_multiplier) + (((strike_chance / (strike_count + ball_count)) * a_blood_multiplier) if "skipping" not in playerAttrs else 0.0)
        swing_strike_chance = (min(swing_correct_chance + swing_strike_blood_factors, 1.0)) * strike_chance        
        swing_ball_chance = min(max(((1.0 - swing_correct_chance) * (1.0 - strike_chance)) - (((1.0 - strike_chance) ** ball_count) if "flinch" in playerAttrs else 0.0), 0.0), 1.0)

        connect_log = (adjustments["path_connect"] - patheticism)
        base_connect_chance = log_transform(connect_log, 100.0)
        connect_chance = base_connect_chance * swing_strike_chance
        
        base_hit_log = ((thwackability - unthwackability - omniscience) - (adjustments["thwack_base_hit"] - adjustments["unthwack_base_hit"] - adjustments["omni_base_hit"]))
        base_hit = log_transform(base_hit_log, 100.0)
        base_hit_chance = base_hit * connect_chance                     

        strike_looking_chance = min(((1.0 - swing_correct_chance) * strike_chance), 1.0)
        strike_swinging_chance = min((1.0 - connect_chance) + swing_ball_chance, 1.0)      
        ball_chance = 1.0 - swing_ball_chance     

        foul_ball_log = musclitude - adjustments["muscl_foul_ball"]
        foul_ball_prob = log_transform(foul_ball_log, 100.0)
        foul_ball_chance = foul_ball_prob * (1.0 - base_hit) * connect_chance
        caught_out_chance[playerid] = max(connect_chance - foul_ball_chance - base_hit_chance, 0.0)

        all_connect_events_prob = base_hit_chance + foul_ball_chance + caught_out_chance[playerid]
        if all_connect_events_prob != connect_chance:
            factor = connect_chance / all_connect_events_prob
            base_hit_chance *= factor
            foul_ball_chance *= factor
            caught_out_chance[playerid] *= factor 
            
        all_pitch_events_prob = strike_looking_chance + strike_swinging_chance + connect_chance + ball_chance
        if all_pitch_events_prob != 1.0:
            factor = 1.0 / all_pitch_events_prob
            strike_looking_chance *= factor
            strike_swinging_chance *= factor
            connect_chance *= factor
            ball_chance *= factor

        #possibiliies are any three of foul balls (only up to strikecount - 1), strike swinging, and strike looking
        #always need at least one strike to strike out
        #walks are ball count balls plus any combination above that does not include the final strike
        strikeout = (strike_looking_chance ** strike_count) + (strike_swinging_chance ** strike_count)
        walked = ball_chance ** ball_count
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
        if "o_no" in battingAttrs or "o_no" in playerAttrs or ("a" in battingAttrs and not blood_calc):
            #probability of no balls happening is the probability that every strike is a strike AND every ball is swung at
            no_balls = ((strike_chance * (1.0 - swing_correct_chance)) + (strike_chance * swing_correct_chance * (1.0 - base_connect_chance))) * ((1.0 - swing_correct_chance) * (1.0 - strike_chance))          
            no_balls = min(no_balls, 1.0)
            #straight up for o_no; a blood needs no balls reduced by blood multiplier first since it only matters when a blood procced o_no                     
            if "a" in battingAttrs:                
                no_balls *= a_blood_multiplier
            #probability of a least one ball happening is 1 - probability of no balls happening
            corrected_strike_chance *= (1.0 - no_balls)

        corrected_strike_chance *= strike_mod
        #everything else is per pitch... connect per pitch, base hit per pitch, caught out per pitch, so each ball pitched is 1 / ball count % of a walk
        walk_chance[playerid] = walked
        strike_out_chance[playerid] = corrected_strike_chance

        #the sum of these events (which would be one or the other or the other etc.) must be one, as they are everything that can happen on a plate appearance
        all_macro_events_prob = walk_chance[playerid] + base_hit_chance + strike_out_chance[playerid] + caught_out_chance[playerid]        
        #if the sum is not one, correct all probabilities such that the sum will be equal to 1.0, which will preserve the relative probabilities for all events
        if all_macro_events_prob != 1.0:
            #if caught_out_chance[playerid] > 0.0000:
            #    print("Pre-normalized: strikeout {:.4f}, walked {:.4f}, base hit {:.4f}, caughtout {:.4f}".format(strike_out_chance[playerid], walk_chance[playerid], base_hit_chance, caught_out_chance[playerid]))
            factor = 1.0 / all_macro_events_prob
            walk_chance[playerid] *= factor
            strike_out_chance[playerid] *= factor
            base_hit_chance *= factor
            caught_out_chance[playerid] *= factor
            all_macro_events_prob = walk_chance[playerid] + base_hit_chance + strike_out_chance[playerid] + caught_out_chance[playerid]                 
            #if caught_out_chance[playerid] > 0.0000:
            #    print("Normalized to: strikeout {:.4f}, walked {:.4f}, base hit {:.4f}, caughtout {:.4f}".format(strike_out_chance[playerid], walk_chance[playerid], base_hit_chance, caught_out_chance[playerid]))

        attempt_steal_log = ((basethirst + laserlikeness - watchfulness) - (adjustments["baset_attempt_steal"] + adjustments["laser_attempt_steal"] - adjustments["watch_attempt_steal"]))
        attempt_steal_chance[playerid] = log_transform(attempt_steal_log, 100.0)
        caught_steal_base_log = ((laserlikeness - anticap) - (adjustments["laser_caught_steal_base"] - adjustments["anticap_caught_steal_base"]))
        caught_steal_home_log = ((basethirst + laserlikeness - anticap) - (adjustments["baset_caught_steal_home"] + adjustments["laser_caught_steal_home"] - adjustments["anticap_caught_steal_home"]))
        caught_steal_base_chance[playerid] = log_transform(caught_steal_base_log, 100.0)        
        caught_steal_home_chance[playerid] = log_transform(caught_steal_home_log, 100.0)             
        
        #homeruns needs to care about how many other runners are on base for how valuable they are, with a floor of "1x"
        homerun_log = ((divinity - overpowerment) - (adjustments["div_homer"] - adjustments["overp_homer"]))
        homerun_prob = log_transform(homerun_log, 100.0)
        homerun_chance[playerid] = homerun_prob * base_hit_chance
        homerun_multipliers[playerid] = homer_multiplier        

        triple_log = ((musclitude + groundfriction + continuation - overpowerment - chasiness) - (adjustments["muscl_triple"] + adjustments["ground_triple"] + adjustments["cont_triple"] - adjustments["overp_triple"] - adjustments["chasi_triple"]))
        triple_prob = log_transform(triple_log, 100.0) * (1.0 - homerun_chance[playerid])
        triple_chance[playerid] = triple_prob * base_hit_chance        

        double_log = ((musclitude + continuation - overpowerment - chasiness) - (adjustments["muscl_double"] + adjustments["cont_double"] - adjustments["overp_double"] - adjustments["chasi_double"]))
        double_prob = log_transform(double_log, 100.0) * (1.0 - triple_prob) * (1.0 - homerun_prob)
        double_chance[playerid] = double_prob * base_hit_chance 
        
        single_chance[playerid] = max(base_hit_chance - triple_chance[playerid] - double_chance[playerid] - homerun_chance[playerid], 0.0)        
        #normalize these to sum to base hit chance
        all_base_hit_events_prob = single_chance[playerid] + triple_chance[playerid] + double_chance[playerid] + homerun_chance[playerid]
        if all_base_hit_events_prob != base_hit_chance:
            factor = base_hit_chance / all_macro_events_prob
            single_chance[playerid] *= factor
            triple_chance[playerid] *= factor
            double_chance[playerid] *= factor
            homerun_chance[playerid] *= factor            
        
        hit_modifier[playerid] = hit_multiplier          

        #runners advancing is tricky, since we have to do this based on runners being on base already, but use the batter's martyrdom for sacrifices
        sacrifice_log = martyrdom - adjustments["martyr_sacrifice"]
        sacrifice_chance[playerid] = log_transform(sacrifice_log, 100.0) * caught_out_chance[playerid]        
        
        runner_advances_log = ((laserlikeness + indulgence - tragicness - shakespearianism - tenaciousness) - (adjustments["laser_runner_advances"] + adjustments["indulg_runner_advances"] - adjustments["trag_runner_advances"] - adjustments["shakes_runner_advances"] - adjustments["shakes_runner_advances"]))        
        runner_advance_chance[playerid] = log_transform(runner_advances_log, 100.0)
        average_on_base_position[playerid] = {}
        average_on_base_position[playerid]["first"] = min(single_chance[playerid] + (walk_chance[playerid] * (1.0 - walk_mod)), 1.0)
        average_on_base_position[playerid]["second"] = min(double_chance[playerid] + (walk_chance[playerid] * walk_mod), 1.0)
        average_on_base_position[playerid]["third"] = min(triple_chance[playerid] + (walk_chance[playerid] * walk_mod), 1.0)                

        #need to approximate caught stealing outs for blood calcing        
        average_bases_to_steal = (2.0 * average_on_base_position[playerid]["first"]) + average_on_base_position[playerid]["second"]
        average_home_to_steal = average_on_base_position[playerid]["first"] + average_on_base_position[playerid]["second"] + average_on_base_position[playerid]["third"]
        caught_steal_outs[playerid] = min((caught_steal_base_chance[playerid] * attempt_steal_chance[playerid] * average_bases_to_steal) + (caught_steal_home_chance[playerid] * attempt_steal_chance[playerid] * average_home_to_steal), 1.0)
        
        playerAttrs.clear()

    if blood_calc:                        
        outs_per_lineup = sum(strike_out_chance.values()) + sum(caught_steal_outs.values()) + sum(caught_out_chance.values())            
        average_aaa_blood_impact, average_aa_blood_impact = {}, {}
        max_x = outs * innings * 3.0      
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

def calc_team_score(mods, weather, team_stat_data, opp_stat_data, pitcher_stat_data, team_data, opp_data, pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, innings=9, outs=3, runtime_solution=False):          
    battingAttrs = [attr.lower() for attr in teamAttrs]
    reverb_weather, sun_weather, bh_weather = helpers.get_weather_idx("Reverb"), helpers.get_weather_idx("Sun 2"), helpers.get_weather_idx("Black Hole")
    runner_advance_chance, caught_out_chance, sacrifice_chance, score_mod, hit_modifier, homerun_multipliers, score_multiplier, attempt_steal_chance, walk_chance, strike_out_chance, caught_steal_base_chance, caught_steal_home_chance, homerun_chance, triple_chance, double_chance, single_chance, average_on_base_position, steal_mod, clutch_factor, walk_mod = calc_probs_from_stats(mods, weather, team_stat_data, opp_stat_data, pitcher_stat_data, team_data, opp_data, pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, None, innings)        

    #run three "games" to get a more-representative average
    total_innings = innings * 3.0
    current_innings, atbats_in_inning = 0, 0  
    current_outs = 0.0
    team_score = 100.0 if "home_field" in battingAttrs else 0.0
    inning_score = 0.0

    runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
    runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
    inning_outs = 0.0        
    batter_atbats = 0    
    last_player_out = ""
    stolen_bases, homers, hits = {}, {}, {}    
    loop_checker = {}
    loop_encountered, last_pass = False, False            
    
    while current_innings < total_innings:
        starting_lineup_inning_outs, starting_lineup_inning_score = inning_outs, inning_score
        innings_since_lineup_start = 0
        for playerid in sorted_batters:
            batter_atbats += 1
            playerAttrs = [attr.lower() for attr in team_data[playerid]["attrs"].split(";")]
            base = 20.0 if (("extra_base" in battingAttrs) or ("extra_base" in playerAttrs)) else 25.0                   
            if base == 25.0:
                homerun_score = ((100.0 - (10.0 * score_mod)) * (1.0 + runners_on_first + runners_on_second + runners_on_third)) * homerun_chance[playerid] * homerun_multipliers[playerid]
                triple_runners_score = ((100.0 - (10.0 * score_mod)) * (runners_on_first + runners_on_second + runners_on_third)) * hit_modifier[playerid] * triple_chance[playerid]
                double_runners_score = ((100.0 - (10.0 * score_mod)) * (runners_on_second + runners_on_third)) * hit_modifier[playerid] * double_chance[playerid]    
                single_runners_score = ((100.0 - (10.0 * score_mod)) * runners_on_third) * hit_modifier[playerid] * single_chance[playerid]                               
                runners_advance_score = 100.0 * runners_on_third * sacrifice_chance[playerid]
                walking_score = 100.0 * ((runners_on_third * walk_chance[playerid]) + (runners_on_second * (walk_chance[playerid] * walk_mod)) + (runners_on_first * (walk_chance[playerid] * walk_mod)))
            else:
                homerun_score = ((100.0 - (10.0 * score_mod)) * (1.0 + runners_on_first + runners_on_second + runners_on_third + runners_on_fourth)) * homerun_chance[playerid] * homerun_multipliers[playerid]
                triple_runners_score = ((100.0 - (10.0 * score_mod)) * (runners_on_fourth + runners_on_second + runners_on_third)) * hit_modifier[playerid] * triple_chance[playerid]
                double_runners_score = ((100.0 - (10.0 * score_mod)) * (runners_on_fourth + runners_on_third)) * hit_modifier[playerid] * double_chance[playerid]    
                single_runners_score = ((100.0 - (10.0 * score_mod)) * runners_on_fourth) * hit_modifier[playerid] * single_chance[playerid]                               
                runners_advance_score = 100.0 * runners_on_fourth * sacrifice_chance[playerid]
                walking_score = 100.0 * ((runners_on_fourth * walk_chance[playerid]) + (runners_on_third * walk_chance[playerid] * walk_mod) + (runners_on_second * walk_chance[playerid] * walk_mod) + (runners_on_first * walk_chance[playerid] * walk_mod))                
                runners_on_fourth, runner_advance_fourth = calc_runners_on(runners_on_fourth, runner_advance_fourth, runners_on_third, runner_advance_third, runners_on_second, runner_advance_second, runners_on_first, runner_advance_first, single_chance[playerid], double_chance[playerid], triple_chance[playerid], homerun_chance[playerid], sacrifice_chance[playerid], caught_out_chance[playerid], walk_chance[playerid], walk_mod)
            runners_on_third, runner_advance_third = calc_runners_on(runners_on_third, runner_advance_third, runners_on_second, runner_advance_second, runners_on_first, runner_advance_first, 0.0, 0.0, single_chance[playerid], double_chance[playerid], triple_chance[playerid], homerun_chance[playerid], sacrifice_chance[playerid], caught_out_chance[playerid], walk_chance[playerid], walk_mod)
            runners_on_second, runner_advance_second = calc_runners_on(runners_on_second, runner_advance_second, runners_on_first, runner_advance_first, 0.0, 0.0, 0.0, 0.0, single_chance[playerid], double_chance[playerid], triple_chance[playerid], homerun_chance[playerid], sacrifice_chance[playerid], caught_out_chance[playerid], walk_chance[playerid], walk_mod)
            runners_on_first, runner_advance_first = calc_runners_on(runners_on_first, runner_advance_first, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, single_chance[playerid], double_chance[playerid], triple_chance[playerid], homerun_chance[playerid], sacrifice_chance[playerid], caught_out_chance[playerid], walk_chance[playerid], walk_mod)
            player_score = (runners_advance_score + walking_score + homerun_score + triple_runners_score + double_runners_score + single_runners_score) * score_multiplier[playerid]
            if playerid not in homers:
                homers[playerid] = 0.0
                hits[playerid] = 0.0
            homers[playerid] += homerun_chance[playerid]
            hits[playerid] += triple_chance[playerid] + double_chance[playerid] + single_chance[playerid]
            player_outs = strike_out_chance[playerid] + caught_out_chance[playerid]
            inning_outs += player_outs            
            if inning_outs >= outs:
                inning_outs = 0                
                current_innings += 1
                innings_since_lineup_start += 1
                if not runtime_solution:
                    if playerid in loop_checker:
                        if not last_pass:
                            if (str(batter_atbats - atbats_in_inning) in loop_checker[playerid]) and (loop_checker[playerid][str(batter_atbats - atbats_in_inning)][2] == 1):                            
                                #this means that we have hit a loop point; our inning ended with the same player and had the same number of atbats
                                loop_encountered = True                        
                                inning_score = 0.0
                                runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
                                runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
                                break
                    else:
                        loop_checker[playerid] = {}
                    loop_checker[playerid][str(batter_atbats - atbats_in_inning)] = [team_score, current_innings, 1]
                inning_score += player_score
                atbats_in_inning = batter_atbats
                team_score += inning_score                
                inning_score = 0.0
                runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
                runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
                if current_innings >= total_innings:                
                    break
            else:
                steal_runners_on_second = min(runners_on_second, 1.0)
                steal_runners_on_third = min(runners_on_third, 1.0)
                steal_runners_on_fourth = min(runners_on_fourth, 1.0)
                runners_on_third += average_on_base_position[playerid]["third"]
                runners_on_second += average_on_base_position[playerid]["second"]
                runners_on_first += average_on_base_position[playerid]["first"]
                runner_advance_first += average_on_base_position[playerid]["first"] * runner_advance_chance[playerid]
                runner_advance_second += average_on_base_position[playerid]["second"] * runner_advance_chance[playerid]
                runner_advance_third += average_on_base_position[playerid]["third"] * runner_advance_chance[playerid]                
                runners_on_first = min(runners_on_first, 1.0)
                runners_on_second = min(runners_on_second, 1.0)
                runners_on_third = min(runners_on_third, 1.0)
                runners_on_fourth = min(runners_on_fourth, 1.0)
                #since the inning is still live, now we need to calculate potential steals from the batter, taking their likely position on base and computing how much the runners on base positions change
                #stealing from first to second
                if playerid not in stolen_bases:
                    stolen_bases[playerid] = 0.0                
                steal_base_success_rate = (1.0 - caught_steal_base_chance[playerid]) * attempt_steal_chance[playerid]
                steal_home_success_rate = (1.0 - caught_steal_home_chance[playerid]) * attempt_steal_chance[playerid]                
                #steal second
                steal_second_opportunities = average_on_base_position[playerid]["first"] * (1.0 - steal_runners_on_second) 
                #steal third
                steal_third_opportunities = steal_second_opportunities * (1.0 - steal_runners_on_third)
                steal_third_opportunities += average_on_base_position[playerid]["second"] * (1.0 - steal_runners_on_third)
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
                player_score += ((100.0 + steal_mod[playerid]) * (steal_home_opportunities * steal_home_success_rate)) + (steal_mod[playerid] * steal_base_opportunities * steal_base_success_rate)
                steal_outs = (steal_base_opportunities * caught_steal_base_chance[playerid] * attempt_steal_chance[playerid]) + (steal_home_opportunities * caught_steal_home_chance[playerid] * attempt_steal_chance[playerid])
                inning_outs += steal_outs
                player_outs += steal_outs
                if inning_outs >= outs:
                    inning_outs = 0.0                    
                    current_innings += 1
                    innings_since_lineup_start += 1
                    if not runtime_solution:
                        if playerid in loop_checker:       
                            if not last_pass:
                                if (str(batter_atbats - atbats_in_inning) in loop_checker[playerid]) and (loop_checker[playerid][str(batter_atbats - atbats_in_inning)][2] == 2):                                
                                    #this means that we have hit a loop point; our inning ended with the same player and had the same number of atbats
                                    loop_encountered = True                                 
                                    inning_score = 0.0
                                    runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
                                    runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
                                    break
                        else:
                            loop_checker[playerid] = {}
                        loop_checker[playerid][str(batter_atbats - atbats_in_inning)] = [team_score, current_innings, 2]
                    inning_score += player_score
                    atbats_in_inning = batter_atbats
                    team_score += inning_score                    
                    inning_score = 0.0
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
                        inning_outs += (player_outs * 0.02)
                    if inning_outs >= outs:
                        inning_outs = 0.0                        
                        current_innings += 1
                        innings_since_lineup_start += 1
                        if not runtime_solution:
                            if playerid in loop_checker:         
                                if not last_pass:
                                    if (str(batter_atbats - atbats_in_inning) in loop_checker[playerid]) and (loop_checker[playerid][str(batter_atbats - atbats_in_inning)][2] == 3):
                                        #this means that we have hit a loop point; our inning ended with the same player and had the same number of atbats to get there
                                        loop_encountered = True             
                                        inning_score = 0.0
                                        runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
                                        runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
                                        break
                            else:
                                loop_checker[playerid] = {}
                            loop_checker[playerid][str(batter_atbats - atbats_in_inning)] = [team_score, current_innings, 3]
                        inning_score += player_score
                        atbats_in_inning = batter_atbats
                        team_score += inning_score                
                        inning_score = 0.0
                        runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
                        runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
                        if current_innings >= total_innings:                
                            break
                    else:
                        inning_score += player_score
            playerAttrs.clear()                

        if (current_innings < total_innings):        
            if loop_encountered and not runtime_solution:
                loop_encountered, last_pass = False, True
                #print("We hit this new loop condition, sweet")
                lineup_score = team_score - loop_checker[playerid][str(batter_atbats - atbats_in_inning)][0]
                #print("{} innings before loop started, current innings {}".format(loop_checker[playerid][str(batter_atbats - atbats_in_inning)][1], current_innings))
                innings_in_loop = current_innings - loop_checker[playerid][str(batter_atbats - atbats_in_inning)][1]
                #we will have not added the most-recent inning, but we know we get a loop of innings from there and can replicate that loop N times and be at the same state
                #as the inning where we detected the start of a new loop is our current inning, we need to make sure that gets included in our replicated loop count
                current_innings -= 1
                full_lineup_count = math.floor((total_innings - current_innings) / innings_in_loop)                
                #print("Iterating through {} replicates of the loop of {} innings, current innings {}".format(full_lineup_count, innings_in_loop, current_innings))
                atbats_in_inning = batter_atbats
                team_score += lineup_score * full_lineup_count
                current_innings += innings_in_loop * full_lineup_count
                #print("Current innings now {}, out of total {}".format(current_innings, total_innings))            
            elif ((inning_outs - starting_lineup_inning_outs) < 1) and (innings_since_lineup_start == 0):
                #this means we have gone through the entire lineup and not even gotten one out
                #most likely this will continue, so we are just going to macro score these cases to save time
                #first, we need to determine how many innings remain
                remaining_innings = total_innings - current_innings
                #next, we need to determine how many passes through the lineup it will take at our current rate to complete the remaining innings
                remaining_outs = ((remaining_innings * 3) - inning_outs)
                #we need to have a fail case for accumulating ZERO outs in a lineup pass; a truly absurd number
                if (inning_outs - starting_lineup_inning_outs) == 0:
                    lineup_passes = remaining_outs / 0.0001
                else:
                    lineup_passes = remaining_outs / (inning_outs - starting_lineup_inning_outs)
                #then, we need to take the amount of score we have accumulated in our pass through the lineup and multiply it by our lineup passes, including the pass we just did in our total
                lineup_score = (inning_score - starting_lineup_inning_score) * (lineup_passes + 1)
                #increase team score by this amount
                team_score += lineup_score
                #finish scoring for the team
                current_innings = total_innings
                #only update the hits homers and steals if we are generating runtime output
                if runtime_solution:
                    for playerid in sorted_batters:
                        hits[playerid] *= lineup_passes + 1
                        homers[playerid] *= lineup_passes + 1
                        stolen_bases[playerid] *= lineup_passes + 1
            else:
                if ((runners_on_first + runners_on_second + runners_on_third + runners_on_fourth) == 0.0) and ((runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth) == 0.0):
                    #this means we're going to replicate this result a number of times as we completed the lineup before accumulating whatever remains                    
                    last_pass = True
                    remaining_innings = total_innings - current_innings
                    total_iterations = math.floor(remaining_innings / current_innings)
                    print("Discovered a replicate point at inning {}, {} innings remain, {} replicates".format(current_innings, remaining_innings, total_iterations))
                    team_score *= total_iterations
                    current_innings += current_innings * total_iterations
                    print("Re-entering the loop at inning {}".format(current_innings))
                    if runtime_solution:
                        for playerid in sorted_batters:
                            hits[playerid] *= total_iterations
                            homers[playerid] *= total_iterations
                            stolen_bases[playerid] *= total_iterations
    
    if ((weather == sun_weather) or (weather == bh_weather)) and runtime_solution:        
        adjusted_score = team_score - (math.floor(team_score / 1000.0) * 1000.0)
        #print("Adjusting team score for {} weather: team score = {}, adjusted score = {}".format("Sun 2" if weather == sun_weather else "Black Hole", team_score, adjusted_score))
        team_score = adjusted_score    

    if runtime_solution:
        return team_score, stolen_bases, homers, hits

    return team_score

def calc_runners_on(runners_on_base, runner_advance_base, runners_on_base_minus_one, runner_advance_base_minus_one, runners_on_base_minus_two, runner_advance_base_minus_two, runners_on_base_minus_three, runner_advance_base_minus_three, single_chance, double_chance, triple_chance, homerun_chance, sacrifice_chance, caught_out_chance, walk_chance, walk_mod):

    runners_on = max(runners_on_base + (runner_advance_base_minus_one * runners_on_base_minus_one * caught_out_chance) + ((runners_on_base_minus_one - runners_on_base) * single_chance) + ((runners_on_base_minus_one - runners_on_base) * sacrifice_chance) + ((runners_on_base_minus_two - runners_on_base) * double_chance) + ((runners_on_base_minus_three - runners_on_base) * triple_chance) - (runners_on_base * homerun_chance) + ((runners_on_base_minus_one - runners_on_base) * walk_chance * (1.0 - walk_mod)) + ((runners_on_base_minus_two + runners_on_base_minus_three - runners_on_base) * walk_chance * walk_mod), 0.0)
    
    runner_advance = max(runner_advance_base + (runner_advance_base_minus_one * runners_on_base_minus_one * caught_out_chance * runner_advance_base_minus_one) + (((runners_on_base_minus_one * runner_advance_base_minus_one) - (runners_on_base * runner_advance_base)) * single_chance) + (((runners_on_base_minus_one * runner_advance_base_minus_one) - (runners_on_base * runner_advance_base)) * sacrifice_chance) + (((runners_on_base_minus_two * runner_advance_base_minus_two) - (runners_on_base * runner_advance_base)) * double_chance) + (((runners_on_base_minus_three * runner_advance_base_minus_three) - (runner_advance_base * runners_on_base)) * triple_chance) - (runners_on_base * runner_advance_base * homerun_chance) + (((runners_on_base_minus_one * runner_advance_base_minus_one) - (runners_on_base * runner_advance_base)) * walk_chance * (1.0 - walk_mod)) + (((runners_on_base_minus_two * runner_advance_base_minus_two) + (runners_on_base_minus_three * runner_advance_base_minus_three) - (runners_on_base * runner_advance_base)) * walk_chance * walk_mod), 0.0)
    
    return runners_on, runner_advance

def get_blood_mod(mods, bloodMod, opp_same, player_stat_data, stlatset):                         
    playerMods = collections.defaultdict(lambda: [])    
    for name in stlatset:
        if name in mods[bloodMod][opp_same]:
            stlatterm = mods[bloodMod][opp_same][name]            
            multiplier = calc_player_stlatmod(name, player_stat_data, stlatterm)
            if multiplier is not None:
                playerMods[name].append(multiplier)    
    return playerMods

def calc_a_blood(terms, mods, awayAttrs, homeAttrs, weather, away_home, playerMods, parkMods, player_stat_data, stlatset, adjusted_stat_data=None, overperform_aa=0.0, overperform_aaa=0.0):
    blood_count = 12.0
    a_blood_factor = 1.0 / blood_count
    overperform_pct = (overperform_aa * a_blood_factor) + (overperform_aaa * a_blood_factor)
    
    if stlatset == "defense":                
        base_omniscience, base_watchfulness, base_chasiness, base_anticapitalism, base_tenaciousness = calc_defense(terms, playerMods, parkMods, player_stat_data, adjusted_stat_data, None, overperform_pct)
        player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness = base_omniscience, base_watchfulness, base_chasiness, base_anticapitalism, base_tenaciousness
        for blood in BLOOD_LIST_DEFENSE:            
            if (((away_home == "away") and ("A" in awayAttrs)) or ((away_home == "home") and ("A" in homeAttrs))) and ("same" in mods[blood]):
                opp_same = "same"                
            elif (((away_home == "away") and ("A" in homeAttrs)) or ((away_home == "home") and ("A" in awayAttrs))) and ("opp" in mods[blood]):
                opp_same = "opp"
            else:
                continue            
            bloodMods = get_blood_mod(mods, blood, opp_same, player_stat_data, helpers.DEFENSE_STLATS)            
            blood_omniscience, blood_watchfulness, blood_chasiness, blood_anticapitalism, blood_tenaciousness = calc_defense(terms, playerMods, parkMods, player_stat_data, adjusted_stat_data, bloodMods, overperform_pct)
            player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness = (player_omniscience + ((blood_omniscience - base_omniscience) * a_blood_factor)),  (player_watchfulness + ((blood_watchfulness - base_watchfulness) * a_blood_factor)), (player_chasiness + ((blood_chasiness - base_chasiness) * a_blood_factor)), (player_anticapitalism + ((blood_anticapitalism - base_anticapitalism) * a_blood_factor)), (player_tenaciousness + ((blood_tenaciousness - base_tenaciousness) * a_blood_factor))
            
        return player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness

    elif stlatset == "pitching":
        base_unthwackability, base_ruthlessness, base_overpowerment, base_shakespearianism, base_coldness = calc_pitching(terms, playerMods, parkMods, player_stat_data, None)
        player_unthwackability, player_ruthlessness, player_overpowerment, player_shakespearianism, player_coldness = base_unthwackability, base_ruthlessness, base_overpowerment, base_shakespearianism, base_coldness
        for blood in BLOOD_LIST_PITCHING:            
            if (((away_home == "away") and ("A" in awayAttrs)) or ((away_home == "home") and ("A" in homeAttrs))) and ("same" in mods[blood]):
                opp_same = "same"                
            elif (((away_home == "away") and ("A" in homeAttrs)) or ((away_home == "home") and ("A" in awayAttrs))) and ("opp" in mods[blood]):
                opp_same = "opp"
            else:
                continue                
            bloodMods = get_blood_mod(mods, blood, opp_same, player_stat_data, helpers.PITCHING_STLATS)            
            blood_unthwackability, blood_ruthlessness, blood_overpowerment, blood_shakespearianism, blood_coldness = calc_pitching(terms, playerMods, parkMods, player_stat_data, bloodMods)
            player_unthwackability, player_ruthlessness, player_overpowerment, player_shakespearianism, player_coldness = (player_unthwackability + ((blood_unthwackability - base_unthwackability) * a_blood_factor)),  (player_ruthlessness + ((blood_ruthlessness - base_ruthlessness) * a_blood_factor)), (player_overpowerment + ((blood_overpowerment - base_overpowerment) * a_blood_factor)), (player_shakespearianism + ((blood_shakespearianism - base_shakespearianism) * a_blood_factor)), (player_coldness + ((blood_coldness - base_coldness) * a_blood_factor))            
        return player_unthwackability, player_ruthlessness, player_overpowerment, player_shakespearianism, player_coldness

    else:        
        base_patheticism, base_tragicness, base_thwackability, base_divinity, base_moxie, base_musclitude, base_martyrdom = calc_batting(terms, playerMods, parkMods, player_stat_data, adjusted_stat_data, None, overperform_pct)
        base_laserlikeness, base_basethirst, base_continuation, base_groundfriction, base_indulgence = calc_running(terms, playerMods, parkMods, player_stat_data, adjusted_stat_data, None, overperform_pct)
        player_patheticism, player_tragicness, player_thwackability, player_divinity, player_moxie, player_musclitude, player_martyrdom = base_patheticism, base_tragicness, base_thwackability, base_divinity, base_moxie, base_musclitude, base_martyrdom
        player_laserlikeness, player_basethirst, player_continuation, player_groundfriction, player_indulgence = base_laserlikeness, base_basethirst, base_continuation, base_groundfriction, base_indulgence
        for blood in BLOOD_LIST_OFFENSE:            
            if (((away_home == "away") and ("A" in awayAttrs)) or ((away_home == "home") and ("A" in homeAttrs))) and ("same" in mods[blood]):
                opp_same = "same"                
            elif (((away_home == "away") and ("A" in homeAttrs)) or ((away_home == "home") and ("A" in awayAttrs))) and ("opp" in mods[blood]):
                opp_same = "opp"
            else:
                continue                
            bloodMods = get_blood_mod(mods, blood, opp_same, player_stat_data, helpers.OFFENSE_STLATS)
            blood_patheticism, blood_tragicness, blood_thwackability, blood_divinity, blood_moxie, blood_musclitude, blood_martyrdom = calc_batting(terms, playerMods, parkMods, player_stat_data, adjusted_stat_data, bloodMods, overperform_pct)
            blood_laserlikeness, blood_basethirst, blood_continuation, blood_groundfriction, blood_indulgence = calc_running(terms, playerMods, parkMods, player_stat_data, adjusted_stat_data, bloodMods, overperform_pct)
            player_patheticism, player_tragicness, player_thwackability, player_divinity, player_moxie, player_musclitude, player_martyrdom = (player_patheticism + ((blood_patheticism - base_patheticism) * a_blood_factor)), (player_tragicness + ((blood_tragicness - base_tragicness) * a_blood_factor)), (player_thwackability + ((blood_thwackability - base_thwackability) * a_blood_factor)),  (player_divinity + ((blood_divinity - base_divinity) * a_blood_factor)), (player_moxie + ((blood_moxie - base_moxie) * a_blood_factor)), (player_musclitude + ((blood_musclitude - base_musclitude) * a_blood_factor)), (player_martyrdom + ((blood_martyrdom - base_martyrdom) * a_blood_factor))
            player_laserlikeness, player_basethirst, player_continuation, player_groundfriction, player_indulgence = (player_laserlikeness + ((blood_laserlikeness - base_laserlikeness) * a_blood_factor)),  (player_basethirst + ((blood_basethirst - base_basethirst) * a_blood_factor)), (player_continuation + ((blood_continuation - base_continuation) * a_blood_factor)), (player_groundfriction + ((blood_groundfriction - base_groundfriction) * a_blood_factor)), (player_indulgence + ((blood_indulgence - base_indulgence) * a_blood_factor))            
        return player_patheticism, player_tragicness, player_thwackability, player_divinity, player_moxie, player_musclitude, player_martyrdom, player_laserlikeness, player_basethirst, player_continuation, player_groundfriction, player_indulgence

def calc_player_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, player_stat_data, adjusted_stat_data, overperform_pct=0):        
    playerMods = get_player_mods(mods, awayAttrs, homeAttrs, weather, away_home, player_stat_data)        
    calced_stlats = {}        
    player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness = calc_defense(terms, playerMods, teamMods, player_stat_data, adjusted_stat_data, None, overperform_pct)
    if not player_stat_data["shelled"]:        
        calced_stlats["patheticism"], calced_stlats["tragicness"], calced_stlats["thwackability"], calced_stlats["divinity"], calced_stlats["moxie"], calced_stlats["musclitude"], calced_stlats["martyrdom"] = calc_batting(terms, playerMods, teamMods, player_stat_data, adjusted_stat_data, None, overperform_pct)
        calced_stlats["laserlikeness"], calced_stlats["basethirst"], calced_stlats["continuation"], calced_stlats["groundfriction"], calced_stlats["indulgence"] = calc_running(terms, playerMods, teamMods, player_stat_data, adjusted_stat_data, None, overperform_pct)    
        return calced_stlats, player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness
    return player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness

def calc_ablood_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, player_stat_data, adjusted_stat_data, average_aa_impact, average_aaa_impact):        
    playerMods = get_player_mods(mods, awayAttrs, homeAttrs, weather, away_home, player_stat_data)
    calced_stlats = {}
    player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness = calc_a_blood(terms, mods, awayAttrs, homeAttrs, weather, away_home, playerMods, teamMods, player_stat_data, "defense", adjusted_stat_data, average_aa_impact, average_aaa_impact)        
    if not player_stat_data["shelled"]:        
        calced_stlats["patheticism"], calced_stlats["tragicness"], calced_stlats["thwackability"], calced_stlats["divinity"], calced_stlats["moxie"], calced_stlats["musclitude"], calced_stlats["martyrdom"], calced_stlats["laserlikeness"], calced_stlats["basethirst"], calced_stlats["continuation"], calced_stlats["groundfriction"], calced_stlats["indulgence"] = calc_a_blood(terms, mods, awayAttrs, homeAttrs, weather, away_home, playerMods, teamMods, player_stat_data, "offense", adjusted_stat_data, average_aa_impact, average_aaa_impact)                     
        return calced_stlats, player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness
    return player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness

def calc_pitcher_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, player_stat_data):       
    playerMods = get_player_mods(mods, awayAttrs, homeAttrs, weather, away_home, player_stat_data)    
    calced_stlats = {}    
    if ("A" in awayAttrs) or ("A" in homeAttrs):
        calced_stlats["unthwackability"], calced_stlats["ruthlessness"], calced_stlats["overpowerment"], calced_stlats["shakespearianism"], calced_stlats["coldness"] = calc_a_blood(terms, mods, awayAttrs, homeAttrs, weather, away_home, playerMods, teamMods, player_stat_data, "pitching")
    else:
        calced_stlats["unthwackability"], calced_stlats["ruthlessness"], calced_stlats["overpowerment"], calced_stlats["shakespearianism"], calced_stlats["coldness"] = calc_pitching(terms, playerMods, teamMods, player_stat_data)
    return calced_stlats

def calc_team_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, away_home, team_stat_data, pitcher_stat_data, adjusted_stat_data, blood_impact=None, second_blood_impact=None):
    team_stlats, team_defense, batter_order = {}, {}, {}
    team_defense["omniscience"], team_defense["watchfulness"], team_defense["chasiness"], team_defense["anticapitalism"], team_defense["tenaciousness"] = 0.0, 0.0, 0.0, 0.0, 0.0
    lineup = 0
    
    for playerid in team_stat_data:        
        if (blood_impact and not second_blood_impact) or not blood_impact:
            overperform_pct = 0
            if blood_impact and not second_blood_impact:
                overperform_pct = blood_impact[playerid]        
            if not team_stat_data[playerid]["shelled"]:
                batter_order[playerid] = team_stat_data[playerid]["turnOrder"]
                team_stlats[playerid] = {}                                    
                team_stlats[playerid], player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness = calc_player_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, away_home, team_stat_data[playerid], adjusted_stat_data[away_home][playerid], overperform_pct)                  
            else:
                player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness = calc_player_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, away_home, team_stat_data[playerid], adjusted_stat_data[away_home][playerid], overperform_pct)        
        else:
            average_aa_impact, average_aaa_impact = blood_impact[playerid], second_blood_impact[playerid]
            if not team_stat_data[playerid]["shelled"]:
                batter_order[playerid] = team_stat_data[playerid]["turnOrder"]
                team_stlats[playerid] = {}
                team_stlats[playerid], player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness = calc_ablood_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, away_home, team_stat_data[playerid], adjusted_stat_data[away_home][playerid], average_aa_impact, average_aaa_impact)                  
            else:
                player_omniscience, player_watchfulness, player_chasiness, player_anticapitalism, player_tenaciousness = calc_ablood_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, away_home, team_stat_data[playerid], adjusted_stat_data[away_home][playerid], average_aa_impact, average_aaa_impact)
        lineup += 1
        team_defense["omniscience"] += player_omniscience
        team_defense["watchfulness"] += player_watchfulness
        team_defense["chasiness"] += player_chasiness
        team_defense["anticapitalism"] += player_anticapitalism
        team_defense["tenaciousness"] += player_tenaciousness
    sorted_batters = dict(sorted(batter_order.items(), key=lambda item: item[1]))
    team_defense["omniscience"] = team_defense["omniscience"] / lineup
    team_defense["watchfulness"] = team_defense["watchfulness"] / lineup
    team_defense["chasiness"] = team_defense["chasiness"] / lineup
    team_defense["anticapitalism"] = team_defense["anticapitalism"] / lineup
    team_defense["tenaciousness"] = team_defense["tenaciousness"] / lineup    
    pitcherStlats = calc_pitcher_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, away_home, pitcher_stat_data)

    return team_stlats, team_defense, sorted_batters, pitcherStlats

def blood_impact_calc(terms, mods, weather, away_home, teamMods, calc_team_data, calc_opp_data, calc_pitcher_data, team_stat_data, opp_stat_data, opp_pitcher_data, team_pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjusted_stat_data, adjustments, innings=9):
    if away_home == "away":
        awayAttrs, homeAttrs = teamAttrs, oppAttrs
    else:
        awayAttrs, homeAttrs = oppAttrs, teamAttrs
    if "AA" in teamAttrs:
        average_aa_impact = calc_probs_from_stats(mods, weather, calc_team_data, calc_opp_data, calc_pitcher_data, team_stat_data, opp_stat_data, opp_pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, "aa", innings)
        team_stlats, team_defense, batter_order, pitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data, team_pitcher_data, adjusted_stat_data, average_aa_impact)
    if "AAA" in teamAttrs:
        average_aaa_impact = calc_probs_from_stats(mods, weather, calc_team_data, calc_opp_data, calc_pitcher_data, team_stat_data, opp_stat_data, opp_pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, "aaa", innings)
        team_stlats, team_defense, batter_order, pitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data, team_pitcher_data, adjusted_stat_data, average_aaa_impact)
    if "A" in teamAttrs:
        average_aa_impact, average_aaa_impact = calc_probs_from_stats(mods, weather, calc_team_data, calc_opp_data, calc_pitcher_data, team_stat_data, opp_stat_data, opp_pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, "a", innings)
        team_stlats, team_defense, batter_order, pitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data, team_pitcher_data, adjusted_stat_data, average_aa_impact, average_aaa_impact)
    return team_stlats, team_defense, batter_order, pitcherStlats
    
def get_mofo_playerbased(mods, awayPitcher, homePitcher, awayTeam, homeTeam, awayAttrs, homeAttrs, weather, team_stat_data, pitcher_stat_data, terms, awayMods, homeMods, adjusted_stat_data, adjustments, skip_mods=False, runtime_solution=False):          
    polarity_plus, polarity_minus = helpers.get_weather_idx("Polarity +"), helpers.get_weather_idx("Polarity -")    
    if weather == polarity_plus or weather == polarity_minus:
        return .5, .5    

    away_team_stlats, away_team_defense, away_batter_order, awayPitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, "away", team_stat_data[awayTeam], pitcher_stat_data[awayPitcher], adjusted_stat_data)
    home_team_stlats, home_team_defense, home_batter_order, homePitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, homeMods, weather, "home", team_stat_data[homeTeam], pitcher_stat_data[homePitcher], adjusted_stat_data)

    if "AAA" in awayAttrs or "AA" in awayAttrs or "A" in awayAttrs:
        away_team_stlats, away_team_defense, away_batter_order, awayPitcherStlats = blood_impact_calc(terms, mods, weather, "away", awayMods, away_team_stlats, home_team_defense, homePitcherStlats, team_stat_data[awayTeam], team_stat_data[homeTeam], pitcher_stat_data[homePitcher], pitcher_stat_data[awayPitcher], awayAttrs, homeAttrs, away_batter_order, adjusted_stat_data, adjustments)
    if "AAA" in homeAttrs or "AA" in homeAttrs or "A" in homeAttrs:
        home_team_stlats, home_team_defense, home_batter_order, homePitcherStlats = blood_impact_calc(terms, mods, weather, "home", homeMods, home_team_stlats, away_team_defense, awayPitcherStlats, team_stat_data[homeTeam], team_stat_data[awayTeam], pitcher_stat_data[awayPitcher], pitcher_stat_data[homePitcher], homeAttrs, awayAttrs, home_batter_order, adjusted_stat_data, adjustments)

    if runtime_solution:
        away_score, away_stolen_bases, away_homers, away_hits = calc_team_score(mods, weather, away_team_stlats, home_team_defense, homePitcherStlats, team_stat_data[awayTeam], team_stat_data[homeTeam], pitcher_stat_data[homePitcher], awayAttrs, homeAttrs, away_batter_order, adjustments, False, runtime_solution)
        home_score, home_stolen_bases, home_homers, home_hits = calc_team_score(mods, weather, home_team_stlats, away_team_defense, awayPitcherStlats, team_stat_data[homeTeam], team_stat_data[awayTeam], pitcher_stat_data[awayPitcher], homeAttrs, awayAttrs, home_batter_order, adjustments, False, runtime_solution)
    else:    
        away_score = calc_team_score(mods, weather, away_team_stlats, home_team_defense, homePitcherStlats, team_stat_data[awayTeam], team_stat_data[homeTeam], pitcher_stat_data[homePitcher], awayAttrs, homeAttrs, away_batter_order, adjustments)
        home_score = calc_team_score(mods, weather, home_team_stlats, away_team_defense, awayPitcherStlats, team_stat_data[homeTeam], team_stat_data[awayTeam], pitcher_stat_data[awayPitcher], homeAttrs, awayAttrs, home_batter_order, adjustments)   

    numerator = away_score - home_score
    denominator = abs(away_score + home_score)
    if not denominator:
        return .5, .5    
    away_formula = numerator / denominator        
    away_odds = log_transform(away_formula, 100.0)
    if runtime_solution:
        return away_odds, 1.0 - away_odds, away_hits, home_hits, away_homers, home_homers, away_stolen_bases, home_stolen_bases
    return away_odds, 1.0 - away_odds

def get_player_mods(mods, awayAttrs, homeAttrs, weather, away_home, player_stat_data):            
    lowerAwayAttrs = [attr.lower() for attr in awayAttrs]
    lowerHomeAttrs = [attr.lower() for attr in homeAttrs]            
    playerAttrs = [attr.lower() for attr in player_stat_data["attrs"].split(";")]       
    allAttrs_lol = [lowerAwayAttrs, lowerHomeAttrs, playerAttrs]
    allAttrs_set = set().union(*allAttrs_lol)
    modAttrs_set = set(mods.keys())
    allModAttrs_set = allAttrs_set.intersection(modAttrs_set) - MODS_CALCED_DIFFERENTLY
    allAttrs = list(allAttrs_set)   
    modAttrs = list(allModAttrs_set)    
    playerMods = collections.defaultdict(lambda: [])
    #applied_mods = []
    bird_weather = helpers.get_weather_idx("Birds")    
    flood_weather = helpers.get_weather_idx("Flooding")       

    for attr in modAttrs:        
        if attr == "affinity_for_crows" and weather != bird_weather:
            continue
        if attr == "high_pressure" and weather != flood_weather:
            continue    
        if away_home == "home" and attr == "traveling":
            continue
        if attr in mods:            
            if (away_home == "home" and attr in lowerHomeAttrs) or (away_home == "away" and attr in lowerAwayAttrs) or (attr in playerAttrs):
                for name, stlatterm in mods[attr]["same"].items():                
                    multiplier = calc_player_stlatmod(name, player_stat_data, stlatterm)
                    if multiplier is not None:
                        playerMods[name].append(multiplier)                        
            if (away_home == "away" and attr in lowerHomeAttrs) or (away_home == "home" and attr in lowerAwayAttrs):
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
                if ballparkstlat != "hype":
                    normalized_value = stlatterm.calc(value) - stlatterm.calc(0.5)
                else:
                    normalized_value = stlatterm.calc(value) - stlatterm.calc(0.0)
                base_multiplier = log_transform(normalized_value, 100.0)
                #forcing harmonic mean with quicker process time?                
                multiplier = 1.0 / (2.0 * base_multiplier)
                if ballparkstlat != "hype":                                                    
                    awayMods[playerstlat].append(multiplier)
                    homeMods[playerstlat].append(multiplier)
                else:                                        
                    homeMods[playerstlat].append(multiplier)
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
