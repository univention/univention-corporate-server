# -*- coding: utf-8 -*-

from univention.admin import option, property
from univention.admin.filter import conjunction, expression
from univention.admin.handlers import simpleLdap
from univention.admin.layout import Group, Tab
from univention.admin.localization import translation
from univention.admin.mapping import ListToString, mapping as Mapping, mapRewrite
from univention.admin.syntax import integer, ipProtocol, string

_ = translation('univention.admin.handlers.tests').translate

module = 'tests/ipservice'
operations = ['add', 'edit', 'remove', 'search', 'move']
childs = False
short_description = _('IP Service')
long_description = '/etc/services in LDAP'

options = {
	'default': option(
		short_description='IP Service',
		default=True,
		objectClasses=['ipService'],
	),
}

property_descriptions = {
	'name': property(
		short_description=_('service name'),
		long_description=_('Name of the service'),
		syntax=string,
		include_in_default_search=True,
		required=True,
	),
	'protocol': property(
		short_description=_('Protocol'),
		long_description=_('Protocol of the service'),
		syntax=ipProtocol,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'port': property(
		short_description=_('Port'),
		long_description=_('Network port of the service'),
		syntax=integer,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'description': property(
		short_description=_('Description'),
		long_description=_('Optional description for service'),
		syntax=string,
		include_in_default_search=True,
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
		return '%(protocol)s@%(port)s' % self


def lookup_filter(filter_s=None, lo=None):
	filter_expr = conjunction('&', [expression('objectClass', 'ipService')])
	filter_expr.append_unmapped_filter_string(filter_s, mapRewrite, mapping)
	return filter_expr


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
	filter_str = str(lookup_filter(filter_s))
	return [object(co, lo, None, dn, attributes=attrs) for dn, attrs in lo.search(filter_str, base, scope, [], unique, required, timeout, sizelimit)]


def identify(dn, attr, canonical=0):
	return b'ipService' in attr.get('objectClass', [])
