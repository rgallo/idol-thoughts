from __future__ import division
from __future__ import print_function

import collections
import copy
import datetime
import time

import helpers
import math
import numpy as np
from numba import njit
from numba.typed import List
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

@njit(cache=True)
def calc_player(term, stlatvalue, hype):    
    multiplier = 1.0 * hype
    total = term.calc(stlatvalue) * multiplier
    return float(total)

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

@njit(cache=True)
def log_transform(value, base):                            
    denominator = (1.0 + (base ** (-1.0 * value)))        
    transformed_value = 1.0 / denominator
    return float(transformed_value)

@njit(cache=True)
def prob_adjust(prob, multiplier):   
    if prob == 1.0:
        return prob
    else:
        odds = prob / (1.0 - prob)
        new_odds = odds * (1.0 + multiplier)
        new_prob = new_odds / (1.0 + new_odds)
    return float(new_prob)

@njit(cache=True)
def calc_defense(terms, park_mods, player_stat_data, adjusted_stlats, overperform_pct=0.0):
    omniscience, watchfulness, chasiness, anticapitalism, tenaciousness = player_stat_data
    adjust_omniscience, adjust_watchfulness, adjust_chasiness, adjust_anticapitalism, adjust_tenaciousness = adjusted_stlats    
    if overperform_pct > 0.01:                
        omniscience += (adjust_omniscience - omniscience) * overperform_pct
        watchfulness += (adjust_watchfulness - watchfulness) * overperform_pct 
        chasiness += (adjust_chasiness - chasiness) * overperform_pct 
        anticapitalism += (adjust_anticapitalism - anticapitalism) * overperform_pct 
        tenaciousness += (adjust_tenaciousness - tenaciousness) * overperform_pct    
    player_omni_base_hit = calc_player(terms[0], omniscience, park_mods[0])
    player_watch_attempt_steal = calc_player(terms[1], watchfulness, park_mods[1])
    player_chasi_triple = calc_player(terms[2], chasiness, park_mods[2])
    player_chasi_double = calc_player(terms[3], chasiness, park_mods[3])
    player_anticap_base = calc_player(terms[4], anticapitalism, park_mods[4])
    player_anticap_home = calc_player(terms[5], anticapitalism, park_mods[5])
    player_tenacious_ra = calc_player(terms[6], tenaciousness, park_mods[6])        
    return (float(player_omni_base_hit), float(player_watch_attempt_steal), float(player_chasi_triple), float(player_chasi_double), float(player_anticap_base), float(player_anticap_home), float(player_tenacious_ra))

@njit(cache=True)
def calc_batting(terms, park_mods, player_stat_data, adjusted_stlats, overperform_pct=0.0):  
    patheticism, tragicness, thwackability, divinity, moxie, musclitude, martyrdom = player_stat_data
    adjust_patheticism, adjust_tragicness, adjust_thwackability, adjust_divinity, adjust_moxie, adjust_musclitude, adjust_martyrdom = adjusted_stlats    
    if overperform_pct > 0.01:                
        patheticism += (adjust_patheticism - patheticism) * overperform_pct
        tragicness += (adjust_tragicness - tragicness) * overperform_pct
        thwackability += (adjust_thwackability - thwackability) * overperform_pct
        divinity += (adjust_divinity - divinity) * overperform_pct 
        moxie += (adjust_moxie - moxie) * overperform_pct 
        musclitude += (adjust_musclitude - musclitude) * overperform_pct 
        martyrdom += (adjust_martyrdom - martyrdom) * overperform_pct        
    player_path_connect = calc_player(terms[0], patheticism, park_mods[0])
    player_trag_ra = calc_player(terms[1], tragicness, park_mods[1])
    player_thwack_base_hit = calc_player(terms[2], thwackability, park_mods[2])
    player_div_homer = calc_player(terms[3], divinity, park_mods[3])
    player_moxie_swing_correct = calc_player(terms[4], moxie, park_mods[4])
    player_muscl_foul_ball = calc_player(terms[5], musclitude, park_mods[5])
    player_muscl_triple = calc_player(terms[6], musclitude, park_mods[6])
    player_muscl_double = calc_player(terms[7], musclitude, park_mods[7])
    player_martyr_sacrifice = calc_player(terms[8], martyrdom, park_mods[8])    
    return List([float(player_path_connect), float(player_trag_ra), float(player_thwack_base_hit), float(player_div_homer), float(player_moxie_swing_correct), float(player_muscl_foul_ball), float(player_muscl_triple), float(player_muscl_double), float(player_martyr_sacrifice)])

@njit(cache=True)
def calc_running(terms, park_mods, player_stat_data, adjusted_stlats, overperform_pct=0.0):
    laserlikeness, baseThirst, continuation, groundFriction, indulgence = player_stat_data
    adjust_laserlikeness, adjust_baseThirst, adjust_continuation, adjust_groundFriction, adjust_indulgence = adjusted_stlats
    if overperform_pct > 0.01:                
        laserlikeness += (adjust_laserlikeness - laserlikeness) * overperform_pct
        baseThirst += (adjust_baseThirst - baseThirst) * overperform_pct 
        continuation += (adjust_continuation - continuation) * overperform_pct 
        groundFriction += (adjust_groundFriction - groundFriction) * overperform_pct 
        indulgence += (adjust_indulgence - indulgence) * overperform_pct
    player_laser_attempt_steal = calc_player(terms[0], laserlikeness, park_mods[0])
    player_laser_caught_steal_base = calc_player(terms[1], laserlikeness, park_mods[1])
    player_laser_caught_steal_home = calc_player(terms[2], laserlikeness, park_mods[2])
    player_laser_runner_advances = calc_player(terms[3], laserlikeness, park_mods[3])
    player_baset_attempt_steal = calc_player(terms[4], baseThirst, park_mods[4])
    player_baset_caught_steal_home = calc_player(terms[5], baseThirst, park_mods[5])
    player_cont_triple = calc_player(terms[6], continuation, park_mods[6])
    player_cont_double = calc_player(terms[7], continuation, park_mods[7])
    player_ground_triple = calc_player(terms[8], groundFriction, park_mods[8])
    player_indulg_runner_advances = calc_player(terms[9], indulgence, park_mods[9])     
    return List([float(player_laser_attempt_steal), float(player_laser_caught_steal_base), float(player_laser_caught_steal_home), float(player_laser_runner_advances), float(player_baset_attempt_steal), float(player_baset_caught_steal_home), float(player_cont_triple), float(player_cont_double), float(player_ground_triple), float(player_indulg_runner_advances)])

@njit(cache=True)
def calc_pitching(terms, park_mods, pitcher_stat_data):   
    unthwackability, ruthlessness, overpowerment, shakespearianism, coldness = pitcher_stat_data    
    player_unthwack_base_hit = calc_player(terms[0], unthwackability, park_mods[0])
    player_ruth_strike = calc_player(terms[1], ruthlessness, park_mods[1])
    player_overp_homer = calc_player(terms[2], overpowerment, park_mods[2])
    player_overp_triple = calc_player(terms[3], overpowerment, park_mods[3])
    player_overp_double = calc_player(terms[4], overpowerment, park_mods[4])
    player_shakes_runner_advances = calc_player(terms[5], shakespearianism, park_mods[5])    
    player_cold_clutch_factor = 1.0
    return (float(player_unthwack_base_hit), float(player_ruth_strike), float(player_overp_homer), float(player_overp_triple), float(player_overp_double), float(player_shakes_runner_advances), float(player_cold_clutch_factor))

@njit(cache=True)
def calc_strikeout_walked(strike_looking, strike_swinging, ball_chance, foul_ball_chance, strike_count, ball_count, base_hit_chance, caught_out_chance):        
    #strikeout, walked, base_hit, caught_out = 0.0, 0.0, 0.0, 0.0            
    strikes, max_balls = int(strike_count), int(ball_count)
    foul_ball_count = max(strikes - 1, 0)
    #need to compute all possible configurations per up to N pitches
    maximum_pitches = strikes + foul_ball_count + max_balls + 1    

    strikeout, walked, base_hit, caught_out = strikeout_numba(strikes, max_balls, maximum_pitches, strike_looking, strike_swinging, foul_ball_chance, foul_ball_count, base_hit_chance, caught_out_chance, ball_chance)
    #print("Probabilities: base hit = {:.2f}, caught_out = {:.2f}, strikeout = {:.2f}, walked = {:.2f}, sum = {:.2f}".format(base_hit, caught_out, strikeout, walked, base_hit + caught_out + strikeout + walked))
    return strikeout, walked, base_hit, caught_out

@njit(cache=True)
def strikeout_numba(strikes, max_balls, maximum_pitches, strike_looking, strike_swinging, foul_ball_chance, foul_ball_count, base_hit_chance, caught_out_chance, ball_chance):
    strikeout, walked, base_hit, caught_out = 0.0, 0.0, 0.0, 0.0
    for foul_balls in range(0, maximum_pitches):
        for balls in range(0, max_balls + 1):
            for thrown_strikes in range(0, strikes + 1):
                for strike_looking_count in range(0, thrown_strikes + 1):
                    if foul_balls + thrown_strikes >= strikes and balls < max_balls:
                        strikeout += (strike_looking ** strike_looking_count) * (strike_swinging ** (thrown_strikes - strike_looking_count)) * (foul_ball_chance ** foul_balls) * (ball_chance ** balls) * ((1.0 - base_hit_chance) ** (foul_balls + balls + thrown_strikes)) * ((1.0 - caught_out_chance) ** (foul_balls + balls + thrown_strikes))
                    if balls == max_balls and thrown_strikes < strikes:
                        walked += (ball_chance ** max_balls) * (strike_looking ** strike_looking_count) * (strike_swinging ** (thrown_strikes - strike_looking_count)) * (foul_ball_chance ** foul_balls) * ((1.0 - base_hit_chance) ** (foul_balls + balls + thrown_strikes)) * ((1.0 - caught_out_chance) ** (foul_balls + balls + thrown_strikes))
                    if thrown_strikes < strikes and balls < max_balls:
                        base_hit += base_hit_chance * ((1.0 - base_hit_chance) ** (foul_balls + balls + thrown_strikes)) * ((1.0 - caught_out_chance) ** (foul_balls + balls + thrown_strikes)) * (foul_ball_chance ** foul_balls) * (ball_chance ** balls) * (strike_looking ** strike_looking_count) * (strike_swinging ** (thrown_strikes - strike_looking_count))
                        caught_out += caught_out_chance * ((1.0 - base_hit_chance) ** (foul_balls + balls + thrown_strikes)) * ((1.0 - caught_out_chance) ** (foul_balls + balls + thrown_strikes)) * (foul_ball_chance ** foul_balls) * (ball_chance ** balls) * (strike_looking ** strike_looking_count) * (strike_swinging ** (thrown_strikes - strike_looking_count))        
    return strikeout, walked, base_hit, caught_out

