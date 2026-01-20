#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test the /directory/unmap-ldap-attributes endpoint
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-rest

import base64
import subprocess
import time

import requests

from univention.testing.strings import random_name


def test_invented_object(account):
    dn = account.binddn
    # uid=Administrator... surely nonsense, but shows that
    # (a) there is no lookup in case the dn actually exists
    # (b) dn does not need to make sense for attributes

    attrs = {
        'cn': [b'fantasy'],
        'gidNumber': [b'5011'],
        'sambaGroupType': [b'2'],
        'univentionGroupType': [b'-2147483646'],
        'univentionObjectIdentifier': [b'6ab9be03-4c95-4989-829f-621e370da07a'],
        'sambaSID': [b'S-1-5-21-3939622176-1304685295-672766427-11023'],
        'objectClass': [b'sambaGroupMapping', b'univentionGroup', b'top', b'posixGroup', b'univentionObject'],
        'univentionObjectType': [b'groups/group'],
    }

    _attrs = {k: [base64.b64encode(_v).decode('ASCII') for _v in v] for k, v in attrs.items()}  # the request uses b64 encoded values as we cannot send bytes (e.g. jpegPhoto) via JSON
    auth = (account.username, account.bindpw)
    response = requests.post('http://localhost/univention/udm/directory/unmap-ldap-attributes', json={'dn': dn, 'attributes': _attrs}, headers={'Accept': 'application/json'}, auth=auth)
    assert response.json()['dn'] == dn
    assert response.json()['objectType'] == 'groups/group'
    assert response.json()['properties']['name'] == 'fantasy'
    assert response.json()['properties']['gidNumber'] == 5011


def test_broken_object(account):
    dn = account.binddn
    attrs = {
        'cn': [b'fantasy'],
        'gidNumber': [b'5011'],
        'sambaGroupType': [b'2'],
        'univentionGroupType': [b'-2147483646'],
        'univentionObjectIdentifier': [b'6ab9be03-4c95-4989-829f-621e370da07a'],
        'sambaSID': [b'S-1-5-21-3939622176-1304685295-672766427-11023'],
        'objectClass': [b'sambaGroupMapping', b'top', b'posixGroup', b'univentionObject'],  # note that we are missing b'univentionGroup'
        'univentionObjectType': [b'groups/group'],  # but we clearly want groups/group -> will UDM REST recognize?
    }

    _attrs = {k: [base64.b64encode(_v).decode('ASCII') for _v in v] for k, v in attrs.items()}  # the request uses b64 encoded values as we cannot send bytes (e.g. jpegPhoto) via JSON
    auth = (account.username, account.bindpw)
    response = requests.post('http://localhost/univention/udm/directory/unmap-ldap-attributes', json={'dn': dn, 'attributes': _attrs}, headers={'Accept': 'application/json'}, auth=auth)
    assert response.status_code == 422


def test_unknown_object(account):
    dn = account.binddn
    attrs = {
        'cn': [b'fantasy'],  # this is a bit little, will UDM REST give the correct status_code?
    }

    _attrs = {k: [base64.b64encode(_v).decode('ASCII') for _v in v] for k, v in attrs.items()}  # the request uses b64 encoded values as we cannot send bytes (e.g. jpegPhoto) via JSON
    auth = (account.username, account.bindpw)
    response = requests.post('http://localhost/univention/udm/directory/unmap-ldap-attributes', json={'dn': dn, 'attributes': _attrs}, headers={'Accept': 'application/json'}, auth=auth)
    assert response.status_code == 422


def test_module_inits_with_new_extended_attribute(account, lo, udm):
    # first, get the user data
    dn = account.binddn
    attrs = lo.get(dn)

    # second create ext attribute and restart UDM REST, so that unmap-ldap-attributes never "saw" the users module
    name = f'ext-attr-{random_name()}'
    value = f'ext-attr-value-{random_name()}'
    udm.create_object(
        'settings/extended_attribute',
        position=udm.UNIVENTION_CONTAINER,
        name=name,
        shortDescription=name,
        CLIName=name,
        module='users/user',
        objectClass='univentionFreeAttributes',
        ldapMapping='univentionFreeAttribute9',
        syntax='string',
        multivalue=0,
        valueRequired=0,
        mayChange=1,
    )
    attrs['univentionFreeAttribute9'] = [value.encode()]  # add a value for the new ext attribute
    subprocess.call(['systemctl', 'restart', 'univention-directory-manager-rest.service'])
    time.sleep(3)

    # third, check if we get the new ext attr from the unmap-ldap-attributes endpoint
    auth = (account.username, account.bindpw)
    _attrs = {k: [base64.b64encode(_v).decode('ASCII') for _v in v] for k, v in attrs.items()}  # the request uses b64 encoded values as we cannot send bytes (e.g. jpegPhoto) via JSON
    response = requests.post('http://localhost/univention/udm/directory/unmap-ldap-attributes', json={'dn': dn, 'attributes': _attrs}, headers={'Accept': 'application/json'}, auth=auth)
    assert response.status_code == 200
    data = response.json()
    assert name in data['properties']
    assert data['properties'][name] == value
