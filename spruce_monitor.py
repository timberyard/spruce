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
import json
from lxml import etree as xmltree
from threading import Thread

#Import evertest modules
from spruce_netcfg_host import *

#hostIP = "192.168.0.223" # has to be changed for new machine!
hostIP = "192.168.0.184"

#Paths
evertestNetPath     = "/var/evertest/net/"
evertestTestPath	= "/var/evertest/tests/"

#--------------------------------------------------------------------------------------
# Set EVETEST_DEBUG_LEVEL TO - 0: Short debug message; 1: explicit debug message
#--------------------------------------------------------------------------------------
EVERTEST_DEBUG_LEVEL = 1
edl = EVERTEST_DEBUG_LEVEL
#--------------------------------------------------------------------------------------
# EOF Debug-Settings
#--------------------------------------------------------------------------------------

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

results = {}
dics = {}

class testData:
	
	def __init__(self, vmname):
		self.vmname = vmname
		self.duration = "??:??:??"
		self.outfile = self.vmname + "_results.txt"
		self.warnings = []
		self.errors = []
		self.infos = []

	def appendWarning(self, warningMsg):
		self.warnings.append(["WARNING", warningMsg])

	def appendError(self, errorMsg):
		self.errors.append(["ERROR", errorMsg])

	def appendInfo(self, infoMsg):
		self.infos.append(["INFO", infoMsg])

	def writeResults(self):
		if self.outfile != "":
			dic = {"vm" : {"name" : self.vmname, "time running" : self.duration, "output" : {"warning" : [ls for ls in self.warnings], "info" : [ls for ls in self.infos], "error" : [ls for ls in self.errors]}}}
			dics[self.vmname] = {"name" : self.vmname, "time running" : self.duration, "output" : {"warning" : [ls for ls in self.warnings], "info" : [ls for ls in self.infos], "error" : [ls for ls in self.errors]}}
			with open(self.outfile, 'w') as outfile:
				json.dump(dic, outfile, indent=3, sort_keys=True)
		else:
			print "No outfile specified! Writing aborted."


def writeAggregatedResults(outfile):
	if outfile != "":
		dic = {"test" : {"vm" : [v for k, v in dics.items()]}, "general" : {"name" : "", "duration" : "", "warnings" : 4, "errors" : 2}}
		with open(outfile, 'w') as outfile:
			json.dump(dic, outfile, indent=3, sort_keys=True)
	else:
		print "No outfile specified! Writing aborted."
#--------------------------------------------------------------------------------------------------------
# Function receiving the live status from all running VMs (success, fail..)
# 	-> have to be sorted and analyzed / maybe over 2. module in another process and then passing to core 
#--------------------------------------------------------------------------------------------------------
def evertestReceiveStatus(port, xmlPath):
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

				tData = results[hostname]

				dataString = str(data)
				status = dataString.split('-')[0]
				sMessage = dataString.split('-')[1]

				if "warning" in status:
					tData.appendWarning(sMessage)
				if "error" in status:
					tData.appendError(sMessage)
				if "info" in status:
					tData.appendInfo(sMessage)
					print "Append info to: " + tData.vmname
				if "finish" in status:
					for k, v in results.items():
						v.writeResults()
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
		confXmlPath = evertestTestPath + givenTest + "/" + givenTest + ".conf"

		#create testData objects for all VMs in the test
		root = xmltree.parse(confXmlPath).getroot()
		for child in root:
			if (child.tag == "vm"):
				name = str(child.get("name"))
				results[name] = testData(name) #the testData objects created here have no names - they are just accessible via the index of results[]

		t = Thread(target=evertestReceiveStatus, args=(port, xmlPath))
		t.start()
		print "Opened up monitor!"
		t.join()
		writeAggregatedResults("aggResults.txt")
	except:																			# maybe ports in /proc/sys/net/ipv4/ip_local_port_range has to be changed
		e = sys.exc_info()[edl]														# pass, so that the script does not exit because of no activity on a monitored port
		print "Error in evertestMonitorMain: \n" + str(e)
#--------------------------------------------------------------------------------------------------------
# EOF evertestMonitorMain
#--------------------------------------------------------------------------------------------------------

#evertestMonitorMain("install_apache")