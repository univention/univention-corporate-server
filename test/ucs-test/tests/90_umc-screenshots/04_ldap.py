#!/usr/share/ucs-test/runner python
## desc: UMC LDAP screenshots
## roles-not: [basesystem]
## exposure: dangerous

from lib.screen_shooter import BaseScreenShooter
from univention.admin import localization

translator = localization.translation('univention-ucs-test_umc-screenshots')
_ = translator.translate


class ScreenShooter(BaseScreenShooter):
	def take_screenshots(self):
		self.selenium.open_module(_("LDAP directory"))
		self.selenium.wait_for_text("Virtual Machine Manager")
		self.selenium.click_tree_entry("groups")
		self.selenium.save_screenshot("umc-ldap")

		# The screenshot with the right-click-menu on the ldap-tree won't be
		# made here, since it is undoable with selenium or JavaScript. Ask
		# ulmer@univention.de if you don't want to believe.

if __name__ == '__main__':
	with ScreenShooter(translator) as screen_shooter:
		screen_shooter.take_screenshots()
