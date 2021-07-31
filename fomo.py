from __future__ import division
from __future__ import print_function

import collections

import helpers
import os
import mofo

def setup_playerbased(weather, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, team_stat_data, pitcher_stat_data):
    terms_url = os.getenv("FOMO_TERMS")
    terms, _ = helpers.load_terms(terms_url)
    halfterms_url = os.getenv("FOMO_HALF_TERMS")
    halfterms = helpers.load_half_terms(halfterms_url)
    mods_url = os.getenv("FOMO_MODS")
    mods = helpers.load_mods(mods_url)
    ballparks_url = os.getenv("BALLPARKS")
    ballparks = helpers.load_ballparks(ballparks_url)
    ballpark_mods_url = os.getenv("FOMO_BALLPARK_TERMS")
    ballpark_mods = helpers.load_bp_terms(ballpark_mods_url)
    homeTeamId = helpers.get_team_id(homeTeam)
    ballpark = ballparks.get(homeTeamId, collections.defaultdict(lambda: 0.5))
    awayMods, homeMods = mofo.get_park_mods(ballpark, ballpark_mods)
    adjustments = mofo.instantiate_adjustments(terms, halfterms)
    return mods, terms, awayMods, homeMods, adjustments

def calculate(awayPitcher, homePitcher, awayTeam, homeTeam, team_stat_data, pitcher_stat_data, awayAttrs, homeAttrs,
              day, weather, skip_mods=False):
    mods, terms, awayMods, homeMods, adjustments = setup_playerbased(weather, awayAttrs, homeAttrs, awayTeam, homeTeam, awayPitcher, homePitcher, team_stat_data, pitcher_stat_data)
    adjusted_stat_data = helpers.calculate_adjusted_stat_data(awayAttrs, homeAttrs, awayTeam, homeTeam, team_stat_data)
    return mofo.get_mofo_playerbased(mods, awayPitcher, homePitcher, awayTeam, homeTeam, awayAttrs, homeAttrs, weather, team_stat_data, pitcher_stat_data, terms, awayMods, homeMods, adjusted_stat_data, adjustments, skip_mods=skip_mods)