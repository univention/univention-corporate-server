#!/usr/bin/python2.4

import os, sys
import debian_bundle
import debian_bundle.debian_support

OLD_FILENAME='/var/lib/univention-client-root/var/lib/dpkg/status'
NEW_FILENAME='/usr/share/univention-thin-client-basesystem/status'

if not os.path.exists(OLD_FILENAME):
	print 'ERROR: %s does not exist.' % OLD_FILENAME
	sys.exit(1)
if not os.path.exists(NEW_FILENAME):
	print 'ERROR: %s does not exist.' % NEW_FILENAME
	sys.exit(1)

status_old=debian_bundle.debian_support.PackageFile(OLD_FILENAME)
status_new_stream=debian_bundle.debian_support.PackageFile(NEW_FILENAME)
status_new={}
for pn in status_new_stream:
	status_new[pn[0][1]]=pn

status_result={}

def package_print(package):
	for entry in package:
		if entry[0] == 'Description':
			print '%s: %s' % (entry[0], entry[1].replace('\n','\n ').replace('\n \n', '\n .\n'))
		elif entry[0] == 'Conffiles':
			print '%s: %s' % (entry[0], entry[1].replace('\n','\n ').replace('\n \n', '\n .\n'))
		else:
			print '%s: %s' % (entry[0], entry[1])
	print ''

for old_package in status_old:
	package_name=old_package[0][1]
	if package_name in status_new.keys():
		package_print(status_new[package_name])
	else:
		package_print(old_package)

sys.exit(0)

