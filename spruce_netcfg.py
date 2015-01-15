# -------------------------------------------------------------------------------------------------------
# File: evertest-netcfg.py
# Author(s): HAUSWALD, Tom (EVB Everbase AG)
# Last rev.: Dec. 16, 2014 (Jan - Added EVERTEST_MONITOR_PORT variable)
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
# This Python module implements all functionality relevant to the configuration of libvirt VM networks 
# (also referred to as Domains). It provides routines to assign static IP and MAC addresses to the
# virtual machines and makes those retrievable by solely passing the VM's name string. When first setting
# up an Evertest Testcase Network, an XML file will be created inside the evertestNetworkDir() directory, this
# File will be used by libvirt (virsh) to configure the domain correspoinding to each newly created VM.
# In order to tell libvirt's DHCP server, which VM shall be addressable at which address, the user needs
# to register as many VMs in the configuration file as he requires in order to perform his testcase.
# During the latter execution of a testcase, each VM can be accessed from code by its name.
#
# IP- & MAC-addresses will be assigned according to the following pattern:
#
#		IP  := 192.168.s.n,
#		MAC := aa:bb:cc:dd:s:n,
#
#			where 's' corresponds to the ID of the subnet [1-255] that belongs to the current testcase and 
#			'n' is the ip no. of the respective virtual machine [2-254] assigned to the testcase. Both 's' 
#			and 'n' will be automatically determined upon the registration of a new testcase and or 
#			virtual machine. Either by incrementing these values or by finding a lower number not yet in 
#			use.
#
#	Issue: Every created VM has to have a assigned port for monitoring purposes -> Has to be fixed quick! (27.12.14)
#
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
# Checks whether a specific Command Line Argument was passed to Python. (--flag)
# -------------------------------------------------------------------------------------------------------
def shellFlag(flag):

	for cmdarg in sys.argv:
		if(cmdarg == "--" + flag):
			return 1
	return 0
# -------------------------------------------------------------------------------------------------------
# EOF shellFlag
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the Value assigned to a Command Line Parameter. (--param=value) 
# If no Value was passed in, the specified default will be returned.
# -------------------------------------------------------------------------------------------------------
def shellParam(param, default):

	for cmdarg in sys.argv:
		if(("--" + param + "=") in cmdarg):
			return int(cmdarg.replace(("--" + param + "="), ""))
	return default
# -------------------------------------------------------------------------------------------------------
# EOF shellFlag
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Suppress Debug Output?
EVERTEST_SILENT = shellFlag("silent")

# Is the Script currently running the Host Machine or a Worker VM?
# Use evertestSetClientLevel(level) to change Client Level.
EVERTEST_CLIENT_LEVEL_HOST 	 = 0
EVERTEST_CLIENT_LEVEL_WORKER = 1
EVERTEST_CLIENT_LEVEL = EVERTEST_CLIENT_LEVEL_HOST

# Evertest Root Directory on Host Machine
EVERTEST_HOST_ROOT_DIR = "/var/evertest"

# Directory in which the virtual Machine's Script and the current
# Test's Configuration File are stored
EVERTEST_WORKER_ROOT_DIR = "/mnt"

# Port on which incoming Files (sent via TCP) will be received
EVERTEST_TCP_FILE_PORT = 8021
EVERTEST_MONITOR_PORT = 8025

# Separation Line
SEPLN = "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"

# New Line (Blank)
NEWLN = "\n"
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Representation of a simple Test Scenario (Testcase)
# Members:
#			name 	- The Name of the Test, produces netcfg_name.xml
#			vmCount - Number of VMs required for this Test's Execution
#			
# -------------------------------------------------------------------------------------------------------
class Testcase(object):

	def __init__(self, name, vmCount):
		
		self.name 	 = name
		self.vmCount = vmCount
# -------------------------------------------------------------------------------------------------------
# EOF Testcase Class
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Creates an Indentation String of 'n' Layers.
# -------------------------------------------------------------------------------------------------------
def indent(n):

	indent_str = ""
	for i in range(0, n):
		indent_str += "  "
	return indent_str
# -------------------------------------------------------------------------------------------------------
# EOF indent
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Replaces all Occurences of 'search' in 'file' with 'replace'
# -------------------------------------------------------------------------------------------------------
def replaceAll(file, search, replace):

    for line in fileinput.input(file, inplace=1):
        if search in line:
            line = line.replace(search, replace)
        sys.stdout.write(line)
