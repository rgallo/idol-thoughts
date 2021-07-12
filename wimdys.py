from __future__ import division
from __future__ import print_function

import collections
import statistics
from scipy.stats import hmean

import helpers
import math
from mofo import calculate_playerbased
import os

WEATHERS = ["Void", "Sunny", "Overcast", "Rainy", "Sandstorm", "Snowy", "Acidic", "Solar Eclipse",
            "Glitter", "Blooddrain", "Peanuts", "Birds", "Feedback", "Reverb"]

def calculate_playerbased(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, awayAttrs, homeAttrs,
              day, weather, skip_mods=False):    
    mods, terms, awayMods, homeMods = setup_playerbased(weather, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, team_stat_data, pitcher_stat_data)
    return get_mofo_playerbased(mods, awayPitcher, homePitcher, awayTeam, homeTeam, awayAttrs, homeAttrs, team_stat_data, pitcher_stat_data, terms, awayMods,
                    homeMods, skip_mods=skip_mods)

#pitcher_stat_data is formatted as [awayPitcher] and [homePitcher] with stlats of [stlats] [ispitcher] and [attrs]
#what we actually want to do is create relative weightings of all players based on how they shape up in matchups across the entire league, assuming everything else is equal

def calc_team_score(mods, team_stat_data, opp_stat_data, pitcher_stat_data, team_data, opp_data, pitcher_data, teamAttrs, oppAttrs, adjustments):
    team_score, runners_advance_score, homerun_score = 0.0, 0.0, 0.0
    opponentAttrs = [attr.lower() for attr in oppAttrs]
        
    unthwack_adjust, ruth_adjust, overp_adjust, shakes_adjust, cold_adjust, path_adjust, trag_adjust, thwack_adjust, div_adjust, moxie_adjust, muscl_adjust, martyr_adjust, omni_adjust, watch_adjust, tenacious_adjust, chasi_adjust, anticap_adjust, laser_adjust, basethirst_adjust, groundfriction_adjust, continuation_adjust, indulgence_adjust, max_thwack, max_moxie, max_ruth = adjustments

    omniscience, watchfulness, chasiness, anticap, tenaciousness = opp_stat_data["omniscience"], opp_stat_data["watchfulness"], opp_stat_data["chasiness"], opp_stat_data["anticapitalism"], opp_stat_data["tenaciousness"]
    unthwackability, ruthlessness, overpowerment, shakespearianism, coldness = pitcher_stat_data["unthwackability"], pitcher_stat_data["ruthlessness"], pitcher_stat_data["overpowerment"], pitcher_stat_data["shakespearianism"], pitcher_stat_data["coldness"]

    omni, watch, anti, chasi, tenacious = (omniscience - omni_adjust), (watchfulness - watch_adjust), (anticap - anticap_adjust), (chasiness - chasi_adjust), (tenaciousness - tenacious_adjust)
    ruth, unthwack, overp, shakes, cold = (ruthlessness - ruth_adjust), (unthwackability - unthwack_adjust), (overpowerment - overp_adjust), (shakespearianism - shakes_adjust), (coldness - cold_adjust)
        
    homer_multiplier = -1.0 if "UNDERHANDED" in pitcher_data["attrs"] else 1.0  
    hit_multiplier = 1.0
    strike_mod = 1.0
    if "fiery" in opponentAttrs:        
        normalized_value = mods["fiery"]["same"]["ruthlessness"].calc(ruthlessness)        
        strike_mod += log_transform(normalized_value, 100.0)

    strike_log = (ruthlessness - 20.0) / (10.0 + ruth_adjust)
    strike_chance = log_transform(strike_log, 100.0)
    runners_advance_points, runners_advance_chance, runners_on_base, homerun_multipliers = [], [], [], []
    
    for playerid in team_stat_data:                              
        playerAttrs = [attr.lower() for attr in team_data[playerid]["attrs"].split(";")]
        homer_multiplier *= -1.0 if "SUBTRACTOR" in playerAttrs else 1.0
        hit_multiplier *= -1.0 if "SUBTRACTOR" in playerAttrs else 1.0
        patheticism, tragicness, thwackability, divinity, moxie, musclitude, martyrdom = team_stat_data[playerid]["patheticism"], team_stat_data[playerid]["tragicness"], team_stat_data[playerid]["thwackability"], team_stat_data[playerid]["divinity"], team_stat_data[playerid]["moxie"], team_stat_data[playerid]["musclitude"], team_stat_data[playerid]["martyrdom"]
        laserlikeness, basethirst, continuation, groundfriction, indulgence = team_stat_data[playerid]["laserlikeness"], team_stat_data[playerid]["basethirst"], team_stat_data[playerid]["continuation"], team_stat_data[playerid]["groundfriction"], team_stat_data[playerid]["indulgence"]
            
        path, tragic, thwack, div, mox, muscl, martyr = (patheticism - path_adjust), (tragicness - trag_adjust), (thwackability - thwack_adjust), (divinity - div_adjust), (moxie - moxie_adjust), (musclitude - muscl_adjust), (martyrdom - martyr_adjust)
        laser, baset, cont, ground, indulg = (laserlikeness - laser_adjust), (basethirst - basethirst_adjust), (continuation - continuation_adjust), (groundfriction - groundfriction_adjust), (indulgence - indulgence_adjust)                        

        moxie_log = (moxie - 20.0) / (10.0 + moxie_adjust)
        swing_correct_chance = log_transform(moxie_log, 100.0)
        walk_chance = swing_correct_chance * (1.0 - strike_chance)
        swing_strike_chance = swing_correct_chance * strike_chance        

        connect_log = (20 - patheticism) / (10.0 + path_adjust)
        connect_chance = log_transform(connect_log, 100.0) * swing_strike_chance
        
        base_hit_log = ((thwackability - unthwackability - omniscience) - 20.0) / (10.0 + thwack_adjust + unthwack_adjust + omni_adjust)
        base_hit_chance = log_transform(base_hit_log, 100.0) * connect_chance         
        
        runners_advance_log = (20 + martyrdom - musclitude) / (10.0 + martyr_adjust + muscl_adjust)
        runner_advance_chance = log_transform(runners_advance_log, 100.0) * (1.0 - base_hit_chance)
        runners_advance_chance.append(runner_advance_chance)        
        
        base_steal_score = (baset + laser - watch - anti) * min((base_hit_chance + walk_chance), 1.0)
        walk_score = max((mox - ruth), 0.0) * walk_chance
        strike_count_chance = (1.0 - swing_correct_chance) + (1.0 - connect_chance)
        
        strike_score = min((mox - ruth - path), 0.0) * max(strike_count_chance, 1.0) * strike_mod        
        hit_score = (ground + muscl - overp - chasi - shakes) * base_hit_chance * hit_multiplier
        
        team_score += base_steal_score + walk_score + hit_score + strike_score

        #homeruns needs to care about how many other runners are on base for how valuable they are, with a floor of "1x"
        homerun_multipliers.append(max((div - overp), 0.0) * base_hit_chance * homer_multiplier)
        runners_on_base.append(min((base_hit_chance + walk_chance), 1.0))

        #runners advancing is tricky, since we have to do this based on runners being on base already, but use the batter's martyrdom                
        runner_advance_points = max((laser + cont + indulg - tragic - cold - tenacious), 0.0) * min((base_hit_chance + walk_chance), 1.0)
        runners_advance_points.append(runner_advance_points)    
    
    for idx, val in enumerate(runners_advance_chance):
        runners_advance_batter = max(sum(runners_advance_points) - runners_advance_points[idx], 0.0)
        runners_advance_score += val * runners_advance_batter                
        
        if len(runners_on_base) < 4:            
            average_runners_on_base = max(sum(runners_on_base), 0.0) / len(runners_on_base)     
        else:
            average_runners_on_base = max(sum(runners_on_base) - runners_on_base[idx], 0.0) / (len(runners_on_base) - 1)             

        homerun_score += homerun_multipliers[idx] * (1.0 + max(average_runners_on_base, 3.0))

    team_score += runners_advance_score + homerun_score

    return team_score
    
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
    
    away_score = calc_team_score(mods, away_team_stlats, home_team_defense, homePitcherStlats, team_stat_data[awayTeam], team_stat_data[homeTeam], pitcher_stat_data[homePitcher], awayAttrs, homeAttrs, adjustments)
    home_score = calc_team_score(mods, home_team_stlats, away_team_defense, awayPitcherStlats, team_stat_data[homeTeam], team_stat_data[awayTeam], pitcher_stat_data[awayPitcher], homeAttrs, awayAttrs, adjustments)   

    numerator = away_score - home_score
    denominator = abs(away_score + home_score)
    if not denominator:
        return .5, .5    
    away_formula = numerator / denominator        
    away_odds = log_transform(away_formula, 100.0)
    return away_odds, 1.0 - away_odds

