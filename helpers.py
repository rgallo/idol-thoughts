from __future__ import division
from __future__ import print_function

import argparse
import collections
import csv
import json
import linecache
import operator
import os
import random
import sys
import time
import copy
from functools import reduce
import requests
from discord_webhook import DiscordWebhook, DiscordEmbed
from blaseball_stat_csv import blaseball_stat_csv

PITCHING_STLATS = ["overpowerment", "ruthlessness", "unthwackability", "shakespearianism", "coldness", "suppression"]
BATTING_STLATS = ["divinity", "martyrdom", "moxie", "musclitude", "patheticism", "thwackability", "tragicness"]
DEFENSE_STLATS = ["anticapitalism", "chasiness", "omniscience", "tenaciousness", "watchfulness"]
BASERUNNING_STLATS = ["baseThirst", "continuation", "groundFriction", "indulgence", "laserlikeness"]
OFFENSE_STLATS = ["divinity", "martyrdom", "moxie", "musclitude", "patheticism", "thwackability", "tragicness", "basethirst", "continuation", "groundfriction", "indulgence", "laserlikeness"]
INVERSE_STLATS = ["tragicness", "patheticism"]  # These stlats are better for the target the smaller they are

LAST_SEASON_STAT_CUTOFF = 11
DISCORD_SPLIT_LIMIT = 1900


class StlatTerm:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def calc(self, val):
        b_val = self.b * val
        c_val = 1.0 if (b_val < 0.0 or (b_val < 1.0 and self.c < 0.0)) else self.c        
        calc_val = self.a * (b_val ** c_val)        
        return calc_val

    #def calc(self, val):
    #    b_val = self.b 
    #    c_val = self.c ** (val * b_val)
    #    calc_val = self.a * c_val
    #    return calc_val

class ParkTerm(StlatTerm):
    def __init__(self, a, b, c):
        super().__init__(a, b, c)

    def calc(self, val):
        b_val = val * self.b
        c_val = self.c       
        calc_val = self.a * (b_val ** c_val)        
        return calc_val

    #def calc(self, val):
    #    b_val = self.b 
    #    c_val = self.c ** (val * b_val)
    #    calc_val = self.a * c_val
    #    return calc_val


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

def parse_half_terms(data):
    results = collections.defaultdict(lambda: {})
    splitdata = [d.split(",") for d in data.split("\n")[1:] if d]
    for row in splitdata:
        name, event = row[0].lower(), row[1].lower()        
        results[name][event] = float(row[2])
    return results

def parse_bp_terms(data):
    results = collections.defaultdict(lambda: {"bpterm": {}})
    splitdata = [d.split(",") for d in data.split("\n")[1:] if d]
    for row in splitdata:
        bpstlat, stlat = row[0].lower(), row[1].lower()        
        results[bpstlat][stlat] = ParkTerm(float(row[2]), float(row[3]), float(row[4]))
    return results

def load_terms(term_url, special_cases=None):
    if term_url not in WEB_CACHE:
        special_case_list = [case.lower() for case in special_cases] if special_cases else []
        data = requests.get(term_url, headers={"Authorization": "token {}".format(os.getenv("GITHUB_TOKEN"))}).text
        results, special = parse_terms(data, special_case_list)
        WEB_CACHE[term_url] = (results, special)
    return WEB_CACHE[term_url]

def load_half_terms(term_url):
    if term_url not in WEB_CACHE:        
        data = requests.get(term_url, headers={"Authorization": "token {}".format(os.getenv("GITHUB_TOKEN"))}).text
        results = parse_half_terms(data)
        WEB_CACHE[term_url] = results
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
        a = float(row[3])
        mods[attr][team][name] = a
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


class PrintWebhook:
    def __init__(self, content=None, **kwargs):
        self.content = content
        self.embeds = []

    def add_embed(self, embed):
        self.embeds.append(embed)

    def execute(self):
        if self.content:
            print(self.content)
        for embed in self.embeds:
            print(embed)


class PrintEmbed:
    def __init__(self, description=None, **kwargs):
        self.description = description

    def __repr__(self):
        return "{}\n{}".format(discord_hr(), self.description)


