#!/usr/bin/python2.7
#
# Univention Management Console
#  Module lib containing low-lewel commands to control the UMC server
#
# Copyright 2012-2019 Univention GmbH
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

from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import simple_response, sanitize
from univention.management.console.modules.sanitizers import StringSanitizer
from univention.management.console.protocol.definitions import MODULE_ERR

from univention.lib.i18n import Translation

import subprocess
import locale

_ = Translation('univention-management-console-module-lib').translate

CMD_ENABLE_EXEC = ['/usr/share/univention-updater/enable-apache2-umc', '--no-restart']
CMD_ENABLE_EXEC_WITH_RESTART = '/usr/share/univention-updater/enable-apache2-umc'
CMD_DISABLE_EXEC = '/usr/share/univention-updater/disable-apache2-umc'


class MessageSanitizer(StringSanitizer):

	def _sanitize(self, value, name, further_args):
		value = super(MessageSanitizer, self)._sanitize(value, name, further_args)
		if isinstance(value, unicode):
			# unicodestr -> bytestr (for use in command strings)
			for encoding in (locale.getpreferredencoding, 'UTF-8', 'ISO8859-1'):
				try:
					value = value.encode(encoding)
					break
				except UnicodeEncodeError:
					pass
		return value


class Server(object):

	def restart_isNeeded(self, request):
		"""TODO: It would be helpful to monitor the init.d scripts in order to
		determine which service exactly should be reloaded/restartet.
		"""
		self.finished(request.id, True)

	def restart(self, request):
		"""Restart apache, UMC Web server, and UMC server.
		"""
		# send a response immediately as it won't be sent after the server restarts
		self.finished(request.id, True)

		# enable server restart and trigger restart
		# (disable first to make sure the services are restarted)
		subprocess.call(CMD_DISABLE_EXEC)
		p = subprocess.Popen(CMD_ENABLE_EXEC_WITH_RESTART, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		out, err = p.communicate()
		MODULE.info('enabling server restart:\n%s' % out)

	@simple_response
	def ping(self):
		return dict(success=True)

	@sanitize(message=MessageSanitizer(default=''))
	def reboot(self, request):
		message = _('The system will now be restarted')
		if request.options['message']:
			message = '%s (%s)' % (message, request.options['message'])

		if self._shutdown(message, reboot=True) != 0:
			message = _('System could not reboot')
			request.status = MODULE_ERR

		self.finished(request.id, None, message)

	@sanitize(message=MessageSanitizer(default=''))
	def shutdown(self, request):
		message = _('The system will now be shut down')
		if request.options['message']:
			message = '%s (%s)' % (message, request.options['message'])

		if self._shutdown(message, reboot=False) != 0:
			message = _('System could not shutdown')
			request.status = MODULE_ERR

		self.finished(request.id, None, message)

	def _shutdown(self, message, reboot=False):
		action = '-r' if reboot else '-h'

		try:
			subprocess.call(('/usr/bin/logger', '-f', '/var/log/syslog', '-t', 'UMC', message))
		except (OSError, Exception):
			pass
		return subprocess.call(('/sbin/shutdown', action, 'now', message))
