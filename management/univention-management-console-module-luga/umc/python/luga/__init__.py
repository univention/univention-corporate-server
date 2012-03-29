#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console module:
#   manage local users and groups
#
# Copyright 2012 Univention GmbH
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

from Users import Users
from Groups import Groups

from univention.lib.i18n import Translation
from univention.management.console.modules import UMC_OptionTypeError, UMC_CommandError, UMC_OptionMissing, Base
from univention.management.console.log import MODULE

from subprocess import PIPE, Popen
from shlex import split

_ = Translation( 'univention-management-console-module-luga' ).translate

class Process:
	def sanitize_arg(self, arg):
		return '"' + str(arg).replace('\\','\\\\').replace('\"','\\\"') + '"'

	def sanitize_int(self, num):
		if str(num).isdigit() and type(int(num)) is int:
			return int(num)
		raise UMC_OptionTypeError( _("argument type has to be 'int': %s") % num )

	def sanitize_dict(self, d):
		return d if type(d) is dict else {}

	def process(self, args, stdin=None):
		"""
			process a shell command
			
			param args = string of arguments
			param stdin = stdin string
			return int returncode|string 'OSError'
		"""

		try:
			p = Popen( args = split(args.encode('utf-8')), env = {'LANG':'en'}, stderr = PIPE, stdin = PIPE )
			(stdout, stderr) = p.communicate(stdin)
		except OSError as e:
			MODULE.error( _('Command failed: %s\n Exception: %s') % (args, str(e)) )
			raise ValueError( _('Command failed') )

		return p.returncode

class Instance(Users, Groups, Base, Process):
	def __init__(self):
		Base.__init__(self)


