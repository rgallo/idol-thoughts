from collections import namedtuple

MOFOTerm = namedtuple("MOFOTerm", ["stat", "bounds"])
DefaultBounds = [[1, 3], [1, 3], [1, 3]]

MOFO_TERMS = [        
    MOFOTerm("tragicness", DefaultBounds),
    MOFOTerm("patheticism", DefaultBounds),
    MOFOTerm("thwackability", DefaultBounds),
    MOFOTerm("divinity", DefaultBounds),
    MOFOTerm("moxie", DefaultBounds),
    MOFOTerm("musclitude", DefaultBounds),    
    MOFOTerm("martyrdom", DefaultBounds),
    MOFOTerm("laserlikeness", DefaultBounds), 
    MOFOTerm("basethirst", DefaultBounds),    
    MOFOTerm("continuation", DefaultBounds),    
    MOFOTerm("groundfriction", DefaultBounds),    
    MOFOTerm("indulgence", DefaultBounds),        
    MOFOTerm("unthwackability", DefaultBounds),
    MOFOTerm("ruthlessness", DefaultBounds),
    MOFOTerm("overpowerment", DefaultBounds),    
    MOFOTerm("shakespearianism", DefaultBounds),    
    MOFOTerm("coldness", DefaultBounds),
    MOFOTerm("omniscience", DefaultBounds),           
    MOFOTerm("tenaciousness", DefaultBounds),    
    MOFOTerm("watchfulness", DefaultBounds),    
    MOFOTerm("anticapitalism", DefaultBounds),
    MOFOTerm("chasiness", DefaultBounds)    
]