#
# Univention Directory Custom Export
#  listener module: write LDAP changes to a file
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

name='custom_export'
description='export customized by /etc/univention/listener-export.conf'

import listener
import string, re, univention.debug, os, time

# parse configuration file
conffile = '/etc/univention/listener-export.conf'
try:
	fp = open(conffile)
except IOError:
	univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'custom_export: Failed to open %s.' % conffile)
	raise 'no configuration'

config = []
for line in fp.readlines():
	line=line[0:-1]
	pos=line.find('#')
	if pos > -1:
		line=line[:pos]
	line=line.lstrip()

	if not line:
		continue

	cols=line.split('::')
	if len(cols) < 3:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'custom_export: Error while parsing %s: malformed line %s' % (conffile,line))
		continue

	file=cols[0]
	del cols[0]
	ocs=re.split(' *, *', cols[0])
	del cols[0]
	format=string.join(cols, '::')

	config.append((file, ocs, format))
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'custom_export: config file %s ocs %s format %s' % (file,ocs,format))


modfilters=[]
for file, ocs, format in config:
	if len(ocs) > 1:
		modfilters.append('&(objectClass='+string.join(ocs, ')(objectClass=')+')')
	elif len(ocs) == 1:
		modfilters.append('objectClass='+ocs[0]+'')
	else:
		modfilters.append('objectClass=*')
if len(modfilters) > 1:
	filter='(|('+string.join(modfilters, ')(')+'))'
elif len(modfilters) == 1:
	filter='('+modfilters[0]+')'
else:
	raise 'bad configuration'
attributes=[]

univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'custom_export: filter %s' % (filter))

def handler(dn, new, old):
	for file, ocs, format in config:
		matches=1
		for oc in ocs:
			if not oc in new.get('objectClass', []) and \
					not oc in old.get('objectClass', []):
				matches=0
				break
		if not matches:
			continue

		f=format

		if new and old:
			modtype = 'modify'
		elif new and not old:
			modtype = 'add'
		elif not new and old:
			modtype = 'delete'
		else:
			raise 'error'

		for attr in re.findall('<([^>]+)>', format):
			if attr == 'LDAP-MODTYPE':
				value=modtype
			elif attr == "TIMESTAMP":
				value="%f"%time.time()
			else:
				if not modtype == 'delete':
					values=new.get(attr, [''])
				else:
					values=old.get(attr, [''])
				value=''
				for val in values:
					if len(value):
						value="%s %s"%(value,val)
					else:
						value=val

			f=f.replace('<'+attr+'>', value)

		listener.setuid(0)
		try:
			fp = open(file, 'a')
			print >>fp, f
			fp.close()
			os.chmod(file,int("0600",0))
			os.chown(file,0,0)
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'custom_export: append to file %s line %s' % (file, f))
		finally:
			listener.unsetuid()
