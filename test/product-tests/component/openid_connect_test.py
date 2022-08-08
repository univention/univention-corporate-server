#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2022 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.
#

import os
import os.path
import importlib
import time
import sys
import random
import string


# Good to know when further developing these tests
# ================================================
#
# https://www.browserstack.com/guide/wait-commands-in-selenium-webdriver
#     chrome.driver.implicitly_wait(10)
# an implicit wait would be beneficial, because it would simplify our code
# by avoiding most explicit waits. But at the time of writing this does not
# work. The command above would not set a value to wait for implicitly (as
# documented) and instead wait for 10 seconds.
#
# How to locate elements with selenium
# ------------------------------------
#
# https://selenium-python.readthedocs.io/locating-elements.html

from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys


# helper functions -------------------------------------------------------------

def wait_for_page_fully_loaded(driver):
	"""
	wait 10 seconds at max. until javascript thinks that the page is fully
	loaded. That does not include downloads performed by javascript when
	the page is laoded (AJAX)
	"""
	WebDriverWait(driver, 10).until(
		lambda driver: driver.execute_script(
			'return document.readyState') == 'complete')


def highlight_this_part(chrome, name):
	"""
	helper function to mark an important part of any selenium test. It saves
	a screenshot and makes sure, that this screenshot is also visible in the
	recoreded video, because it comes handy when debugging
	"""
	chrome.save_screenshot(name)
	time.sleep(1)


def owncloud_login(chrome, user):
	# sanity check first, e.g. wrong tab or redirect not working...
	assert chrome.driver.current_url.endswith("owncloud/login")
	# enter usual user data...
	chrome.enter_input("user", user.properties["username"])
	chrome.enter_input("password", "univention")
	time.sleep(1)  # this sleep improves visibility in the screen recording
	# click the 'log in' button...
	chrome.click_element("#submit")
	wait_for_page_fully_loaded(chrome.driver)


def owncloud_logout(chrome):
	# sanity check: somewhere in owncloud, because we could be in the wrong tab
	assert chrome.driver.current_url.find("/owncloud/")
	# the username in owncloud is clickable and opens a menu
	element = WebDriverWait(chrome.driver, 10).until(
		EC.presence_of_element_located((By.ID, "expandDisplayName")))
	element.click()
	time.sleep(1)  # this sleep improves visibility in the screen recording
	# within the open menu there is a logout link. Click it...
	chrome.driver.find_element_by_id('logout').click()
	wait_for_page_fully_loaded(chrome.driver)


def owncloud_close_welcome_screen(chrome):
	""" with the very first login the user will be shown a quick tutorial """
	try:
		# the wizard could have been disappeared in an upcoming owncloud
		# version But we do not want to test owncloud and only get rid of the
		# dialog.  So we try to get rid of it, but it does not break our test
		# if it is not there.
		chrome.driver.find_element_by_id("closeWizard").click()
		time.sleep(1)
	except NoSuchElementException:
		pass  # since we are not testing the owncloud app it does not matter


def portal_goto(chrome):
	"""
	The goto_portal function from `apptest.py` sometimes fails, because it
	relies on a hard coded loading time of 2 seconds. It also continiously
	tests the language switch, which takes multiple seconds and is here
	unnecessary. This function does one thing and does it as quick as possible
	"""

	# how this version works:
	# visit the portal in a predictable language, because we need that to
	# locate elements via xpaths
	chrome.driver.get(chrome.base_url + '/univention/portal/?lang=en-US')
	wait_for_page_fully_loaded(chrome.driver)
	# the content area should now be visible, but the tiles within may still be
	# missing. However we can already click the login button.
	WebDriverWait(chrome.driver, 10).until(
		EC.presence_of_element_located((By.ID, "content")))


def portal_wait_for_tiles(chrome):
	# locate the block element which includes all tiles. This appears in a
	# after the page has been loaded, so that we have to wait for it. We
	# wait 10 seconds at max...
	WebDriverWait(chrome.driver, 10).until(
		EC.presence_of_element_located((By.ID, "dgrid_0")))


def portal_login_click(chrome):
	# sanity check...
	assert chrome.driver.current_url.find("/univention/portal/")
	# click the login button and wait for the login page...
	chrome.driver.find_element_by_id('umcLoginButton_label').click()
	wait_for_page_fully_loaded(chrome.driver)


