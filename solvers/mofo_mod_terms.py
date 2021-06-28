from collections import namedtuple

MofoModTerm = namedtuple("MofoModTerm", ["attr", "team", "stat", "bounds"])
DefaultBounds = [[-3, 3], [0, 1], [1, 1.5]]

MOFO_MOD_TERMS = [    
    MofoModTerm("LOVE", "opp", "Ruthlessness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Unthwackability", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Overpowerment", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Shakespearianism", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Coldness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Omniscience", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Tenaciousness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Watchfulness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Anticapitalism", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Chasiness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Tragicness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Patheticism", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Thwackability", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Divinity", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Moxie", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Musclitude", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Martyrdom", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Laserlikeness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "BaseThirst", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Continuation", DefaultBounds),
    MofoModTerm("LOVE", "opp", "GroundFriction", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Indulgence", DefaultBounds),    
    MofoModTerm("EXTRA_STRIKE", "opp", "Ruthlessness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "Unthwackability", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "Overpowerment", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "Shakespearianism", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "Coldness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "Omniscience", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "Tenaciousness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "Watchfulness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "Anticapitalism", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "Chasiness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "Tragicness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "Patheticism", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "Thwackability", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "Divinity", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "Moxie", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "Musclitude", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "Martyrdom", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "Laserlikeness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "BaseThirst", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "Continuation", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "GroundFriction", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "Indulgence", DefaultBounds),        
    MofoModTerm("O_NO", "opp", "Ruthlessness", DefaultBounds),
    MofoModTerm("O_NO", "opp", "Unthwackability", DefaultBounds),
    MofoModTerm("O_NO", "opp", "Overpowerment", DefaultBounds),
    MofoModTerm("O_NO", "opp", "Shakespearianism", DefaultBounds),
    MofoModTerm("O_NO", "opp", "Coldness", DefaultBounds),
    MofoModTerm("O_NO", "opp", "Omniscience", DefaultBounds),
    MofoModTerm("O_NO", "opp", "Tenaciousness", DefaultBounds),
    MofoModTerm("O_NO", "opp", "Watchfulness", DefaultBounds),
    MofoModTerm("O_NO", "opp", "Anticapitalism", DefaultBounds),
    MofoModTerm("O_NO", "opp", "Chasiness", DefaultBounds),
    MofoModTerm("O_NO", "same", "Tragicness", DefaultBounds),
    MofoModTerm("O_NO", "same", "Patheticism", DefaultBounds),
    MofoModTerm("O_NO", "same", "Thwackability", DefaultBounds),
    MofoModTerm("O_NO", "same", "Divinity", DefaultBounds),
    MofoModTerm("O_NO", "same", "Moxie", DefaultBounds),
    MofoModTerm("O_NO", "same", "Musclitude", DefaultBounds),
    MofoModTerm("O_NO", "same", "Martyrdom", DefaultBounds),
    MofoModTerm("O_NO", "same", "Laserlikeness", DefaultBounds),
    MofoModTerm("O_NO", "same", "BaseThirst", DefaultBounds),
    MofoModTerm("O_NO", "same", "Continuation", DefaultBounds),
    MofoModTerm("O_NO", "same", "GroundFriction", DefaultBounds),
    MofoModTerm("O_NO", "same", "Indulgence", DefaultBounds),            
    MofoModTerm("HIGH_PRESSURE", "same", "Tragicness", DefaultBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Patheticism", DefaultBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Thwackability", DefaultBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Divinity", DefaultBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Moxie", DefaultBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Musclitude", DefaultBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Martyrdom", DefaultBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Laserlikeness", DefaultBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "BaseThirst", DefaultBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Continuation", DefaultBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "GroundFriction", DefaultBounds),
    MofoModTerm("HIGH_PRESSURE", "same", "Indulgence", DefaultBounds),        
    MofoModTerm("BASE_INSTINCTS", "opp", "Ruthlessness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "Unthwackability", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "Overpowerment", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "Shakespearianism", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "Coldness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "Omniscience", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "Tenaciousness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "Watchfulness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "Anticapitalism", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "Chasiness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "Tragicness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "Patheticism", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "Thwackability", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "Divinity", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "Moxie", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "Musclitude", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "Martyrdom", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "Laserlikeness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "BaseThirst", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "Continuation", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "GroundFriction", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "Indulgence", DefaultBounds),    
    MofoModTerm("0", "opp", "Ruthlessness", DefaultBounds),
    MofoModTerm("0", "opp", "Unthwackability", DefaultBounds),
    MofoModTerm("0", "opp", "Overpowerment", DefaultBounds),
    MofoModTerm("0", "opp", "Shakespearianism", DefaultBounds),
    MofoModTerm("0", "opp", "Coldness", DefaultBounds),
    MofoModTerm("0", "opp", "Omniscience", DefaultBounds),
    MofoModTerm("0", "opp", "Tenaciousness", DefaultBounds),
    MofoModTerm("0", "opp", "Watchfulness", DefaultBounds),
    MofoModTerm("0", "opp", "Anticapitalism", DefaultBounds),
    MofoModTerm("0", "opp", "Chasiness", DefaultBounds),
    MofoModTerm("0", "same", "Tragicness", DefaultBounds),
    MofoModTerm("0", "same", "Patheticism", DefaultBounds),
    MofoModTerm("0", "same", "Thwackability", DefaultBounds),
    MofoModTerm("0", "same", "Divinity", DefaultBounds),
    MofoModTerm("0", "same", "Moxie", DefaultBounds),
    MofoModTerm("0", "same", "Musclitude", DefaultBounds),
    MofoModTerm("0", "same", "Martyrdom", DefaultBounds),
    MofoModTerm("0", "same", "Laserlikeness", DefaultBounds),
    MofoModTerm("0", "same", "BaseThirst", DefaultBounds),
    MofoModTerm("0", "same", "Continuation", DefaultBounds),
    MofoModTerm("0", "same", "GroundFriction", DefaultBounds),
    MofoModTerm("0", "same", "Indulgence", DefaultBounds),    
    MofoModTerm("H20", "opp", "Ruthlessness", DefaultBounds),
    MofoModTerm("H20", "opp", "Unthwackability", DefaultBounds),
    MofoModTerm("H20", "opp", "Overpowerment", DefaultBounds),
    MofoModTerm("H20", "opp", "Shakespearianism", DefaultBounds),
    MofoModTerm("H20", "opp", "Coldness", DefaultBounds),
    MofoModTerm("H20", "opp", "Omniscience", DefaultBounds),
    MofoModTerm("H20", "opp", "Tenaciousness", DefaultBounds),
    MofoModTerm("H20", "opp", "Watchfulness", DefaultBounds),
    MofoModTerm("H20", "opp", "Anticapitalism", DefaultBounds),
    MofoModTerm("H20", "opp", "Chasiness", DefaultBounds),
    MofoModTerm("H20", "same", "Tragicness", DefaultBounds),
    MofoModTerm("H20", "same", "Patheticism", DefaultBounds),
    MofoModTerm("H20", "same", "Thwackability", DefaultBounds),
    MofoModTerm("H20", "same", "Divinity", DefaultBounds),
    MofoModTerm("H20", "same", "Moxie", DefaultBounds),
    MofoModTerm("H20", "same", "Musclitude", DefaultBounds),
    MofoModTerm("H20", "same", "Martyrdom", DefaultBounds),
    MofoModTerm("H20", "same", "Laserlikeness", DefaultBounds),
    MofoModTerm("H20", "same", "BaseThirst", DefaultBounds),
    MofoModTerm("H20", "same", "Continuation", DefaultBounds),
    MofoModTerm("H20", "same", "GroundFriction", DefaultBounds),
    MofoModTerm("H20", "same", "Indulgence", DefaultBounds),    
    MofoModTerm("FIERY", "same", "Ruthlessness", DefaultBounds),
    MofoModTerm("FIERY", "same", "Unthwackability", DefaultBounds),
    MofoModTerm("FIERY", "same", "Overpowerment", DefaultBounds),
    MofoModTerm("FIERY", "same", "Shakespearianism", DefaultBounds),
    MofoModTerm("FIERY", "same", "Coldness", DefaultBounds),
    MofoModTerm("FIERY", "same", "Omniscience", DefaultBounds),
    MofoModTerm("FIERY", "same", "Tenaciousness", DefaultBounds),
    MofoModTerm("FIERY", "same", "Watchfulness", DefaultBounds),
    MofoModTerm("FIERY", "same", "Anticapitalism", DefaultBounds),
    MofoModTerm("FIERY", "same", "Chasiness", DefaultBounds),
    MofoModTerm("FIERY", "opp", "Tragicness", DefaultBounds),
    MofoModTerm("FIERY", "opp", "Patheticism", DefaultBounds),
    MofoModTerm("FIERY", "opp", "Thwackability", DefaultBounds),
    MofoModTerm("FIERY", "opp", "Divinity", DefaultBounds),
    MofoModTerm("FIERY", "opp", "Moxie", DefaultBounds),
    MofoModTerm("FIERY", "opp", "Musclitude", DefaultBounds),
    MofoModTerm("FIERY", "opp", "Martyrdom", DefaultBounds),
    MofoModTerm("FIERY", "opp", "Laserlikeness", DefaultBounds),
    MofoModTerm("FIERY", "opp", "BaseThirst", DefaultBounds),
    MofoModTerm("FIERY", "opp", "Continuation", DefaultBounds),
    MofoModTerm("FIERY", "opp", "GroundFriction", DefaultBounds),
    MofoModTerm("FIERY", "opp", "Indulgence", DefaultBounds),    
    MofoModTerm("AAA", "same", "Omniscience", DefaultBounds),
    MofoModTerm("AAA", "same", "Tenaciousness", DefaultBounds),
    MofoModTerm("AAA", "same", "Watchfulness", DefaultBounds),
    MofoModTerm("AAA", "same", "Anticapitalism", DefaultBounds),
    MofoModTerm("AAA", "same", "Chasiness", DefaultBounds),
    MofoModTerm("AAA", "same", "Tragicness", DefaultBounds),
    MofoModTerm("AAA", "same", "Patheticism", DefaultBounds),
    MofoModTerm("AAA", "same", "Thwackability", DefaultBounds),
    MofoModTerm("AAA", "same", "Divinity", DefaultBounds),
    MofoModTerm("AAA", "same", "Moxie", DefaultBounds),
    MofoModTerm("AAA", "same", "Musclitude", DefaultBounds),
    MofoModTerm("AAA", "same", "Martyrdom", DefaultBounds),
    MofoModTerm("AAA", "same", "Laserlikeness", DefaultBounds),
    MofoModTerm("AAA", "same", "BaseThirst", DefaultBounds),
    MofoModTerm("AAA", "same", "Continuation", DefaultBounds),
    MofoModTerm("AAA", "same", "GroundFriction", DefaultBounds),
    MofoModTerm("AAA", "same", "Indulgence", DefaultBounds),        
    MofoModTerm("AA", "same", "Omniscience", DefaultBounds),
    MofoModTerm("AA", "same", "Tenaciousness", DefaultBounds),
    MofoModTerm("AA", "same", "Watchfulness", DefaultBounds),
    MofoModTerm("AA", "same", "Anticapitalism", DefaultBounds),
    MofoModTerm("AA", "same", "Chasiness", DefaultBounds),
    MofoModTerm("AA", "same", "Tragicness", DefaultBounds),
    MofoModTerm("AA", "same", "Patheticism", DefaultBounds),
    MofoModTerm("AA", "same", "Thwackability", DefaultBounds),
    MofoModTerm("AA", "same", "Divinity", DefaultBounds),
    MofoModTerm("AA", "same", "Moxie", DefaultBounds),
    MofoModTerm("AA", "same", "Musclitude", DefaultBounds),
    MofoModTerm("AA", "same", "Martyrdom", DefaultBounds),
    MofoModTerm("AA", "same", "Laserlikeness", DefaultBounds),
    MofoModTerm("AA", "same", "BaseThirst", DefaultBounds),
    MofoModTerm("AA", "same", "Continuation", DefaultBounds),
    MofoModTerm("AA", "same", "GroundFriction", DefaultBounds),
    MofoModTerm("AA", "same", "Indulgence", DefaultBounds),        
    MofoModTerm("PSYCHIC", "opp", "Ruthlessness", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Unthwackability", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Overpowerment", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Shakespearianism", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Coldness", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Omniscience", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Tenaciousness", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Watchfulness", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Anticapitalism", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Chasiness", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Tragicness", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Patheticism", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Thwackability", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Divinity", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Moxie", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Musclitude", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Martyrdom", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Laserlikeness", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "BaseThirst", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Continuation", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "GroundFriction", DefaultBounds),
    MofoModTerm("PSYCHIC", "opp", "Indulgence", DefaultBounds),    
    MofoModTerm("ACIDIC", "same", "Ruthlessness", DefaultBounds),
    MofoModTerm("ACIDIC", "same", "Unthwackability", DefaultBounds),
    MofoModTerm("ACIDIC", "same", "Overpowerment", DefaultBounds),
    MofoModTerm("ACIDIC", "same", "Shakespearianism", DefaultBounds),
    MofoModTerm("ACIDIC", "same", "Coldness", DefaultBounds),
    MofoModTerm("ACIDIC", "same", "Omniscience", DefaultBounds),
    MofoModTerm("ACIDIC", "same", "Tenaciousness", DefaultBounds),
    MofoModTerm("ACIDIC", "same", "Watchfulness", DefaultBounds),
    MofoModTerm("ACIDIC", "same", "Anticapitalism", DefaultBounds),
    MofoModTerm("ACIDIC", "same", "Chasiness", DefaultBounds),
    MofoModTerm("ACIDIC", "opp", "Tragicness", DefaultBounds),
    MofoModTerm("ACIDIC", "opp", "Patheticism", DefaultBounds),
    MofoModTerm("ACIDIC", "opp", "Thwackability", DefaultBounds),
    MofoModTerm("ACIDIC", "opp", "Divinity", DefaultBounds),
    MofoModTerm("ACIDIC", "opp", "Moxie", DefaultBounds),
    MofoModTerm("ACIDIC", "opp", "Musclitude", DefaultBounds),
    MofoModTerm("ACIDIC", "opp", "Martyrdom", DefaultBounds),
    MofoModTerm("ACIDIC", "opp", "Laserlikeness", DefaultBounds),
    MofoModTerm("ACIDIC", "opp", "BaseThirst", DefaultBounds),
    MofoModTerm("ACIDIC", "opp", "Continuation", DefaultBounds),
    MofoModTerm("ACIDIC", "opp", "GroundFriction", DefaultBounds),
    MofoModTerm("ACIDIC", "opp", "Indulgence", DefaultBounds)    
]


    