from collections import namedtuple

BallParkTerm = namedtuple("BallParkTerm", ["ballparkstat", "playerstat", "bounds"])
DefaultBounds = [[0.01, 3], [0.01, 3], [0.01, 2]]
BuffOnlyBounds = [[0.01, 3], [0.01, 3], [0.01, 2]]
DebuffOnlyBounds = [[-3, -0.01], [0.01, 3], [0.01, 2]]

BALLPARK_TERMS = [                    
    BallParkTerm("grandiosity", "plus_hit_minus_homer", DefaultBounds),    
    BallParkTerm("obtuseness", "plus_hit_minus_foul", DefaultBounds),         
    BallParkTerm("ominousness", "plus_groundout_minus_hardhit", DefaultBounds),                
    BallParkTerm("viscosity", "plus_contact_minus_hardhit", DefaultBounds),            
    BallParkTerm("forwardness", "plus_strike", DefaultBounds),    
    BallParkTerm("forwardness", "plus_hardhit", DefaultBounds),    
    BallParkTerm("elongation", "minus_stealsuccess", DefaultBounds),        
    BallParkTerm("elongation", "minus_doubleplay", DefaultBounds),    
    BallParkTerm("inconvenience", "minus_stealattempt", DefaultBounds),    
    BallParkTerm("inconvenience", "minus_hit", DefaultBounds),        
    BallParkTerm("fortification", "minus_homer", DefaultBounds),    
    BallParkTerm("hype", "trag_runner_advances", DebuffOnlyBounds),
    BallParkTerm("hype", "path_connect", DebuffOnlyBounds),
    BallParkTerm("hype", "thwack_base_hit", BuffOnlyBounds),
    BallParkTerm("hype", "div_homer", BuffOnlyBounds),
    BallParkTerm("hype", "moxie_swing_correct", BuffOnlyBounds),
    BallParkTerm("hype", "muscl_foul_ball", BuffOnlyBounds),    
    BallParkTerm("hype", "muscl_triple", BuffOnlyBounds),    
    BallParkTerm("hype", "muscl_double", BuffOnlyBounds),    
    BallParkTerm("hype", "martyr_sacrifice", BuffOnlyBounds),
    BallParkTerm("hype", "laser_attempt_steal", BuffOnlyBounds), 
    BallParkTerm("hype", "laser_caught_steal_base", BuffOnlyBounds), 
    BallParkTerm("hype", "laser_caught_steal_home", BuffOnlyBounds), 
    BallParkTerm("hype", "laser_runner_advances", BuffOnlyBounds), 
    BallParkTerm("hype", "baset_attempt_steal", BuffOnlyBounds),    
    BallParkTerm("hype", "baset_caught_steal_home", BuffOnlyBounds),    
    BallParkTerm("hype", "cont_triple", BuffOnlyBounds),    
    BallParkTerm("hype", "cont_double", BuffOnlyBounds),    
    BallParkTerm("hype", "ground_triple", BuffOnlyBounds),    
    BallParkTerm("hype", "indulg_runner_advances", BuffOnlyBounds),        
    BallParkTerm("hype", "unthwack_base_hit", BuffOnlyBounds),
    BallParkTerm("hype", "ruth_strike", BuffOnlyBounds),
    BallParkTerm("hype", "overp_homer", BuffOnlyBounds),    
    BallParkTerm("hype", "overp_triple", BuffOnlyBounds),    
    BallParkTerm("hype", "overp_double", BuffOnlyBounds),    
    BallParkTerm("hype", "shakes_runner_advances", BuffOnlyBounds),    
    #BallParkTerm("hype", "cold_clutch_factor", [[0, 0.1], [0, 0.1], [0, 0.1]]),
    BallParkTerm("hype", "omni_base_hit", BuffOnlyBounds),           
    BallParkTerm("hype", "tenacious_runner_advances", BuffOnlyBounds),    
    BallParkTerm("hype", "watch_attempt_steal", BuffOnlyBounds),    
    BallParkTerm("hype", "anticap_caught_steal_base", BuffOnlyBounds),
    BallParkTerm("hype", "anticap_caught_steal_home", BuffOnlyBounds),
    BallParkTerm("hype", "chasi_triple", BuffOnlyBounds),
    BallParkTerm("hype", "chasi_double", BuffOnlyBounds)    
]