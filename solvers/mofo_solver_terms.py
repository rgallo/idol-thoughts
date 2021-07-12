from collections import namedtuple

MOFOTerm = namedtuple("MOFOTerm", ["stat", "bounds"])

MOFO_TERMS = [        
    MOFOTerm("tragicness", [[0, 3], [0, 3], [0, 3]]),
    MOFOTerm("patheticism", [[0, 3], [0, 3], [0, 3]]),
    MOFOTerm("thwackability", [[0, 3], [0, 3], [0, 3]]),
    MOFOTerm("divinity", [[0, 3], [0, 3], [0, 3]]),
    MOFOTerm("moxie", [[0, 3], [0, 3], [0, 3]]),
    MOFOTerm("musclitude", [[0, 3], [0, 3], [0, 3]]),    
    MOFOTerm("martyrdom", [[0, 3], [0, 3], [0, 3]]),
    MOFOTerm("laserlikeness", [[0, 3], [0, 3], [0, 3]]), 
    MOFOTerm("basethirst", [[0, 3], [0, 3], [0, 3]]),    
    MOFOTerm("continuation", [[0, 3], [0, 3], [0, 3]]),    
    MOFOTerm("groundfriction", [[0, 3], [0, 3], [0, 3]]),    
    MOFOTerm("indulgence", [[0, 3], [0, 3], [0, 3]]),        
    MOFOTerm("unthwackability", [[0, 3], [0, 3], [0, 3]]),
    MOFOTerm("ruthlessness", [[0, 3], [0, 3], [0, 3]]),
    MOFOTerm("overpowerment", [[0, 3], [0, 3], [0, 3]]),    
    MOFOTerm("shakespearianism", [[0, 3], [0, 3], [0, 3]]),    
    MOFOTerm("coldness", [[0, 3], [0, 3], [0, 3]]),
    MOFOTerm("omniscience", [[0, 3], [0, 3], [0, 3]]),           
    MOFOTerm("tenaciousness", [[0, 3], [0, 3], [0, 3]]),    
    MOFOTerm("watchfulness", [[0, 3], [0, 3], [0, 3]]),    
    MOFOTerm("anticapitalism", [[0, 3], [0, 3], [0, 3]]),
    MOFOTerm("chasiness", [[0, 3], [0, 3], [0, 3]])    
]