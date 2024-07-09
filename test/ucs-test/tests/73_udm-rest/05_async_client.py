#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test asynchronous client
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-rest
# execute with: --tb=native -s -l -vv --cov-report=term-missing  --cov-report=html --cov=univention.admin.rest.async_client


import subprocess

import pytest

from univention.admin.rest.async_client import (
    UDM, NotFound, PatchDocument, ServiceUnavailable, UnprocessableEntity, _NoRelation,
)
from univention.testing import strings as uts
from univention.testing.utils import verify_ldap_object


@pytest.mark.asyncio()
async def test_create_modify_move_remove(random_string, ucr):
    uri = 'http://localhost/univention/udm/'
    pwd = ucr.get('tests/domainadmin/pwd', 'univention')
    async with UDM.http(uri, 'Administrator', pwd) as udm:
        module = await udm.get("users/user")
        cn = await udm.get("container/cn")
        obj = await module.new()
        obj.properties['username'] = uts.random_username()
        obj.properties['lastname'] = uts.random_string()
        obj.properties['firstname'] = uts.random_string()
        obj.properties['description'] = uts.random_string()
        with pytest.raises(UnprocessableEntity):
            await obj.save()
        obj.properties['password'] = uts.random_string()
        await obj.save()

        verify_ldap_object(obj.dn, {
            'uid': [obj.properties['username']],
            'sn': [obj.properties['lastname']],
            'givenName': [obj.properties['firstname']],
            'description': [obj.properties['description']],
        })

        obj = await module.get(obj.dn)

        async for obj2 in module.search(filter='username=%s' % obj.properties['username'], opened=False):
            assert obj2.dn == obj.dn
        async for obj2 in module.search(filter='username=%s' % obj.properties['username'], opened=True):
            assert obj2.dn == obj.dn

        assert isinstance(obj.options, dict)
        assert isinstance(obj.policies, dict)
        assert isinstance(obj.position, str)
        assert isinstance(obj.uri, str)
        assert obj.superordinate is None

        assert isinstance(await obj.generate_service_specific_password('radius'), str)
        obj.etag = None
        obj.last_modified = None
        await obj.reload()

        # test that the user is and only is in group Domain Users
        group_names = []
        for group in obj.objects.groups:
            grp = await group.open()
            group_names.append(grp.properties['name'])
        domain_users = ucr.get('groups/default/domainusers', 'Domain Users')  # AD Member?
        assert group_names == [domain_users]

        # TODO: test move and rename
        container = await cn.new()
        container.properties['name'] = uts.random_string()
        await container.save()

        container2 = await cn.new()
        container2.properties['name'] = uts.random_string()
        await container2.save()

        await obj.move(container.dn)
        assert container.dn in obj.dn

        await container.move(container2.dn)
        assert container2.dn in container.dn

        obj.hal.clear()
        obj.representation['dn'] = 'uid=%s,%s' % (obj.properties['username'], container.dn)
        await obj.reload()

        obj.properties['description'] = 'muhahaha'
        await obj.save()
        verify_ldap_object(obj.dn, {
            'uid': [obj.properties['username']],
            'sn': [obj.properties['lastname']],
            'givenName': [obj.properties['firstname']],
            'description': [obj.properties['description']],
        })

        await obj.delete()
        verify_ldap_object(obj.dn, should_exist=False)


@pytest.mark.asyncio()
async def test_json_patch(random_string, ucr):
    uri = 'http://localhost/univention/udm/'
    pwd = ucr.get('tests/domainadmin/pwd', 'univention')
    async with UDM.http(uri, 'Administrator', pwd) as udm:
        module = await udm.get("users/user")
        obj = await module.new()
        patch = PatchDocument()
        username = uts.random_username()
        lastname = uts.random_string()
        firstname = uts.random_string()
        description = uts.random_string()
        patch.replace(['properties', 'username'], username)
        patch.replace(['properties', 'lastname'], lastname)
        patch.replace(['properties', 'firstname'], firstname)
        patch.replace(['properties', 'password'], uts.random_string())
        patch.replace(['properties', 'description'], description)
        await obj.json_patch(patch.patch)
        verify_ldap_object(obj.dn, {
            'uid': [username],
            # 'sn': [lastname],
            'givenName': [firstname],
            'description': [description],
        }, retry_count=1)

        patch = PatchDocument()
        firstname = uts.random_string()
        patch.add(['properties', 'firstname'], firstname)  # not multivalue, but let's try
        patch.remove(['properties', 'description'], description)
        await obj.json_patch(patch.patch)
        verify_ldap_object(obj.dn, {
            'uid': [username],
            # 'sn': [lastname],
            # 'givenName': [firstname],
            'description': [],
        }, retry_count=1)


