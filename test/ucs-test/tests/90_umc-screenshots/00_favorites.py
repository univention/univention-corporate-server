#!/usr/share/ucs-test/runner python
## desc: UMC favorites screenshot
## roles-not: [basesystem]
## exposure: dangerous

from lib.screen_shooter import BaseScreenShooter
from univention.admin import localization

translator = localization.translation('univention-ucs-test_umc-screenshots')
_ = translator.translate


class ScreenShooter(BaseScreenShooter):
	def take_screenshots(self):
		self.selenium.click_button(_('Favorites'))
		self.selenium.save_screenshot("umc-favorites")


if __name__ == '__main__':
	with ScreenShooter(translator) as screen_shooter:
		screen_shooter.take_screenshots()
