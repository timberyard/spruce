# -------------------------------------------------------------------------------------------------------
# This Python module implements all functionality relevant to the configuration of libvirt VM networks 
# (also referred to as Domains). It provides routines to assign static IP and MAC addresses to the
# virtual machines and makes those retrievable by solely passing the VM's name string. When first setting
# up an Evertest Testcase Network, an XML file will be created inside the networkDir() directory, this
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

# Evertest Root Directory on Host Machine
EVERTEST_ROOT_PATH = "/var/evertest"

# Start of valid Range of Ports to run VM processes on. (On Host Machine)
EVERTEST_VM_PORT_BASE = 1024;

# Separation Line
SEPLN = "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"

# New Line (Blank)
NEWLN = "\n"

# Ports to not assign to virtual Machines
EVERTEST_FORBIDDEN_PORTS = [ 1025, 1279, 8080 ]
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
def networkDir():

	# Return the Path of the Configuration File residing on the Host
	return EVERTEST_ROOT_PATH + "/net"
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

	# Return the Path of the Configuration File residing on the Host
	return "{}/net/netconf_{}.xml".format(EVERTEST_ROOT_PATH, testName)
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

	# Return the Path of the Portmap File residing on the Host
	return "{}/net/portmap_{}.xml".format(EVERTEST_ROOT_PATH, testName)
# -------------------------------------------------------------------------------------------------------
# EOF getNetconfPath
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
def createNetconfXml(testName, subnet):

	path = getNetconfPath(testName)

	if(os.path.isfile(path)):
		print "Network Configuration File for Test already exists! (TID = " + testName + ")" 
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
			print NEWLN + SEPLN
			print "Created Network Configuration XML File for Evertest Network:\n\t Testname (TID) = " + testName + "\n\t Subnet = %d" % subnet
			print "Configuration File will be stored as \"" + path + "\""
			print "VM IP-Address Range: 192.168.%d.[2-254]" % (subnet)
			print SEPLN + NEWLN
# -------------------------------------------------------------------------------------------------------
# EOF createNetconfXml
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Creates the (.xml) Portmap File for the specified Test that contains all mapped Port Numbers of each
# virtual machine registered in the Test Network.
# -------------------------------------------------------------------------------------------------------
# Params:
#	str testName
#		- The Name of the Test, resulting XML File will be called portmap_'testName'.xml
# -------------------------------------------------------------------------------------------------------
def createPortmapXml(testName):

	path = getPortmapPath(testName)
	subnet = getTestSubnet(testName)
	minPort = calculateMinPort(testName)
	maxPort = calculateMaxPort(testName)

	if(os.path.isfile(path)):
		print "Portmap File for Test Network already exists! (TID = " + testName + ")" 
	else:
		xmlFile = open(path, "w+")
		xmlFile.write("<portmap>\n</portmap>")
		xmlFile.close()

		if(not EVERTEST_SILENT):
			print NEWLN + SEPLN
			print "Created Network Portmap XML File for Evertest Network:\n\t Testname (TID) = " + testName + "\n\t Subnet = %d" % (subnet)
			print "Portmap File will be stored as \"" + path + "\""

			print "VM Port Range: %d-%d [containing %d forbidden Port(s)]" % (minPort, maxPort, maxPort - minPort + 1 - 253)
			print SEPLN + NEWLN