def discord_hr(spaces=25, char=" "):
    return "~~-{}-~~".format(char * spaces)


def send_discord_message(title, message, screen=False, webhook_url=None):
    Webhook, Embed = (PrintWebhook, PrintEmbed) if screen else (DiscordWebhook, DiscordEmbed)
    discord_webhook_url = (webhook_url or os.getenv("DISCORD_WEBHOOK_URL")).split(";")
    webhook = Webhook(url=discord_webhook_url)
    webhook.add_embed(Embed(title=title, description=message))
    return webhook.execute()


def already_ran_for_day(filepath, season_number, day):
    if os.path.isfile(filepath):
        with open(filepath, "r") as f:
            file_season_number, file_day = (int(n) for n in f.read().split("-"))
            return file_season_number == season_number and file_day == day
    return False


def write_day(filepath, season_number, day):
    with open(filepath, "w") as f:
        f.write("{}-{}".format(season_number, day))


def outcome_matters(outcome):
    return all(s not in outcome for s in ("is now Unstable", "is now Flickering", "Red Hot", "is now Repeating",
                                          "Black Hole swallowed a Win", "Sun 2 set a Win upon"))


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--print', help="print to screen", action='store_true')
    parser.add_argument('--discord', help="output to discord", action='store_true')
    parser.add_argument('--discordprint', help="print discord-formatted output to screen", action='store_true')
    parser.add_argument('--statfile', default='output.csv', help="stats filepath")
    parser.add_argument('--dayfile', default='lastday.txt', help="dayfile filepath")
    parser.add_argument('--today', help="run for today instead of tomorrow", action='store_true')
    parser.add_argument('--skipupdate', help="skip csv update, even if there should be one", action='store_true')
    parser.add_argument('--forceupdate', help="force csv update, even if it doesn't need it", action='store_true')
    parser.add_argument('--forcerun', help="force running for day, even if it was already run last",
                        action='store_true')
    parser.add_argument('--archive', help="move csv file if a new one is regenerated before writing",
                        action='store_true')
    parser.add_argument('--testfile', help="path to file with test data in jsonl format, pass optional line number as "
                                           "filename:n, otherwise random line is used")
    parser.add_argument('--env', help="path to .env file, defaults to .env in same directory")
    parser.add_argument('--justlooking', help="don't update lastday file", action='store_true')
    args = parser.parse_args()
    if not args.print and not args.discord and not args.discordprint:
        print("No output specified")
        parser.print_help()
        sys.exit(-1)
    return args


def load_test_data(testfile):
    filename, linenumber = testfile, None
    if ":" in testfile:
        filename, linenumber = testfile.split(":")
    else:
        with open(filename) as f:
            for i, l in enumerate(f):
                pass
        linenumber = random.randint(1, i + 1)
    print("Loading test data from {}, line {}".format(filename, linenumber))
    return json.loads(linecache.getline(filename, int(linenumber)))


def get_blaseball_snapshot():
    snapshot = None
    response = requests.get("https://www.blaseball.com/events/streamData", stream=True)
    for line in response.iter_lines():
        snapshot = line
        break
    try:
        json_snapshot = json.loads(snapshot.decode("utf-8")[6:])
    except json.decoder.JSONDecodeError:
        return None
    return json_snapshot


def get_testing_snapshot():
    snapshot = None
    with requests.get("https://api-test.sibr.dev/replay/v1/replay?from=2020-10-19T22:45:00Z", stream=True) as response:
        for line in response.iter_lines():
            if line and line.decode("utf-8").startswith("data"):
                snapshot = line
                break
    try:
        json_snapshot = json.loads(snapshot.decode("utf-8")[5:])
    except json.decoder.JSONDecodeError:
        return None
    return json_snapshot


def get_stream_snapshot():
    json_snapshot = None
    retries = 0
    while json_snapshot is None and retries < 5:
        if retries:
            time.sleep(2)  # Sleep after first time
        json_snapshot = get_blaseball_snapshot()
        retries += 1
    if not json_snapshot:
        raise Exception("Unable to get stream snapshot")
    return json_snapshot


