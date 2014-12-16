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
# This modul is going to be the Evertest Core module.
# It's functions are handling all Evertest modules like at the moment:
#		- evertest_test_handler
#		- evertest_netcfg
#		- evertest_util
# Also it will handle to generate and build the WebUI's contents and manage client interactions with the evertest System.
# -------------------------------------------------------------------------------------------------------

#Import base functions
import os
import sys

#Import evertest modules
from evertest_util import *


#--------------------------------------------------------------------------------------
# Set EVETEST_DEBUG_LEVEL TO - 0: Short debug message; 1: explicit debug message
#--------------------------------------------------------------------------------------
EVERTEST_DEBUG_LEVEL = 1
edl = EVERTEST_DEBUG_LEVEL
#--------------------------------------------------------------------------------------
# EOF Debug-Settings
#--------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
# Returns the Value assigned to a Command Line Parameter. (--param=value) 
# If no Value was passed in, the specified default will be returned.
# -------------------------------------------------------------------------------------------------------
def handleCoreShellParam(param, default):

	for cmdarg in sys.argv:
		if(("--" + param + "=") in cmdarg):
			return str(cmdarg.replace(("--" + param + "="), ""))
	return default
# -------------------------------------------------------------------------------------------------------
# EOF shellFlag
# -------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------
# Evertest main core functionalities
#--------------------------------------------------------------------------------------
def evertest_setup_test(test):
	try:
		process = runTest(test)
		process.wait()
	except:
		e = sys.exc_info()[edl]
		print "Error in run: \n" + str(e)
#--------------------------------------------------------------------------------------
# EOF evertest_core_main
#--------------------------------------------------------------------------------------