from collections import namedtuple

MOFOTerm = namedtuple("MOFOTerm", ["stat", "bounds"])

MOFO_TERMS = [        
    MOFOTerm("tragicness", [[1, 10], [0, 3], [1, 3]]),
    MOFOTerm("patheticism", [[1, 10], [0, 3], [1, 3]]),
    MOFOTerm("thwackability", [[1, 10], [0, 3], [1, 3]]),
    MOFOTerm("divinity", [[1, 10], [0, 3], [1, 3]]),
    MOFOTerm("moxie", [[1, 10], [0, 3], [1, 3]]),
    MOFOTerm("musclitude", [[1, 10], [0, 3], [1, 3]]),    
    MOFOTerm("martyrdom", [[1, 10], [0, 3], [1, 3]]),
    MOFOTerm("laserlikeness", [[1, 10], [0, 3], [1, 3]]), 
    MOFOTerm("basethirst", [[1, 10], [0, 3], [1, 3]]),    
    MOFOTerm("continuation", [[1, 10], [0, 3], [1, 3]]),    
    MOFOTerm("groundfriction", [[1, 10], [0, 3], [1, 3]]),    
    MOFOTerm("indulgence", [[1, 10], [0, 3], [1, 3]]),        
    MOFOTerm("unthwackability", [[1, 10], [0, 3], [1, 3]]),
    MOFOTerm("ruthlessness", [[1, 10], [0, 3], [1, 3]]),
    MOFOTerm("overpowerment", [[1, 10], [0, 3], [1, 3]]),    
    MOFOTerm("shakespearianism", [[1, 10], [0, 3], [1, 3]]),    
    MOFOTerm("coldness", [[1, 10], [0, 3], [1, 3]]),
    MOFOTerm("omniscience", [[1, 10], [0, 3], [1, 3]]),           
    MOFOTerm("tenaciousness", [[1, 10], [0, 3], [1, 3]]),    
    MOFOTerm("watchfulness", [[1, 10], [0, 3], [1, 3]]),    
    MOFOTerm("anticapitalism", [[1, 10], [0, 3], [1, 3]]),
    MOFOTerm("chasiness", [[1, 10], [0, 3], [1, 3]])    
]