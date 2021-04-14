from collections import namedtuple

BatmanModTerm = namedtuple("BatmanModTerm", ["attr", "team", "stat", "bounds"])

BATMAN_MOD_TERMS = [    
    BatmanModTerm("LOVE", "opp", "Ruthlessness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Unthwackability",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Overpowerment",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Shakespearianism",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Coldness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Tragicness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Patheticism",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Thwackability",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Divinity",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Moxie",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Musclitude",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Martyrdom",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Omniscience",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Tenaciousness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Watchfulness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Anticapitalism",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Chasiness",[[-5, 5], [0, 1], [1, 1.5]]),    
    BatmanModTerm("LOVE", "opp", "Laserlikeness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "BaseThirst",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Continuation",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "GroundFriction",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("LOVE", "opp", "Indulgence",[[-5, 5], [0, 1], [1, 1.5]]),    
    BatmanModTerm("EXTRA_STRIKE", "opp", "Ruthlessness", [[-15, 10], [-3, 4], [-3, 4]]),
    BatmanModTerm("EXTRA_STRIKE", "opp", "Unthwackability", [[-15, 10], [-3, 4], [-3, 4]]),
    BatmanModTerm("EXTRA_STRIKE", "opp", "Overpowerment", [[-15, 10], [-3, 4], [-3, 4]]),
    BatmanModTerm("EXTRA_STRIKE", "opp", "Shakespearianism", [[-15, 10], [-3, 4], [-3, 4]]),
    BatmanModTerm("EXTRA_STRIKE", "opp", "Coldness", [[-15, 10], [-3, 4], [-3, 4]]),
    BatmanModTerm("EXTRA_STRIKE", "same", "Tragicness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("EXTRA_STRIKE", "same", "Patheticism",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("EXTRA_STRIKE", "same", "Thwackability",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("EXTRA_STRIKE", "same", "Divinity",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("EXTRA_STRIKE", "same", "Moxie",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("EXTRA_STRIKE", "same", "Musclitude",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("EXTRA_STRIKE", "same", "Martyrdom",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("EXTRA_STRIKE", "opp", "Omniscience", [[-15, 10], [-3, 4], [-3, 4]]),
    BatmanModTerm("EXTRA_STRIKE", "opp", "Tenaciousness", [[-15, 10], [-3, 4], [-3, 4]]),
    BatmanModTerm("EXTRA_STRIKE", "opp", "Watchfulness", [[-15, 10], [-3, 4], [-3, 4]]),
    BatmanModTerm("EXTRA_STRIKE", "opp", "Anticapitalism", [[-15, 10], [-3, 4], [-3, 4]]),
    BatmanModTerm("EXTRA_STRIKE", "opp", "Chasiness", [[-15, 10], [-3, 4], [-3, 4]]),    
    BatmanModTerm("EXTRA_STRIKE", "same", "Laserlikeness", [[-15, 10], [-3, 4], [-3, 4]]),
    BatmanModTerm("EXTRA_STRIKE", "same", "BaseThirst", [[-15, 10], [-3, 4], [-3, 4]]),
    BatmanModTerm("EXTRA_STRIKE", "same", "Continuation", [[-15, 10], [-3, 4], [-3, 4]]),
    BatmanModTerm("EXTRA_STRIKE", "same", "GroundFriction", [[-15, 10], [-3, 4], [-3, 4]]),
    BatmanModTerm("EXTRA_STRIKE", "same", "Indulgence", [[-15, 10], [-3, 4], [-3, 4]]),        
    BatmanModTerm("O_NO", "opp", "Ruthlessness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "opp", "Unthwackability",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "opp", "Overpowerment",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "opp", "Shakespearianism",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "opp", "Coldness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "same", "Tragicness",[[-5, 0], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "same", "Patheticism",[[-5, 0], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "same", "Thwackability",[[0, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "same", "Divinity",[[0, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "same", "Moxie",[[0, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "same", "Musclitude",[[0, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "same", "Martyrdom",[[0, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "opp", "Omniscience",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "opp", "Tenaciousness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "opp", "Watchfulness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "opp", "Anticapitalism",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "opp", "Chasiness",[[-5, 5], [0, 1], [1, 1.5]]),    
    BatmanModTerm("O_NO", "same", "Laserlikeness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "same", "BaseThirst",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "same", "Continuation",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "same", "GroundFriction",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("O_NO", "same", "Indulgence",[[-5, 5], [0, 1], [1, 1.5]]),        
    BatmanModTerm("HIGH_PRESSURE", "same", "Tragicness",[[-5, 0], [0, 1], [1, 1.5]]),
    BatmanModTerm("HIGH_PRESSURE", "same", "Patheticism",[[-5, 0], [0, 1], [1, 1.5]]),
    BatmanModTerm("HIGH_PRESSURE", "same", "Thwackability",[[0, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("HIGH_PRESSURE", "same", "Divinity",[[0, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("HIGH_PRESSURE", "same", "Moxie",[[0, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("HIGH_PRESSURE", "same", "Musclitude",[[0, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("HIGH_PRESSURE", "same", "Martyrdom",[[0, 5], [0, 1], [1, 1.5]]),    
    BatmanModTerm("HIGH_PRESSURE", "same", "Laserlikeness",[[0, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("HIGH_PRESSURE", "same", "BaseThirst",[[0, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("HIGH_PRESSURE", "same", "Continuation",[[0, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("HIGH_PRESSURE", "same", "GroundFriction",[[0, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("HIGH_PRESSURE", "same", "Indulgence",[[0, 5], [0, 1], [1, 1.5]]),        
    BatmanModTerm("BASE_INSTINCTS", "opp", "Ruthlessness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "opp", "Unthwackability",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "opp", "Overpowerment",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "opp", "Shakespearianism",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "opp", "Coldness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "same", "Tragicness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "same", "Patheticism",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "same", "Thwackability",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "same", "Divinity",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "same", "Moxie",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "same", "Musclitude",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "same", "Martyrdom",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "opp", "Omniscience",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "opp", "Tenaciousness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "opp", "Watchfulness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "opp", "Anticapitalism",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "opp", "Chasiness",[[-5, 5], [0, 1], [1, 1.5]]),    
    BatmanModTerm("BASE_INSTINCTS", "same", "Laserlikeness",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "same", "BaseThirst",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "same", "Continuation",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "same", "GroundFriction",[[-5, 5], [0, 1], [1, 1.5]]),
    BatmanModTerm("BASE_INSTINCTS", "same", "Indulgence",[[-5, 5], [0, 1], [1, 1.5]])
]