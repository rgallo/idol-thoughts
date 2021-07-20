from __future__ import division
from __future__ import print_function

import collections
import copy
import statistics
from scipy.stats import hmean

import helpers
import math
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
            multiplier *= statistics.harmonic_mean(modterms)                  
        total += term.calc(val) * multiplier
    return total

def calc_player(terms, stlatname, stlatvalue, mods, parkmods, bloodmods, skip_mods=False):    
    term = terms[stlatname]            
    multiplier, numerator, denominator = 1.0, 0.0, 0.0
    numerator
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
        if denominator > 0:
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
    base_multiplier = stlatterm.calc(1.0)
    #base_multiplier = log_transform(normalized_value, 100.0)    
    #forcing harmonic mean with quicker process time?
    multiplier = 1.0 / (2.0 * base_multiplier)
    return multiplier

def log_transform(value, base):
    try:
        transformed_value = (1.0 / (1.0 + (base ** (-1.0 * value))))
    except OverflowError:
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

def calc_probs_from_stats(mods, weather, team_stat_data, opp_stat_data, pitcher_stat_data, team_data, opp_data, pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, blood_calc=None):
    battingAttrs = [attr.lower() for attr in teamAttrs]
    opponentAttrs = [attr.lower() for attr in oppAttrs]
    pitcherAttrs = [attr.lower() for attr in pitcher_data["attrs"].split(";")]    
    strike_out_chance, caught_out_chance, base_steal_score, walk_score, hit_modifier, sacrifice_chance, runner_advance_points, homerun_multipliers, caught_steal_outs = {}, {}, {}, {}, {}, {}, {}, {}, {}
    single_chance, double_chance, triple_chance, homerun_chance, score_multiplier = {}, {}, {}, {}, {}

    blood_count = 12.0
    a_blood_multiplier = 1.0 / blood_count    

    omniscience, watchfulness, chasiness, anticap, tenaciousness = opp_stat_data["omniscience"], opp_stat_data["watchfulness"], opp_stat_data["chasiness"], opp_stat_data["anticapitalism"], opp_stat_data["tenaciousness"]
    unthwackability, ruthlessness, overpowerment, shakespearianism, coldness = pitcher_stat_data["unthwackability"], pitcher_stat_data["ruthlessness"], pitcher_stat_data["overpowerment"], pitcher_stat_data["shakespearianism"], pitcher_stat_data["coldness"]    
        
    homer_multiplier = -1.0 if "UNDERHANDED" in pitcherAttrs else 1.0  
    hit_multiplier = 1.0
    score_mult_pitcher = 1.0
    if "magnify_2x" in pitcherAttrs:
        score_mult_pitcher *= 2.0
    if "magnify_3x" in pitcherAttrs:
        score_mult_pitcher *= 3.0
    if "magnify_4x" in pitcherAttrs:
        score_mult_pitcher *= 4.0
    if "magnify_5x" in pitcherAttrs:
        score_mult_pitcher *= 5.0
    strike_mod, walk_mod, steal_mod, score_mod = 1.0, 1.0, 1.0, 0.0
    if "fiery" in opponentAttrs:                
        strike_mod += mods["fiery"]["same"]["multiplier"].calc(1.0)    
    if "acidic" in opponentAttrs:                
        score_mod += mods["acidic"]["same"]["multiplier"].calc(1.0)
    if "electric" in battingAttrs:
        strike_mod -= mods["electric"]["same"]["multiplier"].calc(1.0)
    if "base_instincts" in battingAttrs:
        walk_mod += mods["base_instincts"]["same"]["multiplier"].calc(1.0)
    if "a" in opponentAttrs:
        strike_mod += mods["fiery"]["same"]["multiplier"].calc(1.0) * a_blood_multiplier
        score_mod += mods["acidic"]["same"]["multiplier"].calc(1.0) * a_blood_multiplier
    if "a" in battingAttrs:
        strike_mod -= mods["electric"]["same"]["multiplier"].calc(1.0) * a_blood_multiplier
        walk_mod += mods["base_instincts"]["same"]["multiplier"].calc(1.0) * a_blood_multiplier        
    if "blaserunning" in battingAttrs:
        steal_mod += 0.2

    strike_log = (ruthlessness - adjustments["ruth_strike"])
    strike_chance = log_transform(strike_log, 100.0)
    runners_on_base, playerAttrs = [], []
        
    for playerid in sorted_batters:                                                      
        playerAttrs = [attr.lower() for attr in team_data[playerid]["attrs"].split(";")]
        #attempt to make it such that 25 points is a base and 100 points is a run (since a base is 1/4 of a run normally)   
        base = 20.0 if (("extra_base" in battingAttrs) or ("extra_base" in playerAttrs)) else 25.0        
        homer_multiplier *= -1.0 if "SUBTRACTOR" in playerAttrs else 1.0
        homer_multiplier *= -1.0 if "UNDERACHIEVER" in playerAttrs else 1.0
        hit_multiplier *= -1.0 if "SUBTRACTOR" in playerAttrs else 1.0
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
        swing_strike_chance = (swing_correct_chance + ((1.0 / 3.0) if ("h20" in battingAttrs or "h20" in playerAttrs) else 0.0) + (strike_chance if ("0" in battingAttrs or "0" in playerAttrs) else 0.0)) * strike_chance     
        swing_ball_chance = (1.0 - swing_correct_chance) * (1.0 - strike_chance)        

        connect_log = (adjustments["path_connect"] - patheticism)
        connect_chance = log_transform(connect_log, 100.0) * swing_strike_chance
        
        base_hit_log = ((thwackability - unthwackability - omniscience) - (adjustments["thwack_base_hit"] - adjustments["unthwack_base_hit"] - adjustments["omni_base_hit"]))
        base_hit_chance = log_transform(base_hit_log, 100.0) * connect_chance              
        
        walk_chance = ((swing_correct_chance * (1.0 - strike_chance)) + (((1.0 - strike_chance) ** 4.0) if "flinch" in playerAttrs else 0.0)) * ((4.0 / 3.0) if "walk_in_the_park" in battingAttrs else 1.0)

        strike_looking_chance = (1.0 - swing_correct_chance) * strike_chance

        caught_out_log = ((omniscience - musclitude) - (adjustments["omni_caught_out"] - adjustments["muscl_caught_out"]))
        caught_out_chance[playerid] = log_transform(caught_out_log, 100.0) * connect_chance

        on_base_chance = min((base_hit_chance + walk_chance), 1.0)

        attempt_steal_log = ((basethirst + laserlikeness - watchfulness) - (adjustments["baset_attempt_steal"] + adjustments["laser_attempt_steal"] - adjustments["watch_attempt_steal"]))
        attempt_steal_chance = log_transform(attempt_steal_log, 100.0) * on_base_chance
        caught_steal_log = ((basethirst + laserlikeness - anticap - coldness) - (adjustments["baset_caught_steal"] + adjustments["laser_caught_steal"] - adjustments["anticap_caught_steal"] - adjustments["cold_caught_steal"]))
        caught_steal_outs[playerid] = log_transform(caught_steal_log, 100.0) * attempt_steal_chance
        
        base_steal_score[playerid] = (((base * attempt_steal_chance) + (base * (attempt_steal_chance ** 2)) + (base * (attempt_steal_chance ** 3))) * steal_mod) - (10.0 * score_mod)        
        walk_score[playerid] = base * walk_chance * walk_mod        
        strike_out_chance[playerid] = (max(swing_ball_chance + strike_looking_chance + (1.0 - connect_chance), 1.0) * strike_mod) * (1.0 - (walk_chance / 4.0) if ("o_no" in battingAttrs or "o_no" in playerAttrs) else 1.0) * (0.75 if (("extra_strike" in battingAttrs) or ("extra_strike" in playerAttrs)) else 1.0) * (1.5 if "flinch" in playerAttrs else 1.0)
        if "a" in battingAttrs:
            strike_out_chance[playerid] += ((strike_out_chance[playerid] * (1.0 - (walk_chance / 4.0))) - strike_out_chance[playerid]) * a_blood_multiplier

        #homeruns needs to care about how many other runners are on base for how valuable they are, with a floor of "1x"
        homerun_log = ((divinity - overpowerment) - (adjustments["div_homer"] - adjustments["overp_homer"]))
        homerun_chance = log_transform(homerun_log, 100.0) * base_hit_chance
        homerun_multipliers[playerid] = homerun_chance * homer_multiplier
        runners_on_base.append(min((base_hit_chance + walk_chance), 1.0))

        triple_log = ((musclitude + groundfriction + continuation - overpowerment - chasiness) - (adjustments["muscl_triple"] + adjustments["ground_triple"] + adjustments["cont_triple"] - adjustments["overp_triple"] - adjustments["chasi_triple"]))
        triple_prob = log_transform(triple_log, 100.0) * (1.0 - homerun_chance)
        triple_chance[playerid] = triple_prob * base_hit_chance        

        double_log = ((musclitude + continuation - overpowerment - chasiness) - (adjustments["muscl_double"] + adjustments["cont_double"] - adjustments["overp_double"] - adjustments["chasi_double"]))
        double_prob = log_transform(double_log, 100.0) * (1.0 - triple_prob) * (1.0 - homerun_chance)
        double_chance[playerid] = double_prob * base_hit_chance 

        single_prob = (1.0 - triple_prob) * (1.0 - double_prob) * (1.0 - homerun_chance)
        single_chance[playerid] = single_prob * base_hit_chance
        
        hit_modifier[playerid] = hit_multiplier          

        #runners advancing is tricky, since we have to do this based on runners being on base already, but use the batter's martyrdom for sacrifices
        sacrifice_log = martyrdom - adjustments["martyr_sacrifice"]
        sacrifice_chance[playerid] = log_transform(sacrifice_log, 100.0) * caught_out_chance[playerid]
        
        runner_advances_log = ((laserlikeness + indulgence - tragicness - shakespearianism - tenaciousness) - (adjustments["laser_runner_advances"] + adjustments["indulg_runner_advances"] - adjustments["trag_runner_advances"] - adjustments["shakes_runner_advances"] - adjustments["shakes_runner_advances"]))
        runner_advances_chance = log_transform(runner_advances_log, 100.0)
        runner_advance_points[playerid] = base * runner_advances_chance
        playerAttrs.clear()

    if blood_calc:
        max_x = (len(sorted_batters)) * 3
        if blood_calc == "aaa" or blood_calc == "a":
            average_aaa_blood_impact = {}
            for playerid in triple_chance:
                x = 0
                average_aaa_blood_impact[playerid] = 0.0
                while x < max_x:
                    average_aaa_blood_impact[playerid] += (triple_chance[playerid] * ((1.0 - triple_chance[playerid]) ** x)) * ((max_x - x) / max_x)
                    x += 1
        if blood_calc == "aa" or blood_calc == "a":
            average_aa_blood_impact = {}
            for playerid in double_chance:
                x = 0
                average_aa_blood_impact[playerid] = 0.0
                while x < max_x:
                    average_aa_blood_impact[playerid] += (double_chance[playerid] * ((1.0 - double_chance[playerid]) ** x)) * ((max_x - x) / max_x)
                    x += 1
        if blood_calc == "aaa":
            return average_aaa_blood_impact
        if blood_calc == "aa":
            return average_aa_blood_impact
        if blood_calc == "a":
            return average_aa_blood_impact, average_aaa_blood_impact

    return runners_on_base, runner_advance_points, caught_out_chance, sacrifice_chance, score_mod, hit_modifier, homerun_multipliers, score_multiplier, base_steal_score, walk_score, strike_out_chance, caught_steal_outs, triple_chance, double_chance, single_chance

