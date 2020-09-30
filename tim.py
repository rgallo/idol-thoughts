from __future__ import division
from __future__ import print_function

import math

# Discord Embed Colors
PINK = 16728779
RED = 13632027
ORANGE = 16752128
YELLOW = 16312092
GREEN = 8311585
BLUE = 4886754
PURPLE = 9442302
BLACK = 1


class TIMTerm:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def calc(self, val):
        return self.a * ((self.b + val) ** self.c)


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
    TIMTerm(0.177322289, 0.0, 2.597944004),  # UnT
    TIMTerm(0.0, 0.0, 0.0),  # RuT
    TIMTerm(0.0, 0.0, 0.0),  # OvP
    TIMTerm(0.0, 0.0, 0.0),  # ShP
    TIMTerm(0.0, 0.0, 0.0),  # CoL
    TIMTerm(0.094588904, 0.016224189, 4.847784146),  # TrG
    TIMTerm(0.832641828, 0.141320159, 3.314225248),  # PaT
    TIMTerm(7.648261191, 0, 3.435681233),  # ThW
    TIMTerm(0.0, 0.0, 0.0),  # DiV
    TIMTerm(9.99961566, 0.183252128, 4.999824451),  # MoX
    TIMTerm(0.0, 0.0, 0.0),  # MuS
    TIMTerm(0.0, 0.0, 0.0),  # MaR
    lambda x: x > 0.772815176,
    PINK
)

HOT = TIM(
    "Hot",
    TIMTerm(0.002145301, 0.066691001, 3.269944529),  # UnT
    TIMTerm(0.0, 0.0, 0.0),  # RuT
    TIMTerm(11.99299272, 0.274987415, 5.999766736),  # OvP
    TIMTerm(0.0, 0.0, 0.0),  # ShP
    TIMTerm(7.519598636, 0.000138072, 5.999257545),  # CoL
    TIMTerm(3.957129029, 0.056104291, 5.428240871),  # TrG
    TIMTerm(0.0, 0.0, 0.0),  # PaT
    TIMTerm(2.349230548, 1.206080018, 4.845805179),  # ThW
    TIMTerm(1.062939319, 0.415779463, 5.975998002),  # DiV
    TIMTerm(3.82691836, 2.241155807, 1.919126386),  # MoX
    TIMTerm(0.200531697, 0.054364085, 2.310488073),  # MuS
    TIMTerm(0.203404099, 0.046397544, 4.952527765),  # MaR
    lambda x: x >= 0.989385278,
    RED
)

WARM = TIM(
    "Warm",
    TIMTerm(0.002145301, 0.066691001, 3.269944529),  # UnT
    TIMTerm(0.0, 0.0, 0.0),  # RuT
    TIMTerm(11.99299272, 0.274987415, 5.999766736),  # OvP
    TIMTerm(0.0, 0.0, 0.0),  # ShP
    TIMTerm(7.519598636, 0.000138072, 5.999257545),  # CoL
    TIMTerm(3.957129029, 0.056104291, 5.428240871),  # TrG
    TIMTerm(0.0, 0.0, 0.0),  # PaT
    TIMTerm(2.349230548, 1.206080018, 4.845805179),  # ThW
    TIMTerm(1.062939319, 0.415779463, 5.975998002),  # DiV
    TIMTerm(3.82691836, 2.241155807, 1.919126386),  # MoX
    TIMTerm(0.200531697, 0.054364085, 2.310488073),  # MuS
    TIMTerm(0.203404099, 0.046397544, 4.952527765),  # MaR
    lambda x: x >= 0.857489627,
    ORANGE
)

TEPID = TIM(
    "Tepid",
    TIMTerm(9.296347588, 1.123548898, 3.128206331),  # UnT
    TIMTerm(8.400990108, 0.858306755, 2.56543587),  # RuT
    TIMTerm(6.432804813, 0.578874091, 3.086524219),  # OvP
    TIMTerm(7.536314297, 0.611823438, 4.104052762),  # ShP
    TIMTerm(5.690347835, 0.71087485, 3.802016902),  # CoL
    TIMTerm(3.085366284, 1.551089242, 2.935376194),  # TrG
    TIMTerm(2.233738838, 0.812370089, 3.077927013),  # PaT
    TIMTerm(6.421824852, 1.069765806, 2.796632602),  # ThW
    TIMTerm(5.828023617, 0.56688689, 3.317837775),  # DiV
    TIMTerm(4.798888123, 1.399638526, 4.363377101),  # MoX
    TIMTerm(8.721443267, 1.433894815, 2.531678849),  # MuS
    TIMTerm(2.4119358, 0.959596028, 2.737780473),  # MaR
    lambda x: x >= 0.746400436,
    YELLOW
)

