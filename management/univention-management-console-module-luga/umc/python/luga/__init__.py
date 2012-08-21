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
	username_pattern = re.compile(r'^[A-Z_ÄÜÖ](?:[\wÄÜÖ-]{0,31}|[\wÄÜÖ-]{0,30}[$])?$', flags=re.IGNORECASE)
	arguments_pattern = re.compile(r'^[^:]*$')

	def process(self, args, stdin=None):
		"""
			process a shell command
			
			:param list args: list of command and arguments
			:param str stdin: stdin input
			:returns: int returncode
		"""

		try:
			args = map(lambda a: str(a).encode('utf-8'), args)
			p = Popen( args = args, stderr = PIPE, stdin = PIPE )
			(stdout, stderr) = p.communicate(stdin)
			MODULE.debug('%s: stdout=%s; stderr=%s' % (' '.join(args)), stdout, stderr )
		except OSError as e:
			MODULE.error( 'Command failed: %s\nException: %s' % (args, str(e)) )
			raise ValueError( _('Command failed') )

		return p.returncode
