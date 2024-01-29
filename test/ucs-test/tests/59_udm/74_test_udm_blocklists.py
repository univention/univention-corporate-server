#!/usr/share/ucs-test/runner pytest-3
## desc: Test blocklist
## tags: [udm,udm-settings,apptest]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from univention.admin import modules
from univention.admin.blocklist import hash_blocklist_value
from univention.admin.rest.client import UDM as UDM_REST, UnprocessableEntity
from univention.admin.uexceptions import noObject
from univention.admin.uldap import getMachineConnection, position as uldap_position
from univention.udm import UDM
from univention.udm.exceptions import NoObject


BASE = "cn=blocklists,cn=internal"


def get_uuid() -> str:
    return str(uuid.uuid1())


@pytest.fixture()
def blocklist_position(random_string):
    name = random_string()
    lo, po = getMachineConnection(ldap_master=True)
    dn = f"cn={name},{BASE}"
    lo.add(dn, [
        ('cn', name.encode('UTF-8')),
        ('objectClass', b'organizationalRole'),
    ])

    yield SimpleNamespace(cn=name, dn=dn)

    print(f"cleanup {dn}")
    lo.delete(dn)


@pytest.fixture()
def blocklist_list(random_string, udm):
    name = random_string()
    data = {
        'name': name,
        'blockingProperties': 'users/user mailPrimaryAddress',
    }
    dn = udm.create_object('blocklists/list', **data)

    return SimpleNamespace(cn=name, dn=dn)


@pytest.fixture()
def add_ldap_blocklistentries(blocklist_position, random_string):
    dns = []
    container = blocklist_position.cn

    def _func(cns: list) -> list:
        lo, po = getMachineConnection(ldap_master=True)
        for cn in cns:
            dn = f"cn={cn},cn={container},{BASE}"
            lo.add(dn, [
                ('cn', cn.encode('UTF-8')),
                ('objectClass', [b'univentionBlockingEntry', b'univentionObject']),
                ('originUniventionObjectIdentifier', get_uuid().encode('UTF-8')),
                ('blockedUntil', b'21241212000000Z'),
                ('univentionObjectType', b'settings/blocklistentry')
            ])
            dns.append(dn)
        return dns

    yield _func

    lo, po = getMachineConnection(ldap_master=True)
    for dn in dns:
        print(f"cleanup {dn}")
        try:
            lo.delete(dn)
        except noObject:
            pass


@pytest.fixture()
def udm_rest_client(ucr, account):
    udm_rest = UDM_REST(
        uri='https://%(hostname)s.%(domainname)s/univention/udm/' % ucr,
        username=account.username,
        password=account.bindpw,
    )
    return udm_rest.get('blocklists/entry')


def test_udm_cli_list(add_ldap_blocklistentries, random_string, udm):
    name = random_string()
    blocklist_entries = [f'{name}1', f'{name}2', f'{name}3']
    dns = add_ldap_blocklistentries(blocklist_entries)
    obj_dns = [i[0] for i in udm.list_objects('blocklists/entry')]
    for dn in dns:
        assert dn in obj_dns


def test_udm_cli_create_without_position(random_string, udm, blocklist_list):
    value = random_string()
    dn = f'cn={hash_blocklist_value(value)},{blocklist_list.dn}'
    data = {
        'value': value,
        'blockedUntil': '33331212010101Z',
        'originUniventionObjectIdentifier': get_uuid(),
        'superordinate': blocklist_list.dn,
    }
    udm.create_object('blocklists/entry', **data)
    obj_dns = [i[0] for i in udm.list_objects('blocklists/entry')]
    assert dn in obj_dns
    udm.remove_object('blocklists/entry', dn=dn)
    obj_dns = [i[0] for i in udm.list_objects('blocklists/entry')]
    assert dn not in obj_dns


def test_udm_cli_create_with_position(blocklist_list, random_string, udm):
    # with position/superordinate
    value = random_string()
    dn = f'cn={hash_blocklist_value(value)},{blocklist_list.dn}'
    data = {
        'value': value,
        'blockedUntil': '33331212010101Z',
        'originUniventionObjectIdentifier': get_uuid(),
        'position': blocklist_list.dn,
    }
    udm.create_object('blocklists/entry', **data)
    obj_dns = [i[0] for i in udm.list_objects('blocklists/entry')]
    assert dn in obj_dns
    udm.remove_object('blocklists/entry', dn=dn)
    obj_dns = [i[0] for i in udm.list_objects('blocklists/entry')]
    assert dn not in obj_dns


def test_udm_api_list_delete(add_ldap_blocklistentries, random_string):
    name = random_string()
    blocklist_entries = [f'{name}1', f'{name}2', f'{name}3']
    dns = add_ldap_blocklistentries(blocklist_entries)
    # list
    bl_mod = UDM.machine().version(2).get('blocklists/entry')
    objects = bl_mod.search(base=BASE)
    object_dns = [b.dn for b in objects]
    for dn in dns:
        assert dn in object_dns
    # remove
    for dn in dns:
        obj = bl_mod.get(dn)
        obj.delete()
        with pytest.raises(NoObject):
            bl_mod.get(dn)


def test_udm_api_create(random_string, blocklist_list):
    bl_mod = UDM.machine().version(2).get('blocklists/entry')
    value = random_string()
    dn = f'cn={hash_blocklist_value(value)},{blocklist_list.dn}'
    new_bl = bl_mod.new(superordinate=blocklist_list.dn)
    new_bl.props.value = value
    new_bl.props.blockedUntil = '33331212010101Z'
    new_bl.props.originUniventionObjectIdentifier = get_uuid()
    new_bl.save()
    obj = bl_mod.get(new_bl.dn)
    assert hash_blocklist_value(value) == obj.props.value
    assert obj.dn == dn
    obj.delete()
    with pytest.raises(NoObject):
        bl_mod.get(new_bl.dn)


