# SPDX-FileCopyrightText: 2013-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Common functions/fixtures for recyclebin tests."""

import random
from types import SimpleNamespace

import pytest
from ldap.dn import escape_dn_chars

from univention.config_registry import ucr as _ucr
from univention.testing.strings import random_username
from univention.testing.utils import verify_ldap_object


RECYCLEBIN_DN = "cn=recyclebin,cn=internal"


def _deleted_object_dn(dn, u_obj_id):
    """Get the DN of the deleted object in the recyclebin"""
    return f'univentionRecycleBinOriginalDN={escape_dn_chars(dn)}+univentionRecycleBinOriginalUniventionObjectIdentifier={escape_dn_chars(u_obj_id)},{RECYCLEBIN_DN}'


def __recyclebin_policy(udm, ldap_base):
    name = random_username()
    retention_days = random.randint(100, 300)  # days
    pol_dn = udm.create_object(
        'policies/recyclebin',
        position=f'cn=policies,{ldap_base}',
        name=name,
        udm_modules=['users/user', 'groups/group'],
        retention_days=retention_days,
        wait_for_replication=False,
    )
    con_dn = udm.create_object('container/cn', position=f'{ldap_base}', name=f'recyclebin_{name}', policy_reference=pol_dn, wait_for_replication=False)
    return con_dn, retention_days


@pytest.fixture(scope='module')
def recyclebin_policy_session(udm_session, ldap_base):
    return __recyclebin_policy(udm_session, ldap_base)


@pytest.fixture
def recyclebin_policy(udm, ldap_base):
    return __recyclebin_policy(udm, ldap_base)


@pytest.fixture
def deleted_user_object(recyclebin_policy, udm):
    container_recyclebin_policy, _ = recyclebin_policy
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(user_dn, uoid)
    verify_ldap_object(deleted_dn, should_exist=True)
    return user_dn, deleted_dn


@pytest.fixture(scope='module')
def share_for_testing_session(udm_session, ldap_base):
    """Create a share for testing homeShare attributes"""
    hostname = _ucr.get('hostname', 'server')
    domainname = _ucr.get('domainname', 'ucs.test')
    share_dn = udm_session.create_object(
        'shares/share',
        position=f'cn=shares,{ldap_base}',
        name='test_recyclebin_share',
        host=f'{hostname}.{domainname}',
        path='/home/shares/test_recyclebin',
        wait_for_replication=False,
    )
    return share_dn


@pytest.fixture
def deleted_object_user_properties(ldap_base) -> SimpleNamespace:
    data = {
        'originalDN': f'uid=testdeluser,cn=users,{ldap_base}',
        'purgeAt': '20261212085050Z',
        'removalDate': '30261212085050Z',
        'originalObjectType': 'users/user',
        'originalUniventionObjectIdentifier': 'f2b2e6ff-ad41-47ce-87ea-9d2ac39aaaca',
        'originalEntryUUID': 'f2b2e6ff-ad41-47ce-87ea-9d2ac33aaacb',
        'originalObjectClasses': [
            'automount',
            'univentionMail',
            'univentionPWHistory',
            'inetOrgPerson',
            'person',
            'organizationalPerson',
            'sambaSamAccount',
            'top',
            'shadowAccount',
            'univentionPerson',
            'krb5Principal',
            'krb5KDCEntry',
            'univentionObject',
            'posixAccount',
        ],
        'ldap_attrs': {
            'cn': [b'lastname'],
            'displayName': [b'lastname'],
            'gecos': [b'lastname'],
            'gidNumber': [b'5001'],
            'homeDirectory': [b'/home/test1'],
            'krb5KDCFlags': [b'126'],
            'krb5Key': [
                b'07\xa1\x1b0\x19\xa0\x03\x02\x01\x11\xa1\x12\x04\x10\xa7\x86\xdc\x0f\xdcn0c\x91\x98Z\xa0\xd2Y\xc7t\xa2\x180\x16\xa0\x03\x02\x01\x03\xa1\x0f\x04\rUCS.TESTtest1',
                b'07\xa1\x1b0\x19\xa0\x03\x02\x01\x17\xa1\x12\x04\x10\xca\xa1#\x9dD\xda~\xdf\x92k\xce9\xf5\xc6]\x0f\xa2\x180\x16\xa0\x03\x02\x01\x03\xa1\x0f\x04\rUCS.TESTtest1',
            ],
            'krb5KeyVersionNumber': [b'1'],
            'krb5MaxLife': [b'86400'],
            'krb5MaxRenew': [b'604800'],
            'krb5PrincipalName': [b'test1@UCS.TEST'],
            'loginShell': [b'/bin/bash'],
            'mailForwardCopyToSelf': [b'0'],
            'pwhistory': [b' $6$znLCTmtimN7H0T92$2iuAyLCkTT/hjoSqTVzMy7U7Fh5OGHaHc6fGupy4KvYoSA2V4FCsfcw3qfQyKA5goXFclV6hvZNCk.xx3B4/u/'],
            'sambaAcctFlags': [b'[U          ]'],
            'sambaBadPasswordCount': [b'0'],
            'sambaBadPasswordTime': [b'0'],
            'sambaNTPassword': [b'CAA1239D44DA7EDF926BCE39F5C65D0F'],
            'sambaPrimaryGroupSID': [b'S-1-5-21-4050189495-1942909977-1471735533-513'],
            'sambaPwdLastSet': [b'1756909087'],
            'sambaSID': [b'S-1-5-21-4050189495-1942909977-1471735533-5386'],
            'sn': [b'lastname'],
            'uid': [b'testdeluser'],
            'uidNumber': [b'2193'],
            'userPassword': [b'{crypt}$6$Si5dxjbGT8wI147P$AazXJ3prqclvVvCuIiou97V0XkzcuUoRiHqN.bqidlcg8kruJe23IIq6lZCJ00WuSPYbuE6IfTyFmPA3EipgA1'],
            'memberOf': [
                f'cn=Domain Users,cn=groups,{ldap_base}'.encode(),
                f'cn=Domain Admins,cn=groups,{ldap_base}'.encode(),
                f'cn=doesnotexist,cn=groups,{ldap_base}'.encode(),
            ],
        },
        'ignore_ldap_attrs': {
            # these should be ignored
            'structuralObjectClass': [b'inetOrgPerson'],
            'entryUUID': [b'09679f3a-1867-1040-8fe5-d7f9203edc52'],
            'creatorsName': [b'cn=admin,dc=ucs,dc=test'],
            'createTimestamp': [b'20250828142840Z'],
            'entryCSN': [b'20250912080929.667762Z#000000#000#000000'],
            'modifiersName': [b'cn=admin,dc=ucs,dc=test'],
            'modifyTimestamp': [b'20250912080929Z'],
            'entryDN': [b'uid=Administrator,cn=users,dc=ucs,dc=test'],
            'subschemaSubentry': [b'cn=Subschema'],
            'hasSubordinates': [b'FALSE'],
        },
    }
    return SimpleNamespace(**data)
