# -------------------------------------------------------------------------------------------------------
# This module is used as monitoring module. It provides functions to eather monitor messages sent by a single vm
# or bundle messages by all VMs to testwide logs.
# -------------------------------------------------------------------------------------------------------

#Import base functions
import os
import sys
import socket
import thread
import time
from lxml import etree as xmltree

#Import evertest modules
from spruce_util import *
from spruce_netcfg_host import *

#hostIP = "192.168.0.223" # has to be changed for new machine!
hostIP = "192.168.0.223"
hostIP = "192.168.11.156"
#Paths
evertestNetPath     = "/var/evertest/net/"

#--------------------------------------------------------------------------------------
# Set EVETEST_DEBUG_LEVEL TO - 0: Short debug message; 1: explicit debug message
#--------------------------------------------------------------------------------------
EVERTEST_DEBUG_LEVEL = 1
edl = EVERTEST_DEBUG_LEVEL
#--------------------------------------------------------------------------------------
# EOF Debug-Settings
#--------------------------------------------------------------------------------------

def handleShellParam(param, default):

	for cmdarg in sys.argv:
		if(("--" + param + "=") in cmdarg):
			return str(cmdarg.replace(("--" + param + "="), ""))
	return default


def evertestGetName(xmlPath, ip):
	try:
		root = xmltree.parse(xmlPath).getroot()
		for child in root.iter():
			if (child.tag == "host"):
				if(child.get("ip") == ip):
					name = child.get("name")
					return name
	except:
		e = sys.exc_info()[edl]
		print "Error in evertestGetName: \n" + str(e)
#--------------------------------------------------------------------------------------------------------

class testData:

	warnings = []
	errors = []
	infos = []

	def appendWarning(self, warningMsg):
		self.warnings.append(["WARNING", warningMsg])

	def appendError(self, errorMsg):
		self.errors.append(["ERROR", errorMsg])

	def appendInfo(self, infoMsg):
		self.infos.append(["INFO", infoMsg])

#--------------------------------------------------------------------------------------------------------
# Function receiving the live status from all running VMs (success, fail..)
# 	-> have to be sorted and analyzed / maybe over 2. module in another process and then passing to core 
#--------------------------------------------------------------------------------------------------------
def evertestReceiveStatus(port, xmlPath, tData):
	try:
		cnt = 0
		while (cnt == 0):
			buffer_size = 1024
			message = "Got status."
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 	# after conn.close() the used socket has been left in TIME_WAIT state. The SO_REUSEADDR option tells the kernel to reuse the socket in TIME_WAIT state.
			s.bind((hostIP, (port)))	# Otherwise it would need its time until the socket can be reused and throw errors (multiple threads would be tried to start on the same socket without success) EVERTEST_MONITOR_PORT + port
			s.listen(1)

			conn, addr = s.accept()
			hostname = str(evertestGetName(xmlPath, addr[0]))
			print "Received status from " + str(addr) + " [" + hostname + "] {" + time.strftime("%H:%M:%S") + "}"
			while 1:
				data = conn.recv(buffer_size)
				if not data: break

				dataString = str(data)
				status = dataString.split('-')[0]
				sMessage = dataString.split('-')[1]
				if "warning" in status:
					tData.appendWarning(sMessage)
				if "error" in status:
					tData.appendError(sMessage)
				if "info" in status:
					tData.appendInfo(sMessage)
				if "finish" in status:
					writeCall(tData)
					cnt = 1
				conn.send(message)
			conn.close()	
	except:
		e = sys.exc_info()[edl]
		print "Error in evertestReceiveStatus: \n" + str(e)
#--------------------------------------------------------------------------------------------------------
# EOF evertestWait
#--------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------------
# Monitor main function; not sure if really needed yet 
#--------------------------------------------------------------------------------------------------------
def evertestMonitorMain(givenTest):
	try:
		mode = "test"
		port = evertestGetVmPort(givenTest, "foo", mode)
		xmlPath = evertestNetPath + "netconf_" + givenTest + ".xml"
		tData = testData()
		thread.start_new_thread(evertestReceiveStatus, (port, xmlPath, tData))
		print "Opened up monitor!"
	except:																			# maybe ports in /proc/sys/net/ipv4/ip_local_port_range has to be changed
		e = sys.exc_info()[edl]														# pass, so that the script does not exit because of no activity on a monitored port
		print "Error in evertestMonitorMain: \n" + str(e)
	while 1: pass
#--------------------------------------------------------------------------------------------------------
# EOF evertestMonitorMain
#--------------------------------------------------------------------------------------------------------

##givenTest = handleShellParam("n", 0)
#givenTest = "install_apache"
#givenVM = handleShellParam("v", 0)
#mode = handleShellParam("m", 0) # This option will let the user set the type of monitoring: Each vm seperated or the whole test
#mode = "test"					# Actually just testwide monitoring is used -> The used port in this mode is the first one on the portmap
#if givenTest != 0:
#	cnt = 0
#	if givenTest:
#		try:
#			port = evertestGetVmPort(givenTest, "foo", mode)
#			xmlPath = evertestNetPath + "netconf_" + givenTest + ".xml"
#			tData = testData()
#			evertestMonitorMain(port, xmlPath, tData)
#
#		except:
#			print "The given test does not exist!"
##			print str(sys.exc_info()[edl])
#	else:
#		print "Empty string given as testname!"
#else:
#	if givenTest == 0 and givenVM == 0:
#		print "No testname(--n=$testname) and vmname(--v=$vmname) given!"
#	elif givenTest == 0:
#		print "No testname given! Add it with --n=$testname."
#	elif givenVM == 0:
#		print "No vmname given! Add it with --v=$vmname."
