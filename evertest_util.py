# -------------------------------------------------------------------------------------------------------
# File: evertest-util.py
# Author(s): HAUSWALD, Tom (EVB Everbase AG); RIEDEL, Jan (EVB Everbase AG)
# Last rev.: Dec. 16, 2014
# -------------------------------------------------------------------------------------------------------
#                            .
#                           / \
#						   /   \
#						  /     \
#						 /		 \
#						/		  \
#					   /		   \
#					  /			    \
#					 /				 \
#					/				  \
#				   /				   \
#				  /_____________________\
#				 / \				   / \
#				/   \			      /	  \
#			   /	 \			     /	   \
#			  /		  \			    /	    \
#			 /		   \		   /	  	 \
#			/		    \	      /			  \
#		   /			 \	     /			   \
#		  /				  \	    /			    \
#		 /				   \   /			 	 \
#		/				    \ /	      everbase	  \
#	   /_____________________V_____________________\
#
# This Python module implements useful additional routines that will be provided for the virtual machines
# to use during their testcase execution.
# -------------------------------------------------------------------------------------------------------

import sendfile
import subprocess
import socket
from lxml import etree as xmltree

from glob			 import *
from evertest_netcfg import *

#--------------------------------------------------------------------------------------
# Set EVETEST_DEBUG_LEVEL TO - 0: Short debug message; 1: explicit debug message
#--------------------------------------------------------------------------------------
EVERTEST_DEBUG_LEVEL = 1
edl = EVERTEST_DEBUG_LEVEL
#--------------------------------------------------------------------------------------
# EOF Debug-Settings
#--------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Executes a Bash Command.
# -------------------------------------------------------------------------------------------------------
def evertestRunBash(command):

	# Start Subprocess
	process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	# Supply User w/ piped stdout & stderr Output
	for lout in iter(process.stdout.readline, b''):
		print lout
	for lerr in iter(process.stderr.readline, b''):
		print lerr

	process.communicate()
# -------------------------------------------------------------------------------------------------------
# EOF evertestRunBash
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the Name of the virtual Machine that the Script is running on.
# -------------------------------------------------------------------------------------------------------
def evertestGetLocalName():

	script = glob(EVERTEST_WORKER_ROOT_DIR + "/*.script")[0]
	return script.replace(EVERTEST_WORKER_ROOT_DIR + "/", "").replace(".script", "")
# -------------------------------------------------------------------------------------------------------
# EOF evertestGetLocalName
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the Name of the Test (Network) that the Script is currently running as a Part of.
# -------------------------------------------------------------------------------------------------------
def evertestGetLocalTestId():

	conf = glob(EVERTEST_WORKER_ROOT_DIR + "/*.conf")[0]
	return conf.replace(EVERTEST_WORKER_ROOT_DIR + "/", "").replace(".conf", "")
# -------------------------------------------------------------------------------------------------------
# EOF evertestGetLocalName
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the actual tests network XML
# -------------------------------------------------------------------------------------------------------
def evertestGetLocalNetXml():
	try:
		conf = glob(EVERTEST_WORKER_ROOT_DIR + "/*.net")[0]
		return conf
	except:
		e = sys.exc_info()[edl]
		print "Error in evertestBreakSend: \n" + str(e)
# -------------------------------------------------------------------------------------------------------
# EOF evertestGetLocalNetXml
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Sends a File via TCP to the specified virtual Machine
# -------------------------------------------------------------------------------------------------------
def evertestSendFile(filename, tid, receiver):

	path = EVERTEST_WORKER_ROOT_DIR + "/" + filename
	sock = socket.socket()
	addr = evertestGetVmIpAddr(tid, receiver)
	print "IP Address of Receiver: " + addr
	sock.connect((addr, EVERTEST_TCP_FILE_PORT))
	position = 0

	print "Sending File '" + path + "' to VM: " + receiver + " (TID=" + tid + ")"

	data = open(path, "rb")
	
	while 1:
	    sent = sendfile.sendfile(sock.fileno(), data.fileno(), position, os.path.getsize(path))
	    if sent == 0:
	        break  # End of File reached
	    position += sent
# -------------------------------------------------------------------------------------------------------
# EOF evertestSendFile
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Listens on TCP Port until File was received
# -------------------------------------------------------------------------------------------------------
def evertestRecvFile():

	sendfile.wait(EVERTEST_TCP_FILE_PORT)
# -------------------------------------------------------------------------------------------------------
# EOF evertestSendFile
# -------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------------
# 
#--------------------------------------------------------------------------------------------------------
def evertestBreakSend(receiver, description):
	try:
		path = evertestGetLocalNetXml()
		root = xmltree.parse(path).getroot()
		for child in root:
			if(child.tag == host):
				if(child.get("name") == "receiver"):
					receiverIp = child.get("ip")

		buffer_size = 1024
		message = "Reached (" + description + ")."
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((receiverIp, EVERTEST_TCP_FILE_PORT))
		s.send(message)
		data = s.recv(buffer_size)
		s.close
		print "Reached breakpoint (" + description + "), sent command to go on, recieved {'" + data + "'} as answer."
	except:
		e = sys.exc_info()[edl]
		print "Error in evertestBreakSend: \n" + str(e)
#--------------------------------------------------------------------------------------------------------
# EOF evertestBreakSend
#--------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------------
#
#--------------------------------------------------------------------------------------------------------
def evertestBreakListen(rcvMessage):
	try:
		myIp = "127.0.0.1"
		buffer_size = 1024
		message = "Got it."
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind(('', EVERTEST_TCP_FILE_PORT))
		s.listen(1)

		conn, addr = s.accept()
		print "Got message from " + str(addr)
		while 1:
			data = conn.recv(buffer_size)
			if not data: break
			print "Message: " + str(data)
			conn.send(message)
			print "Sent 'Got it' as answer. Going on now.."
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
def evertestSendStatus(status):
	try:
		receiverIp = "192.168.0.223"
		buffer_size = 1024
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((receiverIp, EVERTEST_MONITOR_PORT))
		s.send(status)
		data = s.recv(buffer_size)
		s.close
		print "Got answer: " + str(data)
	except:
		e = sys.exc_info()[edl]
		print "Error in evertestSendStatus: \n" + str(e)
#--------------------------------------------------------------------------------------------------------
# EOF evertestSendStatus
#--------------------------------------------------------------------------------------------------------

actStatus = "Success!"
evertestSendStatus(actStatus)