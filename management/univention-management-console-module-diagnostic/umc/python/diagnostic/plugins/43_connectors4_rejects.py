#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2016-2019 Univention GmbH
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

import sys

import univention
import univention.uldap
from univention.management.console.modules.diagnostic import Critical, Warning, MODULE
from univention.management.console.modules.diagnostic import util

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('S4 Connector rejects')
description = _('No S4 Connector rejects were found.')
links = [{
	'name': 'sdb',
	'href': 'https://help.univention.com/t/how-to-deal-with-s4-connector-rejects/33',
	'label': _('Univention Support Database - How to deal with s4-connector rejects')
}]
run_descr = ['Checking S4-Connector rejects. Similar to running: univention-s4connector-list-rejected']


class MissingConfigurationKey(KeyError):
	def __str__(self):
		return '{}: {}'.format(self.__class__.__name__, self.message)


def load_mapping(configbasename='connector'):
	'''
	Load the s4-connector mappings as defined in
	`/etc/univention/<configbasename>/s4/mapping.py` (`s4_mapping` dictionary).
	'''
	old_sys_path = sys.path[:]
	sys.path.append('/etc/univention/{}/s4/'.format(configbasename))
	try:
		import mapping
	finally:
		sys.path = old_sys_path
	return mapping.s4_mapping


def get_s4_connector(configbasename='connector'):
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	if '%s/s4/ldap/certificate' % configbasename not in configRegistry or True:
		if configRegistry.is_true('%s/s4/ldap/ssl' % configbasename):
			MODULE.error('Missing Configuration Key %s/s4/ldap/certificate' % configbasename)
			raise MissingConfigurationKey('%s/s4/ldap/certificate' % configbasename)

	if configRegistry.get('%s/s4/ldap/bindpw' % configbasename):
		with open(configRegistry['%s/s4/ldap/bindpw' % configbasename]) as fob:
			s4_ldap_bindpw = fob.read().rstrip('\n')
	else:
		s4_ldap_bindpw = None

	try:
		s4 = univention.s4connector.s4.s4(
			configbasename,
			load_mapping(configbasename),
			configRegistry,
			configRegistry['%s/s4/ldap/host' % configbasename],
			configRegistry['%s/s4/ldap/port' % configbasename],
			configRegistry['%s/s4/ldap/base' % configbasename],
			configRegistry.get('%s/s4/ldap/binddn' % configbasename),
			s4_ldap_bindpw,
			configRegistry['%s/s4/ldap/certificate' % configbasename],
			configRegistry['%s/s4/listener/dir' % configbasename],
			False
		)
	except KeyError as error:
		MODULE.error('Missing Configuration key %s' % error.message)
		raise MissingConfigurationKey(error.message)
	else:
		return s4


def get_ucs_rejected(s4):
	for (filename, dn) in s4.list_rejected_ucs():
		encoded_dn = univention.s4connector.s4.encode_attrib(dn)
		encoded_s4_dn = univention.s4connector.s4.encode_attrib(s4.get_dn_by_ucs(dn))
		yield (filename, encoded_dn.strip(), encoded_s4_dn.strip())


def get_s4_rejected(s4):
	for (s4_id, dn) in s4.list_rejected():
		encoded_dn = univention.s4connector.s4.encode_attrib(dn)
		encoded_ucs_dn = univention.s4connector.s4.encode_attrib(s4.get_dn_by_con(dn))
		yield (s4_id, encoded_dn.strip(), encoded_ucs_dn.strip())


def run(_umc_instance):
	if not util.is_service_active('S4 Connector'):
		return

	try:
		import univention.s4connector
		import univention.s4connector.s4  # noqa: F401
	except ImportError:
		error_description = _('Univention S4 Connector is not installed.')
		raise Critical(description=error_description)

	try:
		s4 = get_s4_connector()
	except MissingConfigurationKey as error:
		error_description = _('The UCR variable {variable!r} is unset, but necessary for the S4 Connector.')
		MODULE.error(error_description.format(variable=error.message))
		raise Critical(description=error_description.format(variable=error.message))

	ucs_rejects = list(get_ucs_rejected(s4))
	s4_rejects = list(get_s4_rejected(s4))

	if ucs_rejects or s4_rejects:
		error_description = _('Found {ucs} UCS rejects and {s4} S4 rejects. See {{sdb}} for more information.')
		error_description = error_description.format(ucs=len(ucs_rejects), s4=len(s4_rejects))
		error_descriptions = [error_description]
		if ucs_rejects:
			error_descriptions.append(_('UCS rejected:'))
			for (filename, ucs_dn, s4_dn) in ucs_rejects:
				s4_dn = s4_dn if s4_dn else _('not found')
				line = _('UCS DN: {ucs}, S4 DN: {s4}, Filename: {fn}')
				line = line.format(ucs=ucs_dn, s4=s4_dn, fn=filename)
				error_descriptions.append(line)
		if s4_rejects:
			error_descriptions.append(_('S4 rejected:'))
			for (_s4_id, s4_dn, ucs_dn) in s4_rejects:
				ucs_dn = ucs_dn if ucs_dn else _('not found')
				line = _('S4 DN: {s4}, UCS DN: {ucs}')
				line = line.format(s4=s4_dn, ucs=ucs_dn)
				error_descriptions.append(line)
		MODULE.error('\n'.join(error_descriptions))
		raise Warning(description='\n'.join(error_descriptions))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