@njit(cache=True)
def calc_probs_method(total_batters, sorted_playerAttrs, battingAttrs, blood_calc, score_mult_pitcher, pitcher_homer_multiplier, pitcher_hit_multiplier, pitching_values, defense_values, sorted_bat_values, sorted_run_values, adjustments, parkmods, log_transform_base, outs, strike_chance, strike_to_walk, walk_buff, walk_mod, walk_to_strike, strike_mod, a_blood_multiplier):
    steal_mod = List()
    score_multiplier = List()
    caught_out_chance = List()
    walk_chance = List()
    strike_out_chance = List()

    attempt_steal_chance = List()
    caught_steal_base_chance = List()
    caught_steal_home_chance = List()

    homerun_chance = List()
    homerun_multipliers = List()
    triple_chance = List()
    double_chance = List()
    single_chance = List()
    caught_steal_outs = List()
    on_base_chance = List()
    hit_modifier = List()

    sacrifice_chance = List()
    runner_advance_chance = List()
    average_on_first_position = List()
    average_on_second_position = List()
    average_on_third_position = List()

    (unthwack_base_hit, ruth_strike, overp_homer, overp_triple, overp_double, shakes_runner_advances, cold_clutch_factor) = pitching_values

    (omni_base_hit, watch_attempt_steal, chasi_triple, chasi_double, anticap_caught_steal_base, anticap_caught_steal_home, tenacious_runner_advances) = defense_values

    (moxie_swing_correct_adjustment, path_connect_adjustment, thwack_base_hit_adjustment, unthwack_base_hit_adjustment, omni_base_hit_adjustment, muscl_foul_ball_adjustment, baset_attempt_steal_adjustment, laser_attempt_steal_adjustment, watch_attempt_steal_adjustment, anticap_caught_steal_base_adjustment, laser_caught_steal_base_adjustment, anticap_caught_steal_home_adjustment, baset_caught_steal_home_adjustment, laser_caught_steal_home_adjustment, div_homer_adjustment, overp_homer_adjustment, muscl_triple_adjustment, ground_triple_adjustment, cont_triple_adjustment, overp_triple_adjustment, chasi_triple_adjustment, muscl_double_adjustment, cont_double_adjustment, overp_double_adjustment, chasi_double_adjustment, martyr_sacrifice_adjustment, laser_runner_advances_adjustment, indulg_runner_advances_adjustment, trag_runner_advances_adjustment, shakes_runner_advances_adjustment, tenacious_runner_advances_adjustment) = adjustments

    (plus_contact_minus_hardhit, plus_hit_minus_foul, plus_groundout_minus_hardhit, minus_doubleplay, minus_stealattempt, minus_stealsuccess, plus_hit_minus_homer, plus_hardhit, minus_homer, minus_hit) = parkmods         

    for playerid in range(0, len(sorted_bat_values)):            
        playerAttrs = sorted_playerAttrs[playerid]        
        homer_multiplier = pitcher_homer_multiplier
        hit_multiplier = pitcher_hit_multiplier
        homer_multiplier *= -1.0 if "subtractor" in playerAttrs else 1.0
        homer_multiplier *= -1.0 if "underachiever" in playerAttrs else 1.0
        hit_multiplier *= -1.0 if "subtractor" in playerAttrs else 1.0
        strike_count = 4.0 if (("extra_strike" in battingAttrs) or ("extra_strike" in playerAttrs)) else 3.0
        strike_count -= 1.0 if "flinch" in playerAttrs else 0.0
        ball_count = 3.0 if (("walk_in_the_park" in battingAttrs) or ("walk_in_the_park" in playerAttrs)) else 4.0            
        steal_mod.append(20.0 if ("blaserunning" in battingAttrs or "blaserunning" in playerAttrs) else 0.0)
        if "skipping" in playerAttrs:            
            average_strikes = (strike_count - 1.0) / 2.0
            average_balls = (ball_count - 1.0) / 2.0
            strike_count -= average_strikes            
            strike_count = max(strike_count, 1.0)
            ball_count -= average_balls
            ball_count = max(ball_count, 1.0)
        score_multiplier.append(score_mult_pitcher)
        if "magnify_2x" in playerAttrs:
            score_multiplier[playerid] *= 2.0
        if "magnify_3x" in playerAttrs:
            score_multiplier[playerid] *= 3.0
        if "magnify_4x" in playerAttrs:
            score_multiplier[playerid] *= 4.0
        if "magnify_5x" in playerAttrs:
            score_multiplier[playerid] *= 5.0
        path_connect, trag_runner_advances, thwack_base_hit, div_homer, moxie_swing_correct, muscl_foul_ball, muscl_triple, muscl_double, martyr_sacrifice = sorted_bat_values[playerid]
        laser_attempt_steal, laser_caught_steal_base, laser_caught_steal_home, laser_runner_advances, baset_attempt_steal, baset_caught_steal_home, cont_triple, cont_double, ground_triple, indulg_runner_advances = sorted_run_values[playerid]
        
        moxie_log = moxie_swing_correct - moxie_swing_correct_adjustment
        swing_correct_chance = log_transform(moxie_log, log_transform_base)        
        swing_strike_blood_factors = ((1.0 / outs) if ("h20" in battingAttrs or "h20" in playerAttrs) else 0.0) + ((strike_chance / (strike_count + ball_count)) if (("0" in battingAttrs or "0" in playerAttrs) and "skipping" not in playerAttrs) else 0.0)
        if "a" in battingAttrs and blood_calc != "a":
            swing_strike_blood_factors += ((1.0 / outs) * a_blood_multiplier) + (((strike_chance / (strike_count + ball_count)) * a_blood_multiplier) if "skipping" not in playerAttrs else 0.0)
        swing_strike_chance = (swing_correct_chance + swing_strike_blood_factors) * strike_chance        
        swing_ball_chance = ((1.0 - swing_correct_chance) * (1.0 - strike_chance)) - (((1.0 - strike_chance) ** ball_count) if "flinch" in playerAttrs else 0.0)

        connect_log = path_connect_adjustment - path_connect
        base_connect_prob = log_transform(connect_log, log_transform_base)                   
        base_connect_chance = prob_adjust(base_connect_prob, plus_contact_minus_hardhit)        
        connect_chance = max(base_connect_chance, 0.0) * max(swing_strike_chance, 0.0)

        base_hit_adjust = thwack_base_hit_adjustment - unthwack_base_hit_adjustment - omni_base_hit_adjustment
        base_hit_log = thwack_base_hit - unthwack_base_hit - omni_base_hit - base_hit_adjust
        base_hit = log_transform(base_hit_log, log_transform_base)
        base_hit_chance = base_hit * connect_chance                     

        strike_looking_chance = (1.0 - swing_correct_chance) * strike_chance
        strike_swinging_chance = (1.0 - connect_chance) + swing_ball_chance
        ball_chance = 1.0 - max(swing_ball_chance, 0.0)

        foul_ball_log = muscl_foul_ball - muscl_foul_ball_adjustment
        foul_ball_prob = log_transform(foul_ball_log, log_transform_base)         
        foul_ball_chance = prob_adjust(foul_ball_prob, -plus_hit_minus_foul)        
        foul_ball_chance *= (1.0 - base_hit) * connect_chance
        caught_out_prob = connect_chance - foul_ball_chance - base_hit_chance           
        caught_out_chance.append((prob_adjust(caught_out_prob, plus_groundout_minus_hardhit) + prob_adjust(caught_out_prob, -minus_doubleplay)) / 2.0)

        #for each of these, we need to make sure nothing is actually counting as 0 or less probability, but rather skew them relative to each other
        if base_hit_chance <= 0.0 or foul_ball_chance <= 0.0 or caught_out_chance[playerid] <= 0.0:            
            base_hit_chance += abs(base_hit_chance) + abs(foul_ball_chance) + abs(caught_out_chance[playerid])
            foul_ball_chance += abs(base_hit_chance) + abs(foul_ball_chance) + abs(caught_out_chance[playerid])
            caught_out_chance[playerid] += abs(base_hit_chance) + abs(foul_ball_chance) + abs(caught_out_chance[playerid])                        
        all_zeros = base_hit_chance == 0.0 and foul_ball_chance == 0.0 and caught_out_chance[playerid] == 0.0
        caught_out_chance[playerid] += connect_chance if all_zeros else 0.0
        all_connect_events_prob = base_hit_chance + foul_ball_chance + caught_out_chance[playerid]        
        
        if all_connect_events_prob != 0.0:
            factor = connect_chance / all_connect_events_prob
            base_hit_chance *= factor
            foul_ball_chance *= factor
            caught_out_chance[playerid] *= factor                     

        if strike_looking_chance <= 0.0 or strike_swinging_chance <= 0.0 or connect_chance <= 0.0 or ball_chance <= 0.0:
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
        
        strikeout, walked, base_hit_chance, caught_out_chance[playerid] = calc_strikeout_walked(float(strike_looking_chance), float(strike_swinging_chance), float(ball_chance), float(foul_ball_chance), float(strike_count), float(ball_count), float(base_hit_chance), float(caught_out_chance[playerid]))         
        
        corrected_strike_chance = strikeout
        corrected_strike_chance += strike_mod
        walked += walk_buff
        if "o_no" in battingAttrs or "o_no" in playerAttrs or ("a" in battingAttrs and blood_calc != "a"):
            #probability of no balls happening is the probability that every strike is a strike AND every ball is swung at
            no_balls = ((strike_chance * (1.0 - swing_correct_chance)) + (strike_chance * swing_correct_chance * (1.0 - base_connect_chance))) * ((1.0 - swing_correct_chance) * (1.0 - strike_chance))          
            no_balls = min(no_balls, 1.0)
            #straight up for o_no; a blood needs no balls reduced by blood multiplier first since it only matters when a blood procced o_no                     
            if "a" in battingAttrs:                
                no_balls *= a_blood_multiplier
            #probability of a least one ball happening is 1 - probability of no balls happening
            corrected_strike_chance *= (1.0 - no_balls)              

        walked_psychic = walked + (corrected_strike_chance * strike_to_walk) - (walked * walk_to_strike)
        corrected_strike_chance += (walked * walk_to_strike) - (corrected_strike_chance * strike_to_walk)
        walked = walked_psychic
        if corrected_strike_chance < 0.0:            
            walked += abs(corrected_strike_chance) * 2.0
            corrected_strike_chance = abs(corrected_strike_chance) * 2.0
        if walked < 0.0:            
            corrected_strike_chance += abs(walked) * 2.0
            walked += abs(walked) * 2.0
        walk_chance.append(walked)
        strike_out_chance.append(corrected_strike_chance)

        if walk_chance[playerid] <= 0.0 or base_hit_chance <= 0.0 or strike_out_chance[playerid] <= 0.0 or caught_out_chance[playerid] <= 0.0:
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
        
        attempt_steal_adjust = baset_attempt_steal_adjustment + laser_attempt_steal_adjustment - watch_attempt_steal_adjustment
        attempt_steal_log = baset_attempt_steal + laser_attempt_steal - watch_attempt_steal - attempt_steal_adjust
        attempt_steal_prob = log_transform(attempt_steal_log, log_transform_base)                
        attempt_steal_chance.append(prob_adjust(attempt_steal_prob, -minus_stealattempt))

        caught_steal_base_adjust = anticap_caught_steal_base_adjustment - laser_caught_steal_base_adjustment
        caught_steal_base_log = anticap_caught_steal_base - laser_caught_steal_base - caught_steal_base_adjust
        caught_steal_base_prob = log_transform(caught_steal_base_log, log_transform_base)            
        caught_steal_base_chance.append(prob_adjust(caught_steal_base_prob, minus_stealsuccess))
        
        caught_steal_home_adjust = anticap_caught_steal_home_adjustment + baset_caught_steal_home_adjustment + laser_caught_steal_home_adjustment
        caught_steal_home_log = anticap_caught_steal_home - baset_caught_steal_home - laser_caught_steal_home - caught_steal_home_adjust
        caught_steal_home_prob = log_transform(caught_steal_home_log, log_transform_base)        
        caught_steal_home_chance.append(prob_adjust(caught_steal_home_prob, minus_stealsuccess))
        
        homerun_adjust = div_homer_adjustment - overp_homer_adjustment
        homerun_log = div_homer - overp_homer - homerun_adjust
        homerun_prob = log_transform(homerun_log, log_transform_base)      
        homerun_adjusted = (prob_adjust(homerun_prob, -plus_hit_minus_homer) + prob_adjust(homerun_prob, -plus_groundout_minus_hardhit) + prob_adjust(homerun_prob, -plus_contact_minus_hardhit) + prob_adjust(homerun_prob, plus_hardhit) + prob_adjust(homerun_prob, -minus_homer)) / 5.0
        homerun_chance.append(homerun_adjusted * base_hit_chance)
        homerun_multipliers.append(homer_multiplier)        

        triple_adjust = muscl_triple_adjustment + ground_triple_adjustment + cont_triple_adjustment - overp_triple_adjustment - chasi_triple_adjustment
        triple_log = muscl_triple + ground_triple + cont_triple - overp_triple - chasi_triple - triple_adjust
        triple_prob = log_transform(triple_log, log_transform_base)    
        triple_adjusted = (prob_adjust(triple_prob, plus_hit_minus_homer) + prob_adjust(triple_prob, plus_hit_minus_foul) + prob_adjust(triple_prob, -plus_groundout_minus_hardhit) + prob_adjust(triple_prob, -plus_contact_minus_hardhit) + prob_adjust(triple_prob, plus_hardhit) + prob_adjust(triple_prob, -minus_hit)) / 6.0            
        triple_chance.append(triple_adjusted * base_hit_chance)

        double_adjust = muscl_double_adjustment + cont_double_adjustment - overp_double_adjustment - chasi_double_adjustment
        double_log = muscl_double + cont_double - overp_double - chasi_double - double_adjust
        double_prob = log_transform(double_log, log_transform_base)    
        double_adjusted = (prob_adjust(double_prob, plus_hit_minus_homer) + prob_adjust(double_prob, plus_hit_minus_foul) + prob_adjust(double_prob, -plus_groundout_minus_hardhit) + prob_adjust(double_prob, -plus_contact_minus_hardhit) + prob_adjust(double_prob, plus_hardhit) + prob_adjust(double_prob, -minus_hit)) / 6.0    
        double_chance.append(double_adjusted * base_hit_chance)

        single_prob = base_hit_chance - triple_chance[playerid] - double_chance[playerid] - homerun_chance[playerid]    
        if single_prob < 0.0:
            single_adjusted = (prob_adjust(single_prob, -plus_hit_minus_homer) + prob_adjust(single_prob, -plus_hit_minus_foul) + prob_adjust(single_prob, minus_hit)) / 3.0             
        else:
            single_adjusted = (prob_adjust(single_prob, plus_hit_minus_homer) + prob_adjust(single_prob, plus_hit_minus_foul) + prob_adjust(single_prob, -minus_hit)) / 3.0    
        single_chance.append(single_adjusted)

        if single_chance[playerid] <= 0.0 or triple_chance[playerid] <= 0.0 or double_chance[playerid] <= 0.0 or homerun_chance[playerid] <= 0.0:
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

        player_on_base = min(single_chance[playerid] + double_chance[playerid] + triple_chance[playerid] + walk_chance[playerid], 1.0)
        on_base_chance.append(player_on_base)
        
        hit_modifier.append(hit_multiplier)

        #runners advancing is tricky, since we have to do this based on runners being on base already, but use the batter's martyrdom for sacrifices
        sacrifice_log = martyr_sacrifice - martyr_sacrifice_adjustment
        sacrifice_chance.append(log_transform(sacrifice_log, log_transform_base) * caught_out_chance[playerid])
        
        runner_advances_adjust = laser_runner_advances_adjustment + indulg_runner_advances_adjustment - trag_runner_advances_adjustment - shakes_runner_advances_adjustment - tenacious_runner_advances_adjustment
        runner_advances_log = laser_runner_advances + indulg_runner_advances - trag_runner_advances - shakes_runner_advances - tenacious_runner_advances - runner_advances_adjust
        runner_advance_chance.append(log_transform(runner_advances_log, log_transform_base))    
        average_on_first_position.append(min(single_chance[playerid] + (walk_chance[playerid] * (1.0 - walk_mod)), 1.0))
        average_on_second_position.append(min(double_chance[playerid] + (walk_chance[playerid] * walk_mod), 1.0))
        average_on_third_position.append(min(triple_chance[playerid] + (walk_chance[playerid] * walk_mod), 1.0))

        #need to approximate caught stealing outs for blood calcing        
        average_bases_to_steal = (2.0 * average_on_first_position[playerid]) + average_on_second_position[playerid]
        average_home_to_steal = average_on_first_position[playerid] + average_on_second_position[playerid] + average_on_third_position[playerid]
        caught_steal_outs.append(min((caught_steal_base_chance[playerid] * attempt_steal_chance[playerid] * average_bases_to_steal) + (caught_steal_home_chance[playerid] * attempt_steal_chance[playerid] * average_home_to_steal), 1.0))
    return steal_mod, score_multiplier, caught_out_chance, walk_chance, strike_out_chance, attempt_steal_chance, caught_steal_base_chance, caught_steal_home_chance, homerun_chance, homerun_multipliers, triple_chance, double_chance, single_chance, caught_steal_outs, sacrifice_chance, runner_advance_chance, on_base_chance, hit_modifier, average_on_first_position, average_on_second_position, average_on_third_position

