#!/usr/bin/python
import libvirt
c = libvirt.open('qemu:///system')
print c.listDefinedStoragePools()
print c.listStoragePools()
p = c.storagePoolLookupByName('default')
p.isActive()
p.isPersistent()
