from __future__ import division
from __future__ import print_function

import os
import math
import copy

from helpers import geomean, load_terms


def calc_pitcher_batter(terms, pitcher, pitcher_stat_data, team_pid_stat_data, batter, battingteam):
    pitcher_data = pitcher_stat_data[pitcher]    
    batter_list_dict = [stlats for player_id, stlats in team_pid_stat_data[battingteam].items() if player_id == batter]
    batter_data = batter_list_dict[0]    
    return sum([term.calc(val) for term, val in (
        (terms["unthwackability"], pitcher_data["unthwackability"]),
        (terms["ruthlessness"], pitcher_data["ruthlessness"]),
        (terms["overpowerment"], pitcher_data["overpowerment"]),
        (terms["shakespearianism"], pitcher_data["shakespearianism"]),
        (terms["coldness"], pitcher_data["coldness"]),
        (terms["tragicness"], batter_data["tragicness"]),
        (terms["patheticism"], batter_data["patheticism"]),
        (terms["thwackability"], batter_data["thwackability"]),
        (terms["divinity"], batter_data["divinity"]),
        (terms["moxie"], batter_data["moxie"]),
        (terms["musclitude"], batter_data["musclitude"]),
        (terms["martyrdom"], batter_data["martyrdom"])
    )])

def calc_pitcher(terms, pitcher, pitcher_stat_data):    
    pitcher_data = pitcher_stat_data[pitcher]    
    return sum([term.calc(val) for term, val in (
        (terms["unthwackability"], pitcher_data["unthwackability"]),
        (terms["ruthlessness"], pitcher_data["ruthlessness"]),
        (terms["overpowerment"], pitcher_data["overpowerment"]),
        (terms["shakespearianism"], pitcher_data["shakespearianism"]),
        (terms["coldness"], pitcher_data["coldness"])
    )])

def calc_everythingelse(terms, pitchingteam, battingteam, team_pid_stat_data, batter):
    pitching_team_data = [stlats for player_id, stlats in team_pid_stat_data[pitchingteam].items()]
    batting_team_data = [stlats for player_id, stlats in team_pid_stat_data[battingteam].items() if (player_id != batter and not stlats.get("shelled", False))]
    return sum([term.calc(val) for term, val in (
        (terms["meanomniscience"], geomean([row["omniscience"] for row in pitching_team_data])),
        (terms["meantenaciousness"], geomean([row["tenaciousness"] for row in pitching_team_data])),
        (terms["meanwatchfulness"], geomean([row["watchfulness"] for row in pitching_team_data])),
        (terms["meananticapitalism"], geomean([row["anticapitalism"] for row in pitching_team_data])),
        (terms["meanchasiness"], geomean([row["chasiness"] for row in pitching_team_data])),        
        (terms["meanlaserlikeness"], geomean([row["laserlikeness"] for row in batting_team_data])),
        (terms["meanbasethirst"], geomean([row["baseThirst"] for row in batting_team_data])),
        (terms["meancontinuation"], geomean([row["continuation"] for row in batting_team_data])),
        (terms["meangroundfriction"], geomean([row["groundFriction"] for row in batting_team_data])),
        (terms["meanindulgence"], geomean([row["indulgence"] for row in batting_team_data])),
        (terms["maxomniscience"], max([row["omniscience"] for row in pitching_team_data])),
        (terms["maxtenaciousness"], max([row["tenaciousness"] for row in pitching_team_data])),
        (terms["maxwatchfulness"], max([row["watchfulness"] for row in pitching_team_data])),
        (terms["maxanticapitalism"], max([row["anticapitalism"] for row in pitching_team_data])),
        (terms["maxchasiness"], max([row["chasiness"] for row in pitching_team_data])),                
        (terms["maxlaserlikeness"], max([row["laserlikeness"] for row in batting_team_data])),
        (terms["maxbasethirst"], max([row["baseThirst"] for row in batting_team_data])),
        (terms["maxcontinuation"], max([row["continuation"] for row in batting_team_data])),
        (terms["maxgroundfriction"], max([row["groundFriction"] for row in batting_team_data])),
        (terms["maxindulgence"], max([row["indulgence"] for row in batting_team_data])),
    )])


def setup(eventofinterest):
    if eventofinterest == "hits":
        terms_url = os.getenv("BATMAN_HIT_TERMS")
    elif eventofinterest == "hrs":
        terms_url = os.getenv("BATMAN_HR_TERMS")
    elif eventofinterest == "abs":
        terms_url = os.getenv("BATMAN_AB_TERMS")
    else:
        raise ValueError("Unsupported event of interest type")
    terms, special_cases = load_terms(terms_url, ["factors"])
    return terms, special_cases