def calc_team_score(mods, weather, team_stat_data, opp_stat_data, pitcher_stat_data, team_data, opp_data, pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, innings=9, outs=3):      
    battingAttrs = [attr.lower() for attr in teamAttrs]
    reverb_weather = helpers.get_weather_idx("Reverb")    
    runners_on_base, runner_advance_points, caught_out_chance, sacrifice_chance, score_mod, hit_modifier, homerun_multipliers, score_multiplier, base_steal_score, walk_score, strike_out_chance, caught_steal_outs, triple_chance, double_chance, single_chance = calc_probs_from_stats(mods, weather, team_stat_data, opp_stat_data, pitcher_stat_data, team_data, opp_data, pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments)    
    
    #run ten "games" to get a more-representative average
    total_outs = innings * outs * 10
    current_outs = 0.0
    team_score = 100.0 if "home_field" in battingAttrs else 0.0

    while current_outs < total_outs:        
        current_batter = 0
        previous_outs = current_outs
        for playerid in sorted_batters:            
            playerAttrs = [attr.lower() for attr in team_data[playerid]["attrs"].split(";")]
            base = 20.0 if (("extra_base" in battingAttrs) or ("extra_base" in playerAttrs)) else 25.0
            if len(runners_on_base) < 4:            
                average_runners_on_base = max(sum(runners_on_base), 0.0) / len(runners_on_base)     
            else:
                average_runners_on_base = max(sum(runners_on_base) - runners_on_base[current_batter], 0.0) / (len(runners_on_base) - 1)
            runners_advance_batter = max(sum(runner_advance_points.values()) - runner_advance_points[playerid], 0.0) * max(average_runners_on_base, 3.0)
            runners_advance_score = sacrifice_chance[playerid] * runners_advance_batter
            homerun_score = ((100.0 * (1.0 + max(average_runners_on_base, 3.0))) - (10.0 * score_mod)) * homerun_multipliers[playerid]
            triple_score = (((base * 3.0) * triple_chance[playerid] * (1.0 + max(average_runners_on_base, 3.0))) - (10.0 * score_mod)) * hit_modifier[playerid]
            double_score = (((base * 2.0) * double_chance[playerid] * (1.0 + max(average_runners_on_base, 3.0))) - (10.0 * score_mod)) * hit_modifier[playerid]
            single_score = (((base * 1.0) * single_chance[playerid] * (1.0 + max(average_runners_on_base, 3.0))) - (10.0 * score_mod)) * hit_modifier[playerid]                        
            player_score = ((runners_advance_score + homerun_score + triple_score + double_score + single_score) * score_multiplier[playerid]) + base_steal_score[playerid] + walk_score[playerid] 
            player_outs = strike_out_chance[playerid] + caught_out_chance[playerid] + caught_steal_outs[playerid]
            if ("reverberating" in playerAttrs) or ("repeating" in playerAttrs and weather == reverb_weather):
                player_score *= 1.02
                player_outs *= 1.02            
            team_score += player_score
            current_outs += player_outs
            if current_outs >= total_outs:
                break
            current_batter += 1
            playerAttrs.clear()
        
        if current_outs == previous_outs:
            #this means we did not accumulate any outs during an entire lineup run, so we need to be done and assume an absurd score
            team_score *= 100.0
            current_outs = total_outs
        elif current_outs < total_outs:
            #shortcut number of times through the lineup for loop to 2 maximum; each full time through will produce the same answer, after all
            lineup_score = team_score
            #we've been through it one time already, accumulating N outs, so we'll go through it another (total outs / N) - 1 times
            full_lineup_count = (math.floor(total_outs / current_outs)) - 1            
            team_score += lineup_score * full_lineup_count
            current_outs += current_outs * full_lineup_count

    return team_score

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

