from __future__ import division
from __future__ import print_function

import collections

from helpers import geomean, load_terms, get_weather_idx, load_mods
import os

WEATHERS = ["Void", "Sunny", "Overcast", "Rainy", "Sandstorm", "Snowy", "Acidic", "Solar Eclipse",
            "Glitter", "Blooddrain", "Peanuts", "Birds", "Feedback", "Reverb"]


def calc_team(terms, termset, mods):
    total = 0.0
    for termname, val in termset:
        term = terms[termname]
        total += term.calc(val)
        modterms = (mods or {}).get(termname, [])
        for modterm in modterms:
            total += modterm.calc(val)
    return total


def team_defense(terms, pitcher, teamname, mods, team_stat_data, pitcher_stat_data):
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
    return calc_team(terms, termset, mods)


def team_offense(terms, teamname, mods, team_stat_data):
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
    return calc_team(terms, termset, mods)


def setup(day, weather, awayAttrs, homeAttrs):
    terms_url = os.getenv("MOFO_TERMS")
    terms, _ = load_terms(terms_url)
    mods_url = os.getenv("MOFO_MODS")
    mods = load_mods(mods_url, day)
    awayMods, homeMods = collections.defaultdict(lambda: []), collections.defaultdict(lambda: [])
    lowerAwayAttrs = [attr.lower() for attr in awayAttrs]
    lowerHomeAttrs = [attr.lower() for attr in homeAttrs]
    bird_weather = get_weather_idx("Birds")
    for attr in mods:
        # Special case for Affinity for Crows
        if attr == "affinity_for_crows" and weather != bird_weather:
            continue
        if attr in lowerAwayAttrs:
            for name, stlatterm in mods[attr]["same"].items():
                awayMods[name].append(stlatterm)
            for name, stlatterm in mods[attr]["opp"].items():
                homeMods[name].append(stlatterm)
        if attr in lowerHomeAttrs and attr != "traveling":
            for name, stlatterm in mods[attr]["same"].items():
                homeMods[name].append(stlatterm)
            for name, stlatterm in mods[attr]["opp"].items():
                awayMods[name].append(stlatterm)
    return terms, awayMods, homeMods


def calculate(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, awayAttrs, homeAttrs,
              day, weather):
    terms, awayMods, homeMods = setup(day, weather, awayAttrs, homeAttrs)
    return get_mofo(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, terms, awayMods, homeMods)


def get_mofo(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, terms, awayMods, homeMods):
    away_offense = abs(team_offense(terms, awayTeam, awayMods, team_stat_data))
    away_defense = abs(team_defense(terms, awayPitcher, awayTeam, awayMods, team_stat_data, pitcher_stat_data))
    home_offense = abs(team_offense(terms, homeTeam, homeMods, team_stat_data))
    home_defense = abs(team_defense(terms, homePitcher, homeTeam, homeMods, team_stat_data, pitcher_stat_data))
    numerator = (away_offense - home_defense) - (home_offense - away_defense)
    denominator = (away_offense - home_defense) + (home_offense - away_defense)
    if not denominator:
        return .5, .5
    away_formula = numerator / denominator
    away_odds = (1 / (1 + 10 ** (-1 * away_formula)))
    return away_odds, 1.0 - away_odds
