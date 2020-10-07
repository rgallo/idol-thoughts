from __future__ import division
from __future__ import print_function

import math
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
                 mox_term, mus_term, mar_term, condition, color):
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
        self.condition = condition
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
        return calc, self.condition(calc)


RED_HOT = TIM(
    "Red Hot",
    StlatTerm(0.177322289, 0.0, 2.597944004),  # UnT
    StlatTerm(0.0, 0.0, 0.0),  # RuT
    StlatTerm(0.0, 0.0, 0.0),  # OvP
    StlatTerm(0.0, 0.0, 0.0),  # ShP
    StlatTerm(0.0, 0.0, 0.0),  # CoL
    StlatTerm(0.094588904, 0.016224189, 4.847784146),  # TrG
    StlatTerm(0.832641828, 0.141320159, 3.314225248),  # PaT
    StlatTerm(7.648261191, 0, 3.435681233),  # ThW
    StlatTerm(0.0, 0.0, 0.0),  # DiV
    StlatTerm(9.99961566, 0.183252128, 4.999824451),  # MoX
    StlatTerm(0.0, 0.0, 0.0),  # MuS
    StlatTerm(0.0, 0.0, 0.0),  # MaR
    lambda x: x > 0.772815176,
    PINK
)

HOT = TIM(
    "Hot",
    StlatTerm(0.002145301, 0.066691001, 3.269944529),  # UnT
    StlatTerm(0.0, 0.0, 0.0),  # RuT
    StlatTerm(11.99299272, 0.274987415, 5.999766736),  # OvP
    StlatTerm(0.0, 0.0, 0.0),  # ShP
    StlatTerm(7.519598636, 0.000138072, 5.999257545),  # CoL
    StlatTerm(3.957129029, 0.056104291, 5.428240871),  # TrG
    StlatTerm(0.0, 0.0, 0.0),  # PaT
    StlatTerm(2.349230548, 1.206080018, 4.845805179),  # ThW
    StlatTerm(1.062939319, 0.415779463, 5.975998002),  # DiV
    StlatTerm(3.82691836, 2.241155807, 1.919126386),  # MoX
    StlatTerm(0.200531697, 0.054364085, 2.310488073),  # MuS
    StlatTerm(0.203404099, 0.046397544, 4.952527765),  # MaR
    lambda x: x >= 0.989385278,
    RED
)

WARM = TIM(
    "Warm",
    StlatTerm(0.002145301, 0.066691001, 3.269944529),  # UnT
    StlatTerm(0.0, 0.0, 0.0),  # RuT
    StlatTerm(11.99299272, 0.274987415, 5.999766736),  # OvP
    StlatTerm(0.0, 0.0, 0.0),  # ShP
    StlatTerm(7.519598636, 0.000138072, 5.999257545),  # CoL
    StlatTerm(3.957129029, 0.056104291, 5.428240871),  # TrG
    StlatTerm(0.0, 0.0, 0.0),  # PaT
    StlatTerm(2.349230548, 1.206080018, 4.845805179),  # ThW
    StlatTerm(1.062939319, 0.415779463, 5.975998002),  # DiV
    StlatTerm(3.82691836, 2.241155807, 1.919126386),  # MoX
    StlatTerm(0.200531697, 0.054364085, 2.310488073),  # MuS
    StlatTerm(0.203404099, 0.046397544, 4.952527765),  # MaR
    lambda x: x >= 0.857489627,
    ORANGE
)

TEPID = TIM(
    "Tepid",
    StlatTerm(9.296347588, 1.123548898, 3.128206331),  # UnT
    StlatTerm(8.400990108, 0.858306755, 2.56543587),  # RuT
    StlatTerm(6.432804813, 0.578874091, 3.086524219),  # OvP
    StlatTerm(7.536314297, 0.611823438, 4.104052762),  # ShP
    StlatTerm(5.690347835, 0.71087485, 3.802016902),  # CoL
    StlatTerm(3.085366284, 1.551089242, 2.935376194),  # TrG
    StlatTerm(2.233738838, 0.812370089, 3.077927013),  # PaT
    StlatTerm(6.421824852, 1.069765806, 2.796632602),  # ThW
    StlatTerm(5.828023617, 0.56688689, 3.317837775),  # DiV
    StlatTerm(4.798888123, 1.399638526, 4.363377101),  # MoX
    StlatTerm(8.721443267, 1.433894815, 2.531678849),  # MuS
    StlatTerm(2.4119358, 0.959596028, 2.737780473),  # MaR
    lambda x: x >= 0.746400436,
    YELLOW
)

TEMPERATE = TIM(
    "Temperate",
    StlatTerm(9.296347588, 1.123548898, 3.128206331),  # UnT
    StlatTerm(8.400990108, 0.858306755, 2.56543587),  # RuT
    StlatTerm(6.432804813, 0.578874091, 3.086524219),  # OvP
    StlatTerm(7.536314297, 0.611823438, 4.104052762),  # ShP
    StlatTerm(5.690347835, 0.71087485, 3.802016902),  # CoL
    StlatTerm(3.085366284, 1.551089242, 2.935376194),  # TrG
    StlatTerm(2.233738838, 0.812370089, 3.077927013),  # PaT
    StlatTerm(6.421824852, 1.069765806, 2.796632602),  # ThW
    StlatTerm(5.828023617, 0.56688689, 3.317837775),  # DiV
    StlatTerm(4.798888123, 1.399638526, 4.363377101),  # MoX
    StlatTerm(8.721443267, 1.433894815, 2.531678849),  # MuS
    StlatTerm(2.4119358, 0.959596028, 2.737780473),  # MaR
    lambda x: x >= 0.71954724,
    GREEN
)

COOL = TIM(
    "Cool",
    StlatTerm(9.296347588, 1.123548898, 3.128206331),  # UnT
    StlatTerm(8.400990108, 0.858306755, 2.56543587),  # RuT
    StlatTerm(6.432804813, 0.578874091, 3.086524219),  # OvP
    StlatTerm(7.536314297, 0.611823438, 4.104052762),  # ShP
    StlatTerm(5.690347835, 0.71087485, 3.802016902),  # CoL
    StlatTerm(3.085366284, 1.551089242, 2.935376194),  # TrG
    StlatTerm(2.233738838, 0.812370089, 3.077927013),  # PaT
    StlatTerm(6.421824852, 1.069765806, 2.796632602),  # ThW
    StlatTerm(5.828023617, 0.56688689, 3.317837775),  # DiV
    StlatTerm(4.798888123, 1.399638526, 4.363377101),  # MoX
    StlatTerm(8.721443267, 1.433894815, 2.531678849),  # MuS
    StlatTerm(2.4119358, 0.959596028, 2.737780473),  # MaR
    lambda x: x >= 0.61970085,
    BLUE
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
    lambda x: True,
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
    lambda x: True,
    BLACK
)


def get_tiers():
    return [RED_HOT, HOT, WARM, TEPID, TEMPERATE, COOL, DEAD_COLD]
