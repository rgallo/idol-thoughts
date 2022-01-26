from __future__ import division
from __future__ import print_function

import collections
import copy
import datetime
import time

import helpers
import math
import numpy as np

from numba import njit, float64
from numba.typed import List
from helpers import StlatTerm, ParkTerm, geomean
import os
#from numba.core.registry import cpu_target
#from numba.core.unsafe.nrt import NRT_get_api
#from numba.core.runtime.nrt import rtsys
#cpu_target.target_context
import tracemalloc
tracemalloc.start()    

MODS_CALCED_DIFFERENTLY = {"aaa", "aa", "a", "fiery", "base_instincts", "o_no", "electric", "h20", "0", "acidic", "love", "high_pressure", "psychic"}
#GAMES_PROCESSED = 0
#SNAPSHOT = tracemalloc.take_snapshot()

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

#@njit
#def calc_player(term, stlatvalue, hype):     
#    return float(term.calc(stlatvalue) * (1.0 * hype))    

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

@njit
def log_transform(value, base):                                
    return float64(1.0 / (1.0 + (base ** (-1.0 * value))))

@njit
def prob_adjust(prob, multiplier):   
    if prob == 1.0:
        return prob    
    return float64(((prob / (1.0 - prob)) * (1.0 + multiplier)) / (1.0 + ((prob / (1.0 - prob)) * (1.0 + multiplier))))

@njit
def calc_strikeout_walked(strike_looking, strike_swinging, ball_chance, foul_ball_chance, strike_count, ball_count, base_hit_chance, caught_out_chance):               
    strikeout, walked, base_hit, caught_out = float64(0.0), float64(0.0), float64(0.0), float64(0.0)
    strikes = int(strike_count)
    max_balls = int(ball_count)
    foul_ball_count = max(strikes - 1, 0)    
    maximum_pitches = strikes + foul_ball_count + max_balls + 1     
    
    for foul_balls in range(0, maximum_pitches + 1):
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
    factor = float64(strikeout + walked + base_hit + caught_out)
    strikeout *= 1.0 / factor
    walked *= 1.0 / factor
    base_hit *= 1.0 / factor
    caught_out *= 1.0 / factor
    
    return strikeout, walked, base_hit, caught_out

