#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2017-2019 Univention GmbH
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

import socket
import ldap.filter
import itertools as it

import univention.admin.uldap
import univention.admin.modules as udm_modules
import univention.admin.objects as udm_objects
from univention.management.console.log import MODULE

import univention.config_registry
from univention.management.console.modules.diagnostic import Warning

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check nameserver entries on DNS zones')
description = ['All nameserver entries are ok.']
links = [{
	'name': 'sdb',
	'href': _('http://sdb.univention.de/1273'),
	'label': _('Univention Support Database - Bind: zone transfer failed')
}]
run_descr = ['Checks nameserver entries on DNS zones']


class RecordNotFound(Exception):
	pass


class ZoneError(Exception):
	def __init__(self, nameserver):
		self.nameserver = nameserver

	@property
	def zone(self):
		return self.nameserver.zone


class NoHostRecord(ZoneError):
	def __str__(self):
		msg = _('Found no host record (A/AAAA record) for nameserver {ns}.')
		return msg.format(ns=self.nameserver.nameserver())


class CnameAsNameServer(ZoneError):
	def __str__(self):
		msg = _('Found illegal alias record (CNAME record) for nameserver {ns}.')
		return msg.format(ns=self.nameserver.nameserver())


class Zone(object):
	def __init__(self, udm_zone, domainname):
		self.udm_zone = udm_zone
		self.domainname = domainname

	@property
	def kind(self):
		return self.udm_zone.module

	@property
	def zone(self):
		if self.kind == 'dns/forward_zone':
			return self.udm_zone.get('zone')
		return self.udm_zone.get('subnet')

	def base(self):
		if self.kind == 'dns/forward_zone':
			return self.zone
		return '{}.in-addr.arpa'.format(self.zone)

	def nameserver(self):
		for nameserver in self.udm_zone.get('nameserver'):
			yield NameServer(self, nameserver)

	def umc_link(self):
		text = 'udm:dns/dns'
		link = {
			'module': 'udm',
			'flavor': 'dns/dns',
			'props': {
				'openObject': {
					'objectDN': self.udm_zone.dn,
					'objectType': self.kind,
				}
			}
		}
		return (text, link)


class NameServer(object):
	def __init__(self, zone, nameserver):
		self.zone = zone
		self._nameserver = nameserver

	def is_qualified(self):
		return self._nameserver.endswith('.')

	def nameserver(self):
		return self._nameserver.rstrip('.')

	def fqdn(self):
		if self.is_qualified():
			return self.nameserver()
		return '{}.{}'.format(self.nameserver(), self.zone.base())

	def is_in_zone(self):
		return not self.is_qualified() or \
			self.nameserver().endswith(self.zone.domainname)

	def _generate_splits(self, fqdn):
		zn = fqdn
		while '.' in zn and zn != self.zone.domainname:
			(rdn, zn) = zn.split('.', 1)
			if rdn and zn:
				yield (rdn, zn)

	def build_filter(self):
		template = '(&(relativeDomainName=%s)(zoneName=%s))'
		expressions = (ldap.filter.filter_format(template, (rdn, zn)) for (rdn, zn) in self._generate_splits(self.fqdn()))
		return '(|{})'.format(''.join(expressions))


class UDM(object):

	def __init__(self):
		univention.admin.modules.update()
		(self.ldap_connection, self.position) = univention.admin.uldap.getMachineConnection()
		self.configRegistry = univention.config_registry.ConfigRegistry()
		self.configRegistry.load()

	def lookup(self, module_name, filter_expression=''):
		module = udm_modules.get(module_name)
		for instance in module.lookup(None, self.ldap_connection, filter_expression):
			instance.open()
			yield instance

	def find(self, nameserver):
		filter_expression = nameserver.build_filter()
		MODULE.process("Trying to find nameserver %s in UDM/LDAP" % (nameserver.fqdn()))
		MODULE.process("Similar to running: univention-ldapsearch '%s'" % (filter_expression))
		for (dn, attr) in self.ldap_connection.search(filter_expression):
			if dn:
				for module in udm_modules.identify(dn, attr):
					record = udm_objects.get(module, None, self.ldap_connection, self.position, dn, attr=attr, attributes=attr)
					record.open()
					return record
		raise RecordNotFound()

	def all_zones(self):
		domainname = self.configRegistry.get('domainname')
		for zone in self.lookup('dns/forward_zone'):
			yield Zone(zone, domainname)
		for zone in self.lookup('dns/reverse_zone'):
			yield Zone(zone, domainname)

	def check_zone(self, zone):
		for nameserver in zone.nameserver():
			try:
				record = self.find(nameserver)
			except RecordNotFound:
				if not nameserver.is_in_zone():
					try:
						socket.getaddrinfo(nameserver.fqdn(), None)
					except socket.gaierror:
						yield NoHostRecord(nameserver)
				else:
					yield NoHostRecord(nameserver)

			else:
				if record.module == 'dns/alias':
					yield CnameAsNameServer(nameserver)
				elif record.module != 'dns/host_record':
					yield NoHostRecord(nameserver)


def find_all_zone_problems():
	udm = UDM()
	for zone in udm.all_zones():
		for error in udm.check_zone(zone):
			MODULE.process('Found error %s in %s' % (error, udm.check_zone(zone)))
			yield error


def run(_umc_instance):
	ed = [
		_('Found errors in the nameserver entries of the following zones.') + ' ' +
		_('Please refer to {sdb} for further information.')]
	modules = list()
	tmpl_forward = _('In forward zone {name} (see {{{link}}}):')
	tmpl_reverse = _('In reverse zone {name} (see {{{link}}}):')
	for (zone, group) in it.groupby(find_all_zone_problems(), lambda error: error.zone):
		(text, link) = zone.umc_link()
		ed.append('')
		if zone.kind == 'dns/forward_zone':
			ed.append(tmpl_forward.format(kind=zone.kind, name=zone.zone, link=text))
		elif zone.kind == 'dns/reverse_zone':
			ed.append(tmpl_reverse.format(kind=zone.kind, name=zone.zone, link=text))
		ed.extend(str(error) for error in group)
		modules.append(link)

	if modules:
		raise Warning(description='\n'.join(ed), umc_modules=modules)


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