def blood_impact_calc(terms, mods, weather, away_home, teamMods, calc_team_data, calc_opp_data, calc_pitcher_data, team_stat_data, opp_stat_data, opp_pitcher_data, team_pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjusted_stat_data, adjustments):
    if away_home == "away":
        awayAttrs, homeAttrs = teamAttrs, oppAttrs
    else:
        awayAttrs, homeAttrs = oppAttrs, teamAttrs
    if "AA" in teamAttrs:
        average_aa_impact = calc_probs_from_stats(mods, weather, calc_team_data, calc_opp_data, calc_pitcher_data, team_stat_data, opp_stat_data, opp_pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, "aa")
    if "AAA" in teamAttrs:
        average_aaa_impact = calc_probs_from_stats(mods, weather, calc_team_data, calc_opp_data, calc_pitcher_data, team_stat_data, opp_stat_data, opp_pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, "aaa")
    if "A" in teamAttrs:
        average_aa_impact, average_aaa_impact = calc_probs_from_stats(mods, weather, calc_team_data, calc_opp_data, calc_pitcher_data, team_stat_data, opp_stat_data, opp_pitcher_data, teamAttrs, oppAttrs, sorted_batters, adjustments, "a")
    if "AA" in teamAttrs:
        team_stlats, team_defense, batter_order, pitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data, team_pitcher_data, adjusted_stat_data, average_aa_impact)
    if "AAA" in teamAttrs:
        team_stlats, team_defense, batter_order, pitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data, team_pitcher_data, adjusted_stat_data, average_aaa_impact)
    if "A" in teamAttrs:
        team_stlats, team_defense, batter_order, pitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data, team_pitcher_data, adjusted_stat_data, average_aa_impact, average_aaa_impact)
    return team_stlats, team_defense, batter_order, pitcherStlats
    
