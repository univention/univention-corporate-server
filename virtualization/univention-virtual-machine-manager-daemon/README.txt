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
