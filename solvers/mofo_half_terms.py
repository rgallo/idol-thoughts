from collections import namedtuple

MOFOHalfTerm = namedtuple("MOFOHalfTerm", ["stat", "event", "bounds"])
DefaultBounds = [[0, 2]]

MOFO_HALF_TERMS = [        
    MOFOHalfTerm("tragicness", "trag_runner_advances", DefaultBounds),
    MOFOHalfTerm("patheticism", "path_connect", DefaultBounds),
    MOFOHalfTerm("thwackability", "thwack_base_hit", DefaultBounds),
    MOFOHalfTerm("divinity", "div_homer", DefaultBounds),
    MOFOHalfTerm("moxie", "moxie_swing_correct", DefaultBounds),
    MOFOHalfTerm("musclitude", "muscl_foul_ball", DefaultBounds),
    MOFOHalfTerm("musclitude", "muscl_triple", DefaultBounds),
    MOFOHalfTerm("musclitude", "muscl_double", DefaultBounds),    
    MOFOHalfTerm("martyrdom", "martyr_sacrifice", DefaultBounds),
    MOFOHalfTerm("laserlikeness", "laser_attempt_steal", DefaultBounds),
    MOFOHalfTerm("laserlikeness", "laser_caught_steal_base", DefaultBounds),
    MOFOHalfTerm("laserlikeness", "laser_caught_steal_home", DefaultBounds),
    MOFOHalfTerm("laserlikeness", "laser_runner_advances", DefaultBounds),
    MOFOHalfTerm("basethirst", "baset_attempt_steal", DefaultBounds),
    MOFOHalfTerm("basethirst", "baset_caught_steal_home", DefaultBounds),
    MOFOHalfTerm("continuation", "cont_triple", DefaultBounds),
    MOFOHalfTerm("continuation", "cont_double", DefaultBounds),
    MOFOHalfTerm("groundfriction", "ground_triple", DefaultBounds),
    MOFOHalfTerm("indulgence", "indulg_runner_advances", DefaultBounds),
    MOFOHalfTerm("unthwackability", "unthwack_base_hit", DefaultBounds),
    MOFOHalfTerm("ruthlessness", "ruth_strike", DefaultBounds),
    MOFOHalfTerm("overpowerment", "overp_homer", DefaultBounds),
    MOFOHalfTerm("overpowerment", "overp_triple", DefaultBounds),
    MOFOHalfTerm("overpowerment", "overp_double", DefaultBounds),
    MOFOHalfTerm("shakespearianism", "shakes_runner_advances", DefaultBounds),
    MOFOHalfTerm("coldness", "cold_clutch_factor", [[0, 0.1]]),
    MOFOHalfTerm("omniscience", "omni_base_hit", DefaultBounds),    
    MOFOHalfTerm("tenaciousness", "tenacious_runner_advances", DefaultBounds),
    MOFOHalfTerm("watchfulness", "watch_attempt_steal", DefaultBounds),
    MOFOHalfTerm("anticapitalism", "anticap_caught_steal_base", DefaultBounds),
    MOFOHalfTerm("anticapitalism", "anticap_caught_steal_home", DefaultBounds),
    MOFOHalfTerm("chasiness", "chasi_triple", DefaultBounds),
    MOFOHalfTerm("chasiness", "chasi_double", DefaultBounds)
]