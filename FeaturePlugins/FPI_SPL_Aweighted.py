"""
Feature PLugIn (FPI) to compute the a weighted RMS of OlMEGA Data. The results are the mean (linear mean of all values) in dB and
the standard deviation of the dB values für each 125ms block.
"""

# (c) Joerg Bitzer @ Jade HS, BSD 3-clause license is the valid license for this source code
# version 0.9 mean is working (std is missing, wait for different interface)
# version 0.9.5 changed interface to multi feature
# version 1.0.0 rc-1 0.0 replaced by means of data
# version 1.0.0 tested and worked


import datetime
import numpy as np
import FeaturePlugins.acousticweighting as aw

import matplotlib.pyplot as plt

class SPL_A_Mean_60:
    feature = ['SPL(A)_broadband_mean_10s', 'SPL(A)_broadband_stddev_10s']
    description = ['The mean (mu) of 10s A-weighted SPL value (computed by all 125ms SPL blocks)', 'The Standard Deviation (sigma) of 10s A-weighted SPL value (Attention in dB) (computed by all 125ms SPL blocks)']
    isActive = True
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
            w,f = aw.get_fftweight_vector((fft_size-1)*2,fs,'a','lin')
            meanPSD = (((Pxx+Pyy)*0.5*fs)*w)*0.25 # this works because of broadcasting rules in python
            rms_psd = np.mean((meanPSD), axis=1) # mean over frequency
            
            # just debug
            #RMS = existingFeatures['RMS']
            #print(10*np.log10(np.mean(rms_psd)))
            #print(20*np.log10(np.mean(RMS[:,0])))

            # test of wiener-chintchine
            #fig,ax = plt.subplots(nrows=2)
            #ax[0].plot(10*np.log10(rms_psd))
            #ax[1].plot(20*np.log10(RMS[:,0]))
            #plt.show()
            
            
            values_mean = []
            values_std = []
            
            sliceStart = startTime
            counter = int(0)
            frames_per_block = int(nr_of_frames/self.nr_of_blocks)
            
            while sliceStart < endTime:
                data_block = rms_psd[counter*frames_per_block:(counter+1)*frames_per_block]
                mean_data_block = np.mean(data_block)
                # data extension for non possible values
                data_block[data_block == 0] = mean_data_block
                log_data_block = 10*np.log10(data_block)
                cur_std = np.nanstd(log_data_block,)
                cur_rms = 10*np.log10(mean_data_block)
                counter += 1
                sliceEnd = sliceStart + datetime.timedelta(seconds= min(60, self.timedelta))
                values_mean.append({"start": sliceStart, "end": sliceEnd, "side": "B", "value": cur_rms, "isvalid": 1})
                values_std.append({"start": sliceStart, "end": sliceEnd, "side": "B", "value": cur_std, "isvalid": 1})
                sliceStart = sliceEnd
            return values_mean, values_std

