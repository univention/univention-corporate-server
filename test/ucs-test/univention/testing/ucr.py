# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2013-2022 Univention GmbH
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

"""
BETA VERSION

Wrapper around Univention Configuration Registry that is able to revert
the UCR status after usage. For usage examples look at the end of this
file.

.. warning::
	changes to the ConfigRegistry object will also trigger the evaluation of templates
	and therefore changes in configuration files created by UCR!

.. warning:: The API is currently under development and may change before next UCS release!
"""

from __future__ import print_function

import copy
from types import TracebackType  # noqa: F401
from typing import Any, Dict, Optional, Type  # noqa: F401

import univention.config_registry
from univention.config_registry import ConfigRegistry


class UCSTestConfigRegistry(ConfigRegistry):
	"""
		Extension to ConfigRegistry to be able to clean up after
		several changes to UCR variables have been done.
	"""

	def __init__(self, *args, **kwargs):
		# type: (*Any, **Any) -> None
		""" initialise object """
		ConfigRegistry.__init__(self, *args, **kwargs)
		self.__original_registry = None  # type: Optional[Dict[int, Dict[str, str]]]

	def ucr_update(self, *args):
		return univention.config_registry.frontend.ucr_update(*args)

	def handler_set(self, *args):
		return univention.config_registry.handler_set(*args)

	def handler_unset(self, *args):
		return univention.config_registry.handler_unset(*args)

	def load(self):
		# type: () -> None
		""" call load() of superclass and save original registry values """
		ConfigRegistry.load(self)
		if self.__original_registry is None:
			self.__original_registry = {
				regtype: copy.deepcopy(dict(reg))
				for (regtype, reg) in self._walk()
			}

	def revert_to_original_registry(self):
		# type: () -> None
		""" revert UCR values back to original state """
		# load current values again to perform correct comparison
		self.load()
		assert self.__original_registry is not None
		for regtype, option in (
			(ConfigRegistry.NORMAL, ''),
			(ConfigRegistry.LDAP, 'ldap-policy'),
			(ConfigRegistry.FORCED, 'force'),
			(ConfigRegistry.SCHEDULE, 'schedule')
		):
			# remove new variables
			keylist = set(self._registry[regtype]) - set(self.__original_registry[regtype])
			if keylist:
				self.handler_unset(list(keylist), {option: True})

			# add/revert existing variables
			changes = [
				'%s=%s' % (key, origval)
				for key, origval in self.__original_registry[regtype].items()
				if origval != self._registry[regtype].get(key)
			]
			if changes:
				self.handler_set(changes, {option: True})
		# load new/original values
		self.load()

	def __enter__(self):
		# type: () -> UCSTestConfigRegistry
		self.load()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		# type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> None
		self.revert_to_original_registry()


if __name__ == '__main__':
	import time

	# Usage variant 1 "the manual way"

	print('Loading UCR...')
	ucr = UCSTestConfigRegistry()
	ucr.load()
	print('Setting some variables...')
	ucr.handler_set(['foo/bar=ding/dong'])
	ucr.handler_set(['repository/online/server=ftp.debian.org'])
	ucr.handler_unset(['server/role'])
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
		ucr2.handler_set(['foo/bar=ding/dong'])
		ucr2.handler_set(['repository/online/server=ftp.debian.org'])
		ucr2.handler_unset(['server/role'])
		print('Waiting for 3 seconds...')
		time.sleep(3)
		print('Cleanup...')
