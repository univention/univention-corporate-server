#!/usr/share/ucs-test/runner python
## desc: UMC login screenshots
## roles-not: [basesystem]
## exposure: dangerous

from lib.screen_shooter import BaseScreenShooter
import logging
import univention.testing.udm as udm_test
import univention.testing.selenium as selenium_test


class ScreenShooter(BaseScreenShooter):
	def __init__(self):
		self.args = self.parse_args()

		logging.basicConfig(level=logging.INFO)

		self.udm = udm_test.UCSTestUDM()
		self.selenium = selenium_test.UMCSeleniumTest(login=False, language=self.args.language)

	def take_screenshots(self):
		self.selenium.set_viewport_size(800, 600)
		self.selenium.save_screenshot("umc-login")
		self.selenium.save_screenshot("umc-login_cropped", xpath='//*[@id="umcLoginDialog"]')


if __name__ == '__main__':
	with ScreenShooter() as screen_shooter:
		screen_shooter.take_screenshots()
