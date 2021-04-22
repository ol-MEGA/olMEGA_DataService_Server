import os
import glob
import uuid
import main
import numpy
import inspect
import datetime
import matplotlib.pyplot as plt
from olMEGA_DataService_Server.dataConnectors import databaseConnector

class FeatureService():

    def __init__(self):
        self.plugins = []
        self.db = databaseConnector()
        query = "Select * FROM EMA_usergroup"
        usergroups = self.db.execute_query(query)
        for file in os.listdir("FeaturePlugins"):
            if file.endswith(".py"):
                imported_module = __import__("FeaturePlugins.%s" % file.replace(".py", ""))
                for name, module in inspect.getmembers(imported_module):
                    if not name.startswith("__"):
                        for name, plugin in inspect.getmembers(module):
                            if not name.startswith("__") and hasattr(plugin, "feature") and hasattr(plugin, "description") and hasattr(plugin, "isActive") and plugin.isActive:
                                self.plugins.append(plugin)
                                query = 'SELECT * FROM EMA_Feature WHERE name like "%s"' % plugin.feature.lower()
                                Features = self.db.execute_query(query)
                                if len(Features) == 0:
                                    newFeatureId = str(uuid.uuid4())
                                    query = 'INSERT INTO EMA_Feature (ID, Name, Description) VALUES ("%s", "%s", "%s")' % (newFeatureId, plugin.feature.lower(), plugin.description)
                                    self.db.execute_query(query)
                                    if main.develServer:
                                        for usergroup in usergroups:
                                            query = 'INSERT INTO EMA_authorization (ID, Feature_ID, UserGroup_ID, AllowRead, AllowWrite) VALUES ("%s", "%s", "%s", %d, %d)' % (str(uuid.uuid4()), newFeatureId, usergroup["id"], 1, 0)
                                            self.db.execute_query(query)
        self.db.connection.commit()
        
    def loadFeatureFileData(self, filenames):
        featureFileData = {}
        fs = None
        for file in filenames:
            fileNameParts = os.path.basename(file).split("_")
            if len(fileNameParts) > 1:
                with open(file, mode='rb') as filereader:
                    data = filereader.read()
                vFrames = int.from_bytes(data[0:4], byteorder='big', signed=True)
                nDim = int.from_bytes(data[4:8], byteorder='big', signed=True)
                FrameSizeInSamples = int.from_bytes(data[8:12], byteorder='big', signed=True)
                HopSizeInSamples = int.from_bytes(data[12:16], byteorder='big', signed=True)
                fs = int.from_bytes(data[16:20], byteorder='big', signed=True)
                nBytesHeader = 36
                if len(fileNameParts) < 4:
                    nBytesHeader = 29
                data = numpy.frombuffer(data, dtype='>f4', offset = nBytesHeader, count=-1).reshape([vFrames, nDim])[ :: , 2 :: ]
                if fileNameParts[0].lower() == "psd":
                    n = [int(data.shape[1] / 2), int(data.shape[1] / 4)]
                    temp = data[:, 0 : n[0]]
                    featureFileData["Pxy"] = temp[:, 1 : -1 : 2] + temp[:, 2 : -1 : 2] * 1j
                    featureFileData["Pxx"] = data[:, n[0] + 1 : n[0] + n[1]]
                    featureFileData["Pyy"] = data[:, n[0] + n[1] + 1 : ]                    
                else:
                    featureFileData[fileNameParts[0]] = data
        if fs != None:       
            featureFileData["fs"] = fs
        return featureFileData
    
    def removeFeature(self, featureName):
        if main.develServer:
            query = 'SELECT ID from EMA_Feature WHERE name like "%s"' % featureName
            feature = self.db.execute_query(query)
            if len(feature) > 0:
                query = 'delete from EMA_authorization where Feature_ID = "%s"' % feature[0]["id"]
                self.db.execute_query(query)
                query = 'delete from EMA_featurevalue where Feature_ID = "%s"' % feature[0]["id"]
                self.db.execute_query(query)
                query = 'delete from EMA_feature where ID = "%s"' % feature[0]["id"]
                self.db.execute_query(query)
                self.db.connection.commit()

    def run(self):
        query = "SELECT * FROM EMA_Feature"
        Features = self.db.execute_query(query)
        limit = 200
        for plugin in self.plugins:
            if len([element for element in Features if element['name'] == plugin.feature.lower()]):
                currentFeatureId = [element for element in Features if element['name'] == plugin.feature.lower()][0]["id"]
                data = None
                while data is None or len(data) > 0:
                    queryValueList = []
                    query= 'SELECT EMA_datachunk.ID as datachunkID, EMA_datachunk.subject as subject, EMA_datachunk.start as start, EMA_datachunk.end as end, EMA_datachunk.Subject as Subject, EMA_file.Filename as Filename FROM EMA_file \
                        join EMA_datachunk on EMA_file.DataChunk_id = EMA_datachunk.ID \
                        WHERE \
                            (SELECT count(EMA_featurevalue.ID) FROM EMA_featurevalue \
                            JOIN EMA_feature ON EMA_featurevalue.Feature_id = EMA_feature.ID \
                            WHERE EMA_featurevalue.DataChunk_id = EMA_datachunk.ID AND EMA_feature.Name = "%s") = 0 \
                        order by EMA_datachunk.subject, EMA_datachunk.start, EMA_datachunk.ID LIMIT %d' % (plugin.feature.lower(), limit)
                    data = self.db.execute_query(query)
                    if len(data):
                        files = []
                        lastItem = {"datachunkid": "", "subject": "", "filename": ""}
                        data.append(lastItem.copy())
                        for item in data:
                            if item["datachunkid"] != lastItem["datachunkid"] and len(files) > 0:
                                previousFeatures = {}
                                for feature in Features:
                                    query = 'SELECT EMA_featurevalue.Start as start, EMA_featurevalue.End as end, EMA_featurevalue.Side as Side, EMA_featurevalue.Value as value, EMA_featurevalue.isValid as isValid FROM EMA_featurevalue \
                                        join EMA_feature on EMA_featurevalue.Feature_id = EMA_feature.ID \
                                        WHERE EMA_feature.name = "%s" AND EMA_featurevalue.DataChunk_id = "%s" \
                                        ORDER by EMA_featurevalue.Start' % (feature['name'].lower(), lastItem["datachunkid"])
                                    temp = self.db.execute_query(query)
                                    if len(temp):
                                        previousFeatures[feature['name'].lower()] = temp
                                values = currentPlugin.process(datetime.datetime.strptime(lastItem["start"], '%Y-%m-%d %H:%M:%S'), datetime.datetime.strptime(lastItem["end"], '%Y-%m-%d %H:%M:%S'), {**previousFeatures, **self.loadFeatureFileData(files)})
                                for value in values:
                                    queryValueList.append('("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")' % (str(uuid.uuid4()), lastItem["datachunkid"], currentFeatureId, value["start"], value["end"], value["side"], value["value"], value["isvalid"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                files = []
                            if item["subject"] != lastItem["subject"]:
                                currentPlugin = plugin()
                            lastItem = item
                            files.append(os.path.join("FeatureFiles", item["subject"], item["filename"]))
                    if len(queryValueList):
                        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        query = 'INSERT INTO EMA_featurevalue (ID, DataChunk_Id, Feature_Id, Start, End, Side, Value, isValid, LastUpdate) VALUES ' + ','.join(queryValueList)
                        self.db.execute_query(query)
        self.db.connection.commit()

if __name__ == "__main__":
    featureService = FeatureService()
    featureService.removeFeature("testFeature")
    #featureService.run()