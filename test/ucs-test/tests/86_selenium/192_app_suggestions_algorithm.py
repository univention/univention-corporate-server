#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: |
##  Test suggestion algorithm
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

from univention.admin import localization
from univention.testing import selenium
from univention.testing.selenium.appcenter import AppCenter
from univention.appcenter.app_cache import AppCache

translator = localization.translation('ucs-test-selenium')
_ = translator.translate


class UMCTester(object):
	def test_umc(self):
		self.selenium.do_login()
		self.appcenter.open(do_reload=False)
		self.selenium.wait_for_text('Available')

		app_cache = AppCache.build()
		apps = app_cache.get_all_apps()
		installed_apps = [
			{'id': apps[0].id},
			{'id': apps[1].id},
		]
		suggestions = [{
			'condition': [installed_apps[0]['id'], 'xxx'],
			'candidates': [{
				'id': apps[2].id,
				'mayNotBeInstalled': []
			}]
		}, {
			'condition': [installed_apps[0]['id']],
			'candidates': [{
				'id': apps[3].id,
				'mayNotBeInstalled': [installed_apps[1]['id']]
			}]
		}, {
			'condition': [installed_apps[0]['id'], installed_apps[1]['id']],
			'candidates': [{
				'id': apps[4].id,
				'mayNotBeInstalled': ['xxx']
			}, {
				'id': apps[5].id,
				'mayNotBeInstalled': ['xxx']
			}, {
				'id': apps[6].id,
				'mayNotBeInstalled': [installed_apps[0]['id']]
			}]
		}]

		r = self.selenium.driver.execute_script('''
			var w = dijit.byId('umc_modules_appcenter_AppCenterPage_0')
			return w._getSuggestedAppIds(arguments[0], arguments[1]);
		''', suggestions, installed_apps)

		assert apps[4].id in r, "Expected '%s' to be in suggested ids %s" % (apps[6].id, r,)
		assert apps[5].id in r, "Expected '%s' to be in suggested ids %s" % (apps[6].id, r,)

if __name__ == '__main__':
	with selenium.UMCSeleniumTest() as s:
		umc_tester = UMCTester()
		umc_tester.selenium = s
		umc_tester.appcenter = AppCenter(umc_tester.selenium)

		umc_tester.test_umc()
