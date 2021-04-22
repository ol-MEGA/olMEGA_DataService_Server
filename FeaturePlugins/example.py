import datetime

class Example:
    
    feature = 'testFeature'
    description = 'Demo Feature for testing...'
    isActive = True
    
    def __init__(self):
        self.timedelta = 2 # in seconds (max: 60)
        pass
    
    def process(self, startTime, endTime, existingFeatures):
        values = []
        sliceStart = startTime
        while sliceStart < endTime:
            sliceEnd = sliceStart + datetime.timedelta(seconds= min(60, self.timedelta))
            values.append({"start": sliceStart, "end": sliceEnd, "side": "B", "value": 0, "isvalid": 1})
            sliceStart = sliceEnd
        return values