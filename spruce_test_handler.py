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
import argparse
import fileinput
import subprocess as sub
from threading import Thread

#Tools
import time
import shutil
import smbPull
import tarfile
from lxml import etree as xmltree

from spruce_netcfg_host import *
from spruce_monitor import collectMessages

import paramiko
import traceback
from scp import SCPClient

spruceVersion = "0.2"

#--------------------------------------------------------------------------------------
# Paths
#--------------------------------------------------------------------------------------
evertestNetPath     = "/var/evertest/net/"
evertestTestPath	= "/var/evertest/tests/"
evertestRootPath	= "/var/spruce/"
evertestImgPath 	= "/var/lib/libvirt/images/"
vmPrefix			= "spruce_"
boarder       		= "~~~~~~~~~~"
# -------------------------------------------------------------------------------------
# Credentials
# -------------------------------------------------------------------------------------
localVmPassword = "evb"
localVmUsername = "tester"

#--------------------------------------------------------------------------------------
# Set EVETEST_DEBUG_LEVEL TO - 0: Short debug message; 1: Explicit debug message
#--------------------------------------------------------------------------------------
EVERTEST_DEBUG_LEVEL = 1
edl = EVERTEST_DEBUG_LEVEL

allVm = [] #All started VMs names are appended here to be handled later on destroying process


#--------------------------------------------------------------------------------------
# Get the number of VMs to create from the testconfig
#--------------------------------------------------------------------------------------
def countVm(testname):
	try:
		path = "{0}{1}/{1}.conf".format(evertestTestPath, testname)
		if not os.path.lexists(path):
			raise IOError("{} does not exist!".format(path))

		root = xmltree.parse(path).getroot()
		for child in root:
			if(child.tag == "info"):
				value = child.get("vmcount")
				return value

	except Exception:
		print("An error occured whilst counting the VMs!")
		raise

#--------------------------------------------------------------------------------------
# Place own mac and network name in VM xml
#--------------------------------------------------------------------------------------
def configureVmNetwork(testID, vmname, hostname):
	try:
		mac = getVmMacAddr(testID, hostname)
		path = "/etc/libvirt/qemu/{}.xml".format(vmname)
		if not os.path.lexists(path):
			raise IOError("{} does not exist!".format(path))

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

	except Exception:
		print("An error occured whilst configuring the VMs ({}) network!".format(vmname))
		raise

#--------------------------------------------------------------------------------------
# Unzip the test .tar file
#--------------------------------------------------------------------------------------
def extractTest(testname):
	try:
		extractString = "{}{}.tar".format(evertestTestPath, testname)
		extractPath = "{}{}/".format(evertestTestPath, testname)
		if os.path.lexists(extractString):
			tfile = tarfile.open(extractString)
			tfile.extractall(extractPath)
		else:
			raise IOError("No .tar package for the given test name found!")

	except Exception:
		print("An error occured whilst extracting the test .tar!")
		raise

#--------------------------------------------------------------------------------------
# Repack the test .tar file with updated dependency files
#--------------------------------------------------------------------------------------
def repackTest(testname):
	try:
		packFolder = evertestTestPath + testname + "/"
		output = evertestTestPath + testname + ".tar"
		with tarfile.open(output, "w:gz") as tar:
			tar.add(packFolder, arcname=os.path.basename(packFolder))
		print("Repacked test with new files")

	except Exception:
		print("An error occured whilst repacking the test .tar!")
		raise

#--------------------------------------------------------------------------------------
# Send the test files to the VM via ssh
#--------------------------------------------------------------------------------------
def sendTest(vmname, testname):
	try:
		print boarder
		vmip = getVmIpAddr(testname, vmname)

		ssh = paramiko.SSHClient()
		ssh.load_system_host_keys()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Add targets host key to spruce server if unknown
		ssh.connect(vmip, password=localVmPassword, username=localVmUsername)
		
		scp = SCPClient(ssh.get_transport())

		print "Send related files to {}, {}".format(vmname, vmip)

		filename = "{}{}.tar".format(evertestTestPath, testname)
		if os.path.lexists(filename):
			scp.put(filename, remote_path=b'/mnt/')
		else:
			raise IOError("Missing file: {}".format(filename))

		filename = "{}netconf_{}.xml".format(evertestNetPath, testname)
		if os.path.lexists(filename):
			scp.put(filename, remote_path=b'/mnt/{}.net'.format(testname))
		else:
			raise IOError("Missing file: {}".format(filename))

		filename = "{}portmap_{}.xml".format(evertestNetPath, testname)
		if os.path.lexists(filename):
			scp.put(filename, remote_path=b'/mnt/{}.ports'.format(testname))
		else:
			raise IOError("Missing file: {}".format(filename))

		filename = "{}spruce_netcfg_client.py".format(evertestRootPath)
		if os.path.lexists(filename):
			scp.put(filename, remote_path=b'/mnt/spruce_netcfg_client.py')
		else:
			raise IOError("Missing file: {}".format(filename))

		filename = "{}spruce_util.py".format(evertestRootPath)
		if os.path.lexists(filename):
			scp.put(filename, remote_path=b'/mnt/spruce_util.py')
		else:
			raise IOError("Missing file: {}".format(filename))

	except Exception:						
		print("An error occured sending files to the VM ({})!".format(vmname))
		raise


