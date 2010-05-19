=== Prerequisits ===
In /etc/xen/xend-config.sxp:
 (xend-unix-server yes)

In /etc/libvirt/libvirtd.conf:
 listen_tls = 1
 tls_allowed_dn_list = ["C=DE,ST=Bremen,L=Bremen,O=U,OU=IT,CN=ms22.xen.test,*",]

["C=%(ssl/country)s,ST=%(ssl/state)s,L=%(ssl/locality)s,O=%(ssl/organization)s,OU=%(ssl/organizationalunit)s,CN=%(hostname)s.%(domainname)s,*" % univention.config_registry.ConfigRegistry().load()]

On a management station:
 apt-get install univention-virtual-machine-manager-daemon
 ln /etc/univention/ssl/$HOSTNAME/private.key /etc/pki/libvirt/private/clientkey.pem
 ln /etc/univention/ssl/$HOSTNAME/cert.pem /etc/pki/libvirt/clientcert.pem
 ln /etc/univention/ssl/ucsCA/CAcert.pem /etc/pki/CA/cacert.pem

On a virtualization server:
 apt-get install libvirt-bin
 ln /etc/univention/ssl/$HOSTNAME/private.key /etc/pki/libvirt/private/serverkey.pem
 ln /etc/univention/ssl/$HOSTNAME/cert.pem /etc/pki/libvirt/servercert.pem
 ln /etc/univention/ssl/ucsCA/ctl/crl.pem /etc/pki/CA/crl.pem
 ln /etc/univention/ssl/ucsCA/CAcert.pem /etc/pki/CA/cacert.pem

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
