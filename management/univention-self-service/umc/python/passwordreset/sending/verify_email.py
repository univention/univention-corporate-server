#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Send a token to a user by email.
#
# Copyright 2020-2022 Univention GmbH
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

import os.path
import smtplib
import urllib
from email.mime.nonmultipart import MIMENonMultipart
from email.utils import formatdate
import email.charset

from univention.lib.i18n import Translation
from univention.management.console.modules.passwordreset.send_plugin import UniventionSelfServiceTokenEmitter

_ = Translation('univention-self-service-passwordreset-umc').translate


class VerifyEmail(UniventionSelfServiceTokenEmitter):

	def __init__(self, *args, **kwargs):
		super(VerifyEmail, self).__init__(*args, **kwargs)
		self.server = self.ucr.get("umc/self-service/account-verification/email/server", "localhost")

	@staticmethod
	def send_method():
		return "verify_email"

	@staticmethod
	def message_application():
		return 'email_verification'

	@staticmethod
	def is_enabled():
		return True
		#  For now this sending message is always enabled (unless we have for methods for sending verification tokens)
		#  ucr = ConfigRegistry()
		#  ucr.load()
		#  return ucr.is_true("umc/self-service/account-verification/email/enabled")

	@property
	def udm_property(self):
		return "PasswordRecoveryEmailVerified"

	@property
	def token_length(self):
		length = self.ucr.get("umc/self-service/account-verification/email/token_length", 64)
		try:
			length = int(length)
		except ValueError:
			length = 64
		return length

	def send(self):
		path_ucr = self.ucr.get("umc/self-service/account-verification/email/text_file")
		if path_ucr and os.path.exists(path_ucr):
			path = path_ucr
		else:
			path = "/usr/share/univention-self-service/email_bodies/verification_email_body.txt"
		with open(path, "r") as fp:
			txt = fp.read()

		fqdn = ".".join([self.ucr["hostname"], self.ucr["domainname"]])
		frontend_server = self.ucr.get("umc/self-service/account-verification/email/webserver_address", fqdn)
		link = "https://{fqdn}/univention/self-service/#page=verifyaccount".format(fqdn=frontend_server)
		tokenlink = "https://{fqdn}/univention/self-service/#page=verifyaccount&token={token}&username={username}&method={method}".format(
			fqdn=frontend_server,
			username=urllib.quote(self.data["username"]),
			token=urllib.quote(self.data["token"]),
			method=self.send_method(),
		)

		txt = txt.format(username=self.data["username"], token=self.data["token"], link=link, tokenlink=tokenlink)

		msg = MIMENonMultipart('text', 'plain', charset='utf-8')
		cs = email.charset.Charset("utf-8")
		cs.body_encoding = email.charset.QP
		msg["Subject"] = "Account verification"
		msg["Date"] = formatdate(localtime=True)
		msg["From"] = self.ucr.get("umc/self-service/account-verification/email/sender_address", "Account Verification Service <noreply@{}>".format(fqdn))
		msg["To"] = self.data["address"]
		msg.set_payload(txt, charset=cs)

		smtp = smtplib.SMTP(self.server)
		smtp.sendmail(msg["From"], self.data["address"], msg.as_string())
		smtp.quit()
		self.log("Sent mail with token to address {}.".format(self.data["address"]))

		return True
