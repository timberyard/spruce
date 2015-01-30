# -------------------------------------------------------------------------------------------------------
# File: evertest_netcfg_client.py
# Author(s): HAUSWALD, Tom (EVB Everbase AG); RIEDEL, Jan (EVB Everbase AG)
# Last rev.: Jan 05, 2015
# -------------------------------------------------------------------------------------------------------
#                            .
#                           / \
#						   /   \
#						  /     \
#						 /		 \
#						/		  \
#					   /		   \
#					  /			    \
#					 /				 \
#					/				  \
#				   /				   \
#				  /_____________________\
#				 / \				   / \
#				/   \			      /	  \
#			   /	 \			     /	   \
#			  /		  \			    /	    \
#			 /		   \		   /	  	 \
#			/		    \	      /			  \
#		   /			 \	     /			   \
#		  /				  \	    /			    \
#		 /				   \   /			 	 \
#		/				    \ /	      everbase	  \
#	   /_____________________V_____________________\
#
# Client version of the Evertest Network Handling Script. Only allows access to functionality available on
# the Client Side and resolves local Paths accordingly. Refer to the Description in 
# evertest_netcfg_client.py for further detail.
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
EVERTEST_ROOT_PATH = "/mnt/scripts/"

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
def evertestNetworkDir():

	# Return the Path of the Configuration File residing on the Worker
	return EVERTEST_ROOT_PATH
# -------------------------------------------------------------------------------------------------------
# EOF evertestNetworkDir
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Constructs the Network Configuration (.xml) File's absolute Path from the specified Test Name.
# -------------------------------------------------------------------------------------------------------
# Params:
#	str testName
#		- The Name of the Test
# -------------------------------------------------------------------------------------------------------
def evertestGetNetconfPath(testName):

	# Return the Path of the Configuration File residing on the Worker
	return EVERTEST_ROOT_PATH + "/" + testName + ".net"
# -------------------------------------------------------------------------------------------------------
# EOF evertestGetNetconfPath
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Constructs the Test Network's Portmap File's absolute Path from the specified Test Name.
# -------------------------------------------------------------------------------------------------------
# Params:
#	str testName
#		- The Name of the Test
# -------------------------------------------------------------------------------------------------------
def evertestGetPortmapPath(testName):

	# Return the Path of the Portmap File residing on the Worker
	return EVERTEST_ROOT_PATH + "/" + testName + ".ports"
# -------------------------------------------------------------------------------------------------------
# EOF evertestGetNetconfPath
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the Subnet corresponding to the specified Test Name
# -------------------------------------------------------------------------------------------------------
def evertestGetTestSubnet(testName):

	root = xmltree.parse(evertestGetNetconfPath(testName)).getroot()
	for child in root:
		if(child.tag == "ip"):
			# Remove preceding '192.168.' and following '.1' of IP to obtain Subnet ID
			return int(child.get("address").replace("192.168.", "").replace(".1", ""))

	print("Error: Failed to find Test with TID '" & testName & "'")
	return -1 # Failed to find Test.
# -------------------------------------------------------------------------------------------------------
# EOF evertestGetTestSubnet
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the IP Address of an existing VM
# -------------------------------------------------------------------------------------------------------
def evertestGetVmIpAddr(testName, vmName):
	
	root = xmltree.parse(evertestGetNetconfPath(testName)).getroot()
	for node in root.iter():
		if(node.tag == "host"):
			if(node.get("name") == vmName):
				return node.get("ip")

	print "Could not find IP Address Entry for VM: { Name = " + vmName + " }"
	return "???.???.???.???"
# -------------------------------------------------------------------------------------------------------
# EOF evertestGetVmIpAddr
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the MAC Address of an existing VM
# -------------------------------------------------------------------------------------------------------
def evertestGetVmMacAddr(testName, vmName):
	
	root = xmltree.parse(evertestGetNetconfPath(testName)).getroot()
	for node in root.iter():
		if(node.tag == "host"):
			if(node.get("name") == vmName):
				return node.get("mac")

	print "Could not find Mac Address Entry for VM: { Name = " + vmName + " }"
	return "???.???.???.???"
# -------------------------------------------------------------------------------------------------------
# EOF evertestGetVmMacAddr
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the dedicated Port Number of the VM
# -------------------------------------------------------------------------------------------------------
def evertestGetVmPort(testName, vmName):
	
	root = xmltree.parse(evertestGetPortmapPath(testName)).getroot()
	for node in root.iter():
		if(node.tag == "entry"):
			if(node.get("name") == vmName):
				return int(node.get("port"))

	print "Could not find dedicated Port No. Entry for VM: { Name = " + vmName + " }"
	return "???.???.???.???"
# -------------------------------------------------------------------------------------------------------
# EOF evertestGetVmMacAddr
# -------------------------------------------------------------------------------------------------------