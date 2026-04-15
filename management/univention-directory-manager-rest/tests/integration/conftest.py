# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2023-2025 Univention GmbH
"""
Module providing command-line argument parser
and common fixtures for use in integration tests.
"""

import random
from typing import Any, Callable, Dict, List, Tuple
import urllib.parse
from univention.admin.rest.client import UDM

import pytest
import requests


def pytest_addoption(parser: pytest.Parser):
    """
    Allow customizing global options of the tests,
    e.g. where to find the UDM REST container and how to connect.
    """
    parser.addoption(
        "--udm-rest-url",
        action="store",
        default="http://localhost:9979/udm/",
        help="UDM REST API base url to run tests against.",
    )
    parser.addoption(
        "--ldap-base-dn",
        action="store",
        default="dc=univention-organization,dc=intranet",
        help="Base DN of the LDAP directory.",
    )
    parser.addoption(
        "--username",
        action="store",
        default="cn=admin",
        help="Username to authenticate with the UDM REST API.",
    )
    parser.addoption(
        "--password",
        action="store",
        default="univention",
        help="Password to authenticate with the UDM REST API.",
    )


@pytest.fixture(scope="session")
def base_dn(pytestconfig):
    """Base DN of the LDAP server."""
    return pytestconfig.getoption("--ldap-base-dn")


@pytest.fixture(scope="session")
def udm_url(pytestconfig):
    """Base URL of the UDM REST API."""
    return pytestconfig.getoption("--udm-rest-url")


@pytest.fixture(scope="session")
def session(pytestconfig):
    """Prepare requests to UDM REST API."""
    session = requests.Session()
    session.auth = (
        pytestconfig.getoption("--username"),
        pytestconfig.getoption("--password"),
    )
    session.headers["accept"] = "application/json"
    session.headers["content-type"] = "application/json"
    yield session


@pytest.fixture(scope="session")
def main_domain(session: requests.Session, udm_url: str) -> str:
    """Get the FQDN of a provisioned mail/domain or empty string if none exists."""
    url = urllib.parse.urljoin(
        udm_url,
        f"mail/domain/?filter={urllib.parse.quote('(objectClass=*)')}")

    conn = session.get(url)

    assert conn.status_code == requests.codes.ok, repr(conn.__dict__)
    result = conn.json()
    try:
        domains = [
            o["properties"]["name"] for o in result["_embedded"]["udm:object"]
        ]
        return domains[0]
    except KeyError:
        return ""


@pytest.fixture(scope="session")
def delete_obj_after_test(session: requests.Session,
                          udm_url: str) -> Callable[[str, str], None]:
    udm_objects: List[Tuple[str, str]] = []

    def _delete_obj_after_test(udm_module: str, dn: str):
        udm_objects.append((udm_module, dn))

    yield _delete_obj_after_test

    for _udm_mod, _dn in udm_objects:
        url = urllib.parse.urljoin(udm_url, f"{_udm_mod}/{_dn}")
        conn = session.delete(url)
        if conn.status_code == requests.codes.no_content:
            print(f"Deleted {_udm_mod!r} object at {_dn!r}")
        else:
            print(
                f"Error deleting {_udm_mod!r} object at {_dn!r}: {conn.status_code} {conn.reason}",
            )


@pytest.fixture(scope="session")
def random_user_properties(main_domain) -> Callable[[], Dict[str, Any]]:

    def _random_user_properties() -> Dict[str, Any]:
        postfix = "{:08X}".format(random.getrandbits(2**5)).lower()
        return {
            "username":
            f"username-{postfix}",
            "firstname":
            f"firstname-{postfix}",
            "lastname":
            f"lastname-{postfix}",
            "mailPrimaryAddress":
            f"email-{postfix}@{main_domain}" if main_domain else None,
            "password":
            "univention",
        }

    return _random_user_properties


@pytest.fixture(scope="session")
def create_user(
    session: requests.Session,
    udm_url: str,
    base_dn: str,
    delete_obj_after_test,
    random_user_properties,
) -> Callable[[], Dict[str, Any]]:
    url_users = urllib.parse.urljoin(udm_url, "users/user/")

    def _create_user(with_univentionObjectIdentifier: bool = False) -> Dict[str, Any]:
        properties = random_user_properties()
        delete_obj_after_test(
            "users/user", f"uid={properties['username']},cn=users,{base_dn}")
        conn = session.post(url_users, json={"properties": properties})
        assert conn.status_code == requests.codes.created, repr(conn.__dict__)
        if with_univentionObjectIdentifier:
            user_uuid = conn.json().get('uuid')
            properties['uuid'] = user_uuid
        return properties

    return _create_user


@pytest.fixture(scope="session")
def udm_rest_api_client(udm_url: str, pytestconfig):
    username = pytestconfig.getoption("--username")
    password = pytestconfig.getoption("--password")
    udm = UDM.http(udm_url, username, password)
    assert udm.get_ldap_base()

    return udm
