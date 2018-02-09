#!/usr/share/ucs-test/runner python
## desc: UMC portal screenshot
## roles-not: [basesystem]
## exposure: dangerous

from lib.screen_shooter import BaseScreenShooter
from univention.admin import localization

translator = localization.translation('univention-ucs-test_umc-screenshots')
_ = translator.translate


class ScreenShooter(BaseScreenShooter):
	def take_screenshots(self):
		self.selenium.driver.get(self.selenium.base_url + 'univention/portal/?lang=%s' % (self.selenium.language,))
		self.selenium.wait_for_text(_("Administration"))
		self.selenium.save_screenshot("portal")


if __name__ == '__main__':
	with ScreenShooter(translator) as screen_shooter:
		screen_shooter.take_screenshots()
