#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Send a token to a user by email.
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

import os
import subprocess

from univention.config_registry import ConfigRegistry
from univention.management.console.modules.passwordreset.send_plugin import UniventionSelfServiceTokenEmitter


class SendWithExernal(UniventionSelfServiceTokenEmitter):

	@staticmethod
	def send_method():
		return "external"

	@staticmethod
	def is_enabled():
		ucr = ConfigRegistry()
		ucr.load()
		return ucr.is_true("self-service/passwordreset/external/enabled")

	@property
	def ldap_attribute(self):
		return "e-mail"

	@property
	def token_length(self):
		length = self.ucr.get("self-service/passwordreset/external/token_length", 64)
		try:
			length = int(length)
		except ValueError:
			length = 64
		return length

	def send(self):
		env = os.environ.copy()
		env["server"] = self.server
		env["username"] = self.username
		env["addresses"] = self.addresses
		env["token"] = self.token

		#############################################################################
		#                                                                           #
		# ATTENTION                                                                 #
		# The environment is inherited by all programs that are started by your     #
		# program. Your program should remove the token from its environment,       #
		# before starting any other program.                                        #
		#                                                                           #
		#############################################################################

		cmd = ["/usr/bin/example", "-v"]
		cmd_proc = subprocess.Popen(cmd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		cmd_out, cmd_err = cmd_proc.communicate()
		cmd_exit = cmd_proc.wait()

		if cmd_out:
			print "STDOUT of {}:\n{}".format(cmd, cmd_out)
		if cmd_err:
			print "STDERR of {}:\n{}".format(cmd, cmd_err)

		if cmd_exit == 0:
			return True
		else:
			print "Sending not successful"
			return False