def test_udm_python_list_delete(add_ldap_blocklistentries, random_string):
    name = random_string()
    blocklist_entries = [f'{name}1', f'{name}2', f'{name}3']
    dns = add_ldap_blocklistentries(blocklist_entries)
    lo, position = getMachineConnection(ldap_master=True)
    modules.update()
    blocklistentry_mod = modules.get('blocklists/entry')
    modules.init(lo, position, blocklistentry_mod)
    # list
    blocklist_objects = blocklistentry_mod.lookup(None, lo, "objectclass=*")
    blocklist_object_dns = [bl.dn for bl in blocklist_objects]
    for dn in dns:
        assert dn in blocklist_object_dns
    # remove
    for dn in dns:
        print(dn)
        obj = blocklistentry_mod.lookup(None, lo, None, base=dn, unique=True, required=True)[0]
        obj.open()
        obj.remove()


def test_udm_python_create_superordinate(random_string, blocklist_list):
    lo, position = getMachineConnection(ldap_master=True)
    modules.update()
    blocklistentry_mod = modules.get('blocklists/entry')
    blocklist_mod = modules.get('blocklists/list')
    modules.init(lo, position, blocklistentry_mod)
    modules.init(lo, position, blocklist_mod)
    list_obj = blocklist_mod.lookup(None, lo, filter_s=f'name={blocklist_list.cn}')[0]
    new = blocklistentry_mod.object(None, lo, None)
    value = random_string()
    new['value'] = value
    new['blockedUntil'] = '20331212000000Z'
    new['originUniventionObjectIdentifier'] = get_uuid()
    new.superordinate = list_obj
    new.position = uldap_position(blocklist_list.dn)
    new.create()
    obj = blocklistentry_mod.lookup(None, lo, f'value={value}')[0]
    obj.open()
    assert hash_blocklist_value(value) == obj['value']
    assert obj.dn == f'cn={hash_blocklist_value(value)},cn={blocklist_list.cn},{BASE}'
    obj.remove()
    assert not blocklistentry_mod.lookup(None, lo, f'value={value}')


def test_udm_python_create_with_position(blocklist_list, random_string):
    lo, position = getMachineConnection(ldap_master=True)
    modules.update()
    blocklistentry_mod = modules.get('blocklists/entry')
    modules.init(lo, position, blocklistentry_mod)
    position.setBase(blocklist_list.dn)
    new = blocklistentry_mod.object(None, lo, position)
    value = random_string()
    new['value'] = value
    new['blockedUntil'] = '20331212000000Z'
    new['originUniventionObjectIdentifier'] = get_uuid()
    new.create()
    entry_obj = blocklistentry_mod.lookup(None, lo, f'value={value}')[0]
    assert entry_obj.dn == f'cn={hash_blocklist_value(value)},{blocklist_list.dn}'
    entry_obj.remove()
    assert not blocklistentry_mod.lookup(None, lo, f'value={value}')


def test_udm_rest_list_delete(add_ldap_blocklistentries, random_string, udm_rest_client):
    name = random_string()
    blocklist_entries = [f'{name}1', f'{name}2', f'{name}3']
    dns = add_ldap_blocklistentries(blocklist_entries)

    # list all
    blocklistentries = [i.dn for i in udm_rest_client.search()]
    for dn in dns:
        assert dn in blocklistentries

    # get and delete
    for dn in dns:
        obj = udm_rest_client.get(dn)
        assert obj.dn == dn
        assert obj.position.endswith(BASE)
        assert obj.properties['value'].startswith(name)
        obj.delete()
        with pytest.raises(UnprocessableEntity):
            udm_rest_client.get(dn)


def test_udm_rest_create_without_position(random_string, udm_rest_client, blocklist_list):
    value = random_string()
    new = udm_rest_client.new()
    new.properties['value'] = value
    new.properties['blockedUntil'] = '99331212000000Z'
    new.superordinate = blocklist_list.dn
    my_uuid = get_uuid()
    new.properties['originUniventionObjectIdentifier'] = my_uuid
    new.position = None
    new.save()
    obj = udm_rest_client.get(new.dn)
    assert obj.properties['value'] == hash_blocklist_value(value)
    assert obj.properties['blockedUntil'] == '99331212000000Z'
    assert obj.properties['originUniventionObjectIdentifier'] == my_uuid
    assert obj.dn == f'cn={hash_blocklist_value(value)},{blocklist_list.dn}'
    obj.delete()
    with pytest.raises(UnprocessableEntity):
        udm_rest_client.get(obj.dn)


def test_udm_rest_create_with_position(blocklist_list, random_string, udm_rest_client):
    value = random_string()
    new = udm_rest_client.new()
    new.properties['value'] = value
    new.properties['blockedUntil'] = '99331212000000Z'
    my_uuid = get_uuid()
    new.properties['originUniventionObjectIdentifier'] = my_uuid
    new.position = blocklist_list.dn
    new.save()
    obj = udm_rest_client.get(new.dn)
    assert obj.properties['value'] == hash_blocklist_value(value)
    assert obj.properties['blockedUntil'] == '99331212000000Z'
    assert obj.properties['originUniventionObjectIdentifier'] == my_uuid
    assert obj.dn == f'cn={hash_blocklist_value(value)},{blocklist_list.dn}'
    obj.delete()
    with pytest.raises(UnprocessableEntity):
        udm_rest_client.get(obj.dn)
