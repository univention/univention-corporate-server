# -*- coding: utf-8 -*-

from univention.admin import property
from univention.admin.syntax import (string, ipProtocol, integer)
from univention.admin.layout import Tab, Group
from univention.admin.filter import (conjunction, expression)
from univention.admin.mapping import (mapping as Mapping, ListToString, mapRewrite)
from univention.admin.handlers import simpleLdap
from univention.admin.localization import translation

_ = translation('univention.admin.handlers.tests').translate

module = 'tests/ipservice'
operations = ['add', 'edit', 'remove', 'search', 'move']
usewizard = 1

childs = 0
short_description = _('IP Service')
long_description = '/etc/services in LDAP'

property_descriptions = {
	'name': property(
		short_description=_('service name'),
		long_description=_('Name of the service'),
		syntax=string,
		multivalue=False,
		include_in_default_search=True,
		required=True,
		may_change=True,
		identifies=False,
	),
	'protocol': property(
		short_description=_('Protocol'),
		long_description=_('Protocol of the service'),
		syntax=ipProtocol,
		multivalue=False,
		include_in_default_search=True,
		required=True,
		may_change=True,
		identifies=True
	),
	'port': property(
		short_description=_('Port'),
		long_description=_('Network port of the service'),
		syntax=integer,
		multivalue=False,
		include_in_default_search=True,
		required=True,
		may_change=True,
		identifies=True
	),
	'description': property(
		short_description=_('Description'),
		long_description=_('Optional description for service'),
		syntax=string,
		multivalue=False,
		include_in_default_search=True,
		required=False,
		may_change=True,
		identifies=False,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General IMAP mail folder settings'), layout=[
			["name", "description"],
			["protocol", "port"],
		]),
	]),
]

mapping = Mapping()
mapping.register('name', 'cn', None, ListToString)
mapping.register('protocol', 'ipServiceProtocol', None, ListToString)
mapping.register('port', 'ipServicePort', None, ListToString)
mapping.register('description', 'description', None, ListToString)


class object(simpleLdap):
	module = module

	def description(self):
		return '%{protocol}s@%{port}s' % self

	def _ldap_addlist(self):
		ocs = ['ipService']
		al = [('objectClass', oc) for oc in ocs]
		return al


def lookup_filter(filter_s=None, lo=None):
	filter_expr = conjunction('&', [expression('objectClass', 'ipService')])
	filter_expr.append_unmapped_filter_string(filter_s, mapRewrite, mapping)
	return filter_expr


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
	filter_str = unicode(lookup_filter(filter_s))
	return [object(co, lo, None, dn, attributes=attrs) for dn, attrs in lo.search(filter_str, base, scope, [], unique, required, timeout, sizelimit)]


def identify(dn, attr, canonical=0):
	return 'ipService' in attr.get('objectClass', [])
