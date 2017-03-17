#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Test error messages if UMC server is down
## exposure: dangerous
## packages: [univention-management-console-server]

import pytest
import json
import socket
import subprocess


class Test_ServerDown_Messages(object):

	def test_umc_webserver_down(Client, ServiceUnavailable):
		try:
			subprocess.call(['service', 'univention-management-console-web-server', 'stop'])
			with pytest.raises(ServiceUnavailable) as exc:
				Client().umc_get('modules')
			assert json.loads(exc.response.body)['message'] == 'The Univention Management Console Web Server could not be reached. Please restart it or try again later.'
		finally:
			subprocess.call(['service', 'univention-management-console-web-server', 'start'])

	def test_umc_server_down(Client, ServiceUnavailable):
		try:
			subprocess.call(['service', 'univention-management-console-server', 'stop'])
			with pytest.raises(ServiceUnavailable) as exc:
				Client().umc_get('modules')
			assert exc.message.splitlines() == [
				'The connection to the Univention Management Console Server broke up unexpectedly. ',
				'If you have root permissions on the system you can restart UMC by executing the following commands:',
				' * service univention-management-console-server restart',
				' * service univention-management-console-web-server restart',
				'Otherwise please contact an administrator or try again later.',
			]
		finally:
			subprocess.call(['service', 'univention-management-console-server', 'start'])

	def test_apache_down(Client, ConnectionError):
		try:
			subprocess.call(['service', 'apache2', 'stop'])
			with pytest.raises(ConnectionError) as exc:
				Client().umc_get('modules')
			assert isinstance(exc.reason, socket.error)
		finally:
			subprocess.call(['service', 'apache2', 'start'])
