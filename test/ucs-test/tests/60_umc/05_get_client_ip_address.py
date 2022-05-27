#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Check if UMC is able to return correct IP address
## exposure: dangerous
## packages: [univention-management-console-web-server]

from six.moves.http_client import HTTPConnection
import pytest

from univention.testing import network, utils
from univention.testing.umc import Client


class HTTPConnectionClient(Client):
	# workaround ssl.CertificateError: hostname '1.2.3.4' doesn't match either of 'master091.$domainname', 'master091'
	ConnectionType = HTTPConnection


@pytest.mark.exposure('dangerous')
@pytest.mark.parametrize('addr2', ['4.3.2.1', '1.1.1.1', '2.2.2.2'])
def test_get_client_ip_address(addr2):
	"""Check if UMC is able to return correct IP address"""
	account = utils.UCSTestDomainAdminCredentials()
	print('*** Check with remote addresses:', addr2)

	with network.NetworkRedirector() as nethelper:
		nethelper.add_loop('1.2.3.4', addr2)

		client = HTTPConnectionClient('1.2.3.4', account.username, account.bindpw)
		result = client.umc_get('ipaddress').data
		assert addr2 in result, 'UMC webserver is unable to determine correct UMCP client address (expected=%r result=%r)' % (addr2, result)

		nethelper.remove_loop('1.2.3.4', addr2)


@pytest.mark.exposure('dangerous')
def test_get_client_ip_address_localhost():
	"""Check if UMC is able to return correct IP address"""
	print('*** Check with localhost')
	account = utils.UCSTestDomainAdminCredentials()

	client = HTTPConnectionClient('localhost', account.username, account.bindpw)
	result = client.umc_get('ipaddress').data
	assert not result, 'Response is expected to be empty'
