#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: ipchange
#
# Copyright 2012 Univention GmbH
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
# <http://www.gnu.org/licenses/>.

import threading
import traceback
import time
import notifier
import notifier.threads
import re
import csv
import univention.info_tools as uit
from univention.lib.i18n import Translation
import univention.management.console.modules as umcm
import os
import copy
import locale
import univention.config_registry
import univention.admin.config
import univention.admin.modules
import univention.admin.uldap

univention.admin.modules.update()

# update choices-lists which are defined in LDAP
univention.admin.syntax.update_choices()

from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *

class Instance(umcm.Base):
	def change(self, request):
		'''Return a dict with all necessary values for ipchange read from the current
		status of the system.'''

		MODULE.info('IP Change')
		if self._username.endswith('$'):
			server_name='%s' % self._username[:-1]
			MODULE.info('Server Name: %s' % server_name)

			lo, position = univention.admin.uldap.getAdminConnection()                                                                                                                                       
			co = univention.admin.config.config()   
			cmodule = univention.admin.modules.get('computers/%s' % request.options.get('role'))                                                                                                                                

			filter='(cn=%s)' % server_name
			cobject = univention.admin.modules.lookup(cmodule, co, lo, scope='sub', superordinate=None, filter=filter)

			if cobject:
				# change IP
				server = cobject[0]
				server.open()
				MODULE.info('Change IP to %s' % request.options.get('ip'))
				server['ip'] = request.options.get('ip')
				server.modify()
		self.finished(request.id, True)

