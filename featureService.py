import os
import uuid
import sys
import main
import numpy
import inspect
import datetime
from olMEGA_DataService_Server.dataConnectors import databaseConnector
from random import randint
import struct
import glob
import time

class FeatureService():

    def __init__(self):
        self.ValidationPlugins = []
        self.FeaturePlugins = []
        self.db = databaseConnector()
        query = "Select * FROM EMA_usergroup"
        usergroups = self.db.execute_query(query)
        for file in os.listdir("ValidationPlugins"):
            if file.endswith(".py"):
                imported_module = __import__("ValidationPlugins.%s" % file.replace(".py", ""))
                for name, module in inspect.getmembers(imported_module):
                    if not name.startswith("__"):
                        for name, plugin in inspect.getmembers(module):
                            if not name.startswith("__") and hasattr(plugin, "isActive") and plugin.isActive:
                                self.ValidationPlugins.append(plugin)
        for file in os.listdir("FeaturePlugins"):
            if file.endswith(".py"):
                imported_module = __import__("FeaturePlugins.%s" % file.replace(".py", ""))
                for name, module in inspect.getmembers(imported_module):
                    if not name.startswith("__"):
                        for name, plugin in inspect.getmembers(module):
                            if not name.startswith("__") and hasattr(plugin, "feature") and hasattr(plugin, "description") and hasattr(plugin, "isActive"):
                                self.FeaturePlugins.append(plugin)
                                if plugin.storeAsFeatureFile == False:                                        
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
                                elif plugin.storeAsFeatureFile == True:
                                    plugin.feature = plugin.feature.replace("_", "")
                                    query = 'SELECT * FROM EMA_filetype WHERE FileExtension = "%s"' % plugin.feature.lower()
                                    FeatureFileTypes = self.db.execute_query(query)
                                    if len(FeatureFileTypes) == 0:
                                        FeatureFileTypesId = str(uuid.uuid4())
                                        query = 'INSERT INTO EMA_filetype (ID, FileExtension) VALUES ("%s", "%s")' % (FeatureFileTypesId, plugin.feature.lower())
                                        self.db.execute_query(query)
        self.db.connection.commit()
        
    def loadFeatureFileData(self, filenames):
        featureFileData = {}
        fs = None
        for file in filenames:
            fileNameParts = os.path.basename(file).split("_")
            if len(fileNameParts) > 1:
                if os.path.isfile(file):
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
                    hasDataModified = False
                    for plugin in self.FeaturePlugins:
                        if plugin.feature.lower() == fileNameParts[0].lower():
                            try:                                
                                featureFileData[fileNameParts[0]] = plugin().modifieData(data)
                                hasDataModified = True
                            except:
                                print(sys.exc_info()[1])
                                featureFileData[fileNameParts[0]] = data
                            break;
                    if hasDataModified == False:
                        featureFileData[fileNameParts[0]] = data
                    """
                    if fileNameParts[0].lower()== "Coherence":
                        featureFileData["Coherence"] = data[:, 1 : -1 : 2] + temp[:, 2 : -1 : 2] * 1j
                    if fileNameParts[0].lower() == "psd":
                        n = [int(data.shape[1] / 2), int(data.shape[1] / 4)]
                        temp = data[:, 0 : n[0]]
                        featureFileData["Pxy"] = temp[:, 1 : -1 : 2] + temp[:, 2 : -1 : 2] * 1j
                        featureFileData["Pxx"] = data[:, n[0] + 1 : n[0] + n[1]]
                        featureFileData["Pyy"] = data[:, n[0] + n[1] + 1 : ]                    
                    else:
                        featureFileData[fileNameParts[0]] = data
                    """
                else:
                    pass
                    #print (file)
        if fs != None:       
            featureFileData["fs"] = fs
        return featureFileData
    
    def removeFeature(self, featureName):
        if main.develServer:
            query = 'SELECT ID from EMA_Feature WHERE name like "%s"' % featureName.lower()
            feature = self.db.execute_query(query)
            if len(feature) > 0:
                query = 'delete from EMA_authorization where Feature_ID = "%s"' % feature[0]["id"]
                self.db.execute_query(query)
                query = 'delete from EMA_featurevalue where Feature_ID = "%s"' % feature[0]["id"]
                self.db.execute_query(query)
                query = 'delete from EMA_feature where ID = "%s"' % feature[0]["id"]
                self.db.execute_query(query)
                self.db.connection.commit()
            query = 'SELECT ID from EMA_filetype WHERE FileExtension = "%s"' % featureName.lower().replace("_", "")
            featurefile = self.db.execute_query(query)
            if len(featurefile) > 0:
                query = 'delete from EMA_file where FileType_ID = "%s"' % featurefile[0]["id"]
                self.db.execute_query(query)
                query = 'delete from EMA_filetype where ID = "%s"' % featurefile[0]["id"]
                self.db.execute_query(query)
                self.db.connection.commit()
            files = glob.glob(os.path.join('FeatureFiles', '**', '%s*.feat' % (featureName.lower().replace("_", ""))), recursive=True)
            for f in files:
                os.remove(f)                

    def run(self):
        def getPreviousFeatures(Features, datachunkId):
            previousFeatures = {}
            for feature in Features:
                query = 'SELECT EMA_featurevalue.Start as start, EMA_featurevalue.End as end, EMA_featurevalue.Side as Side, EMA_featurevalue.Value as value, EMA_featurevalue.isValid as isValid FROM EMA_featurevalue \
                    join EMA_feature on EMA_featurevalue.Feature_id = EMA_feature.ID \
                    WHERE EMA_feature.name = "%s" AND EMA_featurevalue.DataChunk_id = "%s" \
                    ORDER by EMA_featurevalue.Start' % (feature['name'].lower(), datachunkId)
                temp = self.db.execute_query(query)
                if len(temp):
                    previousFeatures[feature['name'].lower()] = temp
            return previousFeatures

        limit = 500
        query = "SELECT * FROM EMA_Feature"
        Features = self.db.execute_query(query)
        query = "SELECT *, fileextension as name FROM EMA_filetype"
        Filetypes = self.db.execute_query(query)
        
        for plugin in self.ValidationPlugins:
            currentPlugin = plugin()
            for table in ["EMA_featurevalue", "EMA_file"]:
                if table == "EMA_featurevalue":
                    subTable = Features
                elif table == "EMA_file":
                    subTable = Filetypes
                for feature in subTable:
                    data = None
                    lastDatachunkId = ""
                    lastId = ""
                    while data is None or len(data) > 0:
                        self.db.resetTimer()
                        queryValueList = [[], [], []]
                        if table == "EMA_featurevalue":
                            query = 'SELECT EMA_datachunk.ID as datachunkID, EMA_datachunk.subject as subject, EMA_datachunk.start as start, EMA_datachunk.end as end, EMA_featurevalue.* FROM EMA_featurevalue \
                                JOIN EMA_datachunk ON EMA_featurevalue.DataChunk_id = EMA_datachunk.ID \
                                WHERE isValid = 0 AND Feature_Id = "%s" AND (EMA_datachunk.ID || EMA_featurevalue.ID) > "%s%s" ORDER BY (EMA_datachunk.ID || EMA_featurevalue.ID) LIMIT %d' % (feature["id"], lastDatachunkId, lastId, limit)
                        elif table == "EMA_file":
                            query = 'SELECT EMA_datachunk.ID as datachunkID, EMA_datachunk.subject as subject, EMA_datachunk.start as start, EMA_datachunk.end as end, EMA_file.* FROM EMA_file \
                                JOIN EMA_datachunk ON EMA_file.DataChunk_id = EMA_datachunk.ID \
                                WHERE isValid = 0 AND FileType_Id = "%s" AND (EMA_datachunk.ID || EMA_file.ID) > "%s%s" ORDER BY (EMA_datachunk.ID || EMA_file.ID) LIMIT %d' % (feature["id"], lastDatachunkId, lastId, limit)
                        data = self.db.execute_query(query)
                        for item in data:
                            if item["datachunkid"] != lastDatachunkId:
                                previousFeatures = getPreviousFeatures(Features, item["datachunkid"])
                                query = 'SELECT * FROM EMA_file WHERE datachunk_id = "%s"' % item["datachunkid"]
                                files = []
                                for file in self.db.execute_query(query):
                                    files.append(os.path.join("FeatureFiles", item["subject"], file["filename"]))
                                previousFeatures = {**previousFeatures, **self.loadFeatureFileData(files)}
                                lastDatachunkId = item["datachunkid"]
                            try:
                                isValid = currentPlugin.process(feature["name"], item, previousFeatures)
                                if isValid.value != item["isvalid"]:
                                    queryValueList[isValid.value + 1].append('ID = "%s"' % (item["id"]))
                            except:
                                pass
                            lastId = item["id"]
                            
                        for idx in range(len(queryValueList)):
                            if (len(queryValueList[idx])) > 0:
                                query = 'UPDATE %s SET isValid = %d, LastUpdate = "%s" WHERE %s' % (table, idx - 1, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), " or ".join(queryValueList[idx]))
                                self.db.execute_query(query)
                                self.db.connection.commit()
                                
                        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
        
        for plugin in self.FeaturePlugins:
            if plugin.isActive:
                lastRow = ""
                if plugin.storeAsFeatureFile == False and len([element for element in Features if element['name'] == plugin.feature.lower()]):
                    currentFeatureId = [element for element in Features if element['name'] == plugin.feature.lower()][0]["id"]
                    data = None
                    while data is None or len(data) > 0:
                        self.db.resetTimer()
                        queryValueList = []
                        query = 'SELECT EMA_datachunk.ID as datachunkID, EMA_datachunk.subject as subject, EMA_datachunk.start as start, EMA_datachunk.end as end, EMA_file.Filename as Filename FROM EMA_file \
                            join EMA_datachunk on EMA_file.DataChunk_id = EMA_datachunk.ID \
                            WHERE \
                                (SELECT count(EMA_featurevalue.ID) FROM EMA_featurevalue \
                                JOIN EMA_feature ON EMA_featurevalue.Feature_id = EMA_feature.ID \
                                WHERE EMA_featurevalue.DataChunk_id = EMA_datachunk.ID AND EMA_feature.Name = "%s") = 0 \
                            AND EMA_datachunk.subject || EMA_datachunk.start || EMA_datachunk.ID > "%s" \
                            order by EMA_datachunk.subject || EMA_datachunk.start || EMA_datachunk.ID LIMIT %d' % (plugin.feature.lower(), lastRow, limit)
                        data = self.db.execute_query(query)
                        if len(data):
                            files = []
                            lastItem = {"datachunkid": "", "subject": "", "filename": ""}
                            if len(data) < limit:
                                data.append(lastItem.copy())
                            for item in data:
                                if "start" in item:
                                    lastRow = item["subject"] + item["start"] + item["datachunkid"]
                                if item["datachunkid"] != lastItem["datachunkid"] and len(files) > 0:
                                    previousFeatures = getPreviousFeatures(Features, lastItem["datachunkid"])
                                    try:
                                        values = currentPlugin.process(datetime.datetime.strptime(lastItem["start"], '%Y-%m-%d %H:%M:%S'), datetime.datetime.strptime(lastItem["end"], '%Y-%m-%d %H:%M:%S'), {**previousFeatures, **self.loadFeatureFileData(files)})
                                        for value in values:
                                            if type(value) is dict and "start" in value and "end" in value and "value" in value and "side" in value and "isvalid" in value:
                                                queryValueList.append('("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")' % (str(uuid.uuid4()), lastItem["datachunkid"], currentFeatureId, value["start"], value["end"], value["side"], value["value"], value["isvalid"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                    except:
                                        pass
                                    files = []
                                if item["subject"] != lastItem["subject"]:
                                    currentPlugin = plugin()
                                lastItem = item
                                files.append(os.path.join("FeatureFiles", item["subject"], item["filename"]))
                        if len(queryValueList):
                            print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            query = 'INSERT INTO EMA_featurevalue (ID, DataChunk_Id, Feature_Id, Start, End, Side, Value, isValid, LastUpdate) VALUES ' + ','.join(queryValueList)
                            self.db.execute_query(query)
                elif plugin.storeAsFeatureFile == True  and len([element for element in Filetypes if element['fileextension'] == plugin.feature.lower()]):
                    currentFiletypeId = [element for element in Filetypes if element['fileextension'] == plugin.feature.lower()][0]["id"]
                    data = None
                    while data is None or len(data) > 0:
                        self.db.resetTimer()
                        queryFileList = []
                        query= 'SELECT EMA_datachunk.ID as datachunkID, EMA_datachunk.subject as subject, EMA_datachunk.start as start, EMA_datachunk.end as end, EMA_file.Filename as Filename FROM EMA_file \
                            join EMA_datachunk on EMA_file.DataChunk_id = EMA_datachunk.ID \
                            WHERE \
                                (SELECT count(EMA_file.ID) FROM EMA_file \
                                JOIN EMA_filetype ON EMA_file.FileType_id = EMA_filetype.ID \
                                WHERE EMA_file.DataChunk_id = EMA_datachunk.ID AND EMA_filetype.FileExtension = "%s") = 0 \
                            AND EMA_datachunk.subject || EMA_datachunk.start || EMA_datachunk.ID > "%s" \
                            order by EMA_datachunk.subject || EMA_datachunk.start || EMA_datachunk.ID LIMIT %d' % (plugin.feature.lower(), lastRow, limit)
                        data = self.db.execute_query(query)
                        if len(data):
                            files = []
                            lastItem = {"datachunkid": "", "subject": "", "filename": ""}
                            if len(data) < limt:
                                data.append(lastItem.copy())
                            for item in data:
                                if "start" in item:
                                    lastRow = item["subject"] + item["start"] + item["datachunkid"]
                                if item["datachunkid"] != lastItem["datachunkid"] and len(files) > 0:
                                    previousFeatures = getPreviousFeatures(Features, lastItem["datachunkid"])
                                    try:
                                        values = currentPlugin.process(datetime.datetime.strptime(lastItem["start"], '%Y-%m-%d %H:%M:%S'), datetime.datetime.strptime(lastItem["end"], '%Y-%m-%d %H:%M:%S'), {**previousFeatures, **self.loadFeatureFileData(files)})
                                        for value in values:
                                            if type(value) is dict and "value" in value and "start" in value and "end" in value and "isvalid" in value:
                                                start = time.time()
                                                filename = plugin.feature.lower() + "_" + str(randint(100000, 999999)) + "_" + value["start"].strftime('%Y%m%d_%H%M%S%f')[:-3] + ".feat"
                                                if value["value"].dtype == 'complex64':
                                                    temp = numpy.zeros([value["value"].shape[0], value["value"].shape[1] * 2])
                                                    temp[:, 0::2] = numpy.real(value["value"])
                                                    temp[:, 1::2] = numpy.imag(value["value"])
                                                    value["value"] = temp
                                                
                                                header = bytearray()
                                                header += value["value"].shape[0].to_bytes(4, "big")
                                                header += (value["value"].shape[1] + 2).to_bytes(4, "big")
                                                header += value["FrameSizeInSamples"].to_bytes(4, "big")
                                                header += value["HopSizeInSamples"].to_bytes(4, "big")
                                                header += value["fs"].to_bytes(4, "big")
                                                header += bytearray(value["BlockTime"], "utf-8")
                                                if len(header) != 36:
                                                    print ("Warning: Header has wrong len, File not saved!")
                                                else:
                                                    content = bytearray()
                                                    for val in numpy.concatenate((numpy.zeros([value["value"].shape[0], 2]),  value["value"]), axis = 1).flatten():
                                                        content += bytearray(struct.pack(">f", val))
                                                    with open(os.path.join("FeatureFiles", lastItem["subject"], filename), mode='wb') as filewriter:
                                                        filewriter.write(header)
                                                        filewriter.write(content)
                                                    print("Duration: ", time.time() - start)
                                                    queryFileList.append('("%s", "%s", "%s", "%s", "%s", "%s")' % (str(uuid.uuid4()), lastItem["datachunkid"], currentFiletypeId, filename, value["isvalid"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                    except:
                                        print(sys.exc_info()[1])
                                    files = []
                                if item["subject"] != lastItem["subject"]:
                                    currentPlugin = plugin()
                                lastItem = item
                                files.append(os.path.join("FeatureFiles", item["subject"], item["filename"]))
                        if len(queryFileList):
                            print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            query = 'INSERT INTO EMA_File (ID, DataChunk_Id, FileType_Id, Filename, isValid, LastUpdate) VALUES ' + ','.join(queryFileList)
                            self.db.execute_query(query)
                    pass
            self.db.connection.commit()

if __name__ == "__main__":
    featureService = FeatureService()
    #featureService.removeFeature("Coherence")
    featureService.run()