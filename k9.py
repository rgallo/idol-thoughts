from __future__ import division
from __future__ import print_function

from helpers import StlatTerm, geomean

UNTHWACKABILITY_TERM = StlatTerm(0.089674954, 1.0872839, 0.281904938)
RUTHLESSNESS_TERM = StlatTerm(0.107069748, 1.034411286, 2.346612798)
OVERPOWERMENT_TERM = StlatTerm(0.027734668, 1.073308907, 0.341601022)
SHAKESPEARIANISM_TERM = StlatTerm(-0.004224479, 1.608307183, 0.465196612)
COLDNESS_TERM = StlatTerm(-0.00179047, 1.521656776, 0.882645789)
MEANOMNISCIENCE_TERM = StlatTerm(-0.062825441, 1.005597437, 1.194485143)
MEANTENACIOUSNESS_TERM = StlatTerm(0.074409839, 0.980028683, 0.958402819)
MEANWATCHFULNESS_TERM = StlatTerm(0.02526575, 0.955258852, 0.4695063)
MEANANTICAPITALISM_TERM = StlatTerm(0.04345223, 0.926211628, 0.937148111)
MEANCHASINESS_TERM = StlatTerm(0.005904331, 0.644465769, 0.870719208)
MEANTRAGICNESS_TERM = StlatTerm(0.040595617, 0.809805976, 2.00139402)
MEANPATHETICISM_TERM = StlatTerm(0.118242434, 1.049691457, 1.2261867)
MEANTHWACKABILITY_TERM = StlatTerm(-0.028594223, 0.990895967, 1.019858569)
MEANDIVINITY_TERM = StlatTerm(-0.043495322, 1.257207328, 1.048549681)
MEANMOXIE_TERM = StlatTerm(0.039799849, 1.273157969, 0.769471873)
MEANMUSCLITUDE_TERM = StlatTerm(0.02578938, 0.921042014, 0.910753032)
MEANMARTYRDOM_TERM = StlatTerm(-0.020885597, 0.897204988, 1.132067928)
MEANLASERLIKENESS_TERM = StlatTerm(0.043322479, 1.20726684, 0.757741163)
MEANBASETHIRST_TERM = StlatTerm(0.047644788, 1.296563461, 0.892144996)
MEANCONTINUATION_TERM = StlatTerm(-0.028807892, 1.228960825, 1.135451015)
MEANGROUNDFRICTION_TERM = StlatTerm(0.019768205, 1.81363748, 0.821252599)
MEANINDULGENCE_TERM = StlatTerm(0.025817879, 0.896230526, 1.106241331)
MAXOMNISCIENCE_TERM = StlatTerm(-0.014476854, 0.742051229, 1.171276583)
MAXTENACIOUSNESS_TERM = StlatTerm(0.055598999, 1.125509644, 0.965626664)
MAXWATCHFULNESS_TERM = StlatTerm(-0.073942866, 0.69692342, 0.883952176)
MAXANTICAPITALISM_TERM = StlatTerm(-0.022051303, 0.936099024, 1.103882402)
MAXCHASINESS_TERM = StlatTerm(0.086060421, 0.161270994, 1.098153643)
MAXTHWACKABILITY_TERM = StlatTerm(0.110351619, 1.00189273, 0.89907867)
MAXDIVINITY_TERM = StlatTerm(-0.018542275, 1.025798932, 0.832022898)
MAXMOXIE_TERM = StlatTerm(-0.099693566, 1.206071114, 1.034520354)
MAXMUSCLITUDE_TERM = StlatTerm(-0.009967767, 1.00712298, 1.094718238)
MAXMARTYRDOM_TERM = StlatTerm(0.060122129, 0.961712015, 0.906268412)
MAXLASERLIKENESS_TERM = StlatTerm(0.031013057, 0.967503551, 1.12646618)
MAXBASETHIRST_TERM = StlatTerm(-0.038611127, 1.044126966, 1.201291941)
MAXCONTINUATION_TERM = StlatTerm(0.007241572, 1.250293014, 1.046142896)
MAXGROUNDFRICTION_TERM = StlatTerm(-0.014720356, 0.951508371, 1.189285181)
MAXINDULGENCE_TERM = StlatTerm(0.013673622, 1.105139005, 1.227428366)


