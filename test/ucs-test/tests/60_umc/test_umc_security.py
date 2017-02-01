import pytest


class TestSecurityHeaders(object):

	@pytest.mark.parametrize('path', [
		'login/blank.html',
		'login/login.html',
	])
	def test_login_site(self, path, umc_get_request):
		response = umc_get_request(path)
		assert response.get_header("X-Frame-Options") == "SAMEORIGIN"
		assert response.get_header("Content-Security-Policy") == "default-src 'self' 'unsafe-inline';"

		assert response.get_header("X-Permitted-Cross-Domain-Policies") == "master-only"
		assert response.get_header("X-XSS-Protection") == "1; mode=block"
		assert response.get_header("X-Content-Type-Options") == "nosniff"

	@pytest.mark.parametrize('path', [
		'/',
		'/management/',
	])
	def test_univention(self, path, umc_get_request):
		response = umc_get_request(path)
		assert response.get_header("X-Permitted-Cross-Domain-Policies") == "master-only"
		assert response.get_header("X-XSS-Protection") == "1; mode=block"
		assert response.get_header("X-Content-Type-Options") == "nosniff"
		assert response.get_header("X-Frame-Options") == "DENY"
