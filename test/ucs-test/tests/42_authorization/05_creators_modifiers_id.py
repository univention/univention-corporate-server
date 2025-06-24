#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check delegated administration in UMC
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous
import subprocess
from types import SimpleNamespace

import pytest

from univention.admin import modules
from univention.admin.authorization import Authorization
from univention.admin.rest.client import UDM as UDM_REST
from univention.admin.uldap import access, getAdminConnection, position
from univention.config_registry import ucr as _ucr
from univention.testing.umc import Client
from univention.testing.utils import UCSTestDomainAdminCredentials


pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/rest/enable-delegative-administration'), reason='authz not activated')
pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/web/enable-delegative-administration'), reason='authz not activated')


def remove_objects(object_type, dns):
    adm = UCSTestDomainAdminCredentials()
    client = UDM_REST('https://%(hostname)s.%(domainname)s/univention/udm/' % _ucr, username=adm.username, password=adm.bindpw)
    module = client.get(object_type)
    for dn in dns:
        obj = module.get(dn)
        obj.delete()


@pytest.fixture
def restart_umc():
    yield
    subprocess.call(['deb-systemd-invoke', 'restart', 'univention-management-console-server.service'])


@pytest.fixture
def ou(ldap_base, lo):
    admin_dn = f'uid=ou1admin,cn=users,{ldap_base}'
    admin_id = lo.get(admin_dn).get('univentionObjectIdentifier')
    admin2_dn = f'uid=ou2admin,cn=users,{ldap_base}'
    admin2_id = lo.get(admin2_dn).get('univentionObjectIdentifier')
    domain_admin = UCSTestDomainAdminCredentials()
    domain_admin_username = domain_admin.username
    domain_admin_password = domain_admin.bindpw
    domain_admin_id = lo.get(domain_admin.binddn).get('univentionObjectIdentifier')
    return SimpleNamespace(
        dn=f'ou=ou1,{ldap_base}',
        dn2=f'ou=ou2,{ldap_base}',
        admin_username='ou1admin',
        admin_dn=admin_dn,
        admin_id=admin_id,
        admin2_username='ou2admin',
        admin2_dn=admin2_dn,
        admin2_id=admin2_id,
        user_username='user1-ou1',
        user_dn=f'uid=user1-ou1,cn=users,ou=ou1,{ldap_base}',
        user_default_container=f'cn=users,ou=ou1,{ldap_base}',
        group_default_container=f'cn=groups,ou=ou1,{ldap_base}',
        domain_admin_id=domain_admin_id,
        domain_admin_username=domain_admin_username,
        domain_admin_password=domain_admin_password,
        domain_admin_dn=domain_admin.binddn,
    )


@pytest.fixture
def create_user_umc(random_username):

    dns = []

    def _func(client, position):
        name = random_username()
        options = [{
            'object': {
                'lastname': name,
                'username': name,
                'password': 'univention',
            },
            "options": {
                "container": position,
                "objectType": "users/user",
            },
        }]
        res = client.umc_command('udm/add', options, 'users/user').result[0]
        assert res['success']
        dns.append(res['$dn$'])
        return res['$dn$']

    yield _func

    remove_objects('users/user', dns)


@pytest.fixture
def create_group_udm_rest(ucr, random_username):

    dns = []

    def _func(client, position, cleanup=True):
        module = client.get('groups/group')
        obj = module.new(position=position)
        obj.properties['name'] = random_username()
        obj.save()
        if cleanup:
            dns.append(obj.dn)
        return obj.dn

    yield _func

    remove_objects('groups/group', dns)


@pytest.fixture
def create_user_udm(random_username, ucr):

    dns = []

    def _func(module, lo, pos, position_dn, cleanup=True):
        pos.setDn(position_dn)
        obj = module.object(None, lo, pos)
        obj['username'] = random_username()
        obj['lastname'] = random_username()
        obj['password'] = 'univention'
        dn = obj.create()
        if cleanup:
            dns.append(dn)
        return dn

    yield _func

    remove_objects('users/user', dns)


@pytest.fixture
def lo_domain_admin(ou, ldap_base):
    return access(binddn=ou.domain_admin_dn, bindpw=ou.domain_admin_password, base=ldap_base)


