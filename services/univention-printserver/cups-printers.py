# -*- coding: utf-8 -*-
#
# Univention Print Server
#  listener module: management of CUPS printers
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

import listener
import os, string
import univention.debug

hostname=listener.baseConfig['hostname']
domainname=listener.baseConfig['domainname']
ip=listener.baseConfig['interfaces/eth0/address']

name='cups-printers'
description='Manage CUPS printer configuration'
filter='(|(objectClass=univentionPrinter)(objectClass=univentionPrinterGroup))'
attributes=['univentionPrinterSpoolHost', 'univentionPrinterModel', 'univentionPrinterURI', 'univentionPrinterLocation', 'description', 'univentionPrinterSambaName','univentionPrinterPricePerPage','univentionPrinterPricePerJob','univentionPrinterQuotaSupport','univentionPrinterGroupMember']

def lpadmin(args):
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "cups-printers: lpadmin args=%s" % args)

	listener.run('/usr/sbin/univention-lpadmin', ['univention-lpadmin']+args, uid=0)

def pkprinters(args):
	listener.setuid(0)
	try:
		if os.path.exists("/usr/sbin/pkprinters"):
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "cups-printers: pkprinters args=%s" % args)
			os.system("/usr/sbin/pkprinters %s" % string.join(args, ' '))
		elif os.path.exists("/usr/bin/pkprinters"):
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "cups-printers: pkprinters args=%s" % args)
			os.system("/usr/bin/pkprinters %s" % string.join(args, ' '))
		else:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "cups-printers: pkprinters binary not found")
	finally:
		listener.unsetuid()

def filter_match(object):
	if object.has_key('univentionPrinterSpoolHost'):
		for i in range(0,len(object['univentionPrinterSpoolHost'])):
			if object['univentionPrinterSpoolHost'][i] == ip:
				return 1
			elif object['univentionPrinterSpoolHost'][i] == '%s.%s' % (hostname, domainname):
				return 1
	return 0

