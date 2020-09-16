"""
This Python app will read the Input file list of Physical Build servers
and then search the CM Scripts SVN repository looking for reference to those
servers in the Build.ENV files and then output a list of the Products/Versions
that use the various Physical Build servers.
"""

# Load the required imports
import sys
import csv
import os.path
from os import path, system, name
import configparser


# Define Gobal Variables
ConfigFileName = "CoverityCreateUser.cfg"


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

    if (path.exists(ConfigFileName)):
        print("Configuration file found so loading configuration...")
        print ("")

        covUser = ReadStrFromConfigFile(ConfigFileName, 'App Settings', 'CoverityUser')
        print ("      * Coverity Username : " + covUser)
        print ("")

        covPass = ReadStrFromConfigFile(ConfigFileName, 'App Settings', 'CoverityPassword')
        print ("      * Coverity Password : " + covPass)
        print ("")

        print ("Doen Loading Configuration Settings")

    else:
        print("FAILURE: Configuration file NOT found so failing")
        sys.exit(1)


###################################################
# Main calls go here
###################################################

# Clear the Console
ClearScreen()

# Load up the configuration (MUST BE First)
LoadConfigurationInfo()

print ("Done.")