import datetime
import numpy

class PSD:
    
    feature = 'PSD'
    description = 'PSD'
    isActive = False
    storeAsFeatureFile = True # False: single Value stored in Database, True: Matrix stored in FeatureFile
    
    def __init__(self):
        pass
    
    def modifieData(self, data):
        n = [int(data.shape[1] / 2), int(data.shape[1] / 4)]
        temp = data[:, 0 : n[0]]
        returnData = {}
        returnData["Pxy"] = temp[:, 0 :: 2] + temp[:, 1 : : 2] * 1j
        returnData["Pxx"] = data[:, n[0] : n[0] + n[1]]
        returnData["Pyy"] = data[:, n[0] + n[1] : ]                    
        return returnData
    
    def process(self, startTime, endTime, existingFeatures):
        return []
        