#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Send a token to a user by google cloud messaging (FCM).
#
# Copyright 2015-2017 Univention GmbH
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

#
#
# This is meant as an example. Please feel free to copy this file and adapt #
# it to your needs.                                                         #
#
#

#
#
# If the return code is other that True or an exception is raised and not   #
# caught, it is assumed that it was not possible to send the token to the   #
# user. The token is then deleted from the database.                        #
#
#

import time
import json
import os.path
import smtplib
import requests

from univention.config_registry import ConfigRegistry
from univention.lib.i18n import Translation
from univention.management.console.modules.passwordreset.send_plugin import UniventionSelfServiceTokenEmitter

_ = Translation('univention-self-service-passwordreset-umc').translate


class SendApp(UniventionSelfServiceTokenEmitter):

	def __init__(self, *args, **kwargs):
		super(SendApp, self).__init__(*args, **kwargs)

	@staticmethod
	def send_method():
		return "app"

	@staticmethod
	def send_method_label():
		return _("App")

	@staticmethod
	def is_enabled():
		ucr = ConfigRegistry()
		ucr.load()
		return ucr.is_true("umc/self-service/passwordreset/app/enabled")

	@property
	def udm_property(self):
		return "PasswordRecoveryAppToken"

	@property
	def token_length(self):
		length = self.ucr.get("umc/self-service/passwordreset/app/token_length", 12)
		try:
			length = int(length)
		except ValueError:
			length = 64
		return length

	def send(self):
		server_token = self.ucr.get("umc/self-service/passwordreset/app/server_token")

		URL_FCM_SEND = 'https://fcm.googleapis.com/fcm/send'
		body = {
			"data": {
				"msgtype": "resettoken",
				"token": self.data["token"],
				"timestamp": str(int(time.time())),
			},
			"registration_ids": [
				self.data["address"],
			],
		}
		headers = {
			"Content-Type":"application/json",
			"Authorization": "key=%s" % (server_token,),
		}
		result = requests.post(URL_FCM_SEND, data=json.dumps(body), headers=headers)
		self.log("FCM result1 = {!r}".format(result))

		self.log("Sent mail with token to address {}.".format(self.data["address"]))

		return True
