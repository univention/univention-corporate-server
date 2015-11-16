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

import xmlrpclib
from univention.config_registry import ConfigRegistry
from univention.lib.i18n import Translation
from univention.management.console.modules.passwordreset.send_plugin import UniventionSelfServiceTokenEmitter

_ = Translation('univention-self-service-passwordreset-umc').translate


class SendSMS(UniventionSelfServiceTokenEmitter):
	def __init__(self, *args, **kwargs):
		super(SendSMS, self).__init__(*args, **kwargs)

		self.country_code = self.ucr.get("umc/self-service/passwordreset/sms/country_code")
		if not unicode(self.country_code).isnumeric():
			raise ValueError("UCR umc/self-service/passwordreset/sms/country_code must contain a number.")

		self.password_file = self.ucr.get("umc/self-service/passwordreset/sms/password_file")
		try:
			with open(self.password_file) as pw_file:
				self.username, self.password = pw_file.readline().strip().split(":")
		except ValueError as ve:
			self.log("__init__(): Format of sipgate secrets file is 'username:password'.")
			self.log("__init__(): Error while parsing sipgate secrets file: {}".format(ve))
			raise
		except (OSError, IOError) as e:
			self.log("__init__(): Could not read {}: {}".format(self.password_file, e))
			raise

	@staticmethod
	def send_method():
		return "mobile"

	@staticmethod
	def send_method_label():
		return _("Mobile number")

	@staticmethod
	def is_enabled():
		ucr = ConfigRegistry()
		ucr.load()
		return ucr.is_true("umc/self-service/passwordreset/sms/enabled")

	@property
	def udm_property(self):
		return "PasswordRecoveryMobile"

	@property
	def token_length(self):
		length = self.ucr.get("umc/self-service/passwordreset/sms/token_length", 12)
		try:
			length = int(length)
		except ValueError:
			length = 12
		return length

	def send(self):
		xmlrpc_url = "https://%s:%s@samurai.sipgate.net/RPC2" % (self.username, self.password)
		self.rpc_srv = xmlrpclib.ServerProxy(xmlrpc_url)
		reply = self.rpc_srv.samurai.ClientIdentify(
			{"ClientName": "Univention Self Service (python xmlrpclib)", "ClientVersion": "1.0",
			 "ClientVendor": "https://www.univention.com/"}
		)
		self.log("send(): Login success. Server reply to ClientIdentify(): {}".format(reply))

		msg = "Password reset token: {token}".format(token=self.data["token"])

		if len(msg) > 160:
			raise ValueError("Message to long: '{}'.".format(msg))

		num = "".join(map(lambda x: x if x.isdigit() else "", self.data["address"]))
		if num.startswith("00"):
			num = num[2:]
		elif num.startswith("0"):
			num = "{}{}".format(self.country_code, num[1:])
		else:
			pass

		self.log("send(): Sending text message to '{}'".format(num))
		args = {"RemoteUri": "sip:%s@sipgate.net" % num, "TOS": "text", "Content": msg}
		reply = self.rpc_srv.samurai.SessionInitiate(args)

		if reply.get("StatusCode") == 200:
			self.log("send(): Success sending token to user {}.".format(self.data["username"]))
			return True
		else:
			self.log("send(): Error sending token to user {}. Sipgate returned: {}".format(self.data["username"]), reply)
			raise Exception("Sipgate error: {}".format(reply))
