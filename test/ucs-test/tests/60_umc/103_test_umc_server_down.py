#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test error messages if UMC server is down
## exposure: dangerous
## packages: [univention-management-console-server]

import socket
import subprocess

import pytest

from univention.lib.umc import ConnectionError, ServiceUnavailable


class Test_ServerDown_Messages:

    def test_umc_server_down(self, Client):
        try:
            subprocess.call(['systemctl', 'stop', 'univention-management-console-server'])
            with pytest.raises(ServiceUnavailable) as exc:
                Client().umc_get('modules')
            assert exc.value.response.reason == 'UMC Service Unavailable'
            assert exc.value.message == 'The Univention Management Console Server could not be reached. Please restart univention-management-console-server or try again later.'
        finally:
            subprocess.call(['systemctl', 'start', 'univention-management-console-server'])

    def test_apache_down(self, Client):
        try:
            subprocess.call(['systemctl', 'stop', 'apache2'])
            with pytest.raises(ConnectionError) as exc:
                Client().umc_get('modules')
            assert isinstance(exc.value.reason, socket.error)
        finally:
            subprocess.call(['systemctl', 'start', 'apache2'])