@njit(cache=True)
def calc_probs_from_stats(mods, weather, parkMods, sorted_bat_values, sorted_run_values, opp_stat_data, pitcher_stat_data, team_data, opp_data, pitcher_data, pitcherAttrs, teamPlayerAttrs, teamAttrs, oppAttrs, sorted_batters, adjustments, ruth_strike_adjust, blood_calc="Nope", innings=9, outs=3):
    if len(oppAttrs) == 0:
        opponentAttrs = List(["none", "none"])
    else:
        opponentAttrs = List([attr for attr in oppAttrs])
    if len(teamAttrs) == 0:
        numba_battingAttrs = List(["none", "none"])
    else:
        numba_battingAttrs = List([attr for attr in teamAttrs])    

    blood_count = 12.0
    a_blood_multiplier = 1.0 / blood_count        

    (unthwack_base_hit, ruth_strike, overp_homer, overp_triple, overp_double, shakes_runner_advances, cold_clutch_factor) = pitcher_stat_data

    (love_strikeout, love_easypitch, basic_multiplier, fiery_multiplier, electric_multiplier, psychic_walktrick, psychic_striketrick, acidic_multiplier) = mods
        
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
        strike_mod += fiery_multiplier
    if "psychic" in opponentAttrs:
        walk_to_strike += psychic_striketrick
    if "love" in opponentAttrs:
        strike_mod += love_strikeout
    if "acidic" in opponentAttrs:                
        score_mod += acidic_multiplier
    if "electric" in numba_battingAttrs:
        strike_mod -= electric_multiplier
    if "psychic" in numba_battingAttrs:
        strike_to_walk += psychic_walktrick
    if "love" in numba_battingAttrs:
        walk_buff += love_easypitch
    if "base_instincts" in numba_battingAttrs:
        walk_mod += basic_multiplier
    if "a" in opponentAttrs and blood_calc != "a":
        strike_mod += fiery_multiplier* a_blood_multiplier
        strike_mod += love_strikeout * a_blood_multiplier
        walk_to_strike += psychic_striketrick * a_blood_multiplier
        score_mod += acidic_multiplier * a_blood_multiplier
    if "a" in numba_battingAttrs and blood_calc != "a":
        strike_mod -= electric_multiplier * a_blood_multiplier
        walk_buff += love_easypitch * a_blood_multiplier
        walk_mod += basic_multiplier * a_blood_multiplier
        strike_to_walk += psychic_walktrick * a_blood_multiplier        

    strike_log = ruth_strike - ruth_strike_adjust
    strike_prob = log_transform(strike_log, log_transform_base)        
    strike_chance = prob_adjust(strike_prob, parkMods[4][4])    
    #clutch_log = (cold_clutch_factor - adjustments["cold_clutch_factor"]) / (cold_clutch_factor + adjustments["cold_clutch_factor"])
    #clutch_factor = log_transform(clutch_log, log_transform_base)            
    clutch_factor = 0.0
    
    tuple_parkmods = (parkMods[4][3], parkMods[4][1], parkMods[4][2], parkMods[4][7], parkMods[4][8], parkMods[4][6], parkMods[4][4], parkMods[4][5], parkMods[4][10], parkMods[4][9])
    
    steal_mod, score_multiplier, caught_out_chance, walk_chance, strike_out_chance, attempt_steal_chance, caught_steal_base_chance, caught_steal_home_chance, homerun_chance, homerun_multipliers, triple_chance, double_chance, single_chance, caught_steal_outs, sacrifice_chance, runner_advance_chance, on_base_chance, hit_modifier, average_on_first_position, average_on_second_position, average_on_third_position = calc_probs_method(len(sorted_batters), teamPlayerAttrs, numba_battingAttrs, blood_calc, score_mult_pitcher, pitcher_homer_multiplier, pitcher_hit_multiplier, pitcher_stat_data, opp_stat_data, sorted_bat_values, sorted_run_values, adjustments, tuple_parkmods, log_transform_base, outs, strike_chance, strike_to_walk, walk_buff, walk_mod, walk_to_strike, strike_mod, a_blood_multiplier)    

    return runner_advance_chance, caught_out_chance, sacrifice_chance, score_mod, hit_modifier, homerun_multipliers, score_multiplier, attempt_steal_chance, walk_chance, strike_out_chance, caught_steal_base_chance, caught_steal_home_chance, homerun_chance, triple_chance, double_chance, single_chance, caught_steal_outs, on_base_chance, average_on_first_position, average_on_second_position, average_on_third_position, steal_mod, clutch_factor, walk_mod

