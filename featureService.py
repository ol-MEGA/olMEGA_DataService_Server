import os
import uuid
import main
import numpy
import inspect
import datetime
from olMEGA_DataService_Server import FeatureFile
from olMEGA_DataService_Server.dataConnectors import databaseConnector
import glob
import time
import configparser

class FeatureService():

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('settings.conf')
        self.ValidationPlugins = []
        self.FeaturePlugins = []
        self.db = databaseConnector(readlOnly=False)
        query = "Select * FROM EMA_usergroup"
        usergroups = self.db.execute_query(query, {})
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
                            if not plugin in self.FeaturePlugins and not name.startswith("__") and hasattr(plugin, "feature") and hasattr(plugin, "description") and hasattr(plugin, "isActive"):
                                if type(plugin.feature) is str:
                                    plugin.feature = [plugin.feature]
                                    plugin.description = [plugin.description]
                                self.FeaturePlugins.append(plugin)
                                if plugin.storeAsFeatureFile == False:                                        
                                    for idx in range(len(plugin.feature)):
                                        query = 'SELECT * FROM EMA_feature WHERE name like %(feature)s'
                                        Features = self.db.execute_query(query, {"feature": plugin.feature[idx].lower()})
                                        if len(Features) == 0:
                                            newFeatureId = str(uuid.uuid4())
                                            query = 'INSERT INTO EMA_feature (ID, Name, Description) VALUES (%(ID)s, %(Name)s, %(Description)s)'
                                            self.db.execute_query(query, {"ID": newFeatureId, "Name": plugin.feature[idx].lower(), "Description": plugin.description[idx]})
                                            for usergroup in usergroups:
                                                query = 'INSERT INTO EMA_authorization (ID, Feature_ID, UserGroup_ID, AllowRead, AllowWrite) VALUES (%(ID)s, %(Feature_ID)s, %(UserGroup_ID)s, %(AllowRead)s, %(AllowWrite)s)'
                                                self.db.execute_query(query, {"ID": str(uuid.uuid4()), "Feature_ID": newFeatureId, "UserGroup_ID": usergroup["id"], "AllowRead": main.develServer, "AllowWrite": 0})
                                elif plugin.storeAsFeatureFile == True:
                                    for idx in range(len(plugin.feature)):
                                        plugin.feature[idx] = plugin.feature[idx].replace("_", "")
                                        query = 'SELECT * FROM EMA_filetype WHERE FileExtension = %(FileExtension)s'
                                        FeatureFileTypes = self.db.execute_query(query, {"FileExtension": plugin.feature[idx].lower()})
                                        if len(FeatureFileTypes) == 0:
                                            FeatureFileTypesId = str(uuid.uuid4())
                                            query = 'INSERT INTO EMA_filetype (ID, FileExtension) VALUES (%(ID)s, %(FileExtension)s)'
                                            self.db.execute_query(query, {"ID": FeatureFileTypesId, "FileExtension": plugin.feature[idx].lower()})
                                        query = 'SELECT * FROM EMA_feature WHERE name like %(name)s'
                                        Features = self.db.execute_query(query, {"name": plugin.feature[idx].lower()})
                                        if len(Features) == 0:
                                            FeatureId = str(uuid.uuid4())
                                            query = 'INSERT INTO EMA_feature (ID, Name, Description) VALUES (%(ID)s, %(Name)s, %(Description)s)'
                                            self.db.execute_query(query, {"ID": FeatureId, "Name": plugin.feature[idx].lower(), "Description": plugin.description[idx]})
                                        else:
                                            FeatureId = Features[0]["id"]
                                        query = 'SELECT count(ID) FROM EMA_authorization WHERE Feature_ID = %(Feature_ID)s'
                                        Authorizations = self.db.execute_query(query, {"Feature_ID": FeatureId})
                                        if Authorizations[0]["count(id)"] == 0:
                                            for usergroup in usergroups:
                                                query = 'INSERT INTO EMA_authorization (ID, Feature_ID, UserGroup_ID, AllowRead, AllowWrite) VALUES (%(ID)s, %(Feature_ID)s, %(UserGroup_ID)s, %(AllowRead)s, %(AllowWrite)s)'
                                                self.db.execute_query(query, {"ID": str(uuid.uuid4()), "Feature_ID": FeatureId, "UserGroup_ID": usergroup["id"], "AllowRead": main.develServer, "AllowWrite": 0})
        self.db.connection.commit()
        
    def loadFeatureFileData(self, filenames):
        featureFileData = {}
        featureFiles = []
        fs = None
        for file in filenames:
            fileNameParts = os.path.basename(file).split("_")
            if len(fileNameParts) > 1:
                if os.path.isfile(file):
                    featureFiles.append(FeatureFile.load(file))
                    fs = featureFiles[-1].fs
                    hasDataModified = False
                    for plugin in self.FeaturePlugins:
                        for idx in range(len(plugin.feature)):
                            if plugin.feature[idx].lower() == fileNameParts[0].lower():
                                try:       
                                    if "modifieData" in plugin.__dict__:                         
                                        featureFileData[fileNameParts[0]] = plugin().modifieData(featureFiles[-1].data)
                                    else:
                                        featureFileData[fileNameParts[0]] = featureFiles[-1].data
                                    hasDataModified = True
                                except Exception as e:
                                    if hasattr(e, 'message'):
                                        print("Error: ", e.message)
                                    else:
                                        print("Error: ", e)
                                    featureFileData[fileNameParts[0]] = featureFiles[-1].data
                                break
                    if hasDataModified == False:
                        featureFileData[fileNameParts[0]] = featureFiles[-1].data
                else:
                    pass
        if fs != None:       
            featureFileData["fs"] = featureFiles[-1].fs
        return featureFileData, featureFiles
    
    def removeFeature(self, featureName):
        if main.develServer:
            query = 'SELECT ID from EMA_feature WHERE name like %(name)s'
            feature = self.db.execute_query(query, {"name": featureName.lower()})
            if len(feature) > 0:
                query = 'delete from EMA_authorization where Feature_ID = %(Feature_ID)s'
                self.db.execute_query(query, {"Feature_ID": feature[0]["id"]})
                query = 'delete from EMA_featurevalue where Feature_ID = %(Feature_ID)s'
                self.db.execute_query(query, {"Feature_ID": feature[0]["id"]})
                query = 'delete from EMA_feature where Name = %(Name)s'
                self.db.execute_query(query, {"Name": featureName.lower()})
                self.db.connection.commit()
            query = 'SELECT ID from EMA_filetype WHERE FileExtension = %(FileExtension)s'
            featurefile = self.db.execute_query(query, {"FileExtension": featureName.lower().replace("_", "")})
            if len(featurefile) > 0:
                query = 'delete from EMA_authorization where Feature_ID = %(Feature_ID)s'
                self.db.execute_query(query, {"Feature_ID": featurefile[0]["id"]})
                query = 'delete from EMA_file where FileType_ID = %(FileType_ID)s'
                self.db.execute_query(query, {"FileType_ID": featurefile[0]["id"]})
                query = 'delete from EMA_filetype where ID = %(ID)s'
                self.db.execute_query(query, {"ID": featurefile[0]["id"]})
                query = 'delete from EMA_feature where Name = %(Name)s'
                self.db.execute_query(query, {"Name": featureName.lower()})
                self.db.connection.commit()
            files = glob.glob(os.path.join(self.config["MAIN"]["Storage"], '**', '%s*.feat' % (featureName.lower().replace("_", ""))), recursive=True)
            for f in files:
                os.remove(f)                

    def run(self):
        def getPreviousFeatures(Features, datachunkId):
            previousFeatures = {}
            for feature in Features:
                query = 'SELECT EMA_featurevalue.Start as start, EMA_featurevalue.End as end, EMA_featurevalue.Side as Side, EMA_featurevalue.Value as value, EMA_featurevalue.isValid as isValid FROM EMA_featurevalue \
                    join EMA_feature on EMA_featurevalue.Feature_id = EMA_feature.ID \
                    WHERE EMA_feature.name = %(name)s AND EMA_featurevalue.DataChunk_id = %(DataChunk_id)s \
                    ORDER by EMA_featurevalue.Start'
                temp = self.db.execute_query(query, {"name": feature['name'].lower(), "DataChunk_id": datachunkId})
                if len(temp):
                    previousFeatures[feature['name'].lower()] = temp
            return previousFeatures

        limit = 500
        query = "SELECT * FROM EMA_feature"
        Features = self.db.execute_query(query, {})
        query = "SELECT *, fileextension as name FROM EMA_filetype"
        Filetypes = self.db.execute_query(query, {})
        
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
                                WHERE isValid = 0 AND Feature_Id = %(Feature_Id)s AND (EMA_datachunk.ID || EMA_featurevalue.ID) > %(IDs)s ORDER BY (EMA_datachunk.ID || EMA_featurevalue.ID) LIMIT %(limit)s'
                        elif table == "EMA_file":
                            query = 'SELECT EMA_datachunk.ID as datachunkID, EMA_datachunk.subject as subject, EMA_datachunk.start as start, EMA_datachunk.end as end, EMA_file.* FROM EMA_file \
                                JOIN EMA_datachunk ON EMA_file.DataChunk_id = EMA_datachunk.ID \
                                WHERE isValid = 0 AND FileType_Id = %(Feature_Id)s AND (EMA_datachunk.ID || EMA_file.ID) > %(IDs)s ORDER BY (EMA_datachunk.ID || EMA_file.ID) LIMIT %(limit)s'
                        data = self.db.execute_query(query, {"Feature_Id": feature["id"], "IDs": lastDatachunkId + lastId, "limit": limit})
                        for item in data:
                            if item["datachunkid"] != lastDatachunkId:
                                previousFeatures = getPreviousFeatures(Features, item["datachunkid"])
                                query = 'SELECT * FROM EMA_file WHERE datachunk_id = %(datachunk_id)s'
                                files = []
                                for file in self.db.execute_query(query, {"datachunk_id": item["datachunkid"]}):
                                    files.append(os.path.join(self.config["MAIN"]["Storage"], item["subject"], file["filename"]))
                                featureFileData, featureFiles = self.loadFeatureFileData(files)
                                previousFeatures = {**previousFeatures, **featureFileData}
                                lastDatachunkId = item["datachunkid"]
                            try:
                                isValid = currentPlugin.process(feature["name"], item, previousFeatures)
                                if isValid.value != item["isvalid"]:
                                    queryValueList[isValid.value + 1].append(["ID=%(ID" + str(len(queryValueList[isValid.value + 1])) + ")s", {"ID" + str(len(queryValueList[isValid.value + 1])): item["id"]}])
                            except Exception as e:
                                if hasattr(e, 'message'):
                                    print("Error: ", e.message)
                                else:
                                    print("Error: ", e)
                            lastId = item["id"]
                            
                        for idx in range(len(queryValueList)):
                            if (len(queryValueList[idx])) > 0:
                                query = ('UPDATE {} SET isValid = %(isValid)s, LastUpdate = %(LastUpdate)s WHERE ' + " or ".join([i[0] for i in queryValueList[idx]])).format(table)
                                values = {"isValid": idx - 1, "LastUpdate": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                                tmp = {values.update(i[1]) for i in queryValueList[idx]}
                                self.db.execute_query(query, values)
                                self.db.connection.commit()
                        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        for plugin in self.FeaturePlugins:
            if plugin.isActive:
                lastRow = ""
                if plugin.storeAsFeatureFile == False and len([element for element in Features if element['name'] in [x.lower() for x in plugin.feature]]):
                    data = None
                    while data is None or len(data) > 0:
                        self.db.resetTimer()
                         
                        queryValueList = []
                        query = 'SELECT EMA_datachunk.ID as datachunkID, EMA_datachunk.subject as subject, EMA_datachunk.start as start, EMA_datachunk.end as end, EMA_file.Filename as Filename FROM EMA_file \
                            join EMA_datachunk on EMA_file.DataChunk_id = EMA_datachunk.ID \
                            WHERE \
                                (SELECT count(EMA_featurevalue.ID) FROM EMA_featurevalue \
                                JOIN EMA_feature ON EMA_featurevalue.Feature_id = EMA_feature.ID \
                                WHERE EMA_featurevalue.DataChunk_id = EMA_datachunk.ID AND EMA_feature.Name in (' + ",".join("%(Name" + str(x) + ")s" for x in range(len(plugin.feature))) + ')) = 0 \
                            AND EMA_datachunk.subject || EMA_datachunk.start || EMA_datachunk.ID > %(ID)s \
                            order by EMA_datachunk.subject || EMA_datachunk.start || EMA_datachunk.ID LIMIT %(limit)s'
                        values = {"Name" + str(idx): plugin.feature[idx].lower() for idx in range(len(plugin.feature))}
                        values.update({"ID": lastRow, "limit": limit})
                        data = self.db.execute_query(query, values)
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
                                        featureFileData, featureFiles = self.loadFeatureFileData(files)
                                        values = currentPlugin.process(datetime.datetime.strptime(lastItem["start"], '%Y-%m-%d %H:%M:%S'), datetime.datetime.strptime(lastItem["end"], '%Y-%m-%d %H:%M:%S'), {**previousFeatures, **featureFileData})
                                        if values:
                                            if not type(values) is tuple:
                                                values = tuple([values])
                                            if len(currentPlugin.feature) == len(values):
                                                for idx in range(len(currentPlugin.feature)):
                                                    currentFeatureId = [element for element in Features if element['name'] == plugin.feature[idx].lower()][0]["id"]
                                                    for value in values[idx]:
                                                        if type(value) is dict and "start" in value and "end" in value and "value" in value and "side" in value and "isvalid" in value:
                                                            queryValueList.append('("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")' % (str(uuid.uuid4()), lastItem["datachunkid"], currentFeatureId, value["start"], value["end"], value["side"], value["value"], value["isvalid"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                            elif not hasattr(currentPlugin, "warning_number_of_features_not_correct"):
                                                currentPlugin.warning_number_of_features_not_correct = True
                                                print("\33[31mWarning: Number of Features not equal return values in ", type(currentPlugin), "\33[0m")
                                    except Exception as e:
                                        if hasattr(e, 'message'):
                                            print(e.message)
                                        else:
                                            print(e)
                                    files = []
                                if item["subject"] != lastItem["subject"]:
                                    currentPlugin = plugin()
                                lastItem = item
                                files.append(os.path.join(self.config["MAIN"]["Storage"], item["subject"], item["filename"]))
                        if len(queryValueList):
                            print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            query = 'INSERT INTO EMA_featurevalue (ID, DataChunk_Id, Feature_Id, Start, End, Side, Value, isValid, LastUpdate) VALUES ' + ','.join(queryValueList)
                            self.db.execute_query(query, {})
                elif plugin.storeAsFeatureFile == True  and len([element for element in Filetypes if element['fileextension'] in [x.lower() for x in plugin.feature]]):
                    data = None
                    while data is None or len(data) > 0:
                        self.db.resetTimer()
                        queryFileList = []
                        query= 'SELECT EMA_datachunk.ID as datachunkID, EMA_datachunk.subject as subject, EMA_datachunk.start as start, EMA_datachunk.end as end, EMA_file.Filename as Filename FROM EMA_file \
                            join EMA_datachunk on EMA_file.DataChunk_id = EMA_datachunk.ID \
                            WHERE \
                                (SELECT count(EMA_file.ID) FROM EMA_file \
                                JOIN EMA_filetype ON EMA_file.FileType_id = EMA_filetype.ID \
                                WHERE EMA_file.DataChunk_id = EMA_datachunk.ID AND EMA_filetype.FileExtension in (' + ",".join("%(FileExtension" + str(x) + ")s" for x in range(len(plugin.feature))) + ')) = 0 \
                            AND EMA_datachunk.subject || EMA_datachunk.start || EMA_datachunk.ID > %(ID)s \
                            order by EMA_datachunk.subject || EMA_datachunk.start || EMA_datachunk.ID LIMIT %(limit)s'
                        values = {"FileExtension" + str(idx): plugin.feature[idx].lower() for idx in range(len(plugin.feature))}
                        values.update({"ID": lastRow, "limit": limit})
                        data = self.db.execute_query(query, values)
                        start = time.time()
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
                                        featureFileData, featureFiles = self.loadFeatureFileData(files)
                                        if len(featureFiles):
                                            values = currentPlugin.process(datetime.datetime.strptime(lastItem["start"], '%Y-%m-%d %H:%M:%S'), datetime.datetime.strptime(lastItem["end"], '%Y-%m-%d %H:%M:%S'), {**previousFeatures, **featureFileData})
                                            if values:
                                                if not type(values) is tuple:
                                                    values = tuple([values])
                                                if len(currentPlugin.feature) == len(values):
                                                    for idx in range(len(currentPlugin.feature)):
                                                        currentFiletypeId = [element for element in Filetypes if element['fileextension'] == currentPlugin.feature[idx].lower()][0]["id"]
                                                        for value in values[idx]:
                                                            if type(value) is dict and "value" in value and "start" in value and "end" in value and "isvalid" in value:
                                                                if "fs" in value and not hasattr(currentPlugin, "warning_fs_is_deprecated"):
                                                                    currentPlugin.warning_fs_is_deprecated = True
                                                                    print("\33[31mWarning: Returning 'fs' is deprecated and will be ignored in", type(currentPlugin), "\33[0m")
                                                                filename = plugin.feature[idx].lower() + "_" + value["start"].strftime('%Y%m%d_%H%M%S%f')[:-3] + ".feat"
                                                                if str(value["value"].dtype).startswith('complex'):
                                                                    temp = numpy.zeros([value["value"].shape[0], value["value"].shape[1] * 2])
                                                                    temp[:, 0::2] = numpy.real(value["value"])
                                                                    temp[:, 1::2] = numpy.imag(value["value"])
                                                                    value["value"] = temp
                                                                featureFile = FeatureFile.FeatureFile()
                                                                featureFile.nFrames = value["value"].shape[0]
                                                                featureFile.nDimensions = value["value"].shape[1]
                                                                featureFile.FrameSizeInSamples = value["FrameSizeInSamples"]
                                                                featureFile.HopSizeInSamples = value["HopSizeInSamples"]
                                                                featureFile.mBlockTime = value["BlockTime"]
                                                                featureFile.SystemTime = featureFile.mBlockTime
                                                                featureFile.fs = featureFiles[0].fs
                                                                featureFile.calibrationInDb = featureFiles[0].calibrationInDb.copy()
                                                                featureFile.AndroidID = featureFiles[0].AndroidID
                                                                featureFile.BluetoothTransmitterMAC = featureFiles[0].BluetoothTransmitterMAC
                                                                if featureFiles[0].mBlockTime == featureFile.mBlockTime:
                                                                    featureFile.SystemTime = featureFiles[0].SystemTime
                                                                featureFile.data = value["value"]
                                                                FeatureFile.save(featureFile, os.path.join(self.config["MAIN"]["Storage"], lastItem["subject"], filename), True)
                                                                queryFileList.append('("%s", "%s", "%s", "%s", "%s", "%s")' % (str(uuid.uuid4()), lastItem["datachunkid"], currentFiletypeId, filename, value["isvalid"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                                elif not hasattr(currentPlugin, "warning_number_of_features_not_correct"):
                                                    currentPlugin.warning_number_of_features_not_correct = True
                                                    print("\33[31mWarning: Number of Features not equal return values for ", currentPlugin, "\33[0m")
                                    except Exception as e:
                                        if hasattr(e, 'message'):
                                            print("Error: ", e.message)
                                        else:
                                            print("Error: ", e)
                                    files = []
                                if item["subject"] != lastItem["subject"]:
                                    currentPlugin = plugin()
                                lastItem = item
                                files.append(os.path.join(self.config["MAIN"]["Storage"], item["subject"], item["filename"]))
                        if len(queryFileList):
                            print("Duration for ", len(data), " Datarows: \t", time.time() - start)
                            query = 'INSERT INTO EMA_File (ID, DataChunk_Id, FileType_Id, Filename, isValid, LastUpdate) VALUES ' + ','.join(queryFileList)
                            self.db.execute_query(query, {})
                    pass
            self.db.connection.commit()

if __name__ == "__main__":
    featureService = FeatureService()
    #featureService.removeFeature("Coherence")
    #featureService.removeFeature("testFeature")
    #featureService.removeFeature("testFeature1")
    #featureService.removeFeature("testFeature2")
    featureService.run()