@pytest.fixture
def lo_ou1_admin(ou, ldap_base):
    return access(binddn=ou.admin_dn, bindpw='univention', base=ldap_base)


@pytest.fixture
def lo_ou2_admin(ou, ldap_base):
    return access(binddn=ou.admin2_dn, bindpw='univention', base=ldap_base)


def test_umc(ou, lo, random_username, create_user_umc, restart_umc):
    """Test univentionObjectCreatorsID is set to the bind user"""
    admin_client = Client()
    admin_client.authenticate(ou.domain_admin_username, ou.domain_admin_password)
    ou1_client = Client()
    ou1_client.authenticate(ou.admin_username, 'univention')
    ou2_client = Client()
    ou2_client.authenticate(ou.admin2_username, 'univention')

    # create as domain admin
    dn = create_user_umc(admin_client, ou.dn)
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.domain_admin_id
    assert attrs['univentionObjectModifiersID'] == ou.domain_admin_id
    # change as ou1 admin
    ou1_client.umc_command('udm/put', [{'object': {'$dn$': dn, 'description': random_username()}}], 'users/user').result[0]
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.domain_admin_id
    assert attrs['univentionObjectModifiersID'] == ou.admin_id

    # create as ou1 admin
    dn = create_user_umc(ou1_client, ou.dn)
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.admin_id
    assert attrs['univentionObjectModifiersID'] == ou.admin_id

    # create a ou2 admin
    dn = create_user_umc(ou2_client, ou.dn2)
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.admin2_id
    assert attrs['univentionObjectModifiersID'] == ou.admin2_id
    # change as domain admin
    admin_client.umc_command('udm/put', [{'object': {'$dn$': dn, 'description': random_username()}}], 'users/user').result[0]
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.admin2_id
    assert attrs['univentionObjectModifiersID'] == ou.domain_admin_id


def test_udm_rest(ou, lo, random_username, ucr, create_group_udm_rest):
    """Test univentionObjectCreatorsID is set to the bind user"""
    admin_client = UDM_REST('https://%(hostname)s.%(domainname)s/univention/udm/' % ucr, username=ou.domain_admin_username, password=ou.domain_admin_password)
    ou1_client = UDM_REST('https://%(hostname)s.%(domainname)s/univention/udm/' % ucr, username=ou.admin_username, password='univention')
    ou2_client = UDM_REST('https://%(hostname)s.%(domainname)s/univention/udm/' % ucr, username=ou.admin2_username, password='univention')

    # create as domain admin
    dn = create_group_udm_rest(admin_client, ou.dn2)
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.domain_admin_id
    assert attrs['univentionObjectModifiersID'] == ou.domain_admin_id
    # change as ou2 admin
    obj = ou2_client.get('groups/group').get(dn)
    obj.properties['description'] = random_username()
    obj.save()
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.domain_admin_id
    assert attrs['univentionObjectModifiersID'] == ou.admin2_id

    # create as ou1 admin
    dn = create_group_udm_rest(ou1_client, ou.dn)
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.admin_id
    assert attrs['univentionObjectModifiersID'] == ou.admin_id

    # create as ou2 admin
    dn = create_group_udm_rest(ou2_client, ou.dn2)
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.admin2_id
    assert attrs['univentionObjectModifiersID'] == ou.admin2_id
    # modify as domain admin
    obj = admin_client.get('groups/group').get(dn)
    obj.properties['description'] = random_username()
    obj.save()
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.admin2_id
    assert attrs['univentionObjectModifiersID'] == ou.domain_admin_id


def test_udm_rest_rename(ou, lo, random_username, ucr, create_group_udm_rest):
    admin_client = UDM_REST('https://%(hostname)s.%(domainname)s/univention/udm/' % ucr, username=ou.domain_admin_username, password=ou.domain_admin_password)
    ou2_client = UDM_REST('https://%(hostname)s.%(domainname)s/univention/udm/' % ucr, username=ou.admin2_username, password='univention')

    # create as domain admin
    dn = create_group_udm_rest(admin_client, ou.dn2, cleanup=False)
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.domain_admin_id
    assert attrs['univentionObjectModifiersID'] == ou.domain_admin_id

    # rename as ou2 admin
    obj = ou2_client.get('groups/group').get(dn)
    name = random_username()
    obj.properties['name'] = name
    obj.save()
    dn = f'cn={name},{ou.dn2}'
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.domain_admin_id
    assert attrs['univentionObjectModifiersID'] == ou.admin2_id

    obj = admin_client.get('groups/group').get(dn)
    obj.delete()


