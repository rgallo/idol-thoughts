from __future__ import division
from __future__ import print_function

import math
import operator
import os

from dotenv import load_dotenv

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
    def __init__(self, name, unt_term, rut_term, ovp_term, shp_term, col_term, trg_term, pat_term, thw_term, div_term,
                 mox_term, mus_term, mar_term, opfunc, cutoff, color):
        self.name = name
        self.unt_term = unt_term
        self.rut_term = rut_term
        self.ovp_term = ovp_term
        self.shp_term = shp_term
        self.col_term = col_term
        self.trg_term = trg_term
        self.pat_term = pat_term
        self.thw_term = thw_term
        self.div_term = div_term
        self.mox_term = mox_term
        self.mus_term = mus_term
        self.mar_term = mar_term
        self.opfunc = opfunc
        self.cutoff = cutoff
        self.color = color

    def check(self, unt, rut, ovp, shp, col, trg, pat, thw, div, mox, mus, mar):
        unt_val = self.unt_term.calc(unt)
        rut_val = self.rut_term.calc(rut)
        ovp_val = self.ovp_term.calc(ovp)
        shp_val = self.shp_term.calc(shp)
        col_val = self.col_term.calc(col)
        trg_val = self.trg_term.calc(trg)
        pat_val = self.pat_term.calc(pat)
        thw_val = self.thw_term.calc(thw)
        div_val = self.div_term.calc(div)
        mox_val = self.mox_term.calc(mox)
        mus_val = self.mus_term.calc(mus)
        mar_val = self.mar_term.calc(mar)
        numerator = (unt_val + rut_val + ovp_val + shp_val + col_val + trg_val + pat_val)
        denominator = (thw_val + div_val + mox_val + mus_val + mar_val)
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

DEAD_COLD = TIM(
    "Dead Cold",
    StlatTerm(0.0, 0.0, 0.0),  # UnT
    StlatTerm(0.0, 0.0, 0.0),  # RuT
    StlatTerm(0.0, 0.0, 0.0),  # OvP
    StlatTerm(0.0, 0.0, 0.0),  # ShP
    StlatTerm(0.0, 0.0, 0.0),  # CoL
    StlatTerm(0.0, 0.0, 0.0),  # TrG
    StlatTerm(0.0, 0.0, 0.0),  # PaT
    StlatTerm(0.0, 0.0, 0.0),  # ThW
    StlatTerm(0.0, 0.0, 0.0),  # DiV
    StlatTerm(0.0, 0.0, 0.0),  # MoX
    StlatTerm(0.0, 0.0, 0.0),  # MuS
    StlatTerm(0.0, 0.0, 0.0),  # MaR
    None,
    0,
    PURPLE
)

TIM_ERROR = TIM(
    "ERROR???",
    StlatTerm(0.0, 0.0, 0.0),  # UnT
    StlatTerm(0.0, 0.0, 0.0),  # RuT
    StlatTerm(0.0, 0.0, 0.0),  # OvP
    StlatTerm(0.0, 0.0, 0.0),  # ShP
    StlatTerm(0.0, 0.0, 0.0),  # CoL
    StlatTerm(0.0, 0.0, 0.0),  # TrG
    StlatTerm(0.0, 0.0, 0.0),  # PaT
    StlatTerm(0.0, 0.0, 0.0),  # ThW
    StlatTerm(0.0, 0.0, 0.0),  # DiV
    StlatTerm(0.0, 0.0, 0.0),  # MoX
    StlatTerm(0.0, 0.0, 0.0),  # MuS
    StlatTerm(0.0, 0.0, 0.0),  # MaR
    None,
    0,
    BLACK
)

TIM_TIERS = []


def get_tiers():
    if not TIM_TIERS:
        load_dotenv()
        for name, propname, color in TERMS:
            terms_url = os.getenv(propname)
            terms, special_cases = helpers.load_terms(terms_url, ["condition"])
            op, cutoff_value = special_cases["condition"][:2]
            opfunc = operator.gt if op == ">" else operator.ge if op == ">=" else operator.lt if op == "<" else operator.le if op == "<=" else None
            if not opfunc:
                raise Exception("Operator not supported: {}".format(op))
            tim = TIM(name, terms["unthwackability"], terms["ruthlessness"], terms["overpowerment"],
                      terms["shakespearianism"], terms["coldness"], terms["meantragicness"], terms["meanpatheticism"],
                      terms["meanthwackability"], terms["meandivinity"], terms["meanmoxie"], terms["meanmusclitude"],
                      terms["meanmartyrdom"], opfunc, float(cutoff_value), color)
            TIM_TIERS.append(tim)
        TIM_TIERS.append(DEAD_COLD)
    return TIM_TIERS
