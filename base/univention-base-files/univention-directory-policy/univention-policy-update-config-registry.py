#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2007-2019 Univention GmbH
"""Get UCR settings from LDAP policy."""
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

import os
import sys
import subprocess
import univention.config_registry as confreg
from optparse import OptionParser


def get_policy(host_dn, verbose=False, server=None):
	"""Retrieve policy for host_dn."""
	set_list = {}

	# get policy result
	if verbose:
		if server:
			print >> sys.stderr, 'Connecting to LDAP host %s...' % server
		print >> sys.stderr, 'Retrieving policy for %s...' % (host_dn,)
	cmd = ['univention_policy_result',
	'-D', host_dn,
	'-y', '/etc/machine.secret']
	if server:
		cmd += ['-h', server]
	cmd += [host_dn]

	proc = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
	for line in proc.stdout:
		line = line.rstrip('\n')
		if line.startswith('Policy: '):
			key = value = None
		elif line.startswith(get_policy.ATTR):
			key = line[len(get_policy.ATTR):]
			key = key.decode('hex')
		elif line.startswith(get_policy.VALUE) and key:
			value = line[len(get_policy.VALUE):]
			set_list[key] = value
			if verbose:
				print >> sys.stderr, "Retrieved %s=%s" % (key, value)
	if proc.wait() != 0:
		# no output: this script is called by cron
		# print 'WARN: univention_policy_result failed - LDAP server may be down'
		sys.exit(1)
	return set_list


get_policy.ATTR = 'Attribute: univentionRegistry;entry-hex-'
get_policy.VALUE = 'Value: '


def parse_cmdline():
	"""Parse command line and return options and dn."""
	usage = '%prog [options] <host_dn>'
	epilog = '<host_dn> distinguished LDAP name of the host'
	parser = OptionParser(usage=usage, epilog=epilog)
	parser.add_option('-a', '--setall',
			dest='setall', action='store_true',
			help='write all variables set by policy')
	parser.add_option('-s', '--simulate',
			dest='simulate', action='store_true',
			help='simulate update and show values to be set')
	parser.add_option('-v', '--verbose',
			dest='verbose', action='store_true',
			help='print verbose information')
	parser.add_option('-l', '--ldap-server', dest='server', help='connect to this ldap host')
	options, args = parser.parse_args()

	if 'UNIVENTION_BASECONF' in os.environ:
		del os.environ['UNIVENTION_BASECONF']
	ucr = confreg.ConfigRegistry()
	ucr.load()

	if len(args) > 0:
		host_dn = args[0]
	else:
		host_dn = ucr.get('ldap/hostdn') or ucr.get('ldap/mydn') or None

	if not host_dn:
		print >> sys.stderr, 'ERROR: cannot get ldap/hostdn'
		sys.exit(1)

	if options.simulate:
		print >> sys.stderr, 'Simulating update...'
	return options, host_dn


def main():
	"""Get UCR settings from LDAP policy."""
	options, host_dn = parse_cmdline()

	confregfn = os.path.join(confreg.ConfigRegistry.PREFIX,
			confreg.ConfigRegistry.BASES[confreg.ConfigRegistry.LDAP])
	ucr_ldap = confreg.ConfigRegistry(filename=confregfn)
	ucr_ldap.load()

	set_list = get_policy(host_dn, options.verbose, options.server)
	if set_list:
		new_set_list = []
		for key, value in set_list.items():
			record = '%s=%s' % (key, value)

			if ucr_ldap.get(key) != value or options.setall:
				new_set_list.append(record.encode())

		if options.simulate or options.verbose:
			for item in new_set_list:
				print >> sys.stderr, 'Setting %s' % item
		if not options.simulate:
			confreg.handler_set(new_set_list, {'ldap-policy': True})

	unset_list = []
	for key, value in ucr_ldap.items():
		if key not in set_list:
			unset_list.append(key.encode())
	if unset_list:
		if options.simulate or options.verbose:
			for item in unset_list:
				print >> sys.stderr, 'Unsetting %s' % item
		if not options.simulate:
			confreg.handler_unset(unset_list, {'ldap-policy': True})


if __name__ == '__main__':
	main()
