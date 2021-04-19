from collections import namedtuple

BatmanHrsTerm = namedtuple("BatmanHrsTerm", ["stat", "bounds"])

BATMAN_HRS_TERMS = [        
    BatmanHrsTerm("Patheticism", [[-10, 0], [0, 3], [0, 2.5]]),
    BatmanHrsTerm("Thwackability", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanHrsTerm("Divinity", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanHrsTerm("Moxie", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanHrsTerm("Musclitude", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanHrsTerm("Martyrdom", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanHrsTerm("Ruthlessness", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanHrsTerm("WalkingRuthlessness", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanHrsTerm("Unthwackability", [[0, 10], [0, 3], [0, 2.5]]),
    BatmanHrsTerm("Overpowerment", [[0, 10], [0, 3], [0, 2.5]]),    
    BatmanHrsTerm("Coldness", [[-10, 10], [0, 3], [0, 2.5]])    
]