# -------------------------------------------------------------------------------------------------------
# EOF replaceAll
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the local Network Folder
# -------------------------------------------------------------------------------------------------------
def evertestNetworkDir():

	# Return the Path of the Configuration File residing on the Host
	if EVERTEST_CLIENT_LEVEL == EVERTEST_CLIENT_LEVEL_HOST:
		return EVERTEST_HOST_ROOT_DIR + "/net"

	# Return the Path of the Configuration File residing on the Worker
	else:
		if EVERTEST_CLIENT_LEVEL == EVERTEST_CLIENT_LEVEL_WORKER:
			return EVERTEST_WORKER_ROOT_DIR

	# Invalid Client Level
	print "Invalid Client Level: %d." % EVERTEST_CLIENT_LEVEL
	print "Set to EVERTEST_CLIENT_LEVEL_HOST / EVERTEST_CLIENT_LEVEL_WORKER!" 
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
def evertestNetworkXmlPath(testName):

	# Return the Path of the Configuration File residing on the Host
	if EVERTEST_CLIENT_LEVEL == EVERTEST_CLIENT_LEVEL_HOST:
		return EVERTEST_HOST_ROOT_DIR + "/net/netcfg_" + testName + ".xml"

	# Return the Path of the Configuration File residing on the Worker
	else:
		if EVERTEST_CLIENT_LEVEL == EVERTEST_CLIENT_LEVEL_WORKER:
			return EVERTEST_WORKER_ROOT_DIR + "/" + testName + ".net"

	# Invalid Client Level
	print "Invalid Client Level: %d." % EVERTEST_CLIENT_LEVEL
	print "Set to EVERTEST_CLIENT_LEVEL_HOST / EVERTEST_CLIENT_LEVEL_WORKER!" 	
# -------------------------------------------------------------------------------------------------------
# EOF evertestNetworkXmlPath
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Creates the (.xml) Configuration File for the specified Test that will be passed to virsh upon
# VM Slave Creation.
# -------------------------------------------------------------------------------------------------------
# Params:
#	str testName
#		- The Name of the Test, resulting XML File will be called netconf_'testName'.xml
#	int subnet [0-255]
#		- The Subnet ID, VMs will be registered as Childs of this Subnet as follows: 
#		  VM IP Address = 192.168.'subnet'.'vmid'
#		  Also the Network Bridge will be called virbr-'subnet'
# -------------------------------------------------------------------------------------------------------
def evertestCreateNetworkXml(testName, subnet):

	if EVERTEST_CLIENT_LEVEL != EVERTEST_CLIENT_LEVEL_HOST:
		print "Error: Client Level 'HOST' required in order to create new Networks!"
		return 

	path = evertestNetworkXmlPath(testName)
	print "Path of network xml: " + path

	if(os.path.isfile(path)):
		print "Network for Test is already configured! (TID = " + testName + ")" 
	else:
		xmlFile = open(path, "w+")
		xmlFile.write("<network>" + NEWLN)
		xmlFile.write(indent(1) + "<name>" + testName + "</name>" + NEWLN)
		xmlFile.write(indent(1) + "<bridge name=\"virbr%d\"" % subnet + "/>" + NEWLN)
		xmlFile.write(indent(1) + "<forward mode=\"nat\"/>" + NEWLN)
		xmlFile.write(indent(1) + "<ip address=\"192.168.%d.1\"" % subnet + " netmask=\"255.255.255.0\">" + NEWLN)
		xmlFile.write(indent(2) + "<dhcp>" + NEWLN)
		xmlFile.write(indent(3) + "<range start=\"192.168.%d.2\" end=\"192.168.%d.254\"/>" % (subnet, subnet) + NEWLN)
		xmlFile.write(indent(2) + "</dhcp>" + NEWLN)
		xmlFile.write(indent(1) + "</ip>" + NEWLN)
		xmlFile.write("</network>")
		xmlFile.close()

		if(not EVERTEST_SILENT):
			print SEPLN
			print "Created Network Configuration XML File for Evertest Network:\n\t Testname (TID) = " + testName + "\n\t Subnet = %d" % subnet + NEWLN
			print "Resulting VM IP Addresses will be 192.168.%d.[1-%d]" % (subnet, 254)
			print SEPLN