@njit(cache=True)
def calc_high_pressure(sorted_on_base_chance):    
    high_pressure_values = List()
    for idx in range(0, len(sorted_on_base_chance)):
        if idx == 0:
            high_pressure_values.append(sorted_on_base_chance[len(sorted_on_base_chance) - 1])
        else:
            high_pressure_values.append(sorted_on_base_chance[idx-1])
    return high_pressure_values

@njit(cache=True)
def optimized_blood_megacalc(outs, innings, outs_per_lineup, event_chance, average_blood_impact, blood_type):        
    max_x = outs * innings   
    lineup_factor = (outs - outs_per_lineup) if (outs_per_lineup < outs) else 1.0    
    for idx in range(0, len(event_chance)):
        x = 0
        average_blood_impact[idx] = 0.0     
        if outs_per_lineup < 0.1:
            average_blood_impact[idx] = 1.0
        else:                        
            while (x < max_x) and (average_blood_impact[idx] < 1.0):                    
                previous_blood_impact = average_blood_impact[idx]
                average_blood_impact[idx] += ((event_chance[idx] * ((1.0 - event_chance[idx]) ** x)) * ((max_x - x) / max_x)) * lineup_factor                    
                if (average_blood_impact[idx] - previous_blood_impact) < 0.001:
                    break
                x += outs_per_lineup * lineup_factor            
            blood_factor = (1.0 / 12.0) if blood_type == "a" else 1.0
            average_blood_impact[idx] = max(average_blood_impact[idx], 1.0) * blood_factor
    return average_blood_impact

@njit(cache=True)
def close_inning(current_innings, innings_since_lineup_start, inning_outs, inning_score, inning_rbi, team_score, team_rbi, total_innings, runners_on_first, runners_on_second, runners_on_third, runners_on_fourth, runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth, loop_encountered, loop_index, final_batter_and_checkpoint, start_loop_score_and_rbi, start_loop_hits, start_loop_homers, start_loop_steals, start_loop_strikeouts, start_loop_inning, player_score, player_rbi, away_home, opp_score, replicates, hits, homers, stolen_bases, strikeouts, last_pass, playerid, checkpoint):
    close_game, close_loop = False, False
    runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
    runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
    current_innings += 1
    innings_since_lineup_start += 1     
    inning_outs = 0.0
    inning_score += player_score           
    inning_rbi += player_rbi
    team_score += inning_score  
    team_rbi += inning_rbi
    if (away_home == "home") and (current_innings == 8):
        if team_score > (opp_score / replicates):
            #home team will only need 8 innings to win
            total_innings = replicates * 8
    inning_score, inning_rbi = 0.0, 0.0                
    if current_innings >= total_innings:                
        close_game = True
    elif not last_pass:                
        if (playerid, checkpoint) in final_batter_and_checkpoint:    
            #experimenting with if .index takes longer than doing it in a loop
            #loop_index = final_batter_and_checkpoint.index((playerid, checkpoint))                                  
            for player in range (2, len(final_batter_and_checkpoint)):
                if final_batter_and_checkpoint[player] == (playerid, checkpoint):
                    loop_index = player
            if final_batter_and_checkpoint[loop_index] == (playerid, checkpoint):
                loop_encountered = True                                
                close_loop = True
        else:
            final_batter_and_checkpoint.append((playerid, checkpoint))            
            start_loop_score_and_rbi.append((team_score, team_rbi))
            start_loop_hits.append(hits[:]), start_loop_homers.append(homers[:]), start_loop_steals.append(stolen_bases[:])
            start_loop_strikeouts.append(strikeouts), start_loop_inning.append(current_innings)
    return current_innings, innings_since_lineup_start, inning_outs, inning_score, inning_rbi, team_score, team_rbi, total_innings, runners_on_first, runners_on_second, runners_on_third, runners_on_fourth, runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth, loop_encountered, loop_index, final_batter_and_checkpoint, start_loop_score_and_rbi, start_loop_hits, start_loop_homers, start_loop_steals, start_loop_strikeouts, start_loop_inning, close_game, close_loop

@njit(cache=True)
def simulate_game(team_score, team_rbi, opp_score, away_home, innings, outs, total_batters, extra_base, homerun_chance, triple_chance, double_chance, single_chance, walk_chance, walk_mod, sacrifice_chance, runner_advance_chance, average_on_first, average_on_second, average_on_third, reverberating, score_mod, strike_out_chance, caught_out_chance, caught_steal_base_chance, caught_steal_home_chance, attempt_steal_chance, homerun_multipliers, hit_modifier, steal_mod, score_multiplier, homers, hits, stolen_bases):    
    replicates = 10
    total_innings = innings * replicates        
    current_innings, atbats_in_inning = 0, 0  
    current_outs = 0.0    
    inning_score, inning_rbi = 0.0, 0.0
    runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
    runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
    inning_outs, strikeouts = 0.0, 0.0        
    final_batter_and_checkpoint, start_loop_score_and_rbi = List([(-1, -1), (-1, -1)]), List([(-1.0, -1.0), (-1.0, -1.0)])
    start_loop_hits, start_loop_homers, start_loop_steals = List(), List(), List()
    #everything has two sets of dummy values
    start_loop_hits.append(hits[:]), start_loop_homers.append(homers[:]), start_loop_steals.append(stolen_bases[:])
    start_loop_hits.append(hits[:]), start_loop_homers.append(homers[:]), start_loop_steals.append(stolen_bases[:])
    start_loop_strikeouts, start_loop_inning = List([-1.0, -1.0]), List([-1, -1])
    last_pass, loop_encountered = False, False
    loop_index, starting_player = 0, 0        

    while current_innings < total_innings:        
        starting_lineup_inning_outs, starting_lineup_inning_score, starting_lineup_inning_rbi = inning_outs, inning_score, inning_rbi
        innings_since_lineup_start = 0
        for playerid in range(starting_player, len(walk_chance)):              
            base = 20.0 if extra_base[playerid] else 25.0                   
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
            runners_on_third, runner_advance_third = calc_runners_on(runners_on_third, runner_advance_third, runners_on_second, runner_advance_second, runners_on_first, runner_advance_first, 0.0, 0.0, single_chance[playerid], double_chance[playerid], triple_chance[playerid], homerun_chance[playerid], sacrifice_chance[playerid], caught_out_chance[playerid], walk_chance[playerid], walk_mod, average_on_third[playerid], runner_advance_chance[playerid])
            runners_on_second, runner_advance_second = calc_runners_on(runners_on_second, runner_advance_second, runners_on_first, runner_advance_first, 0.0, 0.0, 0.0, 0.0, single_chance[playerid], double_chance[playerid], triple_chance[playerid], homerun_chance[playerid], sacrifice_chance[playerid], caught_out_chance[playerid], walk_chance[playerid], walk_mod, average_on_second[playerid], runner_advance_chance[playerid])
            runners_on_first, runner_advance_first = calc_runners_on(runners_on_first, runner_advance_first, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, single_chance[playerid], double_chance[playerid], triple_chance[playerid], homerun_chance[playerid], sacrifice_chance[playerid], caught_out_chance[playerid], walk_chance[playerid], walk_mod, average_on_first[playerid], runner_advance_chance[playerid])
            player_rbi = runners_advance_score + walking_score + homerun_score + triple_runners_score + double_runners_score + single_runners_score
            player_score = (runners_advance_score + walking_score + (homerun_score * homerun_multipliers[playerid]) + ((triple_runners_score + double_runners_score + single_runners_score) * hit_modifier[playerid])) * score_multiplier[playerid]            
            homers[playerid] += homerun_chance[playerid]
            hits[playerid] += triple_chance[playerid] + double_chance[playerid] + single_chance[playerid]
            player_outs = strike_out_chance[playerid] + caught_out_chance[playerid]
            strikeouts += strike_out_chance[playerid]
            inning_outs += player_outs            
            if inning_outs >= outs:                
                current_innings, innings_since_lineup_start, inning_outs, inning_score, inning_rbi, team_score, team_rbi, total_innings, runners_on_first, runners_on_second, runners_on_third, runners_on_fourth, runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth, loop_encountered, loop_index, final_batter_and_checkpoint, start_loop_score_and_rbi, start_loop_hits, start_loop_homers, start_loop_steals, start_loop_strikeouts, start_loop_inning, close_game, close_loop = close_inning(current_innings, innings_since_lineup_start, inning_outs, inning_score, inning_rbi, team_score, team_rbi, total_innings, runners_on_first, runners_on_second, runners_on_third, runners_on_fourth, runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth, loop_encountered, loop_index, final_batter_and_checkpoint, start_loop_score_and_rbi, start_loop_hits, start_loop_homers, start_loop_steals, start_loop_strikeouts, start_loop_inning, player_score, player_rbi, away_home, opp_score, replicates, hits, homers, stolen_bases, strikeouts, last_pass, playerid, 0)   
                if close_game or close_loop:
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
                steal_second_opportunities = average_on_first[playerid] * (1.0 - min(steal_runners_on_second - average_on_second[playerid], 0.0))
                #steal third
                steal_third_opportunities = (steal_second_opportunities * (1.0 - min(steal_runners_on_third - average_on_third[playerid], 0.0))) + (average_on_second[playerid] * (1.0 - min(steal_runners_on_third - average_on_third[playerid], 0.0)))
                #adjust base position based on stealing bases
                runners_on_first -= (steal_second_opportunities * attempt_steal_chance[playerid])
                runner_advance_first -= (steal_second_opportunities * attempt_steal_chance[playerid]) * runner_advance_chance[playerid]
                runners_on_second += (steal_second_opportunities * steal_base_success_rate) - (steal_third_opportunities * attempt_steal_chance[playerid])
                runner_advance_second += ((steal_second_opportunities * steal_base_success_rate) - (steal_third_opportunities * attempt_steal_chance[playerid])) * runner_advance_chance[playerid]
                if base == 20.0:                    
                    #steal fourth
                    steal_fourth_opportunities = steal_third_opportunities * (1.0 - steal_runners_on_fourth)                    
                    steal_fourth_opportunities += average_on_third[playerid] * (1.0 - steal_runners_on_fourth)
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
                    steal_home_opportunities += average_on_third[playerid]
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
                    current_innings, innings_since_lineup_start, inning_outs, inning_score, inning_rbi, team_score, team_rbi, total_innings, runners_on_first, runners_on_second, runners_on_third, runners_on_fourth, runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth, loop_encountered, loop_index, final_batter_and_checkpoint, start_loop_score_and_rbi, start_loop_hits, start_loop_homers, start_loop_steals, start_loop_strikeouts, start_loop_inning, close_game, close_loop = close_inning(current_innings, innings_since_lineup_start, inning_outs, inning_score, inning_rbi, team_score, team_rbi, total_innings, runners_on_first, runners_on_second, runners_on_third, runners_on_fourth, runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth, loop_encountered, loop_index, final_batter_and_checkpoint, start_loop_score_and_rbi, start_loop_hits, start_loop_homers, start_loop_steals, start_loop_strikeouts, start_loop_inning, player_score, player_rbi, away_home, opp_score, replicates, hits, homers, stolen_bases, strikeouts, last_pass, playerid, 1)   
                    if close_game or close_loop:
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
                    if reverberating[playerid]:
                        player_score *= 1.02
                        hits[playerid] += (triple_chance[playerid] + double_chance[playerid] + single_chance[playerid]) * 0.02
                        homers[playerid] += homerun_chance[playerid] * 0.02
                        player_rbi += ((100.0 + steal_mod[playerid]) * (steal_home_opportunities * steal_home_success_rate)) + (steal_mod[playerid] * steal_base_opportunities * steal_base_success_rate) * 0.02
                        player_rbi += (runners_advance_score + walking_score + homerun_score + triple_runners_score + double_runners_score + single_runners_score) * 0.02
                        stolen_bases[playerid] += ((steal_base_opportunities * steal_base_success_rate) + (steal_home_opportunities * steal_home_success_rate)) * 0.02
                        strikeouts += (strike_out_chance[playerid] * 0.02)
                        inning_outs += player_outs * 0.02         
                    if inning_outs >= outs:
                        current_innings, innings_since_lineup_start, inning_outs, inning_score, inning_rbi, team_score, team_rbi, total_innings, runners_on_first, runners_on_second, runners_on_third, runners_on_fourth, runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth, loop_encountered, loop_index, final_batter_and_checkpoint, start_loop_score_and_rbi, start_loop_hits, start_loop_homers, start_loop_steals, start_loop_strikeouts, start_loop_inning, close_game, close_loop = close_inning(current_innings, innings_since_lineup_start, inning_outs, inning_score, inning_rbi, team_score, team_rbi, total_innings, runners_on_first, runners_on_second, runners_on_third, runners_on_fourth, runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth, loop_encountered, loop_index, final_batter_and_checkpoint, start_loop_score_and_rbi, start_loop_hits, start_loop_homers, start_loop_steals, start_loop_strikeouts, start_loop_inning, player_score, player_rbi, away_home, opp_score, replicates, hits, homers, stolen_bases, strikeouts, last_pass, playerid, 2)   
                        if close_game or close_loop:
                            break                        
                    else:
                        inning_score += player_score
                        inning_rbi += player_rbi       
        
        if starting_player == 0:
            if (current_innings < total_innings):                
                if loop_encountered:                
                    loop_encountered, last_pass = False, True                
                    #first determine if we're heading toward winning in 8 innings instead of 9
                    if away_home == "home" and current_innings <= 8:
                        eight_inning_score = team_score * (8.0 / current_innings)                    
                        if eight_inning_score > (opp_score / replicates):
                            total_innings = replicates * 8
                    innings_in_loop = current_innings - start_loop_inning[loop_index]                       
                    loop_count = int((total_innings - current_innings) / innings_in_loop)                                
                    if loop_count > 0:         
                        start_loop_score, rbi_loop_score = start_loop_score_and_rbi[loop_index]
                        team_score += (team_score - start_loop_score) * loop_count
                        team_rbi += (team_rbi - rbi_loop_score) * loop_count
                        loop_hits, loop_homers, loop_steals = start_loop_hits[loop_index], start_loop_homers[loop_index], start_loop_steals[loop_index]                    
                        for loopbatter in range(0, len(walk_chance)):                                         
                            hits[loopbatter] += (hits[loopbatter] - loop_hits[loopbatter]) * loop_count                        
                            homers[loopbatter] += (homers[loopbatter] - loop_homers[loopbatter]) * loop_count
                            stolen_bases[loopbatter] += (stolen_bases[loopbatter] - loop_steals[loopbatter]) * loop_count                                                
                        strikeouts += (strikeouts - start_loop_strikeouts[loop_index]) * loop_count                    
                        current_innings += innings_in_loop * loop_count                                    
                    starting_player, checkpoint = final_batter_and_checkpoint[loop_index]                
                    starting_player = 0 if ((len(walk_chance) - 1) == starting_player) else (starting_player + 1)                
                
                elif ((inning_outs - starting_lineup_inning_outs) < 1) and (innings_since_lineup_start == 0):
                    #print("hitting the kill switch")
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
                    #try:
                    lineup_score = (inning_score - starting_lineup_inning_score) * (lineup_passes + 1)
                    lineup_rbi = (inning_rbi - starting_lineup_inning_rbi) * (lineup_passes + 1)
                    #except OverflowError:
                    #    lineup_score = 100000000000.0
                    #    lineup_rbi = 100000000000.0
                    #increase team score by this amount
                    team_score += lineup_score
                    team_rbi += lineup_rbi
                    #finish scoring for the team
                    current_innings = total_innings
                    #print("Shortcutting {} lineup passes".format(lineup_passes))
                    #only update the hits homers and steals if we are generating runtime output                                   
                    for playerid in range(0, len(walk_chance)):                        
                        hits[playerid] *= lineup_passes + 1
                        homers[playerid] *= lineup_passes + 1
                        stolen_bases[playerid] *= lineup_passes + 1
                    strikeouts *= lineup_passes + 1        
                    last_pass = True
        starting_player = 0           
    return team_score, stolen_bases, homers, hits, strikeouts, team_rbi