def test_udm_rest_move(ou, lo, random_username, ucr, create_group_udm_rest):
    admin_client = UDM_REST('https://%(hostname)s.%(domainname)s/univention/udm/' % ucr, username=ou.domain_admin_username, password=ou.domain_admin_password)
    ou1_client = UDM_REST('https://%(hostname)s.%(domainname)s/univention/udm/' % ucr, username=ou.admin_username, password='univention')

    # create as domain admin
    dn = create_group_udm_rest(admin_client, ou.dn, cleanup=False)
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.domain_admin_id
    assert attrs['univentionObjectModifiersID'] == ou.domain_admin_id

    # move as ou1 admin
    obj = ou1_client.get('groups/group').get(dn)
    obj.move(ou.user_default_container)
    dn = dn.replace(ou.dn, ou.user_default_container)
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.domain_admin_id
    assert attrs['univentionObjectModifiersID'] == ou.admin_id

    obj = admin_client.get('groups/group').get(dn)
    obj.delete()


def test_udm(ou, ldap_base, lo, create_user_udm, random_username, lo_domain_admin, lo_ou1_admin, lo_ou2_admin):
    lo_priv = getAdminConnection()[0]
    admin_connection_getter = lambda: lo_priv  # noqa: E731
    Authorization.enable(admin_connection_getter)

    lo_domain_admin = Authorization.inject_ldap_connection(lo_domain_admin)
    lo_ou1_admin = Authorization.inject_ldap_connection(lo_ou1_admin)
    lo_ou2_admin = Authorization.inject_ldap_connection(lo_ou2_admin)

    pos = position(lo_domain_admin.base)
    modules.update()
    users = modules.get('users/user')
    modules.init(lo_domain_admin, pos, users)

    # create as domain admin
    dn = create_user_udm(users, lo_domain_admin, pos, ou.user_dn)
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.domain_admin_id
    assert attrs['univentionObjectModifiersID'] == ou.domain_admin_id
    # modify as ou1 admin
    obj = users.lookup(None, lo_ou1_admin, filter_s='cn=*', base=dn, scope='base')[0]
    obj.open()
    print(obj.dn)
    obj['description'] = random_username()
    obj.modify()
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.domain_admin_id
    assert attrs['univentionObjectModifiersID'] == ou.admin_id

    # create as ou1 admin
    dn = create_user_udm(users, lo_ou1_admin, pos, ou.dn)
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.admin_id
    assert attrs['univentionObjectModifiersID'] == ou.admin_id
    # modify as domain admin
    obj = users.lookup(None, lo_domain_admin, filter_s='cn=*', base=dn, scope='base')[0]
    obj.open()
    obj['description'] = random_username()
    obj.modify()
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.admin_id
    assert attrs['univentionObjectModifiersID'] == ou.domain_admin_id

    # create as ou2 admin
    dn = create_user_udm(users, lo_ou2_admin, pos, ou.dn2)
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.admin2_id
    assert attrs['univentionObjectModifiersID'] == ou.admin2_id


