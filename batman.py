from __future__ import division
from __future__ import print_function

import os

from helpers import geomean, load_terms


def calc_pitcher_batter(terms, pitcher, pitcher_stat_data, team_stat_data, batter, battingteam):
    pitcher_data = pitcher_stat_data[pitcher]
    batter_data = [stlats for player_id, stlats in team_stat_data[battingteam].items() if player_id == batter]
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

def calc_everythingelse(terms, pitchingteam, battingteam, team_stat_data, batter):
    pitching_team_data = [stlats for player_id, stlats in team_stat_data[pitchingteam].items()]
    batting_team_data = [stlats for player_id, stlats in team_stat_data[battingteam].items() if player_id != batter]
    return sum([term.calc(val) for term, val in (
        (terms["meanomniscience"], geomean(pitching_team_data["omniscience"])),
        (terms["meantenaciousness"], geomean(pitching_team_data["tenaciousness"])),
        (terms["meanwatchfulness"], geomean(pitching_team_data["watchfulness"])),
        (terms["meananticapitalism"], geomean(pitching_team_data["anticapitalism"])),
        (terms["meanchasiness"], geomean(pitching_team_data["chasiness"])),
        (terms["meantragicness"], geomean(batting_team_data["tragicness"])),
        (terms["meanpatheticism"], geomean(batting_team_data["patheticism"])),
        (terms["meanthwackability"], geomean(batting_team_data["thwackability"])),
        (terms["meandivinity"], geomean(batting_team_data["divinity"])),
        (terms["meanmoxie"], geomean(batting_team_data["moxie"])),
        (terms["meanmusclitude"], geomean(batting_team_data["musclitude"])),
        (terms["meanmartyrdom"], geomean(batting_team_data["martyrdom"])),
        (terms["meanlaserlikeness"], geomean(batting_team_data["laserlikeness"])),
        (terms["meanbasethirst"], geomean(batting_team_data["baseThirst"])),
        (terms["meancontinuation"], geomean(batting_team_data["continuation"])),
        (terms["meangroundfriction"], geomean(batting_team_data["groundFriction"])),
        (terms["meanindulgence"], geomean(batting_team_data["indulgence"])),
        (terms["maxomniscience"], max(pitching_team_data["omniscience"])),
        (terms["maxtenaciousness"], max(pitching_team_data["tenaciousness"])),
        (terms["maxwatchfulness"], max(pitching_team_data["watchfulness"])),
        (terms["maxanticapitalism"], max(pitching_team_data["anticapitalism"])),
        (terms["maxchasiness"], max(pitching_team_data["chasiness"])),
        (terms["maxthwackability"], max(batting_team_data["thwackability"])),
        (terms["maxdivinity"], max(batting_team_data["divinity"])),
        (terms["maxmoxie"], max(batting_team_data["moxie"])),
        (terms["maxmusclitude"], max(batting_team_data["musclitude"])),
        (terms["maxmartyrdom"], max(batting_team_data["martyrdom"])),
        (terms["maxlaserlikeness"], max(batting_team_data["laserlikeness"])),
        (terms["maxbasethirst"], max(batting_team_data["baseThirst"])),
        (terms["maxcontinuation"], max(batting_team_data["continuation"])),
        (terms["maxgroundfriction"], max(batting_team_data["groundFriction"])),
        (terms["maxindulgence"], max(batting_team_data["indulgence"])),
    )])


def setup(eventofinterest):
    if eventofinterest == "hits":
        terms_url = os.getenv("BATMAN_HIT_TERMS")
    if eventofinterest == "hrs":
        terms_url = os.getenv("BATMAN_HR_TERMS")
    if eventofinterest == "abs":
        terms_url = os.getenv("BATMAN_AB_TERMS")
    terms, special_cases = load_terms(terms_url, ["factors"])
    return terms, special_cases


def get_batman(eventofinterest, pitcher, pitchingteam, batter, battingteam, team_stat_data, pitcher_stat_data, terms, special_cases):    
    everythingelse = calc_everythingelse(terms, pitchingteam, battingteam, team_stat_data, batter)    
    factor_exp, factor_const = special_cases["factors"][:2]
    if eventofinterest == "abs":
        pitcher = calc_pitcher(terms, pitcher, pitcher_stat_data)    
        batman = (pitcher ** float(factor_exp)) + everythingelse - float(factor_const)
    else:
        pitcher_batter = calc_pitcher_batter(terms, pitcher, pitcher_stat_data, team_stat_data, batter, battingteam)    
        batman = (pitcher_batter ** float(factor_exp)) + everythingelse - float(factor_const)        
    return batman


def calculate(eventofinterest, pitcher, pitchingteam, batter, battingteam, team_stat_data, pitcher_stat_data, batter_stat_data):
    terms, special_cases = setup(eventofinterest)
    return get_batman(eventofinterest, pitcher, pitchingteam, batter, battingteam, team_stat_data, pitcher_stat_data, batter_stat_data, terms, special_cases)