@njit(cache=True)
def calc_team_score(mods, weather, parkMods, away_home, team_bat_data, team_run_data, opp_stat_data, pitcher_stat_data, team_data, opp_data, pitcher_data, pitcherAttrs, teamPlayerAttrs, teamAttrs, oppAttrs, sorted_batters, adjustments, ruth_strike_adjust, opp_score=0.0, innings=9, outs=3.0, runtime_solution=False):      
    battingAttrs = teamAttrs    
    reverb_weather, sun_weather, bh_weather = weather
    runner_advance_chance, caught_out_chance, sacrifice_chance, score_mod, hit_modifier, homerun_multipliers, score_multiplier, attempt_steal_chance, walk_chance, strike_out_chance, caught_steal_base_chance, caught_steal_home_chance, homerun_chance, triple_chance, double_chance, single_chance, caught_steal_outs, on_base_chance, average_on_first, average_on_second, average_on_third, steal_mod, clutch_factor, walk_mod = calc_probs_from_stats(mods, weather, parkMods, team_bat_data, team_run_data, opp_stat_data, pitcher_stat_data, team_data, opp_data, pitcher_data, pitcherAttrs, teamPlayerAttrs, teamAttrs, oppAttrs, sorted_batters, adjustments, ruth_strike_adjust, "Nope", innings)          
    
    team_score = 100.0 if ("home_field" in battingAttrs and away_home == "home") else 0.0
    team_rbi = team_score        

    runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = 0.0, 0.0, 0.0, 0.0
    runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = 0.0, 0.0, 0.0, 0.0
    inning_outs, strikeouts = 0.0, 0.0
    batter_atbats = 0        
    
    extra_base = List([(("extra_base" in battingAttrs) or ("extra_base" in teamPlayerAttrs[playerid])) for playerid in range(0, len(walk_chance))])
    reverberating = List([(("reverberating" in teamPlayerAttrs[playerid]) or ("repeating" in teamPlayerAttrs[playerid] and reverb_weather)) for playerid in range(0, len(walk_chance))])
    homers_hit, hits_hit, bases_stolen = List([0.0 for val in walk_chance]), List([0.0 for val in walk_chance]), List([0.0 for val in walk_chance])
    
    #single_chances, double_chances, triple_chances, homerun_chances = [val for val in single_chance.values()], [val for val in double_chance.values()], [val for val in triple_chance.values()], [val for val in homerun_chance.values()]    
    #runner_advance_chances, walk_chances, sacrifice_chances = [val for val in runner_advance_chance.values()], [val for val in walk_chance.values()], [val for val in sacrifice_chance.values()]
    #strike_out_chances, caught_out_chances = [val for val in strike_out_chance.values()], [val for val in caught_out_chance.values()]
    #caught_steal_base_chances, caught_steal_home_chances, attempt_steal_chances = [val for val in caught_steal_base_chance.values()], [val for val in caught_steal_home_chance.values()], [val for val in attempt_steal_chance.values()]
    #homerun_multi, hit_mod, steal_modifier, score_multi = [val for val in homerun_multipliers.values()], [val for val in hit_modifier.values()], [val for val in steal_mod.values()], [val for val in score_multiplier.values()]    
    
    team_score, bases_stolen, homers_hit, hits_hit, strikeouts, team_rbi = simulate_game(team_score, team_rbi, opp_score, away_home, int(innings), outs, len(walk_chance), extra_base, homerun_chance, triple_chance, double_chance, single_chance, walk_chance, walk_mod, sacrifice_chance, runner_advance_chance, average_on_first, average_on_second, average_on_third, reverberating, score_mod, strike_out_chance, caught_out_chance, caught_steal_base_chance, caught_steal_home_chance, attempt_steal_chance, homerun_multipliers, hit_modifier, steal_mod, score_multiplier, homers_hit, hits_hit, bases_stolen)    
    
    #need to re-enable this in the case of wanting to do sun/black hole weather handling
    if (sun_weather or bh_weather) and runtime_solution:                
        #print("Adjusting team score for {} weather: team score = {}, adjusted score = {}".format("Sun 2" if weather == sun_weather else "Black Hole", team_score, adjusted_score))
        team_score = team_score % 1000.0            
        
    return team_score, bases_stolen, homers_hit, hits_hit, strikeouts, team_rbi

@njit(cache=True)
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

@njit(cache=True)
def calc_offense_player_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, player_bat_data, player_run_data, adjusted_bat_data, adjusted_run_data, overperform_pct=0.0):
    calced_batting_stlats = calc_batting(terms[2], teamMods[2], player_bat_data, adjusted_bat_data, overperform_pct)
    calced_running_stlats = calc_running(terms[3], teamMods[3], player_run_data, adjusted_run_data, overperform_pct)          
    return calced_batting_stlats, calced_running_stlats

