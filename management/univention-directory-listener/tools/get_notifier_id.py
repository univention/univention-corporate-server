#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Directory Listener
"""Read the notifier id from the DC master"""
from __future__ import print_function
#
# Copyright 2004-2019 Univention GmbH
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

import socket
from optparse import OptionParser
import sys


def parse_args():
	usage = '%prog [options] [master]'
	desc = sys.modules[__name__].__doc__
	parser = OptionParser(usage=usage, description=desc)
	parser.add_option(
		'-m', '--master',
		dest='master',
		help='LDAP Server address')
	parser.add_option(
		'-s', '--shema',
		dest='cmd',
		action='store_const',
		const='GET_SCHEMA_ID',
		default='GET_ID',
		help='Fetch LDAP Schema ID')
	(options, args) = parser.parse_args()

	if not options.master:
		if args:
			try:
				options.master, = args
			except ValueError:
				parser.error('incorrect number of arguments')
		else:
			from univention.config_registry import ConfigRegistry
			configRegistry = ConfigRegistry()
			configRegistry.load()
			options.master = configRegistry.get('ldap/master')

	if not options.master:
		parser.error('ldap/master or --master not set')

	return options


def main():
	"""Retrieve current Univention Directory Notifier transaction ID."""
	options = parse_args()
	try:
		sock = socket.create_connection((options.master, 6669), 60.0)

		sock.send('Version: 3\nCapabilities: \n\n')
		sock.recv(100)

		sock.send('MSGID: 1\n%s\n\n' % (options.cmd,))
		notifier_result = sock.recv(100)

		if notifier_result:
			print("%s" % notifier_result.splitlines()[1])
	except socket.error as ex:
		print('Error: %s' % (ex,), file=sys.stderr)
		sys.exit(1)


if __name__ == '__main__':
	main()
