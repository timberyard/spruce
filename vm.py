
# File I/O
import sys
import os
import time
import subprocess as sub
import shutil
import tarfile
from subprocess import check_output

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
			print extractString + " is not a tarfile."
	except:
		e = sys.exc_info()[1]
		print "Error in evertestExtractTest: \n" + str(e)

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
shutil.copy(source, destination)

#Config File
configDir = "/mnt/" + testname + "/"
config = configDir + testname + ".conf"
source = config
destination = workingDir
shutil.copy(source, destination)

#Other files
srcFilesDir = "/mnt/" + testname + "/files/"
if os.path.exists(srcFilesDir):
	shutil.copytree(srcFilesDir, filesPath, symlinks=False, ignore=None)

#Execute script
scriptFile = "/mnt/" + hostname + ".script"
os.system("python -B " + scriptFile)