def portal_login(chrome, username, password):
	# we assume to be on the login page now and we check that...
	assert chrome.driver.current_url.find("/univention/login/")

	# wait until the login dialog is fully loaded
	WebDriverWait(chrome.driver, 10).until(
		EC.presence_of_element_located((By.ID, "umcLoginDialog")))

	# we enter username and password and log in. Because logging in takes a
	# while we can see the values in the produced video. No sleep required
	# here...
	chrome.driver.find_element_by_id('umcLoginUsername').send_keys(username)
	chrome.driver.find_element_by_id('umcLoginPassword').send_keys(password)
	chrome.driver.find_element_by_id('umcLoginSubmit').click()
	wait_for_page_fully_loaded(chrome.driver)


def owncloud_click_single_signon(chrome):
	# the single sign own button is a little hard to locate, because it has no
	# dedicated id. We use the xpath syntax to click the correct link within
	# the last known element with an `id`
	chrome.driver.find_element_by_xpath(
		'//*[@id="alternative-logins"]/fieldset/ul/li/a').click()
	wait_for_page_fully_loaded(chrome.driver)


def create_random_user(users):
	# if we ever want to change the pattern of the random username, we can do
	# that here in one place...
	username = 'random-'
	username += ''.join(random.choice(string.ascii_uppercase) for _ in range(4))
	return users(username, {
		"owncloudEnabled": True,
		"mailPrimaryAddress": username + "@autotest.local"})


# tests ------------------------------------------------------------------------

def test_owncloud_with_portal_login(chrome, users):
	"""
	what this test does:
	- creates a random user
	- visits the portal page
	- clicks on `login` on the portal page
	- loggs in with username and password
	- that redirects the user automatically back to the portal page
	- there the user clicks on the owncloud tile
	- the owncloud login dialog appears
	- the user chooses the single sign on method
	- by doing so the user gets logged into owncloud
	- the first-run wizard dialog is clicked away
	- the user loggs out of owncloud and is redirected back to the portal
	- a final check ensures, that the user is still logged in
	"""

	test_name = "test_owncloud_with_portal_login"
	user = create_random_user(users)
	with chrome.capture(test_name):
		portal_goto(chrome)
		portal_login_click(chrome)
		portal_login(chrome, user.properties["username"], "univention")

		# make sure, that the app tiles are already loaded, then click...
		portal_wait_for_tiles(chrome)
		chrome.click_portal_tile(u"ownCloud")
		wait_for_page_fully_loaded(chrome.driver)
		highlight_this_part(chrome, test_name + "-before_click_sso_button")

		owncloud_click_single_signon(chrome)
		owncloud_close_welcome_screen(chrome)
		owncloud_logout(chrome)

		assert "https://backup.autotest.local/univention/portal/" \
			== chrome.driver.current_url

		# assert "LOGOUT" \ # it is logout for some reason :/
		assert "LOGOUT" \
			== chrome.driver.find_element_by_id('umcLoginButton_label').text


def test_owncloud_with_openid_login(chrome, users):
	"""
	what this test does:
	- creates a random user
	- visits the ucs portal
	- clicks the owncloud tile
	- gets to the owncloud log in screen and clicks single-sign-on
	- is automatically redirected back to the portal log in page
	- loggs in there and is redirected back into owncloud (and logged in)
	- dismisses the welcome dialog that appears after the first log in.
	- uses the menu to log out again
	- a last check ensures, that this brings the user back to the portal page
	"""

	test_name = "test_owncloud_with_openid_login"
	user = create_random_user(users)
	with chrome.capture(test_name):
		portal_goto(chrome)
		# make sure, that the app tiles are already loaded, then click...
		portal_wait_for_tiles(chrome)
		chrome.click_portal_tile(u"ownCloud")
		wait_for_page_fully_loaded(chrome.driver)

		# in owncloud: click the button under "alternative logins", called
		# "Single Sign-On Login"...
		owncloud_click_single_signon(chrome)

		# at this point we expect to see owncloud redirecting us back to
		# the portal login page...
		portal_login(chrome, user.properties["username"], "univention")
		owncloud_close_welcome_screen(chrome)

		owncloud_logout(chrome)

		assert "https://backup.autotest.local/univention/portal/" \
			== chrome.driver.current_url


