from __future__ import division
from __future__ import print_function

from helpers import StlatTerm, geomean

RUTHLESSNESS_TERM = StlatTerm(4.12127141, 1.429362589, 2.383421924)
UNTHWACKABILITY_TERM = StlatTerm(3.907162647, 1.023279978, 2.229771626)
OVERPOWERMENT_TERM = StlatTerm(4.063997954, 1.35791032, 2.162894994)
SHAKESPEARIANISM_TERM = StlatTerm(2.322073723, 1.034700344, 1.372228932)
COLDNESS_TERM = StlatTerm(0.581091054, 1.59493934, 1.61757634)
MEANOMNISCIENCE_TERM = StlatTerm(-0.200479048, 0.939811067, 1.592903393)
MEANTENACIOUSNESS_TERM = StlatTerm(-1.410485486, 1.63106715, 1.146826446)
MEANWATCHFULNESS_TERM = StlatTerm(-0.759686272, 1.633571165, 1.707425263)
MEANANTICAPITALISM_TERM = StlatTerm(-5.658006805, 2.20027247, 1.444915332)
MEANCHASINESS_TERM = StlatTerm(-1.419737428, 2.301757508, 1.31947045)
MEANTRAGICNESS_TERM = StlatTerm(-1.39402248, 1.739475983, 1.299864147)
MEANPATHETICISM_TERM = StlatTerm(-2.427892124, 1.354166926, 1.732747511)
MEANTHWACKABILITY_TERM = StlatTerm(3.136097839, 1.767032482, 1.161141313)
MEANDIVINITY_TERM = StlatTerm(2.381200372, 1.306600869, 1.814912122)
MEANMOXIE_TERM = StlatTerm(0.190450069, 1.588579787, 1.288260174)
MEANMUSCLITUDE_TERM = StlatTerm(-0.050244726, 1.079894259, 1.488522949)
MEANMARTYRDOM_TERM = StlatTerm(1.41757909, 2.11568125, 1.30549571)
MEANLASERLIKENESS_TERM = StlatTerm(4.391200785, 1.974776864, 1.833591049)
MEANBASETHIRST_TERM = StlatTerm(-0.689587477, 1.338820767, 1.049243273)
MEANCONTINUATION_TERM = StlatTerm(6.336234266, 1.554884411, 1.875561672)
MEANGROUNDFRICTION_TERM = StlatTerm(2.841382058, 1.20556715, 1.243667176)
MEANINDULGENCE_TERM = StlatTerm(0.12207164, 1.649469301, 1.440935125)
MAXOMNISCIENCE_TERM = StlatTerm(-0.725435792, 1.579905617, 1.299479656)
MAXTENACIOUSNESS_TERM = StlatTerm(-2.333339175, 0.979871187, 1.672560608)
MAXWATCHFULNESS_TERM = StlatTerm(-0.310989313, 1.411329639, 1.076910599)
MAXANTICAPITALISM_TERM = StlatTerm(-2.000476038, 1.307503198, 1.463304593)
MAXCHASINESS_TERM = StlatTerm(-0.550879953, 1.140856035, 0.928677289)
MAXTHWACKABILITY_TERM = StlatTerm(-0.94151398, 1.817082622, 1.568832793)
MAXDIVINITY_TERM = StlatTerm(0.164867728, 1.678565989, 1.372523221)
MAXMOXIE_TERM = StlatTerm(-1.97163359, 1.231560771, 0.976182576)
MAXMUSCLITUDE_TERM = StlatTerm(4.046018147, 1.744742771, 1.504264605)
MAXMARTYRDOM_TERM = StlatTerm(-1.343288701, 1.516795255, 1.446295647)
MAXLASERLIKENESS_TERM = StlatTerm(2.883229349, 1.509509015, 1.057108101)
MAXBASETHIRST_TERM = StlatTerm(2.21978482, 1.557654029, 1.883659164)
MAXCONTINUATION_TERM = StlatTerm(-2.372413533, 1.625628665, 1.410690851)
MAXGROUNDFRICTION_TERM = StlatTerm(-0.969762832, 2.128260487, 0.770497847)
MAXINDULGENCE_TERM = StlatTerm(-1.438470181, 1.408115703, 1.232861142)


