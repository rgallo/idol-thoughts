from collections import namedtuple

MOFOTerm = namedtuple("MOFOTerm", ["stat", "bounds"])
DefaultBounds = [[0.01, 2], [0.01, 2], [0.01, 2]]
SoloBounds = [[0.01, 2], [0.01, 2], [0.01, 2]]

MOFO_TERMS = [        
    MOFOTerm("trag_runner_advances", DefaultBounds),
    MOFOTerm("path_connect", SoloBounds),
    MOFOTerm("thwack_base_hit", DefaultBounds),
    MOFOTerm("div_homer", DefaultBounds),
    MOFOTerm("moxie_swing_correct", SoloBounds),
    MOFOTerm("muscl_foul_ball", SoloBounds),    
    MOFOTerm("muscl_triple", DefaultBounds),    
    MOFOTerm("muscl_double", DefaultBounds),    
    MOFOTerm("martyr_sacrifice", SoloBounds),
    MOFOTerm("laser_attempt_steal", DefaultBounds), 
    MOFOTerm("laser_caught_steal_base", DefaultBounds), 
    MOFOTerm("laser_caught_steal_home", DefaultBounds), 
    MOFOTerm("laser_runner_advances", DefaultBounds), 
    MOFOTerm("baset_attempt_steal", DefaultBounds),    
    MOFOTerm("baset_caught_steal_home", DefaultBounds),    
    MOFOTerm("cont_triple", DefaultBounds),    
    MOFOTerm("cont_double", DefaultBounds),    
    MOFOTerm("ground_triple", DefaultBounds),    
    MOFOTerm("indulg_runner_advances", DefaultBounds),        
    MOFOTerm("unthwack_base_hit", DefaultBounds),
    MOFOTerm("ruth_strike", SoloBounds),
    MOFOTerm("overp_homer", DefaultBounds),    
    MOFOTerm("overp_triple", DefaultBounds),    
    MOFOTerm("overp_double", DefaultBounds),    
    MOFOTerm("shakes_runner_advances", DefaultBounds),    
    #MOFOTerm("cold_clutch_factor", [[0, 0.1], [0, 0.1], [0, 0.1]]),
    MOFOTerm("omni_base_hit", DefaultBounds),           
    MOFOTerm("tenacious_runner_advances", DefaultBounds),    
    MOFOTerm("watch_attempt_steal", DefaultBounds),    
    MOFOTerm("anticap_caught_steal_base", DefaultBounds),
    MOFOTerm("anticap_caught_steal_home", DefaultBounds),
    MOFOTerm("chasi_triple", DefaultBounds),
    MOFOTerm("chasi_double", DefaultBounds)    
]