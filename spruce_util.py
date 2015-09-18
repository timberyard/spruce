# -------------------------------------------------------------------------------------------------------
# This Python module implements useful additional routines that will be provided for the virtual machines
# to use during their testcase execution.
# -------------------------------------------------------------------------------------------------------

##!!!Don't actually use the SendFile functions!!!

from subprocess import check_output
import sendfile
import subprocess
import traceback
import socket
import struct
import select
import errno
import time
import sys
import os
from lxml import etree as xmltree

from glob			 import *
from spruce_netcfg_client import *
from collections import OrderedDict

EVERTEST_TCP_FILE_PORT 		= 8021
EVERTEST_SOCKET_MODE_SEND 	= 0
EVERTEST_SOCKET_MODE_RECV 	= 1
EVERTEST_WORKER_ROOT_DIR	= "/mnt"
HOST_IP 					= "192.168.0.226"
HOST_IP						= "192.168.122.1"

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
def runBash(command):
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
# EOF runBash
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the Name of the virtual Machine that the Script is running on.
# -------------------------------------------------------------------------------------------------------
def getHostname():

	# script = glob(EVERTEST_WORKER_ROOT_DIR + "/*.script")[0]
	# script = (EVERTEST_WORKER_ROOT_DIR + "/*.script")
	# replaceString = EVERTEST_WORKER_ROOT_DIR + "/"

	getHostname = "hostname" # WORKAROUND / FIX : Local name is the vm's hostname.. looking .script is not working anymore because every testfile is now a normal .py file
	hostname = check_output(getHostname)
	hostname = hostname.replace('\n', '')

	return hostname
#	return script.replace(replaceString, "").replace(".script", "")
# -------------------------------------------------------------------------------------------------------
# EOF getHostname
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the Name of the Test (Network) that the Script is currently running as a Part of.
# -------------------------------------------------------------------------------------------------------
def getLocalTestId():

	conf = glob(EVERTEST_WORKER_ROOT_DIR + "/*.conf")[0]
	replaceString = EVERTEST_WORKER_ROOT_DIR + "/"

	return conf.replace(replaceString, "").replace(".conf", "")
# -------------------------------------------------------------------------------------------------------
# EOF getHostname
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the actual tests network XML
# -------------------------------------------------------------------------------------------------------
def getLocalNetXml():
	try:
		conf = glob(EVERTEST_WORKER_ROOT_DIR + "/*.net")[0]
		return conf
	except:
		e = sys.exc_info()[edl]
		print "Error in breakSend: \n" + str(e)
# -------------------------------------------------------------------------------------------------------
# EOF getLocalNetXml
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Creates and opens a TCP Socket that is either setup to listen to a specified port or to send Data
# to it. Returns the created Socket Object on Success.
# -------------------------------------------------------------------------------------------------------
def openSocket(tid, vm, port, mode):

	addr = getVmIpAddr(tid, vm)
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
# EOF openSocket
# -------------------------------------------------------------------------------------------------------


def closeSocket(socket):

	socket.shutdown()
	socket.close()


# -------------------------------------------------------------------------------------------------------
# Sends a File via TCP to the specified virtual Machine
# -------------------------------------------------------------------------------------------------------
def sendFile(sock, filename, tid, receiver):

	path = EVERTEST_WORKER_ROOT_DIR + "/" + filename
	
	if receiver == "localhost":
		addr = "127.0.0.1"
	else:
		addr = getVmIpAddr(tid, receiver)
	
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
# EOF sendFile
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Listens on TCP Port until File was received
# -------------------------------------------------------------------------------------------------------
def receiveFile(sock):

	name 		= getHostname()
	test 		= getLocalTestId()
	addr 		= getVmIpAddr(test, name)
	senderaddr  = getVmIpAddr(test, "sender")
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
			if accum >= 10: #for what purpose?
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

	closeSocket(sock)
# -------------------------------------------------------------------------------------------------------
# EOF sendFile
# -------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------------
# 
#--------------------------------------------------------------------------------------------------------
def breakSend(receiver, description):
	try:
		#path = getLocalNetXml()
		#print "Debug (netXml path): " + path
		#root = xmltree.parse(path).getroot()
		#for child in root.iter():
		#	if(child.tag == "host"):
		#		if(child.get("name") == receiver):
		#			receiverIp = child.get("ip")

		receiverIp = receiver
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
		print "Error in breakSend: \n" + str(e)
