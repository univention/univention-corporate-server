#!/usr/share/ucs-test/runner pytest-3 -s
## desc: "Test the UCS<->AD sync with allow_subtree and UCR-V allow-subtree-ancestors"
## exposure: dangerous
## packages:
##  - univention-ad-connector
## tags:
##  - skip_admember

import subprocess

import ldap
import pytest

from adconnector import ADConnection, restart_adconnector, wait_for_sync


@pytest.fixture(scope='module')
def ad_connection():
    ad_connection = ADConnection()
    return ad_connection


@pytest.fixture
def create_ou_in_ad(ad_connection, prepare_cleanup):
    ous = []

    def _create_ou(name, position):
        dn = ad_connection.createou(name=name, position=position)
        ous.insert(0, dn)
        return dn

    yield _create_ou

    prepare_cleanup()

    for ou in ous:
        try:
            ad_connection.delete(ou)
        except ldap.NO_SUCH_OBJECT:
            pass


@pytest.fixture
def create_cn_in_ad(ad_connection, prepare_cleanup):
    cns = []

    def _container_create(name, position):
        dn = ad_connection.container_create(name=name, position=position)
        cns.append(dn)
        return dn

    yield _container_create

    prepare_cleanup()

    for cn in cns:
        try:
            ad_connection.delete(cn)
        except ldap.NO_SUCH_OBJECT:
            pass


@pytest.fixture
def ad_connector_preparation():
    wait_for_sync()
    yield
    wait_for_sync()
    restart_adconnector()


@pytest.fixture
def prepare_cleanup(ucr, udm):
    """Ensure we are syncing everything during cleanup step"""
    ucr_reverted = False

    def _prepare_cleanup():
        nonlocal ucr_reverted
        if not ucr_reverted:
            ucr.revert_to_original_registry()
            ucr.handler_set(['connector/ad/mapping/syncmode=sync'])
            restart_adconnector()
            wait_for_sync()
        ucr_reverted = True

    return _prepare_cleanup


def test_resync_from_ad_with_allow_subtree_ancestors(ucr, ad_connection, udm, create_ou_in_ad, create_cn_in_ad, ad_connector_preparation):
    ldap_base = ucr['ldap/base']
    ad_ldap_base = ucr['connector/ad/ldap/base']

    # subtree that is allowed
    dn_ou112_ucs = f'ou=ou112,ou=ou11,ou=ou1,{ldap_base}'
    dn_ou112_ad = f'ou=ou112,ou=ou11,ou=ou1,{ad_ldap_base}'

    dn_ou1_ucs = f'ou=ou1,{ldap_base}'
    dn_ou1_ad = f'ou=ou1,{ad_ldap_base}'
    dn_ou111_ucs = f'ou=ou111,ou=ou11,ou=ou1,{ldap_base}'
    dn_ou121_ucs = f'ou=ou121,ou=ou12,ou=ou1,{ldap_base}'
    dn_ou2_ucs = f'ou=ou2,{ldap_base}'
    dn_ou3_ucs = f'ou=ou3,{ldap_base}'

    # ignore the subtree of `ou1`
    ucr.handler_set(
        [
            f'connector/ad/mapping/ignoresubtree/ou1/ucs={dn_ou1_ucs}',
            f'connector/ad/mapping/ignoresubtree/ou1/ad={dn_ou1_ad}',
            'connector/ad/mapping/syncmode=sync',
            'connector/ad/mapping/allow-subtree-ancestors=yes',
        ],
    )
    restart_adconnector()

    # create the tree
    create_ou_in_ad(name='ou1', position=ad_ldap_base)
    create_ou_in_ad(name='ou11', position=f'ou=ou1,{ad_ldap_base}')
    create_ou_in_ad(name='ou12', position=f'ou=ou1,{ad_ldap_base}')
    create_ou_in_ad(name='ou111', position=f'ou=ou11,ou=ou1,{ad_ldap_base}')
    create_ou_in_ad(name='ou112', position=f'ou=ou11,ou=ou1,{ad_ldap_base}')
    create_ou_in_ad(name='ou121', position=f'ou=ou12,ou=ou1,{ad_ldap_base}')
    create_cn_in_ad(name='cn1121', position=f'ou=ou112,ou=ou11,ou=ou1,{ad_ldap_base}')

    wait_for_sync()

    # should exist now
    ad_connection.verify_object(dn_ou112_ad, {'name': 'ou112'})
    # ou112 should not exist in UCS yet
    udm.verify_ldap_object(dn_ou112_ucs, should_exist=False)

    # now don't ignore the subtree of `ou1` and allow the ou112 subtree
    ucr.handler_unset(
        [
            'connector/ad/mapping/ignoresubtree/ou1/ucs',
            'connector/ad/mapping/ignoresubtree/ou1/ad',
        ],
    )
    ucr.handler_set(
        [
            f'connector/ad/mapping/allowsubtree/ou112/ucs={dn_ou112_ucs}',
            f'connector/ad/mapping/allowsubtree/ou112/ad={dn_ou112_ad}',
        ],
    )
    restart_adconnector()

    # these should be ignored
    create_ou_in_ad(name='ou2', position=ad_ldap_base)
    create_ou_in_ad(name='ou3', position=ad_ldap_base)

    create_ou_in_ad(name='ou21', position=f'ou=ou2,{ad_ldap_base}')
    create_ou_in_ad(name='ou31', position=f'ou=ou3,{ad_ldap_base}')

    wait_for_sync()

    subprocess.check_call(['/usr/share/univention-ad-connector/resync_object_from_ad.py', '--filter', '(objectClass=*)', '--base', f'{dn_ou112_ad}'])
    wait_for_sync()

    udm.verify_ldap_object(dn_ou112_ucs, {'ou': ['ou112']})
    udm.verify_ldap_object(f'cn=cn1121,{dn_ou112_ucs}', {'cn': ['cn1121']})
    should_not_exist_in_ucs = [dn_ou111_ucs, dn_ou121_ucs, dn_ou2_ucs, dn_ou3_ucs]
    for dn in should_not_exist_in_ucs:
        udm.verify_ldap_object(dn, should_exist=False)

    p = subprocess.run(['/usr/sbin/univention-adconnector-list-rejected'], check=True, capture_output=True)
    assert f'{dn_ou112_ucs}' not in p.stdout.decode('utf-8')