# -------------------------------------------------------------------------------------------------------
# EOF createPortmapXml
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
# Registers a VM in the Test's Network Configuration (.xml) File thus mapping its Name to a unique MAC and 
# IP Address.
# -------------------------------------------------------------------------------------------------------
# Params:
#	str testName
#		- Name of the Test, in that's Network the VM should be registered
#	str vmName
#		- Name of the virtual Machine to register
# -------------------------------------------------------------------------------------------------------
def registerVm(testName, vmName):

	# Number of the virtual Machine to register (IP will be 192.168.'subnet'.'vmNumber')
	vmNumber    = requestVmNumber(testName)
	subnet 	    = getTestSubnet(testName)
	macAddrBase = "aa:bb:cc:dd"
	vmIpAddr    = "192.168.%d.%d" % (subnet, vmNumber)
	vmPort      = requestVmPort(testName)

	# Update netconf_ File
	newEntry    = "<host mac=\"" + macAddrBase + ":" + format(subnet, "02x") + ":" 
	newEntry   += format(vmNumber, "02x") + "\" "
	newEntry   += "name=\"" + vmName + "\" ip=\"" + vmIpAddr + "\"/>"

	replaceAll( getNetconfPath(testName), 
		    indent(2) + "</dhcp>", 
		    indent(3) + newEntry + NEWLN + indent(2) + "</dhcp>" )
	
	# Update portmap_ File
	newEntry   = "<entry name=\"" + vmName + "\" port=\"%d\"/>" % (vmPort)

	replaceAll( getPortmapPath(testName),
			"</portmap>",
			indent(1) + newEntry + NEWLN + "</portmap>" )

	if(not EVERTEST_SILENT):
		print "Successfully registered VM for current Test (TID = " + testName + "): { Name = " + vmName + " | IP = " + getVmIpAddr(testName, vmName) + " | Port = %d }." % (vmPort)
# -------------------------------------------------------------------------------------------------------
# EOF registerVm
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
def unregisterVm(testName, vmName):

	subnet 	  = getTestSubnet(testName)
	vmMacAddr = getVmMacAddr(testName, vmName)
	vmIpAddr  = getVmIpAddr(testName, vmName)

	# Entry to search for in XML (that will be deleted)
	delEntry  = "<host mac=\"" + vmMacAddr + "\" "
	delEntry += "name=\"" + vmName + "\" ip=\"" + vmIpAddr + "\"/>"

	replaceAll( getNetconfPath(testName),
		    indent(3) + delEntry + NEWLN + indent(2) + "</dhcp>",
		    "" )

	if(not EVERTEST_SILENT):
		print "Successfully unregistered VM from current Test (TID = " + testName + "):  { Name = " + vmName + " | IP = " + vmIpAddr + " }"
# -------------------------------------------------------------------------------------------------------
# EOF unregisterVm
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Removes the Network Configuration (.xml) File from the System, thus making Space for a new Domain 
# sitting in the same Subnet ID.
# -------------------------------------------------------------------------------------------------------
# Params:
#	set testName
#		- Name of the Test, that's corresponding Network shall be deleted
# -------------------------------------------------------------------------------------------------------
def destroyTestNetwork(testName):

	print NEWLN + SEPLN + NEWLN + "Destroying Test Network: " + testName + "..."
	
	netconfPath = networkDir() + "/netconf_" + testName + ".xml"
	portmapPath = networkDir() + "/portmap_" + testName + ".xml"
	
	if(os.path.isfile(netconfPath)):
		os.remove(netconfPath)
		print "Deleted corresponding Configuration File: " + netconfPath 
	else:
		print "No Configuration File found!"
	
	if(os.path.isfile(portmapPath)):
		os.remove(portmapPath)
		print "Deleted corresponding Portmap File: " + portmapPath
	else:
		print "No Portmap File found!"

	print SEPLN + NEWLN
# -------------------------------------------------------------------------------------------------------
# EOF destroyTestNetwork
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


# -------------------------------------------------------------------------------------------------------
# Returns the lowest available Number for a new VM to register within the given Test's Network [2-254]
# -------------------------------------------------------------------------------------------------------
def requestVmNumber(testName):

	usedNums = []
	root = xmltree.parse(getNetconfPath(testName)).getroot()
	
	# Find used VM Numbers
	for node in root.iter():
		if(node.tag == "host"):
			usedNums.append(int(node.get("ip").replace("192.168.%d." % getTestSubnet(testName), "")))
	
	# Search for lowest VM Number available 
	for num in range(2, 255):
		if(num not in usedNums):
			return num

	# All VM Numbers occupied!
	print "Error: All VM Spaces [2-%d] for this Testcase are already occupied!" % 254
	return -1
