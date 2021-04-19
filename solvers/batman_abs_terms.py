from collections import namedtuple

BatmanAbsTerm = namedtuple("BatmanAbsTerm", ["stat", "bounds"])

BATMAN_ABS_TERMS = [        
    BatmanAbsTerm("Patheticism", [[-10, 0], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("Thwackability", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("Divinity", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("Moxie", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("Musclitude", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("HitMusclitude", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("Martyrdom", [[-10, 10], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("Ruthlessness", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("WalkingRuthlessness", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("Unthwackability", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanAbsTerm("Overpowerment", [[0, 10], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("Coldness", [[-10, 10], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("HitColdness", [[-10, 10], [0, 3], [0, 2.5]]),        
    BatmanAbsTerm("Omniscience", [[0, 10], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("BaseThirst", [[0, 10], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("AttemptLaserlikeness", [[0, 10], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("Laserlikeness", [[0, 10], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("Tenaciousness", [[0, 10], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("Watchfulness", [[0, 10], [0, 3], [0, 2.5]]),    
    BatmanAbsTerm("Anticapitalism", [[0, 10], [0, 3], [0, 2.5]])  
]