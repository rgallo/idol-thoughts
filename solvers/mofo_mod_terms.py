from collections import namedtuple

MofoModTerm = namedtuple("MofoModTerm", ["attr", "team", "stat", "bounds"])
DefaultBounds = DefaultBounds

MOFO_MOD_TERMS = [    
    MofoModTerm("LOVE", "opp", "Ruthlessness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Unthwackability", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Overpowerment", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Shakespearianism", DefaultBounds),
    MofoModTerm("LOVE", "opp", "Coldness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanOmniscience", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanTenaciousness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanWatchfulness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanAnticapitalism", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanChasiness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanTragicness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanPatheticism", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanThwackability", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanDivinity", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanMoxie", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanMusclitude", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanMartyrdom", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanLaserlikeness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanBaseThirst", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanContinuation", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanGroundFriction", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MeanIndulgence", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MaxOmniscience", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MaxTenaciousness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MaxWatchfulness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MaxAnticapitalism", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MaxChasiness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MaxThwackability", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MaxDivinity", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MaxMoxie", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MaxMusclitude", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MaxMartyrdom", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MaxLaserLikeness", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MaxBaseThirst", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MaxContinuation", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MaxGroundFriction", DefaultBounds),
    MofoModTerm("LOVE", "opp", "MaxIndulgence", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "Ruthlessness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "Unthwackability", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "Overpowerment", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "Shakespearianism", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "Coldness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "MeanOmniscience", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "MeanTenaciousness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "MeanWatchfulness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "MeanAnticapitalism", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "MeanChasiness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "MeanTragicness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "MeanPatheticism", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "MeanThwackability", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("EXTRA_STRIKE", "same", "MeanDivinity", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("EXTRA_STRIKE", "same", "MeanMoxie", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("EXTRA_STRIKE", "same", "MeanMusclitude", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("EXTRA_STRIKE", "same", "MeanMartyrdom", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("EXTRA_STRIKE", "same", "MeanLaserlikeness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "MeanBaseThirst", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "MeanContinuation", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "MeanGroundFriction", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "MeanIndulgence", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "MaxOmniscience", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "MaxTenaciousness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "MaxWatchfulness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "MaxAnticapitalism", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "opp", "MaxChasiness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "MaxThwackability", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("EXTRA_STRIKE", "same", "MaxDivinity", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("EXTRA_STRIKE", "same", "MaxMoxie", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("EXTRA_STRIKE", "same", "MaxMusclitude", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("EXTRA_STRIKE", "same", "MaxMartyrdom", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("EXTRA_STRIKE", "same", "MaxLaserLikeness", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "MaxBaseThirst", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "MaxContinuation", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "MaxGroundFriction", DefaultBounds),
    MofoModTerm("EXTRA_STRIKE", "same", "MaxIndulgence", DefaultBounds),    
    MofoModTerm("O_NO", "opp", "Ruthlessness", DefaultBounds),
    MofoModTerm("O_NO", "opp", "Unthwackability", DefaultBounds),
    MofoModTerm("O_NO", "opp", "Overpowerment", DefaultBounds),
    MofoModTerm("O_NO", "opp", "Shakespearianism", DefaultBounds),
    MofoModTerm("O_NO", "opp", "Coldness", DefaultBounds),
    MofoModTerm("O_NO", "opp", "MeanOmniscience", DefaultBounds),
    MofoModTerm("O_NO", "opp", "MeanTenaciousness", DefaultBounds),
    MofoModTerm("O_NO", "opp", "MeanWatchfulness", DefaultBounds),
    MofoModTerm("O_NO", "opp", "MeanAnticapitalism", DefaultBounds),
    MofoModTerm("O_NO", "opp", "MeanChasiness", DefaultBounds),
    MofoModTerm("O_NO", "same", "MeanTragicness", [[-5, 0], [0, 1], [1, 1.5]]),
    MofoModTerm("O_NO", "same", "MeanPatheticism", [[-5, 0], [0, 1], [1, 1.5]]),
    MofoModTerm("O_NO", "same", "MeanThwackability", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("O_NO", "same", "MeanDivinity", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("O_NO", "same", "MeanMoxie", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("O_NO", "same", "MeanMusclitude", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("O_NO", "same", "MeanMartyrdom", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("O_NO", "same", "MeanLaserlikeness", DefaultBounds),
    MofoModTerm("O_NO", "same", "MeanBaseThirst", DefaultBounds),
    MofoModTerm("O_NO", "same", "MeanContinuation", DefaultBounds),
    MofoModTerm("O_NO", "same", "MeanGroundFriction", DefaultBounds),
    MofoModTerm("O_NO", "same", "MeanIndulgence", DefaultBounds),
    MofoModTerm("O_NO", "opp", "MaxOmniscience", DefaultBounds),
    MofoModTerm("O_NO", "opp", "MaxTenaciousness", DefaultBounds),
    MofoModTerm("O_NO", "opp", "MaxWatchfulness", DefaultBounds),
    MofoModTerm("O_NO", "opp", "MaxAnticapitalism", DefaultBounds),
    MofoModTerm("O_NO", "opp", "MaxChasiness", DefaultBounds),
    MofoModTerm("O_NO", "same", "MaxThwackability", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("O_NO", "same", "MaxDivinity", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("O_NO", "same", "MaxMoxie", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("O_NO", "same", "MaxMusclitude", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("O_NO", "same", "MaxMartyrdom", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("O_NO", "same", "MaxLaserLikeness", DefaultBounds),
    MofoModTerm("O_NO", "same", "MaxBaseThirst", DefaultBounds),
    MofoModTerm("O_NO", "same", "MaxContinuation", DefaultBounds),
    MofoModTerm("O_NO", "same", "MaxGroundFriction", DefaultBounds),
    MofoModTerm("O_NO", "same", "MaxIndulgence", DefaultBounds),        
    MofoModTerm("HIGH_PRESSURE", "same", "MeanTragicness", [[-5, 0], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MeanPatheticism", [[-5, 0], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MeanThwackability", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MeanDivinity", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MeanMoxie", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MeanMusclitude", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MeanMartyrdom", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MeanLaserlikeness", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MeanBaseThirst", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MeanContinuation", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MeanGroundFriction", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MeanIndulgence", [[0, 5], [0, 1], [1, 1.5]]),    
    MofoModTerm("HIGH_PRESSURE", "same", "MaxThwackability", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MaxDivinity", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MaxMoxie", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MaxMusclitude", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MaxMartyrdom", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MaxLaserLikeness", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MaxBaseThirst", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MaxContinuation", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MaxGroundFriction", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("HIGH_PRESSURE", "same", "MaxIndulgence", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("BASE_INSTINCTS", "opp", "Ruthlessness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "Unthwackability", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "Overpowerment", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "Shakespearianism", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "Coldness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "MeanOmniscience", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "MeanTenaciousness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "MeanWatchfulness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "MeanAnticapitalism", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "MeanChasiness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MeanTragicness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MeanPatheticism", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MeanThwackability", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MeanDivinity", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MeanMoxie", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MeanMusclitude", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MeanMartyrdom", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MeanLaserlikeness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MeanBaseThirst", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MeanContinuation", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MeanGroundFriction", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MeanIndulgence", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "MaxOmniscience", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "MaxTenaciousness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "MaxWatchfulness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "MaxAnticapitalism", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "opp", "MaxChasiness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MaxThwackability", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MaxDivinity", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MaxMoxie", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MaxMusclitude", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MaxMartyrdom", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MaxLaserLikeness", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MaxBaseThirst", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MaxContinuation", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MaxGroundFriction", DefaultBounds),
    MofoModTerm("BASE_INSTINCTS", "same", "MaxIndulgence", DefaultBounds),
    MofoModTerm("0", "opp", "Ruthlessness", DefaultBounds),
    MofoModTerm("0", "opp", "Unthwackability", DefaultBounds),
    MofoModTerm("0", "opp", "Overpowerment", DefaultBounds),
    MofoModTerm("0", "opp", "Shakespearianism", DefaultBounds),
    MofoModTerm("0", "opp", "Coldness", DefaultBounds),
    MofoModTerm("0", "opp", "MeanOmniscience", DefaultBounds),
    MofoModTerm("0", "opp", "MeanTenaciousness", DefaultBounds),
    MofoModTerm("0", "opp", "MeanWatchfulness", DefaultBounds),
    MofoModTerm("0", "opp", "MeanAnticapitalism", DefaultBounds),
    MofoModTerm("0", "opp", "MeanChasiness", DefaultBounds),
    MofoModTerm("0", "same", "MeanTragicness", DefaultBounds),
    MofoModTerm("0", "same", "MeanPatheticism", DefaultBounds),
    MofoModTerm("0", "same", "MeanThwackability", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("0", "same", "MeanDivinity", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("0", "same", "MeanMoxie", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("0", "same", "MeanMusclitude", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("0", "same", "MeanMartyrdom", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("0", "same", "MeanLaserlikeness", DefaultBounds),
    MofoModTerm("0", "same", "MeanBaseThirst", DefaultBounds),
    MofoModTerm("0", "same", "MeanContinuation", DefaultBounds),
    MofoModTerm("0", "same", "MeanGroundFriction", DefaultBounds),
    MofoModTerm("0", "same", "MeanIndulgence", DefaultBounds),
    MofoModTerm("0", "opp", "MaxOmniscience", DefaultBounds),
    MofoModTerm("0", "opp", "MaxTenaciousness", DefaultBounds),
    MofoModTerm("0", "opp", "MaxWatchfulness", DefaultBounds),
    MofoModTerm("0", "opp", "MaxAnticapitalism", DefaultBounds),
    MofoModTerm("0", "opp", "MaxChasiness", DefaultBounds),
    MofoModTerm("0", "same", "MaxThwackability", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("0", "same", "MaxDivinity", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("0", "same", "MaxMoxie", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("0", "same", "MaxMusclitude", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("0", "same", "MaxMartyrdom", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("0", "same", "MaxLaserLikeness", DefaultBounds),
    MofoModTerm("0", "same", "MaxBaseThirst", DefaultBounds),
    MofoModTerm("0", "same", "MaxContinuation", DefaultBounds),
    MofoModTerm("0", "same", "MaxGroundFriction", DefaultBounds),
    MofoModTerm("0", "same", "MaxIndulgence", DefaultBounds),
    MofoModTerm("H20", "opp", "Ruthlessness", DefaultBounds),
    MofoModTerm("H20", "opp", "Unthwackability", DefaultBounds),
    MofoModTerm("H20", "opp", "Overpowerment", DefaultBounds),
    MofoModTerm("H20", "opp", "Shakespearianism", DefaultBounds),
    MofoModTerm("H20", "opp", "Coldness", DefaultBounds),
    MofoModTerm("H20", "opp", "MeanOmniscience", DefaultBounds),
    MofoModTerm("H20", "opp", "MeanTenaciousness", DefaultBounds),
    MofoModTerm("H20", "opp", "MeanWatchfulness", DefaultBounds),
    MofoModTerm("H20", "opp", "MeanAnticapitalism", DefaultBounds),
    MofoModTerm("H20", "opp", "MeanChasiness", DefaultBounds),
    MofoModTerm("H20", "same", "MeanTragicness", DefaultBounds),
    MofoModTerm("H20", "same", "MeanPatheticism", DefaultBounds),
    MofoModTerm("H20", "same", "MeanThwackability", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("H20", "same", "MeanDivinity", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("H20", "same", "MeanMoxie", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("H20", "same", "MeanMusclitude", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("H20", "same", "MeanMartyrdom", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("H20", "same", "MeanLaserlikeness", DefaultBounds),
    MofoModTerm("H20", "same", "MeanBaseThirst", DefaultBounds),
    MofoModTerm("H20", "same", "MeanContinuation", DefaultBounds),
    MofoModTerm("H20", "same", "MeanGroundFriction", DefaultBounds),
    MofoModTerm("H20", "same", "MeanIndulgence", DefaultBounds),
    MofoModTerm("H20", "opp", "MaxOmniscience", DefaultBounds),
    MofoModTerm("H20", "opp", "MaxTenaciousness", DefaultBounds),
    MofoModTerm("H20", "opp", "MaxWatchfulness", DefaultBounds),
    MofoModTerm("H20", "opp", "MaxAnticapitalism", DefaultBounds),
    MofoModTerm("H20", "opp", "MaxChasiness", DefaultBounds),
    MofoModTerm("H20", "same", "MaxThwackability", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("H20", "same", "MaxDivinity", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("H20", "same", "MaxMoxie", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("H20", "same", "MaxMusclitude", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("H20", "same", "MaxMartyrdom", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("H20", "same", "MaxLaserLikeness", DefaultBounds),
    MofoModTerm("H20", "same", "MaxBaseThirst", DefaultBounds),
    MofoModTerm("H20", "same", "MaxContinuation", DefaultBounds),
    MofoModTerm("H20", "same", "MaxGroundFriction", DefaultBounds),
    MofoModTerm("H20", "same", "MaxIndulgence", DefaultBounds),
    MofoModTerm("FIERY", "same", "Ruthlessness", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("FIERY", "same", "Unthwackability", DefaultBounds),
    MofoModTerm("FIERY", "same", "Overpowerment", DefaultBounds),
    MofoModTerm("FIERY", "same", "Shakespearianism", DefaultBounds),
    MofoModTerm("FIERY", "same", "Coldness", DefaultBounds),
    MofoModTerm("FIERY", "same", "MeanOmniscience", DefaultBounds),
    MofoModTerm("FIERY", "same", "MeanTenaciousness", DefaultBounds),
    MofoModTerm("FIERY", "same", "MeanWatchfulness", DefaultBounds),
    MofoModTerm("FIERY", "same", "MeanAnticapitalism", DefaultBounds),
    MofoModTerm("FIERY", "same", "MeanChasiness", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MeanTragicness", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MeanPatheticism", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MeanThwackability", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MeanDivinity", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MeanMoxie", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MeanMusclitude", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MeanMartyrdom", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MeanLaserlikeness", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MeanBaseThirst", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MeanContinuation", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MeanGroundFriction", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MeanIndulgence", DefaultBounds),
    MofoModTerm("FIERY", "same", "MaxOmniscience", DefaultBounds),
    MofoModTerm("FIERY", "same", "MaxTenaciousness", DefaultBounds),
    MofoModTerm("FIERY", "same", "MaxWatchfulness", DefaultBounds),
    MofoModTerm("FIERY", "same", "MaxAnticapitalism", DefaultBounds),
    MofoModTerm("FIERY", "same", "MaxChasiness", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MaxThwackability", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MaxDivinity", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MaxMoxie", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MaxMusclitude", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MaxMartyrdom", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MaxLaserLikeness", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MaxBaseThirst", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MaxContinuation", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MaxGroundFriction", DefaultBounds),
    MofoModTerm("FIERY", "opp", "MaxIndulgence", DefaultBounds),
    MofoModTerm("AAA", "same", "MeanOmniscience", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanTenaciousness", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanWatchfulness", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanAnticapitalism", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanChasiness", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanTragicness", [[-5, 0], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanPatheticism", [[-5, 0], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanThwackability", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanDivinity", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanMoxie", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanMusclitude", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanMartyrdom", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanLaserlikeness", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanBaseThirst", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanContinuation", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanGroundFriction", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MeanIndulgence", [[0, 5], [0, 1], [1, 1.5]]),    
    MofoModTerm("AAA", "same", "MaxOmniscience", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MaxTenaciousness", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MaxWatchfulness", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MaxAnticapitalism", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MaxChasiness", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MaxThwackability", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MaxDivinity", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MaxMoxie", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MaxMusclitude", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MaxMartyrdom", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MaxLaserLikeness", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MaxBaseThirst", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MaxContinuation", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MaxGroundFriction", [[0, 5], [0, 1], [1, 1.5]]),
    MofoModTerm("AAA", "same", "MaxIndulgence", [[0, 5], [0, 1], [1, 1.5]])    
]
