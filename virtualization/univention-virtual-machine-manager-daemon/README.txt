=== Prerequisites ===
On a management station:
 apt-get install univention-virtual-machine-manager-daemon

On a virtualization server:
 apt-get install univention-virtual-machine-manager-node-kvm

=== Running ===
Start /usr/sbin/univention-virtual-machine-manager-daemon

Play with:
 /usr/sbin/uvmm groups

 /usr/sbin/uvmm nodes default

 /usr/sbin/uvmm-add qemu:///session

 /usr/sbin/uvmm query qemu:///session

Crash libvirt with
 /usr/sbin/uvmm-rm qemu:///session

=== Hints ===
 "uvmm XXX" is the same as calling the executable "uvmm-XXX"

=== Troubleshooting ===
1. Which version of libvirtd is installed?
	# dpkg-query -W libvirt0
	libvirt0     1.2.7-11.128.201410021141
2. Is libvirtd running?
	# ps $(pgrep libvirtd)
	  PID TTY      STAT   TIME COMMAND
	 3838 ?        Sl     0:59 /usr/sbin/libvirtd -l
3. Is libvirtd usable?
	# virsh -c qemu:///system list --all
	 Id Name                 State
	----------------------------------
	  0 Domain-0             running
	  1 winxp-test           idle
	  - ucs24-6666           shut off
4. Which version of uvmmd is installed?
	# dpkg-query -W univention-virtual-machine-manager-daemon
	univention-virtual-machine-manager-daemon       4.0.1-1
5. Is uvmmd running?
	# ps $(pgrep -f /usr/bin/python.*univention-virtual-machine-manager-daemon)
	  PID TTY      STAT   TIME COMMAND
	 3823 ?        Sl    45:21 /usr/bin/python2.6 /usr/sbin/univention-virtual-m
6. Is uvmmd usable?
	# uvmm nodes default
	DATA:
	['qemu://qemu.ucs.local/system']
7. Is the node itself reachable?
	# uvmm query qemu://$(hostname -f)/system
DATA:
{'capabilities': [{'arch': u'i686',...}],
 ...
 'domains': [{'annotations': {'description': '',...}}]
 ...
 'last_try': 1285071297.233072,
 'last_update': 1285071297.233072,
 ...
 'storages': [{'active': True,...}]}
