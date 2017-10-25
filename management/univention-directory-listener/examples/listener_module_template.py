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
from univention.listener import ListenerModuleAdapter, ListenerModuleHandler, ListenerModuleConfiguration


class ListenerModuleTemplate(ListenerModuleHandler):
	def create(self, dn, new):
		self.logger.debug('dn=%r', dn)

	def modify(self, dn, old, new, old_dn):
		self.logger.debug('dn=%r old_dn=%r', dn, old_dn)
		if old_dn:
			self.logger.info('it is (also) a move')

	def remove(self, dn, old):
		self.logger.debug('dn=%r', dn)


class ListenerModuleTemplateConfiguration(ListenerModuleConfiguration):
	name = 'listener module template'
	description = 'a listener module template'
	ldap_filter = ''
	attributes = []
	listener_module_class = ListenerModuleTemplate


globals().update(ListenerModuleAdapter(ListenerModuleTemplateConfiguration()).get_globals())