def get_team_atbats(pitcher, pitchingteam, battingteam, team_pid_stat_data, pitcher_stat_data, innings, flip_lineup, terms, special_cases, outs_pi=3):
    factor_exp, factor_const, reverberation, repeating = special_cases["factors"][:4]
    team_atbat_data = {}
    atbats, temp_factor = 0.0, 1.0
    batters = team_pid_stat_data.get(battingteam)        
    active_batters = len(batters)
    hits_hrs_walks = 0.0    
    ordered_active_batters = sorted([(k, v) for k,v in batters.items() if not v["shelled"]], key=lambda x: x[1]["turnOrder"], reverse=flip_lineup)    
    outs_pg = innings * outs_pi        
    current_outs = 0
    while current_outs < outs_pg:        
        for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):            
            if batter_id not in team_atbat_data:
                team_atbat_data[batter_id] = 0.0            
            pitcher_batter = calc_pitcher_batter(terms, pitcher, pitcher_stat_data, team_pid_stat_data, batter_id, battingteam)
            everythingelse = calc_everythingelse(terms, pitchingteam, battingteam, team_pid_stat_data, batter_id)
            temp_factor = factor_exp if (pitcher_batter > 0) else 1.0
            hits_hrs_walks = ((pitcher_batter ** float(temp_factor)) + everythingelse) * (float(factor_const) / 100.0)
            if math.isnan(hits_hrs_walks):
                for line_order, (bat_id, curr_batt) in enumerate(ordered_active_batters):
                    team_atbat_data[bat_id] = -10000.0
                return team_atbat_data
            if hits_hrs_walks >= 1.0:
                for line_order, (bat_id, curr_batt) in enumerate(ordered_active_batters):
                    team_atbat_data[bat_id] = -10000.0
                return team_atbat_data
            if hits_hrs_walks >= 0.0:
                outs_pg += hits_hrs_walks                      
            team_atbat_data[batter_id] += 1.0          
            if team_pid_stat_data[battingteam][batter_id]["reverberating"]:                        
                team_atbat_data[batter_id] += reverberation
                if hits_hrs_walks >= 0.0:
                    outs_pg += hits_hrs_walks * reverberation
            if team_pid_stat_data[battingteam][batter_id]["repeating"]:                        
                team_atbat_data[batter_id] += repeating
                if hits_hrs_walks >= 0.0:
                    outs_pg += hits_hrs_walks * repeating
            current_outs += 1      
            if current_outs >= outs_pg:                                
                break        
    # I guess distribute the remaining error equally among all batters?
    for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):
        if batter_id not in team_atbat_data:
            team_atbat_data[batter_id] = 0.0
        if (outs_pg > (current_outs - 1)) and (outs_pg > innings * outs_pi):
            team_atbat_data[batter_id] += (outs_pg - (current_outs - 1)) / active_batters
    return team_atbat_data


def get_batman(eventofinterest, pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, special_cases, outs_pi=3):            
    if eventofinterest == "abs":                
        atbats_data = get_team_atbats(pitcher, pitchingteam, battingteam, team_pid_stat_data, pitcher_stat_data, 9.0, False, terms, special_cases, outs_pi)
        batman = atbats_data[batter]
    else:        
        factor_exp, factor_const = special_cases["factors"][:2]
        everythingelse = calc_everythingelse(terms, pitchingteam, battingteam, team_pid_stat_data, batter)
        pitcher_batter = calc_pitcher_batter(terms, pitcher, pitcher_stat_data, team_pid_stat_data, batter, battingteam)
        factor_exp = factor_exp if (pitcher_batter > 0) else 1.0
        batman = ((pitcher_batter ** float(factor_exp)) + everythingelse) * float(factor_const)
        batman = max(batman, 0.0)
    return batman


def calculatePitcherVsBatter(eventofinterest, pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data):
    terms, special_cases = setup(eventofinterest)
    return get_batman(eventofinterest, pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, special_cases)


def calculate(pitcher, pitchingteam, battingteam, team_pid_stat_data, pitcher_stat_data):
    batters = team_pid_stat_data.get(battingteam)
    batting_lineup_size = len([bid for bid, batter in batters.items() if not batter.get("shelled", False)])
    results = []
    for batter_id, batter in batters.items():
        if batter.get("shelled", False):
            continue
        name = batter["name"]
        batman_atbats = calculatePitcherVsBatter("abs", pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data)
        batman_hits = calculatePitcherVsBatter("hits", pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data)
        batman_homers = calculatePitcherVsBatter("hrs", pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data)
        at_bats = max(batman_atbats, 9 * 3 / batting_lineup_size)
        hits = max(batman_hits * (at_bats * (9.0 / batting_lineup_size)), 0)
        homers = max(batman_homers * (at_bats * (9.0 / batting_lineup_size)), 0)
        results.append({"name": name, "team": battingteam, "hits": hits, "homers": homers, "abs": at_bats,
                        "attrs": batter["attrs"]})
    return results
