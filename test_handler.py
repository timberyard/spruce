# -------------------------------------------------------------------------------------------------------
# File: test_handler.py
# Author(s): RIEDEL, Jan (EVB Everbase AG)
# Last rev.: Dec. 12, 2014
# -------------------------------------------------------------------------------------------------------
#
#                                       /\
#                                      /  \
#									  /    \
#									 /      \
#									/		 \
#								   /		  \
#								  /____________\
#								/\ \          / /\
#							   /  \	\        / /  \
#							  /    \ \      / /    \
#							 /  	\ \    / /      \
#							/    	 \ \  / /		 \
#						   /__________\	\/ /__________\
#
# -------------------------------------------------------------------------------------------------------
#
# This Python module implements all main functionality relevant to the process of creating and managing VMs.
# It provides routines to create and start VMs out of the information captured from the used .test file.
# When the test handling process starts, all relevant information from the test is committed to a local Git
# repository. Then all the VMs are being created, their hostnames are set to the specified VM-name (in test
# config), they get IP and MAC addresses and are being started up. Every single test runs in its own virtual
# network so that all VMs in a test can communicate with each other. After startup the VMs get their test-
# scripts from the Git and run them automatically. When finished, logs are being committed to the repo.
# Notice: Some commands used in this python script are running in a unix based subshell because implementation
# for python is not integrated or available yet.
#
# The IP & MAC addresses will be assigned by evertest_netcfg.py [HAUSWALD, Tom (EVB Everbase AG)].
# The VMs are named in two ways:
# 	1. The name in Virt-Manager etc. ..
# 		- Either by incrementing the number after "evertest_vm_$number" or
#		- finding a lower number being not yet in use
# 	2. The name of the VM itself (used for networking and assigning testcases)
#		- Given by the testcase-author
#		- saved as the VM's hostname
#
# Functions used from evertest_netcfg module are:
#		- evertestSetupTestNetwork -> Setup the virtual network for the actual running test
#		- evertestRegisterVM -> Register new VMs to the virtual network
#		- evertestNetworkXmlPath -> Get network.xml's path
#		- evertestDestroyTestNetwork -> Remove the virtual network
#
# Implementations planned:
#							- whole running test (incl. VM startup-shutdown etc.) in process
#								-> when all processes from testcase end, remove network and VMs
#								 - maybe only when "accepted" in webUI
# -------------------------------------------------------------------------------------------------------


# File I/O
import sys
import os
import fileinput
import subprocess as sub
import git

#Tools
#import re
import shutil
import time
import libvirt
import tarfile
from lxml import etree as xmltree

from evertest_netcfg import *

#--------------------------------------------------------------------------------------
#Paths
#--------------------------------------------------------------------------------------
evertest_path_net   = "/var/evertest/net/"
evertest_path_tests = "/var/evertest/tests/"
evertest_path 		= "/var/evertest/tests/"
boarder       		= "~~~~~~~~~~"
# -------------------------------------------------------------------------------------
# EOF Paths
# -------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Set EVETEST_DEBUG_LEVEL TO - 0: Short debug message; 1: explicit debug message
#--------------------------------------------------------------------------------------
EVERTEST_DEBUG_LEVEL = 1
edl = EVERTEST_DEBUG_LEVEL
#--------------------------------------------------------------------------------------
# EOF Debug-Settings
#--------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the Value assigned to a Command Line Parameter. (--param=value) 
# If no Value was passed in, the specified default will be returned.
# -------------------------------------------------------------------------------------------------------
def shellParam2(param, default):

	for cmdarg in sys.argv:
		if(("--" + param + "=") in cmdarg):
			return str(cmdarg.replace(("--" + param + "="), ""))
	return default
# -------------------------------------------------------------------------------------------------------
# EOF shellFlag
# -------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Get the Test ID from the testconfig
#--------------------------------------------------------------------------------------
def evertestGetTestID(testname):
	try:
		path = "/var/evertest/tests/" + testname + "/" + testname + ".conf"
		root = xmltree.parse(path).getroot()
		for child in root:
			if(child.tag == "info"):
				value = child.get("id")
				return value
	except:
		e = sys.exc_info()[edl]
		print "Error in evertestGetTestID: \n" + str(e)
# -------------------------------------------------------------------------------------
# EOF get evertestGetTestID
# -------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Get the number of VMs to create from the testconfig
#--------------------------------------------------------------------------------------
def evertestGetNumber(testname):
	try:
		path = "/var/evertest/tests/" + testname + "/" + testname + ".conf"
		root = xmltree.parse(path).getroot()
		for child in root:
			if(child.tag == "info"):
				value = child.get("vmcount")
				return value
	except:
		e = sys.exc_info()[edl]
		print "Error in evertestGetNumber: \n" + str(e)
# -------------------------------------------------------------------------------------
# EOF evertestGetNumber
# -------------------------------------------------------------------------------------

		##### Whole part after here could be removed caused by import of "import from evertest_netcfg *"

