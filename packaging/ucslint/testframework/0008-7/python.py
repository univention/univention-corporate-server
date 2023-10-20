#!/usr/bin/python2.7
from __future__ import print_function
from univention.lib.misc import custom_username, custom_groupname
print("Administrator", custom_username("Administrator"),)
print("Domain Admins", custom_groupname("Domain Admins"),)
print("Administrator", custom_groupname("Administrator"),)
print("Windows Hosts", custom_groupname("Windows Hosts"),)
