#!/usr/share/ucs-test/runner pytest-3 -s
## desc: "Test the UCS<->AD sync with position mapping"
## exposure: dangerous
## packages:
##  - univention-ad-connector
## tags:
##  - skip_admember

import pytest

from univention.config_registry import handler_set as ucr_set
from univention.testing import ucr as testing_ucr
from univention.testing.strings import random_string

from adconnector import ADConnection, _Connector, restart_adconnector, wait_for_sync


AD = ADConnection()
connector = _Connector()
name1 = f"{random_string()}"
ucs_name1 = f"plus1{name1}"
ad_name1 = f"\\+1{name1}"
name2 = f"{random_string()}"
ucs_name2 = f"plus2{name2}"
ad_name2 = f"\\+2{name2}"
mapping = f'''
import univention.connector
from univention.config_registry import ucr

POSITIONMAPPED_TYPES = ("container", "ou", "group", "user", "windowscomputer")


def mapping_hook(ad_mapping):
    with ucr as view:
        ad_base = view.get("connector/ad/ldap/base", "")
        ldap_base = view.get("ldap/base", "")
        if ad_base and ldap_base:
            custom_position_mapping = [
                ("ou={ucs_name1}," + ldap_base, "ou={ad_name1}," + ad_base),
                ("ou={ucs_name2}," + ldap_base, "ou={ad_name2}," + ad_base),
                ("cn={ucs_name1}," + ldap_base, "cn={ad_name1}," + ad_base),
                ("cn={ucs_name2}," + ldap_base, "cn={ad_name2}," + ad_base),
            ]
            for obj_type in POSITIONMAPPED_TYPES:
                if ad_mapping.get(obj_type) is not None:
                    ad_mapping[obj_type].position_mapping = custom_position_mapping
    return ad_mapping
'''
mapping_file = "/etc/univention/connector/ad/localmapping.py"


@pytest.fixture(scope="session", autouse=True)
def create_localmapping():
    with open(mapping_file, "w") as f:
        f.write(mapping)

    restart_adconnector()


@pytest.mark.parametrize("mode", ["write", "sync"])
def test_udm_to_ad_position_mapping_cn(udm, ucr, mode):
    """
    Create CN in UDM → expect mapped CN in AD
    Rename CN in UDM → expect rename in AD
    """
    with testing_ucr.UCSTestConfigRegistry() as ucr:
        ucr_set(
            [
                f'connector/ad/mapping/syncmode={mode}',
            ],
        )
        restart_adconnector()

        ad_base = ucr.get("connector/ad/ldap/base")
        ucs_base = ucr.get("ldap/base")
        # Create CN in mapped position
        udm.create_object("container/cn", name=ucs_name1)

        wait_for_sync()
        AD.verify_object(f"cn={ad_name1},{ad_base}", {'cn': f"+1{name1}"})
        wait_for_sync()

        # Expect UDM CN "plus1"
        udm.verify_ldap_object(f"cn={ucs_name1},{ucs_base}", retry_count=3, delay=1)

        # Rename in UDM
        udm.modify_object("container/cn", dn=f"cn={ucs_name1},{ucs_base}", name="blablubb")

        wait_for_sync()

        AD.verify_object(f"cn=blablubb,{ad_base}", {'cn': "blablubb"})


@pytest.mark.parametrize("mode", ["write", "sync"])
def test_udm_to_ad_position_mapping_ou(udm, ucr, mode):
    """
    Create OU in UDM → expect mapped OU in AD
    Rename OU in UDM → expect rename in AD
    """
    with testing_ucr.UCSTestConfigRegistry() as ucr:
        ucr_set(
            [
                f'connector/ad/mapping/syncmode={mode}',
            ],
        )
        restart_adconnector()

        ad_base = ucr.get("connector/ad/ldap/base")
        ucs_base = ucr.get("ldap/base")
        # Create OU in mapped position
        udm.create_object("container/ou", name=ucs_name1)

        wait_for_sync()
        AD.verify_object(f"ou={ad_name1},{ad_base}", {'name': f"+1{name1}"})
        wait_for_sync()

        # Expect UDM OU "plus1"
        udm.verify_ldap_object(f"ou={ucs_name1},{ucs_base}", retry_count=3, delay=1)

        # Rename in UDM
        udm.modify_object("container/ou", dn=f"ou={ucs_name1},{ucs_base}", name="blablubb")

        wait_for_sync()

        AD.verify_object(f"ou=blablubb,{ad_base}", {'name': "blablubb"})


@pytest.mark.parametrize("mode", ["sync", "read"])
def test_ad_to_udm_position_mapping_cn(udm, ucr, mode):
    """
    Create CN in AD → expect mapped CN in UDM
    Rename CN in AD → expect rename in UDM
    """
    with testing_ucr.UCSTestConfigRegistry() as ucr:
        ucr_set(
            [
                f'connector/ad/mapping/syncmode={mode}',
            ],
        )
        restart_adconnector()
        ad_base = ucr.get("connector/ad/ldap/base")
        ucs_base = ucr.get("ldap/base")
        # Create CN in AD
        connector._ad.container_create(f"+2{name2}")
        AD.verify_object(f"cn={ad_name2},{ad_base}", {'cn': f"+2{name2}"})

        wait_for_sync()

        # Expect UDM CN "plus2"
        udm.verify_ldap_object(f"cn={ucs_name2},{ucs_base}", retry_count=3, delay=1)

        # Rename in AD
        connector.rename(f"cn={ad_name2},{ad_base}", rdn="cn=renamed")
        connector.delete_object(f"cn=renamed,{ad_base}", f"cn=renamed,{ucs_base}")

        wait_for_sync()
    restart_adconnector()


@pytest.mark.parametrize("mode", ["sync", "read"])
def test_ad_to_udm_position_mapping_ou(udm, ucr, mode):
    """
    Create OU in AD → expect mapped OU in UDM
    Rename OU in AD → expect rename in UDM
    """
    with testing_ucr.UCSTestConfigRegistry() as ucr:
        ucr_set(
            [
                f'connector/ad/mapping/syncmode={mode}',
            ],
        )
        restart_adconnector()
        ad_base = ucr.get("connector/ad/ldap/base")
        ucs_base = ucr.get("ldap/base")
        # Create OU in AD
        connector.create_ou(f"+2{name2}")
        AD.verify_object(f"ou={ad_name2},{ad_base}", {'name': f"+2{name2}"})

        wait_for_sync()

        # Expect UDM OU "plus2"
        udm.verify_ldap_object(f"ou={ucs_name2},{ucs_base}", retry_count=3, delay=1)

        # Rename in AD
        connector.rename(f"ou={ad_name2},{ad_base}", rdn="ou=renamed")

        wait_for_sync()

        udm.verify_ldap_object(f"ou=renamed,{ucs_base}", retry_count=3, delay=1)
        connector.delete_object(f"ou=renamed,{ad_base}", f"ou=renamed,{ucs_base}")
        wait_for_sync()
    restart_adconnector()
