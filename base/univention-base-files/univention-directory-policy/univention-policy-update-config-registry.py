#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2007-2022 Univention GmbH
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

from __future__ import print_function

import argparse
import os
import sys

import univention.config_registry as confreg
from univention.lib.policy_result import PolicyResultFailed, ucr_policy_result


def get_policy(host_dn, server=None, password_file="/etc/machine.secret", verbose=False):
	"""Retrieve policy for host_dn."""
	try:
		(results, _) = ucr_policy_result(dn=host_dn, binddn=host_dn, bindpw=password_file, ldap_server=server)
	except PolicyResultFailed as ex:
		if verbose:
			print('WARN: failed to execute univention_policy_result: %s' % (ex,), file=sys.stderr)
		sys.exit(1)
	return results


def parse_cmdline():
	"""Parse command line and return options and dn."""
	ucr = confreg.ConfigRegistry()
	ucr.load()

	description = "Set local UCR settings from LDAP policy."
	parser = argparse.ArgumentParser(description=description)
	parser.add_argument('-a', '--setall', action='store_true', help='write all variables set by policy')
	parser.add_argument('-s', '--simulate', action='store_true', help='simulate update and show values to be set')
	parser.add_argument('-v', '--verbose', action='store_true', help='print verbose information')
	parser.add_argument('-l', '--ldap-server', dest='server', help='connect to this ldap host')
	parser.add_argument('-y', '--password-file', type=argparse.FileType('r'), default='/etc/machine.secret', help='password file to connect to ldap host')
	parser.add_argument('hostdn', nargs='?', default=ucr.get('ldap/hostdn'), help='distinguished LDAP name of the host')
	args = parser.parse_args()

	if 'UNIVENTION_BASECONF' in os.environ:
		del os.environ['UNIVENTION_BASECONF']

	if args.hostdn is None:
		parser.error('ERROR: cannot get ldap/hostdn')

	if args.simulate:
		print('Simulating update...', file=sys.stderr)

	return args


def main():
	"""Get UCR settings from LDAP policy."""
	args = parse_cmdline()

	confregfn = os.path.join(confreg.ConfigRegistry.PREFIX, confreg.ConfigRegistry.BASES[confreg.ConfigRegistry.LDAP])
	ucr_ldap = confreg.ConfigRegistry(filename=confregfn)
	ucr_ldap.load()
	set_list = get_policy(args.hostdn, args.server, args.password_file.name, verbose=args.verbose)
	if set_list:
		new_set_list = []
		for key, values in set_list.items():
			value = values[0]
			record = '%s=%s' % (key, value)

			if ucr_ldap.get(key) != value or args.setall:
				new_set_list.append(record)

		if args.simulate or args.verbose:
			for item in new_set_list:
				print('Setting %s' % item, file=sys.stderr)
		if not args.simulate:
			confreg.handler_set(new_set_list, {'ldap-policy': True})

	unset_list = []
	for key, value in ucr_ldap.items():
		if key not in set_list:
			unset_list.append(key)
	if unset_list:
		if args.simulate or args.verbose:
			for item in unset_list:
				print('Unsetting %s' % item, file=sys.stderr)
		if not args.simulate:
			confreg.handler_unset(unset_list, {'ldap-policy': True})


if __name__ == '__main__':
	main()