#--------------------------------------------------------------------------------------
# Construct the new VM(s)
#--------------------------------------------------------------------------------------
def constructVm(templateID, hostname, testID, testfile):
	try:
		# Create VM by increasing (or picking the lowest unused) the number in "evertest_vm_$number" for VMNames
		vmPrefix = testID + "_"
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
		configureVmNetwork(testID, vmname, hostname)

		# Start the created VM
		vmStart = "virsh start {}{}".format(vmPrefix, str(number))
		pVmStart = sub.Popen(vmStart, shell=True, stdout=sub.PIPE)
		pVmStart.wait()

		print "Constructed VM with hostname '{}' from template '{}' and attached '{}' as testfile.".format(hostname, templateID, testfile)
		time.sleep(15)
		sendTest(hostname, testID)


	except Exception:
		print("An error occured constructing an VM!")
		raise


#--------------------------------------------------------------------------------------
# Main (get informations, trigger VM-constructions,...)
#--------------------------------------------------------------------------------------
def main(testname, filename, logmode):
	try:
		#Analyse and echo out
		vmcount = str(countVm(testname))

		#Parse testID and all hostnames to ip-API to create initXML 
		setupTestNetwork(testname)

		path = "{0}{1}/{1}.conf".format(evertestTestPath, testname)
		root = xmltree.parse(path).getroot()

		#Register VMs to network xml
		for child in root:
			if(child.tag == "vm"):
				hostname = str(child.get("name"))
				registerVm(testname, hostname)

		netPath = getNetconfPath(testname)
		if os.path.lexists(netPath):
			netCreate = "virsh net-create {}".format(netPath) #this creates the before defined network in libvirt
			s = sub.Popen(netCreate, shell=True, stdout=sub.PIPE)
			s.wait()
		else:
			sys.exit("{} does not exist!".format(netPath))

		print boarder

		t = Thread(target=collectMessages, args=(testname, logmode))
		t.start()

		for child in root:
			if(child.tag == "vm"):
				hostname = child.get("name")
				templateID = child.get("template")
				testfile = child.get("script")

				constructVm(templateID, hostname, testname, testfile)

		# print "Joined monitoring thread"
		t.join() # Blocks test_handler until the threads have finished and prevents early vm removal 

	except:
		print("Error in main!")
		raise

	finally:
		#Shut down and delete VMs / remove networking filesx
		for vm in allVm:
			vmip = getVmIpAddr(testname, vm[1])
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
# Running the parameter-given test
#--------------------------------------------------------------------------------------
def runTest(testname, args):
	try:
		extractTest(testname) #Check if extract result 0
		
		if args.refresh:
			if not args.branch:
				raise ValueError("A branch has to be given to perform a joinRequest refresh!")

			if not args.commit:
				raise ValueError("A commit has to be given to perform a joinRequest refresh!")
				
			if not args.dist:
				raise ValueError("A distribution has to be given to perform a joinRequest refresh!")
				
			if not (args.output == "jenkins") or (args.output == "json"):
				raise ValueError("An output type has to be given!")

			directory = evertestTestPath + testname + "/files"
			smbPull.main(["everbase_kernel"], args.branch, str(args.commit[0:7]), args.dist, directory)
			smbPull.main(["everbase_filesystem"], args.branch, str(args.commit[0:7]), args.dist, directory)
			smbPull.main(["everbase.so"], args.branch, str(args.commit[0:7]), args.dist, directory, "lib/ruby/1.9.1/x86_64-linux")

			repackTest(testname)

		filename = "{0}{1}/{1}.conf".format(evertestTestPath, testname) #not checked any more after this point
		if os.path.lexists(filename):
			main(testname, filename, args.output)
		else:
			raise IOError("{} does not exist!".format(filename))

	except Exception:
		sys.exit(traceback.format_exc())


parser = argparse.ArgumentParser(description="Spruce Test Handler by Jan Riedel")
parser.add_argument('-n', '--name', help="test name", required=True)
parser.add_argument('-r', '--refresh', help="refresh joinRequest test files", action="store_true")
parser.add_argument('-b', '--branch', help="refresh samba branch")
parser.add_argument('-c', '--commit', help="refresh samba commit")
parser.add_argument('-d', '--dist', help="refresh samba dist")
parser.add_argument('-o', '--output', help="has to be jenkins or json", required=True )

args = parser.parse_args()

runTest(args.name, args)