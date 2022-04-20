# -*- coding: utf-8 -*-
#
# Copyright 2004-2022 Univention GmbH
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

"""
|UDM| module for printers
"""

import re
from ldap.filter import filter_format

from univention.admin.layout import Tab, Group
import univention.admin.uldap
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

import univention.debug as ud
import univention.admin.uexceptions

translation = univention.admin.localization.translation('univention.admin.handlers.shares')
_ = translation.translate


class printerACLTypes(univention.admin.syntax.select):
	name = 'printerACLTypes'
	choices = [
		('allow all', _('Allow all users.')),
		('allow', _('Allow only chosen users/groups.')),
		('deny', _('Deny chosen users/groups.')),
	]


help_link = _('https://docs.software-univention.de/manual-5.0.html#print::shares')

module = 'shares/printer'
operations = ['add', 'edit', 'remove', 'search', 'move']

childs = False
short_description = _('Printer share: Printer')
object_name = _('Printer')
object_name_plural = _('Printers')
long_description = ''
options = {
	'default': univention.admin.option(
		short_description=short_description,
		default=True,
		objectClasses=['top', 'univentionPrinter'],
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
	'location': univention.admin.property(
		short_description=_('Location'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
	),
	'spoolHost': univention.admin.property(
		short_description=_('Print server'),
		long_description='',
		syntax=univention.admin.syntax.ServicePrint_FQDN,
		multivalue=True,
		required=True,
	),
	'uri': univention.admin.property(
		short_description=_('Connection'),
		long_description='',
		syntax=univention.admin.syntax.PrinterURI,
		include_in_default_search=True,
		required=True,
	),
	'model': univention.admin.property(
		short_description=_('Printer model'),
		long_description='',
		syntax=univention.admin.syntax.PrinterDriverList,
		include_in_default_search=True,
		required=True,
	),
	'producer': univention.admin.property(
		short_description=_('Printer producer'),
		long_description='',
		syntax=univention.admin.syntax.PrinterProducerList,
	),
	'sambaName': univention.admin.property(
		short_description=_('Windows name'),
		long_description='',
		syntax=univention.admin.syntax.string_numbers_letters_dots_spaces,
		unique=True
	),
	'ACLtype': univention.admin.property(
		short_description=_('Access control'),
		long_description=_('Access list can allow or deny listed users and groups.'),
		syntax=printerACLTypes,
		default="allow all"
	),
	'ACLUsers': univention.admin.property(
		short_description=_('Allowed/denied users'),
		long_description=_('For the given users printing is explicitly allowed or denied.'),
		syntax=univention.admin.syntax.UserDN,
		multivalue=True,
	),
	'ACLGroups': univention.admin.property(
		short_description=_('Allowed/denied groups'),
		long_description=_('For the given groups printing is explicitly allowed or denied.'),
		syntax=univention.admin.syntax.GroupDN,
		multivalue=True,
	),
}

layout = [
	Tab(_('General'), _('General settings'), layout=[
		Group(_('General printer share settings'), layout=[
			['name', 'sambaName'],
			'spoolHost',
			'uri',
			['producer', 'model'],
			['location', 'description'],
		]),
	], help_text=_('For information about how to manage Windows printer drivers and troubleshooting, see <a href="https://help.univention.com/t/overview-windows-printer-driver-distribution-known-issues-and-workarounds/13387" target="_blank" rel="noreferrer noopener">here</a>.')),
	Tab(_('Access control'), _('Access control for users and groups'), layout=[
		Group(_('Access control'), layout=[
			'ACLtype',
			'ACLUsers',
			'ACLGroups',
		]),
	]),
]


_AVAILABLE_PRINTER_SCHEMAS = []


def unmapPrinterURI(value, encoding=()):
	if not value:
		return (u'', u'')
	schema = u''
	dest = u''
	uri = value[0].decode(*encoding)
	for sch in _AVAILABLE_PRINTER_SCHEMAS:
		if uri.startswith(sch):
			schema = sch
			dest = uri[len(sch):]
			break

	return (schema, dest)


def mapPrinterURI(value, encoding=()):
	return u''.join(value).encode(*encoding)


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('location', 'univentionPrinterLocation', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('spoolHost', 'univentionPrinterSpoolHost', encoding='ASCII')
mapping.register('uri', 'univentionPrinterURI', mapPrinterURI, unmapPrinterURI, encoding='ASCII')
mapping.register('model', 'univentionPrinterModel', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('sambaName', 'univentionPrinterSambaName', None, univention.admin.mapping.ListToString)
mapping.register('ACLUsers', 'univentionPrinterACLUsers')
mapping.register('ACLGroups', 'univentionPrinterACLGroups')
mapping.register('ACLtype', 'univentionPrinterACLtype', None, univention.admin.mapping.ListToString, encoding='ASCII')


class object(univention.admin.handlers.simpleLdap):
	module = module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[]):
		# find the printer uris
		if not _AVAILABLE_PRINTER_SCHEMAS:
			printer_uris = univention.admin.modules.get('settings/printeruri').lookup(co, lo, '')
			for uri in printer_uris:
				_AVAILABLE_PRINTER_SCHEMAS.extend(uri['printeruri'])

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes=attributes)

	def open(self):
		# find the producer
		univention.admin.handlers.simpleLdap.open(self)
		if self['model']:
			models = univention.admin.modules.get('settings/printermodel').lookup(None, self.lo, filter_format('printerModel="%s*', [self['model']]))
			ud.debug(ud.ADMIN, ud.INFO, "printermodel: %s" % str(models))
			if not models or len(models) > 1:
				self['producer'] = []
			else:
				self['producer'] = models[0].dn

		self.save()

	def _ldap_pre_ready(self):
		super(object, self)._ldap_pre_ready()
		# cut off '/' at the beginning of the destination if it exists and protocol is file:/
		if self['uri'] and self['uri'][0] == 'file:/' and self['uri'][1][0] == '/':
			self['uri'][1] = re.sub(r'^/+', '', self['uri'][1])

	def _ldap_pre_remove(self):  # check for last member in printerclass
		super(object, self)._ldap_pre_remove()
		printergroups_filter = '(&(objectClass=univentionPrinterGroup)(|%s))' % (''.join(filter_format('(univentionPrinterSpoolHost=%s)', [x]) for x in self.info['spoolHost']))
		rm_attrib = []
		for pg_dn, member_list in self.lo.search(filter=printergroups_filter, attr=['univentionPrinterGroupMember', 'cn']):
			for member_cn in [x.decode('UTF-8') for x in member_list['univentionPrinterGroupMember']]:
				if member_cn == self.info['name']:
					rm_attrib.append(pg_dn)
					if len(member_list['univentionPrinterGroupMember']) < 2:
						raise univention.admin.uexceptions.emptyPrinterGroup(_('%(name)s is the last member of the printer group %(group)s. ') % {'name': self.info['name'], 'group': member_list['cn'][0].decode('UTF-8')})

		printergroup_module = univention.admin.modules.get('shares/printergroup')
		for rm_dn in rm_attrib:
			printergroup_object = univention.admin.objects.get(printergroup_module, None, self.lo, position='', dn=rm_dn)
			printergroup_object.open()
			printergroup_object['groupMember'].remove(self.info['name'])
			printergroup_object.modify()


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
