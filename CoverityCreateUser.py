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
pageSizeToUse = 50

defectSvcClient = ""
configSvcClient = ""

logging.basicConfig()
# Uncomment to debug SOAP XML
# logging.getLogger('suds.client').setLevel(logging.DEBUG)
# logging.getLogger('suds.transport').setLevel(logging.DEBUG)

CoverityRoleList = []


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


def OverwriteConsoleOutput(stringToPrint):
    """Method to overwrite the console so it does not scroll off the page, like a progress bar so to speak."""
    sys.stdout.write("\r" + str(stringToPrint))
    sys.stdout.flush()


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
        pageSpecDO.sortAscending = True
        pageSpecDO.pageSize = pageSizeToUse
        pageSpecDO.startIndex = 0

        resultingUsers = configSvcClient.client.service.getUsers(userIdDO, pageSpecDO)

        if (resultingUsers.totalNumberOfRecords == 1):
            print ("   User was found. Username: " + str(resultingUsers.users[0].username))
            return True
        elif (resultingUsers.totalNumberOfRecords > 1):
            print ("   ------------------------------------------")
            print ("   Total Users Found: " + str(resultingUsers.totalNumberOfRecords))
            print ("   ------------------------------------------")
            print ("   WARNING: Multiple Users were found as follows:")
            for user in resultingUsers.users:
                print ("   Username: [" + str(user.username) + "]")
            print ("   WARNING: Multiple Users were found.")
            return False
        else:
            print ("   WARNING: User [" + usernameToSearchFor + "] was NOT found.")
            return False
    else:
        if (configSvcClient == ""):
            print ("FAILURE: Configuration Service Client NOT initialized so fail.")
        
        if (defectSvcClient == ""):
            print ("FAILURE: Defect Service Client NOT initialized so fail.")

        raise Exception("FAILURE: Required Service Client was NOT initialized so failing.")


def SearchByEmail(emailToSearchFor):
    """Method used to search for a specified email in the list of all Coverity users."""

    if (defectSvcClient == ""):
        InitDefectClient()
    
    if (configSvcClient == ""):
        InitConfigClient()

    print ("")
    print ("Searching for email: " + emailToSearchFor)

    if (configSvcClient != "" and defectSvcClient != ""):
        userIdDO = configSvcClient.client.factory.create('userFilterSpecDataObj')
        userIdDO.namePattern = "*"

        pageSpecDO = defectSvcClient.client.factory.create('pageSpecDataObj')
        pageSpecDO.sortAscending = True
        pageSpecDO.sortField = "email"

        # Call with a single record (pageSize = 1) to get fast and get the totalNumberOfRecords
        pageSpecDO.pageSize = 1
        pageSpecDO.startIndex = 0
        resultingUsers = configSvcClient.client.service.getUsers(userIdDO, pageSpecDO)

        print ("   Processing [" + str(resultingUsers.totalNumberOfRecords) + "] User records...")

        userFound = False
        userCount = 0
        if (resultingUsers.totalNumberOfRecords > 0):
            # Get FIRST batch of user records
            pageSpecDO.pageSize = pageSizeToUse
            pageSpecDO.startIndex = 0
            resultingUsers = configSvcClient.client.service.getUsers(userIdDO, pageSpecDO)

            while (hasattr(resultingUsers, 'users')):
                for user in resultingUsers.users:
                    userCount += 1
                    OverwriteConsoleOutput("   Processing # " + str(userCount))

                    if (hasattr(user, 'email') and str(user.email).lower() == emailToSearchFor.lower()):
                        print ("")
                        print ("      Email address FOUND.  Username: [" + str(user.username) + "]")
                        userFound = True
                        GetUserInfo(str(user.username))
                        break

                if (userFound):
                    break

                # Get NEXT batch of user records based on pageSizeToUse
                pageSpecDO.startIndex += pageSizeToUse
                resultingUsers = configSvcClient.client.service.getUsers(userIdDO, pageSpecDO)

        if (userFound):
            return True
        else:
            print ("")
            print ("   WARNING: Email [" + emailToSearchFor + "] was NOT found.")
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

        try:
            resultingUser = configSvcClient.client.service.getUser(userToGet)

            print ("-----------------------------------------------------------------")
            print ("   Username    : " + str(resultingUser.username))
            print ("   Domain      : " + str(resultingUser.domain.name))
            print ("   Email       : " + str(resultingUser.email))
            print ("   Groups      : " + str(resultingUser.groups))
            print ("   Disabled    : " + str(resultingUser.disabled))
            print ("   Locked      : " + str(resultingUser.locked))
            print ("   Created     : " + str(resultingUser.dateCreated))
            print ("   Who Created : " + str(resultingUser.userCreated))
            print ("-----------------------------------------------------------------")
        except Exception as ex:
            if ("No user found for user name " + userToGet + "." in str(ex)):
                print ("")
                print ("WARNING: User [" + userToGet + "] was NOT found.")
            else:
                raise Exception(ex)
    else:
        print ("")
        print ("FAILURE: Configuration Service Client NOT initialized so fail.")
        raise Exception("FAILURE: Required Service Client was NOT initialized so failing.")