def get_mofo_playerbased(mods, awayPitcher, homePitcher, awayTeam, homeTeam, awayAttrs, homeAttrs, weather, team_stat_data, pitcher_stat_data, terms, awayMods, homeMods, adjusted_stat_data, adjustments, skip_mods=False):          
    polarity_plus, polarity_minus = helpers.get_weather_idx("Polarity +"), helpers.get_weather_idx("Polarity -")
    if weather == polarity_plus or weather == polarity_minus:
        return .5, .5    

    away_team_stlats, away_team_defense, away_batter_order, awayPitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, awayMods, weather, "away", team_stat_data[awayTeam], pitcher_stat_data[awayPitcher], adjusted_stat_data)
    home_team_stlats, home_team_defense, home_batter_order, homePitcherStlats = calc_team_stlats(terms, mods, awayAttrs, homeAttrs, homeMods, weather, "home", team_stat_data[homeTeam], pitcher_stat_data[homePitcher], adjusted_stat_data)

    if "AAA" in awayAttrs or "AA" in awayAttrs or "A" in awayAttrs:
        away_team_stlats, away_team_defense, away_batter_order, awayPitcherStlats = blood_impact_calc(terms, mods, weather, "away", awayMods, away_team_stlats, home_team_defense, homePitcherStlats, team_stat_data[awayTeam], team_stat_data[homeTeam], pitcher_stat_data[homePitcher], pitcher_stat_data[awayPitcher], awayAttrs, homeAttrs, away_batter_order, adjusted_stat_data, adjustments)
    if "AAA" in homeAttrs or "AA" in homeAttrs or "A" in homeAttrs:
        home_team_stlats, home_team_defense, home_batter_order, homePitcherStlats = blood_impact_calc(terms, mods, weather, "home", homeMods, home_team_stlats, away_team_defense, awayPitcherStlats, team_stat_data[homeTeam], team_stat_data[awayTeam], pitcher_stat_data[awayPitcher], pitcher_stat_data[homePitcher], homeAttrs, awayAttrs, home_batter_order, adjusted_stat_data, adjustments)
    
    away_score = calc_team_score(mods, weather, away_team_stlats, home_team_defense, homePitcherStlats, team_stat_data[awayTeam], team_stat_data[homeTeam], pitcher_stat_data[homePitcher], awayAttrs, homeAttrs, away_batter_order, adjustments, pitcher_stat_data[homePitcher]["innings"])
    home_score = calc_team_score(mods, weather, home_team_stlats, away_team_defense, awayPitcherStlats, team_stat_data[homeTeam], team_stat_data[awayTeam], pitcher_stat_data[awayPitcher], homeAttrs, awayAttrs, home_batter_order, adjustments, pitcher_stat_data[awayPitcher]["innings"])   

    numerator = away_score - home_score    
    denominator = abs(away_score + home_score)
    if not denominator:
        return .5, .5    
    away_formula = numerator / denominator        
    away_odds = log_transform(away_formula, 100.0)    
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
