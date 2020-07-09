import sqlite3
import copy
import datetime
import os
import xml.etree.ElementTree as ET
from dateutil.parser import parse
import mysql.connector as mysql
import time

def validate(date_text):
    try:
        parse(str(date_text))
        return True
    except ValueError:
        return False
    
def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class databaseConnector(object):
    def __init__(self, dbType = "mySQL", timeout = 60 * 5):
        self.db = dbType
        #self.db = "sqlite3"
        if self.db == "mySQL":
            self.connection = mysql.connect(
                host = "localhost",
                user = "djangouser",
                passwd = "mypassword",
                database = "django_db"
            )
            self.cursor = self.connection.cursor(dictionary=True, buffered=False)
        elif self.db == "sqlite3":
            if str(self.getDatabasePath()) == "":
                raise FileNotFoundError
            self.connection = sqlite3.connect(self.getDatabasePath())
            self.connection.row_factory = dict_factory
            self.cursor = self.connection.cursor()
        self.startTime = time.time()
        self.printQuery = False
        self.timeout = timeout
        
    def getDatabasePath(self):
        if os.path.isfile("../IhaWebServices/db.sqlite3"): 
            return "../IhaWebServices/db.sqlite3"
        elif os.path.isfile("db.sqlite3"): 
            return "db.sqlite3"
        elif os.path.isfile("../db.sqlite3"): 
            return "../db.sqlite3"
        else:
            return ""

    def execute_query(self, query):
        if time.time() - self.startTime > self.timeout:
            raise TimeoutError
        if not query.endswith(";"):
            query += ";"
        if self.printQuery:
            print(query);
        self.cursor.execute(query)
        if self.db == "mySQL":
            pass
        elif self.db == "sqlite3":
            self.connection.commit()
        if query.lower().startswith("select ") or query.lower().startswith("show ") or query.lower().startswith("pragma "):
            data = self.cursor.fetchall()
            if type(data) is list:
                for idx in range(len(data)):
                    data[idx] = {k.lower(): v for k, v in data[idx].items()} 
            return data
    
    def close(self):
        if self.connection.is_connected():
            self.connection.commit()
            self.connection.close()
        pass

