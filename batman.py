from __future__ import division
from __future__ import print_function

import os
import math

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


def get_batman(eventofinterest, pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, special_cases, outs_pi=3):            
    if eventofinterest == "abs":                
        factor_exp, factor_const, reverberation, repeating = special_cases["factors"][:4]
        atbats = 0.0
        batters = team_pid_stat_data.get(battingteam)        
        active_batters = len(batters)         
        ordered_active_batters = sorted([(k, v) for k,v in batters.items() if not v["shelled"]], key=lambda x: x[1]["turnOrder"])
        outs_pg = 9.0 * outs_pi        
        current_outs = 0
        while current_outs < outs_pg:
            batter_batted = False
            for lineup_order, (batter_id, current_batter) in enumerate(ordered_active_batters):                                
                pitcher_batter = calc_pitcher_batter(terms, pitcher, pitcher_stat_data, team_pid_stat_data, batter_id, battingteam)
                everythingelse = calc_everythingelse(terms, pitchingteam, battingteam, team_pid_stat_data, batter_id)                
                if math.isnan((pitcher_batter ** float(factor_exp)) + everythingelse - float(factor_const)):
                    return -10000.0
                if ((pitcher_batter ** float(factor_exp)) + everythingelse - float(factor_const)) >= 1.0:
                    return -1000.0                
                if ((pitcher_batter ** float(factor_exp)) + everythingelse - float(factor_const)) >= 0.0:
                    outs_pg += (pitcher_batter ** float(factor_exp)) + everythingelse - float(factor_const)  
                if math.isnan(outs_pg):
                    return -10000.0
                current_outs += 1                             
                if batter_id == batter:
                    atbats += 1.0
                    if team_pid_stat_data[battingteam][batter]["reverberating"]:                        
                        atbats += reverberation
                        if ((pitcher_batter ** float(factor_exp)) + everythingelse - float(factor_const)) >= 0.0:
                            outs_pg += ((pitcher_batter ** float(factor_exp)) + everythingelse - float(factor_const)) * reverberation
                    if team_pid_stat_data[battingteam][batter]["repeating"]:                        
                        atbats += repeating
                        if ((pitcher_batter ** float(factor_exp)) + everythingelse - float(factor_const)) >= 0.0:
                            outs_pg += ((pitcher_batter ** float(factor_exp)) + everythingelse - float(factor_const)) * repeating
                    batter_batted = True
                if current_outs >= outs_pg:
                    if batter_batted:
                        atbats += (outs_pg - (current_outs - 1)) / (lineup_order + 1)
                    else:
                        atbats -= (outs_pg - (current_outs - 1)) / (lineup_order + 1)
                    break
        batman = atbats
    else:        
        factor_exp, factor_const = special_cases["factors"][:2]
        everythingelse = calc_everythingelse(terms, pitchingteam, battingteam, team_pid_stat_data, batter)
        pitcher_batter = calc_pitcher_batter(terms, pitcher, pitcher_stat_data, team_pid_stat_data, batter, battingteam)
        batman = (pitcher_batter ** float(factor_exp)) + everythingelse - float(factor_const)     
        batman = max(batman, 0.0)
    return batman


def calculatePitcherVsBatter(eventofinterest, pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data):
    terms, special_cases = setup(eventofinterest)
    return get_batman(eventofinterest, pitcher, pitchingteam, batter, battingteam, team_pid_stat_data, pitcher_stat_data, terms, special_cases)


def calculate(pitcher, pitchingteam, battingteam, team_pid_stat_data, pitcher_stat_data):
    batters = team_pid_stat_data.get(battingteam)
    batting_lineup_size = len(batters)
    results = []
    for batter_id, batter in batters.items():
        if batter["shelled"]:
            continue
        name = batter["name"]
        batman_atbats = calculatePitcherVsBatter("abs", pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data)
        batman_hits = calculatePitcherVsBatter("hits", pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data)
        batman_homers = calculatePitcherVsBatter("hrs", pitcher, pitchingteam, batter_id, battingteam, team_pid_stat_data, pitcher_stat_data)
        hits = batman_hits * (batman_atbats * (9.0 / batting_lineup_size))
        homers = batman_homers * (batman_atbats * (9.0 / batting_lineup_size))
        results.append({"name": name, "team": battingteam, "hits": hits, "homers": homers, "abs": batman_atbats})
    return results