@njit
def calc_probs_from_stats(mods, active_batters, event_mods, sorted_bat_values, sorted_run_values, opp_stat_data, pitcher_stat_data, pitcherAttrs, teamPlayerAttrs, battingAttrs, oppAttrs, adjustments, ruth_strike_adjust, blood_calc, outs):   
    blood_count = float64(12.0)
    a_blood_multiplier = 1.0 / blood_count        

    (unthwack_base_hit, ruth_strike, overp_homer, overp_triple, overp_double, shakes_runner_advances, cold_clutch_factor) = pitcher_stat_data

    (love_strikeout, love_easypitch, basic_multiplier, fiery_multiplier, electric_multiplier, psychic_walktrick, psychic_striketrick, acidic_multiplier) = mods
        
    log_transform_base = math.e   

    strike_log = float64(ruth_strike - ruth_strike_adjust)
    strike_prob = log_transform(strike_log, log_transform_base)        
    strike_chance = prob_adjust(strike_prob, event_mods[4])            
    
    parkmods = (event_mods[3], event_mods[1], event_mods[2], event_mods[7], event_mods[8], event_mods[6], event_mods[4], event_mods[5], event_mods[10], event_mods[9])    

    steal_mod = np.zeros((20))
    score_multiplier = np.zeros((20))
    caught_out_chance = np.zeros((20))
    walk_chance = np.zeros((20))
    strike_out_chance = np.zeros((20))

    attempt_steal_chance = np.zeros((20))
    caught_steal_base_chance = np.zeros((20))
    caught_steal_home_chance = np.zeros((20))

    homerun_chance = np.zeros((20))    
    triple_chance = np.zeros((20))
    double_chance = np.zeros((20))
    single_chance = np.zeros((20))
    caught_steal_outs = np.zeros((20))
    on_base_chance = np.zeros((20))    

    sacrifice_chance = np.zeros((20))
    runner_advance_chance = np.zeros((20))
    average_on_first_position = np.zeros((20))
    average_on_second_position = np.zeros((20))
    average_on_third_position = np.zeros((20))

    strike_count, ball_count, average_strikes, average_balls = float64(0.0), float64(0.0), float64(0.0), float64(0.0)    

    swing_correct_chance, swing_strike_blood_factors, swing_strike_chance, swing_ball_chance, base_connect_chance = float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0)
    connect_chance, base_hit_chance, strike_looking_chance, strike_swinging_chance, ball_chance, foul_ball_chance = float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0)
    caught_out_prob, factor, strikeout, walked, base_hit, caught_out, no_balls, walked_psychic, attempt_steal_prob = float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0)
    caught_steal_base_prob, caught_steal_home_prob, homerun_prob, triple_prob, double_prob, single_prob = float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0)               
    
    homerun_multipliers = np.ones((20))
    hit_modifier = np.ones((20))

    homerun_multipliers[19] = float64(-1.0 * cold_clutch_factor)
    hit_modifier[19] = float64(-1.0)
    score_multiplier[19] = float64(2.0)
    steal_mod[19] = float64(20.0)
    
    score_mult_pitcher = float64(1.0 * (2.0 if "magnify_2x" in pitcherAttrs else 1.0) * (3.0 if "magnify_3x" in pitcherAttrs else 1.0) * (4.0 if "magnify_4x" in pitcherAttrs else 1.0) * (5.0 if "magnify_5x" in pitcherAttrs else 1.0))    
    strike_mod = float64((fiery_multiplier if "fiery" in oppAttrs else 0.0) + (love_strikeout if "love" in oppAttrs else 0.0) + (((fiery_multiplier * a_blood_multiplier) + (love_strikeout * a_blood_multiplier)) if "a" in oppAttrs and not blood_calc else 0.0) - (electric_multiplier if "electric" in battingAttrs else 0.0) - ((electric_multiplier * a_blood_multiplier) if "a" in battingAttrs and not blood_calc else 0.0)  )
    walk_to_strike = float64((psychic_striketrick if "psychic" in oppAttrs else 0.0) + ((psychic_striketrick * a_blood_multiplier) if "a" in oppAttrs and not blood_calc else 0.0))    
    score_mod = float64((acidic_multiplier if "acidic" in oppAttrs else 0.0) + ((acidic_multiplier * a_blood_multiplier) if "a" in oppAttrs and not blood_calc else 0.0))    
    strike_to_walk = float64((psychic_walktrick if "psychic" in battingAttrs else 0.0) + ((psychic_walktrick * a_blood_multiplier) if "a" in battingAttrs and not blood_calc else 0.0))    
    walk_buff = float64((love_easypitch if "love" in battingAttrs else 0.0) + ((love_easypitch * a_blood_multiplier) if "a" in battingAttrs and not blood_calc else 0.0))
    walk_mod = float64((basic_multiplier if "base_instincts" in battingAttrs else 0.0) + ((basic_multiplier * a_blood_multiplier) if "a" in battingAttrs and not blood_calc else 0.0))
    
    for playerid in range(0, active_batters):                    
        homerun_multipliers[playerid] *= float64(-1.0 if "underhanded" in pitcherAttrs else 1.0)
        homerun_multipliers[playerid] *= float64(-1.0 if "subtractor" in teamPlayerAttrs[playerid] else 1.0)
        homerun_multipliers[playerid] *= float64(-1.0 if "underachiever" in teamPlayerAttrs[playerid] else 1.0)
        hit_modifier[playerid] *= float64(-1.0 if "subtractor" in teamPlayerAttrs[playerid] else 1.0)
        strike_count = float64(4.0 if (("extra_strike" in battingAttrs) or ("extra_strike" in teamPlayerAttrs[playerid])) else 3.0)
        strike_count -= float64(1.0 if "flinch" in teamPlayerAttrs[playerid] else float64(0.0))
        ball_count = float64(3.0 if (("walk_in_the_park" in battingAttrs) or ("walk_in_the_park" in teamPlayerAttrs[playerid])) else 4.0)    
        steal_mod[playerid] = float64(20.0 if ("blaserunning" in battingAttrs or "blaserunning" in teamPlayerAttrs[playerid]) else float64(0.0))
        average_strikes = float64(((strike_count - 1.0) / 2.0) if "skipping" in teamPlayerAttrs[playerid] else 0.0)
        average_balls = float64(((ball_count - 1.0) / 2.0) if "skipping" in teamPlayerAttrs[playerid] else 0.0)
        strike_count = float64(max(strike_count - average_strikes, 1.0))
        ball_count = float64(max(ball_count - average_balls, 1.0))        
        score_multiplier[playerid] = score_mult_pitcher * (2.0 if "magnify_2x" in teamPlayerAttrs[playerid] else 1.0) * (3.0 if "magnify_3x" in teamPlayerAttrs[playerid] else 1.0) * (4.0 if "magnify_4x" in teamPlayerAttrs[playerid] else 1.0) * (5.0 if "magnify_5x" in teamPlayerAttrs[playerid] else 1.0)        
        
        swing_correct_chance = log_transform((sorted_bat_values[playerid, 4] - adjustments[0]), log_transform_base)        
        swing_strike_blood_factors = float64(((1.0 / outs) if ("h20" in battingAttrs or "h20" in teamPlayerAttrs[playerid]) else float64(0.0)) + ((strike_chance / (strike_count + ball_count)) if (("0" in battingAttrs or "0" in teamPlayerAttrs[playerid]) and "skipping" not in teamPlayerAttrs[playerid]) else float64(0.0)))
        if "a" in battingAttrs and not blood_calc:
            swing_strike_blood_factors += float64(((1.0 / outs) * a_blood_multiplier) + (((strike_chance / (strike_count + ball_count)) * a_blood_multiplier) if "skipping" not in teamPlayerAttrs[playerid] else float64(0.0)))
        swing_strike_chance = (swing_correct_chance + swing_strike_blood_factors) * strike_chance        
        swing_ball_chance = float64(((1.0 - swing_correct_chance) * (1.0 - strike_chance)) - (((1.0 - strike_chance) ** ball_count) if "flinch" in teamPlayerAttrs[playerid] else float64(0.0)))
        
        connect_chance = log_transform((adjustments[1] - sorted_bat_values[playerid, 0]), log_transform_base)
        connect_chance = prob_adjust(connect_chance, parkmods[0])        
        connect_chance = max(connect_chance, float64(0.0)) * max(swing_strike_chance, float64(0.0))       
        
        strike_looking_chance = (1.0 - swing_correct_chance) * strike_chance
        strike_swinging_chance = (1.0 - connect_chance) + swing_ball_chance
        ball_chance = 1.0 - max(swing_ball_chance, float64(0.0))
        
        strike_looking_chance += (abs(strike_looking_chance) + abs(strike_swinging_chance) + abs(connect_chance) + abs(ball_chance)) if (strike_looking_chance <= float64(0.0) or strike_swinging_chance <= float64(0.0) or connect_chance <= float64(0.0) or ball_chance <= float64(0.0)) else float64(0.0)
        strike_swinging_chance += (abs(strike_looking_chance) + abs(strike_swinging_chance) + abs(connect_chance) + abs(ball_chance)) if (strike_looking_chance <= float64(0.0) or strike_swinging_chance <= float64(0.0) or connect_chance <= float64(0.0) or ball_chance <= float64(0.0)) else float64(0.0)
        connect_chance += (abs(strike_looking_chance) + abs(strike_swinging_chance) + abs(connect_chance) + abs(ball_chance)) if (strike_looking_chance <= float64(0.0) or strike_swinging_chance <= float64(0.0) or connect_chance <= float64(0.0) or ball_chance <= float64(0.0)) else float64(0.0)
        ball_chance += (abs(strike_looking_chance) + abs(strike_swinging_chance) + abs(connect_chance) + abs(ball_chance)) if (strike_looking_chance <= float64(0.0) or strike_swinging_chance <= float64(0.0) or connect_chance <= float64(0.0) or ball_chance <= float64(0.0)) else float64(0.0)
        #just always do this rather than running an if?
        factor = 1.0 / (strike_looking_chance + strike_swinging_chance + connect_chance + ball_chance)
        strike_looking_chance *= factor
        strike_swinging_chance *= factor
        connect_chance *= factor
        ball_chance *= factor

        base_hit_chance = log_transform((sorted_bat_values[playerid, 2] - pitcher_stat_data[0] - opp_stat_data[0] - (adjustments[2] - adjustments[3] - adjustments[4])), log_transform_base)
        base_hit_chance *= connect_chance

        foul_ball_chance = log_transform((sorted_bat_values[playerid, 5] - adjustments[5]), log_transform_base)         
        foul_ball_chance = prob_adjust(foul_ball_chance, -parkmods[1])        
        foul_ball_chance *= (connect_chance - base_hit_chance)
        caught_out_prob = connect_chance - foul_ball_chance - base_hit_chance       
        caught_out_prob = (prob_adjust(caught_out_prob, parkmods[2]) + prob_adjust(caught_out_prob, -parkmods[3])) / 2.0
        
        base_hit_chance += (abs(base_hit_chance) + abs(foul_ball_chance) + abs(caught_out_prob)) if (base_hit_chance < float64(0.0) or foul_ball_chance < float64(0.0) or caught_out_prob < float64(0.0)) else float64(0.0)
        foul_ball_chance += (abs(base_hit_chance) + abs(foul_ball_chance) + abs(caught_out_prob)) if (base_hit_chance < float64(0.0) or foul_ball_chance < float64(0.0) or caught_out_prob < float64(0.0)) else float64(0.0)
        caught_out_prob += (abs(base_hit_chance) + abs(foul_ball_chance) + abs(caught_out_prob)) if (base_hit_chance < float64(0.0) or foul_ball_chance < float64(0.0) or caught_out_prob < float64(0.0)) else float64(0.0)
        
        factor = connect_chance / (base_hit_chance + foul_ball_chance + caught_out_prob)
        base_hit_chance *= factor
        foul_ball_chance *= factor
        caught_out_prob *= factor

        strikeout, walked, base_hit, caught_out = calc_strikeout_walked(strike_looking_chance, strike_swinging_chance, ball_chance, foul_ball_chance, strike_count, ball_count, base_hit_chance, caught_out_prob)        

        strikeout += strike_mod
        walked += walk_buff

        #probability of no balls happening is the probability that every strike is a strike AND every ball is swung at
        no_balls = float64((min(((strike_chance * (1.0 - swing_correct_chance)) + (strike_chance * swing_correct_chance * (1.0 - connect_chance))) * ((1.0 - swing_correct_chance) * (1.0 - strike_chance)), 1.0)) * (a_blood_multiplier if "a" in battingAttrs else 1.0))
        strikeout *= float64((1.0 - no_balls) if ("o_no" in battingAttrs or "o_no" in teamPlayerAttrs[playerid] or ("a" in battingAttrs and not blood_calc)) else 1.0)        
            
        caught_out_chance[playerid] = caught_out
        
        walked_psychic = walked + (strikeout * strike_to_walk) - (walked * walk_to_strike)
        strikeout += (walked * walk_to_strike) - (strikeout * strike_to_walk)
        walked = walked_psychic        
        walked += (abs(strikeout) * 2.0) if strikeout < float64(0.0) else 0.0
        strikeout += (abs(strikeout) * 2.0) if strikeout < float64(0.0) else 0.0
        strikeout += (abs(walked) * 2.0) if walked < float64(0.0) else 0.0
        walked += (abs(walked) * 2.0) if walked < float64(0.0) else 0.0        
        walk_chance[playerid] = walked
        strike_out_chance[playerid] = strikeout

        walk_chance[playerid] += (abs(walk_chance[playerid]) + abs(base_hit) + abs(strike_out_chance[playerid]) + abs(caught_out_chance[playerid])) if (walk_chance[playerid] < float64(0.0) or base_hit < float64(0.0) or strike_out_chance[playerid] < float64(0.0) or caught_out_chance[playerid] < float64(0.0)) else 0.0
        base_hit += (abs(walk_chance[playerid]) + abs(base_hit) + abs(strike_out_chance[playerid]) + abs(caught_out_chance[playerid])) if (walk_chance[playerid] < float64(0.0) or base_hit < float64(0.0) or strike_out_chance[playerid] < float64(0.0) or caught_out_chance[playerid] < float64(0.0)) else 0.0
        strike_out_chance[playerid] += (abs(walk_chance[playerid]) + abs(base_hit) + abs(strike_out_chance[playerid]) + abs(caught_out_chance[playerid])) if (walk_chance[playerid] < float64(0.0) or base_hit < float64(0.0) or strike_out_chance[playerid] < float64(0.0) or caught_out_chance[playerid] < float64(0.0)) else 0.0
        caught_out_chance[playerid] += (abs(walk_chance[playerid]) + abs(base_hit) + abs(strike_out_chance[playerid]) + abs(caught_out_chance[playerid])) if (walk_chance[playerid] < float64(0.0) or base_hit < float64(0.0) or strike_out_chance[playerid] < float64(0.0) or caught_out_chance[playerid] < float64(0.0)) else 0.0
        #the sum of these events (which would be one or the other or the other etc.) must be one, as they are everything that can happen on a plate appearance        
        #if the sum is not one, correct all probabilities such that the sum will be equal to 1.0, which will preserve the relative probabilities for all events        
        #just always do this rather than running an if?
        factor = 1.0 / (walk_chance[playerid] + base_hit + strike_out_chance[playerid] + caught_out_chance[playerid])
        walk_chance[playerid] *= factor
        strike_out_chance[playerid] *= factor
        base_hit *= factor
        caught_out_chance[playerid] *= factor                
        
        attempt_steal_prob = log_transform((sorted_run_values[playerid, 4] + sorted_run_values[playerid, 0] - opp_stat_data[1] - (adjustments[6] + adjustments[7] - adjustments[8])), log_transform_base)
        attempt_steal_chance[playerid] = prob_adjust(attempt_steal_prob, -parkmods[4])
        
        caught_steal_base_prob = log_transform((opp_stat_data[4] - sorted_run_values[playerid, 1] - (adjustments[9] - adjustments[10])), log_transform_base)            
        caught_steal_base_chance[playerid] = prob_adjust(caught_steal_base_prob, parkmods[5])
        
        caught_steal_home_prob = log_transform((opp_stat_data[5] - sorted_run_values[playerid, 5] - sorted_run_values[playerid, 2] - (adjustments[11] + adjustments[12] + adjustments[13])), log_transform_base)        
        caught_steal_home_chance[playerid] = prob_adjust(caught_steal_home_prob, parkmods[5])
        
        homerun_prob = log_transform((sorted_bat_values[playerid, 3] - pitcher_stat_data[2] - (adjustments[14] - adjustments[15])), log_transform_base)      
        homerun_prob = (prob_adjust(homerun_prob, -parkmods[6]) + prob_adjust(homerun_prob, -parkmods[2]) + prob_adjust(homerun_prob, -parkmods[0]) + prob_adjust(homerun_prob, parkmods[7]) + prob_adjust(homerun_prob, -parkmods[8])) / 5.0
        homerun_chance[playerid] = homerun_prob * base_hit
        
        triple_prob = log_transform((sorted_bat_values[playerid, 6] + sorted_run_values[playerid, 8] + sorted_run_values[playerid, 6] - pitcher_stat_data[3] - opp_stat_data[2] - (adjustments[16] + adjustments[17] + adjustments[18] - adjustments[19] - adjustments[20])), log_transform_base)    
        triple_prob = (prob_adjust(triple_prob, parkmods[6]) + prob_adjust(triple_prob, parkmods[1]) + prob_adjust(triple_prob, -parkmods[2]) + prob_adjust(triple_prob, -parkmods[0]) + prob_adjust(triple_prob, parkmods[7]) + prob_adjust(triple_prob, -parkmods[9])) / 6.0            
        triple_chance[playerid] = triple_prob * base_hit
        
        double_prob = log_transform((sorted_bat_values[playerid, 7] + sorted_run_values[playerid, 7] - pitcher_stat_data[4] - opp_stat_data[3] - (adjustments[21] + adjustments[22] - adjustments[23] - adjustments[24])), log_transform_base)    
        double_prob = (prob_adjust(double_prob, parkmods[6]) + prob_adjust(double_prob, parkmods[1]) + prob_adjust(double_prob, -parkmods[2]) + prob_adjust(double_prob, -parkmods[0]) + prob_adjust(double_prob, parkmods[7]) + prob_adjust(double_prob, -parkmods[9])) / 6.0    
        double_chance[playerid] = double_prob * base_hit

        single_prob = base_hit - triple_chance[playerid] - double_chance[playerid] - homerun_chance[playerid]   
        single_prob = ((prob_adjust(single_prob, -parkmods[6]) + prob_adjust(single_prob, -parkmods[1]) + prob_adjust(single_prob, parkmods[9])) / 3.0) if single_prob < float64(0.0) else ((prob_adjust(single_prob, parkmods[6]) + prob_adjust(single_prob, parkmods[1]) + prob_adjust(single_prob, -parkmods[9])) / 3.0)        
        single_chance[playerid] = single_prob
        
        single_chance[playerid] += (abs(single_chance[playerid]) + abs(triple_chance[playerid]) + abs(double_chance[playerid]) + abs(homerun_chance[playerid])) if (single_chance[playerid] <= float64(0.0) or triple_chance[playerid] <= float64(0.0) or double_chance[playerid] <= float64(0.0) or homerun_chance[playerid] <= float64(0.0)) else 0.0
        triple_chance[playerid] += (abs(single_chance[playerid]) + abs(triple_chance[playerid]) + abs(double_chance[playerid]) + abs(homerun_chance[playerid])) if (single_chance[playerid] <= float64(0.0) or triple_chance[playerid] <= float64(0.0) or double_chance[playerid] <= float64(0.0) or homerun_chance[playerid] <= float64(0.0)) else 0.0
        double_chance[playerid] += (abs(single_chance[playerid]) + abs(triple_chance[playerid]) + abs(double_chance[playerid]) + abs(homerun_chance[playerid])) if (single_chance[playerid] <= float64(0.0) or triple_chance[playerid] <= float64(0.0) or double_chance[playerid] <= float64(0.0) or homerun_chance[playerid] <= float64(0.0)) else 0.0
        homerun_chance[playerid] += (abs(single_chance[playerid]) + abs(triple_chance[playerid]) + abs(double_chance[playerid]) + abs(homerun_chance[playerid])) if (single_chance[playerid] <= float64(0.0) or triple_chance[playerid] <= float64(0.0) or double_chance[playerid] <= float64(0.0) or homerun_chance[playerid] <= float64(0.0)) else 0.0
        #normalize these to sum to base hit chance
        factor = base_hit / (single_chance[playerid] + triple_chance[playerid] + double_chance[playerid] + homerun_chance[playerid])
        single_chance[playerid] *= factor
        triple_chance[playerid] *= factor
        double_chance[playerid] *= factor
        homerun_chance[playerid] *= factor                        
        
        on_base_chance[playerid] = min(single_chance[playerid] + double_chance[playerid] + triple_chance[playerid] + walk_chance[playerid], 1.0)
        
        #runners advancing is tricky, since we have to do this based on runners being on base already, but use the batter's martyrdom for sacrifices        
        sacrifice_chance[playerid] = log_transform((sorted_bat_values[playerid, 8] - adjustments[25]), log_transform_base) * caught_out_chance[playerid]
        
        runner_advance_chance[playerid] = log_transform((sorted_run_values[playerid, 3] + sorted_run_values[playerid, 9] - sorted_bat_values[playerid, 1] - pitcher_stat_data[5] - opp_stat_data[6] - (adjustments[26] + adjustments[27] - adjustments[28] - adjustments[29] - adjustments[30])), log_transform_base)
        average_on_first_position[playerid] = min(single_chance[playerid] + (walk_chance[playerid] * (1.0 - walk_mod)), 1.0)
        average_on_second_position[playerid] = min(double_chance[playerid] + (walk_chance[playerid] * walk_mod), 1.0)
        average_on_third_position[playerid] = min(triple_chance[playerid] + (walk_chance[playerid] * walk_mod), 1.0)

        #need to approximate caught stealing outs for blood calcing        
        caught_steal_outs[playerid] = min((caught_steal_base_chance[playerid] * attempt_steal_chance[playerid] * ((2.0 * average_on_first_position[playerid]) + average_on_second_position[playerid])) + (caught_steal_home_chance[playerid] * attempt_steal_chance[playerid] * (average_on_first_position[playerid] + average_on_second_position[playerid] + average_on_third_position[playerid])), 1.0)

    return runner_advance_chance, caught_out_chance, sacrifice_chance, score_mod, hit_modifier, homerun_multipliers, score_multiplier, attempt_steal_chance, walk_chance, strike_out_chance, caught_steal_base_chance, caught_steal_home_chance, homerun_chance, triple_chance, double_chance, single_chance, caught_steal_outs, on_base_chance, average_on_first_position, average_on_second_position, average_on_third_position, steal_mod, walk_mod

