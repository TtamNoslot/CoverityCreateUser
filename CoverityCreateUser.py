"""
This Python app will read the Input file list of Physical Build servers
and then search the CM Scripts SVN repository looking for reference to those
servers in the Build.ENV files and then output a list of the Products/Versions
that use the various Physical Build servers.
"""

# Load the required imports
import sys
import csv
from os import path, system, name
import configparser
import requests
import json
from suds.client import Client
from suds.wsse import Security, UsernameToken

# For basic logging
import logging

logging.basicConfig()
# Uncomment to debug SOAP XML
# logging.getLogger('suds.client').setLevel(logging.DEBUG)
# logging.getLogger('suds.transport').setLevel(logging.DEBUG)

# getFileContents result requires decompress and decoding
import base64, zlib

# Define Gobal Variables
ConfigFileName = "CoverityCreateUser.cfg"

defectServiceClient = ""
configServiceClient = ""


###################################################
# Class definitions
###################################################

# -----------------------------------------------------------------------------
class WebServiceClient:
    def __init__(self, webservice_type, host, port, ssl, username, password):
        url = ''
        if (ssl):
            url = 'https://' + host + ':' + port
        else:
            url = 'http://' + host + ':' + port
        if webservice_type == 'configuration':
            self.wsdlFile = url + '/ws/v9/configurationservice?wsdl'
        elif webservice_type == 'defect':
            self.wsdlFile = url + '/ws/v9/defectservice?wsdl'
        else:
            raise "unknown web service type: " + webservice_type

        self.client = Client(self.wsdlFile)
        self.security = Security()
        self.token = UsernameToken(username, password)
        self.security.tokens.append(self.token)
        self.client.set_options(wsse=self.security)

    def getwsdl(self):
        print(self.client)

# -----------------------------------------------------------------------------
class DefectServiceClient(WebServiceClient):
    def __init__(self, host, port, ssl, username, password):
        WebServiceClient.__init__(self, 'defect', host, port, ssl, username, password)

# -----------------------------------------------------------------------------
class ConfigServiceClient(WebServiceClient):
    def __init__(self, host, port, ssl, username, password):
        WebServiceClient.__init__(self, 'configuration', host, port, ssl, username, password)
    def getProjects(self):
        return self.client.service.getProjects()		

# -----------------------------------------------------------------------------

###################################################
# Functions definitions
###################################################

def ClearScreen():
    """Method to clear the Console screen for Windows/Linux systems."""
    if name == 'nt': 
        _ = system('cls') 
  
    # for mac and linux(here, os.name is 'posix') 
    else: 
        _ = system('clear') 

def ReadStrFromConfigFile(configfile, section, option):
    """Method used to read a string value from a config file and return the string"""
    print("   * Reading section [" + section + "] and option [" + option + "] from config file [" + configfile + "] ...")
    config = configparser.RawConfigParser()
    config.read(configfile)
    if (config.has_option(section, option)):
        return config.get(section, option, raw=True)
    else:
        print("FAILURE: Either the section specified or the option specified was NOT found in config file so fail.")
        sys.exit(1)


def LoadConfigurationInfo():
    """Method used to load the configuration settings from the ConfigFileName file."""
    global covUser
    global covPass
    global covServer
    global covPort

    if (path.exists(ConfigFileName)):
        print("Configuration file found so loading configuration...")
        print ("")

        covUser = ReadStrFromConfigFile(ConfigFileName, 'App Settings', 'CoverityUser')
        print ("      * Coverity Username : " + covUser)
        print ("")

        covPass = ReadStrFromConfigFile(ConfigFileName, 'App Settings', 'CoverityPassword')
        print ("      * Coverity Password : " + covPass)
        print ("")

        covServer = ReadStrFromConfigFile(ConfigFileName, 'App Settings', 'CoverityServer')
        print ("      * Coverity Server   : " + covServer)
        print ("")

        covPort = ReadStrFromConfigFile(ConfigFileName, 'App Settings', 'CoverityPort')
        print ("      * Coverity Port     : " + covPort)
        print ("")

        print ("Done Loading Configuration Settings")

    else:
        print("FAILURE: Configuration file NOT found so failing")
        sys.exit(1)


def InitDefectClient():
    """Method used to initialize the DefectServiceClient and connect to the Coverity server."""

    global defectServiceClient

    print ("Setting up the Defect Service Client...")

    defectServiceClient = DefectServiceClient(covServer, covPort, True, covUser, covPass)


def InitConfigClient():
    """Method used to initialize the ConfigServiceClient and connect to the Coverity server."""

    global configServiceClient

    print ("Setting up the Configuration Service Client...")

    configServiceClient = ConfigServiceClient(covServer, covPort, True, covUser, covPass)


def SearchUsers(userToSearchFor):
    """Method used to search for a specified user in the list of all Coverity users.
    
    NOTE: You can use wildcards like *mtol* to find the user."""

    print ("Searching for user: " + userToSearchFor)

    if (configServiceClient != "" and defectServiceClient != ""):
        userIdDO = configServiceClient.client.factory.create('userFilterSpecDataObj')
        userIdDO.namePattern = userToSearchFor
        pageSpecDO = defectServiceClient.client.factory.create('pageSpecDataObj')
        pageSpecDO.pageSize=10
        pageSpecDO.startIndex=0

        v = configServiceClient.client.service.getUsers(userIdDO, pageSpecDO)

        if (v.totalNumberOfRecords == 1):
            print ("   User was found. Username: " + str(v.users[0].username))
            return True
        elif (v.totalNumberOfRecords > 1):
            print ("------------------------------------------")
            print ("Total Users Found: " + str(v.totalNumberOfRecords))
            print ("------------------------------------------")
            print ("WARNING: Multiple Users were found as follows:")
            for u in v.users:
                print ("   Username: [" + str(u.username) + "]")
            print ("WARNING: Multiple Users were found.")
            return False
        else:
            print ("WARNING: User [" + userToSearchFor + "] was NOT found.")
            return False
    else:
        if (configServiceClient == ""):
            print ("FAILURE: Configuration Service Client NOT initialized so fail.")
        
        if (defectServiceClient == ""):
            print ("FAILURE: Defect Service Client NOT initialized so fail.")

        sys.exit(1)


def GetUser(userToGet):
    """Method to get the specified user information from Coverity."""

    if (configServiceClient != ""):
        print("Searching for user: " + userToGet)

        v = configServiceClient.client.service.getUser(userToGet)

        print ("   Username : " + str(v.username))
        print ("   Email    : " + str(v.email))
        print ("   Groups   : " + str(v.groups))
    else:
        print ("FAILURE: Configuration Service Client NOT initialized so fail.")
        sys.exit(1)


###################################################
# Main calls go here
###################################################

# Clear the Console
ClearScreen()

# Load up the configuration (MUST BE First)
LoadConfigurationInfo()

print ("")

# Connect to Coverity Server
InitDefectClient()
InitConfigClient()

print ("")
GetUser("mtolson")

print ("")
if (SearchUsers("tolsonm") == True):
    print ("Success!!!!!")

print ("")
if (SearchUsers("*tolson*") == True):
    print ("Success!!!!!")

print ("")
if (SearchUsers("*") == True):
    print ("Success!!!!!")

print ("Done.")