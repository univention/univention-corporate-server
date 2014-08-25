# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager
#  UDM Virtual Machine Manager Information
#
# Copyright 2014 Univention GmbH
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

import univention.admin
import univention.admin.filter as udm_filter
import univention.admin.mapping as udm_mapping
from univention.admin.handlers import simpleLdap
import univention.admin.syntax as udm_syntax
from univention.admin.localization import translation
from univention.admin.layout import Tab, Group


_ = translation('univention.admin.handlers.uvmm').translate

module = 'uvmm/cloudtype'
default_containers = ['cn=Cloud Type,cn=Virtual Machine Manager']

childs = 0
short_description = _('UVMM: Cloud Types')
long_description = ''
operations = ['search', 'edit', 'add', 'remove']

usewizard = 1
wizardmenustring = _("Cloud Type")
wizarddescription = _("Add, edit and delete Cloud Types")
wizardoperations = {"add": [_("Add"), _("Add Cloud Type")], "find": [_("Search"), _("Search for Cloud Types")]}

# UDM properties
property_descriptions = {
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description=_('Name'),
			syntax=udm_syntax.string,
			multivalue=False,
			options=[],
			required=True,
			may_change=True,
			identifies=True
		),
}

# UDM web layout
layout = [
	Tab(_('General'), _('Virtual machine cloud type'), layout=[
		Group(_('General'), layout=[
			"name",
		])
	])
	]

# Maping between UDM properties and LDAP attributes
mapping = udm_mapping.mapping()
mapping.register('name', 'cn', None, udm_mapping.ListToString)


class object(simpleLdap):
	"""UVMM Cloud Type."""
	module = module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[]):
		global mapping
		global property_descriptions

		self.mapping = mapping
		self.descriptions = property_descriptions

		simpleLdap.__init__(self, co, lo, position, dn, superordinate)

	def _ldap_pre_create(self):
		"""Create DN for new UVMM Cloud Type."""
		self.dn = '%s=%s,%s' % (
				mapping.mapName('name'),
				mapping.mapValue('name', self.info['name']),
				self.position.getDn()
				)

	def _ldap_addlist(self):
		"""Add LDAP objectClass for UVMM Cloud Type."""
		return [
				('objectClass', ['univentionVirtualMachineCloudType'])
				]


def lookup_filter(filter_s=None, lo=None):
	"""
	Return LDAP search filter for UVMM Cloud Type entries.
	"""
	ldap_filter = udm_filter.conjunction('&', [
				udm_filter.expression('objectClass', 'univentionVirtualMachineCloudType'),
				])
	ldap_filter.append_unmapped_filter_string(filter_s, udm_mapping.mapRewrite, mapping)
	return unicode(ldap_filter)


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):
	"""Search for UVMM Cloud Type objects."""
	ldap_filter = lookup_filter(filter_s)
	return [object(co, lo, None, dn)
			for dn in lo.searchDn(ldap_filter, base, scope, unique, required, timeout, sizelimit)]


def identify(dn, attr, canonical=0):
	"""Return True if LDAP object is a UVMM Cloud Type."""
	return 'univentionVirtualMachineCloudType' in attr.get('objectClass', [])
