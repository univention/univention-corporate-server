#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Send a token to a user using a text message service.
#
# Copyright 2015-2019 Univention GmbH
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

import os
import subprocess
from univention.config_registry import ConfigRegistry
from univention.lib.i18n import Translation
from univention.management.console.modules.passwordreset.send_plugin import UniventionSelfServiceTokenEmitter

_ = Translation('univention-self-service-passwordreset-umc').translate


class SendSMS(UniventionSelfServiceTokenEmitter):

	def __init__(self, *args, **kwargs):
		super(SendSMS, self).__init__(*args, **kwargs)

		self.cmd = self.ucr.get("umc/self-service/passwordreset/sms/command", "").split()
		if not self.cmd:
			raise ValueError("SendSMS: UCR umc/self-service/passwordreset/sms/command must contain the path to the program to execute.")

		self.country_code = self.ucr.get("umc/self-service/passwordreset/sms/country_code")
		if not unicode(self.country_code).isnumeric():
			raise ValueError("SendSMS: UCR umc/self-service/passwordreset/sms/country_code must contain a number.")
		self.read_sms_secret()

	def read_sms_secret(self):
		self.password_file = self.ucr.get("umc/self-service/passwordreset/sms/password_file")
		if self.password_file is None:
			self.log("SendSMS: No sms secret file set")
			self.sms_username = ""
			self.sms_password = ""
			return

		try:
			with open(self.password_file) as pw_file:
				self.sms_username, self.sms_password = pw_file.readline().strip().split(":")
		except ValueError as ve:
			self.log("SendSMS: Format of sms secrets file ({}) is 'username:password'. Error: {}").format(self.password_file, ve)
			self.log("SendSMS: Format error in sms secrets file ({}): {}".format(self.password_file, ve))
			raise
		except (OSError, IOError) as e:
			self.log("SendSMS: Error reading sms secrets file ({}): {}".format(self.password_file, e))
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
		env = os.environ.copy()
		env["selfservice_username"] = self.data["username"]
		env["selfservice_address"] = self.data["address"]
		env["selfservice_token"] = self.data["token"]
		env["sms_country_code"] = self.country_code
		env["sms_username"] = self.sms_username
		env["sms_password"] = self.sms_password

		#
		#
		# ATTENTION                                                                 #
		# The environment is inherited by all programs that are started by your     #
		# program. Your program should remove the token from its environment,       #
		# before starting any other program.                                        #
		#
		#

		print("Starting external program {}...".format(self.cmd))
		cmd_proc = subprocess.Popen(self.cmd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		cmd_out, cmd_err = cmd_proc.communicate()
		cmd_exit = cmd_proc.wait()

		if cmd_out:
			self.log("STDOUT of {}: {}".format(self.cmd, cmd_out))
		if cmd_err:
			self.log("STDERR of {}: {}".format(self.cmd, cmd_err))

		if cmd_exit == 0:
			return True
		else:
			raise Exception("Error sending token.")
