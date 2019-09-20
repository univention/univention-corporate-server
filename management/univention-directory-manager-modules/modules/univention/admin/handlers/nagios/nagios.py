#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Nagios
#  univention admin nagios module
#
# Copyright 2004-2019 Univention GmbH
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

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

import univention.admin.handlers.nagios.service
import univention.admin.handlers.nagios.timeperiod

translation = univention.admin.localization.translation('univention.admin.handlers.nagios')
_ = translation.translate

module = 'nagios/nagios'
help_link = _('https://docs.software-univention.de/manual-4.4.html#nagios:Configuration_of_the_Nagios_monitoring')
default_containers = ['cn=nagios']

childmodules = ['nagios/service', 'nagios/timeperiod']

childs = 0
short_description = _('Nagios object')
object_name = _('Nagios object')
object_name_plural = _('Nagios objects')
long_description = ''
operations = ['search']
virtual = 1
options = {}

property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description=_('Nagios object name'),
		syntax=univention.admin.syntax.string_numbers_letters_dots,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True
	),
}

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
	return univention.admin.handlers.nagios.service.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit) + univention.admin.handlers.nagios.timeperiod.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)


def identify(dn, attr, canonical=0):
	pass
