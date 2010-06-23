# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  i18n utils
#
# Copyright 2007-2010 Univention GmbH
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

import gettext, os
import locale

__all__ = [ '_' ]

class Translation:
	def __init__( self, namespace ):
		domain = namespace.replace( '/', '-' ).replace( '.', '-' )
		try:
			lang = locale.getlocale( locale.LC_MESSAGES )
			if lang[ 0 ]:
				self.translation = gettext.translation( domain, languages = ( lang[ 0 ], ) )
			else:
				self.translation = gettext.translation( domain, languages = ( 'de', ) )
		except IOError, e:
			self.translation = None

	def __call__( self, message ):
		if self.translation:
			return self.translation.ugettext( message )
		else:
			return message

_ = Translation( 'univention-directory-reports' )
