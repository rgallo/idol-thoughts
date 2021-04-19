from collections import namedtuple

BatmanHitsTerm = namedtuple("BatmanHitsTerm", ["stat", "bounds"])

BATMAN_HITS_TERMS = [        
    BatmanHitsTerm("Patheticism", [[-10, 0], [0, 3], [0, 2.5]]),
    BatmanHitsTerm("Thwackability", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanHitsTerm("Divinity", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanHitsTerm("Moxie", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanHitsTerm("Musclitude", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanHitsTerm("Martyrdom", [[0, 5], [0, 3], [0, 2.5]]),
    BatmanHitsTerm("Ruthlessness", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanHitsTerm("WalkingRuthlessness", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanHitsTerm("Unthwackability", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanHitsTerm("Overpowerment", [[0, 10], [0, 3], [0, 2.5]]),    
    BatmanHitsTerm("Coldness", [[-10, 10], [0, 3], [0, 2.5]]),    
    BatmanHitsTerm("Omniscience", [[0, 10], [0, 3], [0, 2.5]])    
]