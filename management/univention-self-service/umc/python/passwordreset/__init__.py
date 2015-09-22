#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: password reset service
#
# Copyright 2015 Univention GmbH
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

import pgdb  # TODO; add dependency: python-pygresql

from univention.lib.i18n import Translation
from univention.management.console.base import Base
from univention.management.console.log import MODULE
from univention.management.console.config import ucr

from univention.management.console.modules.decorators import sanitize
from univention.management.console.modules.sanitizers import StringSanitizer, EmailSanitizer

_ = Translation('univention-management-console-module-passwordreset').translate


def prevent_denial_of_service(func):
	def _decorated(self, request, *args, **kwargs):
		self.prevent_denial_of_service()
		return func(self, request, *args, **kwargs)


class Instance(Base):

	def init(self):
		pass # TODO: you can do something at initilization here
		self.load_plugins()
		self.open_database_connect()

	def load_plugins(self):
		pass # e.g. SMTP or SMS service

	def open_database_connection(self):
		# see <http://www.postgresql.org/docs/8.4/static/libpq-connect.html>
		connection_info = {
			'dbname': 'pkgdb',
			#'sslmode': 'require'
			}
		connection_info['host'] = db_server
		connection_info['user'] = db_user
		password_file = ''
		with open(password_file, 'rb') as fd:
			connection_info['password'] = fd.read().rstrip('\n')
		connectstring = ' '.join(["%s='%s'" % (key, value.replace('\\', '\\\\').replace("'", "\\'"),) for (key, value, ) in connection_info.items()])
		self.connection = pgdb.connect(database=connectstring)

	@prevent_denial_of_service
	@sanitize(
		username=StringSanitizer(required=True),
		mailaddress=EmailSanitizer(required=True),
	)
	@simple_response
	def request_token(self, username, mailaddress):
		if invalid:
			raise UMC_Error(_('This user is not allowed to reset its password.'))
		return 'token'

	@prevent_denial_of_service
	@sanitize(
		token=StringSanitizer(required=True),
	)
	@simple_response
	def submit_token(self, token):
		username = self.get_username_by_token(token)
		try:
			self.reset_password(username)
		except PasswordChangingFailed as exc:
			raise UMC_Error(str(exc), status=500)
		return True

	def prevent_denial_of_service(self):
		if too_many_request_in_the_last_five_minutes:
			raise UMC_Error(_('There have been too many requests in the last time. Please wait 5 minutes for the next request.'))
