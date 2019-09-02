#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Warning, ProblemFixed

from univention.admin.uldap import getAdminConnection
from univention.admin.modules import update
from univention.admin.samba import acctFlags

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Server Role Windows')
description = '\n'.join([
	_('Several services rely on the attribute "univentionServerRole" to search and identify objects in OpenLDAP.'),
	_('Objects that implicitly satisfy the criteria of a Univention Object but lack this attribute should be migrated.'),
])

_UPDATED = False

_WINDOWS_SERVER_ROLES = {
	'windows_domaincontroller': ('computers/windows_domaincontroller', 'S'),
	'windows_client': ('computers/windows', 'W'),
	}

def sambaAcctFlags_to_univentionServerRole(sambaAcctFlags):
	flags = acctFlags(sambaAcctFlags)
	for server_role, (udm_module, account_flag) in _WINDOWS_SERVER_ROLES.items():
		try:
			if flags[account_flag]:
				return server_role
		except KeyError:
			pass


def udm_objects_without_ServerRole(lo):
	global _UPDATED
	if not _UPDATED:
		update()
		_UPDATED = True
	objs = {}
	result = lo.search('(&(objectClass=univentionWindows)(!(univentionServerRole=*)))', attr=['sambaAcctFlags'])
	if result:
		ldap_base = ucr.get('ldap/base')
		for dn, attrs in result:
			if dn.endswith(',cn=temporary,cn=univention,%s' % ldap_base):
				continue
			try:
				sambaAcctFlags = attrs['sambaAcctFlags'][0]
				server_role = sambaAcctFlags_to_univentionServerRole(sambaAcctFlags)
			except KeyError:
				server_role = None

			try:
				objs[server_role].append(dn)
			except KeyError:
				objs[server_role] = [dn]
	return objs


def run(_umc_instance):
	if ucr.get('server/role') != 'domaincontroller_master':
		return

	lo, pos = getAdminConnection()
	objs = udm_objects_without_ServerRole(lo)
	details = '\n\n' + _('These objects were found:')

	total_objs = 0
	show_fix_button = False
	for server_role in sorted(objs.iterkeys()):
		num_objs = len(objs[server_role])
		if num_objs:
			total_objs += num_objs
			if server_role:
				show_fix_button = True
				udm_module = _WINDOWS_SERVER_ROLES[server_role][0]
				details += '\n· ' + _('Number of %s objects that should be marked as "%s": %d') % (udm_module, server_role, num_objs,)
			else:
				details += '\n· ' + _('Number of unspecific Windows computer objects with missing sambaAcctFlags attribute: %d (Can\'t fix this automatically)') % (num_objs,)
	if total_objs:
		if show_fix_button:
			raise Warning(description + details, buttons=[{
				'action': 'migrate_objects',
				'label': _('Migrate %d LDAP objects') % total_objs,
			}])
		else:
			raise Warning(description + details, buttons=[])


def migrate_objects(_umc_instance):
	lo, pos = getAdminConnection()
	objs = udm_objects_without_ServerRole(lo)
	for server_role in sorted(objs.iterkeys()):
		for dn in objs[server_role]:
			changes = [('univentionServerRole', None, server_role)]
			lo.modify(dn, changes)
	raise ProblemFixed(buttons=[])


actions = {
	'migrate_objects': migrate_objects,
}


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
