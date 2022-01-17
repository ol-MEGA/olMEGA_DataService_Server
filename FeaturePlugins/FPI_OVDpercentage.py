"""
Feature PLugIn (FPI) to compute the percentage (defined between 0 and 1) of OVD blocks (125ms) in one chunk of one minute
"""

# (c) Joerg Bitzer @ Jade HS, BSD 3-clause license is the valid license for this source code
# 
# version 0.1.0 first try 11.01.2021
# version 1.0.0 tested 12.01.2021 JB
# version 1.0.1 debugged and major bug fixed
# version 1.0.0 adding olMEGA_DataService_Tools

import datetime
import numpy as np
import olMEGA_DataService_Tools.acousticweighting as aw

import matplotlib.pyplot as plt

class OVDpercentage:
    feature = ['OVDpercentage']
    description = ['The percentage (0...1) of blocks (125ms) with OVD in 60s data']
    isActive = True
    storeAsFeatureFile = False # False: single Value stored in Database, True: Matrix stored in FeatureFile
    
    def __init__(self):
        self.timedelta = 60 # in seconds (max: 60)
        if (self.timedelta >= 60):
            self.timedelta = 60
        
        self.nr_of_blocks = int(60/self.timedelta)
        pass
    
    def modifieData(self, data):
        returnData = data
        return returnData
    
    def process(self, startTime, endTime, existingFeatures):
        if "OVD" in existingFeatures.keys():
            ## Example for Value in Database
            OVDdata = existingFeatures['OVD']
            
            result = []
            sliceStart = startTime
            sliceEnd = sliceStart + datetime.timedelta(seconds= min(60, self.timedelta))
            
            result.append({"start": sliceStart, "end": sliceEnd, "side": "B", "value": np.mean(OVDdata), "isvalid": 1})
  
            return result

