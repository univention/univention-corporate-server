#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os.path
import subprocess

from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Warning, Critical, ProblemFixed, MODULE

from univention.udm import UDM, NoObject

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('LDAP schema files are not properly registered')
description = '\n'.join([
	_('Old packages and Apps registered schema files by copying the files locally into a certain directory.'),
	_('The preferred way now is to register them in LDAP; this is less error prone in situations like backup2master.'),
])
run_descr = ['Checks whether there are LDAP schema files that were not properly registered in LDAP itself.']

SCHEMA_FILES = {
	'/var/lib/univention-ldap/local-schema/univention-fetchmail.schema': {
		'package': 'univention-fetchmail-schema',
		'packageversion': '12.0.4-7A~4.4.0.201912061609',
	},
	'/var/lib/univention-ldap/local-schema/univention-openvpn.schema': {
		'package': 'univention-openvpn-master',
		'packageversion': '1.1.19',
	},
	'/var/lib/univention-ldap/local-schema/kopano4ucs.schema': {
		'package': 'kopano4ucs-schema',
		'packageversion': '1.6.2',
	},
	'/var/lib/univention-ldap/local-schema/plucs.schema': {
		'package': 'plucs',
		'packageversion': '0.3-0',
	},
	'/var/lib/univention-ldap/local-schema/zarafa4ucs.schema': {
		'package': 'zarafa',
		'packageversion': '7.2.6-10',
	},
	'/usr/share/univention-ldap/schema/asterisk4ucs.schema': {
		'package': 'asterisk4ucs',
		'packageversion': '1.0.9',
	},
	'/var/lib/univention-ldap/local-schema/univention-corporate-client.schema': {
		'package': 'ucc',
		'packageversion': '3.0',
	},
}

def udm_schema_obj_exists(name):
	name = os.path.splitext(os.path.basename(name))[0]
	udm = UDM.admin().version(1)
	try:
		udm.get('settings/ldapschema').get_by_id(name)
	except NoObject:
		return False
	else:
		return True

def create_udm_schema_obj(pname, pversion, fname):
	subprocess.check_call(['bash', '-c', 'source /usr/share/univention-lib/ldap.sh && ucs_registerLDAPExtension --packagename "%s" --packageversion "%s" --schema "%s"' % (pname, pversion, fname)])

def run(_umc_instance):
	if ucr.get('server/role') != 'domaincontroller_master':
		return

	unregistered = []
	for fname in sorted(SCHEMA_FILES):
		if not os.path.exists(fname):
			continue
		if not udm_schema_obj_exists(fname):
			unregistered.append(fname)

	if unregistered:
		MODULE.error(description + repr(unregistered))
		raise Warning(description + '\n' + _('The following files seem to be registered in the old way:') + '\n * ' + '\n * '.join(unregistered), buttons=[{
			'action': 'register_schema',
			'label': _('Register Schema files'),
		}])


def register_schema(_umc_instance):
	for fname in sorted(SCHEMA_FILES):
		if not os.path.exists(fname):
			continue
		info = SCHEMA_FILES[fname]
		if not udm_schema_obj_exists(fname):
			try:
				create_udm_schema_obj(info['package'], info['packageversion'], fname)
			except Exception as exc:
				raise Critical(_('The registration failed: %s') % (exc,))
	raise ProblemFixed(buttons=[])


actions = {
	'register_schema': register_schema,
}


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
