# -------------------------------------------------------------------------------------------------------
# File: evertest_core.py
# Author(s): RIEDEL, Jan (EVB Everbase AG)
# Last rev.: Dec. 27, 2014
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

hostIP = "192.168.0.223" # has to be changed for new machine!

#--------------------------------------------------------------------------------------
# Set EVETEST_DEBUG_LEVEL TO - 0: Short debug message; 1: explicit debug message
#--------------------------------------------------------------------------------------
EVERTEST_DEBUG_LEVEL = 1
edl = EVERTEST_DEBUG_LEVEL
#--------------------------------------------------------------------------------------
# EOF Debug-Settings
#--------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------------
# Function receiving the live status from all running VMs (success, fail..)
# 	-> have to be sorted and analyzed / maybe over 2. module in another process and then passing to core 
#--------------------------------------------------------------------------------------------------------
def evertestReceiveStatus(hostname, port):
	try:
		while (cnt == 0):
#			print "Started a new server-socket."
			buffer_size = 1024
			message = "Got status."
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 	# after conn.close() the used socket has been left in TIME_WAIT state. The SO_REUSEADDR option tells the kernel to reuse the socket in TIME_WAIT state.
			s.bind((hostIP, (EVERTEST_MONITOR_PORT + port)))	# Otherwise it would need its time until the socket can be reused and throw errors (multiple threads would be tried to start on the same socket without success)
			s.listen(1)

			conn, addr = s.accept()
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
def evertestMonitorMain(test, xmlPath, port):
	try:
		path = xmlPath
		root = xmltree.parse(path).getroot()
		for child in root:
			if(child.tag == "vm"):
				hostname = child.get("name")
				print "der hostname der VM ist " + hostname
				ip = evertestGetVmIpAddr(test, hostname)
				print "The VMs IP is " + ip
				thread.start_new_thread(evertestReceiveStatus, (hostname, port,)) 	# every VM is monitored in it's own thread
				port = port + 1 													# because of the large number of threads, ports from 1024 to 49151 (well known ports (ICANN)) and 49152 to 65535 (dynamit/private ports)
				if((port + 1024) > 49151):
					print "Error: Maximum port number is 49151 (public ports)!"
					break
	except:																			# maybe ports in /proc/sys/net/ipv4/ip_local_port_range has to be changed
		e = sys.exc_info()[edl]														# pass, so that the script does not exit because of no activity on a monitored port
		print "Error in evertestMonitorMain: \n" + str(e)
	while 1: pass
#--------------------------------------------------------------------------------------------------------
# EOF evertestMonitorMain
#--------------------------------------------------------------------------------------------------------

cnt = 0
port = 0
testname = "xfer_file"
xmlPath = "/var/evertest/tests/" + testname + "/" + testname + ".conf"
print xmlPath
evertestMonitorMain(testname, xmlPath, port)