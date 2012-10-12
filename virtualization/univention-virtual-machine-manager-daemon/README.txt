=== Prerequisits ===
In /etc/xen/xend-config.sxp:
 (xend-unix-server yes)

On a management station:
 apt-get install univention-virtual-machine-manager-daemon

On a virtualization server:
 apt-get install univention-virtual-machine-manager-node-xen
 or
 apt-get install univention-virtual-machine-manager-node-kvm

=== Running ===
Start /usr/sbin/univention-virtual-machine-manager-daemon

Play with:
 /usr/sbin/uvmm groups

 /usr/sbin/uvmm nodes default

 /usr/sbin/uvmm-add xen:///
 /usr/sbin/uvmm-add xen://m230.xen.test/
 /usr/sbin/uvmm-add xen+unix:///
 /usr/sbin/uvmm-add qemu:///session

 /usr/sbin/uvmm query xen:///
 /usr/sbin/uvmm query xen://m230.xen.test/
 /usr/sbin/uvmm query xen+unix:///
 /usr/sbin/uvmm query qemu:///session

Crash libvirt with
 /usr/sbin/uvmm-rm xen:///
 /usr/sbin/uvmm-rm xen://m230.xen.test/
 /usr/sbin/uvmm-rm xen+unix:///
 /usr/sbin/uvmm-rm qemu:///session

=== Hints ===
 "uvmm XXX" is the same as calling the executable "uvmm-XXX"

=== Troubleshooting ===
1. Which version of libvirtd is installed?
	# dpkg-query -W libvirt-bin
	libvirt-bin     0.8.3-1.38.201008101339
2. Is libvirtd running?
	# ps $(pgrep libvirtd)
	  PID TTY      STAT   TIME COMMAND
	 3838 ?        Sl     0:59 /usr/sbin/libvirtd -l
3. Is libvirtd usable?
	# virsh -c xen+unix:/// list --all
	 Id Name                 State
	----------------------------------
	  0 Domain-0             running
	  1 winxp-test           idle
	  - ucs24-6666           shut off
4. Which version of uvmmd is installed?
	# dpkg-query -W univention-virtual-machine-manager-daemon
	univention-virtual-machine-manager-daemon       0.10.2-2
5. Is uvmmd running?
	# ps $(pgrep -f /usr/bin/python.*univention-virtual-machine-manager-daemon)
	  PID TTY      STAT   TIME COMMAND
	 3823 ?        Sl    45:21 /usr/bin/python2.4 /usr/sbin/univention-virtual-m
6. Is uvmmd usable?
	# uvmm nodes default
	DATA:
	['xen://xen4.opendvdi.local/',
	 'xen://xen2.opendvdi.local/',
	 'xen://xen1.opendvdi.local/',
	 'qemu://xen2.opendvdi.local/system']
7. Is the node itself reachable?
	# uvmm query xen://$(hostname -f)/
DATA:
{'capabilities': [{'arch': u'i686',...}],
 ...
 'domains': [{'annotations': {'description': '',...}}]
 ...
 'last_try': 1285071297.233072,
 'last_update': 1285071297.233072,
 ...
 'storages': [{'active': True,...}]}

8. If UMC doesn't show domains anymore, compare the output of the following
commands:
	# virsh -c xen:/// list
	# virsh -c xen+unix:/// list
	If they differ, restart libvirtd:
	# /etc/init.d/libvirt-bin restart
