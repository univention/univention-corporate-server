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
import re

_ = Translation( 'univention-management-console-module-luga' ).translate

class Instance(Users, Groups, Base):
	@staticmethod
	def validate_type(obj, seq, cast = False):
		"""
			check if obj is of type seq, if not raise an UMC_OptionTypeError
			param obj: the object to check
			param class|type|tuple seq: sequence of types
			param bool cast: cast the given object to seq
		"""
		if cast:
			obj = seq(obj)
		if not isinstance(obj, seq):
			raise UMC_OptionTypeError( _("argument type has to be '%r'") % (seq,) )
		return True

	def sanitize_arg(self, arg):
		if ':' in str(arg):
			raise ValueError(_('arguments can not contain ":"'))
		return arg

	def sanitize_int(self, num):
		self.validate_type(num, int, True)
		return int(num)

	def sanitize_dict(self, d):
		return d if isinstance(d, dict) else {}

	def validate_name(self, name):
		if not name:
			raise ValueError( _('No name given.') )
		rpattern = r'^[a-zA-Z_äÄüÜöÖ][a-zA-ZäÄüÜöÖ0-9_-]*[$]?$'
		if None is re.match(rpattern, str(name)):
			raise ValueError( _('Name may only contain letters, numbers, "-" and "_" and must not start with "-".') )
		if len(str(name)) > 32:
			raise ValueError( _('Name may not be longer than 32 characters.') )

	def process(self, args, stdin=None):
		"""
			process a shell command
			
			param args = array of arguments
			param stdin = stdin string
			return int returncode|string 'OSError'
		"""

		try:
			p = Popen( args = map(lambda a: str(a).encode('utf-8'), args), stderr = PIPE, stdin = PIPE )
			(stdout, stderr) = p.communicate(stdin)
		except OSError as e:
			MODULE.error( 'Command failed: %s\nException: %s' % (args, str(e)) )
			raise ValueError( _('Command failed') )

		return p.returncode