def GetCoverityRolesFromServer(RoleToLoad):
    """Method to get the the Coverity Groups from the server.
    
    NOTE: You can use wildcards like Endpoint* or *Manager to find the Role."""

    if (defectSvcClient == ""):
        InitDefectClient()
    
    if (configSvcClient == ""):
        InitConfigClient()

    print ("")
    print ("   Loading Coverity Groups from server.")

    if (configSvcClient != "" and defectSvcClient != ""):
        groupIdDO = configSvcClient.client.factory.create('groupFilterSpecDataObj')
        groupIdDO.namePattern = RoleToLoad

        pageSpecDO = defectSvcClient.client.factory.create('pageSpecDataObj')
        # pageSpecDO.sortAscending = True
        # pageSpecDO.sortField = "name"
        pageSpecDO.pageSize = pageSizeToUse
        pageSpecDO.startIndex = 0

        resultingGroups = configSvcClient.client.service.getGroups(groupIdDO, pageSpecDO)

        if (resultingGroups.totalNumberOfRecords > 1):
            for group in resultingGroups.groups:
                if(str(group.name.name).lower() != "Users".lower()):
                    # print ("      Group: [" + str(group.name.name) + "]")
                    CoverityRoleList.append(group.name.name)
            CoverityRoleList.sort()
            return True
        else:
            print ("      WARNING: NO groups were found.")
            return False
    else:
        if (configSvcClient == ""):
            print ("FAILURE: Configuration Service Client NOT initialized so fail.")
        
        if (defectSvcClient == ""):
            print ("FAILURE: Defect Service Client NOT initialized so fail.")

        raise Exception("FAILURE: Required Service Client was NOT initialized so failing.")


def GetMaxStringLengthOfCoverityRole():
    """Method that will loop through CoverityRoleList looking for the max string length and return that."""
    maxLength = 0

    for role in CoverityRoleList:
        # print ("Role: " + str(role) + " Length: " + str(len(role)))
        if (len(role) > maxLength):
            maxLength = len(role)
    
    return maxLength


def PrintCoverityRolesList(numberOfColumns):
    """Method used to print out the complete list of Coverity Roles based on the nubmer of columns passed in."""

    # Should be max String length + 6 ([###] ) + 1 extra space = StrLength + 7
    paddingLength = GetMaxStringLengthOfCoverityRole() + 7

    print ("-------------------")
    print ("Coverity Roles List")
    print ("-------------------")

    printReturn = 0
    roleCount = 0
    for role in CoverityRoleList:
        print (str("[" + str(roleCount).rjust(3, '0') + "] " + str(role)).ljust(paddingLength, ' '), end='')
        roleCount += 1
        printReturn += 1
        if (printReturn >= numberOfColumns):
            printReturn = 0
            print ("")


