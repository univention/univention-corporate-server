#!/usr/share/ucs-test/runner python
## desc: Test appending and removing groups for all computer roles (except computers/ipmanagedclient)
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import univention.testing.udm as udm_test
import univention.testing.strings as uts
import univention.testing.utils as utils


if __name__ == '__main__':
	with udm_test.UCSTestUDM() as udm:
		for role in udm.COMPUTER_MODULES:
			if role == 'computers/ipmanagedclient':
				continue

			groups = (udm.create_group()[0], udm.create_group()[0], udm.create_group()[0], udm.create_group()[0])

			computerName = uts.random_name()
			computer = udm.create_object(role, name = computerName, append = {'groups': groups[:2]})
			# validate group memberships set during creation
			for group in groups[:2]:
				if not utils.verify_ldap_object(group, {'memberUid': ['%s$' % computerName], 'uniqueMember': [computer]}):
					utils.fail('Found broken group memembership of %s in group %s after trying to append groups %r during creationg' % (role, group, groups[:2]))


			udm.modify_object(role, dn = computer, append = {'groups': groups[2:]})
			# validate group memberships set during modification
			for group in groups:
				if not utils.verify_ldap_object(group, {'memberUid': ['%s$' % computerName], 'uniqueMember': [computer]}):
					utils.fail('Found broken group memembership of %s in group %s after trying to append groups %r during modification' % (role, group, groups[2:]))


			udm.modify_object(role, dn = computer, remove = {'groups': groups[:2]})
			# validate that group memberships of groups removed during modification have been decomposed
			for group in groups[:2]:
				if not utils.verify_ldap_object(group, {'memberUid': [], 'uniqueMember': []}):
					utils.fail('Group membership of %s in group %s was not fully decomposed after trying to remove groups %r' % (role, group, groups[:2]))

			# validate that the other group memberships are still unimpaired
			for group in groups[2:]:
				if not utils.verify_ldap_object(group, {'memberUid': ['%s$' % computerName], 'uniqueMember': [computer]}):
					utils.fail('Group membership of %s in group %s was decomposed while removing groups %r' % (role, group, groups[:2]))

