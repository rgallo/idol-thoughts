from __future__ import division
from __future__ import print_function

from helpers import StlatTerm, geomean

RUTHLESSNESS_TERM = StlatTerm(5.761838436, 1.863956211, 2.359435087)
UNTHWACKABILITY_TERM = StlatTerm(5.628562937, 1.330045351, 1.511686798)
OVERPOWERMENT_TERM = StlatTerm(2.682719692, 1.969547261, 1.911636521)
SHAKESPEARIANISM_TERM = StlatTerm(0.947955776, 1.484704276, 0.595427976)
COLDNESS_TERM = StlatTerm(6.052314371, 2.003271099, 1.122249235)
MEANOMNISCIENCE_TERM = StlatTerm(0.558734347, 1.501202397, 0.682952971)
MEANTENACIOUSNESS_TERM = StlatTerm(-3.050917886, 1.261973335, 1.450999506)
MEANWATCHFULNESS_TERM = StlatTerm(-2.952478693, 1.773605096, 1.594244696)
MEANANTICAPITALISM_TERM = StlatTerm(0.009127423, 0.816798849, 1.378546118)
MEANCHASINESS_TERM = StlatTerm(-2.291002886, 0.436101836, 1.233398352)
MEANTRAGICNESS_TERM = StlatTerm(-2.056832146, 3, 1.494604472)
MEANPATHETICISM_TERM = StlatTerm(0.265762817, 2.06815205, 1.945886955)
MEANTHWACKABILITY_TERM = StlatTerm(4.677415421, 1.541432157, 1.986109719)
MEANDIVINITY_TERM = StlatTerm(0.271394816, 2.156699332, 2.22815622)
MEANMOXIE_TERM = StlatTerm(2.75065124, 1.25762953, 1.573189466)
MEANMUSCLITUDE_TERM = StlatTerm(3.918587744, 1.576323657, 1.289065013)
MEANMARTYRDOM_TERM = StlatTerm(3.569351084, 1.555631473, 1.405199488)
MEANLASERLIKENESS_TERM = StlatTerm(2.102811356, 2.203316348, 1.734613915)
MEANBASETHIRST_TERM = StlatTerm(-0.05904748, 1.646263691, 1.553291906)
MEANCONTINUATION_TERM = StlatTerm(4.955671313, 1.445057055, 2.157180726)
MEANGROUNDFRICTION_TERM = StlatTerm(1.256635179, 2.248094344, 1.586470565)
MEANINDULGENCE_TERM = StlatTerm(-0.7206634, 1.148200263, 1.513829175)
MAXOMNISCIENCE_TERM = StlatTerm(-2.133950329, 1.040456285, 0.86124262)
MAXTENACIOUSNESS_TERM = StlatTerm(-1.754533171, 1.125247407, 2.102632613)
MAXWATCHFULNESS_TERM = StlatTerm(-0.336252721, 1.916210954, 0.828253197)
MAXANTICAPITALISM_TERM = StlatTerm(1.096622608, 1.452743741, 1.783626882)
MAXCHASINESS_TERM = StlatTerm(-2.700589016, 0.735022758, 1.30485437)
MAXTHWACKABILITY_TERM = StlatTerm(4.354958904, 1.436460084, 1.61305774)
MAXDIVINITY_TERM = StlatTerm(0.260677557, 1.547955714, 1.488696861)
MAXMOXIE_TERM = StlatTerm(0.193634075, 0.992151075, 1.898068343)
MAXMUSCLITUDE_TERM = StlatTerm(3.223560985, 1.825785123, 1.485677608)
MAXMARTYRDOM_TERM = StlatTerm(1.181094204, 1.396048857, 0.879521619)
MAXLASERLIKENESS_TERM = StlatTerm(1.006209832, 1.621746145, 1.325796914)
MAXBASETHIRST_TERM = StlatTerm(1.765336524, 0.822273171, 1.49047763)
MAXCONTINUATION_TERM = StlatTerm(0.313321425, 1.233034225, 1.911300007)
MAXGROUNDFRICTION_TERM = StlatTerm(0.426835303, 0.87173141, 0.952125832)
MAXINDULGENCE_TERM = StlatTerm(5.053907278, 1.175737596, 0.631339991)


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
        (MAXOMNISCIENCE_TERM, max(team_data["omniscience"])),
        (MAXTENACIOUSNESS_TERM, max(team_data["tenaciousness"])),
        (MAXWATCHFULNESS_TERM, max(team_data["watchfulness"])),
        (MAXANTICAPITALISM_TERM, max(team_data["anticapitalism"])),
        (MAXCHASINESS_TERM, max(team_data["chasiness"])))])


def team_offense(teamname, team_stat_data):
    team_data = team_stat_data[teamname]
    return sum([term.calc(val) for term, val in (
        (MEANCHASINESS_TERM, geomean(team_data["chasiness"])),
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