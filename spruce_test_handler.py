# -------------------------------------------------------------------------------------------------------
# This Python module implements all main functionality relevant to the process of creating and managing VMs.
# It provides routines to create and start VMs out of the information captured from the used .tar file.
# When the test handling process starts, all relevant information from the test is committed to a local Git
# repository. Then all the VMs are being created, their hostnames are set to the specified VM-name (in test
# config), they get IP and MAC addressesb and are being started up. Every single test runs in its own virtual
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
#		- evertestGetNetconfPath -> Get network.xml's path
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
from threading import Thread
import git

#Tools
#import re
import shutil
import time
import libvirt
import tarfile
from lxml import etree as xmltree

from spruce_netcfg_host import *
from spruce_monitor import evertestReceiveStatus

spruceVersion = "0.1"

#--------------------------------------------------------------------------------------
#Paths
#--------------------------------------------------------------------------------------
evertestNetPath     = "/var/evertest/net/"
evertestTestPath	= "/var/evertest/tests/"
evertestRootPath	= "/home/jan/Schreibtisch/evertest/"
evertestImgPath 	= "/var/lib/libvirt/images/"
vmPrefix			= "evertest_vm_"
boarder       		= "~~~~~~~~~~"
# -------------------------------------------------------------------------------------
# EOF Paths
# -------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Set EVETEST_DEBUG_LEVEL TO - 0: Short debug message; 1: Explicit debug message
#--------------------------------------------------------------------------------------
EVERTEST_DEBUG_LEVEL = 1
edl = EVERTEST_DEBUG_LEVEL
#--------------------------------------------------------------------------------------
# EOF Debug-Settings
#--------------------------------------------------------------------------------------

allVm = [] #All started VMs names are appended here to be handled later on destroying process

# -------------------------------------------------------------------------------------------------------
# Returns the Value assigned to a Command Line Parameter. (--param=value) 
# If no Value was passed in, the specified default will be returned.
# -------------------------------------------------------------------------------------------------------
def handleShellParam(param, default):

	for cmdarg in sys.argv:
		if(("--" + param + "=") in cmdarg):
			return str(cmdarg.replace(("--" + param + "="), ""))
		elif(("-" + param + "=") in cmdarg):
			return str(cmdarg.replace(("-" + param + "="), ""))
		elif(("--" + param) in cmdarg):
			return str(cmdarg.replace(("--"), ""))
		elif(("-" + param) in cmdarg):
			return str(cmdarg.replace(("-"), ""))
	return default
# -------------------------------------------------------------------------------------------------------
# EOF shellFlag
# -------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Get the Test ID from the testconfig
#--------------------------------------------------------------------------------------
def evertestGetTestID(testname):
	try:
		path = "{0}{1}/{1}.conf".format(evertestTestPath, testname)
		root = xmltree.parse(path).getroot()
		for child in root:
			if(child.tag == "info"):
				value = child.get("id")
				return value
	except:
		e = sys.exc_info()[edl]
		print "Error in evertestGetTestID: \n" + str(e)
		stat = 1
# -------------------------------------------------------------------------------------
# EOF get evertestGetTestID
# -------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Get the number of VMs to create from the testconfig
#--------------------------------------------------------------------------------------
def evertestGetNumber(testname):
	try:
		path = "{0}{1}/{1}.conf".format(evertestTestPath, testname)
		root = xmltree.parse(path).getroot()
		for child in root:
			if(child.tag == "info"):
				value = child.get("vmcount")
				return value

	except:
		e = sys.exc_info()[edl]
		print "Error in evertestGetNumber: \n" + str(e)
		stat = 1
# -------------------------------------------------------------------------------------
# EOF evertestGetNumber
# -------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Place own mac and network name in VM xml
#--------------------------------------------------------------------------------------
def evertestConfigureVMNetwork(testID, vmname, hostname):
	try:
		mac = evertestGetVmMacAddr(testID, hostname)
		path = "/etc/libvirt/qemu/{}.xml".format(vmname)
		if os.path.lexists(path):
			tree = xmltree.parse(path)
			root = tree.getroot()
			for child in root.iter():
				if(child.tag == "mac"):
					child.set("address", mac)
				if(child.tag == "source"):
					child.set("network", testID)
			tree.write(path)
			defineVM = "virsh define /etc/libvirt/qemu/{}.xml".format(vmname)
			define = sub.Popen(defineVM, shell=True, stdout=sub.PIPE)
			define.wait()
		else:
			raise IOError
	except IOError:
		sys.exit("{} does not exist!".format(path))
	except:
		e = sys.exc_info()[edl]
		print "Error in evertestConfigureVMNetwork: \n" + str(e)
		stat = 1
