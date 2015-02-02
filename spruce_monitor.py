# -------------------------------------------------------------------------------------------------------
# File: evertest_core.py
# Author(s): RIEDEL, Jan (EVB Everbase AG)
# Last rev.: Feb. 02, 2015
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
# This module is going to be the Evertest monitoring module.
# -------------------------------------------------------------------------------------------------------

#Import base functions
import os
import sys
import socket
import thread
import time
from lxml import etree as xmltree

#Import evertest modules
from spruce_netcfg_host import *

#hostIP = "192.168.0.223" # has to be changed for new machine!
hostIP = "192.168.0.223"

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
# Function receiving the live status from all running VMs (success, fail..)
# 	-> have to be sorted and analyzed / maybe over 2. module in another process and then passing to core 
#--------------------------------------------------------------------------------------------------------
def evertestReceiveStatus(port, xmlPath):
	try:
		while (cnt == 0):
#			print "Started a new server-socket."
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
				print "Status: " + str(data)
				print "~~~~~~~~~~~~~~~~~~~~"
				if (str(data) == "failed"):
					print "The testcase has failed!"
				conn.send(message)
			conn.close()
#			print "Connection closed."	
	except:
		e = sys.exc_info()[edl]
		print "Error in evertestReceiveStatus: \n" + str(e)
#--------------------------------------------------------------------------------------------------------
# EOF evertestWait
#--------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------------
# Monitor main function; not sure if really needed yet 
#--------------------------------------------------------------------------------------------------------
def evertestMonitorMain(port, xmlPath):
	try:
#		path = xmlPath
#		root = xmltree.parse(path).getroot()
#		for child in root:
#			if(child.tag == "vm"):
#				hostname = child.get("name")
#				print "der hostname der VM ist " + hostname
#				ip = evertestGetVmIpAddr(test, hostname)
#				print "The VMs IP is " + ip
#				thread.start_new_thread(evertestReceiveStatus, (hostname, port,)) 	# every VM is monitored in it's own thread
#				port = port + 1 													# because of the large number of threads, ports from 1024 to 49151 (well known ports (ICANN)) and 49152 to 65535 (dynamit/private ports)
#				if((port + 1024) > 49151):
#					print "Error: Maximum port number is 49151 (public ports)!"
#					break
		thread.start_new_thread(evertestReceiveStatus, (port, xmlPath))
	except:																			# maybe ports in /proc/sys/net/ipv4/ip_local_port_range has to be changed
		e = sys.exc_info()[edl]														# pass, so that the script does not exit because of no activity on a monitored port
		print "Error in evertestMonitorMain: \n" + str(e)
	while 1: pass
#--------------------------------------------------------------------------------------------------------
# EOF evertestMonitorMain
#--------------------------------------------------------------------------------------------------------

givenTest = handleShellParam("n", 0)
givenVM = handleShellParam("v", 0)
xmlPath = "/var/evertest/net/netconf_" + givenTest + ".xml"
#mode = handleShellParam("m", 0) # This option will let the user set the type of monitoring: Each vm seperated or the whole test
mode = "test"					# Actually just testwide monitoring is used -> The used port in this mode is the first one on the portmap
if givenTest != 0:
	cnt = 0
	port = evertestGetVmPort(givenTest, "foo", mode)
	evertestMonitorMain(port, xmlPath)
else:
	if givenTest == 0 and givenVM == 0:
		print "No testname(--n=$testname) and vmname(--v=$vmname) given!"
	elif givenTest == 0:
		print "No testname given! Add it with --n=$testname."
	elif givenVM == 0:
		print "No vmname given! Add it with --v=$vmname."
