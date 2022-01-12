"""
Feature PLugIn (FPI) to compute the percentage of OVD blocks (125ms) in one chunk of one minute
"""

# (c) Joerg Bitzer @ Jade HS, BSD 3-clause license is the valid license for this source code
# version 0.1.0 first try

import datetime
import numpy as np
import FeaturePlugins.acousticweighting as aw

import matplotlib.pyplot as plt

class OVDpercentage:
    feature = ['OVDpercentage']
    description = ['The percentage of blocks (125ms) with OVD in 60s data']
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
        if self.storeAsFeatureFile == False:
            ## Example for Value in Database
            OVDdata = existingFeatures['OVD']
            
            # just debug
            print(np.mean(OVDdata))
            print(len(OVDdata[OVDdata == 1])/len(OVDdata))
            #plt.show()
            
            
            result = []
            
            
            while sliceStart < endTime:
                result.append(len(OVDdata[OVDdata == 1])/len(OVDdata))
            return result

