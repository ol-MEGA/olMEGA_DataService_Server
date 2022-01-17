"""
Feature-PLugIn (FPI) to compute the mean of the bandenergy for 125ms blocks in the octave bands from 125 Hz upt o 4kHz 
"""

# (c) Joerg Bitzer @ Jade HS, BSD 3-clause license is the valid license for this source code
# version 0.1 init
# version 1.0.0 adding olMEGA_DataService_Tools

import datetime
import numpy as np
import olMEGA_DataService_Tools.freq2freqtransforms as ft

import matplotlib.pyplot as plt

class SPL_A_Mean_60:
    feature = ['band_energy_125Hz','band_energy_250Hz','band_energy_500Hz','band_energy_1000Hz','band_energy_2000Hz','band_energy_4000Hz']
    description = ['The mean (mu) of the 125Hz band of 60s data (125ms blocks)','The mean (mu) of the 250Hz band of 60s data (125ms blocks)',
                   'The mean (mu) of the 500Hz band of 60s data (125ms blocks)','The mean (mu) of the 1000Hz band of 60s data (125ms blocks)',
                   'The mean (mu) of the 2000Hz band of 60s data (125ms blocks)','The mean (mu) of the 4000Hz band of 60s data (125ms blocks)']
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
            fs = existingFeatures['fs']
            PSD = existingFeatures['PSD']
            Pxx = PSD['Pxx']
            Pyy = PSD['Pyy']
            nr_of_frames, fft_size = Pxx.shape
            weight_mat,a,b = ft.get_spectrum_fractionaloctave_transformmatrix((fft_size-1)*2,fs,125,4000,1)
            mu_Pxx = np.mean(Pxx, axis = 0)
            mu_Pyy = np.mean(Pyy, axis = 0)
            band_energL = (mu_Pxx@weight_mat)
            band_energR = (mu_Pyy@weight_mat)
            band_energ = 10*np.log10(0.5*(band_energL +band_energR) + np.finfo(float).eps)
                        
            # just debug
            #RMS = existingFeatures['RMS']
            #print(10*np.log10(np.mean(rms_psd)))
            #print(20*np.log10(np.mean(RMS[:,0])))

            # test of wiener-chintchine
            #fig,ax = plt.subplots(nrows=2)
            #ax[0].plot(10*np.log10(rms_psd))
            #ax[1].plot(20*np.log10(RMS[:,0]))
            #plt.show()
            
            
            values_125 = []
            values_250 = []
            values_500 = []
            values_1000 = []
            values_2000 = []
            values_4000 = []
            
            sliceStart = startTime
            
            while sliceStart < endTime:
                sliceEnd = sliceStart + datetime.timedelta(seconds= min(60, self.timedelta))
                values_125.append({"start": sliceStart, "end": sliceEnd, "side": "B", "value": band_energ[0], "isvalid": 1})
                values_250.append({"start": sliceStart, "end": sliceEnd, "side": "B", "value": band_energ[1], "isvalid": 1})
                values_500.append({"start": sliceStart, "end": sliceEnd, "side": "B", "value": band_energ[2], "isvalid": 1})
                values_1000.append({"start": sliceStart, "end": sliceEnd, "side": "B", "value": band_energ[3], "isvalid": 1})
                values_2000.append({"start": sliceStart, "end": sliceEnd, "side": "B", "value": band_energ[4], "isvalid": 1})
                values_4000.append({"start": sliceStart, "end": sliceEnd, "side": "B", "value": band_energ[5], "isvalid": 1})
                sliceStart = sliceEnd
            return values_125,values_250,values_500,values_1000,values_2000,values_4000

