# -*- coding: utf-8 -*-
#
# UCS test
"""
BETA VERSION

Wrapper around Univention Configuration Registry that is able to revert
the UCR status after usage. For usage examples look at the end of this
file.

WARNING:
changes to the ConfigRegistry object will also trigger the evaluation of templates
and therefore changes in configuration files created by UCR!

WARNING2:
The API is currently under development and may change before next UCS release!
"""
from __future__ import print_function
#
# Copyright 2013-2019 Univention GmbH
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

import copy
import univention.config_registry

ConfigRegistry = univention.config_registry.ConfigRegistry


class UCSTestConfigRegistry(ConfigRegistry):

	"""
			Extension to ConfigRegistry to be able to clean up after
			several changes to UCR variables have been done.
	"""

	def __init__(self, *args, **kwargs):
		""" initialise object """
		ConfigRegistry.__init__(self, *args, **kwargs)
		self.__original_registry = None

	def load(self):
		""" call load() of superclass and save original registry values """
		ConfigRegistry.load(self)
		if self.__original_registry is None:
			self.__original_registry = {}
			for regtype in (ConfigRegistry.NORMAL, ConfigRegistry.LDAP, ConfigRegistry.FORCED, ConfigRegistry.SCHEDULE):
				self.__original_registry[regtype] = copy.deepcopy(dict(self._registry[regtype]))

	def revert_to_original_registry(self):
		""" revert UCR values back to original state """
		# load current values again to perform correct comparison
		self.load()
		for regtype, option in (
			(ConfigRegistry.NORMAL, ''),
			(ConfigRegistry.LDAP, 'ldap-policy'),
			(ConfigRegistry.FORCED, 'force'),
			(ConfigRegistry.SCHEDULE, 'schedule')
		):
			# remove new variables
			keylist = list(set(self._registry[regtype]) - set(self.__original_registry[regtype]))
			if keylist:
				univention.config_registry.handler_unset(keylist, {option: True})

			# add/revert existing variables
			changes = []
			for key, origval in self.__original_registry[regtype].items():
				if origval != self._registry[regtype].get(key):
					changes.append('%s=%s' % (key, origval))
			if changes:
				univention.config_registry.handler_set(changes, {option: True})
		# load new/original values
		self.load()

	def __enter__(self):
		self.load()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.revert_to_original_registry()


if __name__ == '__main__':
	import time

	# Usage variant 1 "the manual way"

	print('Loading UCR...')
	ucr = UCSTestConfigRegistry()
	ucr.load()
	print('Setting some variables...')
	univention.config_registry.handler_set(['foo/bar=ding/dong'])
	univention.config_registry.handler_set(['repository/online/server=ftp.debian.org'])
	univention.config_registry.handler_unset(['server/role'])
	print('Waiting for 3 seconds...')
	time.sleep(3)
	print('Cleanup...')
	ucr.revert_to_original_registry()

	# Usage variant 2 "with statement"

	with UCSTestConfigRegistry() as ucr2:
		print('Old values...')
		print(ucr2.get('foo/bar', '<unset>'))
		print(ucr2.get('repository/online/server', '<unset>'))
		print(ucr2.get('server/role', '<unset>'))
		print('Setting some variables...')
		univention.config_registry.handler_set(['foo/bar=ding/dong'])
		univention.config_registry.handler_set(['repository/online/server=ftp.debian.org'])
		univention.config_registry.handler_unset(['server/role'])
		print('Waiting for 3 seconds...')
		time.sleep(3)
		print('Cleanup...')
