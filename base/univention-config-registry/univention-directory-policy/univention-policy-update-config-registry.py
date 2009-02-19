#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Univention GmbH
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

import os, sys, getopt, subprocess
import univention.config_registry as confreg

def usage():
	print 'syntax: univention-policy-update-config-registry [-a] [-h] [-s] [<dn>]'
	print '     -a               write all variables set by policy'
	print '     -h               print this help'
	print '     -s               simulate update and show values to be set'
	print '     <dn>             use univention-policy-result of <dn>'
	print ''


############
### MAIN ###
############

def main():
	if os.environ.has_key('UNIVENTION_BASECONF'):
		del os.environ['UNIVENTION_BASECONF']

	confregfn = os.path.join(confreg.ConfigRegistry.PREFIX, confreg.ConfigRegistry.BASES[ confreg.ConfigRegistry.LDAP ] )

	configRegistry = confreg.ConfigRegistry()
	configRegistry.load()

	configRegistryLDAP = confreg.ConfigRegistry( filename = confregfn )
	configRegistryLDAP.load()
	unsetList = []
	setList = {}
	simulate = False
	setall = False
	dn = None

	if configRegistry.has_key('ldap/hostdn'):
		dn = configRegistry['ldap/hostdn']
	elif configRegistry.has_key('ldap/mydn'):
		dn = configRegistry['ldap/mydn']

	# parse command line
	try:
		(opts, pargs) = getopt.getopt(sys.argv[1:], 'ahs', ['setall', 'help', 'simulate'])
	except:
		usage()
		sys.exit(0)

	# get command line data
	for opt in opts:
		if opt[0] == '-a' or opt[0] == '--setall':
			setall = True
		elif opt[0] == '-h' or opt[0] == '--help':
			usage()
			sys.exit(0)
		elif opt[0] == '-s' or opt[0] == '--simulate':
			simulate = True

	if len(pargs) > 0:
		dn = pargs[0]

	if dn==None:
		print 'ERROR: cannot get ldap/hostdn'
		sys.exit(0)

	if simulate:
		print 'Simulating update...'

	# get policy result
	p1 = subprocess.Popen('univention-policy-result "%s"' % dn, shell=True, stdout=subprocess.PIPE)
	p2 = subprocess.Popen('grep -A1 "^Attribute: univentionRegistry;entry-hex-"',
						  shell=True, stdin=p1.stdout, stdout=subprocess.PIPE)
	result = p2.communicate()[0]
	# if univention-policy-result fails then quit and do not parse output
	if p1.wait() != 0:
		# no output: this script is called by cron
		# print 'WARN: univention-policy-result failed - LDAP server may be down'
		sys.exit(0)


	result = result.strip('\n')

	if result:
		for record in result.split('\n--\n'):
			record = record.strip('\t\n\r ')

			lines = record.splitlines()
			if len(lines) != 2:
				print "ERROR: cannot parse following lines:"
				print "==> %s" % '\n==> '.join(lines)
			else:
				key = None
				value = None
				if lines[0].startswith('Attribute: univentionRegistry;entry-hex-'):
					key = lines[0][ len('Attribute: univentionRegistry;entry-hex-') : ]
					#key = key.replace('-','/')
					key = key.decode('hex')
				else:
					print 'ERROR: cannot parse key line:', lines[0]

				if lines[1].startswith('Value: '):
					value = lines[1][ len('Value: ') : ]
				else:
					print 'ERROR: cannot parse value line:', lines[1]

				setList[key] = value

	if setList:
		newSetList = []
		for key, value in setList.items():
			record = '%s=%s' % (key, value)
			if configRegistryLDAP.has_key(key):
				if configRegistryLDAP[key] != value or setall:
					# value changed
					newSetList.append( record.encode() )
			else:
				# value is new
				newSetList.append( record.encode() )

		if not simulate:
			confreg.handler_set( newSetList, { 'ldap-policy': True } )
		else:
			for item in newSetList:
				print 'Setting %s' % item

	for key, value in configRegistryLDAP.items():
		if not setList.has_key(key):
			unsetList.append(key.encode())

	if unsetList:
		if not simulate:
			confreg.handler_unset( unsetList, { 'ldap-policy': True } )
		else:
			for item in unsetList:
				print 'Unsetting %s' % item

	sys.exit(0)



if __name__ == '__main__':
	main()