def adjust_by_pct(row, pct, stlats, star_func):
    new_row = row.copy()
    original_stars = star_func(row)
    new_stars = original_stars
    op = operator.lt if pct >= 0.0 else operator.gt
    while op(new_stars, original_stars * (1.0 + pct)):
        for stlat in stlats:
            if pct >= 0.0:
                #if stlat in INVERSE_STLATS and stlat != "tragicness":
                if stlat in INVERSE_STLATS:
                    new_row[stlat] = max(float(new_row[stlat]) - .01, .001)
                elif stlat not in INVERSE_STLATS:
                    new_row[stlat] = float(new_row[stlat]) + .01
            else:
                #if stlat in INVERSE_STLATS and stlat != "tragicness":
                if stlat in INVERSE_STLATS:
                    new_row[stlat] = float(new_row[stlat]) + .01
                elif stlat not in INVERSE_STLATS:
                    new_row[stlat] = max(float(new_row[stlat]) - .01, .001)
        new_stars = star_func(new_row)
    return new_row

def adjust_by_blood_pct(row, pct, stlats, star_func, bloodpct):
    new_row = row.copy()
    adjusted_stlats = row.copy()
    adjusted_stlats = adjust_by_pct(adjusted_stlats, pct, stlats, star_func)
    for stlat in stlats:
        new_row[stlat] = float(row[stlat]) + ((float(adjusted_stlats[stlat]) - float(row[stlat])) * bloodpct)
    return new_row


def batting_stars(player):
    return (
        ((1 - float(player["tragicness"])) ** 0.01)        
        * (float(player["thwackability"]) ** 0.35)
        * (float(player["moxie"]) ** 0.075)
        * (float(player["divinity"]) ** 0.35)
        * (float(player["musclitude"]) ** 0.075)
        * ((1 - float(player["patheticism"])) ** 0.05)
        * (float(player["martyrdom"]) ** 0.02)
        * 5.0
    )


def pitching_stars(player):
    return (
        (float(player["shakespearianism"]) ** 0.1)        
        * (float(player["unthwackability"]) ** 0.5)
        * (float(player["coldness"]) ** 0.025)
        * (float(player["overpowerment"]) ** 0.15)
        * (float(player["ruthlessness"]) ** 0.4)
        * 5.0
    )


def baserunning_stars(player):
    return (
        (float(player["laserlikeness"]) ** 0.5)
        * (float(player["continuation"]) ** 0.1)
        * (float(player["baseThirst"]) ** 0.1)
        * (float(player["indulgence"]) ** 0.1)
        * (float(player["groundFriction"]) ** 0.1)
        * 5.0
    )


def defense_stars(player):
    return (
        (float(player["omniscience"]) ** 0.2)
        * (float(player["tenaciousness"]) ** 0.2)
        * (float(player["watchfulness"]) ** 0.1)
        * (float(player["anticapitalism"]) ** 0.1)
        * (float(player["chasiness"]) ** 0.1)
        * 5.0
    )


def get_team_attributes(attributes={}):
    if not attributes:
        attributes.update({team["fullName"]: (team["gameAttr"] + team["weekAttr"] + team["seasAttr"] + team["permAttr"]) for team in requests.get("https://www.blaseball.com/database/allTeams").json()})
    return attributes


