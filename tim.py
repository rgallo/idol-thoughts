from __future__ import division
from __future__ import print_function

import collections
import math
import operator
import os

import helpers
from helpers import StlatTerm

# Discord Embed Colors
PINK = 16728779
RED = 13632027
ORANGE = 16752128
YELLOW = 16312092
GREEN = 8311585
BLUE = 4886754
PURPLE = 9442302
BLACK = 1


class TIM:
    DEFENSE_TERMS = ("unthwackability", "ruthlessness", "overpowerment", "shakespearianism", "coldness",
                     "meantragicness", "meanpatheticism", "meanomniscience", "maxomniscience",
                     "meantenaciousness", "maxtenaciousness", "meanwatchfulness", "maxwatchfulness", "meanchasiness",
                     "maxchasiness", "meananticapitalism", "maxanticapitalism")
    OFFENSE_TERMS = ("meanthwackability", "meandivinity", "meanmoxie", "meanmusclitude", "meanmartyrdom",
                     "maxmartyrdom", "meanlaserlikeness", "maxlaserlikeness", "meanbasethirst", "maxbasethirst",
                     "meancontinuation", "maxcontinuation", "meangroundfriction", "maxgroundfriction",
                     "meanindulgence", "maxindulgence", "maxthwackability", "maxdivinity", "maxmoxie",
                     "maxmusclitude")

    def __init__(self, name, terms, opfuncs, cutoffs, color):
        self.name = name
        self.terms = terms
        self.opfuncs = opfuncs
        self.cutoffs = cutoffs
        self.color = color

    def calc(self, stlatdata):
        defense = sum([self.terms[term].calc(stlatdata[term]) for term in self.DEFENSE_TERMS])
        offense = sum([self.terms[term].calc(stlatdata[term]) for term in self.OFFENSE_TERMS])
        numerator = defense - offense
        denominator = defense + offense
        formula = (numerator / denominator) if denominator else 0
        calc = 1.0 / (1.0 + math.exp(-1 * formula))
        return calc

    def check(self, stlatdata):
        calc = self.calc(stlatdata)
        return calc, all(opfunc(calc, cutoff) if opfunc else True for opfunc, cutoff in zip(self.opfuncs, self.cutoffs)) if self.opfuncs else True


TERMS = (
    ("Red Hot", "REDHOT_TERMS", PINK),
    ("Hot", "HOT_TERMS", RED),
    ("Warm", "WARM_TERMS", ORANGE),
    ("Tepid", "TEPID_TERMS", YELLOW),
    ("Temperate", "TEMPERATE_TERMS", GREEN),
    ("Cool", "COOL_TERMS", BLUE),
)

DEAD_COLD = TIM("Dead Cold", collections.defaultdict(lambda: StlatTerm(0.0, 0.0, 0.0)), None, 0, PURPLE)

TIM_ERROR = TIM("ERROR???", collections.defaultdict(lambda: StlatTerm(0.0, 0.0, 0.0)), None, 0, BLACK)

TIM_TIERS = []


def get_tiers():
    if not TIM_TIERS:
        for name, propname, color in TERMS:
            terms_url = os.getenv(propname)
            terms, special_cases = helpers.load_terms(terms_url, ["condition"])
            opfuncs, cutoffs = [], []
            for condition in special_cases["condition"]:
                if not condition:
                    continue
                op, cutoff = condition.split(":")
                opfunc = operator.gt if op == ">" else operator.ge if op == ">=" else operator.lt if op == "<" else operator.le if op == "<=" else None
                if not opfunc:
                    raise Exception("Operator not supported: {}".format(op))
                opfuncs.append(opfunc)
                cutoffs.append(float(cutoff))
            tim = TIM(name, terms, opfuncs, cutoffs, color)
            TIM_TIERS.append(tim)
        TIM_TIERS.append(DEAD_COLD)
    return TIM_TIERS
