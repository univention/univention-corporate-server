import pytest


class TestI18N(object):

	@pytest.mark.parametrize('path', [
		'management/modules/i18n/de/udm.json',
		'management/js/umc/modules/i18n/de/udm.json',
		'js/umc/i18n/de/app.json',
		'js/umc/i18n/en/branding.json',
		'js/umc/i18n/en/app.json',
		'js_$20170106132942$/umc/i18n/en/app.json',
	])
	def test_with_content(self, path, umc_get_request):
		response = umc_get_request(path)
		assert isinstance(response.data, dict) and response.data

	@pytest.mark.parametrize('path', [
		'management/modules/i18n/en/udm.json',
		'management/js/umc/modules/i18n/en/udm.json',
		'js/umc/i18n/de/branding.json',
	])
	def test_empty(self, path, umc_get_request):
		"""Test apache redirect rule which rewrites not existing files to empty.json"""
		response = umc_get_request(path)
		assert isinstance(response.data, dict) and not response.data
