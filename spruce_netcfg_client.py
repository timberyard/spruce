# -------------------------------------------------------------------------------------------------------
# Client version of the Evertest Network Handling Script, customized for the use on testing machines. 
#Only allows access to functionality available on the Client Side and resolves local Paths accordingly. 
#Refer to the Description in evertest_netcfg_client.py for further detail.
# -------------------------------------------------------------------------------------------------------


# File I/O
import os
import sys
import string
import fileinput

# XML Parsing
import lxml 
from lxml import etree as xmltree

# RNG
import random

# -------------------------------------------------------------------------------------------------------
# Suppress Debug Output?
EVERTEST_SILENT = False

# Directory in which the virtual Machine's Script and the current
# Test's Configuration File are stored
EVERTEST_ROOT_PATH = "/mnt"

# Start of valid Range of Ports to run VM processes on. (On Host Machine)
EVERTEST_VM_PORT_BASE = 1024;

# Separation Line
SEPLN = "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"

# New Line (Blank)
NEWLN = "\n"
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the local Network Folder
# -------------------------------------------------------------------------------------------------------
def networkDir():

	# Return the Path of the Configuration File residing on the Worker
	return EVERTEST_ROOT_PATH
# -------------------------------------------------------------------------------------------------------
# EOF networkDir
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Constructs the Network Configuration (.xml) File's absolute Path from the specified Test Name.
# -------------------------------------------------------------------------------------------------------
# Params:
#	str testName
#		- The Name of the Test
# -------------------------------------------------------------------------------------------------------
def getNetconfPath(testName):

	# Return the Path of the Configuration File residing on the Worker
	return EVERTEST_ROOT_PATH + "/" + testName + ".net"
# -------------------------------------------------------------------------------------------------------
# EOF getNetconfPath
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Constructs the Test Network's Portmap File's absolute Path from the specified Test Name.
# -------------------------------------------------------------------------------------------------------
# Params:
#	str testName
#		- The Name of the Test
# -------------------------------------------------------------------------------------------------------
def getPortmapPath(testName):

	# Return the Path of the Portmap File residing on the Worker
	return EVERTEST_ROOT_PATH + "/" + testName + ".ports"
# -------------------------------------------------------------------------------------------------------
# EOF getNetconfPath
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the Subnet corresponding to the specified Test Name
# -------------------------------------------------------------------------------------------------------
def getTestSubnet(testName):

	root = xmltree.parse(getNetconfPath(testName)).getroot()
	for child in root:
		if(child.tag == "ip"):
			# Remove preceding '192.168.' and following '.1' of IP to obtain Subnet ID
			return int(child.get("address").replace("192.168.", "").replace(".1", ""))

	print("Error: Failed to find Test with TID '" & testName & "'")
	return -1 # Failed to find Test.
# -------------------------------------------------------------------------------------------------------
# EOF getTestSubnet
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the IP Address of an existing VM
# -------------------------------------------------------------------------------------------------------
def getVmIpAddr(testName, vmName):
	
	root = xmltree.parse(getNetconfPath(testName)).getroot()
	for node in root.iter():
		if(node.tag == "host"):
			if(node.get("name") == vmName):
				return node.get("ip")

	print "Could not find IP Address Entry for VM: { Name = " + vmName + " }"
	return "???.???.???.???"
# -------------------------------------------------------------------------------------------------------
# EOF getVmIpAddr
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the MAC Address of an existing VM
# -------------------------------------------------------------------------------------------------------
def getVmMacAddr(testName, vmName):
	
	root = xmltree.parse(getNetconfPath(testName)).getroot()
	for node in root.iter():
		if(node.tag == "host"):
			if(node.get("name") == vmName):
				return node.get("mac")

	print "Could not find Mac Address Entry for VM: { Name = " + vmName + " }"
	return "???.???.???.???"
# -------------------------------------------------------------------------------------------------------
# EOF getVmMacAddr
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the dedicated Port Number of the VM
# -------------------------------------------------------------------------------------------------------
def getVmMonitoringPort(testName, vmName, mode):
	
	root = xmltree.parse(getPortmapPath(testName)).getroot()
	if mode == "vm":
		for node in root.iter():
			if(node.tag == "entry"):
				if(node.get("name") == vmName):
					return int(node.get("port"))

	elif mode == "test":
		entry = root.find("entry")
		port = int(entry.get("port"))
		if port != 0:
			return port
		else:
			return "No port entry found."
	else:
		return "No mode given. Choose between 'vm' or 'test'side monitoring."

#	print "Could not find dedicated Port No. Entry for VM: { Name = " + vmName + " }"
#	return "???.???.???.???"
# -------------------------------------------------------------------------------------------------------
# EOF getVmMacAddr
# -------------------------------------------------------------------------------------------------------