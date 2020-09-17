"""
This Python app will read the Input file list of Physical Build servers
and then search the CM Scripts SVN repository looking for reference to those
servers in the Build.ENV files and then output a list of the Products/Versions
that use the various Physical Build servers.
"""

# Load the required imports
import configparser
import csv
import json
import logging  # For basic logging of WebClient
import sys
from os import name, path, system

import requests
from suds.client import Client
from suds.wsse import Security, UsernameToken

# Define Gobal Variables
ConfigFileName = "CoverityCreateUser.cfg"

defectSvcClient = ""
configSvcClient = ""

logging.basicConfig()
# Uncomment to debug SOAP XML
# logging.getLogger('suds.client').setLevel(logging.DEBUG)
# logging.getLogger('suds.transport').setLevel(logging.DEBUG)


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
        raise Exception("FAILURE: Either section [" + section + "] or option [" + option + "] was NOT found in config file so fail.")


def LoadConfigurationInfo():
    """Method used to load the configuration settings from the ConfigFileName file.
    Returns True if all is successful or False if there were issues reading in the properties."""
    global covUser
    global covPass
    global covServer
    global covPort

    if (path.exists(ConfigFileName)):
        print("Configuration file found so loading configuration...")
        print ("")

        try:
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
            return True
        except Exception as ex:
            print (ex)
            return False

    else:
        print("FAILURE: Configuration file NOT found so failing")
        return False


def InitDefectClient():
    """Method used to initialize the DefectServiceClient and connect to the Coverity server."""

    global defectSvcClient

    print ("")
    print ("Setting up the Defect Service Client...")

    defectSvcClient = DefectServiceClient(covServer, covPort, True, covUser, covPass)


def InitConfigClient():
    """Method used to initialize the ConfigServiceClient and connect to the Coverity server."""

    global configSvcClient

    print ("")
    print ("Setting up the Configuration Service Client...")

    configSvcClient = ConfigServiceClient(covServer, covPort, True, covUser, covPass)


def SearchByUsername(usernameToSearchFor):
    """Method used to search for a specified user in the list of all Coverity users.
    
    NOTE: You can use wildcards like *mtol* to find the user."""

    if (defectSvcClient == ""):
        InitDefectClient()
    
    if (configSvcClient == ""):
        InitConfigClient()

    print ("")
    print ("Searching for user: " + usernameToSearchFor)

    if (configSvcClient != "" and defectSvcClient != ""):
        userIdDO = configSvcClient.client.factory.create('userFilterSpecDataObj')
        userIdDO.namePattern = usernameToSearchFor
        pageSpecDO = defectSvcClient.client.factory.create('pageSpecDataObj')
        pageSpecDO.pageSize=10
        pageSpecDO.startIndex=0

        v = configSvcClient.client.service.getUsers(userIdDO, pageSpecDO)

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
            print ("WARNING: User [" + usernameToSearchFor + "] was NOT found.")
            return False
    else:
        if (configSvcClient == ""):
            print ("FAILURE: Configuration Service Client NOT initialized so fail.")
        
        if (defectSvcClient == ""):
            print ("FAILURE: Defect Service Client NOT initialized so fail.")

        raise Exception("FAILURE: Required Service Client was NOT initialized so failing.")


def GetUserInfo(userToGet):
    """Method to get the specified user information from Coverity."""

    if (configSvcClient == ""):
        InitConfigClient()

    if (configSvcClient != ""):
        print ("")
        print("Searching for user: " + userToGet)

        v = configSvcClient.client.service.getUser(userToGet)

        print ("   Username : " + str(v.username))
        print ("   Domain   : " + str(v.domain.name))
        print ("   Email    : " + str(v.email))
        print ("   Groups   : " + str(v.groups))
    else:
        print ("")
        print ("FAILURE: Configuration Service Client NOT initialized so fail.")
        raise Exception("FAILURE: Required Service Client was NOT initialized so failing.")


###################################################
# Main calls go here
###################################################

# Clear the Console
ClearScreen()

# Load up the configuration (MUST BE First)
if (LoadConfigurationInfo()):

    try:
        # Test getting a single user's information
        GetUserInfo("mtolson")

        # Try doing some searching of users
        if (SearchByUsername("tolsonm") == True):
            print ("Success!!!!!")

        if (SearchByUsername("*tolson*") == True):
            print ("Success!!!!!")

        if (SearchByUsername("*") == True):
            print ("Success!!!!!")
    except Exception as ex:
        print ("")
        print ("Something went wrong so existing. Exception: " + str(ex))

print ("Done.")
