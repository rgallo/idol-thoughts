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
    NUMERATOR_TERMS = ("unthwackability", "ruthlessness", "overpowerment", "shakespearianism", "coldness",
                       "meantragicness", "meanpatheticism", "meanomniscience", "maxomniscience",
                       "meantenaciousness", "maxtenaciousness", "meanwatchfulness", "maxwatchfulness", "meanchasiness",
                       "maxchasiness")
    DENOMINATOR_TERMS = ("meanthwackability", "meandivinity", "meanmoxie", "meanmusclitude", "meanmartyrdom",
                         "maxmartyrdom", "meanlaserlikeness", "maxlaserlikeness", "meanbasethirst", "maxbasethirst",
                         "meancontinuation", "maxcontinuation", "meangroundfriction", "maxgroundfriction",
                         "meanindulgence", "maxindulgence", "maxthwackability", "maxdivinity", "maxmoxie",
                         "maxmusclitude")

    def __init__(self, name, terms, opfunc, cutoff, color):
        self.name = name
        self.terms = terms
        self.opfunc = opfunc
        self.cutoff = cutoff
        self.color = color

    def check(self, stlatdata):
        numerator = sum([self.terms[term].calc(stlatdata[term]) for term in self.NUMERATOR_TERMS])
        denominator = sum([self.terms[term].calc(stlatdata[term]) for term in self.DENOMINATOR_TERMS])
        formula = (numerator / denominator) if denominator else 0
        calc = 1.0 / (1.0 + math.exp(-1 * formula))
        return calc, self.opfunc(calc, self.cutoff) if self.opfunc else True


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
            op, cutoff_value = special_cases["condition"][:2]
            opfunc = operator.gt if op == ">" else operator.ge if op == ">=" else operator.lt if op == "<" else operator.le if op == "<=" else None
            if not opfunc:
                raise Exception("Operator not supported: {}".format(op))
            tim = TIM(name, terms, opfunc, float(cutoff_value), color)
            TIM_TIERS.append(tim)
        TIM_TIERS.append(DEAD_COLD)
    return TIM_TIERS
