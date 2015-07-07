
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

while os.path.isfile("/mnt/spruce_util.py") != True:
	time.sleep(1)

def evertestExtractTest(dottest, testname):
	try:
		extractString = "/mnt/" + dottest
		extractPath = "/mnt/" + testname + "/"
		tfile = tarfile.open(extractString)
		if tarfile.is_tarfile(extractString):
			tfile.extractall(extractPath)
		else:
			logger.error("%s is not a tarfile.", extractString)
	except:
		e = sys.exc_info()[1]
		logger.error("Error in evertestExtractTest: \n %s", str(e))

getHostname = "hostname"
hostname = check_output(getHostname)
hostname = hostname.replace('\n', '')

dottest = check_output(["ls -LR /mnt/ | grep *.test*"], shell=True)
dottest = dottest.replace('\n', '')
testname = check_output(["ls -LR /mnt/ | grep *.test* | cut -d'.' -f 1"], shell=True)
testname = testname.replace('\n', '')

evertestExtractTest(dottest, testname)

#Script File
scriptFile = hostname + ".script"
sourceDir = "/mnt/" + testname + "/scripts/"
destination = workingDir
source = sourceDir + scriptFile
if (os.path.exists(source)):
	shutil.copy(source, destination)
else:
	logger.error("%s cannot be found!", source)

#Config File
configDir = "/mnt/" + testname + "/"
config = configDir + testname + ".conf"
source = config
destination = workingDir
if (os.path.exists(source)):
	shutil.copy(source, destination)
else:
	logger.error("%s cannot be found!", source)

#Other files
srcFilesDir = "/mnt/" + testname + "/files/"
if os.path.exists(srcFilesDir):
	shutil.copytree(srcFilesDir, filesPath, symlinks=False, ignore=None)
else:
	logger.error("%s does not exist!", srcFilesDir)

#Execute script
scriptFile = "/mnt/" + hostname + ".script"

runs = "python -B " + scriptFile
try:
	run = sub.Popen(runs, shell=True, stdout=sub.PIPE)
except:
	logger.error("Error on executing '%s'!", runs)
run.wait()

