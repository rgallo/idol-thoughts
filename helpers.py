from __future__ import division
from __future__ import print_function

import collections
import os
from functools import reduce
import requests


class StlatTerm:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def calc(self, val):
        b_val = self.b + val
        c_val = 1.0 if (b_val < 0.0 or (b_val < 1.0 and self.c < 0.0)) else self.c
        return self.a * (b_val ** c_val)


def geomean(numbers):
    correction = .001 if 0.0 in numbers else 0.0
    return (reduce(lambda x, y: x*y, [(n + correction) for n in numbers])**(1.0/len(numbers))) - correction


TERM_RESULTS = {}


def parse_terms(data, special_case_list):
    results, special = {}, {}
    splitdata = [d.split(",") for d in data.split("\n")[1:] if d]
    for row in splitdata:
        name = row[0].lower()
        if name in special_case_list:
            special[name] = row[1:]
        else:
            results[name] = StlatTerm(float(row[1]), float(row[2]), float(row[3]))
    return results, special


def load_terms(term_url, special_cases=None):
    if term_url not in TERM_RESULTS:
        special_case_list = [case.lower() for case in special_cases] if special_cases else []
        data = requests.get(term_url, headers={"Authorization": "token {}".format(os.getenv("GITHUB_TOKEN"))}).text
        results, special = parse_terms(data, special_case_list)
        TERM_RESULTS[term_url] = (results, special)
    return TERM_RESULTS[term_url]


MOD_RESULTS = {}


def growth_stlatterm(stlatterm, day):
    return StlatTerm(stlatterm.a * (min(day / 99, 1)), stlatterm.b * (min(day / 99, 1)),
                     stlatterm.c * (min(day / 99, 1)))


def parse_mods(data):
    mods = collections.defaultdict(lambda: {"opp": {}, "same": {}})
    splitdata = [d.split(",") for d in data.split("\n")[1:] if d]
    for row in splitdata:
        attr, team, name = [val.lower() for val in row[:3]]
        a, b, c = float(row[3]), float(row[4]), float(row[5])
        mods[attr][team][name] = StlatTerm(a, b, c)
    return mods


def load_mods(mods_url):
    if mods_url not in MOD_RESULTS:
        data = requests.get(mods_url, headers={"Authorization": "token {}".format(os.getenv("GITHUB_TOKEN"))}).text
        mods = parse_mods(data)
        MOD_RESULTS[mods_url] = mods
    return MOD_RESULTS[mods_url]


DATA_RESULTS = {}


def load_data(data_url):
    if data_url not in DATA_RESULTS:
        data = requests.get(data_url, headers={"Authorization": "token {}".format(os.getenv("GITHUB_TOKEN"))}).text
        splitdata = [d.split(",") for d in data.split("\n")[1:] if d]
        result = {row[0].lower(): row[1:] for row in splitdata}
        DATA_RESULTS[data_url] = result
    return DATA_RESULTS[data_url]


WEATHERS = ["Void", "Sun 2", "Overcast", "Rainy", "Sandstorm", "Snowy", "Acidic", "Solar Eclipse",
            "Glitter", "Blooddrain", "Peanuts", "Birds", "Feedback", "Reverb", "Black Hole"]


def get_weather_idx(weather):
    return WEATHERS.index(weather)