# -------------------------------------------------------------------------------------
# EOF evertestConfigureVMNetwork
# -------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Unzip the test tar file
#--------------------------------------------------------------------------------------
def evertestExtractTest(testname):
	try:
		extractString = "{}{}.tar".format(evertestTestPath, testname)
		extractPath = "{}{}/".format(evertestTestPath, testname)
		if os.path.lexists(extractString):
			tfile = tarfile.open(extractString)
			tfile.extractall(extractPath)
		else:
			raise IOError
	except IOError:
		sys.exit("No .tar package for the given test name found!")
	except:
		e = sys.exc_info()[edl]
		print "Error occoured while extracting testTar file: \n" + str(e)
		stat = 1
#--------------------------------------------------------------------------------------
# EOF evertestExtractTest
#--------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Send the test files to the VM via ssh
#--------------------------------------------------------------------------------------
def evertestSendTest(vmname, testname):
	try:
		print boarder
		vmip = evertestGetVmIpAddr(testname, vmname)
		print "VM-Name: {}, VM-IP: {}".format(vmname, vmip)

		filename = "{}{}.tar".format(evertestTestPath, testname)
		if os.path.lexists(filename):
			os.system("scp {} tester@{}:/mnt/{}.tar".format(filename, vmip, testname))
		else:
			print "{} does not exist! not sent!".format(filename)

		filename = "{}netconf_{}.xml".format(evertestNetPath, testname)
		if os.path.lexists(filename):
			os.system("scp {} tester@{}:/mnt/{}.net".format(filename, vmip, testname))
		else:
			print "{} does not exist! not sent!".format(filename)

		filename = "{}portmap_{}.xml".format(evertestNetPath, testname)
		if os.path.lexists(filename):
			os.system("scp {} tester@{}:/mnt/{}.ports".format(filename, vmip, testname))
		else:
			print "{} does not exist! not sent!".format(filename)

		filename = "{}spruce_netcfg_client.py".format(evertestRootPath)
		if os.path.lexists(filename):
			os.system("scp {} tester@{}:/mnt/spruce_netcfg_client.py".format(filename, vmip))
		else:
			print "{} does not exist! not sent!".format(filename)

		filename = "{}spruce_util.py".format(evertestRootPath)
		if os.path.lexists(filename):
			os.system("scp {} tester@{}:/mnt/spruce_util.py".format(filename, vmip))
		else:
			print "{} does not exist! not sent!".format(filename)

	except:																					
		e = sys.exc_info()[edl]
		print "Error occoured in evertestSendTest: \n" + str(e)
		stat = 1
#--------------------------------------------------------------------------------------
# EOF evertestSendTest
#--------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Construct the new VM(s)
#--------------------------------------------------------------------------------------
def evertestConstructVM(templateID, hostname, testID, testfile):
	try:
		# Create VM by increasing (or picking the lowest unused) the number in "evertest_vm_$number" for VMNames
		creationIndex = 1
		string = "virt-clone -o {0} -n {1}{2} -f {3}{1}{2}.img".format(templateID, vmPrefix, str(creationIndex), evertestImgPath)
		o = sub.Popen(string, shell=True, stdout=sub.PIPE, stderr=sub.STDOUT)
		o.wait()
		if o.returncode == 1:				
			creationIndex = 2
			status = 1
			while status != 0:
				string = "virt-clone -o {0} -n {1}{2} -f {3}{1}{2}.img".format(templateID, vmPrefix, str(creationIndex), evertestImgPath)
				p = sub.Popen(string, shell=True, stdout=sub.PIPE, stderr=sub.STDOUT)
				p.wait()
				if p.returncode == 0:
					status = 0
				else:
					creationIndex += 1
					status = 1
		# Collect informations about created VM
		number = creationIndex
		vmname = vmPrefix + str(number)
		allVm.append((vmname, hostname))
		sysprep = "virt-sysprep --operations -ssh-userdir --hostname {} -a {}{}.img".format(hostname, evertestImgPath, vmname)
		# Set the VMs hostname as the name given in test.conf
		pSysprep = sub.Popen(sysprep, shell=True, stdout=sub.PIPE)
		pSysprep.wait()

		# Configure the VM's network XML for the test specific virtual network		
		evertestConfigureVMNetwork(testID, vmname, hostname)

		# Start the created VM
		vmStart = "virsh start {}{}".format(vmPrefix, str(number))
		pVmStart = sub.Popen(vmStart, shell=True, stdout=sub.PIPE)
		pVmStart.wait()

		print "Constructed VM with hostname '{}' from template '{}' and attached '{}' as testfile.".format(hostname, templateID, testfile)
		time.sleep(15)
		evertestSendTest(hostname, testID)


	except:
		e = sys.exc_info()[edl]
		print "Error in evertestConstructVM: \n" + str(e)
		stat = 1