TEMPERATE = TIM(
    "Temperate",
    TIMTerm(9.296347588, 1.123548898, 3.128206331),  # UnT
    TIMTerm(8.400990108, 0.858306755, 2.56543587),  # RuT
    TIMTerm(6.432804813, 0.578874091, 3.086524219),  # OvP
    TIMTerm(7.536314297, 0.611823438, 4.104052762),  # ShP
    TIMTerm(5.690347835, 0.71087485, 3.802016902),  # CoL
    TIMTerm(3.085366284, 1.551089242, 2.935376194),  # TrG
    TIMTerm(2.233738838, 0.812370089, 3.077927013),  # PaT
    TIMTerm(6.421824852, 1.069765806, 2.796632602),  # ThW
    TIMTerm(5.828023617, 0.56688689, 3.317837775),  # DiV
    TIMTerm(4.798888123, 1.399638526, 4.363377101),  # MoX
    TIMTerm(8.721443267, 1.433894815, 2.531678849),  # MuS
    TIMTerm(2.4119358, 0.959596028, 2.737780473),  # MaR
    lambda x: x >= 0.71954724,
    GREEN
)

COOL = TIM(
    "Cool",
    TIMTerm(9.296347588, 1.123548898, 3.128206331),  # UnT
    TIMTerm(8.400990108, 0.858306755, 2.56543587),  # RuT
    TIMTerm(6.432804813, 0.578874091, 3.086524219),  # OvP
    TIMTerm(7.536314297, 0.611823438, 4.104052762),  # ShP
    TIMTerm(5.690347835, 0.71087485, 3.802016902),  # CoL
    TIMTerm(3.085366284, 1.551089242, 2.935376194),  # TrG
    TIMTerm(2.233738838, 0.812370089, 3.077927013),  # PaT
    TIMTerm(6.421824852, 1.069765806, 2.796632602),  # ThW
    TIMTerm(5.828023617, 0.56688689, 3.317837775),  # DiV
    TIMTerm(4.798888123, 1.399638526, 4.363377101),  # MoX
    TIMTerm(8.721443267, 1.433894815, 2.531678849),  # MuS
    TIMTerm(2.4119358, 0.959596028, 2.737780473),  # MaR
    lambda x: x >= 0.61970085,
    BLUE
)

DEAD_COLD = TIM(
    "Dead Cold",
    TIMTerm(0.0, 0.0, 0.0),  # UnT
    TIMTerm(0.0, 0.0, 0.0),  # RuT
    TIMTerm(0.0, 0.0, 0.0),  # OvP
    TIMTerm(0.0, 0.0, 0.0),  # ShP
    TIMTerm(0.0, 0.0, 0.0),  # CoL
    TIMTerm(0.0, 0.0, 0.0),  # TrG
    TIMTerm(0.0, 0.0, 0.0),  # PaT
    TIMTerm(0.0, 0.0, 0.0),  # ThW
    TIMTerm(0.0, 0.0, 0.0),  # DiV
    TIMTerm(0.0, 0.0, 0.0),  # MoX
    TIMTerm(0.0, 0.0, 0.0),  # MuS
    TIMTerm(0.0, 0.0, 0.0),  # MaR
    lambda x: True,
    PURPLE
)

TIM_ERROR = TIM(
    "ERROR???",
    TIMTerm(0.0, 0.0, 0.0),  # UnT
    TIMTerm(0.0, 0.0, 0.0),  # RuT
    TIMTerm(0.0, 0.0, 0.0),  # OvP
    TIMTerm(0.0, 0.0, 0.0),  # ShP
    TIMTerm(0.0, 0.0, 0.0),  # CoL
    TIMTerm(0.0, 0.0, 0.0),  # TrG
    TIMTerm(0.0, 0.0, 0.0),  # PaT
    TIMTerm(0.0, 0.0, 0.0),  # ThW
    TIMTerm(0.0, 0.0, 0.0),  # DiV
    TIMTerm(0.0, 0.0, 0.0),  # MoX
    TIMTerm(0.0, 0.0, 0.0),  # MuS
    TIMTerm(0.0, 0.0, 0.0),  # MaR
    lambda x: True,
    BLACK
)
