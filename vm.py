
# File I/O
import sys
import os
import logging
import time
import subprocess as sub
import shutil
import tarfile
from subprocess import check_output

###############
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# create handler for filelogging
handler = logging.FileHandler('vm.log')
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)
###############

workingDir = "/mnt/"
filesPath  = "/mnt/files"

#while os.path.isfile("/mnt/spruce_util.py") != True: #util file is the last one being sent to the vm
#	time.sleep(1)

from spruce_util import *

def evertestExtractTest(dottest, testname):
	try:
		extractString = "/mnt/" + dottest
		extractPath = "/mnt/" + testname + "/"
		tfile = tarfile.open(extractString)
		if tarfile.is_tarfile(extractString):
			tfile.extractall(extractPath)
		else:
			logger.error("%s is no tarfile or does not exist!", extractString)
			raise IOError
	except IOError:
		logger.error("Tarfile not found, aborting!")
		evertestSendStatus("[error] - Tarfile not found, aborting!")
		evertestSendStatus("[finish]")
		sys.exit()
	except:
		e = sys.exc_info()[1]
		logger.error("Error in evertestExtractTest: \n %s", str(e))

getHostname = "hostname"
hostname = check_output(getHostname)
hostname = hostname.replace('\n', '')

dottest = check_output(["ls -LR /mnt/ | grep *.tar*"], shell=True)
dottest = dottest.replace('\n', '')
testname = check_output(["ls -LR /mnt/ | grep *.tar* | cut -d'.' -f 1"], shell=True)
testname = testname.replace('\n', '')

evertestExtractTest(dottest, testname)

#Script File
source = "/mnt/{}/scripts/{}.script".format(testname, hostname)
if (os.path.exists(source)):
	shutil.copy(source, workingDir)
else:
	logger.error("Script file cannot be found!")
	evertestSendStatus("[error] - Script file not found, aborting!")
	evertestSendStatus("[finish]")
	sys.exit()

#Config File
config = "/mnt/{0}/{0}.conf".format(testname)
if (os.path.exists(config)):
	shutil.copy(config, workingDir)
else:
	logger.error("Config file cannot be found!")
	evertestSendStatus("[error] - Config file not found, aborting!")
	evertestSendStatus("[finish]")
	sys.exit()

#Other files
srcFilesDir = "/mnt/{}/files/".format(testname)
if os.path.exists(srcFilesDir):
	shutil.copytree(srcFilesDir, filesPath, symlinks=False, ignore=None)

#Execute script
scriptFile = "/mnt/" + hostname + ".script"

runs = "python -B " + scriptFile
try:
	run = sub.Popen(runs, shell=True, stdout=sub.PIPE)
except:
	logger.error("Error on executing '{}'!".format(runs))
	evertestSendStatus("[error] - Error on executing '{}'!".format(runs))
	evertestSendStatus("[finish]")
#run.wait()