def test_resync_from_ucs_with_allow_subtree_ancestors(ad_connection, udm, ucr, ad_connector_preparation):
    ldap_base = ucr['ldap/base']
    ad_ldap_base = ucr['connector/ad/ldap/base']

    # subtree that is allowed
    dn_ou112_ucs = f'ou=ou112,ou=ou11,ou=ou1,{ldap_base}'
    dn_ou112_ad = f'ou=ou112,ou=ou11,ou=ou1,{ad_ldap_base}'

    dn_ou1_ucs = f'ou=ou1,{ldap_base}'
    dn_ou1_ad = f'ou=ou1,{ad_ldap_base}'
    dn_ou111_ad = f'ou=ou111,ou=ou11,ou=ou1,{ad_ldap_base}'
    dn_ou121_ad = f'ou=ou121,ou=ou12,ou=ou1,{ad_ldap_base}'
    dn_ou2_ad = f'ou=ou2,{ad_ldap_base}'
    dn_ou3_ad = f'ou=ou3,{ad_ldap_base}'

    # ignore the subtree of `ou1`
    ucr.handler_set(
        [
            f'connector/ad/mapping/ignoresubtree/ou1/ucs={dn_ou1_ucs}',
            f'connector/ad/mapping/ignoresubtree/ou1/ad={dn_ou1_ad}',
        ],
    )
    restart_adconnector()

    # create the tree
    udm.create_object('container/ou', name='ou1', position=ldap_base)

    udm.create_object('container/ou', name='ou11', position=f'ou=ou1,{ldap_base}')
    udm.create_object('container/ou', name='ou12', position=f'ou=ou1,{ldap_base}')
    udm.create_object('container/ou', name='ou111', position=f'ou=ou11,ou=ou1,{ldap_base}')
    udm.create_object('container/ou', name='ou112', position=f'ou=ou11,ou=ou1,{ldap_base}')
    udm.create_object('container/ou', name='ou121', position=f'ou=ou12,ou=ou1,{ldap_base}')

    udm.create_object('container/cn', name='cn1121', position=f'ou=ou112,ou=ou11,ou=ou1,{ldap_base}')

    wait_for_sync()

    # ad object should not exist
    ad_connection.verify_object(dn_ou112_ad, None)
    udm.verify_ldap_object(dn_ou112_ucs, {'ou': ['ou112']})

    # don't ignore the subtree of `ou1` anymore and only
    # allow ou112
    ucr.handler_unset(
        [
            'connector/ad/mapping/ignoresubtree/ou1/ucs',
            'connector/ad/mapping/ignoresubtree/ou1/ad',
        ],
    )
    ucr.handler_set(
        [
            f'connector/ad/mapping/allowsubtree/ou112/ucs={dn_ou112_ucs}',
            f'connector/ad/mapping/allowsubtree/ou112/ad={dn_ou112_ad}',
            'connector/ad/mapping/syncmode=sync',
            'connector/ad/mapping/allow-subtree-ancestors=yes',
        ],
    )
    restart_adconnector()

    # these should be ignored by the connector
    udm.create_object('container/ou', name='ou2', position=ldap_base)
    udm.create_object('container/ou', name='ou3', position=ldap_base)
    udm.create_object('container/ou', name='ou21', position=f'ou=ou2,{ldap_base}')
    udm.create_object('container/ou', name='ou31', position=f'ou=ou3,{ldap_base}')

    wait_for_sync()

    subprocess.check_call(['/usr/share/univention-ad-connector/resync_object_from_ucs.py', '--filter', '(objectClass=*)', '--base', f'{dn_ou112_ucs}'])
    wait_for_sync()

    udm.verify_ldap_object(dn_ou112_ucs, {'ou': ['ou112']})
    udm.verify_ldap_object(f'cn=cn1121,{dn_ou112_ucs}', {'cn': ['cn1121']})

    should_not_exist_in_ad = [dn_ou111_ad, dn_ou121_ad, dn_ou2_ad, dn_ou3_ad]
    for dn in should_not_exist_in_ad:
        ad_connection.verify_object(dn, None)

    p = subprocess.run(['/usr/sbin/univention-adconnector-list-rejected'], check=True, capture_output=True)
    assert f'{dn_ou112_ucs}' not in p.stdout.decode('utf-8')