@pytest.mark.asyncio()
async def test_various_api_methods(random_string, ucr):
    uri = 'http://localhost/univention/udm/'
    pwd = ucr.get('tests/domainadmin/pwd', 'univention')
    async with UDM.http(uri, 'Administrator', pwd) as udm:
        assert (await udm.get_ldap_base()) == ucr['ldap/base']
        mod = await udm.get('container/dc')
        with pytest.raises(_NoRelation):
            await mod.new()
        assert (await (await udm.get('users/user')).new()).uri is None

        obj = await udm.obj_by_dn(ucr['ldap/base'])
        assert obj
        obj2 = await udm.obj_by_uuid(obj.representation['uuid'])
        obj3 = await udm.get_object('container/dc', ucr['ldap/base'])
        obj4 = await mod.get_by_entry_uuid(obj.representation['uuid'])

        assert obj.dn == obj2.dn == obj3.dn == obj4.dn

        await obj.reload()
        assert obj.dn == obj2.dn

        assert repr(udm).startswith('UDM(uri=')
        assert repr(mod).startswith('Module(uri=')
        assert repr(obj).startswith('Object(module=')
        async for shallow_obj in mod.search(opened=False):
            assert repr(shallow_obj).startswith('ShallowObject(dn=')

        assert (await udm.get('users/nothing')) is None

        assert (await mod.get_layout())
        assert (await mod.get_properties())
        assert (await mod.get_property_choices('dnsForwardZone'))
        with pytest.raises(_NoRelation):
            await mod.policy_result('policies/nothing', ucr['ldap/base'])
        assert isinstance(await mod.policy_result('policies/umc', ucr['ldap/base']), dict)

        assert (await obj.get_layout())
        assert (await obj.get_properties())
        assert (await obj.get_property_choices('dnsForwardZone'))
        assert isinstance(await obj.policy_result('policies/umc'), dict)

        report_types = await (await udm.get('users/user')).get_report_types()
        assert len(report_types) == 2
        await (await udm.get('users/user')).create_report(report_types[0], ['uid=Administrator,cn=users,%(ldap/base)s' % ucr])

        superordinate = (await (await udm.get('dns/forward_zone')).search().__anext__()).dn
        ptr = (await (await udm.get('dns/host_record')).search(superordinate=superordinate, opened=True).__anext__())
        assert ptr.dn
        ptr.superordinate = superordinate

        with pytest.raises(NotFound):
            await mod.get('cn=users,%(ldap/base)s' % ucr)
        with pytest.raises(UnprocessableEntity):
            await mod.get('cn=notexists,%(ldap/base)s' % ucr)
        with pytest.raises(NotFound):
            await mod.get_by_entry_uuid('6d925222-6706-48c5-bf33-86ef00610b3f')


@pytest.mark.asyncio()
async def test_service_unavailable(ucr):
    uri = 'http://localhost/univention/udm/'
    pwd = ucr.get('tests/domainadmin/pwd', 'univention')
    async with UDM.http(uri, 'Administrator', pwd) as udm:
        subprocess.call(['systemctl', 'stop', 'univention-directory-manager-rest'])  # noqa: ASYNC101
        try:
            with pytest.raises(ServiceUnavailable):
                await udm.get("users/user")
        finally:
            subprocess.call(['systemctl', 'start', 'univention-directory-manager-rest'])  # noqa: ASYNC101
