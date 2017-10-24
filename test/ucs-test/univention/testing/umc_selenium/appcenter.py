#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Selenium Tests
#
# Copyright 2017 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

from univention.admin import localization

translator = localization.translation('ucs-test-framework')
_ = translator.translate


class AppCenter(object):

	def __init__(self, selenium):
		self.selenium = selenium

	def install_app(app):
		s.open_module(_('App Center'))
		s.wait_until_all_standby_animations_disappeared()
		s.click_text(app)
		s.wait_for_text(_('Details'))
		s.wait_for_text(_('More information'))
		s.click_text(_('Install'))
		s.click_text(_('Next'))
		s.click_text(_('Continue'))
		s.click_text(_('Install'))
		s.wait_until_all_standby_animations_disappeared()
		s.wait_for_text(_('Please confirm to install the application'))


if __name__ == '__main__':
	import univention.testing.umc_selenium
	s = univention.testing.umc_selenium.UMCSeleniumTest()
	s.__enter__()
	s.do_login()
	a = AppCenter(s)
	a.install_app('Dudle')
