#!/usr/bin/python3
# Copyright 2011-2022 Univention GmbH
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

"""Univention IP Calculator for DNS records (IPv6 edition)."""

from __future__ import print_function

import ipaddress
import sys
from argparse import ArgumentParser, Namespace  # noqa: F401
from typing import Optional, List  # noqa: F401

from univention import ipcalc


def parse_options(args=None):
	# type: (Optional[List[str]]) -> Namespace
	"""Parse command line options."""
	epilog = 'Calculate network values from network address for DNS records.'
	parser = ArgumentParser(epilog=epilog)
	parser.add_argument(
		'--ip', dest='address',
		required=True,
		type=ipaddress.ip_address,
		help='IPv4 or IPv6 address')
	parser.add_argument(
		'--netmask', dest='netmask',
		required=True,
		help='Netmask or prefix length')
	parser.add_argument(
		'--output', dest='output',
		required=True,
		choices=('network', 'reverse', 'pointer'),
		help='Specify requested output type')
	parser.add_argument(
		'--calcdns', dest='calcdns',
		action='store_true',
		required=True,
		help='Request to calcuale DNS record entries')

	opt = parser.parse_args(args)

	try:
		opt.network = ipaddress.ip_interface(u'%s/%s' % (opt.address, opt.netmask))
	except ValueError as ex:
		parser.error("Invalid --netmask: %s" % (ex,))

	return opt


def main(args=None):
	# type: (Optional[List[str]]) -> None
	"""Calculate IP address parameters-"""
	options = parse_options(args)

	if isinstance(options.network, ipaddress.IPv6Interface):
		family = 'ipv6'
	elif isinstance(options.network, ipaddress.IPv4Interface):
		family = 'ipv4'
	else:  # pragma: no cover
		sys.exit("Unknown address format")

	func = getattr(ipcalc, 'calculate_%s_%s' % (family, options.output))
	result = func(options.network)
	print(result)


if __name__ == "__main__":
	main()
