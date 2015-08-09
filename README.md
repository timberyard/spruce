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
**Python:** ```sudo apt-get install python2.7, python-lxml, python-sendfile```

**Virtualization:** ```sudo apt-get install libvirt-bin virt-manager libguestfs-dev libguestfs-tools```

**Test scripts:** ```git clone https://github.com/timberyard/spruce``` -> *I recommend to clone to /var/spruce/*

###Assemble a test package
A test package consists of a simple .tar file. It's packed as following:

```  
dummytest.tar
  |-- dummytest.conf
  |-- scripts
  |   |-- vm1.py
  |   |-- vm2.py
  |
  |-- files
  |   |-- somedependecy.py
  |   |-- ...
```  
Let's start with the ***dummytest*.conf**, it's a simple xml-file, .conf is just for easier handling:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rootElement>
	<info vmcount='2'/>
	<vm name="vm1" template="client_15.04" script="vm1.py"/>
	<vm name="vm2" template="server_15.04" script="vm2.py"/>
</rootElement>
```
The template attribute names the vm that is being cloned to run the test on it, vmcount tells the test handler how many vms he is handling.

The **vm*.py** files are the scripts being executed by the vms as specified in the config. The can contain everything from `print "foo"` through to complex algorithms etc. In **/files/** you should store everything your test scripts require as for example your own python libraries or utility files.

###Start a testcase
**Just this one command line:** ```sudo python spruce_test_handler.py -n=dummytest``` where you have to replace *testname* with the tests plain name / the name of the testfile without fileending.


##To do:
- Add support for dedicated monitoring; sent logging either to VM-Host or to remote system, e.g. developers device


