# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for printer groups
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

from ldap.filter import filter_format, escape_filter_chars

from univention.admin.layout import Tab, Group
import univention.admin.uldap
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.shares')
_ = translation.translate

module = 'shares/printergroup'
operations = ['add', 'edit', 'remove', 'search', 'move']
childs = 0
short_description = _('Printer share: Printer group')
object_name = _('Printer share group')
object_name_plural = _('Printer share groups')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionPrinterGroup'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.printerName,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True
	),
	'spoolHost': univention.admin.property(
		short_description=_('Print server'),
		long_description='',
		syntax=univention.admin.syntax.ServicePrint_FQDN,
		multivalue=True,
		required=True,
	),
	'groupMember': univention.admin.property(
		short_description=_('Group members'),
		long_description='',
		syntax=univention.admin.syntax.PrinterNames,
		multivalue=True,
		required=True,
	),
	'sambaName': univention.admin.property(
		short_description=_('Windows name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		unique=True
	),
	'setQuota': univention.admin.property(
		short_description=_('Enable quota support'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
	),
	'pagePrice': univention.admin.property(
		short_description=_('Price per page'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
	'jobPrice': univention.admin.property(
		short_description=_('Price per print job'),
		long_description='',
		syntax=univention.admin.syntax.integer,
	),
}

layout = [
	Tab(_('General'), _('General settings'), layout=[
		Group(_('General printer group share settings'), layout=[
			['name', 'spoolHost'],
			['sambaName', 'groupMember'],
			'setQuota',
			['pagePrice', 'jobPrice'],
		]),
	]),
]


def boolToString(value):
	if value == '1':
		return ['yes']
	else:
		return ['no']


def stringToBool(value):
	if value[0].lower() == 'yes':
		return '1'
	else:
		return '0'


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('spoolHost', 'univentionPrinterSpoolHost')
mapping.register('sambaName', 'univentionPrinterSambaName', None, univention.admin.mapping.ListToString)
mapping.register('groupMember', 'univentionPrinterGroupMember')
mapping.register('setQuota', 'univentionPrinterQuotaSupport', None, univention.admin.mapping.ListToString)
mapping.register('pagePrice', 'univentionPrinterPricePerPage', None, univention.admin.mapping.ListToString)
mapping.register('jobPrice', 'univentionPrinterPricePerJob', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_pre_create(self):
		super(object, self)._ldap_pre_create()
		self.is_valid_printer_object()  # check all members

	def _ldap_modlist(self):  # check for membership in a quota-printerclass
		if self.hasChanged('setQuota') and self.info.get('setQuota', '0') == '0':
			printergroups_filter = '(&(objectClass=univentionPrinterGroup)(univentionPrinterQuotaSupport=1))'
			group_cn = []
			for pg_dn, member_list in self.lo.search(filter=printergroups_filter, attr=['univentionPrinterGroupMember', 'cn']):
				for member_cn in member_list.get('univentionPrinterGroupMember', []):
					if member_cn == self.info['name']:
						group_cn.append(member_list['cn'][0])
			if len(group_cn) > 0:
				raise univention.admin.uexceptions.leavePrinterGroup(_('%(name)s is member of the following quota printer groups %(groups)s') % {'name': self.info['name'], 'groups': ', '.join(group_cn)})
		elif self.info.get('setQuota', None) == '1' and self.info.get('spoolHost'):
			for member_cn in self.info['groupMember']:
				if not self.lo.searchDn(filter='(&(objectClass=univentionPrinter)(|%s)(cn=%s)(univentionPrinterQuotaSupport=1))' % (''.join(filter_format('(univentionPrinterSpoolHost=%s)', [x]) for x in self.info['spoolHost']), escape_filter_chars(member_cn))):
					raise univention.admin.uexceptions.leavePrinterGroup(_('%s is disabled for quota support. ') % member_cn)
		if self.hasChanged('groupMember'):
			self.is_valid_printer_object()  # check all members
		return univention.admin.handlers.simpleLdap._ldap_modlist(self)

	def _ldap_pre_remove(self):  # check for last member in printerclass on same spoolhost
		printergroups_filter = '(&(objectClass=univentionPrinterGroup)(|%s))' % (''.join(filter_format('(univentionPrinterSpoolHost=%s)', [x]) for x in self.info['spoolHost']))
		rm_attrib = []
		for pg_dn, member_list in self.lo.search(filter=printergroups_filter, attr=['univentionPrinterGroupMember', 'cn']):
			for member_cn in member_list['univentionPrinterGroupMember']:
				if member_cn == self.info['name']:
					rm_attrib.append(pg_dn)
					if len(member_list['univentionPrinterGroupMember']) < 2:
						raise univention.admin.uexceptions.emptyPrinterGroup(_('%(name)s is the last member of the printer group %(group)s. ') % {'name': self.info['name'], 'group': member_list['cn'][0]})
		printergroup_module = univention.admin.modules.get('shares/printergroup')
		for rm_dn in rm_attrib:
			printergroup_object = univention.admin.objects.get(printergroup_module, None, self.lo, position='', dn=rm_dn)
			printergroup_object.open()
			printergroup_object['groupMember'].remove(self.info['name'])
			printergroup_object.modify()

	def is_valid_printer_object(self):  # check printer on current spoolhost
		spoolhosts = '(|%s)' % ''.join(filter_format('(univentionPrinterSpoolHost=%s)', [host]) for host in self.info['spoolHost'])
		for member in self.info['groupMember']:
			if not self.lo.searchDn(filter='(&(objectClass=univentionPrinter)(cn=%s)%s)' % (escape_filter_chars(member), spoolhosts)):
				raise univention.admin.uexceptions.notValidPrinter(_('%(name)s is not a valid printer on Spoolhost %(host)s.') % {'name': member, 'host': self.info['spoolHost']})


lookup = object.lookup
identify = object.identify