class dataConnector(object):
    def __init__(self, dataTables, forbiddenTables, UserRights, returnRawTable = False, timeout = 60 * 10):
        self.FeatureFilesFolder = "FeatureFiles"
        self.lastDataset = None
        self.database = databaseConnector(timeout = timeout)
        self.dataTables = dataTables
        self.forbiddenTables = forbiddenTables
        self.returnRawTable = returnRawTable        
        self.UserRights = UserRights
        if not os.path.isdir(self.FeatureFilesFolder):
            os.makedirs(self.FeatureFilesFolder)
    
    def close(self):
        self.database.close()
        del self.database

    def isFlatCondtitions(self, conditions):
        if (conditions):
            for item in conditions.keys():
                if type(conditions[item]) is list or type(conditions[item]) is dict:
                    return False
        return True
    
    def expandFlatCondtitions(self, flatConditions, table):
        if (flatConditions):
            newConditions = {}
            if flatConditions:
                for childTable in table.childTables:
                    newConditions.update(self.expandFlatCondtitions(flatConditions, childTable))
                for field in table.fields:
                    if field[0] in flatConditions and not (table.name == "file" and flatConditions[field[0]].find(".feat") < 0 or table.name == "questionnaire" and flatConditions[field[0]].find(".xml") < 0):
                        newConditions[field[0]] = flatConditions[field[0]]
                for field in flatConditions:        
                    for parentTable in table.parentTables:
                        if field in [item[0] for item in parentTable.fields]:
                            if not parentTable.name in newConditions.keys():
                                newConditions[parentTable.name] = {}
                            newConditions[parentTable.name][field] = flatConditions[field]
                            #newConditions[field] = flatConditions[field]
                for count in reversed(range(len(flatConditions))):
                    field = list(flatConditions.keys())[count]
                    if not field in [item[0] for item in table.fields]:
                        del flatConditions[field]
                if len(newConditions):
                    return {table.name: newConditions}
        return {}


    def getDataSet(self, tableName, conditions = False, originalId = False):
        
        def createCopyWithoutIDs(forbiddenTables, UserRights, data):
            if type(data) is dict:
                for item in [item for item  in list(data) if type(data[item]) is list]:
                    if item in forbiddenTables:
                        del data[item]
                    else:
                        createCopyWithoutIDs(forbiddenTables, UserRights, data[item])
                if "id" in data.keys():
                    data["id"] = data["hash"]
                    del data["hash"]
                for item in [x for x in data.keys() if x[-3:] == "_id"]:
                    del data[item]
            elif type(data) is list:
                for idx in [idx for idx in reversed(range(len(data))) if type(data[idx]) is dict]:
                    if "feature_id" in data[idx].keys() and (len([row["allowread"] for row in UserRights["authorization"] if row["feature_id"] == data[idx]["feature_id"]]) == 0 or [row["allowread"] for row in UserRights["authorization"] if row["feature_id"] == data[idx]["feature_id"]][0] == 0):
                        del data[idx]
                    else:
                        createCopyWithoutIDs(forbiddenTables, UserRights, data[idx])
        tableName = tableName.lower()
        conditions = self.dictKeysToLower(conditions)
        
        self.dataTables[tableName].forbiddenTables = self.forbiddenTables
        if self.returnRawTable == True:
            return self.dictKeysToLower({tableName : self.dataTables[tableName].getDataSet(self.database, conditions)})
        elif hasattr(self, "UserRights") and type(self.UserRights) is dict and self.UserRights["user"]["isactive"] and tableName in self.dataTables.keys():
            self.lastDataset = self.dictKeysToLower({tableName : self.dataTables[tableName].getDataSet(self.database, conditions)})
            returnDataset = copy.deepcopy(self.lastDataset)
            if originalId == False:
                createCopyWithoutIDs(self.forbiddenTables, self.UserRights, returnDataset)
            return returnDataset[tableName]
        return False
    
    def exists(self, tableName, conditions = False):
        tableName = tableName.lower()
        if tableName == "file" and "file" in conditions.keys() and "subject" in conditions["file"].keys() and "filename" in conditions["file"].keys():
            return os.path.isfile(os.path.join(self.FeatureFilesFolder, conditions["file"]["subject"], conditions["file"]["filename"]))
        conditions = self.dictKeysToLower(conditions)
        self.dataTables[tableName].forbiddenTables = self.forbiddenTables
        return self.dataTables[tableName].exists(self.database, conditions)
    
    def getDataSQL(self, table, where = "", limit = ""):
        self.dataTables[table].forbiddenTables = self.forbiddenTables
        strSql = "SELECT " + ", ".join(self.dataTables[table].SQL["allfields"]) + " FROM " + self.dataTables[table].prefix + table + " "
        tmp = self.dataTables[table].SQL["join"];
        tmp.reverse()
        strSql += " ".join(tmp)
        if where != "":
            strSql += " WHERE " + where
        if limit != "":
            strSql += " LIMIT " + limit
        return self.database.execute_query(strSql)
        #print (strSql)

    def updateDataSet(self, dataset, lastDataset = None, internalCall = False):
        def removeForbiddenTables(forbiddenTables, UserRights, data, origData):
            if type(data) is dict:
                for item in [item for item  in list(data) if type(data[item]) is list]:
                    if item in forbiddenTables:
                        del data[item]
                        if item in origData.keys():
                            del origData[item]
                    elif item in origData.keys():
                        removeForbiddenTables(forbiddenTables, UserRights, data[item], origData[item])
            elif type(data) is list:
                for idx in [idx for idx in reversed(range(len(data))) if type(data[idx]) is dict]:
                    origRow = {}
                    if "id" in data[idx] and data[idx]["id"] == "":
                        del data[idx]["id"]
                    for tmpRow in origData:
                        if "id" in tmpRow.keys() and "id" in data[idx] and tmpRow["hash"] == data[idx]["id"]:
                            origRow = tmpRow
                    if "feature_id" in origRow.keys() and (len([row["allowwrite"] for row in UserRights["authorization"] if row["feature_id"] == origRow["feature_id"]]) == 0 or [row["allowwrite"] for row in UserRights["authorization"] if row["feature_id"] == origRow["feature_id"]][0] == 0):
                        del data[idx]
                    elif "id" in data[idx].keys() and data[idx]["id"] != "" and "hash" in origRow.keys() and data[idx]["id"] == origRow["hash"]:
                        removeForbiddenTables(forbiddenTables, UserRights, data[idx], origRow)
        dataset = self.dictKeysToLower(dataset)
        if type(dataset) is list and type(lastDataset) is dict:
            dataset = {list(lastDataset.keys())[0] : dataset}
        if lastDataset and hasattr(self, "UserRights") and type(self.UserRights) is dict and self.UserRights["user"]["isactive"]:
            lastDataset = self.dictKeysToLower(lastDataset) 
            if internalCall:
                removeForbiddenTables([], self.UserRights, dataset, lastDataset)
            else:
                removeForbiddenTables(self.forbiddenTables + ["file", "feature", "question", "filetype"], self.UserRights, dataset, lastDataset)
            self.dataTables[list(dataset.keys())[0]].forbiddenTables = self.forbiddenTables
            self.dataTables[list(dataset.keys())[0]].updateDataSet(self.database, dataset, lastDataset)
            lastDataset = None
            return list(dataset.keys())[0]
    
    def insertDataSet(self, tableName, dataset):
        tableName = tableName.lower()
        dataset = self.dictKeysToLower(dataset)
        if hasattr(self, "UserRights") and type(self.UserRights) is dict and self.UserRights["user"]["isactive"]:
            self.dataTables[tableName].forbiddenTables = self.forbiddenTables
            self.dataTables[tableName].insertDataSet(self.database, dataset)
                    
    def importFiles(self, data, filedata):
        if not(type(self.UserRights) is dict and self.UserRights["user"]["allow_fileupload"] == 1):
            raise PermissionError("Uploading Files not allowed!")            
        data = self.dictKeysToLower(data)
        validFileTypes = self.database.execute_query("SELECT DISTINCT EMA_filetype.* FROM EMA_filetype")
        fileNameComponents = data["filename"].lower().replace(".feat", "").split("_")
        if fileNameComponents[0].lower() in [item['fileextension'].lower() for item in validFileTypes]:
            if not os.path.isdir(os.path.join(self.FeatureFilesFolder, data["subject"])):
                os.makedirs(os.path.join(self.FeatureFilesFolder, data["subject"]))
            if data["overwrite"] == True or not os.path.isfile(os.path.join(self.FeatureFilesFolder, data["subject"], data["filename"])):
                startDate = datetime.datetime.strptime(fileNameComponents[-2] + fileNameComponents[-1], '%Y%m%d%H%M%S%f').strftime("%Y-%m-%d %H:%M:%S")
                endDate = (datetime.datetime.strptime(fileNameComponents[-2] + fileNameComponents[-1], '%Y%m%d%H%M%S%f') + datetime.timedelta(seconds=60)).strftime("%Y-%m-%d %H:%M:%S")
                myFiles = self.getDataSet("file", {"subject": data["subject"], "start": startDate, "filename" : data["filename"]}, True)
                if len(myFiles) == 0:
                    newFile = {}
                    newFile["filetype_id"] = [item['id'] for item in validFileTypes if item['fileextension'] == data["filename"][0:3].lower()][0]
                    newFile["lastupdate"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
                    newFile["filename"] = data["filename"]
                    newFile["isvalid"] = False
                    myDataChunk = self.getDataSet("datachunk", {"subject": data["subject"], "start" : "[<=]" + startDate, "end": "[>]" + startDate}, True)
                    if len(myDataChunk) == 0:
                        newDataSet = {}
                        newDataSet["subject"] = data["subject"]
                        newDataSet["start"] = startDate
                        newDataSet["end"] = endDate
                        newDataSet["file"] = [newFile]
                        myDataChunk.append(newDataSet)
                        self.insertDataSet("datachunk", {"datachunk": myDataChunk})
                    else:
                        if myDataChunk[0]["start"] != datetime.datetime.strptime(startDate, "%Y-%m-%d %H:%M:%S") or myDataChunk[0]["end"] != datetime.datetime.strptime(endDate, "%Y-%m-%d %H:%M:%S"):
                            myDataChunk[0]["start"] = startDate
                            myDataChunk[0]["end"] = endDate
                            self.insertDataSet("datachunk", myDataChunk)
                        newFile["datachunk_id"] = myDataChunk[0]["id"]
                        self.insertDataSet("file", {"file": [newFile]})
                else:
                    updatedFile = copy.deepcopy(myFiles[0])
                    updatedFile["lastupdate"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    updatedFile["id"] = myFiles[0]["hash"]
                    self.updateDataSet({"file" : [updatedFile]}, {"file": [myFiles[0]]}, True)
                filedata.save(os.path.join(self.FeatureFilesFolder, data["subject"], data["filename"]))
                filedata.close()
        return True
    
    def exportFiles(self, dataset):
        dataset = self.dictKeysToLower(dataset)
        def findURLs(data, returnData = [], subject = ""):
            if type(data) is dict:
                if type(data) is dict and "subject" in  data.keys():
                    subject = data["subject"]
                for item in data.keys():
                    if type(data[item]) is dict or type(data[item]) is list:
                        returnData = findURLs(data[item], returnData, subject = subject)
                if "filename" in data.keys():
                    returnData.append(os.path.join(subject, data["filename"]))
            elif type(data) is list:
                for item in data:
                    if type(data) is dict and "subject" in  data.keys():
                        subject = data["subject"]
                    if type(item) is dict or type(item) is list:
                        returnData = findURLs(item, returnData, subject)
            return returnData
        filenames = findURLs(dataset)
        filesToExport = []
        for idx in reversed(range(len(filenames))):
            filename = os.path.basename(filenames[idx])
            if os.path.isfile(filenames[idx]) and (not filenames[idx] in filesToExport) and (len([row["allowread"] for row in self.UserRights["authorization"] if row["name"] == filename[0:3].lower()]) != 0 and [row["allowread"] for row in self.UserRights["authorization"] if row["name"] == filename[0:3].lower()][0] != 0):
                filesToExport.append(filenames[idx])
        return self.dictKeysToLower(filesToExport)

    def importQuestinares(self, data, filedata):
        if not(type(self.UserRights) is dict and self.UserRights["user"]["allow_fileupload"] == 1):
            raise PermissionError("Uploading Files not allowed!")            
        data = self.dictKeysToLower(data)
        newQuestinare = {}
        newQuestinare["answer"] = []
        newQuestinare["motivation"] = ""
        newQuestinare["app_version"] = ""
        newQuestinare["device"] = ""
        newQuestinare["filename"] = data["filename"]
        for child in ET.fromstring(filedata):
            if "motivation" in child.attrib.keys():
                newQuestinare["motivation"] = child.attrib["motivation"]
            elif "survey_uri" in child.attrib.keys():
                newQuestinare["surveyfile"] = os.path.basename(child.attrib["survey_uri"])
            for subchild in child:
                if subchild.tag == "value":
                    if "start_date" in subchild.attrib.keys() and validate(subchild.attrib["start_date"]):
                        newQuestinare["start"] = datetime.datetime.strptime(subchild.attrib["start_date"], '%Y-%m-%dT%H:%M:%S').strftime("%Y-%m-%d %H:%M:%S")
                    elif "end_date" in subchild.attrib.keys() and validate(subchild.attrib["end_date"]):
                        newQuestinare["end"] = datetime.datetime.strptime(subchild.attrib["end_date"], '%Y-%m-%dT%H:%M:%S').strftime("%Y-%m-%d %H:%M:%S")
                    elif "device_id" in subchild.attrib.keys():
                        newQuestinare["device"] = subchild.attrib["device_id"]
                    elif "app_version" in subchild.attrib.keys():
                        newQuestinare["app_version"] = subchild.attrib["app_version"]
                    elif "question_id" in subchild.attrib.keys() and "option_ids" in subchild.attrib.keys():
                        for answer in subchild.attrib["option_ids"].split(";"):                                
                            tmpAnswer = {}
                            #newAnswer["question_id"] = subchild.attrib["question_id"]
                            tmpAnswer["questionkey"] = subchild.attrib["question_id"]
                            tmpAnswer["answerkey"] = answer
                            newQuestinare["answer"].append(tmpAnswer)
                    elif "question_id" in subchild.attrib.keys():
                        if subchild.attrib["question_id"] == "10817" and validate(subchild.text):
                            newQuestinare["start"] = datetime.datetime.strptime(subchild.text, '%Y-%m-%dT%H:%M:%S').strftime("%Y-%m-%d %H:%M:%S")
                        elif subchild.attrib["question_id"] == "10834" and validate(subchild.text):
                            newQuestinare["end"] = datetime.datetime.strptime(subchild.text, '%Y-%m-%dT%H:%M:%S').strftime("%Y-%m-%d %H:%M:%S")
                        elif subchild.attrib["question_id"] == "10816":
                            newQuestinare["device"] = str(subchild.text)
                        
        if len(newQuestinare["answer"]) > 0 and "start" in newQuestinare.keys() and "end" in newQuestinare.keys():
            DataChunks = self.getDataSet("datachunk", {"subject": data["subject"], "questionnaire" : {"filename" : newQuestinare["filename"]}}, True)
            if len(DataChunks) == 0:
                DataChunks = self.getDataSet("datachunk", {"subject": data["subject"], "start" : "[<=]" + newQuestinare["start"], "end": "[>]" + newQuestinare["start"]}, True)
                if len(DataChunks) == 0:
                    newDataChunk = {}
                    newDataChunk["start"] = newQuestinare["start"]
                    newDataChunk["end"] = newQuestinare["end"] # (datetime.datetime.strptime(newQuestinare["start"], "%Y-%m-%d %H:%M:%S")  + datetime.timedelta(seconds=60)).strftime("%Y-%m-%d %H:%M:%S")
                    newDataChunk["subject"] = data["subject"]
                    DataChunks.append(newDataChunk)
                DataChunks[0]["questionnaire"] = [newQuestinare]
                self.insertDataSet("datachunk", {"datachunk": DataChunks})
            else:
                AnswersToImport = []
                AnswersToDelete = []
                for count in range(len(DataChunks[0]["questionnaire"])):
                    if DataChunks[0]["questionnaire"][count]["filename"] == newQuestinare["filename"]:       
                        existingAnswers = DataChunks[0]["questionnaire"][count]["answer"]
                        for count in reversed(range(len(newQuestinare["answer"]))):
                            currAnswer = newQuestinare["answer"][count]
                            for countExistingAnswers in reversed(range(len(existingAnswers))):
                                if currAnswer["questionkey"] == existingAnswers[countExistingAnswers]["questionkey"] and currAnswer["answerkey"] == existingAnswers[countExistingAnswers]["answerkey"]:
                                    del newQuestinare["answer"][count]
                                    del existingAnswers[countExistingAnswers]
                        for count in reversed(range(len(newQuestinare["answer"]))):
                            currAnswer = newQuestinare["answer"][count]
                            blnFirstRow = True
                            for countExistingAnswers in reversed(range(len(existingAnswers))):
                                if currAnswer["questionkey"] == existingAnswers[countExistingAnswers]["questionkey"] and currAnswer["answerkey"] != existingAnswers[countExistingAnswers]["answerkey"]:
                                    if blnFirstRow:
                                        existingAnswers[countExistingAnswers]["answerkey"] = currAnswer["answerkey"]
                                        AnswersToImport.append(existingAnswers[countExistingAnswers])
                                        blnFirstRow = False
                                    else:
                                        AnswersToDelete.append(existingAnswers[countExistingAnswers])                                
                                    del newQuestinare["answer"][count]
                                    del existingAnswers[countExistingAnswers]
                        for currAnswer in newQuestinare["answer"]:
                            AnswersToImport.append(currAnswer)
                        for AnswerToDelete in AnswersToDelete:
                            self.database.execute_query("DELETE FROM EMA_answer WHERE id = '" + AnswerToDelete["id"] + "'")
                        if len(AnswersToImport) > 0:
                            DataChunks[0]["questionnaire"][count]["answer"] = AnswersToImport
                            self.insertDataSet("datachunk", {"datachunk": DataChunks})
        return True
    
    def createNewFeatureValue(self, FeatureName):
        self.dataTables["feature"].forbiddenTables = self.forbiddenTables
        feature = self.dataTables["feature"].getDataSet(self.database, {"feature" : {"name" : "[like]" + FeatureName}}, False)
        if len(feature) == 1:
            userRight = [item["allowwrite"] for item in self.UserRights["authorization"] if item["name"] == feature[0]["name"].lower()]
            if len(userRight) != 1 or userRight[0] != 1:
                raise PermissionError("Creating feature '" + feature[0]["name"] + "' not allowed!")
            value = feature[0].copy()
            del value["id"]
            del value["hash"]
            self.dataTables["featurevalue"].forbiddenTables = self.forbiddenTables
            for field in self.dataTables["featurevalue"].fields:
                if field[1].startswith("datetime"):
                    value[field[0]] = "0000-00-00 00:00:00:000000"
                elif field[1] == "bool":
                    value[field[0]] = False
                elif field[1] == "tinyint(1)":
                    value[field[0]] = 0
                elif field[1] == "real" or field[1] == "double" or field[1] == "integer" or field[1].startswith("int("): 
                    value[field[0]] = 0
                else:
                    value[field[0]] = ""
            value["subject"] = ""
            del value["description"]
            del value["lastupdate"]
            value = self.dictKeysToLower(value)
            return self.dictKeysToLower(value)

    def saveFeatureValue(self, value):
        self.dataTables["feature"].forbiddenTables = self.forbiddenTables
        if type(value) is list:
            values = value
        else:
            values = [value]
        for value in values:
            feature = self.dataTables["feature"].getDataSet(self.database, {"feature" : {"name" : value["name"]}}, False)
            if len(feature) == 0:
                raise ValueError("feature name not valid!")
            else:
                userRight = [item["allowwrite"] for item in self.UserRights["authorization"] if item["name"] == value["name"].lower()]
                if len(userRight) != 1 or userRight[0] != 1:
                    raise PermissionError("Writing feature '" + value["name"] + "' not allowed!")
                value["feature_id"] = feature[0]["id"]
            if str(value["side"]) == "":
                raise ValueError("side must be set!")
            self.dataTables["featurevalue"].forbiddenTables = self.forbiddenTables
            featurevalues = self.dataTables["featurevalue"].getDataSet(self.database, {"featurevalue" : {"subject" : value["subject"], "start": value["start"], "end": value["end"], "side": value["side"], "feature": {"name": value["name"]}}}, False)
            if len(featurevalues) == 0:
                newFeaturevalues = {}
                newFeaturevalues["name"] = value["name"] 
                newFeaturevalues["side"] = value["side"] 
                newFeaturevalues["start"] = value["start"]
                newFeaturevalues["end"] = value["end"] 
                newFeaturevalues["value"] = value["value"] 
                newFeaturevalues["isvalid"] = value["isvalid"] 
                featurevalues.append(newFeaturevalues)
                self.dataTables["datachunk"].forbiddenTables = self.forbiddenTables
                DataChunk = self.dataTables["datachunk"].getDataSet(self.database, {"datachunk" : {"subject" : value["subject"], "start": "<=" + value["start"], "end": ">" + value["start"]}}, False)
                if len(DataChunk) == 0:
                    newDataChunk = {}
                    newDataChunk["start"] = value["start"]
                    newDataChunk["end"] = value["end"] 
                    newDataChunk["subject"] = value["subject"] 
                    newDataChunk["featurevalue"] = [newFeaturevalues]
                    DataChunk.append(newDataChunk)
                else:
                    DataChunk[0]["featurevalue"] = [newFeaturevalues]
                self.insertDataSet("datachunk", {"datachunk": DataChunk})
            else:    
                updatedFeaturevalue = copy.deepcopy(featurevalues[0])
                updatedFeaturevalue["id"] = featurevalues[0]["hash"]
                updatedFeaturevalue["value"] = value["value"] 
                updatedFeaturevalue["isvalid"] = value["isvalid"] 
                self.updateDataSet({"featurevalue" : [updatedFeaturevalue]}, {"featurevalue": [featurevalues[0]]}, True)
        return True
            
    def deleteFeatureValues(self, dataset):
        def removeUnwantedRows(fieldsToFind, UserRights, data, origData):
            rowsToDelete = []
            if type(data) is dict:
                for item in [item for item in list(data) if type(data[item]) is list]:
                    if item in origData.keys():
                        rowsToDelete += removeUnwantedRows(fieldsToFind, UserRights, data[item], origData[item])
            elif type(data) is list:
                for idx in [idx for idx in reversed(range(len(data))) if type(data[idx]) is dict]:
                    origRow = {}
                    for tmpRow in origData:
                        if "id" in tmpRow.keys() and "id" in data[idx] and tmpRow["hash"] == data[idx]["id"]:
                            origRow = tmpRow
                            if len([item for item in origRow.keys() if item in fieldsToFind + ["description", "name"]]) == len(fieldsToFind) + 2:
                                if "feature_id" in origRow.keys() and [row["allowwrite"] for row in UserRights["authorization"] if row["feature_id"] == origRow["feature_id"]][0] == 1:
                                    rowsToDelete += [origRow["id"]]
                            rowsToDelete += removeUnwantedRows(fieldsToFind, UserRights, data[idx], origRow)
            return rowsToDelete

        if self.lastDataset and len(self.lastDataset) > 0 and hasattr(self, "UserRights") and type(self.UserRights) is dict and self.UserRights["user"]["isactive"]:
            lastDataset = self.dictKeysToLower(self.lastDataset)
            dataset = self.dictKeysToLower(dataset)
            if type(dataset) is list and type(lastDataset) is dict:
                dataset = {list(lastDataset.keys())[0] : dataset}
            self.dataTables["featurevalue"].forbiddenTables = self.forbiddenTables
            rowsToDelete = removeUnwantedRows([item[0] for item in self.dataTables["featurevalue"].fields],  self.UserRights, dataset, lastDataset)
            if not hasattr(self, 'deletehash') or not self.deletehash == hash(str(rowsToDelete)):
                self.deletehash = hash(str(rowsToDelete))
                return {"CONFIRMDELETE" : len(rowsToDelete)}
            else:
                return self.dataTables["featurevalue"].deleteRowsFromTable(self.database, rowsToDelete)
    
    def dictKeysToLower(self, data):
        return data
        """
        if type(data) is dict:
            data = {k.lower(): v for k, v in data.items()}
            for item in list(data):
                data[item] = self.dictKeysToLower(data[item])
        elif type(data) is list:
            if len(data) == 1 and type(data[0]) is list:
                data = data[0]
            for idx in [idx for idx in range(len(data)) if type(data[idx]) is dict]:
                data[idx] = self.dictKeysToLower(data[idx])
        return data
        """