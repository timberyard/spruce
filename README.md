Spruce - a distributed test runner
========
##Spruce v0.1

Spruce is a framework for testing software in several ways on "on-demand" VMs.

There are four main modules used as testing framework:

1. spruce_test_handler.py - This modules creates VMs from templates and gives them all needed data.
2. spruce_netcfg_host.py - This module rules networking stuff like creating virtual networks for every single testcase (full functions)
3. spruce_netcfg_client.py - Same thing as _host.py, just less functions
4. spruce_util.py - This modules does what its' name says: It provides utilities.
5. spruce_monitor.py - Monitoring module

Also there are:

1. vm.py - This is the script running on the vm that collects data and executes the test
2. spruce-pkgmgr.jar - This little java applet lets the user create .test packages and place them at the host machine
