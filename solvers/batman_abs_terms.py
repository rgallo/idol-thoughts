from collections import namedtuple

BatmanAbsTerm = namedtuple("BatmanAbsTerm", ["stat", "bounds"])

BATMAN_ABS_TERMS = [        
    BatmanAbsTerm("Patheticism", [[0, 5], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("Thwackability", [[0, 5], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("Divinity", [[0, 5], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("Moxie", [[0, 5], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("Musclitude", [[0, 5], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("Martyrdom", [[-5, 5], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("Ruthlessness", [[0, 5], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("WalkingRuthlessness", [[0, 5], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("Unthwackability", [[0, 5], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("Overpowerment", [[0, 5], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("HitOverpowerment", [[0, 5], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("Coldness", [[-5, 5], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("StealWatchfulness", [[0, 5], [0, 3], [0, 2.5]]),        
    BatmanAbsTerm("Omniscience", [[0, 5], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("BaseThirst", [[0, 5], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("AttemptLaserlikeness", [[0, 5], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("Laserlikeness", [[0, 5], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("Tenaciousness", [[0, 5], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("Watchfulness", [[0, 5], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("Anticapitalism", [[0, 5], [0, 3], [0, 2.5]])  
]