def adjust_stlats(row, game, day, roster_size, raw_player_attrs, team_attrs=None):
    blood_count = 12.0
    blood_pct = 1.0 / blood_count
    player_attrs = []
    for attr in raw_player_attrs.split(";"):
        if attr.lower() != "":
            player_attrs.append(attr.upper())      
    new_row = row.copy()
    if game:
        team = row["team"]
        coffee_weathers = [get_weather_idx("Coffee"), get_weather_idx("Coffee 2"), get_weather_idx("Coffee 3s")]
        bird_weather = get_weather_idx("Birds")
        current_team_attrs = (team_attrs if team_attrs is not None else get_team_attributes()).get(team, {})                     

        overperforming = ("EARLBIRDS" in current_team_attrs and 1 <= day <= 27) or (("MIDDLING" in current_team_attrs or "MIDDLING" in player_attrs) and 28 <= day <= 72) or (("LATE_TO_PARTY" in current_team_attrs or "LATE_TO_PARTY" in player_attrs) and 73 <= day <= 99) or ("OVERPERFORMING" in current_team_attrs) or ("OVERPERFORMING" in player_attrs) or (("AMBITIOUS" in current_team_attrs or "AMBITIOUS" in player_attrs) and day > 99) or ("PERK" in player_attrs and game["weather"] in coffee_weathers) or ("HOMEBODY" in player_attrs and team == game["homeTeamName"])
        underperforming = (("COASTING" in current_team_attrs or "COASTING" in player_attrs) and 28 <= day <= 72) or ("EARLY_TO_PARTY" in current_team_attrs and 73 <= day <= 99) or ("UNDERPERFORMING" in current_team_attrs) or ("UNDERPERFORMING" in player_attrs) or (("UNAMBITIOUS" in current_team_attrs or "UNAMBITIOUS" in player_attrs) and day > 99) or ("HOMEBODY" in player_attrs and team == game["awayTeamName"])
    
        if underperforming:
            new_row = adjust_by_pct(new_row, -0.2, PITCHING_STLATS, pitching_stars)
            new_row = adjust_by_pct(new_row, -0.2, BATTING_STLATS, batting_stars)
            new_row = adjust_by_pct(new_row, -0.2, BASERUNNING_STLATS, baserunning_stars)
            new_row = adjust_by_pct(new_row, -0.2, DEFENSE_STLATS, defense_stars)
        if overperforming:
            new_row = adjust_by_pct(new_row, 0.2, PITCHING_STLATS, pitching_stars)
            new_row = adjust_by_pct(new_row, 0.2, BATTING_STLATS, batting_stars)
            new_row = adjust_by_pct(new_row, 0.2, BASERUNNING_STLATS, baserunning_stars)
            new_row = adjust_by_pct(new_row, 0.2, DEFENSE_STLATS, defense_stars)
        if "SINKING_SHIP" in current_team_attrs:
            growth_pct = .01 * (14 - roster_size)
            new_row = adjust_by_pct(new_row, growth_pct, PITCHING_STLATS, pitching_stars)
            new_row = adjust_by_pct(new_row, growth_pct, BATTING_STLATS, batting_stars)
            new_row = adjust_by_pct(new_row, growth_pct, BASERUNNING_STLATS, baserunning_stars)
            new_row = adjust_by_pct(new_row, growth_pct, DEFENSE_STLATS, defense_stars)
        if "GROWTH" in current_team_attrs:
            growth_pct = .05 * min(day / 99, 1.0)
            new_row = adjust_by_pct(new_row, growth_pct, PITCHING_STLATS, pitching_stars)
            new_row = adjust_by_pct(new_row, growth_pct, BATTING_STLATS, batting_stars)
            new_row = adjust_by_pct(new_row, growth_pct, BASERUNNING_STLATS, baserunning_stars)
            new_row = adjust_by_pct(new_row, growth_pct, DEFENSE_STLATS, defense_stars)                       
        if "TRAVELING" in current_team_attrs and team == game["awayTeamName"]:
            new_row = adjust_by_pct(new_row, 0.05, PITCHING_STLATS, pitching_stars)
            new_row = adjust_by_pct(new_row, 0.05, BATTING_STLATS, batting_stars)
            new_row = adjust_by_pct(new_row, 0.05, BASERUNNING_STLATS, baserunning_stars)
            new_row = adjust_by_pct(new_row, 0.05, DEFENSE_STLATS, defense_stars)        
        if "A" in current_team_attrs:
            growth_pct = .05 * min(day / 99, 1.0)
            new_row = adjust_by_blood_pct(new_row, growth_pct, PITCHING_STLATS, pitching_stars, blood_pct)
            new_row = adjust_by_blood_pct(new_row, growth_pct, BATTING_STLATS, batting_stars, blood_pct)
            new_row = adjust_by_blood_pct(new_row, growth_pct, BASERUNNING_STLATS, baserunning_stars, blood_pct)
            new_row = adjust_by_blood_pct(new_row, growth_pct, DEFENSE_STLATS, defense_stars, blood_pct)
        if "AFFINITY_FOR_CROWS" in current_team_attrs and game["weather"] == bird_weather:
            new_row = adjust_by_pct(new_row, 0.50, PITCHING_STLATS, pitching_stars)
            new_row = adjust_by_pct(new_row, 0.50, BATTING_STLATS, batting_stars)        
    return new_row