def team_defense(pitcher, teamname, team_stat_data, pitcher_stat_data):
    pitcher_data = pitcher_stat_data[pitcher]
    team_data = team_stat_data[teamname]
    return sum([term.calc(val) for term, val in (
        (UNTHWACKABILITY_TERM, pitcher_data["unthwackability"]),
        (RUTHLESSNESS_TERM, pitcher_data["ruthlessness"]),
        (OVERPOWERMENT_TERM, pitcher_data["overpowerment"]),
        (SHAKESPEARIANISM_TERM, pitcher_data["shakespearianism"]),
        (COLDNESS_TERM, pitcher_data["coldness"]),
        (MEANOMNISCIENCE_TERM, geomean(team_data["omniscience"])),
        (MEANTENACIOUSNESS_TERM, geomean(team_data["tenaciousness"])),
        (MEANWATCHFULNESS_TERM, geomean(team_data["watchfulness"])),
        (MEANANTICAPITALISM_TERM, geomean(team_data["anticapitalism"])),
        (MEANCHASINESS_TERM, geomean(team_data["chasiness"])),
        (MAXOMNISCIENCE_TERM, max(team_data["omniscience"])),
        (MAXTENACIOUSNESS_TERM, max(team_data["tenaciousness"])),
        (MAXWATCHFULNESS_TERM, max(team_data["watchfulness"])),
        (MAXANTICAPITALISM_TERM, max(team_data["anticapitalism"])),
        (MAXCHASINESS_TERM, max(team_data["chasiness"])))])


def team_offense(teamname, team_stat_data):
    team_data = team_stat_data[teamname]
    return sum([term.calc(val) for term, val in (
        (MEANTRAGICNESS_TERM, geomean(team_data["tragicness"])),
        (MEANPATHETICISM_TERM, geomean(team_data["patheticism"])),
        (MEANTHWACKABILITY_TERM, geomean(team_data["thwackability"])),
        (MEANDIVINITY_TERM, geomean(team_data["divinity"])),
        (MEANMOXIE_TERM, geomean(team_data["moxie"])),
        (MEANMUSCLITUDE_TERM, geomean(team_data["musclitude"])),
        (MEANMARTYRDOM_TERM, geomean(team_data["martyrdom"])),
        (MAXTHWACKABILITY_TERM, max(team_data["thwackability"])),
        (MAXDIVINITY_TERM, max(team_data["divinity"])),
        (MAXMOXIE_TERM, max(team_data["moxie"])),
        (MAXMUSCLITUDE_TERM, max(team_data["musclitude"])),
        (MAXMARTYRDOM_TERM, max(team_data["martyrdom"])),
        (MEANLASERLIKENESS_TERM, geomean(team_data["laserlikeness"])),
        (MEANBASETHIRST_TERM, geomean(team_data["baseThirst"])),
        (MEANCONTINUATION_TERM, geomean(team_data["continuation"])),
        (MEANGROUNDFRICTION_TERM, geomean(team_data["groundFriction"])),
        (MEANINDULGENCE_TERM, geomean(team_data["indulgence"])),
        (MAXLASERLIKENESS_TERM, max(team_data["laserlikeness"])),
        (MAXBASETHIRST_TERM, max(team_data["baseThirst"])),
        (MAXCONTINUATION_TERM, max(team_data["continuation"])),
        (MAXGROUNDFRICTION_TERM, max(team_data["groundFriction"])),
        (MAXINDULGENCE_TERM, max(team_data["indulgence"])))])


def calculate(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data):
    away_offense = team_offense(awayTeam, team_stat_data)
    away_defense = team_defense(awayPitcher, awayTeam, team_stat_data, pitcher_stat_data)
    home_offense = team_offense(homeTeam, team_stat_data)
    home_defense = team_defense(homePitcher, homeTeam, team_stat_data, pitcher_stat_data)
    away_formula = ((away_offense - home_defense) - (home_offense - away_defense)) / ((away_offense - home_defense) + (home_offense - away_defense))
    away_odds = (1 / (1 + 10 ** (-1 * away_formula)))
    return away_odds, 1.0-away_odds