@njit
def simulate_game(active_batters, battingAttrs, teamPlayerAttrs, opp_score, is_home, outs, homerun_chance, triple_chance, double_chance, single_chance, walk_chance, walk_mod, sacrifice_chance, runner_advance_chance, average_on_first, average_on_second, average_on_third, reverb_weather, score_mod, strike_out_chance, caught_out_chance, caught_steal_base_chance, caught_steal_home_chance, attempt_steal_chance, homerun_multipliers, hit_modifier, steal_mod, score_multiplier):        
    maximum_inning_atbats = 25
    current_innings, atbats_in_inning = 0, 0      
    probable_atbat = float64(1.0)
    inning_score, inning_rbi = float64(0.0), float64(0.0)
    runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = float64(0.0), float64(0.0), float64(0.0), float64(0.0)
    runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = float64(0.0), float64(0.0), float64(0.0), float64(0.0)    
    strikeouts, no_outs = float64(0.0), float64(1.0)
    starting_player = 0        
    team_score = float64(101.0 if ("home_field" in battingAttrs and is_home) else float64(1.0))
    team_rbi = team_score            
    total_innings = 8 if is_home else 9
    game_complete = False
    #inform the compiler that player_score could go negative?
    player_score = float64(-1.0)
    #inform the compiler that team_score could go negative?
    team_score *= float64(-1.0)
    #switch it back
    team_score *= float64(-1.0)
    team_score -= float64(1.0)
    
    batter_atbats = 0        
    
    homerun_score, triple_runners_score, double_runners_score, single_runners_score, runners_advance_score, walking_score = float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0)
    player_rbi, player_outs = float64(0.0), float64(0.0)
    steal_runners_on_second, steal_runners_on_third, steal_runners_on_fourth, steal_base_success_rate, steal_home_success_rate = float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0)
    steal_second_opportunities, steal_third_opportunities, steal_fourth_opportunities, steal_home_opportunities, steal_base_opportunities = float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0)
    steal_outs, current_batter_no_out, current_batter_out, one_out, two_out = float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0)    
    
    one_outs, two_outs = List([1.0, 1.0]), List([1.0, 1.0])        
    
    homers, hits, stolen_bases = np.zeros((20)), np.zeros((20)), np.zeros((20))
    while not game_complete:
        while current_innings < total_innings:                
            for playerid in range(starting_player, active_batters):                                                
                extra_base = (("extra_base" in battingAttrs) or ("extra_base" in teamPlayerAttrs[playerid]))
                reverberating = (("reverberating" in teamPlayerAttrs[playerid]) or ("repeating" in teamPlayerAttrs[playerid] and reverb_weather))
                if not extra_base:
                    homerun_score = ((100.0 - (10.0 * score_mod)) * (1.0 + runners_on_first + runners_on_second + runners_on_third)) * homerun_chance[playerid] * probable_atbat
                    triple_runners_score = ((100.0 - (10.0 * score_mod)) * (runners_on_first + runners_on_second + runners_on_third)) * triple_chance[playerid] * probable_atbat
                    double_runners_score = ((100.0 - (10.0 * score_mod)) * (runners_on_second + runners_on_third)) * double_chance[playerid] * probable_atbat
                    single_runners_score = ((100.0 - (10.0 * score_mod)) * runners_on_third) * single_chance[playerid] * probable_atbat
                    runners_advance_score = 100.0 * runners_on_third * sacrifice_chance[playerid] * probable_atbat
                    walking_score = 100.0 * ((runners_on_third * walk_chance[playerid]) + (runners_on_second * (walk_chance[playerid] * walk_mod)) + (runners_on_first * (walk_chance[playerid] * walk_mod))) * probable_atbat
                else:
                    homerun_score = ((100.0 - (10.0 * score_mod)) * (1.0 + runners_on_first + runners_on_second + runners_on_third + runners_on_fourth)) * homerun_chance[playerid] * probable_atbat
                    triple_runners_score = ((100.0 - (10.0 * score_mod)) * (runners_on_fourth + runners_on_second + runners_on_third)) * triple_chance[playerid] * probable_atbat
                    double_runners_score = ((100.0 - (10.0 * score_mod)) * (runners_on_fourth + runners_on_third)) * double_chance[playerid] * probable_atbat
                    single_runners_score = ((100.0 - (10.0 * score_mod)) * runners_on_fourth) * single_chance[playerid] * probable_atbat
                    runners_advance_score = 100.0 * runners_on_fourth * sacrifice_chance[playerid] * probable_atbat
                    walking_score = 100.0 * ((runners_on_fourth * walk_chance[playerid]) + (runners_on_third * walk_chance[playerid] * walk_mod) + (runners_on_second * walk_chance[playerid] * walk_mod) + (runners_on_first * walk_chance[playerid] * walk_mod)) * probable_atbat
                    runners_on_fourth, runner_advance_fourth = calc_runners_on(runners_on_fourth, runner_advance_fourth, runners_on_third, runner_advance_third, runners_on_second, runner_advance_second, runners_on_first, runner_advance_first, single_chance[playerid], double_chance[playerid], triple_chance[playerid], homerun_chance[playerid], sacrifice_chance[playerid], caught_out_chance[playerid], walk_chance[playerid], walk_mod, float64(0.0), runner_advance_chance[playerid])
                runners_on_third, runner_advance_third = calc_runners_on(runners_on_third, runner_advance_third, runners_on_second, runner_advance_second, runners_on_first, runner_advance_first, float64(0.0), float64(0.0), single_chance[playerid], double_chance[playerid], triple_chance[playerid], homerun_chance[playerid], sacrifice_chance[playerid], caught_out_chance[playerid], walk_chance[playerid], walk_mod, average_on_third[playerid], runner_advance_chance[playerid])
                runners_on_second, runner_advance_second = calc_runners_on(runners_on_second, runner_advance_second, runners_on_first, runner_advance_first, float64(0.0), float64(0.0), float64(0.0), float64(0.0), single_chance[playerid], double_chance[playerid], triple_chance[playerid], homerun_chance[playerid], sacrifice_chance[playerid], caught_out_chance[playerid], walk_chance[playerid], walk_mod, average_on_second[playerid], runner_advance_chance[playerid])
                runners_on_first, runner_advance_first = calc_runners_on(runners_on_first, runner_advance_first, float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0), float64(0.0), single_chance[playerid], double_chance[playerid], triple_chance[playerid], homerun_chance[playerid], sacrifice_chance[playerid], caught_out_chance[playerid], walk_chance[playerid], walk_mod, average_on_first[playerid], runner_advance_chance[playerid])
                player_rbi = runners_advance_score + walking_score + homerun_score + triple_runners_score + double_runners_score + single_runners_score
                player_score = (runners_advance_score + walking_score + (homerun_score * homerun_multipliers[playerid]) + ((triple_runners_score + double_runners_score + single_runners_score) * hit_modifier[playerid])) * score_multiplier[playerid]
                homers[playerid] += homerun_chance[playerid] * probable_atbat
                hits[playerid] += triple_chance[playerid] + double_chance[playerid] + single_chance[playerid] * probable_atbat            
                player_outs = strike_out_chance[playerid] + caught_out_chance[playerid]
                strikeouts += strike_out_chance[playerid] * probable_atbat            
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
                steal_second_opportunities = average_on_first[playerid] * (1.0 - min(steal_runners_on_second - average_on_second[playerid], float64(0.0)))
                #steal third
                steal_third_opportunities = (steal_second_opportunities * (1.0 - min(steal_runners_on_third - average_on_third[playerid], float64(0.0)))) + (average_on_second[playerid] * (1.0 - min(steal_runners_on_third - average_on_third[playerid], float64(0.0))))
                #adjust base position based on stealing bases
                runners_on_first -= (steal_second_opportunities * attempt_steal_chance[playerid])
                runner_advance_first -= (steal_second_opportunities * attempt_steal_chance[playerid]) * runner_advance_chance[playerid]
                runners_on_second += (steal_second_opportunities * steal_base_success_rate) - (steal_third_opportunities * attempt_steal_chance[playerid])
                runner_advance_second += ((steal_second_opportunities * steal_base_success_rate) - (steal_third_opportunities * attempt_steal_chance[playerid])) * runner_advance_chance[playerid]
                if extra_base:                    
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
                    steal_fourth_opportunities = float64(0.0)
                    #steal_home                    
                    steal_home_opportunities = steal_third_opportunities                    
                    steal_home_opportunities += average_on_third[playerid]
                    #adjust third base
                    runners_on_third += (steal_third_opportunities * steal_base_success_rate) - (steal_home_opportunities * attempt_steal_chance[playerid])
                    runner_advance_third += ((steal_third_opportunities * steal_base_success_rate) - (steal_home_opportunities * attempt_steal_chance[playerid])) * runner_advance_chance[playerid]
                steal_base_opportunities = steal_second_opportunities + steal_third_opportunities + steal_fourth_opportunities
                stolen_bases[playerid] += steal_base_opportunities * steal_base_success_rate * probable_atbat
                stolen_bases[playerid] += steal_home_opportunities * steal_home_success_rate * probable_atbat
                player_rbi += ((100.0 + steal_mod[playerid]) * (steal_home_opportunities * steal_home_success_rate * probable_atbat)) + (steal_mod[playerid] * steal_base_opportunities * steal_base_success_rate * probable_atbat)
                player_score += ((100.0 + steal_mod[playerid]) * (steal_home_opportunities * steal_home_success_rate) * probable_atbat) + (steal_mod[playerid] * steal_base_opportunities * steal_base_success_rate * probable_atbat)
                steal_outs = (steal_base_opportunities * caught_steal_base_chance[playerid] * attempt_steal_chance[playerid]) + (steal_home_opportunities * caught_steal_home_chance[playerid] * attempt_steal_chance[playerid])                      
            
                runners_on_first = float64(max(min(runners_on_first, 1.0), float64(0.0)))
                runners_on_second = float64(max(min(runners_on_second, 1.0), float64(0.0)))
                runners_on_third = float64(max(min(runners_on_third, 1.0), float64(0.0)))
                runners_on_fourth = float64(max(min(runners_on_fourth, 1.0), float64(0.0)))
                runner_advance_first = float64(max(min(runner_advance_first, 1.0), float64(0.0)))
                runner_advance_second = float64(max(min(runner_advance_second, 1.0), float64(0.0)))
                runner_advance_third = float64(max(min(runner_advance_third, 1.0), float64(0.0)))
                runner_advance_fourth = float64(max(min(runner_advance_fourth, 1.0), float64(0.0)))

                player_score += float64((player_score * 0.02 * probable_atbat) if reverberating else 0.0)
                hits[playerid] += float64(((triple_chance[playerid] + double_chance[playerid] + single_chance[playerid]) * 0.02 * probable_atbat) if reverberating else 0.0)
                homers[playerid] += float64((homerun_chance[playerid] * 0.02 * probable_atbat) if reverberating else 0.0)
                player_rbi += float64((((100.0 + steal_mod[playerid]) * (steal_home_opportunities * steal_home_success_rate)) + (steal_mod[playerid] * steal_base_opportunities * steal_base_success_rate) * 0.02) if reverberating else 0.0)
                player_rbi += float64(((runners_advance_score + walking_score + homerun_score + triple_runners_score + double_runners_score + single_runners_score) * 0.02 * probable_atbat) if reverberating else 0.0)
                stolen_bases[playerid] += float64((((steal_base_opportunities * steal_base_success_rate) + (steal_home_opportunities * steal_home_success_rate)) * 0.02 * probable_atbat) if reverberating else 0.0)
                strikeouts += float64(((strike_out_chance[playerid] * 0.02 * probable_atbat)) if reverberating else 0.0)
            
                inning_score += player_score
                inning_rbi += player_rbi                

                current_batter_no_out = (1.0 - caught_out_chance[playerid]) * (1.0 - strike_out_chance[playerid]) * (1.0 - steal_outs)
                current_batter_out = min(caught_out_chance[playerid] + strike_out_chance[playerid] + steal_outs, 1.0)                                    
                if atbats_in_inning > 0:
                    if atbats_in_inning > 1:
                        two_outs = List([i * current_batter_no_out for i in two_outs])
                    two_outs.extend([i * current_batter_out for i in one_outs])                
                    two_out = sum(two_outs)
                if atbats_in_inning > 0:                                
                    one_outs = List([i * current_batter_no_out for i in one_outs])                
                    one_outs.append(no_outs * current_batter_out)
                else:                
                    one_outs.append(current_batter_out)
                one_out = sum(one_outs)            
                no_outs *= current_batter_no_out

                atbats_in_inning += 1 
            
                if atbats_in_inning >= int(outs):
                    probable_atbat = float64(min(no_outs + one_out + two_out, 1.0))
                else:
                    probable_atbat = float64(1.0)
                
                if (atbats_in_inning == maximum_inning_atbats) or (probable_atbat <= 0.02):                
                    current_innings += 1
                    team_score += inning_score  
                    team_rbi += inning_rbi
                    inning_score, inning_rbi = float64(0.0), float64(0.0)                
                    runners_on_first, runners_on_second, runners_on_third, runners_on_fourth = float64(0.0), float64(0.0), float64(0.0), float64(0.0)
                    runner_advance_first, runner_advance_second, runner_advance_third, runner_advance_fourth = float64(0.0), float64(0.0), float64(0.0), float64(0.0)                        
                    game_complete = (is_home) and (team_score > opp_score) and (current_innings == 8)
                    break

            if (atbats_in_inning == maximum_inning_atbats) or (probable_atbat <= 0.02):            
                starting_player = playerid
                probable_atbat, no_outs = 1.0, 1.0
                atbats_in_inning = 0            
                one_outs.clear(), two_outs.clear()
            else:
                starting_player = 0 
                
        if current_innings == 9:
            game_complete = True
        elif (current_innings == 8) and not game_complete:
            total_innings = 9
    return team_score, stolen_bases, homers, hits, strikeouts, team_rbi