def calculate_adjusted_stat_data(awayAttrs, homeAttrs, awayTeam, homeTeam, team_stat_data):        
    adjusted_stat_data = {}
    adjusted_stat_data["away"], adjusted_stat_data["home"] = {}, {}      
    home_blood = "a" in homeAttrs or "aa" in homeAttrs or "aaa" in homeAttrs
    away_blood = "a" in awayAttrs or "aa" in awayAttrs or "aaa" in awayAttrs

    for playerid in team_stat_data[awayTeam]:            
        adjusted_stat_data["away"][playerid] = {}        
        adjusted_defense_stlats = {"omniscience": team_stat_data[awayTeam][playerid]["omniscience"], "watchfulness": team_stat_data[awayTeam][playerid]["watchfulness"], "chasiness": team_stat_data[awayTeam][playerid]["chasiness"], "anticapitalism": team_stat_data[awayTeam][playerid]["anticapitalism"], "tenaciousness": team_stat_data[awayTeam][playerid]["tenaciousness"]} 
        if not team_stat_data[awayTeam][playerid]["shelled"]:
            adjusted_batting_stlats = {"patheticism": team_stat_data[awayTeam][playerid]["patheticism"], "tragicness": team_stat_data[awayTeam][playerid]["tragicness"], "thwackability": team_stat_data[awayTeam][playerid]["thwackability"], "divinity": team_stat_data[awayTeam][playerid]["divinity"], "moxie": team_stat_data[awayTeam][playerid]["moxie"], "musclitude": team_stat_data[awayTeam][playerid]["musclitude"], "martyrdom": team_stat_data[awayTeam][playerid]["martyrdom"]}
            adjusted_running_stlats = {"laserlikeness": team_stat_data[awayTeam][playerid]["laserlikeness"], "baseThirst": team_stat_data[awayTeam][playerid]["baseThirst"], "continuation": team_stat_data[awayTeam][playerid]["continuation"], "groundFriction": team_stat_data[awayTeam][playerid]["groundFriction"], "indulgence": team_stat_data[awayTeam][playerid]["indulgence"]}
        if away_blood or ("high_pressure" in awayAttrs):
            if away_blood:
                adjusted_defense_stlats = adjust_by_pct(adjusted_defense_stlats, 0.2, DEFENSE_STLATS, defense_stars)
            if not team_stat_data[awayTeam][playerid]["shelled"]:
                adjusted_batting_stlats = adjust_by_pct(adjusted_batting_stlats, 0.2, BATTING_STLATS, batting_stars)
                adjusted_running_stlats = adjust_by_pct(adjusted_running_stlats, 0.2, BASERUNNING_STLATS, baserunning_stars)                  
        if not team_stat_data[awayTeam][playerid]["shelled"]:
            adjusted_stat_data["away"][playerid] = {**adjusted_defense_stlats, **adjusted_batting_stlats, **adjusted_running_stlats}        
        else:
            adjusted_stat_data["away"][playerid] = {**adjusted_defense_stlats}
        adjusted_defense_stlats.clear() 
        if not team_stat_data[awayTeam][playerid]["shelled"]:
            adjusted_batting_stlats.clear() 
            adjusted_running_stlats.clear()   
        
    for playerid in team_stat_data[homeTeam]:                    
        adjusted_stat_data["home"][playerid] = {}
        adjusted_defense_stlats = {"omniscience": team_stat_data[homeTeam][playerid]["omniscience"], "watchfulness": team_stat_data[homeTeam][playerid]["watchfulness"], "chasiness": team_stat_data[homeTeam][playerid]["chasiness"], "anticapitalism": team_stat_data[homeTeam][playerid]["anticapitalism"], "tenaciousness": team_stat_data[homeTeam][playerid]["tenaciousness"]} 
        if not team_stat_data[homeTeam][playerid]["shelled"]:            
            adjusted_batting_stlats = {"patheticism": team_stat_data[homeTeam][playerid]["patheticism"], "tragicness": team_stat_data[homeTeam][playerid]["tragicness"], "thwackability": team_stat_data[homeTeam][playerid]["thwackability"], "divinity": team_stat_data[homeTeam][playerid]["divinity"], "moxie": team_stat_data[homeTeam][playerid]["moxie"], "musclitude": team_stat_data[homeTeam][playerid]["musclitude"], "martyrdom": team_stat_data[homeTeam][playerid]["martyrdom"]}
            adjusted_running_stlats = {"laserlikeness": team_stat_data[homeTeam][playerid]["laserlikeness"], "baseThirst": team_stat_data[homeTeam][playerid]["baseThirst"], "continuation": team_stat_data[homeTeam][playerid]["continuation"], "groundFriction": team_stat_data[homeTeam][playerid]["groundFriction"], "indulgence": team_stat_data[homeTeam][playerid]["indulgence"]}
        if home_blood or ("high_pressure" in homeAttrs):
            if home_blood:
                adjusted_defense_stlats = adjust_by_pct(adjusted_defense_stlats, 0.2, DEFENSE_STLATS, defense_stars)
            if not team_stat_data[homeTeam][playerid]["shelled"]:
                adjusted_batting_stlats = adjust_by_pct(adjusted_batting_stlats, 0.2, BATTING_STLATS, batting_stars)
                adjusted_running_stlats = adjust_by_pct(adjusted_running_stlats, 0.2, BASERUNNING_STLATS, baserunning_stars)        
        if not team_stat_data[homeTeam][playerid]["shelled"]:
            adjusted_stat_data["home"][playerid] = {**adjusted_defense_stlats, **adjusted_batting_stlats, **adjusted_running_stlats}                    
        else:
            adjusted_stat_data["home"][playerid] = {**adjusted_defense_stlats}
        adjusted_defense_stlats.clear() 
        if not team_stat_data[homeTeam][playerid]["shelled"]:
            adjusted_batting_stlats.clear() 
            adjusted_running_stlats.clear()        
    
    return adjusted_stat_data


