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

#
# Example for an asynchronous listener module.
#

from __future__ import absolute_import
import traceback
from univention.listener.async import AsyncListenerModuleHandler


class MyAsyncListenerModule(AsyncListenerModuleHandler):
	class Configuration:
		name = 'my_async_listener_module'
		ldap_filter = '(objectClass=inetOrgPerson)'
		attributes = ['sn', 'givenName']
		run_asynchronously = True

	def __init__(self, listener_configuration, *args, **kwargs):
		super(MyAsyncListenerModule, self).__init__(listener_configuration, *args, **kwargs)
		self.logger.info('MyAsyncListenerModule.__init__()')
		self.logger.debug('DEBUG level message')
		self.logger.info('INFO level message')
		self.logger.warn('WARN level message')
		self.logger.error('ERROR level message')

	def create(self, dn, new):
		self.logger.info('MyAsyncListenerModule.create() dn=%r', dn)

	def modify(self, dn, old, new, old_dn):
		self.logger.info('MyAsyncListenerModule.modify() dn=%r old_dn=%r', dn, old_dn)
		if old_dn:
			self.logger.info('MyAsyncListenerModule.modify() this is (also) a MOVE')
		self.logger.info('MyAsyncListenerModule.modify() self.diff(old, new)=%r', self.diff(old, new))
		self.logger.info('MyAsyncListenerModule.modify() self.diff(old, new, ignore_metadata=False)=%r', self.diff(old, new, ignore_metadata=False))

	def remove(self, dn, old):
		self.logger.info('MyAsyncListenerModule.remove() dn=%r', dn)
		fail = {}['fail']  # this will raise an Exception, which will be handled by self.error_handler

	def initialize(self):
		super(MyAsyncListenerModule, self).initialize()
		self.logger.info('MyAsyncListenerModule.initialize()')

	def clean(self):
		super(MyAsyncListenerModule, self).clean()
		self.logger.info('MyAsyncListenerModule.clean()')

	def pre_run(self):
		super(MyAsyncListenerModule, self).pre_run()
		self.logger.info('MyAsyncListenerModule.pre_run()')

	def post_run(self):
		super(MyAsyncListenerModule, self).post_run()
		self.logger.info('MyAsyncListenerModule.post_run()')

	def error_handler(self, dn, old, new, command, exc_type, exc_value, exc_traceback):
		self.logger.error(
			'An error occurred in listener module %r. dn=%r old={%d keys...} new={%d keys...} command=%r',
			self.config.name, dn, len(old.keys()), len(new.keys()), command
		)
		self.logger.error(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