@njit
def calc_team_score(mods, weather, active_batters, event_mods, away_home, team_bat_data, team_run_data, opp_stat_data, pitcher_stat_data, pitcherAttrs, teamPlayerAttrs, battingAttrs, oppAttrs, adjustments, ruth_strike_adjust, opp_score, outs):              
    (reverb_weather, sun_weather, bh_weather) = weather        

    blood_calc = "madJayEm" in battingAttrs
    
    runner_advance_chance, caught_out_chance, sacrifice_chance, score_mod, hit_modifier, homerun_multipliers, score_multiplier, attempt_steal_chance, walk_chance, strike_out_chance, caught_steal_base_chance, caught_steal_home_chance, homerun_chance, triple_chance, double_chance, single_chance, caught_steal_outs, on_base_chance, average_on_first, average_on_second, average_on_third, steal_mod, walk_mod = calc_probs_from_stats(mods, active_batters, event_mods, team_bat_data, team_run_data, opp_stat_data, pitcher_stat_data, pitcherAttrs, teamPlayerAttrs, battingAttrs, oppAttrs, adjustments, ruth_strike_adjust, blood_calc, outs)    

    #start = datetime.datetime.now()               
    
    team_score, bases_stolen, homers_hit, hits_hit, strikeouts, team_rbi = simulate_game(active_batters, battingAttrs, teamPlayerAttrs, opp_score, away_home, outs, homerun_chance, triple_chance, double_chance, single_chance, walk_chance, float64(walk_mod), sacrifice_chance, runner_advance_chance, average_on_first, average_on_second, average_on_third, reverb_weather, float64(score_mod), strike_out_chance, caught_out_chance, caught_steal_base_chance, caught_steal_home_chance, attempt_steal_chance, homerun_multipliers, hit_modifier, steal_mod, score_multiplier)                       

    #end = datetime.datetime.now()                
    #if ((end-start).total_seconds()) > 1.0:
    #print("{} inputs:\n ab {}\n batatts {}\n teamPlayAtts {}\n opp_score {}\n outs {}\n hr {}\n trip {}\n double {}\n single {}\n walk {}\n wmod {}\n sac {}\n ra {}\n aof {}\n aos {}\n aot {}\n weather {}\n scoremod {}\n so {}\n co {}\n csb {}\n csh {}\n asc {}\n hrmult {}\n hitmod {}\n stealmod {}\n scoremult {}\n".format(away_home, active_batters, battingAttrs, teamPlayerAttrs, opp_score, outs, homerun_chance, triple_chance, double_chance, single_chance, walk_chance, walk_mod, sacrifice_chance, runner_advance_chance, average_on_first, average_on_second, average_on_third, reverb_weather, score_mod, strike_out_chance, caught_out_chance, caught_steal_base_chance, caught_steal_home_chance, attempt_steal_chance, homerun_multipliers, hit_modifier, steal_mod, score_multiplier))
    
    #print("{} outputs:\n score {}\n steals {}\n homers {}\n hits {}\n ks {}\n rbi {}\n".format(away_home, team_score, bases_stolen, homers_hit, hits_hit, strikeouts, team_rbi))

    if sun_weather or bh_weather:                        
        team_score = float64(team_score % 1000.0)
        
    return team_score, bases_stolen, homers_hit, hits_hit, strikeouts, team_rbi

