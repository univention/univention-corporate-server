#!/usr/bin/python
from __future__ import print_function
import libvirt
c = libvirt.open('qemu:///system')
print(c.listDefinedStoragePools())
print(c.listStoragePools())
p = c.storagePoolLookupByName('default')
p.isActive()
p.isPersistent()