@njit(cache=True)
def calc_defense_player_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, player_stat_data, adjusted_stat_data, overperform_pct=0.0):    
    ovp_from_hp = (away_home == "away" and "high_presssure" in awayAttrs and weather) or (away_home == "home" and "high_presssure" in homeAttrs and weather)
    if ovp_from_hp:
        player_omni_base_hit, player_watch_attempt_steal, player_chasi_triple, player_chasi_double, player_anticap_caught_steal_base, player_anticap_caught_steal_home, player_tenacious_runner_advances = calc_defense(terms[1], teamMods[1], player_stat_data, adjusted_stat_data, 0.0)
    else:
        player_omni_base_hit, player_watch_attempt_steal, player_chasi_triple, player_chasi_double, player_anticap_caught_steal_base, player_anticap_caught_steal_home, player_tenacious_runner_advances = calc_defense(terms[1], teamMods[1], player_stat_data, adjusted_stat_data, overperform_pct)    
    return player_omni_base_hit, player_watch_attempt_steal, player_chasi_triple, player_chasi_double, player_anticap_caught_steal_base, player_anticap_caught_steal_home, player_tenacious_runner_advances

@njit(cache=True)
def calc_team_stlats(terms, sorted_batters, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data, pitcher_stat_data, adjusted_stat_data, shelled, aa_blood_impact, aaa_blood_impact, high_pressure_mod):    
    team_omni_base_hit, team_watch_attempt_steal, team_chasi_triple, team_chasi_double, team_anticap_caught_steal_base, team_anticap_caught_steal_home, team_tenacious_runner_advances = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    lineup = 0.0    
    blood_player = 0
    team_batting, team_running = List(), List()
    
    for playerid in range(0, len(sorted_batters)):                        
        overperform_pct = 0.0        
        player_omni_base_hit, player_watch_attempt_steal, player_chasi_triple, player_chasi_double, player_anticap_caught_steal_base, player_anticap_caught_steal_home, player_tenacious_runner_advances = calc_defense_player_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data[0][playerid], adjusted_stat_data[0][playerid], overperform_pct)
        if not shelled[playerid]:                        
            overperform_pct = aa_blood_impact[blood_player] + aaa_blood_impact[blood_player] + high_pressure_mod[blood_player]            
            player_batting, player_running = calc_offense_player_stlats(terms, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data[1][blood_player], team_stat_data[2][blood_player], adjusted_stat_data[1][blood_player], adjusted_stat_data[2][blood_player], overperform_pct)            
            team_batting.append(player_batting), team_running.append(player_running)
            #if blood_player < 2:
            #    team_stlats[blood_player] = player_stats
            #else:
            #    team_stlats.append(player_stats)
            blood_player += 1
        lineup += 1.0
        team_omni_base_hit += player_omni_base_hit
        team_watch_attempt_steal += player_watch_attempt_steal
        team_chasi_triple += player_chasi_triple
        team_chasi_double += player_chasi_double
        team_anticap_caught_steal_base += player_anticap_caught_steal_base
        team_anticap_caught_steal_home += player_anticap_caught_steal_home
        team_tenacious_runner_advances += player_tenacious_runner_advances    
    team_omni_base_hit = team_omni_base_hit / lineup
    team_watch_attempt_steal = team_watch_attempt_steal / lineup
    team_chasi_triple = team_chasi_triple / lineup
    team_chasi_double = team_chasi_double / lineup
    team_anticap_caught_steal_base = team_anticap_caught_steal_base / lineup
    team_anticap_caught_steal_home = team_anticap_caught_steal_home / lineup
    team_tenacious_runner_advances = team_tenacious_runner_advances / lineup
    team_defense = (team_omni_base_hit, team_watch_attempt_steal, team_chasi_triple, team_chasi_double, team_anticap_caught_steal_base, team_anticap_caught_steal_home, team_tenacious_runner_advances)
    pitcherStlats = calc_pitching(terms[0], teamMods[0], pitcher_stat_data)

    return team_batting, team_running, team_defense, pitcherStlats

@njit(cache=True)
def blood_impact_calc(terms, batter_order, mods, weather, away_home, teamMods, calc_team_bat, calc_team_run, calc_opp_data, calc_pitcher_data, team_stat_data, opp_stat_data, opp_pitcher_data, opp_pitcher_attrs, team_pitcher_data, team_pitcher_attrs, teamPlayerAttrs, teamAttrs, oppAttrs, sorted_batters, adjusted_stat_data, average_aa_impact, average_aaa_impact, high_pressure_mod, adjustments, shelled, ruth_strike_adjust, innings=9):        
    if away_home == "away":
        awayAttrs, homeAttrs = teamAttrs, oppAttrs
    else:
        awayAttrs, homeAttrs = oppAttrs, teamAttrs    
    blood_calc = "a" if "a" in teamAttrs else "None"    
    runner_advance_chance, caught_out_chance, sacrifice_chance, score_mod, hit_modifier, homerun_multipliers, score_multiplier, attempt_steal_chance, walk_chance, strike_out_chance, caught_steal_base_chance, caught_steal_home_chance, homerun_chance, triple_chance, double_chance, single_chance, caught_steal_outs, on_base_chance, average_on_first, average_on_second, average_on_third, steal_mod, clutch_factor, walk_mod = calc_probs_from_stats(mods, weather, teamMods, calc_team_bat, calc_team_run, calc_opp_data, calc_pitcher_data, team_stat_data, opp_stat_data, opp_pitcher_data, opp_pitcher_attrs, teamPlayerAttrs, teamAttrs, oppAttrs, batter_order, adjustments, ruth_strike_adjust, blood_calc, innings)

    outs = 3.0
    outs_per_lineup = sum(strike_out_chance) + sum(caught_steal_outs) + sum(caught_out_chance)        
    
    if "aa" in teamAttrs:                
        average_aa_blood_impact = optimized_blood_megacalc(outs, innings, outs_per_lineup, double_chance, average_aa_impact, "aa")                
        team_batting, team_running, team_defense, pitcherStlats = calc_team_stlats(terms, batter_order, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data, team_pitcher_data, adjusted_stat_data, shelled, average_aa_blood_impact, average_aaa_impact, high_pressure_mod)
    if "aaa" in teamAttrs:        
        average_aaa_blood_impact = optimized_blood_megacalc(outs, innings, outs_per_lineup, triple_chance, average_aaa_impact, "aaa")                
        team_batting, team_running, team_defense, pitcherStlats = calc_team_stlats(terms, batter_order, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data, team_pitcher_data, adjusted_stat_data, shelled, average_aa_impact, average_aaa_blood_impact, high_pressure_mod)
    if "a" in teamAttrs:        
        average_aa_blood_impact = optimized_blood_megacalc(outs, innings, outs_per_lineup, double_chance, average_aa_impact, "a")                        
        average_aaa_blood_impact = optimized_blood_megacalc(outs, innings, outs_per_lineup, triple_chance, average_aaa_impact, "a")                
        team_batting, team_running, team_defense, pitcherStlats = calc_team_stlats(terms, batter_order, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data, team_pitcher_data, adjusted_stat_data, shelled, average_aa_blood_impact, average_aaa_blood_impact, high_pressure_mod)
    if "high_pressure" in teamAttrs:
        high_pressure = calc_high_pressure(on_base_chance)
        team_batting, team_running, team_defense, pitcherStlats = calc_team_stlats(terms, batter_order, mods, awayAttrs, homeAttrs, teamMods, weather, away_home, team_stat_data, team_pitcher_data, adjusted_stat_data, shelled, average_aa_impact, average_aaa_impact, high_pressure)
    return team_batting, team_running, team_defense, pitcherStlats

def get_lists_from_loop(batter_order, team_stat_data, team, adjusted_stat_data, away_home):
    shelled, active_batters, average_aa_impact, average_aaa_impact, high_pressure_mod = List(), List(), List(), List(), List()    
    defense_data, batting_data, running_data, playerAttrs = List(), List(), List(), List()
    for playerid in batter_order:
        shelled.append(team_stat_data[team][playerid]["shelled"])        
        defense_data.append(List([team_stat_data[team][playerid]["omniscience"], team_stat_data[team][playerid]["watchfulness"], team_stat_data[team][playerid]["chasiness"], team_stat_data[team][playerid]["anticapitalism"], team_stat_data[team][playerid]["tenaciousness"]]))
        if not team_stat_data[team][playerid]["shelled"]:
            active_batters.append(playerid)
            average_aa_impact.append(0.0), average_aaa_impact.append(0.0), high_pressure_mod.append(0.0)                                 
            batting_data.append(List([team_stat_data[team][playerid]["patheticism"], team_stat_data[team][playerid]["tragicness"], team_stat_data[team][playerid]["thwackability"], team_stat_data[team][playerid]["divinity"], team_stat_data[team][playerid]["moxie"], team_stat_data[team][playerid]["musclitude"], team_stat_data[team][playerid]["martyrdom"]])) 
            running_data.append(List([team_stat_data[team][playerid]["laserlikeness"], team_stat_data[team][playerid]["baseThirst"], team_stat_data[team][playerid]["continuation"], team_stat_data[team][playerid]["groundFriction"], team_stat_data[team][playerid]["indulgence"]]))
            if len(team_stat_data[team][playerid]["attrs"]) > 0:
                playerAttrs.append(List(team_stat_data[team][playerid]["attrs"]))
            else:
                playerAttrs.append(List(["none", "none"]))    
    team_stat_data = List([defense_data, batting_data, running_data])    
    return shelled, active_batters, average_aa_impact, average_aaa_impact, high_pressure_mod, adjusted_stat_data[away_home], team_stat_data, playerAttrs
    
