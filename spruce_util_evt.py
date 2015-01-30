# -------------------------------------------------------------------------------------------------------
# File: evertest-util.py
# Author(s): RIEDEL, Jan (EVB Everbase AG); HAUSWALD, Tom (EVB Everbase AG); 
# Last rev.: Jan. 23, 2015
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
import errno
from lxml import etree as xmltree

from glob			 import *
from evertest_netcfg import *

EVERTEST_TCP_FILE_PORT 		= 8021
EVERTEST_SOCKET_MODE_SEND 	= 0
EVERTEST_SOCKET_MODE_RECV 	= 1
EVERTEST_WORKER_ROOT_DIR	= "/mnt/scripts"

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
	try:
		# Start Subprocess
		process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		# Supply User w/ piped stdout & stderr Output
		for lout in iter(process.stdout.readline, b''):
			print lout
		for lerr in iter(process.stderr.readline, b''):
			print lerr

		process.communicate()
		return 0
	except:
		return 1
# -------------------------------------------------------------------------------------------------------
# EOF evertestRunBash
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the Name of the virtual Machine that the Script is running on.
# -------------------------------------------------------------------------------------------------------
def evertestGetLocalName():

	script = glob(EVERTEST_WORKER_ROOT_DIR + "/*.script")[0]
	replaceString = EVERTEST_WORKER_ROOT_DIR + "/"
	return script.replace(replaceString, "").replace(".script", "")
# -------------------------------------------------------------------------------------------------------
# EOF evertestGetLocalName
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the Name of the Test (Network) that the Script is currently running as a Part of.
# -------------------------------------------------------------------------------------------------------
def evertestGetLocalTestId():

	conf = glob(EVERTEST_WORKER_ROOT_DIR + "/*.conf")[0]
	replaceString = EVERTEST_WORKER_ROOT_DIR + "/"
	return conf.replace(replaceString, "").replace(".conf", "")
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
# Creates and opens a TCP Socket that is either setup to listen to a specified port or to send Data
# to it. Returns the created Socket Object on Success.
# -------------------------------------------------------------------------------------------------------
def evertestOpenSocket(tid, vm, port, mode):

	addr = evertestGetVmIpAddr(tid, vm)
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Print Success once socket was opened
	if mode == EVERTEST_SOCKET_MODE_SEND:
		print "Successfully opened socket on port %d for outgoing data." % port
	else:
		print "Successfully opened socket on port %d for incoming data." % port

	# OUTGOING MODE
	# Connect to Recipient Port
	if mode == EVERTEST_SOCKET_MODE_SEND:
		try:
			print "Trying to connect to recipiant socket %d on " % port + addr + "..."
			sock.connect((addr, port))
		except socket.error as err:
			print "TCP connection setup failed. Error: " + err.strerror
			return 
	
	# INCOMING MODE
	# Bind to dedicated Port, listen to Connections
	else:
		sock.bind((addr, port))
		sock.listen(5)

	return sock
# -------------------------------------------------------------------------------------------------------
# EOF evertestOpenSocket
# -------------------------------------------------------------------------------------------------------


def evertestCloseSocket(socket):

	socket.shutdown()
	socket.close()


# -------------------------------------------------------------------------------------------------------
# Sends a File via TCP to the specified virtual Machine
# -------------------------------------------------------------------------------------------------------
def evertestSendFile(sock, filename, tid, receiver):

	path = EVERTEST_WORKER_ROOT_DIR + "/" + filename
	
	if receiver == "localhost":
		addr = "127.0.0.1"
	else:
		addr = evertestGetVmIpAddr(tid, receiver)
	
	datasz = os.path.getsize(path)
	data = open(path, "rb")

	print "Resolved target address => Worker Name: " + receiver + ", IP: " + addr
	print "Sending File '" + path + ("' [sz=%d] to VM: " % datasz) + receiver + " (TID=" + tid + ")"

	while 1:
	    # Try to send File's Data
	    sent = sendfile.sendfile(sock.fileno(), data.fileno(), position, )
	    
	    # End of File reached
	    if sent == 0:
	    	print "End of file reached, transmission succeeded."
	        break 
	    position += sent
# -------------------------------------------------------------------------------------------------------
# EOF evertestSendFile
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Listens on TCP Port until File was received
# -------------------------------------------------------------------------------------------------------
def evertestRecvFile(sock):

	name 		= evertestGetLocalName()
	test 		= evertestGetLocalTestId()
	addr 		= evertestGetVmIpAddr(test, name)
	senderaddr  = evertestGetVmIpAddr(test, "sender")
	chunks 		= []
	recvd  		= 0
	chunk  		= "-"
	accum 		= 0

	# Wait for incoming Connections from Sender
	while 1:
		(clientsocket, address) = serversocket.accept()
		if address == senderaddr:
			print "Connected to Sender VM!"
			break
		else:
			accum += 1
			if accum >= 10:
				print "Waiting for Connection from Sender..."
				accum = 0


	while len(chunk) != 0:
		chunk = sock.recv( 1024 )
		if chunk == '':
			print "Could not receive data."
			return ""
		chunks.append(chunk)
		recvd += len(chunk)
	return "".join(chunks)

	evertestCloseSocket(sock)
# -------------------------------------------------------------------------------------------------------
# EOF evertestSendFile
# -------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------------
# 
#--------------------------------------------------------------------------------------------------------
def evertestBreakSend(receiver, description):
	try:
		path = evertestGetLocalNetXml()
		print "Debug (netXml path): " + path
		root = xmltree.parse(path).getroot()
		for child in root.iter():
			if(child.tag == "host"):
				if(child.get("name") == receiver):
					receiverIp = child.get("ip")

		buffer_size = 2048
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
		buffer_size = 2048
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
		EVERTEST_MONITOR_PORT = evertestGetVmPort(evertestGetLocalTestId(), evertestGetLocalName())
		print "Monitor Port: " + str(EVERTEST_MONITOR_PORT)
		receiverIp = "192.168.0.211"
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

#actStatus = "Success!"
#evertestSendStatus(actStatus)