# -------------------------------------------------------------------------------------------------------
# EOF evertestCreateNetworkXml
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the Subnet corresponding to the specified Test Name
# -------------------------------------------------------------------------------------------------------
def evertestGetTestSubnet(testName):

	root = xmltree.parse(evertestNetworkXmlPath(testName)).getroot()
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
# Registers a VM in the Test's Network Configuration (.xml) File thus mapping its Name to a unique MAC and 
# IP Address.
# -------------------------------------------------------------------------------------------------------
# Params:
#	str testName
#		- Name of the Test, in that's Network the VM should be registered
#	str vmName
#		- Name of the virtual Machine to register
# -------------------------------------------------------------------------------------------------------
def evertestRegisterVm(testName, vmName):
	
	if EVERTEST_CLIENT_LEVEL != EVERTEST_CLIENT_LEVEL_HOST:
		print "Error: Client Level 'HOST' required in order to register Workers!"
		return

	# Number of the virtual Machine to register (IP will be 192.168.'subnet'.'vmNumber')
	vmNumber    = evertestRequestVmNumber(testName)
	subnet 	    = evertestGetTestSubnet(testName)
	macAddrBase = "aa:bb:cc:dd"
	vmIpAddr    = "192.168.%d.%d" % (subnet, vmNumber)
	newEntry    = "<host mac=\"" + macAddrBase + ":" + format(subnet, "02x") + ":" 
	newEntry   += format(vmNumber, "02x") + "\" "
	newEntry   += "name=\"" + vmName + "\" ip=\"" + vmIpAddr + "\"/>"

	replaceAll( evertestNetworkXmlPath(testName), 
		    indent(2) + "</dhcp>", 
		    indent(3) + newEntry + NEWLN + indent(2) + "</dhcp>" )
	
	if(not EVERTEST_SILENT):
		print "Successfully registered VM for current Test (TID = " + testName + "): { Name = " + vmName + " | IP = " + evertestGetVmIpAddr(testName, vmName) + " }"
# -------------------------------------------------------------------------------------------------------
# EOF evertestRegisterVm
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Unregisters a VM from the Test's Network Configuration (.xml) 
# -------------------------------------------------------------------------------------------------------
# Params:
#	str testName
#		- Name of the Test, in that's Network the VM should be registered
#	str vmName
#		- Name of the virtual Machine to register
# -------------------------------------------------------------------------------------------------------
def evertestUnregisterVm(testName, vmName):

	if EVERTEST_CLIENT_LEVEL != EVERTEST_CLIENT_LEVEL_HOST:
		print "Error: Client Level 'HOST' required in order to unregister Workers!"
		return

	subnet 	  = evertestGetTestSubnet(testName)
	vmMacAddr = evertestGetVmMacAddr(testName, vmName)
	vmIpAddr  = evertestGetVmIpAddr(testName, vmName)

	# Entry to search for in XML (that will be deleted)
	delEntry  = "<host mac=\"" + vmMacAddr + "\" "
	delEntry += "name=\"" + vmName + "\" ip=\"" + vmIpAddr + "\"/>"

	replaceAll( evertestNetworkXmlPath(testName),
		    indent(3) + delEntry + NEWLN + indent(2) + "</dhcp>",
		    "" )

	if(not EVERTEST_SILENT):
		print "Successfully unregistered VM from current Test (TID = " + testName + "):  { Name = " + vmName + " | IP = " + vmIpAddr + " }"
# -------------------------------------------------------------------------------------------------------
# EOF evertestUnregisterVm
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Removes the Network Configuration (.xml) File from the System, thus making Space for a new Domain 
# sitting in the same Subnet ID.
# -------------------------------------------------------------------------------------------------------
# Params:
#	set testName
#		- Name of the Test, that's corresponding Network shall be deleted
# -------------------------------------------------------------------------------------------------------
def evertestDestroyTestNetwork(testName):

	if EVERTEST_CLIENT_LEVEL != EVERTEST_CLIENT_LEVEL_HOST:
		print "Error: Client Level 'HOST' required in order to destroy Networks!"
		return

	os.remove(evertestNetworkDir() + "/netcfg_" + testName + ".xml")
