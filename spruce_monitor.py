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
import traceback
from lxml import etree as xmltree
from threading import Thread
from junit_xml import TestSuite, TestCase

#Import evertest modules
from spruce_netcfg_host import *

hostIP = "192.168.0.226"
hostIP = "192.168.122.1"

#Paths
netPath     = "/var/evertest/net/"
testPath	= "/var/evertest/tests/"

boarder       		= "~~~~~~~~~~"
#--------------------------------------------------------------------------------------
# Set EVETEST_DEBUG_LEVEL TO - 0: Short debug message; 1: explicit debug message
#--------------------------------------------------------------------------------------
DEBUG_LEVEL = 1
dl = DEBUG_LEVEL
#--------------------------------------------------------------------------------------
# EOF Debug-Settings
#--------------------------------------------------------------------------------------

def readVmName(xmlPath, ip):
	try:
		root = xmltree.parse(xmlPath).getroot()
		for child in root.iter():
			if (child.tag == "host"):
				if(child.get("ip") == ip):
					name = child.get("name")
					return name
	except:
		e = sys.exc_info()[dl]
		print "Error in readVmName: \n" + str(e)
#--------------------------------------------------------------------------------------------------------

results = {}
dics = {}
jresults = []

class testData:
	
	def __init__(self, vmname, logmode):
		self.vmname = vmname
		self.finished = False
		self.status = "Never started"
		self.duration = 9001
		self.outfile = self.vmname + "_results.xml"
		self.warnings = []
		self.errors = []
		self.infos = []
		self.logmode = logmode

	def appendWarning(self, warningMsg):
		self.warnings.append(["WARNING", warningMsg])

	def appendError(self, errorMsg):
		self.errors.append(["ERROR", errorMsg])

	def appendInfo(self, infoMsg):
		#self.infos.append(["INFO", infoMsg])# -> try now appending only message itself
		self.infos.append(infoMsg)

	def writeResults(self, testname):
		if self.logmode == "jenkins":
			self.writeJenkins(testname)
		elif self.logmode == "json":
			self.writeJson(testname)

	def writeJson(self, testname):
		if self.outfile != "":
			if len(self.errors) != 0:
				self.status = "Failed"
			elif len(self.warnings) != 0:
				self.status = "Success with warnings"
			else:
				self.status = "Success"
			dic = {"vm" : {"name" : self.vmname,"status" : self.status, "running time" : str(self.duration), "output" : {"warning" : [ls for ls in self.warnings], "info" : [ls for ls in self.infos], "error" : [ls for ls in self.errors]}}}
			dics[self.vmname] = {"name" : self.vmname, "running time" : str(self.duration), "output" : {"warning" : [ls for ls in self.warnings], "info" : [ls for ls in self.infos], "error" : [ls for ls in self.errors]}}
			with open(self.outfile, 'w') as outfile:
				json.dump(dic, outfile, indent=3, sort_keys=True)
		else:
			print "No outfile specified! Writing aborted."


	def writeJenkins(self, testname):
		test_case = TestCase(self.vmname, "{}.{}".format("backend", testname), self.duration, [ls for ls in self.infos], [ls for ls in self.warnings])
		jresults.append(test_case)
		

def writeAggregatedResults(testname, resfile, logmode):
	if logmode == "jenkins":
		writeJenskinsResults(testname, resfile)
	elif logmode == "json":
		writeJsonResults(testname, resfile)

def writeJenskinsResults(testname, resfile):
	if resfile != "":
		failures = 0 #init
		errors = 0 #init

	ts = TestSuite("Spruce Backend Test", jresults)	
	with open("/home/tester/jenkins/workspace/backend_spruce_tests_release/aggResults.xml", 'w') as f:
		TestSuite.to_file(f, [ts], prettyprint=False)		


def writeJsonResults(testname, resfile):
	if resfile != "":
		warnings = 0
		errors = 0

		for k, v in results.items():
			warnings = warnings + len(v.warnings)
		for k, v in results.items():
			errors = errors + len(v.errors)

		dic = {"test" : {"vm" : [v for k, v in dics.items()], "general" : {"name" : testname, "warnings" : warnings, "errors" : errors}}}
		with open(resfile, 'w') as outfile:
			json.dump(dic, outfile, indent=3, sort_keys=True)
		print boarder
		print "Wrote aggregated results to " + str(resfile)

	else:
		print "No outfile specified! Writing aborted."
#--------------------------------------------------------------------------------------------------------
# Function receiving the live status from all running VMs (success, fail..)
# 	-> have to be sorted and analyzed / maybe over 2. module in another process and then passing to core 
#--------------------------------------------------------------------------------------------------------
def collectMessages(givenTest, logmode, debug=False):
	try:
		mode = "test"
		port = getVmMonitoringPort(givenTest, "foo", mode)
		xmlPath = "{}netconf_{}.xml".format(netPath, givenTest)
		confXmlPath = "{0}{1}/{1}.conf".format(testPath, givenTest)

		# Append one testData() object per VM to the results dictionary
		root = xmltree.parse(confXmlPath).getroot()
		for child in root:
			if (child.tag == "vm"):
				name = str(child.get("name"))
				results[name] = testData(name, logmode) #the testData objects created here have no names - they are just accessible via the index of results[]
				print "Added {} to result list.".format(name)
		cnt = 0
		while (cnt == 0):
			buffer_size = 1024
			message = "Got status."
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 	# after conn.close() the used socket has been left in TIME_WAIT state. The SO_REUSEADDR option tells the kernel to reuse the socket in TIME_WAIT state.
			s.bind((hostIP, (port)))	# Otherwise it would need its time until the socket can be reused and throw errors (multiple threads would be tried to start on the same socket without success) EVERTEST_MONITOR_PORT + port
			s.listen(1)

			finished = 0
			while (finished == 0):
				conn, addr = s.accept()
				hostname = str(readVmName(xmlPath, addr[0]))

				if debug == True:
					print "Received status from {0} [{1}] {{\"{2}\"}}".format(str(addr), hostname, time.strftime("%H:%M:%S"))
					print boarder

				data = conn.recv(buffer_size)
				if not data: 
					break

				tData = results[hostname]

				dataString = str(data)
				status = dataString.split('- ')[0]
				if '-' in dataString:
					sMessage = dataString.split('- ', 1)[1] #only split string at the first occurence of "-"
				else:
					sMessage = "*no message transmitted*"

				if "warning" in status.lower():
					tData.appendWarning(sMessage)
				elif "error" in status.lower():
					tData.appendError(sMessage)
				elif "info" in status.lower():
					tData.appendInfo(sMessage)
				elif "time" in status.lower():
					tData.duration = float(sMessage)
				elif "finish" in status.lower():
					tData.finished = True
					if all(result.finished == True for key, result in results.items()):
						for k, v in results.items():
							v.writeResults(givenTest)
						cnt = 1
						finished = 1
				else:
					tData.appendInfo("Undefined message type: {}".format(sMessage))

				conn.send(message)

			conn.close()

		writeAggregatedResults(givenTest, "aggResults.json", logmode)
	except:
		e = sys.exc_info()[dl]
		print "Error in collectMessages: \n" + str(e)
		print(traceback.format_exc())
#--------------------------------------------------------------------------------------------------------
# EOF evertestWait
#--------------------------------------------------------------------------------------------------------
