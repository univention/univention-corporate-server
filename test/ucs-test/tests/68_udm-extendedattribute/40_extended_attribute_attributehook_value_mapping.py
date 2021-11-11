#!/usr/share/ucs-test/runner pytest-3
## desc: settings/extented_attribute LDAP modlist hook
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import univention.testing.udm as udm_test
import univention.testing.utils as utils
import univention.testing.strings as uts
import pytest


@pytest.fixture
def hook_name():
	return uts.random_name()


@pytest.fixture
def fn_hook():
	return '/usr/lib/python3/dist-packages/univention/admin/hooks.d/{}.py'.format(hook_name)


@pytest.fixture
def acc(fn_hook):
	exit_cmd = ['/bin/rm', '-f', fn_hook]
	with utils.AutoCallCommand(exit_cmd=exit_cmd) as acc_:
		yield acc_


class Test_UDMExtension(object):
	@pytest.mark.tags('udm', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_attributehook_value_mapping(self, udm, acc, hook_name, fn_hook):
		"""settings/extented_attribute LDAP modlist hook"""
		cli_name = uts.random_string()
		attr_name = 'univentionFreeAttribute15'
		with udm_test.UCSTestUDM() as udm:
			with open(fn_hook, 'w') as hook_module:
				hook_module.write("""
import univention.admin
import univention.admin.modules
import univention.admin.hook
import univention.admin.handlers.users.user
import univention.testing.utils

def mydebug(msg):
    univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, '40_extended_attribute_attributehook_value_mapping: {hook_name}: %s' % (msg,))

mydebug('TEST MODULE LOADED')

class {hook_name}(univention.admin.hook.AttributeHook):
    ldap_attribute_name = '{attr_name}'
    udm_attribute_name = '{cli_name}'

    def map_attribute_value_to_ldap(self, value):
        mydebug('map_attribute_value_to_ldap(%r)' % (value,))
        if value in (b'FALSE', b'yes'):
            return b'no'
        elif value in (b'TRUE', b'yes'):
            return b'yes'
        elif value in (b'', None):
            return b''
        else:
            # this is not great, but works reasonably well
            mydebug('map_attribute_value_to_ldap(%r) ==> found invalid value' % (value,))
            raise univention.admin.uexceptions.valueError('%s: LDAP Value may not be %r' % (self.ldap_attribute_name, value))

    def map_attribute_value_to_udm(self, value):
        mydebug('map_attribute_value_to_udm(%r)' % (value,))
        if value == 'yes':
            return 'TRUE'
        elif value == 'no':
            return 'FALSE'
        elif value in ('', None):
            return ''
        else:
            # this is not great, but works reasonably well
            mydebug('map_attribute_value_to_udm(%r) ==> found invalid value' % (value,))
            raise univention.admin.uexceptions.valueError('%s: UDM Value may not be %r' % (self.udm_attribute_name, value))
""".format(hook_name=hook_name, cli_name=cli_name, attr_name=attr_name))  # noqa: E101

			udm.create_object(
				'settings/extended_attribute',
				position=udm.UNIVENTION_CONTAINER,
				name=uts.random_name(),
				shortDescription=uts.random_string(),
				CLIName=cli_name,
				module='users/user',
				objectClass='univentionFreeAttributes',
				ldapMapping=attr_name,
				hook=hook_name,
				syntax='TrueFalseUpper',
				multivalue=0,
				valueRequired=0,
				mayChange=1,
			)
			udm.stop_cli_server()

			userA = udm.create_user(**{cli_name: 'TRUE'})[0]
			utils.verify_ldap_object(userA, {attr_name: [b'yes']})
			userB = udm.create_user(**{cli_name: 'FALSE'})[0]
			utils.verify_ldap_object(userB, {attr_name: [b'no']})
			with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
				userC = udm.create_user(**{cli_name: 'INVALID'})[0]

			udm.modify_object('users/user', dn=userB, **{cli_name: 'TRUE'})
			utils.verify_ldap_object(userB, {attr_name: [b'yes']})
			udm.modify_object('users/user', dn=userB, **{cli_name: 'FALSE'})
			utils.verify_ldap_object(userB, {attr_name: [b'no']})
			with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
				udm.modify_object('users/user', dn=userB, **{cli_name: 'not valid'})