def load_stat_data(filepath, schedule=None, day=None, team_attrs=None):
    with open(filepath) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    games = {}
    if schedule:
        games.update({game["homeTeamName"]: game for game in schedule})
        games.update({game["awayTeamName"]: game for game in schedule})
    pitcherstatdata = collections.defaultdict(lambda: {})
    teamstatdata = collections.defaultdict(lambda: collections.defaultdict(lambda: []))
    for row in filedata:
        player_attrs = row["permAttr"] + row["seasAttr"] + row["weekAttr"] + row["gameAttr"]
        team = row["team"]
        if games:
            game = games.get(team)
            if game:
                new_row = adjust_stlats(row, game, day, player_attrs, team_attrs)
            else:
                new_row = row
        else:
            new_row = row
        #if new_row["position"] == "rotation":
        for key in (PITCHING_STLATS + ["pitchingStars"]):
            pitcherstatdata[new_row["name"]][key] = float(new_row[key])
        if new_row["position"] == "lineup":
            if "SHELLED" not in player_attrs and "ELSEWHERE" not in player_attrs:
                for key in (BATTING_STLATS + BASERUNNING_STLATS + ["battingStars", "baserunningStars"]):
                    teamstatdata[team][key].append(float(new_row[key]))
            if "ELSEWHERE" not in player_attrs:
                for key in (DEFENSE_STLATS + ["defenseStars"]):
                    teamstatdata[team][key].append(float(new_row[key]))
    return teamstatdata, pitcherstatdata