@njit
def calc_runners_on(runners_on_base, runner_advance_base, runners_on_base_minus_one, runner_advance_base_minus_one, runners_on_base_minus_two, runner_advance_base_minus_two, runners_on_base_minus_three, runner_advance_base_minus_three, single_chance, double_chance, triple_chance, homerun_chance, sacrifice_chance, caught_out_chance, walk_chance, walk_mod, average_new_on_base, new_on_base_advance):
    runners_on = float64(max(runners_on_base + (runner_advance_base_minus_one * runners_on_base_minus_one * caught_out_chance) + ((runners_on_base_minus_one - runners_on_base) * single_chance) + ((runners_on_base_minus_one - runners_on_base) * sacrifice_chance) + ((runners_on_base_minus_two - runners_on_base) * double_chance) + ((runners_on_base_minus_three - runners_on_base) * triple_chance) - (runners_on_base * homerun_chance) + ((runners_on_base_minus_one - runners_on_base) * walk_chance * (1.0 - walk_mod)) + ((runners_on_base_minus_two + runners_on_base_minus_three - runners_on_base) * walk_chance * walk_mod) + average_new_on_base, float64(0.0)))
    
    runner_advance = float64(max(runner_advance_base + (runner_advance_base_minus_one * (runner_advance_base_minus_one * runners_on_base_minus_one * caught_out_chance)) + ((runner_advance_base_minus_one - runner_advance_base) * ((runners_on_base_minus_one - runners_on_base) * single_chance)) + ((runner_advance_base_minus_one - runner_advance_base) * ((runners_on_base_minus_one - runners_on_base) * sacrifice_chance)) + ((runner_advance_base_minus_two - runner_advance_base) * ((runners_on_base_minus_two - runners_on_base) * double_chance)) + ((runner_advance_base_minus_three - runner_advance_base) * ((runners_on_base_minus_three - runners_on_base) * triple_chance)) - (runner_advance_base * (runners_on_base * homerun_chance)) + ((runner_advance_base_minus_one - runner_advance_base) * ((runners_on_base_minus_one - runners_on_base) * walk_chance * (1.0 - walk_mod))) + ((runner_advance_base_minus_two + runner_advance_base_minus_three - runner_advance_base) * ((runners_on_base_minus_two + runners_on_base_minus_three - runners_on_base) * walk_chance * walk_mod)) + (average_new_on_base * new_on_base_advance), float64(0.0)))
    
    return runners_on, runner_advance

@njit
def calc_team_stlats(pitching_terms, defense_terms, batting_terms, running_terms, sorted_batters, pitching_mods, defense_mods, batting_mods, running_mods, defense, batting, running, pitcher_stat_data, adj_def, adj_bat, adj_run, shelled, aa_blood_impact, aaa_blood_impact, high_pressure_mod):        
    lineup = float64(0.0)    
    overperform_pct, def_overperform_pct = float64(0.0), float64(0.0)
    blood_player = 0
    team_batting = np.zeros((20, 9))
    team_running = np.zeros((20, 10))
    team_pitcher = np.zeros((7))
    team_defense = np.zeros((7))
    
    for playerid in range(0, sorted_batters):  
        if not shelled[playerid]:                        
            overperform_pct = float64(aa_blood_impact[blood_player] + aaa_blood_impact[blood_player] + high_pressure_mod[blood_player])
            def_overperform_pct = float64(aa_blood_impact[blood_player] + aaa_blood_impact[blood_player])            
            team_batting[blood_player, 0] = float64(batting_terms[0].calc(max((batting[blood_player, 0] + ((adj_bat[blood_player, 0] - batting[blood_player, 0]) * overperform_pct)), 0.0)) * (batting_mods[0]))
            team_batting[blood_player, 1] = float64(batting_terms[1].calc(max((batting[blood_player, 1] + ((adj_bat[blood_player, 1] - batting[blood_player, 1]) * overperform_pct)), 0.0)) * (batting_mods[1]))
            team_batting[blood_player, 2] = float64(batting_terms[2].calc((batting[blood_player, 2]) + ((adj_bat[blood_player, 2] - batting[blood_player, 2]) * overperform_pct)) * (batting_mods[2]))
            team_batting[blood_player, 3] = float64(batting_terms[3].calc((batting[blood_player, 3]) + ((adj_bat[blood_player, 3] - batting[blood_player, 3]) * overperform_pct)) * (batting_mods[3]))
            team_batting[blood_player, 4] = float64(batting_terms[4].calc((batting[blood_player, 4]) + ((adj_bat[blood_player, 4] - batting[blood_player, 4]) * overperform_pct)) * (batting_mods[4]))
            team_batting[blood_player, 5] = float64(batting_terms[5].calc((batting[blood_player, 5]) + ((adj_bat[blood_player, 5] - batting[blood_player, 5]) * overperform_pct)) * (batting_mods[5]))
            team_batting[blood_player, 6] = float64(batting_terms[6].calc((batting[blood_player, 5]) + ((adj_bat[blood_player, 5] - batting[blood_player, 5]) * overperform_pct)) * (batting_mods[6]))
            team_batting[blood_player, 7] = float64(batting_terms[7].calc((batting[blood_player, 5]) + ((adj_bat[blood_player, 5] - batting[blood_player, 5]) * overperform_pct)) * (batting_mods[7]))
            team_batting[blood_player, 8] = float64(batting_terms[8].calc((batting[blood_player, 6]) + ((adj_bat[blood_player, 6] - batting[blood_player, 6]) * overperform_pct)) * (batting_mods[8]))          
            team_running[blood_player, 0] = float64(running_terms[0].calc((running[blood_player, 0]) + ((adj_run[blood_player, 0] - running[blood_player, 0]) * overperform_pct)) * (running_mods[0]))
            team_running[blood_player, 1] = float64(running_terms[1].calc((running[blood_player, 0]) + ((adj_run[blood_player, 0] - running[blood_player, 0]) * overperform_pct)) * (running_mods[1]))
            team_running[blood_player, 2] = float64(running_terms[2].calc((running[blood_player, 0]) + ((adj_run[blood_player, 0] - running[blood_player, 0]) * overperform_pct)) * (running_mods[2]))
            team_running[blood_player, 3] = float64(running_terms[3].calc((running[blood_player, 0]) + ((adj_run[blood_player, 0] - running[blood_player, 0]) * overperform_pct)) * (running_mods[3]))
            team_running[blood_player, 4] = float64(running_terms[4].calc((running[blood_player, 1]) + ((adj_run[blood_player, 1] - running[blood_player, 1]) * overperform_pct)) * (running_mods[4]))
            team_running[blood_player, 5] = float64(running_terms[5].calc((running[blood_player, 1]) + ((adj_run[blood_player, 1] - running[blood_player, 1]) * overperform_pct)) * (running_mods[5]))
            team_running[blood_player, 6] = float64(running_terms[6].calc((running[blood_player, 2]) + ((adj_run[blood_player, 2] - running[blood_player, 2]) * overperform_pct)) * (running_mods[6]))
            team_running[blood_player, 7] = float64(running_terms[7].calc((running[blood_player, 2]) + ((adj_run[blood_player, 2] - running[blood_player, 2]) * overperform_pct)) * (running_mods[7]))
            team_running[blood_player, 8] = float64(running_terms[8].calc((running[blood_player, 3]) + ((adj_run[blood_player, 3] - running[blood_player, 3]) * overperform_pct)) * (running_mods[8]))
            team_running[blood_player, 9] = float64(running_terms[9].calc((running[blood_player, 4]) + ((adj_run[blood_player, 4] - running[blood_player, 4]) * overperform_pct)) * (running_mods[9]))
            blood_player += 1
        else:
            overperform_pct, def_overperform_pct = float64(0.0), float64(0.0)
        lineup += float64(1.0)
        team_defense[0] += float64(defense_terms[0].calc((defense[playerid, 0]) + ((adj_def[playerid, 0] - defense[playerid, 0]) * def_overperform_pct)) * (defense_mods[0]))
        team_defense[1] += float64(defense_terms[1].calc((defense[playerid, 1]) + ((adj_def[playerid, 1] - defense[playerid, 1]) * def_overperform_pct)) * (defense_mods[1]))
        team_defense[2] += float64(defense_terms[2].calc((defense[playerid, 2]) + ((adj_def[playerid, 2] - defense[playerid, 2]) * def_overperform_pct)) * (defense_mods[2]))
        team_defense[3] += float64(defense_terms[3].calc((defense[playerid, 2]) + ((adj_def[playerid, 2] - defense[playerid, 2]) * def_overperform_pct)) * (defense_mods[3]))
        team_defense[4] += float64(defense_terms[4].calc((defense[playerid, 3]) + ((adj_def[playerid, 3] - defense[playerid, 3]) * def_overperform_pct)) * (defense_mods[4]))
        team_defense[5] += float64(defense_terms[5].calc((defense[playerid, 3]) + ((adj_def[playerid, 3] - defense[playerid, 3]) * def_overperform_pct)) * (defense_mods[5]))
        team_defense[6] += float64(defense_terms[6].calc((defense[playerid, 4]) + ((adj_def[playerid, 4] - defense[playerid, 4]) * def_overperform_pct)) * (defense_mods[6]))
    team_defense[0] *= float64(1.0 / lineup)
    team_defense[1] *= float64(1.0 / lineup)
    team_defense[2] *= float64(1.0 / lineup)
    team_defense[3] *= float64(1.0 / lineup)
    team_defense[4] *= float64(1.0 / lineup)
    team_defense[5] *= float64(1.0 / lineup)
    team_defense[6] *= float64(1.0 / lineup)        
    
    team_pitcher[0] = float64(pitching_terms[0].calc(pitcher_stat_data[0]) * (pitching_mods[0]))
    team_pitcher[1] = float64(pitching_terms[1].calc(pitcher_stat_data[1]) * (pitching_mods[1]))
    team_pitcher[2] = float64(pitching_terms[2].calc(pitcher_stat_data[2]) * (pitching_mods[2]))
    team_pitcher[3] = float64(pitching_terms[3].calc(pitcher_stat_data[2]) * (pitching_mods[3]))
    team_pitcher[4] = float64(pitching_terms[4].calc(pitcher_stat_data[2]) * (pitching_mods[4]))
    team_pitcher[5] = float64(pitching_terms[5].calc(pitcher_stat_data[3]) * (pitching_mods[5]))
    team_pitcher[6] = float64(1.0)

    return team_batting, team_running, team_defense, team_pitcher