def GetCoverityRoleFromUser(userBeingCreated):
    """Method to prompt and get the users Coverity Role and validate against CoverityRoleList list."""

    DoneAssigningRole = False
    while (DoneAssigningRole == False):
        RoleisValid = False
        RolesToUse = ["Users"]

        while (RoleisValid == False):
            ClearScreen()

            PrintCoverityRolesList(4)

            print ("----------------------------------------------------------------------------------")
            print ("Using the number in [] enter the ONE Coverity Role you want to add.")
            print ("NOTE: Users group is automatically added and you get ONE more you can add.")
            print ("----------------------------------------------------------------------------------")

            roleIDToAdd = input("Enter the Coverity Role Number for [" + userBeingCreated + "] (Enter when done): ")

            if (roleIDToAdd.lower() == "".lower()):
                break

            if(int(roleIDToAdd) <= len(CoverityRoleList)):
                if (CoverityRoleList[int(roleIDToAdd)] not in RolesToUse):
                    RolesToUse.append(CoverityRoleList[int(roleIDToAdd)])
                    RoleisValid = True
        
        print ("")
        print ("Assigned Roles: " + str(RolesToUse))
        print ("")
        areWeDone = input ("Does the above look correct (Y or N)? ")
        if (areWeDone.lower() == "Y".lower()):
            DoneAssigningRole = True

    return RolesToUse


def CreateCoverityUser(userToCreate):
    """Method to create a Coverity User."""

    if (configSvcClient == ""):
        InitConfigClient()

    if (configSvcClient != ""):
        print ("")
        print("Creating user: " + userToCreate)

        try:
            if ("@" in userToCreate and "." in userToCreate):
                userToCreate = input("Enter CORPZONE username to be created: ")
            
            userRole = GetCoverityRoleFromUser(userToCreate)
            # userRole.append("Users")

            domainIdDO = configSvcClient.client.factory.create('serverDomainIdDataObj')
            domainIdDO.name = "corpzone"

            groupIdDO = configSvcClient.client.factory.create('groupIdDataObj')
            groupIdDO.name = userRole

            userIdDO = configSvcClient.client.factory.create('userSpecDataObj')
            userIdDO.username = userToCreate
            userIdDO.domain = domainIdDO
            userIdDO.groupNames = groupIdDO
            
            configSvcClient.client.service.createUser(userIdDO)

            print ("   Created Username : " + userToCreate)
            GetUserInfo(userToCreate)

        except Exception as ex:
            print ("FAILURE: User [" + userToCreate + "] was NOT create successfully.  Exception: " + str(ex))
    else:
        print ("")
        print ("FAILURE: Configuration Service Client NOT initialized so fail.")
        raise Exception("FAILURE: Required Service Client was NOT initialized so failing.")


def PrintServerInfo():
    """Method used to print the Coverity information from the CFG file."""
    print ("")
    print ("-----------------------------------------------------------------")
    print ("Coverity Settings")
    print ("-----------------------------------------------------------------")
    print ("Server Name : " + covServer)
    print ("Server Port : " + covPort)
    print ("Server User : " + covUser)
    print ("-----------------------------------------------------------------")


###################################################
# Main calls go here
###################################################

# Clear the Console
ClearScreen()

# Load up the configuration (MUST BE First)
if (LoadConfigurationInfo()):

    try:
        PrintServerInfo()

        print ("")
        userToFind = input("Enter the username or email address you wish to find: ")

        userNeedsToBeCreated = True
        if (len(userToFind) > 0):
            if ("@" in userToFind and "." in userToFind):
                if(SearchByEmail(userToFind)):
                    print ("Found user via email address.")
                    userNeedsToBeCreated = False
            else:
                if (SearchByUsername(userToFind)):
                    print ("Found user via username.")
                    userNeedsToBeCreated = False
                    GetUserInfo(userToFind)

        if (userNeedsToBeCreated):
            print ("")
            print ("User was NOT found so creating user...")
            if(GetCoverityRolesFromServer("*")):
                if (len(CoverityRoleList) > 0):
                    CreateCoverityUser(userToFind)

    except Exception as ex:
        print ("")
        print ("Something went wrong so existing. Exception: " + str(ex))

print ("Done.")