#--------------------------------------------------------------------------------------------------------
# EOF breakSend
#--------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------------
#
#--------------------------------------------------------------------------------------------------------
def breakListen(rcvMessage, timeout = None):
	try:
		myIp = "127.0.0.1"
		buffer_size = 2048
		message = "Got it."
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(timeout)
		s.bind(('', EVERTEST_TCP_FILE_PORT))
		print "Now waiting for message"
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
		return 0
		
	except timeout:
		return 1
	except:
		e = sys.exc_info()[edl]
		print "Error in breakListen: \n" + str(e)
#--------------------------------------------------------------------------------------------------------
# EOF evertestWait
#--------------------------------------------------------------------------------------------------------

# def initExternalMonitor(exHost, exPort):
# 	i = 1;
# 	while false:
# 		buffer_size = 1024
# 		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 		s.connect((exHost, exPort)) # <- Tuple? Why double brackets?
# 		s.send(status)
# 		response = s.recv(buffer_size)
# 		s.close()
# 		if response == "I'm here!":
# 			return true
# 		else:
# 			if i < 3:
# 				return false
# 			else:
# 				return 	# Possible? Want to exit loop after 3 failed tries

#--------------------------------------------------------------------------------------------------------
# Currently: Add support for dedicated monitoring host -> send logs to developers device instead/additional to the VM-Host
#--------------------------------------------------------------------------------------------------------
def sendStatus(status, exHost="null", exPort="null"): # If host is specified by user, log copies will be sent to that ip -> if fail after 3 inital tries -> abort
	try:
		monitor_port = getVmMonitoringPort(getLocalTestId(), getHostname(), "test") # "test" represents the monitoring mode -> look at spruce_monitor.py
		print "Monitor Port: " + str(monitor_port)
		buffer_size = 1024
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((HOST_IP, monitor_port))
		s.send(status)
		data = s.recv(buffer_size)
		s.close()

#		if (exHost, exPort != "null" && initExternalMonitor(exHost, exPort) == true):
#			pass # Insert function to send copy of messages
#			buffer_size = 1024
#			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#			s.connect((exHost, exPort)) # <- Tuple? Why double brackets?
#			s.send(status)


		print "Got answer: " + str(data)
	except:
		print(traceback.format_exc())
#		e = sys.exc_info()[edl]
#		print "Error in sendStatus: \n" + str(e)
		exc_type, exc_obj, exc_tb = sys.exc_info()
   	 	fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
   		print(exc_type, fname, exc_tb.tb_lineno)
#--------------------------------------------------------------------------------------------------------
# EOF sendStatus
#--------------------------------------------------------------------------------------------------------

def initNetwork(dev):
	try:
		runBash("sudo tc qdisc add dev {} parent root handle 1:0 htb default 1".format(dev))
	except:
		e = sys.exc_info()[edl]
		print "Error in initNetwork: \n" + str(e)

def setNetworkBandwidth(dev, bandwidth):
	try:
		runBash("sudo tc class add dev {0} parent 1:0 classid 1:1 htb rate {1} ceil {1}".format(dev, bandwidth)) #ceil defines the maximum bandwidth rate including borrowing rate from other classes
	except:
		e = sys.exc_info()[edl]
		print "Error in setNetworkBandwidth: \n" + str(e)

def setNetworkProperties(dev, *arg):
	try:
		args = " ".join(arg)
		runBash("sudo tc qdisc add dev {} parent 1:1 handle 2:0 netem {}".format(dev, args))	#Delay has to be "Xms", if it shall be a +/- value, write "Xms Yms" where Xms is the variation
	except:
		e = sys.exc_info()[edl]
		print "Error in setNetworkProperties: \n" + str(e)

def resetNetwork(dev):
	try:
		runBash("sudo tc qdisc del dev {} root".format(dev))
	except:
		e = sys.exc_info()[edl]
		print "Error in resetNetwork: \n" + str(e)

##############################################################################################################################
# Base code source: https://bitbucket.org/delroth/python-ping/src/7084c31fa1603a1071c30525ae0431da42ce93cd/ping.py?at=default
##############################################################################################################################

ICMP_ECHO_REQUEST = 8 # Seems to be the same on Solaris.