@njit
def calc_team_stlats_instantiate_impact(pitching_terms, defense_terms, batting_terms, running_terms, batters, pitching_mods, defense_mods, batting_mods, running_mods, defense, batting, running, pitcher_stat_data, adj_def, adj_bat, adj_run, shelled):

    average_aa_impact = np.zeros((20))
    average_aaa_impact = np.zeros((20))
    high_pressure_mod = np.zeros((20))

    team_batting, team_running, team_defense, team_pitcher = calc_team_stlats(pitching_terms, defense_terms, batting_terms, running_terms, batters, pitching_mods, defense_mods, batting_mods, running_mods, defense, batting, running, pitcher_stat_data, adj_def, adj_bat, adj_run, shelled, average_aa_impact, average_aaa_impact, high_pressure_mod)   

    return team_batting, team_running, team_defense, team_pitcher

@njit
def blood_impact_calc(pitching_terms, defense_terms, batting_terms, running_terms, mods, flooding, batters, active_batters, pitching_mods, defense_mods, batting_mods, running_mods, event_mods, defense, batting, running, pitcher_stat_data, teampitcherAttrs, teamPlayerAttrs, teamAttrs, adj_def, adj_bat, adj_run, shelled, opppitcherAttrs, oppAttrs, team_batting, team_running, opp_team_defense, oppPitcherStlats, adjustments, ruth_strike_adjust):

    average_aa_impact = np.zeros((20))
    average_aaa_impact = np.zeros((20))
    high_pressure_mod = np.zeros((20))
    innings = 9
    outs = float64(3.0)
    
    blood_calc = "a" in teamAttrs    
    _, caught_out_chance, _, _, _, _, _, _, _, strike_out_chance, _, _, _, triple_chance, double_chance, _, caught_steal_outs, on_base_chance, _, _, _, _, _ = calc_probs_from_stats(mods, active_batters, event_mods, team_batting, team_running, opp_team_defense, oppPitcherStlats, opppitcherAttrs, teamPlayerAttrs, teamAttrs, oppAttrs, adjustments, ruth_strike_adjust, blood_calc, outs)            
    
    outs_per_lineup = float64(sum(strike_out_chance) + sum(caught_steal_outs) + sum(caught_out_chance))    

    if ("aa" in teamAttrs) or ("a" in teamAttrs) or ("aaa" in teamAttrs):                                    
        if ("aa" in teamAttrs) or ("a" in teamAttrs):           
            for idx in range(0, active_batters):
                x = 0.0
                previous_blood_impact = float64(0.0)
                average_aa_impact[idx] = float64(0.0)
                if outs_per_lineup < 0.1:
                    average_aa_impact[idx] = float64(1.0)
                else:                        
                    batter_atbats = 0.0
                    while (x < (outs * float64(innings))) and (average_aa_impact[idx] < 1.0):                    
                        previous_blood_impact = average_aa_impact[idx]
                        average_aa_impact[idx] += float64(((double_chance[idx] * ((1.0 - double_chance[idx]) ** batter_atbats)) * (((outs * float64(innings)) - x) / (outs * float64(innings)))))
                        if (average_aa_impact[idx] - previous_blood_impact) < 0.0001:                                
                            break
                        x += outs_per_lineup * ((outs - outs_per_lineup) if (outs_per_lineup < outs) else 1.0)     
                        batter_atbats += 1.0
                    average_aa_impact[idx] = float64(min(average_aa_impact[idx], 1.0) * ((1.0 / 12.0) if blood_calc else 1.0))
            
        if ("aaa" in teamAttrs) or ("a" in teamAttrs):                    
            for idx in range(0, active_batters):
                x = 0.0
                previous_blood_impact = float64(0.0)
                average_aa_impact[idx] = float64(0.0)     
                if outs_per_lineup < 0.1:
                    average_aa_impact[idx] = float64(1.0)
                else:              
                    batter_atbats = 0.0
                    while (x < (outs * float64(innings))) and (average_aa_impact[idx] < 1.0):                    
                        previous_blood_impact = average_aa_impact[idx]
                        average_aa_impact[idx] += float64(((triple_chance[idx] * ((1.0 - triple_chance[idx]) ** batter_atbats)) * (((outs * float64(innings)) - x) / (outs * float64(innings)))))
                        if (average_aa_impact[idx] - previous_blood_impact) < 0.0001:
                            break
                        x += outs_per_lineup * ((outs - outs_per_lineup) if (outs_per_lineup < outs) else 1.0)      
                        batter_atbats += 1.0
                    average_aa_impact[idx] = float64(min(average_aa_impact[idx], 1.0) * ((1.0 / 12.0) if blood_calc else 1.0))

    if ("high_pressure" in teamAttrs) and flooding:        
        high_pressure_mod[0] = float64(on_base_chance[active_batters - 1])
        for idx in range(1, active_batters):
            high_pressure_mod[idx] = float64(on_base_chance[idx-1])
        
    team_batting, team_running, team_defense, teamPitcherStlats = calc_team_stlats(pitching_terms, defense_terms, batting_terms, running_terms, batters, pitching_mods, defense_mods, batting_mods, running_mods, defense, batting, running, pitcher_stat_data, adj_def, adj_bat, adj_run, shelled, average_aa_impact, average_aa_impact, high_pressure_mod)  
    
    return team_batting, team_running, team_defense, teamPitcherStlats    

@njit
def get_mofo_pb_blood_launcher(away_blood, home_blood, pitching_terms, defense_terms, batting_terms, running_terms, mods, flooding, away_batters, away_active_batters, away_pitching_mods, away_defense_mods, away_batting_mods, away_running_mods, away_event_mods, away_defense, away_batting, away_running, away_pitcher_stat_data, awaypitcherAttrs, awayPlayerAttrs, awayAttrs, away_adj_def, away_adj_bat, away_adj_run, away_shelled, home_batters, home_active_batters, home_pitching_mods, home_defense_mods, home_batting_mods, home_running_mods, home_event_mods, home_defense, home_batting, home_running, home_pitcher_stat_data, homepitcherAttrs, homePlayerAttrs, homeAttrs, home_adj_def, home_adj_bat, home_adj_run, home_shelled, adjustments, ruth_strike_adjust, check_weather):

    #if trace_mem:
    #    before = tracemalloc.take_snapshot()
    #    before = before.filter_traces((tracemalloc.Filter(True, "*dispatcher.py"),))                

    away_team_batting, away_team_running, away_team_defense, awayPitcherStlats = calc_team_stlats_instantiate_impact(pitching_terms, defense_terms, batting_terms, running_terms, away_batters, away_pitching_mods, away_defense_mods, away_batting_mods, away_running_mods, away_defense, away_batting, away_running, away_pitcher_stat_data, away_adj_def, away_adj_bat, away_adj_run, away_shelled)

    home_team_batting, home_team_running, home_team_defense, homePitcherStlats = calc_team_stlats_instantiate_impact(pitching_terms, defense_terms, batting_terms, running_terms, home_batters, home_pitching_mods, home_defense_mods, home_batting_mods, home_running_mods, home_defense, home_batting, home_running, home_pitcher_stat_data, home_adj_def, home_adj_bat, home_adj_run, home_shelled)

    #if trace_mem:
    #    after_stats = tracemalloc.take_snapshot()
    #    after_stats = after_stats.filter_traces((tracemalloc.Filter(True, "*dispatcher.py"),))        
    #    top_stats = after_stats.compare_to(before, 'lineno')                            
    #    if top_stats[0].size_diff > 0:                        
    #        print("Increase from stats {}".format(top_stats[0]))
    #    else:
    #        print("No increase from stats {}".format(top_stats[0]))                                    

    blank_score = float64(10.0) if "madJayEm" in awayAttrs else float64(1.01)    
    outs = float64(10.0) if "madJayEm" in awayAttrs else float64(3.0)        

    if away_blood:
        away_team_batting, away_team_running, away_team_defense, awayPitcherStlats = blood_impact_calc(pitching_terms, defense_terms, batting_terms, running_terms, mods, flooding, away_batters, away_active_batters, away_pitching_mods, away_defense_mods, away_batting_mods, away_running_mods, away_event_mods, away_defense, away_batting, away_running, away_pitcher_stat_data, awaypitcherAttrs, awayPlayerAttrs, awayAttrs, away_adj_def, away_adj_bat, away_adj_run, away_shelled, homepitcherAttrs, homeAttrs, away_team_batting, away_team_running, home_team_defense, homePitcherStlats, adjustments, ruth_strike_adjust)        

    if home_blood:
        home_team_batting, home_team_running, home_team_defense, homePitcherStlats = blood_impact_calc(pitching_terms, defense_terms, batting_terms, running_terms, mods, flooding, home_batters, home_active_batters, home_pitching_mods, home_defense_mods, home_batting_mods, home_running_mods, home_event_mods, home_defense, home_batting, home_running, home_pitcher_stat_data, homepitcherAttrs, homePlayerAttrs, homeAttrs, home_adj_def, home_adj_bat, home_adj_run, home_shelled, awaypitcherAttrs, awayAttrs, home_team_batting, home_team_running, away_team_defense, awayPitcherStlats, adjustments, ruth_strike_adjust)            
    
    #if trace_mem:
    #    after_blood = tracemalloc.take_snapshot()
    #    after_blood = after_blood.filter_traces((tracemalloc.Filter(True, "*dispatcher.py"),))        
    #    top_stats = after_blood.compare_to(after_stats, 'lineno')                            
    #    if top_stats[0].size_diff > 0:                        
    #        print("Increase from blood {}".format(top_stats[0]))
    #    else:
    #        print("No increase from blood {}".format(top_stats[0]))

    away_home = ("madJayEm" in awayAttrs)

    away_score, away_steals, away_home_runs, away_hit_balls, home_pitcher_ks, home_pitcher_era = calc_team_score(mods, check_weather, away_active_batters, away_event_mods, away_home, away_team_batting, away_team_running, home_team_defense, homePitcherStlats, homepitcherAttrs, awayPlayerAttrs, awayAttrs, homeAttrs, adjustments, ruth_strike_adjust, blank_score, outs)

    away_home = not ("madJayEm" in awayAttrs)

    ##start = datetime.datetime.now()
    
    home_score, home_steals, home_home_runs, home_hit_balls, away_pitcher_ks, away_pitcher_era = calc_team_score(mods, check_weather, home_active_batters, home_event_mods, away_home, home_team_batting, home_team_running, away_team_defense, awayPitcherStlats, awaypitcherAttrs, homePlayerAttrs, homeAttrs, awayAttrs, adjustments, ruth_strike_adjust, away_score, outs)   
    
    #if trace_mem:
    #    after_score = tracemalloc.take_snapshot()
    #    after_score = after_score.filter_traces((tracemalloc.Filter(True, "*dispatcher.py"),))        
    #    top_stats = after_score.compare_to(after_blood, 'lineno')                            
    #    if top_stats[0].size_diff > 0:                        
    #        print("Increase from score {}".format(top_stats[0]))            
    #    else:
    #        print("No increase from score {}".format(top_stats[0]))

    #away_score, away_steals, away_home_runs, away_hit_balls, home_pitcher_ks, home_pitcher_era, home_score, home_steals, home_home_runs, home_hit_balls, away_pitcher_ks, away_pitcher_era = calc_team_scores(mods, check_weather, away_active_batters, home_active_batters, away_event_mods, home_event_mods, away_team_batting, away_team_running, home_team_defense, homePitcherStlats, home_team_batting, home_team_running, away_team_defense, awayPitcherStlats, awaypitcherAttrs, homepitcherAttrs, awayPlayerAttrs, homePlayerAttrs, awayAttrs, homeAttrs, adjustments, ruth_strike_adjust)

    #end = datetime.datetime.now()                
    #if ((end-start).total_seconds()) > 1.0:
    #    print("{} inputs:\n batting {}\n running {}\n defense {}\n pitcher {}\n pitch attrs {}\n play attrs {}\n team attrs {}\n opp attrs {}\n opp score {}\n".format(away_home, home_team_batting, home_team_running, away_team_defense, awayPitcherStlats, awaypitcherAttrs, homePlayerAttrs, homeAttrs, awayAttrs, away_score))

    return away_score, away_steals, away_home_runs, away_hit_balls, home_pitcher_ks, home_pitcher_era, home_score, home_steals, home_home_runs, home_hit_balls, away_pitcher_ks, away_pitcher_era
   
