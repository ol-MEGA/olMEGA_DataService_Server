import zlib
from olMEGA_DataService_Server.dataConnectors import dataConnector, databaseConnector as databaseConnector
import olMEGA_DataService_Server.dbTable as dbTable
import sys
from flask import Flask, Response, request, json, render_template, session, send_file
from flask_httpauth import HTTPBasicAuth
from json2xml import json2xml
from flask_session import Session
from datetime import timedelta
import traceback
import sqlite3
import mysql.connector
import random
import gc
import os
import zipfile
import tempfile
import logging
import hashlib
import pathlib
import configparser

class olMEGA_DataService_Server(object):
    auth = HTTPBasicAuth()   

    def __init__(self):
        config = configparser.ConfigParser()
        config.read('settings.conf')
        if sys.version_info[0] < 3:
            raise Exception("Must be using Python 3")
        if config["MAIN"]["Debug"] == False:
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
        self.forbiddenTables = ["authorization", "user", "usergroup"]
        self.dataTables = {}
        database = databaseConnector()
        if database.db == "mySQL":
            print ("  ****************************************************************************************")
            print ("  *                                                                                      *")
            print ("  * INFO: you are using a mySQL-Database!                                                *")
            print ("  *                                                                                      *")
            print ("  ****************************************************************************************")
            tables = database.execute_query("SHOW TABLES LIKE 'EMA_%';", {})
        elif database.db == "sqlite3":
            print ("  ****************************************************************************************")
            print ("  *                                                                                      *")
            print ("  * INFO: you are using a SQLITE3-Database!                                              *")
            print ("  *                                                                                      *")
            print ("  ****************************************************************************************")
            tables = database.execute_query("SELECT name FROM sqlite_master WHERE type='table' and name like 'EMA_%';", {})
        for table in tables:
            if database.db == "mySQL":
                fields = database.execute_query("SHOW FIELDS FROM " + table[list(table.keys())[0]] + ";", {})
            elif database.db == "sqlite3":
                fields = database.execute_query("PRAGMA table_info('" + table[list(table.keys())[0]] + "');", {})
            tmpTable = dbTable.dBTable(table[list(table.keys())[0]], fields)
            self.dataTables[tmpTable.name] = tmpTable
        for table in self.dataTables:
            for foreignKey in self.dataTables[table].foreignKeys:
                self.dataTables[table].parentTables.append(self.dataTables[foreignKey[0][:-3].lower()])
                self.dataTables[foreignKey[0][:-3].lower()].childTables.append(self.dataTables[table])
        myDataConnector = dataConnector(self.dataTables, [], [], True)
        for table in self.dataTables:
            self.dataTables[table].createSQLs()
            loop = 0
            while loop < 10:
                try:
                    myDataConnector.getDataSQL(table, limit = "0")
                    loop = 10
                except (sqlite3.OperationalError, mysql.connector.errors.ProgrammingError, mysql.connector.errors.InterfaceError):
                    random.shuffle(self.dataTables[table].SQL["join"])
                    loop += 1
                    if loop == 10:
                        del self.dataTables[table].SQL
        myDataConnector.close()
        del myDataConnector
        self._is_running = True
        self.lastDataset = False
        self.workingDirectory = os.getcwd()
        self.cert = config["MAIN"]["SSL_Cert"]
        self.key = config["MAIN"]["SSL_Key"]
        
        self.app = Flask(config["MAIN"]["ServerName"], static_url_path='/static')
        self.app.config['BASIC_AUTH_FORCE'] = True
        self.app.secret_key = 'RSEFJW8piJSbmNNz2e0k-4i1huEd0ko_igHDCj1k'
        self.app.config['SESSION_TYPE'] = 'filesystem'
        self.app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(minutes=5)
        self.app.debug = config["MAIN"]["Debug"] == 'True' or config["MAIN"]["Debug"] == '1' or config["MAIN"]["Debug"] == 1
        self.app.config['SESSION_FILE_THRESHOLD'] = 100 
        Session(self.app)
        
        self.auth.verify_password_callback = self.verify_password
        self.host = config["MAIN"]["AllowedHost"]
        self.port = config["MAIN"]["Port"]
        self.add_all_endpoints()
        
    def run(self):
        def get_md5(filename):
            return hashlib.md5(pathlib.Path(filename).read_bytes()).hexdigest()
        if self.cert == "devel_cert.pem" or self.key == "devel_key.pem" or get_md5(self.cert) == "ccee4e3d627fa88216c79fdbf65ee447" or get_md5(self.key) == "3b817abb9d94f81037211709a63df348":
            print ("  ****************************************************************************************")
            print ("  *                                                                                      *")
            print ("  * WARNING: you are using developer SSH-Keys! Please generate a new Cert- and Key-File! *")
            print ("  *                                                                                      *")
            print ("  ****************************************************************************************")
        self.app.run(self.host, self.port, ssl_context=(self.cert, self.key), use_reloader=False)

    def add_all_endpoints(self):
        self.add_endpoint("/", "/", self.index)
        self.add_endpoint("/getDataset", "/getDataset", self.getDataset, ['POST', 'GET'])
        self.add_endpoint("/exists", "/exists", self.exists, ['POST'])
        #self.add_endpoint("/updateDataset", "/updateDataset", self.updateDataset, ['POST'])
        self.add_endpoint("/importFiles", "/importFiles", self.importFiles, ['POST', 'PUT'])
        self.add_endpoint("/exportFiles", "/exportFiles", self.exportFiles, ['POST'])
        self.add_endpoint("/importQuestionaere", "/importQuestionaere", self.importQuestionaere, ['POST', 'PUT'])
        self.add_endpoint("/createNewFeatureValue", "/createNewFeatureValue", self.createNewFeatureValue, ['POST'])
        self.add_endpoint("/saveFeatureValue", "/saveFeatureValue", self.saveFeatureValue, ['POST'])
        self.add_endpoint("/executeQuery", "/executeQuery", self.executeQuery, ['POST'])
        #self.add_endpoint("/deleteFeatureValues", "/deleteFeatureValues", self.deleteFeatureValues, ['POST'])
        self.add_endpoint("/close", "/close", self.close, methods=['POST'])
        #if self.app.debug:
        #    self.add_endpoint("/getDataSQL", "/getDataSQL", self.getDataSQL, ['POST'])
    
    def add_endpoint(self, endpoint = None, endpoint_name = None, handler = None, methods = None):
        self.app.add_url_rule(endpoint, endpoint_name, self.EndpointAction(handler), methods = methods)

    def verify_password(self, username, password):
        if "UserRights" in session.keys() and "user" in session["UserRights"].keys() and session["UserRights"]["user"]["login"] == username and session["UserRights"]["user"]["password"] == hashlib.sha224(password.encode('utf-8')).hexdigest():
            return True
        else:
            myDataConnector = dataConnector(self.dataTables, [], {}, True)
            session["UserRights"] = myDataConnector.getDataSet("usergroup", {"usergroup" : {"user" : {"login" : username, "password" : hashlib.sha224(password.encode('utf-8')).hexdigest()}}})
            myDataConnector.close()
            del myDataConnector
            if len(session["UserRights"]["usergroup"]) == 1:
                session.permanent = True
                session["UserRights"] = session["UserRights"]["usergroup"][0]
                session["UserRights"]["user"] = session["UserRights"]["user"][0]
                session["UserRights"]["user"]["isactive"] = session["UserRights"]["user"]["isactive"] and session["UserRights"]["isactive"]
                if session["UserRights"]["user"]["isactive"] == 0:
                    del session["UserRights"]
                    raise PermissionError("User is currently not activated!")
                return True
            else:
                del session["UserRights"]
                return False
            
    class EndpointAction(object):
        def __init__(self, action):
            self.action = action
        def __call__(self, *args):
            answer = self.action()
            if type(answer) is Response and type(answer.response) is list and b'Unauthorized Access' in answer.response:
                self.response = Response('Access denied', 401, {'WWW-Authenticate':'Basic realm="Login Required"'})
            elif type(answer) is Response:
                self.response = answer
            else:
                self.response = Response(answer, status = 200, headers = {})
            #print(psutil.Process(os.getpid()).memory_info())
            gc.collect()
            return self.response

    # ==================== ------ API Calls ------- ====================

    def index(self):
        return render_template('index.html')

    @auth.login_required
    def getDataset(self):
        try:
            if "downloadFileList" in session.keys():
                del session["downloadFileList"]
            returnData = {}
            inputData = []
            if request.args.get("data"):
                inputData = json.loads(request.args.get("data"))
            elif request.is_json:
                inputData = request.get_json()
            conditions = False
            if "CONDITIONS" in inputData and type(inputData["CONDITIONS"]) is dict:
                conditions = inputData["CONDITIONS"]
            if "TABLENAME" in inputData and (str(inputData["TABLENAME"]).lower() == "featureset" or (str(inputData["TABLENAME"]).lower() in self.dataTables.keys() and not str(inputData["TABLENAME"]).lower() in self.forbiddenTables)):
                myDataConnector = dataConnector(self.dataTables, self.forbiddenTables, session["UserRights"])
                if myDataConnector.isFlatCondtitions(conditions):
                    conditions = myDataConnector.expandFlatCondtitions(conditions, self.dataTables[inputData["TABLENAME"]])
                returnData = myDataConnector.getDataSet(str(inputData["TABLENAME"]), conditions)
                if (request.method == "GET"):
                    xmlDocument = "empty"
                    if "TABLENAME" in inputData and type(inputData["TABLENAME"]) is str and inputData["TABLENAME"] != "":
                        xmlDocument = inputData["TABLENAME"]
                    return Response(json2xml.Json2xml({xmlDocument : returnData}).to_xml(), mimetype='text/xml')
                else:
                    session["lastConditions"] = conditions
                    session["lastDataset"] = myDataConnector.lastDataset
                myDataConnector.close()
                del myDataConnector
            return json.dumps(returnData)
        except Exception as e:
            if self.app.debug:
                traceback.print_exc()
            return Response(str(e) + "\n\tEMA-Server encountered this error!", status = 500, headers = {})
    
    @auth.login_required
    def exists(self):
        try:
            if "downloadFileList" in session.keys():
                del session["downloadFileList"]
            returnData = False
            if request.is_json:
                inputData = request.get_json()
                conditions = False
                myDataConnector = dataConnector(self.dataTables, self.forbiddenTables, session["UserRights"])
                if "CONDITIONS" in inputData and type(inputData["CONDITIONS"]) is dict:
                    conditions = inputData["CONDITIONS"]
                if "TABLENAME" in inputData and str(inputData["TABLENAME"]).lower() in self.dataTables.keys() and not str(inputData["TABLENAME"]).lower() in self.forbiddenTables:
                    if myDataConnector.isFlatCondtitions(conditions):
                        conditions = myDataConnector.expandFlatCondtitions(conditions, self.dataTables[inputData["TABLENAME"]])
                    returnData = myDataConnector.exists(str(inputData["TABLENAME"]), conditions)
                if type(inputData) is dict:
                    returnData = {}
                    for subject in inputData:
                        for file in inputData[subject]:
                            if not myDataConnector.exists("file", {"file": {"subject": subject, "filename": os.path.basename(file)}}):
                                if not subject in returnData.keys():
                                    returnData[subject] = []
                                returnData[subject].append(file)
                myDataConnector.close()
                del myDataConnector
            if type(returnData) is bool:
                return str(returnData)
            else:
                return json.dumps(returnData)
        except Exception as e:
            if self.app.debug:
                traceback.print_exc()
            return Response(str(e) + "\n\tEMA-Server encountered this error!", status = 500, headers = {})
          
    @auth.login_required
    def importFiles(self):
        try:
            if "downloadFileList" in session.keys():
                del session["downloadFileList"]
            returnData = True            
            if hasattr(request, 'form') and hasattr(request, 'files') and len(request.files) > 0:
                """
                if type(request.files) is dict and "zip" in request.files.keys():
                    tempFile = tempfile.NamedTemporaryFile(mode='w', delete=False)
                    open(tempFile.name, 'wb').write(request.files.content)
                    with zipfile.ZipFile(tempFile.name,"r") as zip_ref:
                        zip_ref.extractall(outputFolder)
                    tempFile.close()
                """
                myDataConnector = dataConnector(self.dataTables, self.forbiddenTables, session["UserRights"], timeout = 60 * 10, readlOnly = False)
                data = json.loads(request.form["data"])
                for id in data:
                    try:
                        returnData = returnData and myDataConnector.importFiles(data[id], request.files[id])
                    except Exception as e:
                        return Response(str(e) + "\n\tEMA-Server encountered this error!", status = 500, headers = {})
                        #if self.app.debug:
                        #    traceback.print_exc()
                        #returnData = False
                myDataConnector.close()
                del myDataConnector
            return str(returnData)
        except Exception as e:
            if self.app.debug:
                traceback.print_exc()
            return Response(str(e) + "\n\tEMA-Server encountered this error!", status = 500, headers = {})
    
    @auth.login_required
    def exportFiles(self):
        myDataConnector = None
        tempFile = None
        try:
            if request.is_json:
                inputData = request.get_json()
                myDataConnector = dataConnector(self.dataTables, self.forbiddenTables, session["UserRights"])
                os.chdir(myDataConnector.FeatureFilesFolder)
                if type(inputData) is list:
                    if "downloadFileList" in session.keys():
                        del session["downloadFileList"]
                    returnData = myDataConnector.exportFiles(inputData).copy()
                    return Response(json.dumps(returnData), status = 201, headers = {})
                if type(inputData) is dict and "loadnext" in inputData.keys():
                    if type(inputData["loadnext"]) is list:
                        session["downloadFileList"] = inputData["loadnext"].copy()
                    if "downloadFileList" in session.keys() and len(session["downloadFileList"]) > 0:
                        count = 0
                        datasize = 0
                        tempFile = tempfile.NamedTemporaryFile(mode='w', delete=False)
                        zipf = zipfile.ZipFile(tempFile.name, 'w', zipfile.ZIP_DEFLATED)
                        for idx in reversed(range(len(session["downloadFileList"]))):
                            datasize += os.path.getsize(session["downloadFileList"][idx])
                            with open(session["downloadFileList"][idx], mode='rb') as file:
                                compressed_data = file.read()
                            zipf.writestr(session["downloadFileList"][idx], zlib.decompress(compressed_data))
                            #zipf.write(session["downloadFileList"][idx])
                            del session["downloadFileList"][idx]
                            count += 1
                            if datasize >= 500000000 or count >= 1000:
                                break
                        zipf.close()
                        if len(session["downloadFileList"]) == 0:
                            del session["downloadFileList"]
                        return send_file(tempFile.name, mimetype = 'zip', attachment_filename= 'tmp.zip', as_attachment = True)
            return Response(str(False), status = 204, headers = {})
        except Exception as e:
            if self.app.debug:
                traceback.print_exc()
            return Response(str(e) + "\n\tEMA-Server encountered this error!", status = 500, headers = {})
        finally:
            if tempFile != None:
                tempFile.close()
            os.chdir(self.workingDirectory)
            if myDataConnector != None:
                myDataConnector.close()
                del myDataConnector
    
    @auth.login_required
    def importQuestionaere(self):
        try:
            if "downloadFileList" in session.keys():
                del session["downloadFileList"]
            returnData = True            
            if hasattr(request, 'form') and hasattr(request, 'files') and len(request.files) > 0:
                myDataConnector = dataConnector(self.dataTables, self.forbiddenTables, session["UserRights"], timeout = 60 * 5, readlOnly = False)
                data = json.loads(request.form["data"])
                for id in data:
                    try:
                        returnData = returnData and myDataConnector.importQuestinares(data[id], request.files[id].read().decode("utf-8"))
                    except:
                        if self.app.debug:
                            traceback.print_exc()
                        returnData = False
                myDataConnector.close()
                del myDataConnector
            return str(returnData)
        except Exception as e:
            if self.app.debug:
                traceback.print_exc()
            return Response(str(e) + "\n\tEMA-Server encountered this error!", status = 500, headers = {})
    
    @auth.login_required
    def createNewFeatureValue(self):
        try:
            if "downloadFileList" in session.keys():
                del session["downloadFileList"]
            returnData = {}
            if request.is_json:
                inputData = request.get_json()
                if "Feature" in inputData and type(inputData["Feature"]) is str:
                    myDataConnector = dataConnector(self.dataTables, self.forbiddenTables, session["UserRights"])
                    returnData = myDataConnector.createNewFeatureValue(inputData["Feature"])
                    myDataConnector.close()
                    del myDataConnector
            if returnData is None or len(returnData) == 0:
                raise ValueError("Creating new Value not possible! Feature missing oder invalid!")
            return json.dumps(returnData)
        except Exception as e:
            if self.app.debug:
                traceback.print_exc()
            return Response(str(e) + "\n\tEMA-Server encountered this error!", status = 500, headers = {})
    
    @auth.login_required
    def saveFeatureValue(self):
        try:
            if "downloadFileList" in session.keys():
                del session["downloadFileList"]
            returnData = False
            if request.is_json:
                inputData = request.get_json()
                if "Value" in inputData and type(inputData["Value"]) is dict or type(inputData["Value"]) is list:
                    myDataConnector = dataConnector(self.dataTables, self.forbiddenTables, session["UserRights"], readlOnly = False)
                    returnData = myDataConnector.saveFeatureValue(inputData["Value"])
                    myDataConnector.close()
                    del myDataConnector
            return str(returnData)
        except Exception as e:
            if self.app.debug:
                traceback.print_exc()
            return Response(str(e) + "\n\tEMA-Server encountered this error!", status = 500, headers = {})
        
    @auth.login_required
    def executeQuery(self):
        try:
            if request.is_json:
                inputData = request.get_json()
                if "COMMAND" in inputData and type(inputData["COMMAND"]) is str: 
                    inputData["COMMAND"] = str(inputData["COMMAND"]).strip()
                    if inputData["COMMAND"].lower().startswith("select ") and "select" not in inputData["COMMAND"][1:].lower()  and not "update" in inputData["COMMAND"].lower() and not "delete" in inputData["COMMAND"].lower() and not "insert" in inputData["COMMAND"].lower() and not "create" in inputData["COMMAND"].lower() and not "alter" in inputData["COMMAND"].lower() and not "drop" in inputData["COMMAND"].lower():
                        if not ";" in inputData["COMMAND"]:
                            inputData["COMMAND"] += ";"
                        inputData["COMMAND"] = inputData["COMMAND"][:inputData["COMMAND"].index(";")]
                        myDataConnector = dataConnector(self.dataTables, self.forbiddenTables, session["UserRights"])
                        returnData = json.dumps(myDataConnector.database.execute_query(inputData["COMMAND"], {}))
                        myDataConnector.close()                
                        return str(returnData)
        except Exception as e:
            return Response(str(e) + "\n\tEMA-Server encountered this error!", status = 500, headers = {})
    """            
    @auth.login_required
    def getDataSQL(self):
        try:
            if "downloadFileList" in session.keys():
                del session["downloadFileList"]
            returnData = {}
            if request.is_json:
                inputData = request.get_json()
                if "TABLE" in inputData and "WHERE" in inputData and str(inputData["TABLE"]).lower() in self.dataTables.keys() and not str(inputData["TABLE"]).lower() in self.forbiddenTables and hasattr(self.dataTables[str(inputData["TABLE"]).lower()], "SQL"):
                    myDataConnector = dataConnector(self.dataTables, self.forbiddenTables, session["UserRights"])
                    returnData = myDataConnector.getDataSQL(str(inputData["TABLE"]).lower(), str(inputData["WHERE"]))
            return json.dumps(returnData)
        except Exception as e:
            if self.app.debug:
                traceback.print_exc()
            return Response(str(e) + "\n\tEMA-Server encountered this error!", status = 500, headers = {})
    """

    """
    @auth.login_required
    def updateDataset(self):
        try:
            if "downloadFileList" in session.keys():
                del session["downloadFileList"]
            returnData = {}
            if request.is_json and "lastDataset" in session.keys():
                inputData = request.get_json()
                if type(inputData) is list:
                    inputData = {list(session["lastDataset"].keys())[0] : inputData}
                    myDataConnector = dataConnector(self.dataTables, self.forbiddenTables, session["UserRights"])
                    tablename = myDataConnector.updateDataSet(inputData[list(session["lastDataset"].keys())[0]], session["lastDataset"])
                    returnData = myDataConnector.getDataSet(tablename, session["lastConditions"])
                    myDataConnector.close()
                    del myDataConnector
            return json.dumps(returnData)
        except Exception as e:
            if self.app.debug:
                traceback.print_exc()
            return Response(str(e) + "\n\tEMA-Server encountered this error!", status = 500, headers = {})
    """

    """
    @auth.login_required
    def deleteFeatureValues(self):
        try:
            if "downloadFileList" in session.keys():
                del session["downloadFileList"]
            returnData = {}
            if request.is_json:
                inputData = request.get_json()
                myDataConnector = dataConnector(self.dataTables, self.forbiddenTables, session["UserRights"])
                if "confirmDataset" in session.keys():
                    myDataConnector.lastDataset = session["confirmDataset"]
                    del session["confirmDataset"]
                elif "lastDataset" in session.keys():
                    myDataConnector.lastDataset = session["lastDataset"]
                    del session["lastDataset"]
                if "deletehash" in session.keys():
                    myDataConnector.deletehash = session["deletehash"]
                    del session["deletehash"]
                if type(inputData) is list:
                    returnData = myDataConnector.deleteFeatureValues(inputData)
                if not "confirmDataset" in session.keys():
                    session["confirmDataset"] = myDataConnector.lastDataset
                if not "deletehash" in session.keys():
                    session["deletehash"] = myDataConnector.deletehash
                myDataConnector.close()
                del myDataConnector
            return json.dumps(returnData)
        except Exception as e:
            if self.app.debug:
                traceback.print_exc()
            return Response(str(e) + "\n\tEMA-Server encountered this error!", status = 500, headers = {})
    """
    
    @auth.login_required
    def close(self):
        try:
            session.clear()
            session["UserRights"] = None 
            return Response("", status = 200, headers = {})
        except Exception as e:
            if self.app.debug:
                traceback.print_exc()
            return Response(str(e) + "\n\tEMA-Server encountered this error!", status = 500, headers = {})

if __name__ == "__main__":
    exec(open("../main.py").read())