def test_udm_rename(ou, lo, random_username, lo_domain_admin, lo_ou2_admin, create_user_udm):
    lo_priv = getAdminConnection()[0]
    admin_connection_getter = lambda: lo_priv  # noqa: E731
    Authorization.enable(admin_connection_getter)

    lo_domain_admin = Authorization.inject_ldap_connection(lo_domain_admin)
    lo_ou2_admin = Authorization.inject_ldap_connection(lo_ou2_admin)

    pos = position(lo_domain_admin.base)
    modules.update()
    users = modules.get('users/user')
    modules.init(lo_domain_admin, pos, users)

    # create as domain admin
    dn = create_user_udm(users, lo_domain_admin, pos, ou.dn2, cleanup=False)
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.domain_admin_id
    assert attrs['univentionObjectModifiersID'] == ou.domain_admin_id

    # change rdn as ou2 admin
    obj = users.lookup(None, lo_ou2_admin, filter_s='cn=*', base=dn, scope='base')[0]
    obj.open()
    obj['username'] = random_username()
    new_dn = obj.modify()
    assert new_dn != dn
    attrs = lo.get(new_dn)
    assert attrs['univentionObjectCreatorsID'] == ou.domain_admin_id
    assert attrs['univentionObjectModifiersID'] == ou.admin2_id
    # check also the modifiers id for primary group
    group_attrs = lo.get(obj['primaryGroup'])
    assert group_attrs['univentionObjectModifiersID'] == ou.admin2_id

    obj = users.lookup(None, lo_domain_admin, filter_s='cn=*', base=new_dn, scope='base')[0]
    obj.open()
    obj.remove()


def test_udm_move(ou, lo, lo_domain_admin, lo_ou1_admin, create_user_udm):
    lo_priv = getAdminConnection()[0]
    admin_connection_getter = lambda: lo_priv  # noqa: E731
    Authorization.enable(admin_connection_getter)

    lo_domain_admin = Authorization.inject_ldap_connection(lo_domain_admin)
    lo_ou1_admin = Authorization.inject_ldap_connection(lo_ou1_admin)

    pos = position(lo_domain_admin.base)
    modules.update()
    users = modules.get('users/user')

    # create as domain admin
    dn = create_user_udm(users, lo_domain_admin, pos, ou.dn, cleanup=False)
    attrs = lo.get(dn)
    assert attrs['univentionObjectCreatorsID'] == ou.domain_admin_id
    assert attrs['univentionObjectModifiersID'] == ou.domain_admin_id

    # move as ou1 admin
    obj = users.lookup(None, lo_ou1_admin, filter_s='cn=*', base=dn, scope='base')[0]
    obj.open()
    new_dn = dn.replace(ou.dn, ou.user_default_container)
    obj.move(new_dn)
    attrs = lo.get(new_dn)
    assert attrs['univentionObjectCreatorsID'] == ou.domain_admin_id
    assert attrs['univentionObjectModifiersID'] == ou.admin_id
    # check also the modifiers id for primary group
    group_attrs = lo.get(obj['primaryGroup'])
    # FIXME: should be ou.admin_id
    # i guess this is because the slapd refint overlay updates the uniqueMember
    # of the groups when moving a user object, we still have this
    #
    #  /usr/lib/python3/dist-packages/univention/admin/handlers/__init__.py(893)move()
    # -> res = n(self._move(newdn, ignore_license=ignore_license))
    #  /usr/lib/python3/dist-packages/univention/admin/handlers/users/user.py(2038)_move()
    # -> dn = super()._move(newdn, modify_childs, ignore_license)
    #  /usr/lib/python3/dist-packages/univention/admin/handlers/__init__.py(1616)_move()
    # -> self._move_in_groups(olddn)  # can be done always, will do nothing if oldinfo has no attribute 'groups'
    #  /usr/lib/python3/dist-packages/univention/admin/handlers/__init__.py(1596)_move_in_groups()
    # -> self.lo.authz_connection.modify(
    #  /usr/lib/python3/dist-packages/univention/admin/uldap.py(830)modify()
    # -> return self.lo.modify(dn, changes, serverctrls=serverctrls, response=response, rename_callback=rename_callback)
    #  /usr/lib/python3/dist-packages/univention/uldap.py(195)_decorated()
    # -> return func(self, *args, **kwargs)
    #  /usr/lib/python3/dist-packages/univention/uldap.py(714)modify()
    #
    # but this is unnecessary as it wants to remove the old and add the new dn,
    # which is already done by refint, and gets ldap.NO_SUCH_ATTRIBUTE and ldap.TYPE_OR_VALUE_EXISTS
    # in this case there is no modification with univention.uldap and the univentionObjectModifiersID
    # is not updated
    assert group_attrs['univentionObjectModifiersID'] == ou.domain_admin_id

    obj = users.lookup(None, lo_domain_admin, filter_s='cn=*', base=new_dn, scope='base')[0]
    obj.open()
    obj.remove()
