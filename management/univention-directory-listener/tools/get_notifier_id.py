#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#
# Copyright 2004-2021 Univention GmbH
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

"""Read the notifier id from the Primary Directory Node"""

from __future__ import print_function

import argparse
import sys

from univention.listener.tools import NotifierCommunicationError, get_notifier_id


def parse_args():
	# type: () -> argparse.Namespace
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('-m', '--master', help='LDAP Server address')
	parser.add_argument(
		'-s', '--schema',
		dest='cmd',
		action='store_const',
		const='GET_SCHEMA_ID',
		default='GET_ID',
		help='Fetch LDAP Schema ID')
	parser.add_argument('arg', nargs='?', help=argparse.SUPPRESS)
	options = parser.parse_args()

	if not options.master:
		if options.arg:
			options.master = options.arg
		else:
			from univention.config_registry import ConfigRegistry
			configRegistry = ConfigRegistry()
			configRegistry.load()
			options.master = configRegistry.get('ldap/master')

	if not options.master:
		parser.error('ldap/master or --master not set')

	return options


def main():
	# type: () -> None
	"""Retrieve current Univention Directory Notifier transaction ID."""
	options = parse_args()
	try:
		notifier_id = get_notifier_id(host=options.master, cmd=options.cmd.encode('UTF-8'))
		print(str(notifier_id))
	except NotifierCommunicationError as exc:
		print('Error: {}'.format(exc), file=sys.stderr)
		sys.exit(1)


if __name__ == '__main__':
	main()
