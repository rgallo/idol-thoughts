from __future__ import division
from __future__ import print_function

import operator
import os

import helpers

# Discord Embed Colors
PINK = 16728779
RED = 13632027
ORANGE = 16752128
YELLOW = 16312092
GREEN = 8311585
BLUE = 4886754
PURPLE = 9442302
BLACK = 1


DEFENSE_TERMS = ("unthwackability", "ruthlessness", "overpowerment", "shakespearianism", "coldness",
                 "meantragicness", "meanpatheticism", "meanomniscience", "maxomniscience",
                 "meantenaciousness", "maxtenaciousness", "meanwatchfulness", "maxwatchfulness", "meanchasiness",
                 "maxchasiness", "meananticapitalism", "maxanticapitalism")
OFFENSE_TERMS = ("meanthwackability", "meandivinity", "meanmoxie", "meanmusclitude", "meanmartyrdom",
                 "maxmartyrdom", "meanlaserlikeness", "maxlaserlikeness", "meanbasethirst", "maxbasethirst",
                 "meancontinuation", "maxcontinuation", "meangroundfriction", "maxgroundfriction",
                 "meanindulgence", "maxindulgence", "maxthwackability", "maxdivinity", "maxmoxie",
                 "maxmusclitude")


class TIM:
    def __init__(self, name, lower_val, upper_val, lower_op, upper_op, color):
        self.name = name
        self.lower_val = lower_val
        self.upper_val = upper_val
        self.lower_op = lower_op
        self.upper_op = upper_op
        self.color = color

    def check(self, val):
        return self.lower_op(val, self.lower_val) and self.upper_op(val, self.upper_val)


TIER_PARAMS = {
    "dead_cold": ("Dead Cold", operator.ge, operator.lt, PURPLE),
    "cool": ("Cool", operator.ge, operator.lt, BLUE),
    "temperate": ("Temperate", operator.ge, operator.lt, GREEN),
    "tepid": ("Tepid", operator.ge, operator.lt, YELLOW),
    "warm": ("Warm", operator.ge, operator.lt, ORANGE),
    "hot": ("Hot", operator.ge, operator.le, RED),
    "red_hot": ("Red Hot", lambda a, b: True, lambda a, b: True, PINK),
}

TIM_ERROR = TIM("ERROR???", -1, -1, lambda a, b: True, lambda a, b: True, BLACK)

TIM_TIERS = []


def setup():
    terms_url = os.getenv("TIM_TERMS")
    terms, _ = helpers.load_terms(terms_url)
    if not TIM_TIERS:
        conditions_url = os.getenv("TIM_CONDITIONS")
        conditions = helpers.load_data(conditions_url)
        for tier_lookup_name, (tier_lower_val, tier_upper_val) in conditions.items():
            tier_name, tier_lower_op, tier_upper_op, tier_color = TIER_PARAMS[tier_lookup_name.lower()]
            TIM_TIERS.append(TIM(tier_name, float(tier_lower_val), float(tier_upper_val), tier_lower_op, tier_upper_op, tier_color))
    return terms, TIM_TIERS


def get_tim_value(terms, stlatdata):
    defense = sum([terms[term].calc(stlatdata[term]) for term in DEFENSE_TERMS])
    offense = sum([terms[term].calc(stlatdata[term]) for term in OFFENSE_TERMS])
    numerator = defense - offense
    denominator = defense + offense
    formula = (numerator / denominator) if denominator else 0
    calc = 1.0 / (1.0 + (100 ** (-1 * formula)))
    return calc


def get_tim_tier(val, tiers):
    for rank, tier in enumerate(tiers):
        if tier.check(val):
            return tier, rank
    return TIM_ERROR, -1


def calculate(stlatdata):
    terms, tiers = setup()
    val = get_tim_value(terms, stlatdata)
    tier, rank = get_tim_tier(val, tiers)
    return tier, rank, val