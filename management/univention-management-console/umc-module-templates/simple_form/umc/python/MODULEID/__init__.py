#!/usr/bin/python2.7
#
# Univention Management Console
#  MODULEDESC
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

import notifier
import smtplib

from univention.management.console.base import Base
from univention.management.console.log import MODULE
#from univention.management.console.config import ucr
from univention.management.console.modules.decorators import sanitize
from univention.management.console.modules.sanitizers import StringSanitizer

from univention.lib.i18n import Translation

_ = Translation('PACKAGENAME').translate


class Instance(Base):

	def init(self):
		# this initialization method is called when the
		# module process is started and the configuration from the
		# UMC server is completed
		pass

	def configuration(self, request):
		"""Returns a directionary of initial values for the form."""
		self.finished(request.id, {
			'sender': self.username + '@example.com',
			'subject': 'Test mail from PACKAGENAME',
			'recipient': 'test@example.com'
		})

	@sanitize(
		sender=StringSanitizer(required=True),
		recipient=StringSanitizer(required=True),
		subject=StringSanitizer(required=True),
		message=StringSanitizer(required=True),
	)
	def send(self, request):
		def _send_thread(sender, recipient, subject, message):
			MODULE.info('sending mail: thread running')

			# FIXME: contains header injection
			msg = u'From: ' + sender + u'\r\n'
			msg += u'To: ' + recipient + u'\r\n'
			msg += u'Subject: %s\r\n' % subject
			msg += u'\r\n'
			msg += message + u'\r\n'
			msg += u'\r\n'

			msg = msg.encode('latin1')

			server = smtplib.SMTP('localhost')
			server.set_debuglevel(0)
			server.sendmail(sender, recipient, msg)
			server.quit()
			return True

		func = notifier.Callback(
			_send_thread,
			request.options['sender'],
			request.options['recipient'],
			request.options['subject'],
			request.options['message']
		)
		MODULE.info('sending mail: starting thread')
		cb = notifier.Callback(self.thread_finished_callback, request)
		thread = notifier.threads.Simple('mailing', func, cb)
		thread.run()