def test_allow_subtree_ancestors_ucs(ad_connection, udm, ucr, ad_connector_preparation):
    """
    Test the allow-subtree-ancestors UCR-Variable
    Synchronization direction UCS -> AD

    dc=ucs,dc=test
    ├── ou=ou1
    │   ├── ou=ou11
    │   │   ├── ou=ou111
    │   │   └── ou=ou112 <-- only subtree that is allowed
    │   │       └── cn=cn1121
    │   └── ou=ou12
    ├── ou=ou2
    │   └── ou=ou21
    └── ou=ou3
        └── ou=ou31

    Only OU ou112 is allowed and should be synchronized.
    """
    ldap_base = ucr['ldap/base']
    ad_ldap_base = ucr['connector/ad/ldap/base']

    # subtree that is allowed
    dn_ou112_ucs = f'ou=ou112,ou=ou11,ou=ou1,{ldap_base}'
    dn_ou112_ad = f'ou=ou112,ou=ou11,ou=ou1,{ad_ldap_base}'

    # subtrees that are implicitly not allowed
    dn_ou111_ad = f'ou=ou111,ou=ou11,ou=ou1,{ad_ldap_base}'
    dn_ou121_ad = f'ou=ou121,ou=ou12,ou=ou1,{ad_ldap_base}'
    dn_ou2_ad = f'ou=ou2,{ad_ldap_base}'
    dn_ou3_ad = f'ou=ou3,{ad_ldap_base}'

    ucr.handler_set(
        [
            f'connector/ad/mapping/allowsubtree/ou112/ucs={dn_ou112_ucs}',
            f'connector/ad/mapping/allowsubtree/ou112/ad={dn_ou112_ad}',
            'connector/ad/mapping/syncmode=sync',
            'connector/ad/mapping/allow-subtree-ancestors=yes',
        ],
    )
    restart_adconnector()

    udm.create_object('container/ou', name='ou1', position=ldap_base)
    udm.create_object('container/ou', name='ou2', position=ldap_base)
    udm.create_object('container/ou', name='ou3', position=ldap_base)

    udm.create_object('container/ou', name='ou11', position=f'ou=ou1,{ldap_base}')
    udm.create_object('container/ou', name='ou12', position=f'ou=ou1,{ldap_base}')
    udm.create_object('container/ou', name='ou21', position=f'ou=ou2,{ldap_base}')
    udm.create_object('container/ou', name='ou31', position=f'ou=ou3,{ldap_base}')

    udm.create_object('container/ou', name='ou111', position=f'ou=ou11,ou=ou1,{ldap_base}')
    udm.create_object('container/ou', name='ou112', position=f'ou=ou11,ou=ou1,{ldap_base}')
    udm.create_object('container/ou', name='ou121', position=f'ou=ou12,ou=ou1,{ldap_base}')

    udm.create_object('container/cn', name='cn1121', position=f'ou=ou112,ou=ou11,ou=ou1,{ldap_base}')

    wait_for_sync()
    ad_connection.verify_object(dn_ou112_ad, {'name': 'ou112'})
    ad_connection.verify_object(f'cn=cn1121,{dn_ou112_ad}', {'name': 'cn1121'})

    should_not_exist_in_ad = [dn_ou111_ad, dn_ou121_ad, dn_ou2_ad, dn_ou3_ad]
    for dn in should_not_exist_in_ad:
        ad_connection.verify_object(dn, None)


