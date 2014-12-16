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
import system

#Import evertest modules
from evertest_test_handler import *
from evertest_netcfg import *
from evertest_util import *

#--------------------------------------------------------------------------------------
# Evertest main core functionalities
#--------------------------------------------------------------------------------------
def evertest_setup_test(test):
	process = runTest(test)
	process.wait()
#--------------------------------------------------------------------------------------
# EOF evertest_core_main
#--------------------------------------------------------------------------------------

