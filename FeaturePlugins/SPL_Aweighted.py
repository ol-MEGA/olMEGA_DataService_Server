import datetime
import numpy as np
import matplotlib.pyplot as plt

class SPL_A_Mean_60:
    feature = 'SPL(A)_broadband_mean_60s'
    description = 'The mean (mu) of a full chunk A-weighted SPL value (computed by all 125ms SPL blocks)'
    isActive = True
    storeAsFeatureFile = False # False: single Value stored in Database, True: Matrix stored in FeatureFile
    
    def __init__(self):
        self.timedelta = 60 # in seconds (max: 60)
        if (self.timedelta >= 60):
            self.timedelta = 60
        
        pass
    
    def modifieData(self, data):
        returnData = data
        return returnData
    
    def process(self, startTime, endTime, existingFeatures):
        if self.storeAsFeatureFile == False:
            ## Example for Value in Database
            fs = existingFeatures['fs']
            #PSD = existingFeatures['PSD']
            #Pxx = PSD['Pxx']
            #Pyy = PSD['Pyy']
            #RMS = existingFeatures['RMS']
            
            # test of wiener-chintchine
            #rms_psd = np.sum(np.sqrt(Pxx), axis=1)
            #fig,ax = plt.subplots(nrows=2)
            #ax[0].plot(20*np.log10(rms_psd))
            #ax[1].plot(20*np.log10(RMS[:,0]))
            #plt.show()
            
            print(fs)
            values = []
            sliceStart = startTime
            while sliceStart < endTime:
                sliceEnd = sliceStart + datetime.timedelta(seconds= min(60, self.timedelta))
                values.append({"start": sliceStart, "end": sliceEnd, "side": "B", "value": 0, "isvalid": 1})
                sliceStart = sliceEnd
            return values

class SPL_A_StandardDev_60:
 
    feature = 'SPL(A)_broadband_Standarddev_60s'
    description = 'The standard deviation (sigma) of a full chunk A-weighted SPL value (computed by all 125ms SPL blocks)'
    isActive = False
    storeAsFeatureFile = False # False: single Value stored in Database, True: Matrix stored in FeatureFile
    
    def __init__(self):
        self.timedelta = 60 # in seconds (max: 60)
        if (self.timedelta >= 60):
            self.timedelta = 60
        
        pass
    
    def modifieData(self, data):
        returnData = data
        return returnData
    
    def process(self, startTime, endTime, existingFeatures):
        if self.storeAsFeatureFile == False:
            ## Example for Value in Database
            values = []
            sliceStart = startTime
            while sliceStart < endTime:
                sliceEnd = sliceStart + datetime.timedelta(seconds= min(60, self.timedelta))
                values.append({"start": sliceStart, "end": sliceEnd, "side": "B", "value": 0, "isvalid": 1})
                sliceStart = sliceEnd
            return values
        