def test_owncloud_with_owncloud_login(chrome, users):
	"""
	what this test does:
	- creates a random user
	- visits the portal page
	- clicks the owncloud tile
	- gets to the owncloud log in page
	- uses the text fields there to identify as user with password
	- dismisses the welcome dialog in owncloud
	- loggs out again
	- a final check tests if the user gets back to the owncloud login page
	"""

	test_name = "test_owncloud_with_owncloud_login"
	user = create_random_user(users)
	with chrome.capture(test_name):
		portal_goto(chrome)
		# make sure, that the app tiles are already loaded, then click...
		portal_wait_for_tiles(chrome)
		chrome.click_portal_tile(u"ownCloud")
		wait_for_page_fully_loaded(chrome.driver)

		owncloud_login(chrome, user)
		owncloud_close_welcome_screen(chrome)
		owncloud_logout(chrome)

		assert "https://master.autotest.local/owncloud/login" \
			== chrome.driver.current_url


def test_owncloud_in_tab_logout_in_portal(chrome, users):
	"""
	what this test does:
	- creates a random user
	- visits the portal page
	- clicks on `login` on the portal page
	- loggs in with username and password
	- that redirects the user automatically back to the portal page
	- there the user clicks on the owncloud tile with CTRL pressed
	- a new tab opens to which we change
	- in this tab there is owncloud login page, on which we click the sso button
	- we change back to the tab with the portal and log out
	- we change back to the tab with owncloud and log out
	- we are now redirected to the portal page and that is validated
	"""
	test_name = "test_owncloud_in_tab_logout_in_portal"
	user = create_random_user(users)
	with chrome.capture(test_name):
		portal_goto(chrome)
		portal_login_click(chrome)
		portal_login(chrome, user.properties["username"], "univention")

		# back on the portal page, after the log in, we have to wait for the
		# application tiles to appear before we can click them...
		portal_wait_for_tiles(chrome)

		# locate the owncloud tile based on its xpath
		owncloud_tile = chrome.driver.find_element_by_xpath(
			"//*[contains(@class, 'umcGalleryNameContent') and text() = 'ownCloud']")

		# hold the CTRL key, click the owncloud tile, release the CTRL key...
		ActionChains(chrome.driver) \
			.key_down(Keys.CONTROL) \
			.click(owncloud_tile) \
			.key_up(Keys.CONTROL) \
			.perform()

		# we have owncloud open in the first tab and we swtich to that tab...
		chrome.change_tab(1)
		# and wait until owncloud has loaded...
		wait_for_page_fully_loaded(chrome.driver)
		# that can be so quick, that it gets invisible in the produced video,
		# so give it some time before clicking on the single sign on button...
		highlight_this_part(chrome, test_name + "-before_click_sso_button")
		owncloud_click_single_signon(chrome)

		# before changing back to the portal, wait again so that we can see
		# in the video how the single sign on worked...
		highlight_this_part(chrome, test_name + "-before_change_to_portal_tab")
		chrome.change_tab(0)

		# logout button
		chrome.driver.find_element_by_id('umcLoginButton_label').click()
		wait_for_page_fully_loaded(chrome.driver)
		highlight_this_part(chrome, test_name + "-portal_logout_clicked")
		# confirmation dialog of the log out from the portal
		chrome.driver.find_element_by_id('umc_widgets_Button_1_label').click()
		wait_for_page_fully_loaded(chrome.driver)
		highlight_this_part(chrome, test_name + "-portal_logout_confirmation")

		# switch back to owncloud
		chrome.change_tab(1)

		# close the welcome screen and reload the page. If credentials would
		# be checked, we would get disconnected doing so, but that is not the
		# case...
		owncloud_close_welcome_screen(chrome)
		chrome.reload()
		highlight_this_part(chrome, test_name + "-reload_oc_after_logout")

		# log out from owncloud. That will bring us back to the sso page of
		# owncloud and that redirects us to the portal login page, because
		# we have it configured that way.
		owncloud_logout(chrome)
		highlight_this_part(chrome, test_name + "-after_owncloud_logout")
		# we expect to land on the portal page and wait for it to be loaded...
		portal_wait_for_tiles(chrome)

		assert chrome.driver.current_url.startswith(
			"https://backup.autotest.local/univention/portal/")


# main -------------------------------------------------------------------------

# dynamically load test_lib...
try:
	ucs_test_lib = os.environ.get('UCS_TEST_LIB', 'univention.testing.apptest')
	test_lib = importlib.import_module(ucs_test_lib)
except ImportError:
	print(
		"Could not import `{}`. Either try to set $UCS_TEST_LIB to the path "
		"of `apptest` or copy apptest into `PYTHONPATH`.".format(test_lib))
	sys.exit(1)

if __name__ == '__main__':
	test_lib.run_test_file(__file__)