def handler(dn, new, old):
	need_to_reload_samba = 0
	printer_is_group = 0
	quota_support = 0

	changes=[]

	if old:
		if old.has_key('objectClass'):
			if old['objectClass'][1] == 'univentionPrinterGroup':
				printer_is_group=1
		if old.has_key('univentionPrinterQuotaSupport') and (old['univentionPrinterQuotaSupport'][0] == "1"):
			quota_support = 1
	if new:
		if new.has_key('objectClass'):
			if new['objectClass'][1]== 'univentionPrinterGroup':
				printer_is_group=1
		if new.has_key('univentionPrinterQuotaSupport') and (new['univentionPrinterQuotaSupport'][0] == "1"):
			quota_support = 1
		else:
			quota_support = 0
	modified_uri=''
	for n in new.keys():
		if new.get(n, []) != old.get(n, []):
			changes.append(n)
		if n == 'univentionPrinterURI':
			if quota_support:
				modified_uri = "cupspykota:%s" % new['univentionPrinterURI'][0]
			else:
				modified_uri = new['univentionPrinterURI'][0]
	for o in old.keys():
		if not o in changes and new.get(o, []) != old.get(o, []):
			changes.append(o)
		if o == 'univentionPrinterURI' and not modified_uri:
			if quota_support:
				modified_uri = "cupspykota:%s" % old['univentionPrinterURI'][0]
			else:
				modified_uri = old['univentionPrinterURI'][0]

	options={
		'univentionPrinterURI': '-v',
		'univentionPrinterLocation': '-L',
		'description': '-D',
		'univentionPrinterModel': '-m'
	}

	if filter_match(old):
		if 'cn' in changes or not filter_match(new):
			# delete printer
			lpadmin(['-x', old['cn'][0]])
			if old['univentionPrinterQuotaSupport'][0] == "1":
				if printer_is_group:
					for member in old['univentionPrinterGroupMember']:
						pkprinters(['--groups', old['cn'][0], '--remove', member])
				pkprinters(['--delete', old['cn'][0]])
			need_to_reload_samba = 1
		if old.has_key('univentionPrinterSambaName') and old['univentionPrinterSambaName']:
			filename = '/etc/samba/printers.conf.d/%s' % old['univentionPrinterSambaName'][0]
			listener.setuid(0)
			try:
				if os.path.exists(filename):
					os.unlink(filename)
			finally:
				listener.unsetuid()
	if filter_match(new):
		description=""
		page_price=0
		job_price=0
		if new.has_key('univentionPrinterSambaName'):
			description=new['univentionPrinterSambaName'][0]
		if new.has_key('univentionPrinterPricePerPage'):
			page_price=new['univentionPrinterPricePerPage'][0]
		if new.has_key('univentionPrinterPricePerJob'):
			job_price=new['univentionPrinterPricePerJob'][0]

		# Add/Modify Printergroup
		if printer_is_group:
			args=[]
			add = []
			if old: # Diff old <==> new
				rem = old['univentionPrinterGroupMember']
				for el in new['univentionPrinterGroupMember']:
					if el not in old['univentionPrinterGroupMember']:
						add.append(el)
					else:
						rem.remove(el)


			else: # Create new group
				add=new['univentionPrinterGroupMember']

			if new['univentionPrinterQuotaSupport'][0] == "1":
				pkprinters(["--add","-D","\"%s\""%description,"--charge","%s,%s"%(page_price,job_price), new['cn'][0]])
				for member in new['univentionPrinterGroupMember']:
					pkprinters([ "--groups",new['cn'][0],member])
			elif new['univentionPrinterQuotaSupport'][0] == "0" and old:
				for member in old['univentionPrinterGroupMember']:
					pkprinters(['--groups', old['cn'][0], '--remove', member])

			for add_member in add: # Add Members
				args+=['-p', add_member, '-c', new['cn'][0]]
				if new['univentionPrinterQuotaSupport'][0] == "1":
					pkprinters([ "--groups",new['cn'][0],add_member])
			if old: # Remove Members
				for rem_member in rem:
					args+=['-p', rem_member, '-r', new['cn'][0]]
					pkprinters([ "--groups",new['cn'][0],"--remove",rem_member])

			lpadmin(args)
		# Add/Modify Printer
		else:

			args=['-p', new['cn'][0]]
			for a in changes:
				if a == 'univentionPrinterQuotaSupport':
					if new['univentionPrinterQuotaSupport'][0]=='1':
						pkprinters(["--add","-D","\"%s\""%description,"--charge","%s,%s"%(page_price,job_price), new['cn'][0]])

				if a == 'univentionPrinterURI':
					continue

				if a == 'univentionPrinterSpoolHost' and not 'univentionPrinterModel' in changes:
					args+=[options['univentionPrinterModel'], new.get('univentionPrinterModel', [''])[0]]

				if not options.has_key(a):
					continue

				if a == 'univentionPrinterModel':
					if new.get(a, [''])[0] == 'None':
						continue

					if new.get(a, [''])[0] == 'smb':
						continue

					args+=[options[a], new.get(a, [''])[0]]

				else:
					args+=[options[a], '"%s"' % new.get(a, [''])[0]]

			args+=[options['univentionPrinterURI'], modified_uri]

			args+=['-E']

			# insert printer
			lpadmin(args)
			need_to_reload_samba = 1

			if new.has_key('univentionPrinterSambaName') and new['univentionPrinterSambaName']:
				filename = '/etc/samba/printers.conf.d/%s' % new['univentionPrinterSambaName'][0]
				listener.setuid(0)
				try:
					fp = open(filename, 'w')

					print >>fp, '[%s]' % new['univentionPrinterSambaName'][0]
					print >>fp, 'printer name = %s' % new['cn'][0]
					print >>fp, 'path = /tmp'
					print >>fp, 'guest ok = yes'
					print >>fp, 'printable = yes'


					uid = 0
					gid = 0
					mode = '0755'

					os.chmod(filename,int(mode,0))
					os.chown(filename,uid,gid)
				finally:
					listener.unsetuid()


		if need_to_reload_samba == 1:
			samba_script='/etc/init.d/samba'
			if os.path.exists(samba_script):
				univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "cups-printers: samba reload" )
				listener.run(samba_script, ['samba','reload'], uid=0)
			else:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "cups-printers: no samba to reload found" )

def initialize():
	if not os.path.exists('/etc/samba/printers.conf.d'):
		listener.setuid(0)
		try:
			os.mkdir('/etc/samba/printers.conf.d')
		finally:
			listener.unsetuid()

def clean():
	listener.setuid(0)
	try:
		for f in os.listdir('/etc/samba/printers.conf.d'):
			if os.path.exists(os.path.join('/etc/samba/printers.conf.d', f)):
				os.unlink(os.path.join('/etc/samba/printers.conf.d', f))
		if os.path.exists('/etc/samba/printers.conf'):
			os.unlink('/etc/samba/printers.conf')
		os.rmdir('/etc/samba/printers.conf.d')
	finally:
		listener.unsetuid()

def postrun():
	listener.setuid(0)
	try:
		fp = open('/etc/samba/printers.conf', 'w')
		for f in os.listdir('/etc/samba/printers.conf.d'):
			print >>fp, 'include = %s' % os.path.join('/etc/samba/printers.conf.d', f)
		fp.close()
		if listener.baseConfig.has_key('samba/ha/master') and listener.baseConfig['samba/ha/master']:
			initscript='/etc/heartbeat/resource.d/samba'
		else:
			initscript='/etc/init.d/samba'
		os.spawnv(os.P_WAIT, initscript, ['samba', 'reload'])
	finally:
		listener.unsetuid()
