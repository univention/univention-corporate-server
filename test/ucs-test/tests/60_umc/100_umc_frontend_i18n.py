#!/usr/share/ucs-test/runner python
## desc: Test apache redirection rules
## exposure: dangerous
## packages: [univention-management-console-module-udm]

import sys
import json
import pytest
import socket
import subprocess


@pytest.fixture
def request(path, Client):
	client = Client()
	return client.request('GET', path)


class TestI18N(object):

	@pytest.mark.parametrize('path', [
		'management/modules/i18n/de/udm.json',
		'management/js/umc/modules/i18n/de/udm.json',
		'js/umc/i18n/de/app.json',
		'js/umc/i18n/en/branding.json',
		'js/umc/i18n/en/app.json',
		'js_$20170106132942$/umc/i18n/en/app.json',
	])
	def test_with_content(self, path, request):
		response = request(path)
		assert isinstance(response.data, dict) and response.data

	@pytest.mark.parametrize('path', [
		'management/modules/i18n/en/udm.json',
		'management/js/umc/modules/i18n/en/udm.json',
		'js/umc/i18n/de/branding.json',
	])
	def test_empty(self, path, request):
		"""Test apache redirect rule which rewrites not existing files to empty.json"""
		response = request(path)
		assert isinstance(response.data, dict) and not response.data


class TestSecurityHeaders(object):

	@pytest.mark.parametrize('path', [
		'login/blank.html',
		'login/login.html',
	])
	def test_login_site(self, path, request):
		response = request(path)
		assert response.get_header("X-Frame-Options") == "SAMEORIGIN"
		assert response.get_header("Content-Security-Policy") == "default-src 'self' 'unsafe-inline';"

		assert response.get_header("X-Permitted-Cross-Domain-Policies") == "master-only"
		assert response.get_header("X-XSS-Protection") == "1; mode=block"
		assert response.get_header("X-Content-Type-Options") == "nosniff"

	@pytest.mark.parametrize('path', [
		'/',
		'/management/',
	])
	def test_univention(self, path, request):
		response = request(path)
		assert response.get_header("X-Permitted-Cross-Domain-Policies") == "master-only"
		assert response.get_header("X-XSS-Protection") == "1; mode=block"
		assert response.get_header("X-Content-Type-Options") == "nosniff"
		assert response.get_header("X-Frame-Options") == "DENY"


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


if __name__ == '__main__':
	sys.exit(pytest.main([__file__]))
