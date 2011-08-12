#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Copyright 2007-2010 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import os, sys, getopt
import subprocess
import univention.config_registry as confreg

def usage(out=sys.stdout):
	"""Output usage message."""
	print >>out, 'syntax: univention-policy-update-config-registry [-a] [-h] [-s] [-v] [<dn>]'
	print >>out, '     -a, --setall     write all variables set by policy'
	print >>out, '     -h, --help       print this help'
	print >>out, '     -s, --simulate   simulate update and show values to be set'
	print >>out, '     -v, --verbose    print verbose information'
	print >>out, '     <dn>             distinguished LDAP name of object'
	print >>out, ''


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
	verbose = False
	setall = False
	dn = configRegistry.get('ldap/hostdn') or configRegistry.get('ldap/mydn') or None

	# parse command line
	try:
		opts, pargs = getopt.getopt(sys.argv[1:], 'ahsv', ['setall', 'help', 'simulate', 'verbose'])
	except:
		usage(sys.stderr)
		sys.exit(2)

	# get command line data
	for option, value in opts:
		if option == '-a' or option == '--setall':
			setall = True
		elif option == '-h' or option == '--help':
			usage()
			sys.exit(0)
		elif option == '-s' or option == '--simulate':
			simulate = True
		elif option == '-v' or option == '--verbose':
			verbose = True

	if len(pargs) > 0:
		dn = pargs[0]

	if not dn:
		print >>sys.stderr, 'ERROR: cannot get ldap/hostdn'
		sys.exit(1)

	if simulate:
		print >>sys.stderr, 'Simulating update...'

	# get policy result
	ATTR = 'Attribute: univentionRegistry;entry-hex-'
	VALUE = 'Value: '
	if verbose:
		print >>sys.stderr, 'Retrieving policy for %s...' % dn
	p = subprocess.Popen(['univention_policy_result', dn], shell=False, stdout=subprocess.PIPE)
	for line in p.stdout:
		line = line.rstrip('\n')
		if line.startswith('Policy: '):
			key = value = None
		elif line.startswith(ATTR):
			key = line[len(ATTR):]
			key = key.decode('hex')
		elif line.startswith(VALUE) and key:
			value = line[len(VALUE):]
			setList[key] = value
			if verbose:
				print >>sys.stderr, "Retrieved %s=%s" % (key, value)
	if p.wait() != 0:
		# no output: this script is called by cron
		# print 'WARN: univention_policy_result failed - LDAP server may be down'
		sys.exit(1)

	if setList:
		newSetList = []
		for key, value in setList.items():
			record = '%s=%s' % (key, value)

			if configRegistryLDAP.get(key) != value or setall:
				newSetList.append( record.encode() )

		if simulate or verbose:
			for item in newSetList:
				print >>sys.stderr, 'Setting %s' % item
		if not simulate:
			confreg.handler_set( newSetList, { 'ldap-policy': True } )

	for key, value in configRegistryLDAP.items():
		if key not in setList:
			unsetList.append(key.encode())

	if unsetList:
		if simulate or verbose:
			for item in unsetList:
				print >>sys.stderr, 'Unsetting %s' % item
		if not simulate:
			confreg.handler_unset( unsetList, { 'ldap-policy': True } )

if __name__ == '__main__':
	main()
