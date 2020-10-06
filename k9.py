from __future__ import division
from __future__ import print_function

from helpers import StlatTerm, geomean

UNTHWACKABILITY_TERM = StlatTerm(-0.030500297, 1.094857761, 1.11230341)
RUTHLESSNESS_TERM = StlatTerm(0.280751865, 1.074546622, 1.427802353)
OVERPOWERMENT_TERM = StlatTerm(-0.042030409, 0.864437606, 0.472691963)
SHAKESPEARIANISM_TERM = StlatTerm(0.082459858, 1.132132047, 0.705654246)
COLDNESS_TERM = StlatTerm(-0.086072927, 1.205537128, 0.660351645)
MEANOMNISCIENCE_TERM = StlatTerm(-0.055408466, 1.219657152, 1.019002813)
MEANTENACIOUSNESS_TERM = StlatTerm(-0.094923468, 1.059394398, 1.222637745)
MEANWATCHFULNESS_TERM = StlatTerm(-0.023590476, 0.759601795, 1.266757998)
MEANANTICAPITALISM_TERM = StlatTerm(0.071242941, 0.840142582, 1.62329898)
MEANCHASINESS_TERM = StlatTerm(0.019929625, 1.081799047, 1.535314596)
MEANTRAGICNESS_TERM = StlatTerm(-0.057123202, 1.368456609, 1.534048735)
MEANPATHETICISM_TERM = StlatTerm(0.075780076, 0.718738394, 1.573099786)
MEANTHWACKABILITY_TERM = StlatTerm(0.017306283, 1.824816737, 1.633909264)
MEANDIVINITY_TERM = StlatTerm(-0.086789575, 1.595263687, 1.259839951)
MEANMOXIE_TERM = StlatTerm(-0.085112783, 0.631532938, 1.301341723)
MEANMUSCLITUDE_TERM = StlatTerm(0.022078846, 0.799772898, 1.47678487)
MEANMARTYRDOM_TERM = StlatTerm(0.020567984, 1.069240894, 1.463027701)
MEANLASERLIKENESS_TERM = StlatTerm(0.034655413, 1.030304101, 1.607294435)
MEANBASETHIRST_TERM = StlatTerm(0.047996353, 0.773827785, 0.491171334)
MEANCONTINUATION_TERM = StlatTerm(0.005896843, 1.241755771, 1.33153256)
MEANGROUNDFRICTION_TERM = StlatTerm(-0.165681523, 0.663688448, 1.572433503)
MEANINDULGENCE_TERM = StlatTerm(0.000666886, 1.15621154, 1.087888348)
MAXOMNISCIENCE_TERM = StlatTerm(-0.034852745, 0.981809634, 1.150195466)
MAXTENACIOUSNESS_TERM = StlatTerm(0.067420812, 1.216769849, 0.912418993)
MAXWATCHFULNESS_TERM = StlatTerm(0.054110063, 1.200199782, 1.448410334)
MAXANTICAPITALISM_TERM = StlatTerm(0.097823355, 0.801566927, 0.986283588)
MAXCHASINESS_TERM = StlatTerm(-0.070522902, 0.863661062, 1.404192307)
MAXTHWACKABILITY_TERM = StlatTerm(0.207581574, 1.040098448, 1.075372881)
MAXDIVINITY_TERM = StlatTerm(-0.096718229, 0.839218972, 0.766645883)
MAXMOXIE_TERM = StlatTerm(-0.137484877, 1.411317182, 1.091323622)
MAXMUSCLITUDE_TERM = StlatTerm(-0.016538052, 1.352422786, 1.198896648)
MAXMARTYRDOM_TERM = StlatTerm(0.058071464, 0.990440868, 1.412605859)
MAXLASERLIKENESS_TERM = StlatTerm(0.104896742, 0.942186928, 1.055194832)
MAXBASETHIRST_TERM = StlatTerm(0.013791491, 0.983883315, 1.605370897)
MAXCONTINUATION_TERM = StlatTerm(-0.004446567, 1.036673655, 1.995913916)
MAXGROUNDFRICTION_TERM = StlatTerm(0.124388781, 1.352087159, 1.455471326)
MAXINDULGENCE_TERM = StlatTerm(0.053206884, 1.090320921, 1.143201869)


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
    kplus1PI = (pitching ** 1.92728213507654) + everythingelse - 0.246123019416862
    k9 = (kplus1PI * 9) - 1
    return round(k9)
