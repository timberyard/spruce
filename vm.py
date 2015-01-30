
# File I/O
import sys
import os
import subprocess as sub
import shutil
import tarfile
from subprocess import check_output

path = "/var/testing/"

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

dottest = check_output(["ls -LR /mnt/ | grep .test"], shell=True)
dottest = dottest.replace('\n', '')
testname = check_output(["ls -LR /mnt/ | grep .test | cut -d'.' -f 1"], shell=True)
testname = testname.replace('\n', '')

evertestExtractTest(dottest, testname)

scriptFile = hostname + ".script"
sourceDir = "/mnt/" + testname + "/scripts/"

source = sourceDir + scriptFile
destination = "/mnt/scripts/"
shutil.copy2(source, destination)

destination = "/mnt/"
source = sourceDir + "evertest_netcfg.py"
shutil.copy(source, destination)

source = sourceDir + "evertest_util.py"
shutil.copy2(source, destination)

configDir = "/mnt/" + testname + "/"
config = configDir + testname + ".conf"
source = config
shutil.copy2(source, destination)

filesDir = "/mnt/" + testname + "/files/" #has to be -r to copy whole /files/ dir recursively
shutil.copytree(filesDir, destination, symlinks=False, ignore=None)

scriptFile = "/mnt/" + hostname + ".script"
os.system("python -B " + scriptFile)