def load_stat_data_pid(filepath, schedule=None, day=None, team_attrs=None):
    with open(filepath) as f:
        filedata = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    games = {}
    if schedule:
        games.update({game["homeTeamName"]: game for game in schedule})
        games.update({game["awayTeamName"]: game for game in schedule})
    pitcherstatdata = collections.defaultdict(lambda: {})
    teamstatdata = collections.defaultdict(lambda: collections.defaultdict(lambda: {}))
    player_attrs = []
    for row in filedata:
        player_attrs_string = row["permAttr"] + ";" + row["seasAttr"] + ";" + row["weekAttr"] + ";" + row["gameAttr"]
        for attr in player_attrs_string.split(";"):
            if attr.lower() != "":
                player_attrs.append(attr.lower())
        team = row["team"]
        player_id = row["id"]
        roster_size = sum(1 for player in filedata if player["team"] == team)        
        if games:
            game = games.get(team)            
            new_row = adjust_stlats(row, game, day, roster_size, player_attrs_string, team_attrs)
        else:
            new_row = row
        if new_row["position"] == "rotation":
            for key in (PITCHING_STLATS + ["pitchingStars"]):
                pitcherstatdata[new_row["name"]][key] = float(new_row[key])
            pitcherstatdata[new_row["name"]]["ispitcher"] = True
            pitcherstatdata[new_row["name"]]["attrs"] = []
            for attr in player_attrs:
                pitcherstatdata[new_row["name"]]["attrs"].append(attr)
            if game:                
                if team == game["homeTeamName"]:
                    pitcherstatdata[new_row["name"]]["innings"] = game["homeInningsPitched"]                    
                if team == game["awayTeamName"]:
                    pitcherstatdata[new_row["name"]]["innings"] = game["awayInningsPitched"]                    
            else:
                pitcherstatdata[new_row["name"]]["innings"] = 9                
        elif new_row["position"] == "lineup":            
            if "shelled" not in player_attrs and "elsewhere" not in player_attrs:
                for key in (BATTING_STLATS + BASERUNNING_STLATS + ["battingStars", "baserunningStars"]):
                    teamstatdata[team][player_id][key] = float(new_row[key])                
                teamstatdata[team][player_id]["ispitcher"] = False
                teamstatdata[team][player_id]["shelled"] = ("shelled" in player_attrs)
                teamstatdata[team][player_id]["turnOrder"] = int(new_row["turnOrder"])                
            if "elsewhere" not in player_attrs:
                for key in (DEFENSE_STLATS + ["defenseStars"]):
                    teamstatdata[team][player_id][key] = float(new_row[key])                          
                teamstatdata[team][player_id]["ispitcher"] = False
                teamstatdata[team][player_id]["shelled"] = ("shelled" in player_attrs)
                teamstatdata[team][player_id]["reverberating"] = ("reverberating" in player_attrs)
                teamstatdata[team][player_id]["repeating"] = ("repeating" in player_attrs)
            if player_id in teamstatdata[team]:  # these are defaultdicts so we don't want to add skipped players                
                teamstatdata[team][player_id]["team"] = team
                teamstatdata[team][player_id]["name"] = new_row["name"]
                teamstatdata[team][player_id]["attrs"] = []
                for attr in player_attrs:
                    if attr.lower() != "":
                        teamstatdata[team][player_id]["attrs"].append(attr.lower())
        player_attrs.clear()
    return teamstatdata, pitcherstatdata


