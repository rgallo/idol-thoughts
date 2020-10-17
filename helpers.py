from __future__ import division
from __future__ import print_function

import collections
from functools import reduce
import requests


class StlatTerm:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def calc(self, val):
        return self.a * (max(self.b + val, 0.01) ** self.c)


def geomean(numbers):
    correction = .001 if 0.0 in numbers else 0.0
    return (reduce(lambda x, y: x*y, [(n + correction) for n in numbers])**(1.0/len(numbers))) - correction


TERM_RESULTS = {}


def load_terms(term_url, special_cases=None):
    if term_url not in TERM_RESULTS:
        special_case_list = [case.lower() for case in special_cases] if special_cases else []
        results, special = {}, {}
        data = requests.get(term_url).text
        splitdata = [d.split(",") for d in data.split("\n")[1:] if d]
        for row in splitdata:
            name = row[0].lower()
            if name in special_case_list:
                special[name] = row[1:]
            else:
                results[name] = StlatTerm(float(row[1]), float(row[2]), float(row[3]))
        TERM_RESULTS[term_url] = (results, special)
    return TERM_RESULTS[term_url]


MOD_RESULTS = {}


def load_mods(mods_url, day):
    if mods_url not in MOD_RESULTS:
        mods = collections.defaultdict(lambda: {"opp": {}, "same": {}})
        data = requests.get(mods_url).text
        splitdata = [d.split(",") for d in data.split("\n")[1:] if d]
        for row in splitdata:
            attr, team, name = [val.lower() for val in row[:3]]
            a, b, c = float(row[3]), float(row[4]), float(row[5])
            if attr == "growth":
                a, b, c = a * (min(day / 99, 1)), b * (min(day / 99, 1)), c * (min(day / 99, 1))
            mods[attr][team][name] = StlatTerm(a, b, c)
        MOD_RESULTS[mods_url] = mods
    return MOD_RESULTS[mods_url]


WEATHERS = ["Void", "Sunny", "Overcast", "Rainy", "Sandstorm", "Snowy", "Acidic", "Solar Eclipse",
            "Glitter", "Blooddrain", "Peanuts", "Birds", "Feedback", "Reverb"]


def get_weather_idx(weather):
    return WEATHERS.index(weather)
