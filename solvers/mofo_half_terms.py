from collections import namedtuple

MOFOHalfTerm = namedtuple("MOFOHalfTerm", ["stat", "bounds"])
DefaultBounds = [[0.1, 0.9]]

MOFO_HALF_TERMS = [        
    MOFOHalfTerm("tragicness", DefaultBounds),
    MOFOHalfTerm("patheticism", DefaultBounds),
    MOFOHalfTerm("thwackability", DefaultBounds),
    MOFOHalfTerm("divinity", DefaultBounds),
    MOFOHalfTerm("moxie", DefaultBounds),
    MOFOHalfTerm("musclitude", DefaultBounds),
    MOFOHalfTerm("martyrdom", DefaultBounds),
    MOFOHalfTerm("laserlikeness", DefaultBounds),
    MOFOHalfTerm("basethirst", DefaultBounds),
    MOFOHalfTerm("continuation", DefaultBounds),
    MOFOHalfTerm("groundfriction", DefaultBounds),
    MOFOHalfTerm("indulgence", DefaultBounds),
    MOFOHalfTerm("unthwackability", DefaultBounds),
    MOFOHalfTerm("ruthlessness", DefaultBounds),
    MOFOHalfTerm("overpowerment", DefaultBounds),
    MOFOHalfTerm("shakespearianism", DefaultBounds),
    MOFOHalfTerm("coldness", DefaultBounds),
    MOFOHalfTerm("omniscience", DefaultBounds),
    MOFOHalfTerm("tenaciousness", DefaultBounds),
    MOFOHalfTerm("watchfulness", DefaultBounds),
    MOFOHalfTerm("anticapitalism", DefaultBounds),
    MOFOHalfTerm("chasiness", DefaultBounds)
]