# -------------------------------------------------------------------------------------------------------
# EOF evertestDestroyTestNetwork
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the IP Address of an existing VM
# -------------------------------------------------------------------------------------------------------
def evertestGetVmIpAddr(testName, vmName):
	
	root = xmltree.parse(evertestNetworkXmlPath(testName)).getroot()
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
	
	root = xmltree.parse(evertestNetworkXmlPath(testName)).getroot()
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
# Returns the lowest available Number for a new VM to register within the given Test's Network [2-254]
# -------------------------------------------------------------------------------------------------------
def evertestRequestVmNumber(testName):

	usedNums = []
	root = xmltree.parse(evertestNetworkXmlPath(testName)).getroot()
	
	# Find used VM Numbers
	for node in root.iter():
		if(node.tag == "host"):
			usedNums.append(int(node.get("ip").replace("192.168.%d." % evertestGetTestSubnet(testName), "")))
	
	# Search for lowest VM Number available 
	for num in range(2, 255):
		if(num not in usedNums):
			return num

	# All VM Numbers occupied!
	print "Error: All VM Spaces [2-%d] for this Testcase are already occupied!" % 254
	return -1
# -------------------------------------------------------------------------------------------------------
# EOF evertestRequestVmNumber
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Go through the Folder containing all existing Network Configurations and return the Number of Networks
# found.
# -------------------------------------------------------------------------------------------------------
def evertestGetTestCount():

	if EVERTEST_CLIENT_LEVEL != EVERTEST_CLIENT_LEVEL_HOST:
		print "Error: Client Level 'HOST' required in order to count active Tests!"
		return

	numTests = 0
	for configFile in os.listdir(evertestNetworkDir()):
		if(configFile.endswith(".xml")):
			numTests += 1
	return numTests
# -------------------------------------------------------------------------------------------------------
# EOF evertestGetTestCount
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Go through all existing Network Configuration Files in order to find the lowest Subnet ID not yet in
# use. [1-255]
# -------------------------------------------------------------------------------------------------------
def evertestRequestTestSubnet():

	subnetsUsed = []

	# Determine what Subnet IDs are in use yet
	for configFile in os.listdir(evertestNetworkDir()):
		if(configFile.endswith(".xml")):
			subnetsUsed.append(evertestGetTestSubnet(str(configFile).replace("netcfg_", "").replace(".xml", "")))
	
	# Find lowest unoccupied Subnet ID 
	for subnet in range(1, 254 + 1):
		if(subnet not in subnetsUsed):
			return subnet

	# Maximum No. of Subnets already in use
	print "Error: Max. Number of Subnets (%d) already in use!" % 254
	return -1
# -------------------------------------------------------------------------------------------------------
# EOF evertestRequestTestSubnet
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Creates a new libvirt Domain (Test Network) .xml-File that will be used open VM Creation.
# Subnet ID will be chosen automatically to be the lowest Subnet not yet in use.
# -------------------------------------------------------------------------------------------------------
def evertestSetupTestNetwork(testName):

	evertestCreateNetworkXml(testName, evertestRequestTestSubnet())
# -------------------------------------------------------------------------------------------------------
# EOF evertestSetupTestNetwork
# -------------------------------------------------------------------------------------------------------


# Enable Test Configuration Creation in HOST Mode
if EVERTEST_CLIENT_LEVEL == EVERTEST_CLIENT_LEVEL_HOST:

	TESTCNT  = shellParam("t", 0)    # No. of Test Networks to set up
	VMCNTMIN = shellParam("min", 0)  # Minimum No. of VMs to register per Test 
	VMCNTMAX = shellParam("max", 0)  # Maximum No. of VMs to register per Test
	CLEANUP  = shellFlag ("c")		 # Whether to delete Configuration Files after Execution

	for i in range(0, TESTCNT):
		evertestSetupTestNetwork("evertest-network-%d" % i)
		for j in range(random.randint(VMCNTMIN, VMCNTMAX)):
			evertestRegisterVm("evertest-network-%d" % i, "evertest-slave-%d" % j)
	print SEPLN

	# Cleanup after Test
	if CLEANUP:
		for i in range(0, TESTCNT):
			evertestDestroyTestNetwork("evertest-network-%d" % i)
		print "Cleaned up /var/evertest/net."

	if TESTCNT > 0:
		print "Done."