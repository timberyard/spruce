Spruce Repository
========

This is the main Spruce repository.
Spruce is a framework for testing software in several ways on "on-demand" VMs.

There are four main modules used as testing framework.

1. spruce_test_handler.py - This modules creates VMs and gives them all needed data.
2. spruce_netcfg_host.py - This module rules networking stuff like creating virtual networks for every single testcase (full functions)
3. spruce_netcfg_client.py - Same thing as _host.py, just less functions
4. spruce_util.py - This modules does what its' name says: It provides utilities.
5. spruce_monitor.py - Monitoring module --- Work in progress.
