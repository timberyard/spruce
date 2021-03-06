
# File I/O
import sys
import os
import time
import logging
import subprocess as sub
import shutil
import tarfile
from subprocess import check_output

###############
logging.basicConfig(format='%(levelname)s : %(name)s : %(message)s', filename="vm.log", level=logging.INFO)
###############

workingDir = "/mnt/"
filesPath  = "/mnt/"

HOST_IP = "192.168.0.226"
HOST_IP = "192.168.122.1"

startTime = time.time()

while os.path.isfile("/mnt/spruce_util.py") != True: #util file is the last one being sent to the vm
	time.sleep(1)
try:
	try:
		from spruce_util import *
	except:
		e =sys.exc_info()[1]
		logging.error("Cannot import spruce_util!")
		raise

	def extractTest(dottest, testname):
		try:
			extractString = "/mnt/" + dottest
			extractPath = "/mnt/" + testname + "/"
			tfile = tarfile.open(extractString)
			if tarfile.is_tarfile(extractString):
				tfile.extractall(extractPath)
			else:
				logging.error("%s is no tarfile or does not exist!", extractString)
				raise IOError
		except IOError:
			logging.error("Tarfile not found, aborting!")
			raise
		except:
			e = sys.exc_info()[1]
			logging.error("Error in extractTest: \n %s", str(e))
			raise

	getHostname = "hostname"
	hostname = check_output(getHostname)
	hostname = hostname.replace('\n', '')

	dottest = check_output(["ls -LR /mnt/ | grep *.tar*"], shell=True)
	dottest = dottest.replace('\n', '')
	testname = check_output(["ls -LR /mnt/ | grep *.tar* | cut -d'.' -f 1"], shell=True)
	testname = testname.replace('\n', '')

	extractTest(dottest, testname)

	#Script File
	source = "/mnt/{}/scripts/{}.py".format(testname, hostname)
	if (os.path.exists(source)):
		shutil.copy(source, workingDir)
	else:
		logging.error("Script file cannot be found!")
		raise

	#Config File
	config = "/mnt/{0}/{0}.conf".format(testname)
	if (os.path.exists(config)):
		shutil.copy(config, workingDir)
	else:
		logging.error("Config file cannot be found!")
		raise

	#Other files
	fileList = os.listdir("/mnt/{}/files/".format(testname))
	fileList = ["/mnt/{}/files/".format(testname) + filename for filename in fileList]

	for f in fileList:
	    shutil.copy2(f, filesPath)

	#Execute script
	scriptFile = "/mnt/" + hostname + ".py"

	runs = "python -B " + scriptFile
	try:
		logging.info("Trying to execute test script")
		# run = sub.Popen(runs, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE) #Changed sub.PIPE to sys.stdout referring to http://stackoverflow.com/a/20196781 -> broken Pipe [32] Error fix
		run = sub.Popen(runs, shell=True)
		out = run.communicate()
		logging.info(out[0])
		if out[1]:
			logging.error(out[1])
		logging.info("initialized server")
		#sendStatus("[finish]")
	except:
		logging.error("Error on executing '{}'!".format(runs))
		raise

except:
	e = sys.exc_info()[1]
	logging.error("Reraised exception: {}".format(e))
	#with open("vm.log") as l:
	#	for line in l:
	#		sendStatus("[info] - " + line)

finally:
#	command = "scp /mnt/vm.log jan@{}:/home/jan/Schreibtisch/everbase/".format(HOST_IP)
#	process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#	process.communicate()
	endTime = (time.time() - startTime)
	sendStatus("[time] - {}".format(math.ceil(endTime*100000)/100000)) # round to 5 decimal places	
	sendStatus("[finish]")
	sys.exit()

