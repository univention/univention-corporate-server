#!/usr/share/ucs-test/runner pytest-3 -vv
## desc: Check if UMC is able to return correct IP address
## exposure: dangerous
## packages: [univention-management-console-server]

from http.client import HTTPConnection
from typing import Iterator

import pytest

from univention.testing.network import NetworkRedirector
from univention.testing.umc import Client
from univention.testing.utils import UCSTestDomainAdminCredentials


class _Client(Client):
    # workaround ssl.CertificateError: hostname '1.2.3.4' doesn't match either of 'master091.$domainname', 'master091'
    ConnectionType = HTTPConnection


def get_ip_address(host: str, account: UCSTestDomainAdminCredentials) -> str:
    client = _Client(host, account.username, account.bindpw)
    return client.umc_get('ipaddress').data


@pytest.fixture()
def nethelper() -> Iterator[NetworkRedirector]:
    with NetworkRedirector() as nr:
        yield nr


@pytest.mark.parametrize("addr", ['4.3.2.1', '1.1.1.1', '2.2.2.2'])
def test_remote(addr: str, account: UCSTestDomainAdminCredentials, nethelper: NetworkRedirector) -> None:
    nethelper.add_loop('1.2.3.4', addr)
    assert addr in get_ip_address('1.2.3.4', account)


def test_localhost(account: UCSTestDomainAdminCredentials) -> None:
    assert not get_ip_address('localhost', account)