def get_mofo_playerbased(dict_mods, awayPitcher, homePitcher, awayTeam, homeTeam, awayAttrs, homeAttrs, weather, team_stat_data, pitcher_stat_data, terms, away_batter_order, home_batter_order, awayMods, homeMods, adjusted_stat_data, dict_adjustments, away_shelled, away_active_batters, away_average_aa_impact, away_average_aaa_impact, away_high_pressure_mod, adjusted_stat_data_away, away_team_stat_data, awayPlayerAttrs, home_shelled, home_active_batters, home_average_aa_impact, home_average_aaa_impact, home_high_pressure_mod, adjusted_stat_data_home, home_team_stat_data, homePlayerAttrs, skip_mods=False, runtime_solution=False):            
    #start_time = time.time()
    polarity_plus, polarity_minus, flood_weather = helpers.get_weather_idx("Polarity +"), helpers.get_weather_idx("Polarity -"), helpers.get_weather_idx("Flooding")
    if weather == polarity_plus or weather == polarity_minus:
        if not runtime_solution:
            return .5, .5        

    flooding = weather == flood_weather
    check_weather = (helpers.get_weather_idx("Reverb") == weather, helpers.get_weather_idx("Sun 2") == weather, helpers.get_weather_idx("Black Hole") == weather)   
    
    mods = (float(dict_mods["love"]["opp"]["strikeout"]), float(dict_mods["love"]["opp"]["easypitch"]), float(dict_mods["base_instincts"]["same"]["multiplier"]), float(dict_mods["fiery"]["same"]["multiplier"]), float(dict_mods["electric"]["same"]["multiplier"]), float(dict_mods["psychic"]["same"]["walktrick"]), float(dict_mods["psychic"]["same"]["striketrick"]), float(dict_mods["acidic"]["same"]["multiplier"]))

    adjustments = (dict_adjustments["moxie_swing_correct"], dict_adjustments["path_connect"], dict_adjustments["thwack_base_hit"], dict_adjustments["unthwack_base_hit"], dict_adjustments["omni_base_hit"], dict_adjustments["muscl_foul_ball"], dict_adjustments["baset_attempt_steal"], dict_adjustments["laser_attempt_steal"], dict_adjustments["watch_attempt_steal"], dict_adjustments["anticap_caught_steal_base"], dict_adjustments["laser_caught_steal_base"], dict_adjustments["anticap_caught_steal_home"], dict_adjustments["baset_caught_steal_home"], dict_adjustments["laser_caught_steal_home"], dict_adjustments["div_homer"], dict_adjustments["overp_homer"], dict_adjustments["muscl_triple"], dict_adjustments["ground_triple"], dict_adjustments["cont_triple"], dict_adjustments["overp_triple"], dict_adjustments["chasi_triple"], dict_adjustments["muscl_double"], dict_adjustments["cont_double"], dict_adjustments["overp_double"], dict_adjustments["chasi_double"], dict_adjustments["martyr_sacrifice"], dict_adjustments["laser_runner_advances"], dict_adjustments["indulg_runner_advances"], dict_adjustments["trag_runner_advances"], dict_adjustments["shakes_runner_advances"], dict_adjustments["tenacious_runner_advances"])

    ruth_strike_adjust = dict_adjustments["ruth_strike"]    

    #away_shelled, away_active_batters, away_average_aa_impact, away_average_aaa_impact, away_high_pressure_mod, adjusted_stat_data_away, away_team_stat_data, awayPlayerAttrs = get_lists_from_loop(away_batter_order, team_stat_data, awayTeam, adjusted_stat_data, "away")
    #home_shelled, home_active_batters, home_average_aa_impact, home_average_aaa_impact, home_high_pressure_mod, adjusted_stat_data_home, home_team_stat_data, homePlayerAttrs = get_lists_from_loop(home_batter_order, team_stat_data, homeTeam, adjusted_stat_data, "home")    

    #away_shelled, home_shelled = List([team_stat_data[awayTeam][playerid]["shelled"] for playerid in away_batter_order]), List([team_stat_data[homeTeam][playerid]["shelled"] for playerid in home_batter_order])

    #away_active_batters, home_active_batters = List([playerid for playerid in away_batter_order if not team_stat_data[awayTeam][playerid]["shelled"]]), List([playerid for playerid in home_batter_order if not team_stat_data[homeTeam][playerid]["shelled"]])

    #away_average_aa_impact, away_average_aaa_impact, away_high_pressure_mod = List([0.0 for playerid in away_active_batters]), List([0.0 for playerid in away_active_batters]), List([0.0 for playerid in away_active_batters])
    #home_average_aa_impact, home_average_aaa_impact, home_high_pressure_mod = List([0.0 for playerid in home_active_batters]), List([0.0 for playerid in home_active_batters]), List([0.0 for playerid in home_active_batters])
    
    #adjusted_away_defense_data, adjusted_home_defense_data = List([List([adjusted_stat_data["away"][playerid]["omniscience"], adjusted_stat_data["away"][playerid]["watchfulness"], adjusted_stat_data["away"][playerid]["chasiness"], adjusted_stat_data["away"][playerid]["anticapitalism"], adjusted_stat_data["away"][playerid]["tenaciousness"]]) for playerid in away_batter_order]), List([List([adjusted_stat_data["home"][playerid]["omniscience"], adjusted_stat_data["home"][playerid]["watchfulness"], adjusted_stat_data["home"][playerid]["chasiness"], adjusted_stat_data["home"][playerid]["anticapitalism"], adjusted_stat_data["home"][playerid]["tenaciousness"]]) for playerid in home_batter_order])

    #adjusted_away_batting_data, adjusted_home_batting_data = List([List([adjusted_stat_data["away"][playerid]["patheticism"], adjusted_stat_data["away"][playerid]["tragicness"], adjusted_stat_data["away"][playerid]["thwackability"], adjusted_stat_data["away"][playerid]["divinity"], adjusted_stat_data["away"][playerid]["moxie"], adjusted_stat_data["away"][playerid]["musclitude"], adjusted_stat_data["away"][playerid]["martyrdom"]]) for playerid in away_batter_order if not team_stat_data[awayTeam][playerid]["shelled"]]), List([List([adjusted_stat_data["home"][playerid]["patheticism"], adjusted_stat_data["home"][playerid]["tragicness"], adjusted_stat_data["home"][playerid]["thwackability"], adjusted_stat_data["home"][playerid]["divinity"], adjusted_stat_data["home"][playerid]["moxie"], adjusted_stat_data["home"][playerid]["musclitude"], adjusted_stat_data["home"][playerid]["martyrdom"]]) for playerid in home_batter_order if not team_stat_data[homeTeam][playerid]["shelled"]])

    #adjusted_away_running_data, adjusted_home_running_data = List([List([adjusted_stat_data["away"][playerid]["laserlikeness"], adjusted_stat_data["away"][playerid]["baseThirst"], adjusted_stat_data["away"][playerid]["continuation"], adjusted_stat_data["away"][playerid]["groundFriction"], adjusted_stat_data["away"][playerid]["indulgence"]]) for playerid in away_batter_order if not team_stat_data[awayTeam][playerid]["shelled"]]), List([List([adjusted_stat_data["home"][playerid]["laserlikeness"], adjusted_stat_data["home"][playerid]["baseThirst"], adjusted_stat_data["home"][playerid]["continuation"], adjusted_stat_data["home"][playerid]["groundFriction"], adjusted_stat_data["home"][playerid]["indulgence"]]) for playerid in home_batter_order if not team_stat_data[homeTeam][playerid]["shelled"]])

    #adjusted_stat_data_away, adjusted_stat_data_home = List([adjusted_away_defense_data, adjusted_away_batting_data, adjusted_away_running_data]), List([adjusted_home_defense_data, adjusted_home_batting_data, adjusted_home_running_data])

    #away_defense_data, home_defense_data = List([List([team_stat_data[awayTeam][playerid]["omniscience"], team_stat_data[awayTeam][playerid]["watchfulness"], team_stat_data[awayTeam][playerid]["chasiness"], team_stat_data[awayTeam][playerid]["anticapitalism"], team_stat_data[awayTeam][playerid]["tenaciousness"]]) for playerid in away_batter_order]), List([List([team_stat_data[homeTeam][playerid]["omniscience"], team_stat_data[homeTeam][playerid]["watchfulness"], team_stat_data[homeTeam][playerid]["chasiness"], team_stat_data[homeTeam][playerid]["anticapitalism"], team_stat_data[homeTeam][playerid]["tenaciousness"]]) for playerid in home_batter_order])

    #away_batting_data, home_batting_data = List([List([team_stat_data[awayTeam][playerid]["patheticism"], team_stat_data[awayTeam][playerid]["tragicness"], team_stat_data[awayTeam][playerid]["thwackability"], team_stat_data[awayTeam][playerid]["divinity"], team_stat_data[awayTeam][playerid]["moxie"], team_stat_data[awayTeam][playerid]["musclitude"], team_stat_data[awayTeam][playerid]["martyrdom"]]) for playerid in away_batter_order if not team_stat_data[awayTeam][playerid]["shelled"]]), List([List([team_stat_data[homeTeam][playerid]["patheticism"], team_stat_data[homeTeam][playerid]["tragicness"], team_stat_data[homeTeam][playerid]["thwackability"], team_stat_data[homeTeam][playerid]["divinity"], team_stat_data[homeTeam][playerid]["moxie"], team_stat_data[homeTeam][playerid]["musclitude"], team_stat_data[homeTeam][playerid]["martyrdom"]]) for playerid in home_batter_order if not team_stat_data[homeTeam][playerid]["shelled"]])

    #away_running_data, home_running_data = List([List([team_stat_data[awayTeam][playerid]["laserlikeness"], team_stat_data[awayTeam][playerid]["baseThirst"], team_stat_data[awayTeam][playerid]["continuation"], team_stat_data[awayTeam][playerid]["groundFriction"], team_stat_data[awayTeam][playerid]["indulgence"]]) for playerid in away_batter_order if not team_stat_data[awayTeam][playerid]["shelled"]]), List([List([team_stat_data[homeTeam][playerid]["laserlikeness"], team_stat_data[homeTeam][playerid]["baseThirst"], team_stat_data[homeTeam][playerid]["continuation"], team_stat_data[homeTeam][playerid]["groundFriction"], team_stat_data[homeTeam][playerid]["indulgence"]]) for playerid in home_batter_order if not team_stat_data[homeTeam][playerid]["shelled"]])

    #away_team_stat_data, home_team_stat_data = List([away_defense_data, away_batting_data, away_running_data]), List([home_defense_data, home_batting_data, home_running_data])

    #awayPlayerAttrs, homePlayerAttrs = List([(List(team_stat_data[awayTeam][playerid]["attrs"]) if len(team_stat_data[awayTeam][playerid]["attrs"]) > 0 else List(["none", "none"])) for playerid in away_batter_order if not team_stat_data[awayTeam][playerid]["shelled"]]), List([(List(team_stat_data[homeTeam][playerid]["attrs"]) if len(team_stat_data[homeTeam][playerid]["attrs"]) > 0 else List(["none", "none"])) for playerid in home_batter_order if not team_stat_data[homeTeam][playerid]["shelled"]])

    away_pitcher_stat_data, home_pitcher_stat_data = (pitcher_stat_data[awayPitcher]["unthwackability"], pitcher_stat_data[awayPitcher]["ruthlessness"], pitcher_stat_data[awayPitcher]["overpowerment"], pitcher_stat_data[awayPitcher]["shakespearianism"], pitcher_stat_data[awayPitcher]["coldness"]), (pitcher_stat_data[homePitcher]["unthwackability"], pitcher_stat_data[homePitcher]["ruthlessness"], pitcher_stat_data[homePitcher]["overpowerment"], pitcher_stat_data[homePitcher]["shakespearianism"], pitcher_stat_data[homePitcher]["coldness"])

    awaypitcherAttrs = List(pitcher_stat_data[awayPitcher]["attrs"]) if (len(pitcher_stat_data[awayPitcher]["attrs"]) > 0) else List(["none", "none"]) 
    homepitcherAttrs = List(pitcher_stat_data[homePitcher]["attrs"]) if (len(pitcher_stat_data[homePitcher]["attrs"]) > 0) else List(["none", "none"])    

    #end_time = time.time()
    #print("Time in get mofo playerbased before njit methods = {}".format(end_time - start_time))

    #start = time.time()    
    away_team_batting, away_team_running, away_team_defense, awayPitcherStlats = calc_team_stlats(terms, away_batter_order, mods, awayAttrs, homeAttrs, awayMods, flooding, "away", away_team_stat_data, away_pitcher_stat_data, adjusted_stat_data_away, away_shelled, away_average_aa_impact, away_average_aaa_impact, away_high_pressure_mod)
    home_team_batting, home_team_running, home_team_defense, homePitcherStlats = calc_team_stlats(terms, home_batter_order, mods, awayAttrs, homeAttrs, homeMods, flooding, "home", home_team_stat_data, home_pitcher_stat_data, adjusted_stat_data_home, home_shelled, home_average_aa_impact, home_average_aaa_impact, home_high_pressure_mod)        

    if "aaa" in awayAttrs or "aa" in awayAttrs or "a" in awayAttrs or ("high_pressure" in awayAttrs and flooding):                
        away_team_batting, away_team_running, away_team_defense, awayPitcherStlats = blood_impact_calc(terms, away_batter_order, mods, flooding, "away", awayMods, away_team_batting, away_team_running, home_team_defense, homePitcherStlats, away_team_stat_data, home_team_stat_data, home_pitcher_stat_data, homepitcherAttrs, away_pitcher_stat_data, awaypitcherAttrs, awayPlayerAttrs, awayAttrs, homeAttrs, away_batter_order, adjusted_stat_data_away, away_average_aa_impact, away_average_aaa_impact, away_high_pressure_mod, adjustments, away_shelled, ruth_strike_adjust, innings=9)        
    if "aaa" in homeAttrs or "aa" in homeAttrs or "a" in homeAttrs or ("high_pressure" in homeAttrs and flooding):
        home_team_batting, home_team_running, home_team_defense, homePitcherStlats = blood_impact_calc(terms, home_batter_order, mods, flooding, "home", homeMods, home_team_batting, home_team_running, away_team_defense, awayPitcherStlats, home_team_stat_data, away_team_stat_data, away_pitcher_stat_data, awaypitcherAttrs, home_pitcher_stat_data, homepitcherAttrs, homePlayerAttrs, homeAttrs, awayAttrs, home_batter_order, adjusted_stat_data_home, home_average_aa_impact, home_average_aaa_impact, home_high_pressure_mod, adjustments, home_shelled, ruth_strike_adjust, innings=9) 
    away_score, away_bases_stolen, away_homers_hit, away_hits_hit, home_pitcher_ks, away_rbi = calc_team_score(mods, check_weather, awayMods, "away", away_team_batting, away_team_running, home_team_defense, homePitcherStlats, away_team_stat_data, home_team_stat_data, home_pitcher_stat_data, homepitcherAttrs, awayPlayerAttrs, awayAttrs, homeAttrs, away_batter_order, adjustments, ruth_strike_adjust, opp_score=0.0, innings=9, outs=3.0, runtime_solution=runtime_solution)    
    home_score, home_bases_stolen, home_homers_hit, home_hits_hit, away_pitcher_ks, home_rbi = calc_team_score(mods, check_weather, homeMods, "home", home_team_batting, home_team_running, away_team_defense, awayPitcherStlats, home_team_stat_data, away_team_stat_data, away_pitcher_stat_data, awaypitcherAttrs, homePlayerAttrs, homeAttrs, awayAttrs, home_batter_order, adjustments, ruth_strike_adjust, opp_score=away_score, innings=9, outs=3.0, runtime_solution=runtime_solution)    
    #end = time.time()
    #print("Elapsed time for njit methods = {}".format(end - start))
    #start = time.time()    
    away_stolen_bases = dict(zip(away_active_batters, away_bases_stolen))
    away_homers = dict(zip(away_active_batters, away_homers_hit))
    away_hits = dict(zip(away_active_batters, away_hits_hit))  
    home_stolen_bases = dict(zip(home_active_batters, home_bases_stolen))
    home_homers = dict(zip(home_active_batters, home_homers_hit))
    home_hits = dict(zip(home_active_batters, home_hits_hit))          
    #end = time.time()
    #print("Elapsed time to zip data = {}".format(end - start))

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

