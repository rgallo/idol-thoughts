from collections import namedtuple

MofoModTerm = namedtuple("MofoModTerm", ["attr", "team", "stat", "bounds"])
DefaultBounds = [[0, 1]]
BuffOnlyBounds = [[0.5, 1]]
DebuffOnlyBounds = [[0, 0.5]]
#DefaultBounds = [[0, 1], [0, 0], [0, 0]]
#BuffOnlyBounds = [[0.5, 1], [0, 0], [0, 0]]
#DebuffOnlyBounds = [[0, 0.5], [0, 0], [0, 0]]

MOFO_MOD_TERMS = [    
    MofoModTerm("LOVE", "opp", "Strikeout", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Easypitch", DefaultBounds),    
    MofoModTerm("BASE_INSTINCTS", "same", "Multiplier", DefaultBounds),                 
    MofoModTerm("FIERY", "same", "Multiplier", DefaultBounds),
    MofoModTerm("ELECTRIC", "same", "Multiplier", DefaultBounds),         
    MofoModTerm("PSYCHIC", "same", "WalkTrick", DefaultBounds),
    MofoModTerm("PSYCHIC", "same", "StrikeTrick", DefaultBounds),    
    MofoModTerm("ACIDIC", "same", "Multiplier", DefaultBounds)    
]


    