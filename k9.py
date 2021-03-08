from __future__ import division
from __future__ import print_function

import os

from helpers import geomean, load_terms


def calc_pitching(terms, pitcher, pitcher_stat_data):
    pitcher_data = pitcher_stat_data[pitcher]
    return sum([term.calc(val) for term, val in (
        (terms["unthwackability"], pitcher_data["unthwackability"]),
        (terms["ruthlessness"], pitcher_data["ruthlessness"]),
        (terms["overpowerment"], pitcher_data["overpowerment"]),
        (terms["shakespearianism"], pitcher_data["shakespearianism"]),
        (terms["coldness"], pitcher_data["coldness"])
    )])


def calc_everythingelse(terms, pitchingteam, battingteam, team_stat_data):
    pitching_team_data = team_stat_data[pitchingteam]
    batting_team_data = team_stat_data[battingteam]
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


def setup():
    terms_url = os.getenv("K9_TERMS")
    terms, special_cases = load_terms(terms_url, ["factors"])
    return terms, special_cases


def get_k9(pitcher, pitchingteam, battingteam, team_stat_data, pitcher_stat_data, terms, special_cases):
    pitching = calc_pitching(terms, pitcher, pitcher_stat_data)
    everythingelse = calc_everythingelse(terms, pitchingteam, battingteam, team_stat_data)
    factor_exp, factor_const = special_cases["factors"][:2]
    kplus1PI = (pitching ** float(factor_exp)) + everythingelse - float(factor_const)
    k9 = max((kplus1PI * 9) - 1, 0)
    # need to not cap this when solving
    # k9 = max(min((kplus1PI * 9) - 1, 27), 0)
    return round(k9)


def calculate(pitcher, pitchingteam, battingteam, team_stat_data, pitcher_stat_data):
    terms, special_cases = setup()
    return get_k9(pitcher, pitchingteam, battingteam, team_stat_data, pitcher_stat_data, terms, special_cases)
