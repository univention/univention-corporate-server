#
# Univention Admin Modules
#  localization
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
# 
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import univention.debug
import gettext, os

'''
usage:
translation=univention.admin.localization.translation()
_=translation.translate
'''

class translation:
	def __init__(self, namespace):
		domain=namespace.replace('/', '-').replace('.', '-')
		try:
			self.translation=gettext.translation(domain)
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'translating %s' % namespace)
		except IOError, e:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'no translation for %si (%s)' % ( namespace, str( e ) ) )
			self.translation=None
	def translate(self, message):
		if self.translation:
			return self.translation.ugettext(message)
		else:
			return message