#--------------------------------------------------------------------------------------
# Parse vmName to ip-API
#--------------------------------------------------------------------------------------
#def evertestRegisterVM(testID, hostname):
#	try:
#		exec("from " + "evertest_netcfg" + " import evertestRegisterVm")
#		evertestRegisterVm(testID, hostname)
#	except:
#		e = sys.exc_info()[0]
#		print "Error in evertestRegisterVM: \n" + str(e)
# -------------------------------------------------------------------------------------
# EOF evertestRegisterVM
# -------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Get Networkpath from ip-API
#--------------------------------------------------------------------------------------
#def evertestNetworkXmlPath(testID):
#	try:
#		exec("from " + "evertest_netcfg" + " import evertestNetworkXmlPath")
#		path = evertestNetworkXmlPath(testID)
#	except:
#		e = sys.exc_info()[0]
#		print "Error in evertestNetworkXmlPath: \n" + str(e)
#	return path
# -------------------------------------------------------------------------------------
# EOF evertestNetworkXmlPath
# -------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Removes the Network Configuration (.xml) file from the system, thus making space for
# domain sitting in the same subnet ID
#--------------------------------------------------------------------------------------
#def evertestDestroyTestNetwork(testname):
#	try:
#		exec("from " + "evertest_netcfg" + " import evertestDestroyTestNetwork")
#		evertestDestroyTestNetwork(testname)
#		string = "virsh net-destroy " + testname
#		t = sub.Popen(string, shell=True, stdout=sub.PIPE)
#		t.wait()
#	except:
#		e = sys.exc_info()[0]
#		print "Error in evertestDestroyTestNetwork: \n" + str(e)
# -------------------------------------------------------------------------------------
# EOF evertestDestroyTestNetwork
# -------------------------------------------------------------------------------------

		##### Eo replaceable part

#--------------------------------------------------------------------------------------
# Place own mac and network name in VM xml
#--------------------------------------------------------------------------------------
def evertestConfigureVMNetwork(testID, vmname, hostname):
	try:
#		exec("from " + "evertest_netcfg" + " import evertestGetVmMacAddr") 
		mac = evertestGetVmMacAddr(testID, hostname)
		netName = testID
		openString = "/etc/libvirt/qemu/" + vmname +".xml"
		macString = "<mac address='" + mac + "'/>\n"
		networkString = "<source network='" + testID + "'/>\n"
		defineVM = "virsh define /etc/libvirt/qemu/" + vmname + ".xml"
		for line in fileinput.input(openString, inplace=True):
			print line.replace("<mac address='", macString),
		for line in fileinput.input(openString, inplace=True):
			print line.replace("<source network=", networkString),
		define = sub.Popen(defineVM, shell=True, stdout=sub.PIPE)
		define.wait()
	except:
		e = sys.exc_info()[edl]
		print "Error in evertestConfigureVMNetwork: \n" + str(e)
# -------------------------------------------------------------------------------------
# EOF evertestConfigureVMNetwork
# -------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Add .test (archive containing config and scripts) to local Git repository
#--------------------------------------------------------------------------------------
#def evertestAddTest(testname):
#	try:
#		folder = "/var/evertest/tests/" + testname + "/"
#		repo = git.Repo("/var/evertest/tests/")
#		repo.git.add(folder)
#	except:
#		e = sys.exc_info()[edl]
#		print "Error in evertestAddTest: \n" + str(e)
#--------------------------------------------------------------------------------------
# EOF evertestAddTest
#--------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Commit tests to local Git repository	---> commit after every creation of a new vm
#--------------------------------------------------------------------------------------
#def evertestCommitTest(testname):
#	try:
#		commitMsg = "Committed new test: " + testname
#		repo = git.Repo('/var/evertest/tests/')
#		repo.git.commit(m=commitMsg)
#	except:
#		e = sys.exc_info()[edl]
#		print "Error in evertestCommitTest: \n" + str(e)
#--------------------------------------------------------------------------------------
# EOF evertestCommitTest
#--------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------
# Unzip the .test.tar file
#--------------------------------------------------------------------------------------
def evertestExtractTest(testname):
	try:
		extractString = "/var/evertest/tests/" + testname + ".test"
		extractPath = "/var/evertest/tests/" + testname + "/"
		tfile = tarfile.open(extractString)
		if tarfile.is_tarfile(extractString):
			tfile.extractall(extractPath)
		else:
			print extractString + " is not a tarfile." 
	except:
		e = sys.exc_info()[edl]
		print "Error in evertestExtractTest: \n" + str(e)
#--------------------------------------------------------------------------------------
# EOF evertestExtractTest
#--------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Send the test files to the VM via ssh
#--------------------------------------------------------------------------------------
def evertestSendTest(vmname, testname):
	try:
		vmip = evertestGetVmIpAddr(testname, vmname)
		filename = "/var/evertest/tests/" + testname + ".test"
		os.system("scp " + filename + " tester@" + vmip + ":/mnt/" + testname + ".test")
		filename = "/var/evertest/net/netcfg_" + testname + ".xml"
		os.system("scp " + filename + " tester@" + vmip + ":/mnt/" + testname + ".net")
		print boarder
	except:
		e = sys.exc_info()[edl]
		print "Error occoured in evertestSendTest: \n" + str(e)
