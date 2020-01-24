#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import univention.uldap

from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Critical, Warning
from univention.config_registry import handler_set as ucr_set

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check LDAP server role')

run_descr = ['This can be checked by running: ucr get ldap/server/name']


links = [{
	'name': 'sdb',
	'href': 'https://help.univention.com/t/changing-the-primary-ldap-server-to-redistribute-the-server-load/14138',
	'label': _('Univention Support Database - Change the primary LDAP Server to redistribute the server load')
}]


def deactivate_test(umc_instance):
	ucr_set(['diagnostic/check/disable/59_ldap_server_name=yes'])


actions = {
	'deactivate_test': deactivate_test,
}


def run(_umc_instance):

	ucr.load()

	if ucr.is_true('diagnostic/check/disable/59_ldap_server_name') or ucr.get('server/role') != 'memberserver':
		return

	ldap_server_name = ucr.get('ldap/server/name')
	domainname = ucr.get('domainname')
	lo = univention.uldap.getMachineConnection()
	master = lo.search(base=ucr.get('ldap/base'), filter='(univentionServerRole=master)', attr=['cn'])
	try:
		master_cn = master[0][1].get('cn')[0]
	except IndexError:
		raise Critical('Could not find a master DC%s' % (master,))

	master_fqdn = '.'.join([master_cn, domainname])

	if master_fqdn == ldap_server_name:
		res = lo.search(base=ucr.get('ldap/base'), filter='univentionServerRole=backup', attr=['cn'])

		# Case: ldap/server/name is the domain master and there are DC Backups available.
		if res:
			button = [{
				'action': 'deactivate_test',
				'label': _('Deactivate test'),
			}]
			warn = (_('The primary LDAP Server of this System (UCS ldap/server/name) is set to the DC Master of this UCS domain (%s).\nSince this environment provides further LDAP Servers, we recommend a different configuration to reduce the load of the DC Master.\nPlease see {sdb} for further information.') % (master_fqdn,))
			raise Warning(warn, buttons=button)


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