def get_mofo_playerbased(gameid, trace_mem, dict_mods, awayPitcher, homePitcher, awayAttrs, homeAttrs, weather, away_pitcher_stat_data, home_pitcher_stat_data, terms, away_batter_order, away_active_batters, home_batter_order, home_active_batters, awayMods, homeMods, away_adj_def, away_adj_bat, away_adj_run, home_adj_def, home_adj_bat, home_adj_run, dict_adjustments, away_shelled, away_defense, away_batting, away_running, awayPlayerAttrs, awaypitcherAttrs, home_shelled, home_defense, home_batting, home_running, homePlayerAttrs, homepitcherAttrs, skip_mods):                          
    #if trace_mem:
    #    first, second, preall_mi_alloc, preall_mi_free = rtsys.get_allocation_stats()      
    polarity_plus, polarity_minus, flood_weather = helpers.get_weather_idx("Polarity +"), helpers.get_weather_idx("Polarity -"), helpers.get_weather_idx("Flooding")    

    flooding = weather == flood_weather
    check_weather = (helpers.get_weather_idx("Reverb") == weather, helpers.get_weather_idx("Sun 2") == weather, helpers.get_weather_idx("Black Hole") == weather)   
    
    mods = (float64(dict_mods["love"]["opp"]["strikeout"]), float64(dict_mods["love"]["opp"]["easypitch"]), float64(dict_mods["base_instincts"]["same"]["multiplier"]), float64(dict_mods["fiery"]["same"]["multiplier"]), float64(dict_mods["electric"]["same"]["multiplier"]), float64(dict_mods["psychic"]["same"]["walktrick"]), float64(dict_mods["psychic"]["same"]["striketrick"]), float64(dict_mods["acidic"]["same"]["multiplier"]))

    adjustments = (float64(dict_adjustments["moxie_swing_correct"]), float64(dict_adjustments["path_connect"]), float64(dict_adjustments["thwack_base_hit"]), float64(dict_adjustments["unthwack_base_hit"]), float64(dict_adjustments["omni_base_hit"]), float64(dict_adjustments["muscl_foul_ball"]), float64(dict_adjustments["baset_attempt_steal"]), float64(dict_adjustments["laser_attempt_steal"]), float64(dict_adjustments["watch_attempt_steal"]), float64(dict_adjustments["anticap_caught_steal_base"]), float64(dict_adjustments["laser_caught_steal_base"]), float64(dict_adjustments["anticap_caught_steal_home"]), float64(dict_adjustments["baset_caught_steal_home"]), float64(dict_adjustments["laser_caught_steal_home"]), float64(dict_adjustments["div_homer"]), float64(dict_adjustments["overp_homer"]), float64(dict_adjustments["muscl_triple"]), float64(dict_adjustments["ground_triple"]), float64(dict_adjustments["cont_triple"]), float64(dict_adjustments["overp_triple"]), float64(dict_adjustments["chasi_triple"]), float64(dict_adjustments["muscl_double"]), float64(dict_adjustments["cont_double"]), float64(dict_adjustments["overp_double"]), float64(dict_adjustments["chasi_double"]), float64(dict_adjustments["martyr_sacrifice"]), float64(dict_adjustments["laser_runner_advances"]), float64(dict_adjustments["indulg_runner_advances"]), float64(dict_adjustments["trag_runner_advances"]), float64(dict_adjustments["shakes_runner_advances"]), float64(dict_adjustments["tenacious_runner_advances"]))

    ruth_strike_adjust = float64(dict_adjustments["ruth_strike"])

    pitching_terms, defense_terms, batting_terms, running_terms = tuple(terms[0]), tuple(terms[1]), tuple(terms[2]), tuple(terms[3])    
    away_pitching_mods, away_defense_mods, away_batting_mods, away_running_mods, away_event_mods = tuple(awayMods[0]), tuple(awayMods[1]), tuple(awayMods[2]), tuple(awayMods[3]), tuple(awayMods[4])
    home_pitching_mods, home_defense_mods, home_batting_mods, home_running_mods, home_event_mods = tuple(homeMods[0]), tuple(homeMods[1]), tuple(homeMods[2]), tuple(homeMods[3]), tuple(homeMods[4])

    away_batters, home_batters = len(away_batter_order), len(home_batter_order)
    away_blood = "aaa" in awayAttrs or "aa" in awayAttrs or "a" in awayAttrs or ("high_pressure" in awayAttrs and flooding)
    home_blood = "aaa" in homeAttrs or "aa" in homeAttrs or "a" in homeAttrs or ("high_pressure" in homeAttrs and flooding)        

    #if trace_mem:
    #    print(" Away player attrs {}\n Home player attrs {}".format(awayPlayerAttrs, homePlayerAttrs))
    #    print(" Away pitcher attrs {}\n Home pitcher attrs {}".format(awaypitcherAttrs, homepitcherAttrs))
    #    print(" Away team attrs {}\n Home team attrs {}".format(awayAttrs, homeAttrs))

    #if away_blood or home_blood:

    #if trace_mem:
    #    before = tracemalloc.take_snapshot()
    #    before = before.filter_traces((tracemalloc.Filter(True, "*dispatcher.py"),))     

    away_score, away_steals, away_home_runs, away_hit_balls, home_pitcher_ks, home_pitcher_era, home_score, home_steals, home_home_runs, home_hit_balls, away_pitcher_ks, away_pitcher_era = get_mofo_pb_blood_launcher(away_blood, home_blood, pitching_terms, defense_terms, batting_terms, running_terms, mods, flooding, away_batters, away_active_batters, away_pitching_mods, away_defense_mods, away_batting_mods, away_running_mods, away_event_mods, away_defense, away_batting, away_running, away_pitcher_stat_data, awaypitcherAttrs, awayPlayerAttrs, awayAttrs, away_adj_def, away_adj_bat, away_adj_run, away_shelled, home_batters, home_active_batters, home_pitching_mods, home_defense_mods, home_batting_mods, home_running_mods, home_event_mods, home_defense, home_batting, home_running, home_pitcher_stat_data, homepitcherAttrs, homePlayerAttrs, homeAttrs, home_adj_def, home_adj_bat, home_adj_run, home_shelled, adjustments, ruth_strike_adjust, check_weather)

    #if trace_mem:
    #    after_score = tracemalloc.take_snapshot()
    #    after_score = after_score.filter_traces((tracemalloc.Filter(True, "*dispatcher.py"),))        
    #    top_stats = after_score.compare_to(before, 'lineno')                            
    #    if top_stats[0].size_diff > 0:                        
    #        print("Increase from score {}".format(top_stats[0]))         
    #        #output_string = " Away player attrs {}\n Home player attrs {}".format(awayPlayerAttrs, homePlayerAttrs)
    #        #output_string += "\n Away pitcher attrs {}\n Home pitcher attrs {}".format(awaypitcherAttrs, homepitcherAttrs)
    #        #output_string += "\n Away team attrs {}\n Home team attrs {}".format(awayAttrs, homeAttrs)
    #        #output_string += "\n Away shelled {}\n Home shelled {}".format(away_shelled, home_shelled)            
    #        #filename = 'C:\\Users\\milicic\\Downloads\\Blaseball\\Modeling\\AutoOutput\\' + gameid + 'playerinfo.txt'
    #        #log_file = open(filename, 'w')
    #        #log_file.write(output_string)
    #        #log_file.close()
    #        #filename = 'C:\\Users\\milicic\\Downloads\\Blaseball\\Modeling\\AutoOutput\\' + gameid + '_get_mofo_pb_blood_launcher.txt'
    #        #log_file = open(filename, 'w')
    #        #get_mofo_pb_blood_launcher.inspect_types(file=log_file)        
    #        #log_file.close()
    #        #filename = 'C:\\Users\\milicic\\Downloads\\Blaseball\\Modeling\\AutoOutput\\' + gameid + '_calc_probs_from_stats.txt'
    #        #log_file = open(filename, 'w')
    #        #calc_probs_from_stats.inspect_types(file=log_file)        
    #        #log_file.close()
    #        #filename = 'C:\\Users\\milicic\\Downloads\\Blaseball\\Modeling\\AutoOutput\\' + gameid + '_simulate_game.txt'
    #        #log_file = open(filename, 'w')
    #        #simulate_game.inspect_types(file=log_file)        
    #        #log_file.close()
    #        #filename = 'C:\\Users\\milicic\\Downloads\\Blaseball\\Modeling\\AutoOutput\\' + gameid + '_calc_team_score.txt'
    #        #log_file = open(filename, 'w')
    #        #calc_team_score.inspect_types(file=log_file)        
    #        #log_file.close()
    #        #filename = 'C:\\Users\\milicic\\Downloads\\Blaseball\\Modeling\\AutoOutput\\' + gameid + '_blood_impact_calc.txt'
    #        #log_file = open(filename, 'w')
    #        #blood_impact_calc.inspect_types(file=log_file)        
    #        #log_file.close()            
    #    else:
    #        print("No increase from score {}".format(top_stats[0]))    
        
    #else:
    #    away_score, away_steals, away_home_runs, away_hit_balls, home_pitcher_ks, home_pitcher_era, home_score, home_steals, home_home_runs, home_hit_balls, away_pitcher_ks, away_pitcher_era = get_mofo_pb_launcher(pitching_terms, defense_terms, batting_terms, running_terms, mods, flooding, away_batters, away_active_batters, away_pitching_mods, away_defense_mods, away_batting_mods, away_running_mods, away_event_mods, away_defense, away_batting, away_running, away_pitcher_stat_data, awaypitcherAttrs, awayPlayerAttrs, awayAttrs, away_adj_def, away_adj_bat, away_adj_run, away_shelled, home_batters, home_active_batters, home_pitching_mods, home_defense_mods, home_batting_mods, home_running_mods, home_event_mods, home_defense, home_batting, home_running, home_pitcher_stat_data, homepitcherAttrs, homePlayerAttrs, homeAttrs, home_adj_def, home_adj_bat, home_adj_run, home_shelled, adjustments, ruth_strike_adjust, check_weather)
    

    #if trace_mem:
    #    print("Away results:\n Score {}\n Steals {}\n Homers {}\n Hits {}\n Home Ks {}\n Home era {}\n".format(away_score, away_steals, away_home_runs, away_hit_balls, home_pitcher_ks, home_pitcher_era))
    #    print("Home results:\n Score {}\n Steals {}\n Homers {}\n Hits {}\n Home Ks {}\n Home era {}\n".format(home_score, home_steals, home_home_runs, home_hit_balls, away_pitcher_ks, away_pitcher_era))

    away_stolen_bases, away_homers, away_hits = {}, {}, {}
    home_stolen_bases, home_homers, home_hits = {}, {}, {}
    
    active_away_batter, active_home_batter = 0, 0

    for batter in range(0, max(away_batters, home_batters)):
        if batter < away_batters:
            if not away_shelled[batter]:
                away_stolen_bases[away_batter_order[batter]] = away_steals[active_away_batter]
                away_homers[away_batter_order[batter]] = away_home_runs[active_away_batter]
                away_hits[away_batter_order[batter]] = away_hit_balls[active_away_batter] 
                active_away_batter += 1
        if batter < home_batters:
            if not home_shelled[batter]:
                home_stolen_bases[home_batter_order[batter]] = home_steals[active_home_batter]
                home_homers[home_batter_order[batter]] = home_home_runs[active_home_batter]
                home_hits[home_batter_order[batter]] = home_hit_balls[active_home_batter]
                active_home_batter += 1    

    if away_score < 0:
        away_score += abs(away_score) * 2.0
        home_score += abs(away_score) * 2.0
    if home_score < 0:
        away_score += abs(home_score) * 2.0
        home_score += abs(home_score) * 2.0

    numerator = away_score - home_score
    denominator = away_score + home_score              

    #if (helpers.get_weather_idx("Sun 2") == weather) or (helpers.get_weather_idx("Black Hole") == weather):
    #    print("Away score = {}, home_score = {}".format(away_score, home_score))

    #first, second, postall_mi_alloc, postall_mi_free = rtsys.get_allocation_stats()    
    #if ((postall_mi_alloc - preall_mi_alloc) - (postall_mi_free - preall_mi_free)) > 0:
    #    print("Leak from entire getplayerbased = {}".format(((postall_mi_alloc - preall_mi_alloc) - (postall_mi_free - preall_mi_free))))   
    
    if not denominator or weather == polarity_plus or weather == polarity_minus:                
        return .5, .5, away_hits, home_hits, away_homers, home_homers, away_stolen_bases, home_stolen_bases, away_pitcher_ks, home_pitcher_ks, away_pitcher_era, home_pitcher_era
    
    away_formula = numerator / denominator           
    
    log_transform_base = 10.0
    away_odds = log_transform(away_formula, log_transform_base)                   
        
    return away_odds, 1.0 - away_odds, away_hits, home_hits, away_homers, home_homers, away_stolen_bases, home_stolen_bases, away_pitcher_ks, home_pitcher_ks, away_pitcher_era, home_pitcher_era
    

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
                    if base_multiplier <= 0.0001:             
                        multiplier = float(0.0)
                    else:
                        if adjusted_value < 0:
                            base_multiplier *= -1                        
                        multiplier = base_multiplier
                else:                    
                    if value <= 0.0:             
                        multiplier = float(1.0)
                    else:                        
                        normalized_value = stlatterm.calc(value)
                        multiplier = log_transform(normalized_value, logbase) * 2.0
                #forcing harmonic mean with quicker process time?  
                    
                if ballparkstlat != "hype":                                                    
                    awayMods[playerstlat] = multiplier                                           
                homeMods[playerstlat] = multiplier
    away_event_terms = (float64(awayMods["plus_hit_minus_homer"]), float64(awayMods["plus_hit_minus_foul"]), float64(awayMods["plus_groundout_minus_hardhit"]), float64(awayMods["plus_contact_minus_hardhit"]), float64(awayMods["plus_strike"]), float64(awayMods["plus_hardhit"]), float64(awayMods["minus_stealsuccess"]), float64(awayMods["minus_doubleplay"]), float64(awayMods["minus_stealattempt"]), float64(awayMods["minus_hit"]), float64(awayMods["minus_homer"]))
    home_event_terms = (float64(homeMods["plus_hit_minus_homer"]), float64(homeMods["plus_hit_minus_foul"]), float64(homeMods["plus_groundout_minus_hardhit"]), float64(homeMods["plus_contact_minus_hardhit"]), float64(homeMods["plus_strike"]), float64(homeMods["plus_hardhit"]), float64(homeMods["minus_stealsuccess"]), float64(homeMods["minus_doubleplay"]), float64(homeMods["minus_stealattempt"]), float64(homeMods["minus_hit"]), float64(homeMods["minus_homer"]))

    away_hype_pitching_terms = (float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0))
    home_hype_pitching_terms = (float64(homeMods["unthwack_base_hit"]), float64(homeMods["ruth_strike"]), float64(homeMods["overp_homer"]), float64(homeMods["overp_triple"]), float64(homeMods["overp_double"]), float64(homeMods["shakes_runner_advances"]))
    
    away_hype_defense_terms = (float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0))
    home_hype_defense_terms = (float64(homeMods["omni_base_hit"]), float64(homeMods["tenacious_runner_advances"]), float64(homeMods["watch_attempt_steal"]), float64(homeMods["anticap_caught_steal_base"]), float64(homeMods["anticap_caught_steal_home"]), float64(homeMods["chasi_triple"]), float64(homeMods["chasi_double"]))

    away_hype_batting_terms = (float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0))
    home_hype_batting_terms = (float64(homeMods["trag_runner_advances"]), float64(homeMods["path_connect"]), float64(homeMods["thwack_base_hit"]), float64(homeMods["div_homer"]), float64(homeMods["moxie_swing_correct"]), float64(homeMods["muscl_foul_ball"]), float64(homeMods["muscl_triple"]), float64(homeMods["muscl_double"]), float64(homeMods["martyr_sacrifice"]))
    
    away_hype_running_terms = (float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0), float64(1.0))
    home_hype_running_terms = (float64(homeMods["laser_attempt_steal"]), float64(homeMods["laser_caught_steal_base"]), float64(homeMods["laser_caught_steal_home"]), float64(homeMods["laser_runner_advances"]), float64(homeMods["baset_attempt_steal"]), float64(homeMods["baset_caught_steal_home"]), float64(homeMods["cont_triple"]), float64(homeMods["cont_double"]), float64(homeMods["ground_triple"]), float64(homeMods["indulg_runner_advances"]))

    awayMods_list, homeMods_list = (away_hype_pitching_terms, away_hype_defense_terms, away_hype_batting_terms, away_hype_running_terms, away_event_terms), (home_hype_pitching_terms, home_hype_defense_terms, home_hype_batting_terms, home_hype_running_terms, home_event_terms)

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
    pitching_terms =[dict_terms["unthwack_base_hit"], dict_terms["ruth_strike"], dict_terms["overp_homer"], dict_terms["overp_triple"], dict_terms["overp_double"], dict_terms["shakes_runner_advances"], dict_terms["cold_clutch_factor"]]
    defense_terms = [dict_terms["omni_base_hit"], dict_terms["watch_attempt_steal"], dict_terms["chasi_triple"], dict_terms["chasi_double"], dict_terms["anticap_caught_steal_base"], dict_terms["anticap_caught_steal_home"], dict_terms["tenacious_runner_advances"]]
    batting_terms = [dict_terms["path_connect"], dict_terms["trag_runner_advances"], dict_terms["thwack_base_hit"], dict_terms["div_homer"], dict_terms["moxie_swing_correct"], dict_terms["muscl_foul_ball"], dict_terms["muscl_triple"], dict_terms["muscl_double"], dict_terms["martyr_sacrifice"]]
    running_terms = [dict_terms["laser_attempt_steal"], dict_terms["laser_caught_steal_base"], dict_terms["laser_caught_steal_home"], dict_terms["laser_runner_advances"], dict_terms["baset_attempt_steal"], dict_terms["baset_caught_steal_home"], dict_terms["cont_triple"], dict_terms["cont_double"], dict_terms["ground_triple"], dict_terms["indulg_runner_advances"]]
    terms = [pitching_terms, defense_terms, batting_terms, running_terms]
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
