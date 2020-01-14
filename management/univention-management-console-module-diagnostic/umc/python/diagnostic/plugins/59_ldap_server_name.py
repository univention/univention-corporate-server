#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import univention.uldap

from univention.management.console.config import ucr
from univention.config_registry import handler_set as ucr_set
from univention.management.console.modules.diagnostic import Critical

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check Ldap server role')

run_descr = ['This can be checked by running: ucr get ldap/server/name"']
def run(_umc_instance):

	ucr.load()

	if ucr.is_true('diagnostic/check/disable/59_ldap_server_name') or ucr.get('server/role') != "member":
		return

	ldap_server_name = ucr.get('ldap/server/name')
	domainname = ucr.get('domainname')
	lo = univention.uldap.getMachineConnection()
	master = lo.search(base=ucr.get('ldap/base'), filter='(univentionServerRole=master)', attr=["cn"])
	try:
		master_cn = master[0][1].get('cn')[0]
	except IndexError:
		raise Critical('Could not find a master DC%s' % (master,))

	master_fqdn = ".".join([master_cn, domainname])

	if master_fqdn == ldap_server_name:
		res = lo.search(base=ucr.get('ldap/base'), filter='(|(univentionServerRole=slave)(univentionServerRole=backup))', attr=["cn"])

		# Case: ldap/server/name is the domain master and there are other DCs available.
		if res:
			domain_cn = []
			for dn, attr in res:
				domain_cn.append(".".join((str(attr.get('cn')[0]), domainname)))
				warn = _('The ucr variable ldap/server/name is set to the UCS Master %s. Especially in bigger environments it could be beneficial to switch the Ldap server to another DC.\nPossible DCs are: %s\nIf you want to keep your configuration and disable this test run ucr set diagnostic/check/disable/59_ldap_server_name=yes ' % (master_fqdn, ', '.join(domain_cn),))
			raise Critical(warn)


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