#--------------------------------------------------------------------------------------
# EOF evertestSendTest
#--------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Construct the new VM(s)
#--------------------------------------------------------------------------------------
def evertestConstructVM(templateID, hostname, testID):
	try:
		# Create VM by increasing (or picking the lowest unused) the number in "evertest_vm_$number" for VMNames
		creationIndex = 1
		string = "virt-clone -o everbaseTemplate_" + templateID + " -n evertest_vm_" + str(creationIndex) + " -f /var/lib/libvirt/images/evertest_vm_" + str(creationIndex) + ".img"
		o = sub.Popen(string, shell=True, stdout=sub.PIPE, stderr=sub.STDOUT)
		o.wait()
		if o.returncode == 1:				
			newIndex = 2
			status = 1
			while status != 0:
				string = "virt-clone -o everbaseTemplate_" + templateID + " -n evertest_vm_" + str(newIndex) + " -f /var/lib/libvirt/images/evertest_vm_" + str(newIndex) + ".img"
				p = sub.Popen(string, shell=True, stdout=sub.PIPE, stderr=sub.STDOUT)
				p.wait()
				if p.returncode == 0:
					status = 0
				else:
					newIndex = newIndex + 1
					status = 1
		# Collect informations about created VM
		number = newIndex
		vmname = "evertest_vm_" + str(number)
		sysprep = "virt-sysprep --enable hostname --hostname " + hostname + " -a /var/lib/libvirt/images/" + vmname + ".img"
		# Set the VM#s hostname as the name given in test.conf
		pSysprep = sub.Popen(sysprep, shell=True, stdout=sub.PIPE)
		pSysprep.wait()
		# Configure the VM's network XML for the test specific virtual network
		evertestConfigureVMNetwork(testID, vmname, hostname)
		# Start the created VM
		vmStart = "virsh start evertest_vm_" + str(number)
		pVmStart = sub.Popen(vmStart, shell=True, stdout=sub.PIPE)
		pVmStart.wait()

	except:
		e = sys.exc_info()[edl]
		print "Error in evertestConstructVM: \n" + str(e)
# -------------------------------------------------------------------------------------
# EOF evertestConstructVM
# -------------------------------------------------------------------------------------


#----------------------------------------------------------------------------------------------------------
# EOF Defining functions
#----------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Main (get informations, trigger VM-constructions,...)
#--------------------------------------------------------------------------------------
def evertestMain(testname, filename):
	try:

		#Important data

		#Analyse and echo out
		print "ID of running testcase: " + testname
		numberofvm = str(evertestGetNumber(testname))
		print "Number of VM created in this testcase: " + numberofvm

		#Parse testID and all hostnames to ip-API to create initXML 
		evertestSetupTestNetwork(testname)

		path = "/var/evertest/tests/" + testname + "/" + testname + ".conf"
		root = xmltree.parse(path).getroot()

		#Register VMs to network xml
		for child in root:
			if(child.tag == "vm"):
				hostname = str(child.get("name"))
				evertestRegisterVm(testname, hostname)

		netPath = evertestNetworkXmlPath(testname)
		netCreate = "virsh net-create " + netPath
		s = sub.Popen(netCreate, shell=True, stdout=sub.PIPE)
		s.wait()
		print boarder

		#Create VM(s)

		for child in root:
			if(child.tag == "vm"):
				hostname = child.get("name")
				print "Hostname of VM: " + hostname
				templateID = child.get("template")
				print "Used template: " + templateID
				testfile = child.get("script")
				print "Used testfile: " + testfile
				evertestConstructVM(templateID, hostname, testname)
				print "Constructed VM."
				print boarder
				time.sleep(15)
				evertestSendTest(hostname, testname)

	except:
		e = sys.exc_info()[edl]
		print "Error in evertestMain: \n" + str(e)
#--------------------------------------------------------------------------------------
# EOF evertestMain
#-------------------------------------------------------------------

#--------------------------------------------------------------------------------------
# Running the parameter-given test
#--------------------------------------------------------------------------------------
def run(testname):
	try:
		evertestExtractTest(testname)
		filename = "/var/evertest/tests/" + testname + "/" + testname + ".conf"
#		evertestAddTest(testname)
#		evertestCommitTest(testname)
		evertestMain(testname, filename)

	except:
		e = sys.exc_info()[edl]
		print "Error in run: \n" + str(e)
#--------------------------------------------------------------------------------------
# EOF run
#--------------------------------------------------------------------------------------

# Main call. Testname has to be given by --t="testname" (without quotes).

givenParam = shellParam2("n", 0)
if givenParam != 0:
	run(givenParam)
	print "Test started up successfully: " + str(givenParam)
else:
	print "No testname given. (Give the --n=$testname parameter a try)"