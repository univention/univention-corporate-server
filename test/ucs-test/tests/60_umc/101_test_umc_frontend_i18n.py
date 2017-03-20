#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Test apache redirection rules
## exposure: dangerous
## packages: [univention-management-console-module-udm]

import pytest


class TestI18N(object):

	@pytest.mark.parametrize('path', [
		'management/modules/i18n/de/udm.json',
		'js/umc/i18n/de/app.json',
		'js/umc/i18n/en/app.json',
		# 'js_$20170106132942$/umc/i18n/en/app.json',
	])
	def test_with_content(self, path, Client):
		client = Client()
		response = client.request('GET', path)
		assert isinstance(response.data, dict) and response.data

	@pytest.mark.parametrize('path', [
		'management/modules/i18n/en/udm.json',
		'js/umc/modules/i18n/en/udm.json',
		'js/umc/i18n/de/branding.json',
		'js/umc/i18n/en/branding.json',
	])
	def test_empty(self, path, Client):
		"""Test apache redirect rule which rewrites not existing files to empty.json"""
		client = Client()
		response = client.request('GET', path)
		assert isinstance(response.data, dict) and not response.data
