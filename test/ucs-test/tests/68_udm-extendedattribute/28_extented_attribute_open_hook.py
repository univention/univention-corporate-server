#!/usr/share/ucs-test/runner pytest-3
## desc: settings/extented_attribute open hook
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import univention.testing.udm as udm_test
import univention.testing.utils as utils
import univention.testing.strings as uts
import os
import pytest


@pytest.fixture
def hook_name():
	return uts.random_name()


@pytest.fixture
def cleanup(hook_name):
	yield
	os.remove('/usr/lib/python3/dist-packages/univention/admin/hooks.d/%s.py' % hook_name)
	os.remove('/tmp/%s_executed' % hook_name)


class Test_UDMExtension(object):
	@pytest.mark.tags('udm', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extented_attribute_open_hook(self, udm, hook_name, cleanup):
		"""settings/extented_attribute open hook"""
		with open('/usr/lib/python3/dist-packages/univention/admin/hooks.d/%s.py' % hook_name, 'w') as hook_module:
			hook_module.write("""
import univention.admin
import univention.admin.modules
import univention.admin.hook
import univention.admin.handlers.users.user

class %s(univention.admin.hook.simpleHook):
	def hook_open(self, obj):
		with open('/tmp/%s_executed', 'a+') as fp:
			if not isinstance(obj, univention.admin.handlers.users.user.object):
				fp.write('Hook called with wrong object parameter (Type: %%s)' %% type(module))
""" % (hook_name, hook_name))

		udm.stop_cli_server()
		cli_name = uts.random_string()
		udm.create_object(
			'settings/extended_attribute',
			position=udm.UNIVENTION_CONTAINER,
			name=uts.random_name(),
			shortDescription=uts.random_string(),
			CLIName=cli_name,
			module='users/user',
			objectClass='univentionFreeAttributes',
			ldapMapping='univentionFreeAttribute15',
			hook=hook_name
		)

		user = udm.create_user(**{cli_name: uts.random_string()})[0]
		udm.modify_object('users/user', dn=user, displayName=uts.random_name())

		with open('/tmp/%s_executed' % hook_name) as fp:
			fails = fp.read()
			assert not fails, fails
