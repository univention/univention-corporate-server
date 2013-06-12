#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: system halt/reboot
#
# Copyright 2011-2012 Univention GmbH
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

import subprocess

import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.management.console.protocol.definitions import MODULE_ERR, SUCCESS

from univention.management.console.modules.decorators import sanitize
from univention.management.console.modules.sanitizers import StringSanitizer, ChoicesSanitizer

_ = umc.Translation('univention-management-console-module-reboot').translate

class Instance(umcm.Base):
	@sanitize(action=ChoicesSanitizer(['reboot', 'halt'], required=True),
		message=StringSanitizer(required=True))
	def reboot(self, request):
		message = None
		if request.options['action'] == 'halt':
			do = 'h'
			target = _('The system is going down for system halt NOW '
			           'with following message: ')
		elif request.options['action'] == 'reboot':
			do = 'r'
			target = _('The system is going down for reboot NOW '
			           'with following message: ')

		unicode_message = '%s%s' % (target, request.options['message'])
		message = unicode_message.encode('utf-8')
		subprocess.call(('/usr/bin/logger', '-f', '/var/log/syslog',
		                 '-t', 'UMC', message))
		shutdown_failed = subprocess.call(('/sbin/shutdown', '-%s' %do,
		                                   'now', message))
		if shutdown_failed:
			message = _('System could not reboot/shutdown')
			request.status = MODULE_ERR
		else:
			request.status = SUCCESS

		self.finished(request.id, None, message)

