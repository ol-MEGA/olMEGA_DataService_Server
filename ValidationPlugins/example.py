from enum import Enum
import numpy

class state(Enum):
    invalid     = -1
    undefined   = 0
    valid       = 1

class Example:
    
    isActive = False
    
    def __init__(self):
        pass
    
    def process(self, featureName, featureData, existingFeatures):
        return state.undefined