# -*- coding: utf-8 -*-
#
# Copyright 2020 Univention GmbH
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

import univention.admin.localization
from univention.admin.syntax import select, UDM_Objects

translation = univention.admin.localization.translation('univention.admin.handlers.portals.portal')
_portal = translation.translate


class NewPortalCategories(UDM_Objects):
	"""
	Syntax to select a portal from |LDAP| using :py:class:`univention.admin.handlers.portals.category`.
	"""
	udm_modules = ('portals/category', )
	label = '%(name)s'
	empty_value = True
	simple = True


class NewPortalEntries(UDM_Objects):
	"""
	Syntax to select a portal entries from |LDAP| using :py:class:`univention.admin.handlers.portals.entry`.
	"""
	udm_modules = ('portals/entry', )
	label = '%(name)s'
	empty_value = True
	simple = True


class NewPortalComputer(UDM_Objects):
	"""
	Syntax to select a |UCS| host from |LDAP| by |FQDN| running the portal service.
	"""
	udm_modules = ('computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave', 'computers/memberserver')
	udm_filter = '!(univentionObjectFlag=docker)'
	use_objects = False


class NewPortalFontColor(select):
	"""
	Syntax to select the color of the font in the portal.
	"""
	choices = [
		('white', _portal('White')),
		('black', _portal('Black')),
	]


class NewPortalDefaultLinkTarget(select):
	choices = [
		('samewindow', _portal('Same tab')),
		('newwindow', _portal('New tab')),
		('embedded', _portal('Embedded')),
	]


class NewPortalEntryLinkTarget(select):
	choices = [
		('useportaldefault', _portal('Use default of portal')),
		('samewindow', _portal('Same tab')),
		('newwindow', _portal('New tab')),
		('embedded', _portal('Embedded')),
	]
