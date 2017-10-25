# -*- coding: utf-8 -*-
#
# Copyright 2017 Univention GmbH
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
# you and Univention.
#
# This program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import
import traceback
from univention.listener import ListenerModuleAdapter, ListenerModuleHandler, ListenerModuleConfiguration


class MyListenerModule(ListenerModuleHandler):
	def __init__(self, listener_configuration, *args, **kwargs):
		super(MyListenerModule, self).__init__(listener_configuration, *args, **kwargs)
		self.logger.info('MyListenerModule.__init__()')
		self.logger.debug('DEBUG level message')
		self.logger.info('INFO level message')
		self.logger.warn('WARN level message')
		self.logger.error('ERROR level message')

	def create(self, dn, new):
		self.logger.info('MyListenerModule.create() dn=%r', dn)

	def modify(self, dn, old, new, old_dn):
		self.logger.info('MyListenerModule.modify() dn=%r old_dn=%r', dn, old_dn)
		if old_dn:
			self.logger.info('MyListenerModule.modify() this is (also) a MOVE')
		self.logger.info('MyListenerModule.modify() self.diff(old, new)=%r', self.diff(old, new))
		self.logger.info('MyListenerModule.modify() self.diff(old, new, ignore_metadata=False)=%r', self.diff(old, new, ignore_metadata=False))

	def remove(self, dn, old):
		self.logger.info('MyListenerModule.remove() dn=%r', dn)
		fail = {}['fail']  # this will raise an Exception, which will be handled by seld.error_handler

	def initialize(self):
		super(MyListenerModule, self).initialize()
		self.logger.info('MyListenerModule.initialize()')

	def clean(self):
		super(MyListenerModule, self).clean()
		self.logger.info('MyListenerModule.clean()')

	def pre_run(self):
		super(MyListenerModule, self).pre_run()
		self.logger.info('MyListenerModule.pre_run()')

	def post_run(self):
		super(MyListenerModule, self).post_run()
		self.logger.info('MyListenerModule.post_run()')

	def error_handler(self, dn, old, new, command, exc_type, exc_value, exc_traceback):
		self.logger.error(
			'An error occurred in listener module %r. dn=%r old={%d keys...} new={%d keys...} command=%r',
			MyListenerModuleConfiguration.name, dn, len(old.keys()), len(new.keys()), command
		)
		self.logger.error(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))


class MyListenerModuleConfiguration(ListenerModuleConfiguration):
	name = 'my listener module'
	listener_module_class = MyListenerModule
	mytest = 'mytest value'  # no get_mytest() -> log warning

	def get_ldap_filter(self):
		# do more complicated stuff than just setting the class variable
		if 1 + 1 == 2:
			return '(objectClass=inetOrgPerson)'

	def get_configuration_keys(self):
		res = super(MyListenerModuleConfiguration, self).get_configuration_keys()
		res.append('mytest')
		return res


globals().update(ListenerModuleAdapter(MyListenerModuleConfiguration()).get_globals())
