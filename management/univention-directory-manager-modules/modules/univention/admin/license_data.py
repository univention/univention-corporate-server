# -*- coding: utf-8 -*-
"""
|UDM| licence data.
"""
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

UCS = ['UCS', 'Univention Corporate Server']


class Attributes:

	def __init__(self, required_license=None, options={}):
		self.required_license = required_license
		self._options = options

	def options(self, license_type):
		if not self._options:
			return ()
		if not isinstance(license_type, list):
			license_type = list(license_type)
		license_type.sort()

		for key in self._options.keys():
			skey = sorted(key)
			if license_type == skey:
				return self._options[key]

		return ()

	def valid(self, license_type):
		if not isinstance(license_type, list):
			license_type = list(license_type)

		if not self.required_license:
			return True

		if isinstance(self.required_license, list):
			for rl in self.required_license:
				if rl in license_type:
					return True
			return False
		else:
			return self.required_license in license_type


def moreGroupware(license):
	return False, (license.compare(license.licenses[license.ACCOUNT], license.licenses[license.GROUPWARE]) != 1)

# Examples:
#	'computers/managedclient': Attributes( UCS ),
#	'computers/ipmanagedclient': Attributes( UCS + [ 'OEM1'] ),
#	'computers/domaincontroller_master': Attributes( UCS + ['OEM2'] ,options =
#				{
#					( UCS, ) : ( ( 'nagios', (False, False) ), ),
#					( OEM2 ) : ( ( 'nagios', (True, False) ), ),
#					( UCS + ['OEM2'] ) : ( ( 'nagios', (False, False) ), ),
#				} ),


modules = {
}
