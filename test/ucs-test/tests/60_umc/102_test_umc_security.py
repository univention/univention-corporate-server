#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Test security related HTTP headers are set
## exposure: dangerous
## packages: [univention-management-console-server]

import pytest
from collections import defaultdict


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
		assert response.get_header("X-Frame-Options") is None  # changed from: == "SAMEORIGIN"
		assert response.get_header("Content-Security-Policy") == "default-src 'self' 'unsafe-inline' 'unsafe-eval'  https://www.piwik.univention.de/ ; frame-ancestors 'self';"

		assert response.get_header("X-Permitted-Cross-Domain-Policies") == "master-only"
		assert response.get_header("X-XSS-Protection") == "1; mode=block"
		assert response.get_header("X-Content-Type-Options") == "nosniff"

	@pytest.mark.parametrize('path', [
		'/languages.json',
		'/portal/',
		'/management/',
	])
	def test_univention(self, path, ucr, Client):
		client = Client()
		response = client.request('GET', path)
		assert response.get_header("X-Permitted-Cross-Domain-Policies") == "master-only"
		assert response.get_header("X-XSS-Protection") == "1; mode=block"
		assert response.get_header("X-Content-Type-Options") == "nosniff"
		assert response.get_header("X-Frame-Options") is None  # changed from: == "DENY"
		if path == '/languages.json':
			assert response.get_header("Content-Security-Policy") == "frame-ancestors 'none';"
		else:
			expected = "frame-ancestors 'self' https://%(ucs/server/sso/fqdn)s/ http://%(ucs/server/sso/fqdn)s/;" % defaultdict(lambda: '', ucr)
			assert expected in response.get_header("Content-Security-Policy")
