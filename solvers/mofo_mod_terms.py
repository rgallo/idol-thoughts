from collections import namedtuple

MofoModTerm = namedtuple("MofoModTerm", ["attr", "team", "stat", "bounds"])
DefaultBounds = [[0, 1], [0, 0], [0, 0]]
BuffOnlyBounds = [[0.5, 1], [0, 0], [0, 0]]
DebuffOnlyBounds = [[0, 0.5], [0, 0], [0, 0]]

MOFO_MOD_TERMS = [    
    MofoModTerm("LOVE", "opp", "Ruthlessness", DebuffOnlyBounds),
    MofoModTerm("LOVE", "opp", "Unthwackability", DebuffOnlyBounds),
    MofoModTerm("LOVE", "opp", "Overpowerment", DebuffOnlyBounds),      
    MofoModTerm("LOVE", "opp", "Tragicness", BuffOnlyBounds),
    MofoModTerm("LOVE", "opp", "Patheticism", BuffOnlyBounds),
    MofoModTerm("LOVE", "opp", "Thwackability", DebuffOnlyBounds),
    MofoModTerm("LOVE", "opp", "Divinity", DebuffOnlyBounds),
    MofoModTerm("LOVE", "opp", "Moxie", DebuffOnlyBounds),
    MofoModTerm("LOVE", "opp", "Musclitude", DebuffOnlyBounds),
    MofoModTerm("LOVE", "opp", "Martyrdom", DebuffOnlyBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Tragicness", DebuffOnlyBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Patheticism", DebuffOnlyBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Thwackability", BuffOnlyBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Divinity", BuffOnlyBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Moxie", BuffOnlyBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Musclitude", BuffOnlyBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Martyrdom", BuffOnlyBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Laserlikeness", BuffOnlyBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "BaseThirst", BuffOnlyBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Continuation", BuffOnlyBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "GroundFriction", BuffOnlyBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Indulgence", BuffOnlyBounds),       
    MofoModTerm("BASE_INSTINCTS", "same", "Multiplier", DebuffOnlyBounds),                 
    MofoModTerm("FIERY", "same", "Multiplier", DebuffOnlyBounds),
    MofoModTerm("ELECTRIC", "same", "Multiplier", DebuffOnlyBounds),         
    MofoModTerm("PSYCHIC", "opp", "Ruthlessness", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Unthwackability", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Overpowerment", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Shakespearianism", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Coldness", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Omniscience", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Tenaciousness", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Watchfulness", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Anticapitalism", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Chasiness", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Tragicness", BuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Patheticism", BuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Thwackability", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Divinity", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Moxie", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Musclitude", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Martyrdom", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Laserlikeness", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "BaseThirst", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Continuation", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "GroundFriction", DebuffOnlyBounds),
    MofoModTerm("PSYCHIC", "opp", "Indulgence", DebuffOnlyBounds),
    MofoModTerm("ACIDIC", "same", "Multiplier", DebuffOnlyBounds)    
]


    