import datetime
import numpy

class Example_Multi:
    
    feature = ['testFeature1', 'testFeature2']
    description = ['Demo Feature 1 for testing...', 'Demo Feature 2 for testing...']
    isActive = True
    storeAsFeatureFile = False # False: single Value stored in Database, True: Matrix stored in FeatureFile
    
    def __init__(self):
        self.timedelta = 2 # in seconds (max: 60)
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
            return values, values
        elif self.storeAsFeatureFile == True:
            ## Example for Values in FeatureFile
            Frames = 4799
            Dim = 2
            FrameSizeInSamples = 600
            HopSizeInSamples = 300
            fs = 2400
            BlockTime = startTime.strftime('%Y%m%d_%H%M%S%f')[2:-3]
            values = numpy.zeros([Frames, 2])
            return [{"start": startTime, "end": endTime, "value": values, "Frames": Frames, "Dim": Dim, "FrameSizeInSamples": FrameSizeInSamples, "HopSizeInSamples": HopSizeInSamples, "fs" : fs, "BlockTime": BlockTime, "isvalid": 1}], [{"start": startTime, "end": endTime, "value": values, "Frames": Frames, "Dim": Dim, "FrameSizeInSamples": FrameSizeInSamples, "HopSizeInSamples": HopSizeInSamples, "fs" : fs, "BlockTime": BlockTime, "isvalid": 1}]
        