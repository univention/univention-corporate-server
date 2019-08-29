#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: |
##  Test that suggestions category is shown
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import shutil

from univention.admin import localization
from univention.testing import selenium
from univention.testing.selenium.appcenter import AppCenter
from univention.appcenter.app_cache import AppCenterCache, default_server

translator = localization.translation('ucs-test-selenium')
_ = translator.translate


class UMCTester(object):
	def setup(self):
		cache = AppCenterCache.build(server=default_server())
		self.json_file = cache.get_cache_file('.suggestions.json')
		self.json_file_bak = cache.get_cache_file('.suggestions.bak.json')
		shutil.copyfile(self.json_file, self.json_file_bak)
		with open(self.json_file, 'w') as fd:
			fd.write('''
{
	"v1": [{
		"condition": [],
		"candidates": [{
			"id": "owncloud",
			"mayNotBeInstalled": []
		}]
	}]
}
''')

	def cleanup(self):
		try:
			shutil.move(self.json_file_bak, self.json_file)
		except (OSError, IOError):
			pass

	def test_umc(self):
		self.selenium.do_login()
		self.appcenter.open(do_reload=False)
		self.selenium.wait_for_text('Suggestions based on installed apps')
		self.selenium.save_screenshot(name=__file__)


if __name__ == '__main__':
	with selenium.UMCSeleniumTest() as s:
		umc_tester = UMCTester()
		umc_tester.selenium = s
		umc_tester.appcenter = AppCenter(umc_tester.selenium)

		try:
			umc_tester.setup()
			umc_tester.test_umc()
		finally:
			umc_tester.cleanup()
