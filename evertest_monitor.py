# -------------------------------------------------------------------------------------------------------
# File: evertest_core.py
# Author(s): RIEDEL, Jan (EVB Everbase AG)
# Last rev.: Dec. 16, 2014
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
# This modul is going to be the Evertest monitoring module.
# It's functions are handling all Evertest modules like at the moment:
#		- evertest_test_handler
#		- evertest_netcfg
#		- evertest_util
# Also it will handle to generate and build the WebUI's contents and manage client interactions with the evertest System.
# -------------------------------------------------------------------------------------------------------

#Import base functions
import os
import sys
import socket
from lxml import etree as xmltree

#Import evertest modules
from evertest_netcfg import *


#--------------------------------------------------------------------------------------
# Set EVETEST_DEBUG_LEVEL TO - 0: Short debug message; 1: explicit debug message
#--------------------------------------------------------------------------------------
EVERTEST_DEBUG_LEVEL = 1
edl = EVERTEST_DEBUG_LEVEL
#--------------------------------------------------------------------------------------
# EOF Debug-Settings
#--------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------------
#
#--------------------------------------------------------------------------------------------------------
def evertestReceiveStatus():
	try:
		myIp = "192.168.0.223"
		buffer_size = 1024
		message = "Got status."
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind(('', EVERTEST_MONITOR_PORT))
		s.listen(1)

		conn, addr = s.accept()
		print "Got status " + str(addr)
		while 1:
			data = conn.recv(buffer_size)
			if not data: break
			print "Status: " + str(data)
			if (str(data) == "failed"):
				print "The testcase has failed!"
			conn.send(message)
		conn.close()
	except:
		e = sys.exc_info()[edl]
		print "Error in evertestBreakListen: \n" + str(e)
#--------------------------------------------------------------------------------------------------------
# EOF evertestWait
#--------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------------
#
#--------------------------------------------------------------------------------------------------------
def evertestMonitorMain(test, xmlPath):
		path = xmlPath
		root = xmltree.parse(path).getroot()
		for child in root:
			if(child.tag == "vm"):
				hostname = child.get("name")
				ip = evertestGetVmIpAddr(test, hostname)
				evertestReceiveStatus()


#--------------------------------------------------------------------------------------------------------
#
#--------------------------------------------------------------------------------------------------------

cnt = 0
while (cnt == 0):
	evertestReceiveStatus()