def calc_pitching(pitcher, pitcher_stat_data):
    pitcher_data = pitcher_stat_data[pitcher]
    return sum([term.calc(val) for term, val in (
        (UNTHWACKABILITY_TERM, pitcher_data["unthwackability"]),
        (RUTHLESSNESS_TERM, pitcher_data["ruthlessness"]),
        (OVERPOWERMENT_TERM, pitcher_data["overpowerment"]),
        (SHAKESPEARIANISM_TERM, pitcher_data["shakespearianism"]),
        (COLDNESS_TERM, pitcher_data["coldness"])
    )])


def calc_everythingelse(pitchingteam, battingteam, team_stat_data):
    pitching_team_data = team_stat_data[pitchingteam]
    batting_team_data = team_stat_data[battingteam]
    return sum([term.calc(val) for term, val in (
        (MEANOMNISCIENCE_TERM, geomean(pitching_team_data["omniscience"])),
        (MEANTENACIOUSNESS_TERM, geomean(pitching_team_data["tenaciousness"])),
        (MEANWATCHFULNESS_TERM, geomean(pitching_team_data["watchfulness"])),
        (MEANANTICAPITALISM_TERM, geomean(pitching_team_data["anticapitalism"])),
        (MEANCHASINESS_TERM, geomean(pitching_team_data["chasiness"])),
        (MEANTRAGICNESS_TERM, geomean(batting_team_data["tragicness"])),
        (MEANPATHETICISM_TERM, geomean(batting_team_data["patheticism"])),
        (MEANTHWACKABILITY_TERM, geomean(batting_team_data["thwackability"])),
        (MEANDIVINITY_TERM, geomean(batting_team_data["divinity"])),
        (MEANMOXIE_TERM, geomean(batting_team_data["moxie"])),
        (MEANMUSCLITUDE_TERM, geomean(batting_team_data["musclitude"])),
        (MEANMARTYRDOM_TERM, geomean(batting_team_data["martyrdom"])),
        (MEANLASERLIKENESS_TERM, geomean(batting_team_data["laserlikeness"])),
        (MEANBASETHIRST_TERM, geomean(batting_team_data["baseThirst"])),
        (MEANCONTINUATION_TERM, geomean(batting_team_data["continuation"])),
        (MEANGROUNDFRICTION_TERM, geomean(batting_team_data["groundFriction"])),
        (MEANINDULGENCE_TERM, geomean(batting_team_data["indulgence"])),
        (MAXOMNISCIENCE_TERM, max(pitching_team_data["omniscience"])),
        (MAXTENACIOUSNESS_TERM, max(pitching_team_data["tenaciousness"])),
        (MAXWATCHFULNESS_TERM, max(pitching_team_data["watchfulness"])),
        (MAXANTICAPITALISM_TERM, max(pitching_team_data["anticapitalism"])),
        (MAXCHASINESS_TERM, max(pitching_team_data["chasiness"])),
        (MAXTHWACKABILITY_TERM, max(batting_team_data["thwackability"])),
        (MAXDIVINITY_TERM, max(batting_team_data["divinity"])),
        (MAXMOXIE_TERM, max(batting_team_data["moxie"])),
        (MAXMUSCLITUDE_TERM, max(batting_team_data["musclitude"])),
        (MAXMARTYRDOM_TERM, max(batting_team_data["martyrdom"])),
        (MAXLASERLIKENESS_TERM, max(batting_team_data["laserlikeness"])),
        (MAXBASETHIRST_TERM, max(batting_team_data["baseThirst"])),
        (MAXCONTINUATION_TERM, max(batting_team_data["continuation"])),
        (MAXGROUNDFRICTION_TERM, max(batting_team_data["groundFriction"])),
        (MAXINDULGENCE_TERM, max(batting_team_data["indulgence"])),
    )])


def calculate(pitcher, pitchingteam, battingteam, team_stat_data, pitcher_stat_data):
    pitching = calc_pitching(pitcher, pitcher_stat_data)
    everythingelse = calc_everythingelse(pitchingteam, battingteam, team_stat_data)
    kplus1PI = (pitching ** 2.03575576619954) + everythingelse - 0.00663786844682817
    k9 = (kplus1PI * 9) - 1
    return round(k9)
