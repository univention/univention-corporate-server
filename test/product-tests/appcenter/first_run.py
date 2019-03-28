#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import subprocess

from univention.testing.selenium import UMCSeleniumTest
from selenium.common.exceptions import TimeoutException
from univention.appcenter.ucr import ucr_load, ucr_get
from univention.appcenter.udm import search_objects, get_machine_connection


test = UMCSeleniumTest()
test.screenshot_path = '/usr/share/ucs-test/product-tests/selenium'
with test:
	test.do_login()
	test.open_module("App Center")
	# Wird am Anfang ein Hinweis-Text angezeigt?
	test.wait_for_text("Do not show this message again")
	test.save_screenshot("initial_notification")
	test.click_text("Do not show this message again")
	test.click_button("Continue")

	# können Apps mit NotifyVendor=No installiert werden (sollte so sein) ?
	test.wait_for_text("Self Service")
	test.save_screenshot("app_overview")
	test.click_element('//div[contains(concat(" ", normalize-space(@class), " "), " umcGalleryWrapperItem ")][@moduleid="self-service"]')
	test.wait_for_text("Install this App")
	test.save_screenshot("app_selfservice")
	test.click_button("Install")
	test.wait_for_text("Performing software tests")

	# Wird eine Nachfrage mit zu installierenden Paketen angezeigt? Auch für sich in der Domäne befindlichen Master und Backupsystemen (falls MasterPackages eingetragen sind)?
	test.wait_for_text("Installation of Self Service")
	test.click_text("More information")
	test.wait_for_text("univention-self-service-passwordreset-umc", timeout=3)
	#test.wait_for_text("univention-self-service-master", timeout=3)  # Bug https://forge.univention.org/bugzilla/show_bug.cgi?id=49183
	try:
		# Werden wichtige System-Pakete deinstalliert (z.B. univention-server-master)?
		test.wait_for_text("univention-server-", timeout=1)
	except TimeoutException:
		pass
	else:
		raise ValueError("I *DID* find a dangerous package")
	test.click_button("Install")
	test.wait_for_text("Installing Self Service on this host")
	test.wait_until_all_standby_animations_disappeared()

	# Werden README_INSTALL und README_POST_INSTALL korrekt vor bzw. nach der Installation angezeigt?
	test.wait_for_text("Congratulations, the Self Service Modules have been installed!")
	test.click_button("Continue")
	test.wait_until_all_standby_animations_disappeared()
	test.wait_for_text("Self Service modules allow users to take care")
	test.save_screenshot("app_installed")

	# Erfolgreich?
	test.wait_for_text("Manage local installation")
	subprocess.call(['univention-check-join-status'])
	ucr_load()
	for key, value in [('appcenter/installed', 'ME'), ('appcenter/apps/self-service/status', 'installed'), ('appcenter/apps/self-service/version', '4.0')]:
		if ucr_get(key) != value:
			raise ValueError('%s: %r' % (key, ucr_get(key)))
	lo, pos = get_machine_connection()
	app_obj = search_objects('appcenter/app', lo, pos)[0]
	app_obj.dn == 'univentionAppID=self-service_4.0,cn=self-service,cn=apps,cn=univention,%s' % ucr_get('ldap/base')

	# Können Apps mit NotifyVendor=Yes installiert werden (sollte nicht so sein) ?
	test.click_button("Back to overview")
	test.click_element('//div[contains(concat(" ", normalize-space(@class), " "), " umcGalleryWrapperItem ")][@moduleid="nextcloud"]')
	test.wait_for_text("Nextcloud brings together universal access")
	test.click_button("Install")
	test.wait_for_text("License Agreement")
	test.click_button("Accept license")
	test.wait_for_text("Install Information")
	test.click_element("//*[contains(@class, 'dijitDialog')]//*[contains(@class, 'dijitButton')]//*[contains(text(), 'Install')]")
	test.wait_for_text("This App uses a container technology")
	test.click_text("Do not show this message again")
	test.click_button("Continue")
	test.wait_for_text("Error performing the action")
	test.wait_for_text("Activate UCS now")
	test.click_button("Cancel")

	# License-Key über univention-E-Mail-Adresse anfordern + eintragen.
	# Ohne erneuten Login sollte danach eine Installation möglich sein.
	subprocess.call(['/bin/bash -c ". /root/utils.sh && import_license"'], shell=True)
	test.click_button("Install")
	test.wait_for_text("License Agreement")
	test.click_button("Accept license")
	test.wait_for_text("Install Information")
	test.click_element("//*[contains(@class, 'dijitDialog')]//*[contains(@class, 'dijitButton')]//*[contains(text(), 'Install')]")
	test.wait_for_text("In order to proceed with the installation of Nextcloud")
	test.click_button("Cancel")

	# Ist die Deinstallation einer App möglich und erfolgreich?
	test.wait_for_text("Manage local installation")
	test.click_button("Uninstall")
	test.wait_for_text("Please confirm to uninstall")
	test.click_button("Uninstall")
	test.wait_for_text("Uninstalling Self Service from this host")
	test.wait_until_all_standby_animations_disappeared()
	test.wait_for_text("Install this App")
	for key, value in [('appcenter/installed', ''), ('appcenter/apps/self-service/status', None), ('appcenter/apps/self-service/version', None)]:
		if ucr_get(key) != value:
			raise ValueError('%s: %r' % (key, ucr_get(key)))
	try:
		# Werden wichtige System-Pakete deinstalliert (z.B. univention-server-master)?
		test.wait_for_text("univention-server-", timeout=1)
	except TimeoutException:
		pass
	else:
		raise ValueError("I *DID* find a dangerous package")

	# Bei Deinstallation einer App mit LDAP-Schema-Erweiterungen sollten die Schema-Pakete nicht deinstalliert werden.
	output = subprocess.check_output(['dpkg -s univention-self-service-master | grep Status'], shell=True)
	if output != 'Status: install ok installed\n':
		raise ValueError('Master package removed!')
