"""
PLugIn to compute the a weighted RMS of OlMEGA Data
"""

# (c) Joerg Bitzer @ Jade HS, BSD 3-clause license is the valid license for this source code
# version 0.9 mean is working (std is missing, wait for different interface)

import datetime
import numpy as np
import FeaturePlugins.acousticweighting as aw

import matplotlib.pyplot as plt

class SPL_A_Mean_60:
    feature = 'SPL(A)_broadband_mean_60s'
    description = 'The mean (mu) of a full chunk A-weighted SPL value (computed by all 125ms SPL blocks)'
    isActive = False
    storeAsFeatureFile = False # False: single Value stored in Database, True: Matrix stored in FeatureFile
    
    def __init__(self):
        self.timedelta = 10 # in seconds (max: 60)
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
            fs = existingFeatures['fs']
            PSD = existingFeatures['PSD']
            Pxx = PSD['Pxx']
            Pyy = PSD['Pyy']
            nr_of_frames, fft_size = Pxx.shape
            RMS = existingFeatures['RMS']
            w,f = aw.get_fftweight_vector((fft_size-1)*2,fs,'a','lin')
            
            meanPSD = (((Pxx)*fs)*w)*0.25 # this works because of broadcasting rules in python
            rms_psd = np.mean((meanPSD), axis=1) # mean over frequency
            
            # just debug
            #print(10*np.log10(np.mean(rms_psd)))
            #print(20*np.log10(np.mean(RMS[:,0])))

            # test of wiener-chintchine
            #fig,ax = plt.subplots(nrows=2)
            #ax[0].plot(10*np.log10(rms_psd))
            #ax[1].plot(20*np.log10(RMS[:,0]))
            #plt.show()
            
            
            values = []
            sliceStart = startTime
            counter = int(0)
            frames_per_block = int(nr_of_frames/self.nr_of_blocks)
            
            while sliceStart < endTime:
                cur_rms = 10*np.log10(np.mean(rms_psd[counter*frames_per_block:(counter+1)*frames_per_block]))
                counter += 1
                sliceEnd = sliceStart + datetime.timedelta(seconds= min(60, self.timedelta))
                values.append({"start": sliceStart, "end": sliceEnd, "side": "B", "value": cur_rms, "isvalid": 1})
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
        