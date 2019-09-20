#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2015-2019 Univention GmbH
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
from optparse import OptionParser
import sys
import datetime
import univention.uldap


class LicenseCheckError(Exception):
	"""Generic error during license check"""


class LicenseExpired(LicenseCheckError):
	"""The license is expired"""


class LicenseNotFound(LicenseCheckError):
	"""The license cannot be found in LDAP"""


def is_CSP_license(lo=None):
	# type: (Optional[univention.uldap.acceess]) -> bool
	"""
	Function to detect if installed license is a cloud service provider license (CSP).

	:param univention.uldap.acceess lo: Optional |LDAP| connection to re-use. Otherwise a new |LDAP| connection with machine credentials is created.
	:returns: `True` if a valid CSP license has been found or `False` if a valid non-CSP license has been found.
	:raises LicenseNotFound: if no license was found.
	:raises LicenseExpired: if the license has expired.
	"""

	if not lo:
		lo = univention.uldap.getMachineConnection()

	result = lo.search(filter='(&(objectClass=univentionLicense)(cn=admin))')
	if not result:
		raise LicenseNotFound()
	attrs = result[0][1]

	now = datetime.date.today()
	enddate = attrs.get('univentionLicenseEndDate', ['01.01.1970'])[0]
	if not enddate == 'unlimited':
		(day, month, year) = enddate.split('.', 2)
		then = datetime.date(int(year), int(month), int(day))
		if now > then:
			raise LicenseExpired('endDate = %s' % (enddate,))

	return 'CSP' in attrs.get('univentionLicenseOEMProduct', [])


if __name__ == '__main__':
	usage = '''%prog

Checks the installed UCS license and returns an appropriate
exitcode depending on the license status and license type.

Possible exitcodes:
0:  UCS license is valid and contains 'CSP' in the list of OEM products
10: UCS license is valid and does not contain 'CSP' in the list of OEM products
11: UCS license is expired
12: UCS license is invalid or not found'''

	parser = OptionParser(usage=usage)
	(options, args) = parser.parse_args()

	try:
		result = is_CSP_license()
	except LicenseExpired:
		print('License expired')
		sys.exit(11)
	except LicenseNotFound:
		print('License not found')
		sys.exit(12)
	except LicenseCheckError:
		print('License verification error')
		sys.exit(12)

	print('CSP=%s' % (result,))
	if not result:
		sys.exit(10)

	sys.exit(0)
