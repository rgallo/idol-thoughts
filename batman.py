from __future__ import division
from __future__ import print_function

import os

from helpers import geomean, load_terms


def calc_pitcher_batter(terms, pitcher, pitcher_stat_data, team_stat_data, batter, battingteam):
    pitcher_data = pitcher_stat_data[pitcher]    
    batter_list_dict = [stlats for player_id, stlats in team_stat_data[battingteam].items() if player_id == batter]
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

def calc_everythingelse(terms, pitchingteam, battingteam, team_stat_data, batter):
    pitching_team_data = [stlats for player_id, stlats in team_stat_data[pitchingteam].items()]    
    batting_team_data = [stlats for player_id, stlats in team_stat_data[battingteam].items() if (player_id != batter and not stlats.get("shelled", False))]
    return sum([term.calc(val) for term, val in (
        (terms["meanomniscience"], geomean([row["omniscience"] for row in pitching_team_data])),
        (terms["meantenaciousness"], geomean([row["tenaciousness"] for row in pitching_team_data])),
        (terms["meanwatchfulness"], geomean([row["watchfulness"] for row in pitching_team_data])),
        (terms["meananticapitalism"], geomean([row["anticapitalism"] for row in pitching_team_data])),
        (terms["meanchasiness"], geomean([row["chasiness"] for row in pitching_team_data])),
        (terms["meantragicness"], geomean([row["tragicness"] for row in batting_team_data])),
        (terms["meanpatheticism"], geomean([row["patheticism"] for row in batting_team_data])),
        (terms["meanthwackability"], geomean([row["thwackability"] for row in batting_team_data])),
        (terms["meandivinity"], geomean([row["divinity"] for row in batting_team_data])),
        (terms["meanmoxie"], geomean([row["moxie"] for row in batting_team_data])),
        (terms["meanmusclitude"], geomean([row["musclitude"] for row in batting_team_data])),
        (terms["meanmartyrdom"], geomean([row["martyrdom"] for row in batting_team_data])),
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
        (terms["maxthwackability"], max([row["thwackability"] for row in batting_team_data])),
        (terms["maxdivinity"], max([row["divinity"] for row in batting_team_data])),
        (terms["maxmoxie"], max([row["moxie"] for row in batting_team_data])),
        (terms["maxmusclitude"], max([row["musclitude"] for row in batting_team_data])),
        (terms["maxmartyrdom"], max([row["martyrdom"] for row in batting_team_data])),
        (terms["maxlaserlikeness"], max([row["laserlikeness"] for row in batting_team_data])),
        (terms["maxbasethirst"], max([row["baseThirst"] for row in batting_team_data])),
        (terms["maxcontinuation"], max([row["continuation"] for row in batting_team_data])),
        (terms["maxgroundfriction"], max([row["groundFriction"] for row in batting_team_data])),
        (terms["maxindulgence"], max([row["indulgence"] for row in batting_team_data])),
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
