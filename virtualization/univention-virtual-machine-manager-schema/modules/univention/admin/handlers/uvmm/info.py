# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager
#  UDM Virtual Machine Manager Information
#
# Copyright 2010-2012 Univention GmbH
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

import univention.admin.filter
import univention.admin.handlers
import univention.admin.syntax
import univention.admin.localization
from univention.admin.layout import Tab, Group

translation=univention.admin.localization.translation('univention.admin.handlers.uvmm')
_=translation.translate

module = 'uvmm/info'
default_containers = ['cn=Information,cn=Virtual Machine Manager']

childs = 0
short_description = _('UVMM: Machine information')
long_description = ''
operations = [ 'search', 'edit', 'add', 'remove' ]

property_descriptions={
	'uuid': univention.admin.property(
			short_description= _('UUID'),
			long_description= _('UUID'),
			syntax=univention.admin.syntax.string,
			multivalue=False,
			options=[],
			required=True,
			may_change=True,
			identifies=True
		),
	'description': univention.admin.property(
			short_description= _('Description'),
			long_description= _('Description of virtual machine'),
			syntax=univention.admin.syntax.string,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'os': univention.admin.property(
			short_description= _('Operating system'),
			long_description= _('Name of the operation system'),
			syntax=univention.admin.syntax.string,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'contact': univention.admin.property(
			short_description = _('Contact'),
			syntax=univention.admin.syntax.string,
			multivalue = False,
			options = [],
			required = False,
			may_change = True,
			identifies = False
		),
	'profile': univention.admin.property(
			short_description=_('Profile'),
			long_description=_('Reference to the profile used for defining this VM'),
			syntax=univention.admin.syntax.ldapDnOrNone,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
}


layout = [
	Tab( _( 'General' ), _( 'Virtual machine information' ), layout = [
		Group( _( 'General' ), layout = [
			"uuid",
			"description",
			"contact",
			"os",
			"profile",
		] )
	] )
	]

mapping=univention.admin.mapping.mapping()
mapping.register('uuid', 'univentionVirtualMachineUUID', None, univention.admin.mapping.ListToString)
mapping.register('description', 'univentionVirtualMachineDescription', None, univention.admin.mapping.ListToString)
mapping.register('os', 'univentionVirtualMachineOS', None, univention.admin.mapping.ListToString)
mapping.register('contact', 'univentionVirtualMachineContact', None, univention.admin.mapping.ListToString)
mapping.register('profile', 'univentionVirtualMachineProfileRef', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__( self, co, lo, position, dn = '', superordinate = None, attributes = [] ):
		global mapping
		global property_descriptions

		self.co=co
		self.lo=lo
		self.dn=dn
		self.position=position
		self._exists=0
		self.mapping=mapping
		self.descriptions=property_descriptions

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)

	def exists(self):
		return self._exists

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('uuid'), mapping.mapValue('uuid', self.info['uuid']), self.position.getDn())

	def _ldap_addlist(self):
		return [ ('objectClass', [ 'univentionVirtualMachine' ] ) ]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):
	filter=univention.admin.filter.conjunction('&', [
				univention.admin.filter.expression('objectClass', 'univentionVirtualMachine'),
				])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn))
	return res


def identify(dn, attr, canonical=0):
	return 'univentionVirtualMachine' in attr.get('objectClass', [])