# -------------------------------------------------------------------------------------
# EOF evertestConstructVM
# -------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Main (get informations, trigger VM-constructions,...)
#--------------------------------------------------------------------------------------
def evertestMain(testname, filename):
	try:

		#Important data

		#Analyse and echo out
		print "ID of running testcase: {}".format(testname)
		vmcount = str(evertestGetNumber(testname))
		print "Number of VM created in this testcase: {}".format(vmcount)

		#Parse testID and all hostnames to ip-API to create initXML 
		evertestSetupTestNetwork(testname)

		path = "{0}{1}/{1}.conf".format(evertestTestPath, testname)
		root = xmltree.parse(path).getroot()

		#Register VMs to network xml
		for child in root:
			if(child.tag == "vm"):
				hostname = str(child.get("name"))
				evertestRegisterVm(testname, hostname)

		netPath = evertestGetNetconfPath(testname)
		if os.path.lexists(netPath):
			netCreate = "virsh net-create {}".format(netPath) #this creates the before defined network in libvirt
			s = sub.Popen(netCreate, shell=True, stdout=sub.PIPE)
			s.wait()
		else:
			sys.exit("{} does not exist!".format(netPath))

		print boarder

		t = Thread(target=evertestReceiveStatus, args=(testname, ))
		t.start()

		for child in root:
			if(child.tag == "vm"):
				hostname = child.get("name")
				templateID = child.get("template")
				testfile = child.get("script")

				evertestConstructVM(templateID, hostname, testname, testfile)

		# print "Joined monitoring thread"
		t.join() # Blocks test_handler until the threads have finished and prevents early vm removal 

	except:
		e = sys.exc_info()[edl]
		print "Error in evertestMain: \n" + str(e)
		stat = 1

	finally:
		#Shut down and delete VMs / remove networking filesx
		for vm in allVm:
			vmip = evertestGetVmIpAddr(testname, vm[1])
			pRemoveKey = sub.Popen("ssh-keygen -f '/root/.ssh/known_hosts' -R {}".format(vmip), shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
			pRemoveKey.wait()

			vmStop = "virsh shutdown " + str(vm[0])
			pVmStop = sub.Popen(vmStop, shell=True, stdout=sub.PIPE)

			grep = "virsh list | grep " + str(vm[0])
			grepF = sub.Popen(grep, shell=True, stdout=sub.PIPE)
			out, err = grepF.communicate()

			while out:
				time.sleep(1)
				grepF = sub.Popen(grep, shell=True, stdout=sub.PIPE)
				out, err = grepF.communicate()

			undefine = "virsh undefine {0} --storage {1}{0}.img".format(str(vm[0]), evertestImgPath)
			pUndefine = sub.Popen(undefine, shell=True, stdout=sub.PIPE, stderr=sub.PIPE) #No errors and outs piped?
			pUndefine.wait()

			print "Undefined and removed VM: {} alias {}".format(str(vm[0]), str(vm[1]))


		stopNet = "virsh net-destroy " + testname
		pStopNet = sub.Popen(stopNet, shell=True, stdout=sub.PIPE)
		pStopNet.wait()

		netcfg = "{}netconf_{}.xml".format(evertestNetPath, testname)
		portmap = "{}portmap_{}.xml".format(evertestNetPath, testname)
		folder = evertestTestPath + testname
		os.remove(netcfg)
		os.remove(portmap)
		shutil.rmtree(folder)

		print "Removed VMs and undefined Network"
#--------------------------------------------------------------------------------------
# EOF evertestMain
#-------------------------------------------------------------------

#--------------------------------------------------------------------------------------
# Running the parameter-given test
#--------------------------------------------------------------------------------------
def runTest(testname):
	try:
		evertestExtractTest(testname) #Check if extract result 0
		filename = "{0}{1}/{1}.conf".format(evertestTestPath, testname) #not checked any more after this point
		if os.path.lexists(filename):
			evertestMain(testname, filename)
		else:
			raise IOError
	except IOError:
		sys.exit("{} does not exist!".format(filename))
	except:
		e = sys.exc_info()[edl]
		print "Error in run: \n" + str(e)
		stat = 1
#-------------------------------------------------------------------------------------
# EOF run
#--------------------------------------------------------------------------------------

# Main call. Testname has to be given by --t="testname" (without quotes).
givenTest = handleShellParam("n", 0)
helpParam0 = handleShellParam("help", 0)
helpParam1 = handleShellParam("h", 0)

if givenTest != 0:
	stat = 0
	runTest(givenTest)
	sys.exit(stat)

if helpParam0 != 0 or helpParam1 != 0:
	print "This help refers to spruce v{}.".format(spruceVersion)
	print "Parameters:"
	print "    -n or --name   : Defines the used .py testfile"
	print "    -h or --help   : Displays this help"
else:
	sys.exit("No parameters given. Maybe you should have a look for the --help")