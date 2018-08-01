#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Test security related HTTP headers are set
## exposure: dangerous
## packages: [univention-management-console-server]

import pytest


class TestSecurityHeaders(object):

	@pytest.mark.parametrize('path', [
		'login/',
		'login/index.html',
		'login/blank.html',
		'login/login.html',
	])
	def test_login_site(self, path, Client):
		client = Client()
		response = client.request('GET', path)
		assert response.get_header("X-Frame-Options") == "SAMEORIGIN"
		assert response.get_header("Content-Security-Policy") == "default-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.piwik.univention.de/ ;"

		assert response.get_header("X-Permitted-Cross-Domain-Policies") == "master-only"
		assert response.get_header("X-XSS-Protection") == "1; mode=block"
		assert response.get_header("X-Content-Type-Options") == "nosniff"

	@pytest.mark.parametrize('path', [
		'/languages.json',
		'/portal/',
		'/management/',
	])
	def test_univention(self, path, Client):
		client = Client()
		response = client.request('GET', path)
		assert response.get_header("X-Permitted-Cross-Domain-Policies") == "master-only"
		assert response.get_header("X-XSS-Protection") == "1; mode=block"
		assert response.get_header("X-Content-Type-Options") == "nosniff"
		assert response.get_header("X-Frame-Options") == "DENY"
