#!/usr/bin/python2.7
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
import string
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

		result = {'success' : True}
		message = None
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
				server = cobject[0]

				# do we have a forward zone for this IP address?
				if request.options.get('oldip') and request.options.get('oldip') != request.options.get('ip'):
					fmodule = univention.admin.modules.get('dns/forward_zone')
					filter='(aRecord=%s)' % (request.options.get('oldip'))
					forwardobjects = univention.admin.modules.lookup(fmodule, co, lo, scope='sub', superordinate=None, filter=filter)
					for forwardobject in forwardobjects:
						forwardobject.open()
						forwardobject['a'].remove(request.options.get('oldip'))
						forwardobject['a'].append(request.options.get('ip'))
						forwardobject.modify()

				# remove old DNS reverse entries with old IP
				server.open()
				old_ip = server['ip']
				for e in server['dnsEntryZoneReverse']:
					if e[1] == old_ip:
						server['dnsEntryZoneReverse'].remove(e)

				# change IP
				server['ip'] = request.options.get('ip')
				MODULE.info('Change IP to %s' % request.options.get('ip'))
				try:
					server.modify()
				except Exception, err:
					MODULE.warn('Failed to change IP: %s' % traceback.format_exc())
					result['success'] = False
					message = 'Failed to change IP'

				
				# do we have a new reverse zone for this IP address?
				rmodule = univention.admin.modules.get('dns/reverse_zone')
				# ignore all netmask values != 255
				c = request.options.get('netmask').split('.').count('255')
				filter='(subnet=%s)' % (string.join(request.options.get('ip').split('.')[0:c], '.') )
				reverseobject = univention.admin.modules.lookup(rmodule, co, lo, scope='sub', superordinate=None, filter=filter)
				if reverseobject:
					server.open()
					server['dnsEntryZoneReverse'].append([reverseobject[0].dn, request.options.get('ip')])
				try:
					server.modify()
				except Exception, err:
					MODULE.warn('Failed to change DNS reverse zone: %s' % traceback.format_exc())
					result['success'] = False
					message = 'Failed to change DNS reverse zone'

		self.finished(request.id, result, message)

