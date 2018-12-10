# -*- coding: utf-8 -*-
#
# Copyright 2018 Univention GmbH
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
import subprocess
from univention.listener import ListenerModuleHandler


class SenderCheckListener(ListenerModuleHandler):
	"""
	Execute "service univention-postfix-sender-check reload" when a
	settings/data object with public key is created/modified/deleted. Execute
	reload only in postrun to ensure it isn't done multiple times in short
	succession.
	"""
	class Configuration:
		name = 'sender_check_milter_reload'
		description = 'Reload univention-postfix-sender-check when related settings/data object change.'
		ldap_filter = '(&(objectClass=univentionData)(univentionDataType=mail/signing/RSA_public_key))'

	def post_run(self):
		self.logger.info('Reloading univention-postfix-sender-check.')
		with self.as_root():
			if subprocess.call(['systemctl', 'is-enabled', 'univention-postfix-sender-check-smtp']) == 0:
				subprocess.call(['service', 'univention-postfix-sender-check-smtp', 'reload'])
			if subprocess.call(['systemctl', 'is-enabled', 'univention-postfix-sender-check-non-smtp']) == 0:
				subprocess.call(['service', 'univention-postfix-sender-check-non-smtp', 'reload'])