def checksum(source_string):
    """
    I'm not too confident that this is right but testing seems
    to suggest that it gives the same answers as in_cksum in ping.c
    """
    sum = 0
    count_to = (len(source_string) / 2) * 2
    for count in xrange(0, count_to, 2):
        this = ord(source_string[count + 1]) * 256 + ord(source_string[count])
        sum = sum + this
        sum = sum & 0xffffffff # Necessary?

    if count_to < len(source_string):
        sum = sum + ord(source_string[len(source_string) - 1])
        sum = sum & 0xffffffff # Necessary?

    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff

    # Swap bytes. Bugger me if I know why.
    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer

def receive_one_ping(my_socket, id, timeout):
    """
    Receive the ping from the socket.
    """
    while True:
        beginSelect = time.time()
        waitForSocket = select.select([my_socket], [], [], timeout)
        if waitForSocket[0] == []: # Timeout
            return
        selectTime = (time.time() - beginSelect)

        time_received = time.time()
        received_packet, addr = my_socket.recvfrom(1024)
        icmpHeader = received_packet[20:28]
        type, code, checksum, packet_id, sequence = struct.unpack(
            "bbHHh", icmpHeader
        )

	timeout = timeout - selectTime
        if timeout <= 0:
            return

        if packet_id == id:
            bytes = struct.calcsize("d")
            time_sent = struct.unpack("d", received_packet[28:28 + bytes])[0]
            return time_received - time_sent

def send_one_ping(my_socket, dest_addr, id, psize):
    """
    Send one ping to the given >dest_addr<.
    """
    dest_addr  =  socket.gethostbyname(dest_addr)

    # Remove header size from packet size
    psize = psize - 8

    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    my_checksum = 0

    # Make a dummy heder with a 0 checksum.
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, id, 1)
    bytes = struct.calcsize("d")
    data = (psize - bytes) * "Q"
    data = struct.pack("d", time.time()) + data

    # Calculate the checksum on the data and the dummy header.
    my_checksum = checksum(header + data)

    # Now that we have the right checksum, we put that in. It's just easier
    # to make up a new header than to stuff it into the dummy.
    header = struct.pack(
        "bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), id, 1
    )
    packet = header + data
    my_socket.sendto(packet, (dest_addr, 1)) # Don't know about the 1


def do_one(dest_addr, timeout, psize):
    """
    Returns either the delay (in seconds) or none on timeout.
    """
    icmp = socket.getprotobyname("icmp")
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    except socket.error, (errno, msg):
        if errno == 1:
            # Operation not permitted
            msg = msg + (
                " - Note that ICMP messages can only be sent from processes"
                " running as root."
            )
            raise socket.error(msg)
        raise # raise the original error

    my_id = os.getpid() & 0xFFFF

    send_one_ping(my_socket, dest_addr, my_id, psize) #	Send ping
    delay = receive_one_ping(my_socket, my_id, timeout) # Wait for response to sent ping

    my_socket.close()
    return delay


def verbose_ping(dest_addr, timeout = 2, count = 20, psize = 64):
	"""
    Send `count' ping with `psize' size to `dest_addr' with
	the given `timeout' and display the result.
	"""
	allPing = list()
	startTime = time.time()
	for i in xrange(count):
		print "ping %s ... seq=%s ..." % (dest_addr, i),
		try:
			delay  =  do_one(dest_addr, timeout, psize)
		except socket.gaierror, e:
			print "failed. (socket error: '%s')" % e[1]
			break

		if delay  ==  None:
			print "failed. (timeout within %ssec.)" % timeout
		else:
			delay  =  delay * 1000
			print "got ping in %0.4f ms" % delay
			allPing.append(delay)

	endTime = (time.time() - startTime) * 1000 #s -> ms
	loss = 100 - (len(allPing) * 100 / count)

	return allPing, loss, endTime
	print
	
# initNetwork("eth0")
# setNetworkBandwidth("eth0", "100mbit")
# setNetworkProperties("eth0", "delay 0ms", "loss 0%")
# count = 50
# ping, loss, pingTime = verbose_ping("google.de", timeout = 0.1, count = count)
		
# average_time = 0
# for p in ping:
# 	average_time += p
# average_time = average_time / len(ping)
# resetNetwork("eth0")