# -------------------------------------------------------------------------------------------------------
# EOF requestVmNumber
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Go through the Folder containing all existing Network Configurations and return the Number of Networks
# found.
# -------------------------------------------------------------------------------------------------------
def getTestCount():

	numXmlFiles = 0
	for configFile in os.listdir(networkDir()):
		if(configFile.endswith(".xml")):
			numXmlFiles += 1
	return numXmlFiles / 2 # for each Test Network there are 2 xml Files (netconf_, portmap_)
# -------------------------------------------------------------------------------------------------------
# EOF getTestCount
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Go through all existing Network Configuration Files in order to find the lowest Subnet ID not yet in
# use. [1-255]
# -------------------------------------------------------------------------------------------------------
def requestTestSubnet():

	subnetsUsed = []

	# Determine what Subnet IDs are in use yet
	for configFile in os.listdir(networkDir()):
		if(configFile.startswith("netconf_") and configFile.endswith(".xml")):
			subnetsUsed.append(getTestSubnet(str(configFile).replace("netconf_", "").replace(".xml", "")))
	
	# Find lowest unoccupied Subnet ID 
	for subnet in range(1, 254 + 1):
		if(subnet not in subnetsUsed):
			return subnet

	# Maximum No. of Subnets already in use
	print "Error: Max. Number of Subnets (%d) already in use!" % 254
	return -1
# -------------------------------------------------------------------------------------------------------
# EOF requestTestSubnet
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Creates a new libvirt Domain (Test Network) .xml-File that will be used open VM Creation.
# Subnet ID will be chosen automatically to be the lowest Subnet not yet in use.
# -------------------------------------------------------------------------------------------------------
def setupTestNetwork(testName):

	createNetconfXml(testName, requestTestSubnet())
	createPortmapXml(testName)
# -------------------------------------------------------------------------------------------------------
# EOF setupTestNetwork
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Calculates the lower Boundary of the Port Number Range dedicated to the specified Test.
# -------------------------------------------------------------------------------------------------------
def calculateMinPort(testName):

	subnet = getTestSubnet(testName)
	minPort = EVERTEST_VM_PORT_BASE + (subnet - 1) * 253
	increase = 0

	# if forbidden ports exist before the start of the port range, move range to right
	for forbidden in EVERTEST_FORBIDDEN_PORTS:
		if(forbidden <= minPort):
			increase += 1

	return minPort + increase
# -------------------------------------------------------------------------------------------------------
# EOF calculateMinPort
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Calculates the upper Boundary of the Port Number Range dedicated to the specified Test.
# -------------------------------------------------------------------------------------------------------
def calculateMaxPort(testName):

	minPort = calculateMinPort(testName)
	maxPort = minPort + 252
	increase = 0

	# if forbidden ports exist before the start of the port range, move range to right
	for forbidden in EVERTEST_FORBIDDEN_PORTS:
		if(minPort <= forbidden and forbidden <= maxPort):
			increase += 1

	return maxPort + increase
# -------------------------------------------------------------------------------------------------------
# EOF calculateMinPort
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Find a free Port in the Range dedicated to the specified Test.
# -------------------------------------------------------------------------------------------------------
def requestVmPort(testName):

	minPort = calculateMinPort(testName)
	maxPort = calculateMaxPort(testName)
	
	usedPorts = []
	root = xmltree.parse(getPortmapPath(testName)).getroot()
	
	# Find used Port Numbers
	for node in root.iter():
		if(node.tag == "entry"):
			usedPorts.append(int(node.get("port")))

	# Search for lowest Port Number available
	for port in range(minPort, maxPort + 1):
		if(port not in usedPorts and port not in EVERTEST_FORBIDDEN_PORTS):
			return port

	# All Ports occupied!
	print "Error: All Ports in the valid Range of this Test Network are already occupied!"
	return -1
# -------------------------------------------------------------------------------------------------------
# EOF requestVmPort
# -------------------------------------------------------------------------------------------------------