#def get_mofo(mods, awayPitcher, homePitcher, awayTeam, homeTeam, awayAttrs, homeAttrs, weather, team_stat_data, pitcher_stat_data, dict_terms, awayMods, homeMods, adjusted_stat_data, dict_adjustments, skip_mods=False, runtime_solution=False):
#    pitching_terms = List([dict_terms["unthwack_base_hit"], dict_terms["ruth_strike"], dict_terms["overp_homer"], dict_terms["overp_triple"], dict_terms["overp_double"], dict_terms["shakes_runner_advances"], dict_terms["cold_clutch_factor"]])
#    defense_terms = List([dict_terms["omni_base_hit"], dict_terms["watch_attempt_steal"], dict_terms["chasi_triple"], dict_terms["chasi_double"], dict_terms["anticap_caught_steal_base"], dict_terms["anticap_caught_steal_home"], dict_terms["tenacious_runner_advances"]])
#    batting_terms = List([dict_terms["path_connect"], dict_terms["trag_runner_advances"], dict_terms["thwack_base_hit"], dict_terms["div_homer"], dict_terms["moxie_swing_correct"], dict_terms["muscl_foul_ball"], dict_terms["muscl_triple"], dict_terms["muscl_double"], dict_terms["martyr_sacrifice"]])
#    running_terms = List([dict_terms["laser_attempt_steal"], dict_terms["laser_caught_steal_base"], dict_terms["laser_caught_steal_home"], dict_terms["laser_runner_advances"], dict_terms["baset_attempt_steal"], dict_terms["baset_caught_steal_home"], dict_terms["cont_triple"], dict_terms["cont_double"], dict_terms["ground_triple"], dict_terms["indulg_runner_advances"]])
#    terms = List([pitching_terms, defense_terms, batting_terms, running_terms])
#    return get_mofo_playerbased(mods, awayPitcher, homePitcher, awayTeam, homeTeam, awayAttrs, homeAttrs, weather, team_stat_data, pitcher_stat_data, terms, awayMods, homeMods, adjusted_stat_data, dict_adjustments, skip_mods, runtime_solution)

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
    away_event_terms = List([awayMods["plus_hit_minus_homer"], awayMods["plus_hit_minus_foul"], awayMods["plus_groundout_minus_hardhit"], awayMods["plus_contact_minus_hardhit"], awayMods["plus_strike"], awayMods["plus_hardhit"], awayMods["minus_stealsuccess"], awayMods["minus_doubleplay"], awayMods["minus_stealattempt"], awayMods["minus_hit"], awayMods["minus_homer"]])
    home_event_terms = List([homeMods["plus_hit_minus_homer"], homeMods["plus_hit_minus_foul"], homeMods["plus_groundout_minus_hardhit"], homeMods["plus_contact_minus_hardhit"], homeMods["plus_strike"], homeMods["plus_hardhit"], homeMods["minus_stealsuccess"], homeMods["minus_doubleplay"], homeMods["minus_stealattempt"], homeMods["minus_hit"], homeMods["minus_homer"]])

    away_hype_pitching_terms = List([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    home_hype_pitching_terms = List([homeMods["unthwack_base_hit"], homeMods["ruth_strike"], homeMods["overp_homer"], homeMods["overp_triple"], homeMods["overp_double"], homeMods["shakes_runner_advances"]])
    
    away_hype_defense_terms = List([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    home_hype_defense_terms = List([homeMods["omni_base_hit"], homeMods["tenacious_runner_advances"], homeMods["watch_attempt_steal"], homeMods["anticap_caught_steal_base"], homeMods["anticap_caught_steal_home"], homeMods["chasi_triple"], homeMods["chasi_double"]])

    away_hype_batting_terms = List([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    home_hype_batting_terms = List([homeMods["trag_runner_advances"], homeMods["path_connect"], homeMods["thwack_base_hit"], homeMods["div_homer"], homeMods["moxie_swing_correct"], homeMods["muscl_foul_ball"], homeMods["muscl_triple"], homeMods["muscl_double"], homeMods["martyr_sacrifice"]])
    
    away_hype_running_terms = List([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    home_hype_running_terms = List([homeMods["laser_attempt_steal"], homeMods["laser_caught_steal_base"], homeMods["laser_caught_steal_home"], homeMods["laser_runner_advances"], homeMods["baset_attempt_steal"], homeMods["baset_caught_steal_home"], homeMods["cont_triple"], homeMods["cont_double"], homeMods["ground_triple"], homeMods["indulg_runner_advances"]])

    awayMods_list, homeMods_list = List([away_hype_pitching_terms, away_hype_defense_terms, away_hype_batting_terms, away_hype_running_terms, away_event_terms]), List([home_hype_pitching_terms, home_hype_defense_terms, home_hype_batting_terms, home_hype_running_terms, home_event_terms])           
    
    return awayMods_list, homeMods_list

def setup_playerbased(weather, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, team_stat_data, pitcher_stat_data):
    terms_url = os.getenv("MOFO_TERMS")
    dict_terms, _ = helpers.load_terms(terms_url)
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
    adjustments = instantiate_adjustments(dict_terms, halfterms)
    pitching_terms = List([dict_terms["unthwack_base_hit"], dict_terms["ruth_strike"], dict_terms["overp_homer"], dict_terms["overp_triple"], dict_terms["overp_double"], dict_terms["shakes_runner_advances"], dict_terms["cold_clutch_factor"]])
    defense_terms = List([dict_terms["omni_base_hit"], dict_terms["watch_attempt_steal"], dict_terms["chasi_triple"], dict_terms["chasi_double"], dict_terms["anticap_caught_steal_base"], dict_terms["anticap_caught_steal_home"], dict_terms["tenacious_runner_advances"]])
    batting_terms = List([dict_terms["path_connect"], dict_terms["trag_runner_advances"], dict_terms["thwack_base_hit"], dict_terms["div_homer"], dict_terms["moxie_swing_correct"], dict_terms["muscl_foul_ball"], dict_terms["muscl_triple"], dict_terms["muscl_double"], dict_terms["martyr_sacrifice"]])
    running_terms = List([dict_terms["laser_attempt_steal"], dict_terms["laser_caught_steal_base"], dict_terms["laser_caught_steal_home"], dict_terms["laser_runner_advances"], dict_terms["baset_attempt_steal"], dict_terms["baset_caught_steal_home"], dict_terms["cont_triple"], dict_terms["cont_double"], dict_terms["ground_triple"], dict_terms["indulg_runner_advances"]])    
    terms = List([pitching_terms, defense_terms, batting_terms, running_terms])
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


#def calculate(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, awayAttrs, homeAttrs,
#              day, weather, skip_mods=False):
#    terms, awayMods, homeMods = setup(weather, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, team_stat_data, pitcher_stat_data)
#    return get_mofo(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, terms, awayMods,
#                    homeMods, skip_mods=skip_mods)


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
