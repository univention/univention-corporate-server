#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: settings/extented_attribute LDAP post remove hook
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import os

import pytest

import univention.testing.strings as uts


@pytest.fixture()
def hook_name():
    return uts.random_name()


@pytest.fixture()
def cleanup_hooks(hook_name):
    yield
    try:
        os.remove('/usr/lib/python3/dist-packages/univention/admin/hooks.d/%s.py' % hook_name)
    except EnvironmentError:
        pass
    try:
        os.remove('/tmp/%s_executed' % hook_name)
    except EnvironmentError:
        pass


def test_extended_attribute_hooks(udm, ucr, hook_name, lo, cleanup_hooks):
    with open('/usr/lib/python3/dist-packages/univention/admin/hooks.d/%s.py' % hook_name, 'w') as hook_module:
        hook_module.write("""
import traceback

import univention.admin
import univention.admin.modules
import univention.admin.hook
import univention.admin.handlers.users.user

class %(hook_name)s(univention.admin.hook.simpleHook):

	def hook_ldap_pre_rename(self, obj, new_dn):
		with open('/tmp/%(hook_name)s_pre_rename_executed', 'w') as fd:
			try:
				assert isinstance(obj, univention.admin.handlers.users.user.object)
				fd.write('called\\n')
				fd.write(obj.old_dn + '\\n')
				fd.write(obj.dn + '\\n')
				fd.write(new_dn + '\\n')
			except Exception:
				fd.write(traceback.format_exc())
				raise

	def hook_ldap_post_rename(self, obj):
		with open('/tmp/%(hook_name)s_post_rename_executed', 'w') as fd:
			try:
				assert isinstance(obj, univention.admin.handlers.users.user.object)
				fd.write('called\\n')
				fd.write(obj.old_dn + '\\n')
				fd.write(obj.dn + '\\n')
			except Exception:
				fd.write(traceback.format_exc())
				raise

	def hook_ldap_pre_move(self, obj, new_dn):
		with open('/tmp/%(hook_name)s_pre_move_executed', 'w') as fd:
			try:
				assert isinstance(obj, univention.admin.handlers.users.user.object)
				fd.write('called\\n')
				fd.write(obj.old_dn + '\\n')
				fd.write(obj.dn + '\\n')
				fd.write(new_dn + '\\n')
			except Exception:
				fd.write(traceback.format_exc())
				raise

	def hook_ldap_post_move(self, obj):
		with open('/tmp/%(hook_name)s_post_move_executed', 'w') as fd:
			try:
				assert isinstance(obj, univention.admin.handlers.users.user.object)
				fd.write('called\\n')
				fd.write(obj.old_dn + '\\n')
				fd.write(obj.dn + '\\n')
			except Exception:
				fd.write(traceback.format_exc())
				raise
""" % {'hook_name': hook_name, 'ldap_base': ucr['ldap/base']})

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
        hook=hook_name,
    )

    old_dn = udm.create_user(**{cli_name: uts.random_string(), 'username': hook_name})[0]
    new_name = '%s-2' % hook_name
    new_dn = udm.modify_object('users/user', dn=old_dn, username=new_name)
    assert new_dn == 'uid=%s,%s' % (new_name, lo.parentDn(old_dn))

    with open('/tmp/%s_pre_rename_executed' % hook_name) as fd:
        print(fd.read())
        fd.seek(0)
        assert fd.readline().strip() == 'called'
        assert fd.readline().strip() == old_dn
        assert fd.readline().strip() == old_dn
        assert fd.readline().strip() == new_dn
        assert not fd.read()

    with open('/tmp/%s_post_rename_executed' % hook_name) as fd:
        print(fd.read())
        fd.seek(0)
        assert fd.readline().strip() == 'called'
        assert fd.readline().strip() == old_dn
        assert fd.readline().strip() == new_dn
        assert not fd.read()

    cn_name = uts.random_string()
    cn_dn = udm.create_object('container/cn', name=cn_name)

    old_dn = new_dn
    new_dn = udm.move_object('users/user', dn=new_dn, position=cn_dn)
    assert new_dn == 'uid=%s,%s' % (new_name, cn_dn)

    with open('/tmp/%s_pre_move_executed' % hook_name) as fd:
        print(fd.read())
        fd.seek(0)
        assert fd.readline().strip() == 'called'
        assert fd.readline().strip() == old_dn
        assert fd.readline().strip() == old_dn
        assert fd.readline().strip() == new_dn
        assert not fd.read()

    with open('/tmp/%s_post_move_executed' % hook_name) as fd:
        print(fd.read())
        fd.seek(0)
        assert fd.readline().strip() == 'called'
        assert fd.readline().strip() == old_dn
        assert fd.readline().strip() == new_dn
        assert not fd.read()
