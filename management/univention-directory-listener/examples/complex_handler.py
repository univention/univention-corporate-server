# -*- coding: utf-8 -*-
#
# Copyright 2017-2019 Univention GmbH
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
from univention.listener import ListenerModuleHandler, ListenerModuleConfiguration


class ComplexHandler(ListenerModuleHandler):
	#
	# For complex setups make the "Configuration" class a subclass of
	# ListenerModuleConfiguration and overwrite its methods.
	#
	class Configuration(ListenerModuleConfiguration):
		name = 'my_listener_module'
		description = 'a description'
		ldap_filter = '(objectClass=inetOrgPerson)'

		def get_attributes(self):
			# do more complicated stuff than just setting the class variable...
			return ['cn']

		def get_active(self):
			ucr_setting = super(ComplexHandler.Configuration, self).get_active()
			# check something in a database or network service
			query_external_source = True
			return ucr_setting and query_external_source

	def __init__(self, listener_configuration, *args, **kwargs):
		#
		# The log level for messages that go to
		# /var/log/univention/listener_modules/my_listener_module.log is set
		# with the UCR variable listener/module/my_listener_module/debug/level
		#
		super(ComplexHandler, self).__init__(listener_configuration, *args, **kwargs)
		self.logger.info('ComplexHandler.__init__()')
		self.logger.debug('DEBUG level message')
		self.logger.info('INFO level message')
		self.logger.warn('WARN level message')
		self.logger.error('ERROR level message')

	def create(self, dn, new):
		self.logger.info('ComplexHandler.create() dn=%r', dn)

	def modify(self, dn, old, new, old_dn):
		#
		# modify() will be called for both moves and modifies.
		# If old_dn is set, a move happened.
		# Both DN an attributes can change during a move.
		#
		self.logger.info('ComplexHandler.modify() dn=%r', dn)
		if old_dn:
			self.logger.info('ComplexHandler.modify() this is (also) a MOVE, old_dn=%r', old_dn)
		self.logger.info('ComplexHandler.modify() self.diff(old, new)=%r', self.diff(old, new))
		self.logger.info(
			'ComplexHandler.modify() self.diff(old, new, ignore_metadata=False)=%r',
			self.diff(old, new, ignore_metadata=False)
		)

	def remove(self, dn, old):
		#
		# An exception is triggered here to showcase the error_handler feature.
		#
		self.logger.info('ComplexHandler.remove() dn=%r', dn)
		fail = {}['fail']  # this will raise an Exception, which will be handled by self.error_handler
		# The error handler will *not* return here. After all this is an
		# unhandled exception.

	def initialize(self):
		super(ComplexHandler, self).initialize()
		self.logger.info('ComplexHandler.initialize()')

	def clean(self):
		super(ComplexHandler, self).clean()
		self.logger.info('ComplexHandler.clean()')

	def pre_run(self):
		super(ComplexHandler, self).pre_run()
		self.logger.info('ComplexHandler.pre_run()')

	def post_run(self):
		super(ComplexHandler, self).post_run()
		self.logger.info('ComplexHandler.post_run()')

	def error_handler(self, dn, old, new, command, exc_type, exc_value, exc_traceback):
		# exc_type, exc_value and exc_traceback can be examined for further
		# information about the exception.
		self.logger.exception(
			'An error occurred in listener module %r. dn=%r old={%d keys...} new={%d keys...} command=%r',
			self.config.name, dn, len(old.keys()), len(new.keys()), command
		)