def test_allow_subtree_ancestors_ad(create_ou_in_ad, create_cn_in_ad, udm, ucr, ad_connector_preparation):
    """
    Test the allow-subtree-ancestors UCR-Variable
    Synchronization direction AD --> UCS

    dc=ad,dc=test
    ├── ou=ou1
    │   ├── ou=ou11
    │   │   ├── ou=ou111
    │   │   └── ou=ou112 <-- only subtree that is allowed
    │   │       └── cn=cn1121
    │   └── ou=ou12
    ├── ou=ou2
    │   └── ou=ou21
    └── ou=ou3
        └── ou=ou31

    Only OU ou112 is allowed and should be synchronized.
    """
    ldap_base = ucr['ldap/base']
    ad_ldap_base = ucr['connector/ad/ldap/base']

    # subtree that is allowed
    dn_ou112_ucs = f'ou=ou112,ou=ou11,ou=ou1,{ldap_base}'
    dn_ou112_ad = f'ou=ou112,ou=ou11,ou=ou1,{ad_ldap_base}'

    dn_ou111_ucs = f'ou=ou111,ou=ou11,ou=ou1,{ldap_base}'
    dn_ou121_ucs = f'ou=ou121,ou=ou12,ou=ou1,{ldap_base}'
    dn_ou2_ucs = f'ou=ou2,{ldap_base}'
    dn_ou3_ucs = f'ou=ou3,{ldap_base}'

    ucr.handler_set(
        [
            f'connector/ad/mapping/allowsubtree/ou112/ucs={dn_ou112_ucs}',
            f'connector/ad/mapping/allowsubtree/ou112/ad={dn_ou112_ad}',
            'connector/ad/mapping/syncmode=sync',
            'connector/ad/mapping/allow-subtree-ancestors=yes',
        ],
    )
    restart_adconnector()

    create_ou_in_ad(name='ou1', position=ad_ldap_base)
    create_ou_in_ad(name='ou2', position=ad_ldap_base)
    create_ou_in_ad(name='ou3', position=ad_ldap_base)

    create_ou_in_ad(name='ou11', position=f'ou=ou1,{ad_ldap_base}')
    create_ou_in_ad(name='ou12', position=f'ou=ou1,{ad_ldap_base}')
    create_ou_in_ad(name='ou21', position=f'ou=ou2,{ad_ldap_base}')
    create_ou_in_ad(name='ou31', position=f'ou=ou3,{ad_ldap_base}')

    create_ou_in_ad(name='ou111', position=f'ou=ou11,ou=ou1,{ad_ldap_base}')
    create_ou_in_ad(name='ou112', position=f'ou=ou11,ou=ou1,{ad_ldap_base}')
    create_ou_in_ad(name='ou121', position=f'ou=ou12,ou=ou1,{ad_ldap_base}')
    create_cn_in_ad(name='cn1121', position=f'ou=ou112,ou=ou11,ou=ou1,{ad_ldap_base}')

    wait_for_sync()
    udm.verify_ldap_object(dn_ou112_ucs, {'ou': ['ou112']})
    udm.verify_ldap_object(f'cn=cn1121,{dn_ou112_ucs}', {'cn': ['cn1121']})

    should_not_exist_in_ucs = [dn_ou111_ucs, dn_ou121_ucs, dn_ou2_ucs, dn_ou3_ucs]
    for dn in should_not_exist_in_ucs:
        udm.verify_ldap_object(dn, should_exist=False)
