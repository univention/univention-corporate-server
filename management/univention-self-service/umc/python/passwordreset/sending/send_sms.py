#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Send a token to a user using a text message service.
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

#############################################################################
#                                                                           #
# This is meant as an example. Please feel free to copy this file and adapt #
# it to your needs.                                                         #
#                                                                           #
#############################################################################

#############################################################################
#                                                                           #
# If the return code is other that True or an exception is raised and not   #
# caught, it is assumed that it was not possible to send the token to the   #
# user. The token is then deleted from the database.                        #
#                                                                           #
#############################################################################

from univention.config_registry import ConfigRegistry
from univention.lib.i18n import Translation
from univention.management.console.modules.passwordreset.send_plugin import UniventionSelfServiceTokenEmitter

_ = Translation('univention-self-service-passwordreset-umc').translate


class SendSMS(UniventionSelfServiceTokenEmitter):
	def __init__(self):
		super(SendSMS, self).__init__()
		self.server = self.ucr.get("umc/self-service/passwordreset/sms/server", "localhost")

	@staticmethod
	def send_method():
		return "sms"

	@staticmethod
	def send_method_label():
		return _("Text Message")

	@staticmethod
	def is_enabled():
		ucr = ConfigRegistry()
		ucr.load()
		return ucr.is_true("umc/self-service/passwordreset/sms/enabled")

	@property
	def ldap_attribute(self):
		return "PasswordRecoveryMobile"

	@property
	def token_length(self):
		length = self.ucr.get("umc/self-service/passwordreset/email/token_length", 12)
		try:
			length = int(length)
		except ValueError:
			length = 12
		return length

	def send(self):
		raise NotImplementedError("Text message sending not yet implemented")
