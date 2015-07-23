Spruce - a distributed test runner
========
##Spruce v0.2

Spruce is a framework for testing software in several ways on "on-demand" VMs.

Thist are the main script used as testing framework:


| Module | Description |
|:--------:|:-------------|
| spruce_test_handler.py | This modules creates VMs from templates and gives them all needed data. |
| spruce_netcfg_host.py | This module rules networking stuff like creating virtual networks for every single testcase |
| spruce_netcfg_client.py | Same thing as _host.py, just less functions for use on a vm |
| spruce_util.py | This modules does what its' name says: It provides utilities. |
| spruce_monitor.py | Monitoring module |
| vm.py | The vm-side script runnig the test |

##How to set it up
###Dependencies (for a Ubuntu 15.04 host)
**Python**: python2.7, python-lxml, python-sendfile

