from __future__ import division
from __future__ import print_function

import collections
import os
from functools import reduce
import requests

PITCHING_STLATS = ["overpowerment", "ruthlessness", "unthwackability", "shakespearianism", "coldness", "suppression"]
BATTING_STLATS = ["divinity", "martyrdom", "moxie", "musclitude", "patheticism", "thwackability", "tragicness"]
DEFENSE_STLATS = ["anticapitalism", "chasiness", "omniscience", "tenaciousness", "watchfulness"]
BASERUNNING_STLATS = ["baseThirst", "continuation", "groundFriction", "indulgence", "laserlikeness"]
INVERSE_STLATS = ["tragicness", "patheticism"]  # These stlats are better for the target the smaller they are


class StlatTerm:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def calc(self, val):
        b_val = self.b + val
        c_val = 1.0 if (b_val < 0.0 or (b_val < 1.0 and self.c < 0.0)) else self.c        
        return self.a * (b_val ** c_val)

class ParkTerm(StlatTerm):
    def __init__(self, a, b, c):
        super().__init__(a, b, c)

    def calc(self, val):
        b_val = abs(val - 0.5) + self.b
        c_val = self.c        
        return self.a * (b_val ** c_val)


def geomean(numbers):
    correction = .001 if 0.0 in numbers else 0.0
    return (reduce(lambda x, y: x*y, [(n + correction) for n in numbers])**(1.0/len(numbers))) - correction


WEB_CACHE = {}


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


def parse_bp_terms(data):
    results = {}
    splitdata = [d.split(",") for d in data.split("\n")[1:] if d]
    for row in splitdata:
        hometeam, bpstlat, stlat = row[0].lower(), row[1].lower(), row[2].lower()
        results[hometeam][bpstlat][stlat] = ParkTerm(float(row[3]), float(row[4]), float(row[5]))
    return results


def load_terms(term_url, special_cases=None):
    if term_url not in WEB_CACHE:
        special_case_list = [case.lower() for case in special_cases] if special_cases else []
        data = requests.get(term_url, headers={"Authorization": "token {}".format(os.getenv("GITHUB_TOKEN"))}).text
        results, special = parse_terms(data, special_case_list)
        WEB_CACHE[term_url] = (results, special)
    return WEB_CACHE[term_url]


def load_bp_terms(term_url):
    if term_url not in WEB_CACHE:
        data = requests.get(term_url, headers={"Authorization": "token {}".format(os.getenv("GITHUB_TOKEN"))}).text
        results = parse_bp_terms(data)
        WEB_CACHE[term_url] = results
    return WEB_CACHE[term_url]


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
    if mods_url not in WEB_CACHE:
        data = requests.get(mods_url, headers={"Authorization": "token {}".format(os.getenv("GITHUB_TOKEN"))}).text
        mods = parse_mods(data)
        WEB_CACHE[mods_url] = mods
    return WEB_CACHE[mods_url]


def load_data(data_url):
    if data_url not in WEB_CACHE:
        data = requests.get(data_url, headers={"Authorization": "token {}".format(os.getenv("GITHUB_TOKEN"))}).text
        splitdata = [d.split(",") for d in data.split("\n")[1:] if d]
        result = {row[0].lower(): row[1:] for row in splitdata}
        WEB_CACHE[data_url] = result
    return WEB_CACHE[data_url]


WEATHERS = []


def get_weather_idx(weather):
    if not WEATHERS:
        weather_json = requests.get("https://raw.githubusercontent.com/xSke/blaseball-site-files/main/data/weather.json"
                                    "").json()
        WEATHERS.extend([weather["name"] for weather in weather_json])
    return WEATHERS.index(weather)


def load_ballparks(ballparks_url):
    if ballparks_url not in WEB_CACHE:
        stadiums = requests.get(ballparks_url).json()["data"]
        stadium_stlats = {
            row["data"]["teamId"]: {
                key: value for key, value in row["data"].items() if type(value) in (float, int)
            } for row in stadiums
        }
        WEB_CACHE[ballparks_url] = stadium_stlats
    return WEB_CACHE[ballparks_url]


def get_team_id(teamName):
    if "team_id_lookup" not in WEB_CACHE:
        team_id_lookup = {
            team["fullName"]: team["id"] for team in requests.get("https://www.blaseball.com/database/allTeams").json()
        }
        WEB_CACHE["team_id_lookup"] = team_id_lookup
    return WEB_CACHE["team_id_lookup"][teamName]

