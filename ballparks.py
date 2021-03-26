from __future__ import division
from __future__ import print_function

import collections

from helpers import load_bp_terms
import os

def calc_multiplier(term, ballpark_stat_data):    
    bpvalue = ballpark_stat_data[term]
    multiplier_formula = term.calc(bpvalue)
    base_multiplier = (1 / (1 + (2 ** (-1 * multiplier_formula))))
    if bpvalue > 0.5:
        multiplier = 2 * base_multiplier
    elif bpvalue < 0.5:
        multiplier = 2 - (2 * base_multiplier)
    return multiplier

def ballpark_stats(bpstlat, stlat, homeTeam, ballpark_stat_data):
    ballpark_term = ballpark_stat_data[homeTeam][bpstlat][slat]
    return calc_multiplier(ballpark_term, ballpark_stat_data)

def setup():
    terms_url = os.getenv("MOFO_BALLPARK_TERMS")
    terms = load_bp_terms(terms_url)
    return terms

def calculate(bpstlat, stlat, homeTeam):
    ballpark_terms = setup()
    return get_ballpark(bpstlat, homeTeam, ballpark_terms)

def get_ballpark(bpstlat, stlat, homeTeam, terms):
    ballpark_stat_multiplier = ballpark_stats(bpstlat, stlat, homeTeam, terms)    
    return ballpark_stat_multiplier