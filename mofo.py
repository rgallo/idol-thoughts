from __future__ import division
from __future__ import print_function

from helpers import geomean, load_terms
from dotenv import load_dotenv
import os


def team_defense(terms, pitcher, teamname, team_stat_data, pitcher_stat_data):
    pitcher_data = pitcher_stat_data[pitcher]
    team_data = team_stat_data[teamname]
    return sum([term.calc(val) for term, val in (
        (terms["unthwackability"], pitcher_data["unthwackability"]),
        (terms["ruthlessness"], pitcher_data["ruthlessness"]),
        (terms["overpowerment"], pitcher_data["overpowerment"]),
        (terms["shakespearianism"], pitcher_data["shakespearianism"]),
        (terms["coldness"], pitcher_data["coldness"]),
        (terms["meanomniscience"], geomean(team_data["omniscience"])),
        (terms["meantenaciousness"], geomean(team_data["tenaciousness"])),
        (terms["meanwatchfulness"], geomean(team_data["watchfulness"])),
        (terms["meananticapitalism"], geomean(team_data["anticapitalism"])),
        (terms["meanchasiness"], geomean(team_data["chasiness"])),
        (terms["maxomniscience"], max(team_data["omniscience"])),
        (terms["maxtenaciousness"], max(team_data["tenaciousness"])),
        (terms["maxwatchfulness"], max(team_data["watchfulness"])),
        (terms["maxanticapitalism"], max(team_data["anticapitalism"])),
        (terms["maxchasiness"], max(team_data["chasiness"])))])


def team_offense(terms, teamname, team_stat_data):
    team_data = team_stat_data[teamname]
    return sum([term.calc(val) for term, val in (
        (terms["meantragicness"], geomean(team_data["tragicness"])),
        (terms["meanpatheticism"], geomean(team_data["patheticism"])),
        (terms["meanthwackability"], geomean(team_data["thwackability"])),
        (terms["meandivinity"], geomean(team_data["divinity"])),
        (terms["meanmoxie"], geomean(team_data["moxie"])),
        (terms["meanmusclitude"], geomean(team_data["musclitude"])),
        (terms["meanmartyrdom"], geomean(team_data["martyrdom"])),
        (terms["maxthwackability"], max(team_data["thwackability"])),
        (terms["maxdivinity"], max(team_data["divinity"])),
        (terms["maxmoxie"], max(team_data["moxie"])),
        (terms["maxmusclitude"], max(team_data["musclitude"])),
        (terms["maxmartyrdom"], max(team_data["martyrdom"])),
        (terms["meanlaserlikeness"], geomean(team_data["laserlikeness"])),
        (terms["meanbasethirst"], geomean(team_data["baseThirst"])),
        (terms["meancontinuation"], geomean(team_data["continuation"])),
        (terms["meangroundfriction"], geomean(team_data["groundFriction"])),
        (terms["meanindulgence"], geomean(team_data["indulgence"])),
        (terms["maxlaserlikeness"], max(team_data["laserlikeness"])),
        (terms["maxbasethirst"], max(team_data["baseThirst"])),
        (terms["maxcontinuation"], max(team_data["continuation"])),
        (terms["maxgroundfriction"], max(team_data["groundFriction"])),
        (terms["maxindulgence"], max(team_data["indulgence"])))])


def calculate(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data):
    load_dotenv()
    terms_url = os.getenv("MOFO_TERMS")
    terms, _ = load_terms(terms_url)
    away_offense = team_offense(terms, awayTeam, team_stat_data)
    away_defense = team_defense(terms, awayPitcher, awayTeam, team_stat_data, pitcher_stat_data)
    home_offense = team_offense(terms, homeTeam, team_stat_data)
    home_defense = team_defense(terms, homePitcher, homeTeam, team_stat_data, pitcher_stat_data)
    away_formula = ((away_offense - home_defense) - min(home_offense - away_defense, 0.0)) / ((away_offense - home_defense) + min(home_offense - away_defense, 0.0))
    away_odds = (1 / (1 + 10 ** (-1 * away_formula)))
    return away_odds, 1.0-away_odds
