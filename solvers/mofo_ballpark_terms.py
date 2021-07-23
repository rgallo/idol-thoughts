from collections import namedtuple

BallParkTerm = namedtuple("BallParkTerm", ["ballparkstat", "playerstat", "bounds"])
DefaultBounds = [[-3, 3], [0, 2], [0, 2]]
BuffOnlyBounds = [[0, 3], [0, 2], [0, 2]]
DebuffOnlyBounds = [[-3, 0], [0, 2], [0, 2]]

BALLPARK_TERMS = [                    
    BallParkTerm("grandiosity", "Thwackability", BuffOnlyBounds),
    BallParkTerm("grandiosity", "Divinity", DebuffOnlyBounds),        
    BallParkTerm("obtuseness", "Thwackability", BuffOnlyBounds),        
    BallParkTerm("obtuseness", "Musclitude", DebuffOnlyBounds),        
    BallParkTerm("ominousness", "Omniscience", BuffOnlyBounds),        
    BallParkTerm("ominousness", "Musclitude", DebuffOnlyBounds),    
    BallParkTerm("ominousness", "Continuation", DebuffOnlyBounds),
    BallParkTerm("ominousness", "GroundFriction", DebuffOnlyBounds),     
    BallParkTerm("viscosity", "Patheticism", DebuffOnlyBounds),    
    BallParkTerm("viscosity", "Musclitude", DebuffOnlyBounds),    
    BallParkTerm("viscosity", "Continuation", DebuffOnlyBounds),
    BallParkTerm("viscosity", "GroundFriction", DebuffOnlyBounds),    
    BallParkTerm("forwardness", "Ruthlessness", BuffOnlyBounds),    
    BallParkTerm("forwardness", "Musclitude", BuffOnlyBounds),    
    BallParkTerm("forwardness", "Continuation", BuffOnlyBounds),
    BallParkTerm("forwardness", "GroundFriction", BuffOnlyBounds),    
    BallParkTerm("elongation", "Chasiness", DebuffOnlyBounds),        
    BallParkTerm("elongation", "Laserlikeness", DebuffOnlyBounds),         
    BallParkTerm("inconvenience", "Thwackability", DebuffOnlyBounds),    
    BallParkTerm("inconvenience", "BaseThirst", DebuffOnlyBounds),    
    BallParkTerm("fortification", "Divinity", DebuffOnlyBounds),    
    BallParkTerm("hype", "Ruthlessness", BuffOnlyBounds),
    BallParkTerm("hype", "Unthwackability", BuffOnlyBounds),
    BallParkTerm("hype", "Overpowerment", BuffOnlyBounds),
    BallParkTerm("hype", "Shakespearianism", BuffOnlyBounds),
    BallParkTerm("hype", "Coldness", BuffOnlyBounds),
    BallParkTerm("hype", "Omniscience", BuffOnlyBounds),
    BallParkTerm("hype", "Tenaciousness", BuffOnlyBounds),
    BallParkTerm("hype", "Watchfulness", BuffOnlyBounds),
    BallParkTerm("hype", "Anticapitalism", BuffOnlyBounds),
    BallParkTerm("hype", "Chasiness", BuffOnlyBounds),
    BallParkTerm("hype", "Tragicness", DebuffOnlyBounds),
    BallParkTerm("hype", "Patheticism", DebuffOnlyBounds),
    BallParkTerm("hype", "Thwackability", BuffOnlyBounds),
    BallParkTerm("hype", "Divinity", BuffOnlyBounds),
    BallParkTerm("hype", "Moxie", BuffOnlyBounds),
    BallParkTerm("hype", "Musclitude", BuffOnlyBounds),
    BallParkTerm("hype", "Martyrdom", BuffOnlyBounds),
    BallParkTerm("hype", "Laserlikeness", BuffOnlyBounds),
    BallParkTerm("hype", "BaseThirst", BuffOnlyBounds),
    BallParkTerm("hype", "Continuation", BuffOnlyBounds),
    BallParkTerm("hype", "GroundFriction", BuffOnlyBounds),
    BallParkTerm("hype", "Indulgence", BuffOnlyBounds)    
]