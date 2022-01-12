import uuid
import datetime
import sqlite3
import mysql.connector

class dBTable(object):
    def __init__(self, name, fields):
        self.prefix = "EMA_"
        self.name = name.replace(self.prefix, "")
        self.primaryKeys = []
        self.foreignKeys = []
        self.parentTables = []
        self.childTables = []
        self.fields = []
        self.forbiddenTables = []
        for field in fields:
            if "type" in field.keys() and type(field["type"]) is bytes:
                field["type"] = field["type"].decode("utf-8")
            if "name" in field.keys() and type(field["name"]) is bytes:
                field["name"] = field["name"].decode("utf-8")
            if "field" in field.keys() and type(field["field"]) is bytes:
                field["field"] = field["field"].decode("utf-8")
            if "pk" in field.keys() and field["pk"] == 1:
                self.primaryKeys.append([field["name"].lower(), field["type"]])
            elif "key" in field.keys() and field["key"] == "PRI":
                self.primaryKeys.append([field["field"].lower(), field["type"]])
            elif "name" in field.keys() and field["name"][-3:].lower() == "_id":
                self.foreignKeys.append([field["name"].lower(), field["type"]])                
            elif "key" in field.keys() and field["key"] == "MUL":
                self.foreignKeys.append([field["field"].lower(), field["type"]])                
            elif "name" in field.keys():
                self.fields.append([field["name"].lower(), field["type"]])
            elif "field" in field.keys():
                self.fields.append([field["field"].lower(), field["type"]])
        self.allFields = self.primaryKeys + self.foreignKeys + self.fields;
        self.isRealationTable = (len(self.foreignKeys) == 2 and len(self.fields) == 0)
        
    def createSQLs(self):
        if not hasattr(self, "SQL"):
            self.SQL = dict()
            self.SQL["fields"] = list(set(self.prefix + self.name + "." + item[0] + " as " + self.name + "_" + item[0] for item in self.fields))
            self.SQL["allfields"] = list(set(self.prefix + self.name + "." + item[0] + " as " + self.name + "_" + item[0] for item in self.primaryKeys + self.fields))
            self.SQL["join"] = []
            self.SQL["joinparent"] = []

            for table in self.parentTables:
                #if not table.name in self.forbiddenTables:
                self.SQL["fields"] = list(set(self.SQL["fields"]).union(table.createSQLs()["fields"]));
                if table.name + "_" + table.primaryKeys[0][0] in list((item[0] for item in self.foreignKeys)):
                    strJoin = "left join " + table.prefix + table.name + " on " + table.prefix + self.name + "." + table.name + "_" + table.primaryKeys[0][0] + " = " + table.prefix + table.name + "." + self.primaryKeys[0][0]
                    self.SQL["joinparent"] = list(set(self.SQL["joinparent"]).union([strJoin]));
                self.SQL["joinparent"] = list(set(self.SQL["joinparent"]).union(table.createSQLs()["joinparent"]));
                    
            for table in self.childTables:
                #if not table.name in self.forbiddenTables:
                self.SQL["fields"] = list(set(self.SQL["fields"]).union(table.createSQLs()["fields"]));
                if self.name + "_" + self.primaryKeys[0][0] in list((item[0] for item in table.foreignKeys)):
                    strJoin = "left join " + table.prefix + table.name + " on " + table.prefix + self.name + "." + self.primaryKeys[0][0] + " = " + table.prefix + table.name + "." + self.name + "_" + table.primaryKeys[0][0]
                    self.SQL["join"] = list(set(self.SQL["join"]).union([strJoin]));
                self.SQL["join"] = list(set(self.SQL["join"]).union(table.createSQLs()["join"]));
        return self.SQL
        
    def getDataSet_Conditions_Comparison(self, field, value):
        myConditions = []
        myValues = {}
        fieldType = self.allFields[[item[0] for item in self.allFields].index(field.lower())][1]
        if value is None:
            return [field + " is Null "], myValues
        if value.find("||") >= 0:
            tmp = []
            tmpValues = {}
            for item in value.split("||"):
                tmpItems, tmpValues = self.getDataSet_Conditions_Comparison(field, item)
                tmp += tmpItems
                myValues.update(tmpValues)
            myConditions.append("(" +  " or ".join([v for v in tmp]) + ")")
        else:
            if type(value) is str and len(value) > 1 and value[0] == "[" and "]" in value:  
                values = [item.split("]") for item in value.split("[")[1:]]
            else:
                values = [["=", value]]
            tmpConditions = []
            for tmpValue in values:
                if tmpValue[0].startswith(">="):
                    tmpValue[0] = ">="
                    tmpValue[1] = tmpValue[1]
                elif tmpValue[0].startswith("<="):
                    tmpValue[0] = "<="
                    tmpValue[1] = tmpValue[1]
                elif tmpValue[0].startswith(">"):
                    tmpValue[0] = ">"
                    tmpValue[1] = tmpValue[1]
                elif tmpValue[0].startswith("<"):
                    tmpValue[0] = "<"
                    tmpValue[1] = tmpValue[1]
                elif tmpValue[0].startswith("!="):
                    tmpValue[0] = "<>"
                    tmpValue[1] = tmpValue[1]
                else:
                    tmpValue[0] = "="
                if field == "id" and len(str(tmpValue[1])) > 0 and str(tmpValue[1])[0] == "[":
                    pass
                elif fieldType.startswith("datetime"):
                    #tmpConditions.append(self.prefix + self.name + "." + field + " " + tmpValue[0] + " '" + str(tmpValue[1]) + "'") 
                    tmpConditions.append(self.prefix + self.name + "." + field + " " + tmpValue[0] + " %(" + self.prefix + self.name + "_" + field + ")s")
                    myValues[self.prefix + self.name + "_" + field] = tmpValue[1]
                elif fieldType == "bool" or fieldType == "tinyint(1)":
                    if str(tmpValue[1]).upper() == "TRUE" or str(tmpValue[1]).upper() == "1":
                        tmpValue[1] = 1
                    else:
                        tmpValue[1] = 0
                    #tmpConditions.append(self.prefix + self.name + "." + field + " " + tmpValue[0] + " " + str(tmpValue[1]) + " ") 
                    tmpConditions.append(self.prefix + self.name + "." + field + " " + tmpValue[0] + " %(" + self.prefix + self.name + "_" + field + ")s")
                    myValues[self.prefix + self.name + "_" + field] = tmpValue[1]
                elif fieldType == "real" or fieldType == "double" or fieldType == "integer" or fieldType.startswith("int("):
                    if "." in str(tmpValue[1]):
                        r = str(len(str(tmpValue[1])[str(tmpValue[1]).index(".") + 1 :]))
                        #tmpConditions.append("round(" + self.prefix + self.name + "." + field + ", " + r + ") = round(" + str(tmpValue[1]) + ", " + r + ")")
                        tmpConditions.append(self.prefix + self.name + "." + field + " " + tmpValue[0] + " round(%(" + self.prefix + self.name + "_" + field + ")s" + ")")
                        myValues[self.prefix + self.name + "_" + field] = tmpValue[1]
                    else:
                        #tmpConditions.append(self.prefix + self.name + "." + field + " " + tmpValue[0] + " " + str(tmpValue[1]))
                        tmpConditions.append(self.prefix + self.name + "." + field + " " + tmpValue[0] + " %(" + self.prefix + self.name + "_" + field + ")s")
                        myValues[self.prefix + self.name + "_" + field] = tmpValue[1]
                else: # "varchar" in fieldType or fieldType == "text" or 
                    if str(tmpValue[1]).startswith("%") or str(tmpValue[1]).endswith("%"):
                        tmpValue[0] = " like "
                    #tmpConditions.append(self.prefix + self.name + "." + field + " " + tmpValue[0] + " '" + str(tmpValue[1]) + "'")
                    tmpConditions.append(self.prefix + self.name + "." + field + " " + tmpValue[0] + " %(" + self.prefix + self.name + "_" + field + ")s")
                    myValues[self.prefix + self.name + "_" + field] = tmpValue[1]
                if len(tmpConditions) > 0:
                    myConditions.append(" and ".join(tmpConditions))
        return myConditions, myValues
        
    def getDataSet_Conditions(self, conditions, returnAsList = False):
        strWhere = ""
        myConditions = []
        myValues = {}
        if conditions:
            for field in list(set(conditions.keys()).intersection([item[0] for item in self.allFields])):
                tmpConditions, tmpValues = self.getDataSet_Conditions_Comparison(field, conditions[field])
                myConditions += tmpConditions
                myValues.update(tmpValues)
                del conditions[field]
            if len(myConditions):
                strWhere += " WHERE " + " AND ".join(myConditions)
        if returnAsList == False:
            return strWhere, myValues
        else:
            return myConditions, myValues
    
    def getConditionalWhereStatement(self, conditions = False):
        whereStatement = []
        if conditions:
            if self.name in conditions.keys():
                conditions = conditions[self.name]
        conditionStatement, values = self.getDataSet_Conditions(conditions, True)
        whereStatement.extend(conditionStatement)
        for table in self.childTables:
            #if conditions and table.name in conditions.keys():
            if conditions and table.name in conditions.keys():
                conditionStatement, tmpValues = table.getConditionalWhereStatement(conditions[table.name])
                values.update(tmpValues)
                whereStatement.extend(conditionStatement)
        for parent in self.parentTables:
            tmpConditions =  {parent.name : {}}
            if conditions:
                tmpList = []
                tmpList += list(set(conditions.keys()).intersection([item[0] for item in parent.fields]))
                if len(tmpList) > 0:
                    tmpConditions[parent.name].update([{item : conditions[item]} for item in tmpList][0])    
            if parent.name in conditions.keys():
                tmpList = []
                tmpList += list(set(conditions[parent.name].keys()).intersection([item[0] for item in parent.fields]))
                if len(tmpList) > 0:
                    tmpConditions[parent.name].update([{item : conditions[parent.name][item]} for item in tmpList][0])
            conditionStatement, tmpValues = parent.getConditionalWhereStatement(tmpConditions)
            values.update(tmpValues)
            whereStatement.extend(conditionStatement)
        return whereStatement, values
            
    def getDataSet(self, database, conditions = False, recursive = True, callingTableName = ""):
        if conditions:
            if self.name in conditions.keys():
                conditions = conditions[self.name]
        try:
            blnUseExtendedSQL = False
            for table in self.childTables + self.parentTables:
                if conditions and table.name in conditions.keys():
                    blnUseExtendedSQL = True
                    break
            orderBy = ""
            if self.name == "datachunk":
                orderBy = " ORDER BY " + self.prefix + self.name + ".Subject, " + self.prefix + self.name + ".Start"
            elif self.name == "feature":
                orderBy = " ORDER BY " + self.prefix + self.name + ".name"
            elif self.name == "file":
                orderBy = " ORDER BY " + self.prefix + self.name + ".filename"
            elif self.name == "questionnaire":
                orderBy = " ORDER BY " + self.prefix + self.name + ".start"
            elif self.name == "featurevalue":
                orderBy = " ORDER BY " + self.prefix + self.name + ".start, " + self.prefix + self.name + ".Feature_id, " + self.prefix + self.name + ".Side"
            if blnUseExtendedSQL:                            
                conditionList, values = self.getConditionalWhereStatement(conditions)
                strFromAndJoin = "FROM " + self.prefix + self.name + " " + " ".join(self.SQL["join"]) + " " + " ".join(self.SQL["joinparent"])
                for count in reversed(range(len(conditionList))):
                    tmp = conditionList[count].split(".", 1)
                    if not(len(tmp) > 0 and strFromAndJoin.find(tmp[0] + ".") >= 0):
                        del conditionList[count]
                        del values[count]
                strSql = "SELECT DISTINCT " + self.prefix + self.name + ".* " + strFromAndJoin + " WHERE " + " AND ".join(conditionList)
            else:
                conditionStatement, values = self.getDataSet_Conditions(conditions)
                strSql = "SELECT DISTINCT " + self.prefix + self.name + ".* FROM " + self.prefix + self.name + conditionStatement
            mainTable = database.execute_query(strSql + orderBy, values)
        except Exception as e:
            conditionStatement, values = self.getDataSet_Conditions(conditions, False)
            strSql = "SELECT DISTINCT " + self.prefix + self.name + ".* FROM " + self.prefix + self.name + conditionStatement
            mainTable = database.execute_query(strSql, values)
        returnTable = []
        for row in mainTable:
            addRowToFinalDataset = True
            if recursive:
                tablenames = []
                if type(conditions) is dict:
                    tablenames = list(set(conditions.keys()).intersection([i.name for i in self.childTables]))
                tablenames.extend(list(set([i.name for i in self.childTables]).difference(tablenames)))
                for tablename in tablenames:
                    if addRowToFinalDataset:
                        for table in self.childTables:
                            if table.name not in self.forbiddenTables and table.name == tablename:
                                tmpConditions = {}
                                tmpConditions[table.name] = {}
                                hasCondition = False
                                if conditions and table.name in conditions.keys():
                                    tmpConditions[table.name] = conditions[table.name]
                                    hasCondition = True
                                if type (tmpConditions[table.name]) is dict:
                                    tmpConditions[table.name][self.name + "_id"] = row["id"]
                                    row[table.name] = table.getDataSet(database, tmpConditions, True, self.name)
                                    if hasCondition and len(row[table.name]) == 0:
                                        addRowToFinalDataset = False    
                for parent in self.parentTables:
                    if parent.name not in self.forbiddenTables and addRowToFinalDataset and not callingTableName == parent.name:
                        tmpConditions = {parent.name : {"id" : row[parent.name + "_id"]}}
                        hasCondition = False
                        tmpList = []
                        if conditions:
                            tmpList = list(set(conditions.keys()).intersection([item[0] for item in parent.fields]))
                        if len(tmpList) > 0:
                            tmpConditions[parent.name].update([{item : conditions[item]} for item in tmpList][0])
                            hasCondition = True
                        tmp = parent.getDataSet(database, tmpConditions, False)
                        if len(tmp) == 1:
                            row.update({k: v for k, v in tmp[0].items() if k != "hash" and k not in [k2[0] for k2 in parent.primaryKeys]})
                        elif hasCondition and len(tmp) == 0:
                            addRowToFinalDataset = False
            row["hash"] = "[" + str(hash(str(row))).replace("-", "") + "]"
            if addRowToFinalDataset:
                returnTable.append(row)
        return returnTable
    
    def exists(self, database, conditions = False):
        return len(self.getDataSet(database, conditions, False)) > 0

    def updateDataSet(self, database, dataset, origDataset, recursive = True, parentData = {}):
        if type(dataset) is dict and self.name in  dataset.keys():
            for table in dataset:
                if type(dataset[table]) is dict:
                    dataset[table] = [dataset[table]]
                for rowIdx in range(len(dataset[table])):
                    newRow = dataset[table][rowIdx]
                    if type(newRow) is dict: 
                        oldRow = False
                        for tmpRow in origDataset[table]:
                            if "id" in newRow.keys() and tmpRow["hash"] == newRow["id"]:
                                oldRow = tmpRow
                        fields = list(set(item[0] for item in self.fields).intersection(newRow.keys()))
                        if oldRow and oldRow["hash"] == newRow["id"] and not [oldRow[item] for item in fields] == [newRow[item] for item in fields]:
                            if "lastupdate" in [item[0] for item in self.fields]:
                                newRow["lastupdate"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            values = {self.prefix + self.name + "_" + item[0]: newRow[item[0]] for item in self.fields if not newRow[item[0]] == oldRow[item[0]]}
                            values.update({self.prefix + self.name + "_id" : oldRow["id"]})
                            strSql = "UPDATE " + self.prefix + self.name + " SET " + ", ".join([item[0] + " = %(" + self.prefix + self.name +"_" + item[0] + ")s" for item in self.fields if not newRow[item[0]] == oldRow[item[0]]]) + " WHERE id = %(" + self.prefix + self.name + "_id)s"
                            database.execute_query(strSql, values)
                        elif oldRow == False:
                            if not "id" in newRow.keys():
                                if "lastupdate" in newRow.keys():
                                    del newRow["lastupdate"]
                                if len(self.getDataSet(database, {self.name: newRow}, True)) == 0:
                                    #newRow["id"] = str(uuid.uuid4())
                                    for item in parentData:
                                        newRow[item] = parentData[item]
                                    for item in [item.name for item in self.parentTables if item.name in newRow.keys()]:
                                        newRow[item  + "_id"] = newRow[item]
                                    self.insertDataSet(database, {self.name : [newRow]})
                                    oldRow = newRow
                                    oldRow["hash"] = newRow["id"]
                                else:
                                    raise ValueError("Manually added Datarow already exists in Database!") 
                            else:
                                return
                        if recursive:
                            for child in self.childTables:
                                if child.name in newRow.keys():
                                    child.updateDataSet(database, {child.name : newRow[child.name]}, {child.name : oldRow[child.name]}, True, {self.name + "_id" : oldRow["id"]})
                            for parent in self.parentTables:
                                oldRow["id"] = oldRow[parent.name + "_id"]
                                parent.updateDataSet(database, {parent.name: [newRow]}, {parent.name : [oldRow]}, False)
    
    def deleteRowsFromTable(self, database, idList):
        count = 0
        if type(idList) is list:
            for item in idList:
                strSql = "DELETE FROM " + self.prefix + self.name + " WHERE ID = %(ID)s"
                database.execute_query(strSql, {"ID" : item})
                count += 1
        return {"ROWSAFFECTED": count}
                        
    def insertDataSet(self, database, dataset, callingTableName = ""):
        if type(dataset) is dict and self.name in dataset.keys():
            for table in dataset:
                for rowIdx in range(len(dataset[table])):
                    blnNewRew = False
                    newRow = dataset[table][rowIdx]
                    if "id" not in newRow.keys():
                        newRow["id"] = str(uuid.uuid4())
                        blnNewRew = True
                        if "lastupdate" in [item[0] for item in self.fields]:
                            newRow["lastupdate"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    for parent in self.parentTables:
                        fields = list(set(newRow.keys()).intersection([item[0] for item in parent.fields]))
                        if not callingTableName == parent.name and len(fields):
                            values = {self.prefix + parent.name + "_" + item : newRow[item] for item in fields}
                            strSql = "SELECT DISTINCT id FROM " + self.prefix + parent.name + " WHERE " + " AND ".join([item + " = %(" + self.prefix + parent.name + "_" + item + ")s" for item in fields])
                            if not hasattr(self, "strSql_old") or self.strSql_old != strSql or self.values_old != values:
                                self.parentTable = database.execute_query(strSql, values)
                                self.strSql_old = strSql
                                self.values_old = values
                            if len(self.parentTable) == 1:
                                newRow[parent.name + "_id"] = self.parentTable[0]["id"]
                            elif len(self.parentTable) == 0:
                                self.strSql_old = ""
                                newRow[parent.name + "_id"] = str(uuid.uuid4())                                    
                                values = {self.prefix + parent.name + "_" + item : newRow[item] for item in fields}
                                values.update({self.prefix + parent.name + "_" + parent.name + "_id": newRow[parent.name + "_id"]})
                                strSql = "INSERT INTO " + self.prefix + parent.name + " (" + ", ".join(fields + ["id"]) + ") VALUES (" + ", ".join(["%(" + self.prefix + parent.name + "_" + item +")s" for item in fields + [parent.name + "_id"]]) + ");"
                                #database.tempQuery += strSql
                                database.execute_query(strSql, values)
                    
                    if blnNewRew:
                        fields = list(set(newRow.keys()).intersection([item[0] for item in self.allFields]))
                        for field in fields:
                            fieldType = [item[1] for item in self.allFields if item[0] == field]
                            if len(fieldType) == 1:
                                if fieldType[0].startswith("datetime"):
                                    newRow[field] = str(newRow[field])
                                elif fieldType[0] == "bool" or fieldType[0] == "tinyint(1)":
                                    if str(newRow[field]).upper() == "TRUE" or str(newRow[field]) == "1":
                                        newRow[field] = "1"
                                    else:
                                        newRow[field] = "0"
                                elif fieldType[0] == "real" or fieldType[0] == "double" or fieldType[0] == "integer" or fieldType[0].startswith("int("):                                        
                                    newRow[field] = str(newRow[field])
                                elif not (str(newRow[field]).startswith("'") and str(newRow[field]).endswith("'")): 
                                    newRow[field] = str(newRow[field])
                        values = {self.prefix + self.name + "_" + item : newRow[item] for item in fields}
                        strSql = "INSERT INTO " + self.prefix + self.name + " (" + ", ".join(fields) + ") VALUES (" + ", ".join(["%(" + self.prefix + self.name + "_" + item + ")s" for item in fields]) + ");"
                        #database.tempQuery += strSql
                        try:
                            database.execute_query(strSql, values)
                        except (sqlite3.IntegrityError, mysql.connector.errors.DatabaseError):
                            print (strSql)
                            database.close()
                            raise
                        except ValueError:
                            print(strSql)
                            raise
                    for child in self.childTables:
                        if child.name in newRow.keys():
                            for childRow in newRow[child.name]:
                                childRow[self.name + "_id"] = newRow["id"]
                            child.insertDataSet(database, {child.name : newRow[child.name]}, self.name)
if __name__ == "__main__":
    exec(open("../main.py").read())