def do_init(args):
    if args.testfile:
        streamdata = load_test_data(args.testfile)
    else:
        streamdata = get_stream_snapshot()
    season_number = streamdata['value']['games']['season']['seasonNumber']  # 0-indexed
    day = streamdata['value']['games']['sim']['day'] + (1 if args.today else 2)  # 0-indexed, make 1-indexed and add another if tomorrow
    if already_ran_for_day(args.dayfile, season_number, day) and not args.forcerun:
        print("Already ran for Season {} Day {}, exiting.".format(season_number+1, day))
        sys.exit(0)
    today_schedule = streamdata['value']['games']['schedule']
    retry_count = int(os.getenv("RETRY_COUNT", 10))
    show_waiting_message = int(os.getenv("SHOW_WAITING_MESSAGE", 1))
    sleep_interval = int(os.getenv("WAIT_INTERVAL", 30))
    games_complete = all([game["finalized"] for game in today_schedule])
    is_postseason = any([game["isPostseason"] for game in today_schedule])
    if all([(game["day"] == 0 and game["gameStart"] is False) for game in today_schedule]):
        print("This season's games haven't started yet")
        sys.exit(0)
    if not args.today and not args.forcerun and not args.testfile and retry_count > 0:
        first_try = True
        for _ in range(retry_count):
            games_complete = all([game["finalized"] for game in today_schedule])
            is_postseason = any([game["isPostseason"] for game in today_schedule])
            keep_trying = (not games_complete or (is_postseason and not args.today and not streamdata['value']['games']['tomorrowSchedule']))
            if keep_trying and first_try:
                total_seconds = sleep_interval * retry_count
                if show_waiting_message:
                    message = "Waiting up to {} minute{} {}for current games to end."
                    message = message.format(total_seconds // 60, "" if total_seconds // 60 == 1 else "s",
                                             "{} seconds ".format(total_seconds % 60) if total_seconds % 60 else "")
                    if args.discord and os.getenv("WAIT_APOLOGY", "true") == "true":
                        send_discord_message("Sorry!", message)
                    else:
                        print(message)
                first_try = False
            elif not keep_trying:
                break
            time.sleep(sleep_interval)
            streamdata = get_stream_snapshot()
            today_schedule = streamdata['value']['games']['schedule']
        if not games_complete:
            message = "Running even though games aren't complete, watch out!"
            if args.discord:
                send_discord_message("Warning!", message)
            else:
                print(message)
    game_schedule = today_schedule if args.today else streamdata['value']['games']['tomorrowSchedule']
    if not game_schedule and day >= 100 and not args.today:
        time.sleep(30)
        game_schedule = get_stream_snapshot()['value']['games']['tomorrowSchedule']
    if not game_schedule and not args.lineupfile:
        print("No games found for Season {} Day {}, exiting.".format(season_number+1, day))
        if games_complete and is_postseason:
            write_day(args.dayfile, season_number, day)
        sys.exit(0)
    all_pitcher_ids = []
    for game in game_schedule:
        all_pitcher_ids.extend((game["awayPitcher"], game["homePitcher"]))
    all_pitcher_ids = [pid for pid in all_pitcher_ids if pid]
    if not all_pitcher_ids:
        print("No pitchers assigned to games on Season {} Day {}, exiting.".format(season_number + 1, day))
        sys.exit(0)
    outcomes = [outcome for game in streamdata['value']['games']['schedule'] if game["outcomes"] for outcome in game['outcomes'] if outcome_matters(outcome)]
    stat_file_exists = os.path.isfile(args.statfile)
    if (outcomes or not stat_file_exists or args.forceupdate or ((day == 1 and args.today) or day == 2)) and not args.skipupdate:
        if args.discord and os.getenv("SHOW_STAT_CHANGES", "true") == "true":
            message = "Generating new stat file, please stand by.\n\n{}".format("\n".join("`{}`".format(outcome) for outcome in outcomes))
            send_discord_message("One sec!", message[:DISCORD_SPLIT_LIMIT])
        else:
            print("Generating new stat file, please stand by.")
        blaseball_stat_csv.generate_file(args.statfile, False, args.archive, True)
    team_stat_data, pitcher_stat_data = load_stat_data_pid(args.statfile, game_schedule, day)
    team_pid_stat_data, _ = load_stat_data_pid(args.statfile, game_schedule, day)
    return game_schedule, streamdata, season_number, day, all_pitcher_ids, team_stat_data, team_pid_stat_data, pitcher_stat_data


def get_emoji(raw_emoji):
    try:
        emoji = chr(int(raw_emoji, 16))
    except ValueError:
        emoji = raw_emoji
    return emoji
