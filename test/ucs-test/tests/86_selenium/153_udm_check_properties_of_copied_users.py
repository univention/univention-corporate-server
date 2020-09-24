#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium-pytest
## desc: check properties of copied users/user
## tags: [udm]
## roles: [domaincontroller_master]
## bugs: [49823]
## exposure: dangerous
## packages:
## - univention-management-console-module-udm

import pytest

import univention.testing.selenium as sel
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
from univention.udm import UDM
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.ui import WebDriverWait


@pytest.fixture(scope="module")
def ucr():
	with ucr_test.UCSTestConfigRegistry() as ucr:
		yield ucr


@pytest.fixture(scope="module")
def udm():
	with udm_test.UCSTestUDM() as udm:
		yield udm


@pytest.fixture(scope="module")
def selenium():
	with sel.UMCSeleniumTest() as s:
		yield s


def _create_user(udm):
	''' The created user will have all properties set that were removed from being copyable (Bug 49823)'''

	_dn, _username = udm.create_user(
		gecos='',
		displayName='',
		title='Univ',
		initials='U.U.',
		preferredDeliveryMethod='any',
		pwdChangeNextLogin='1',
		employeeNumber='42',
		homePostalAddress='Mary-Somervile 28359 Bremen',
		mobileTelephoneNumber='+49 421 12345-0',
		pagerTelephoneNumber='+49 421 23456-0',
		birthday='2000-01-01',
		jpegPhoto='/9j/4AAQSkZJRgABAQAAAQABAAD/4QBiRXhpZgAATU0AKgAAAAgABQESAAMAAAABAAEAAAEaAAUAAAABAAAASgEbAAUAAAABAAAAUgEoAAMAAAABAAEAAAITAAMAAAABAAEAAAAAAAAAAAABAAAAAQAAAAEAAAAB/9sAQwADAgICAgIDAgICAwMDAwQGBAQEBAQIBgYFBgkICgoJCAkJCgwPDAoLDgsJCQ0RDQ4PEBAREAoMEhMSEBMPEBAQ/9sAQwEDAwMEAwQIBAQIEAsJCxAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQ/8AAEQgAAQABAwERAAIRAQMRAf/EABQAAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFAEBAAAAAAAAAAAAAAAAAAAACP/EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhEDEQA/ADBHP1//2Q==',
		unixhome='/home/username',
		userCertificate="MIICEjCCAXsCAg36MA0GCSqGSIb3DQEBBQUAMIGbMQswCQYDVQQGEwJKUDEOMAwGA1UECBMFVG9reW8xEDAOBgNVBAcTB0NodW8ta3UxETAPBgNVBAoTCEZyYW5rNEREMRgwFgYDVQQLEw9XZWJDZXJ0IFN1cHBvcnQxGDAWBgNVBAMTD0ZyYW5rNEREIFdlYiBDQTEjMCEGCSqGSIb3DQEJARYUc3VwcG9ydEBmcmFuazRkZC5jb20wHhcNMTIwODIyMDUyNjU0WhcNMTcwODIxMDUyNjU0WjBKMQswCQYDVQQGEwJKUDEOMAwGA1UECAwFVG9reW8xETAPBgNVBAoMCEZyYW5rNEREMRgwFgYDVQQDDA93d3cuZXhhbXBsZS5jb20wXDANBgkqhkiG9w0BAQEFAANLADBIAkEAm/xmkHmEQrurE/0re/jeFRLl8ZPjBop7uLHhnia7lQG/5zDtZIUC3RVpqDSwBuw/NTweGyuP+o8AG98HxqxTBwIDAQABMA0GCSqGSIb3DQEBBQUAA4GBABS2TLuBeTPmcaTaUW/LCB2NYOy8GMdzR1mx8iBIu2H6/E2tiY3RIevV2OW61qY2/XRQg7YPxx3ffeUugX9F4J/iPnnu1zAxxyBy2VguKv4SWjRFoRkIfIlHX0qVviMhSlNy2ioFLy7JcPZb+v3ftDGywUqcBiVDoea0Hn+GmxZACg==",
)
	return _dn, _username


def _umc_logon(selenium, username, pw, fqdn):
	"""
	method to log into the ucs portal with a given username and password
	"""

	try:
		selenium.driver.get("http://" + fqdn + "/univention/portal/")

		WebDriverWait(selenium.driver, 30).until(
			expected_conditions.element_to_be_clickable(
				(By.XPATH, '//*[@id="umcLoginButton_label"]')
			)
		).click()
		WebDriverWait(selenium.driver, 30).until(
			expected_conditions.element_to_be_clickable(
				(By.XPATH, '//*[@id="umcLoginUsername"]')
			)
		).send_keys(username)
		WebDriverWait(selenium.driver, 30).until(
			expected_conditions.element_to_be_clickable(
				(By.XPATH, '//*[@id="umcLoginPassword"]')
			)
		).send_keys(pw)

		elem = selenium.driver.find_elements_by_id("umcLoginSubmit")[0]
		elem.click()

		WebDriverWait(selenium.driver, 30).until(
			expected_conditions.element_to_be_clickable(
				(By.XPATH, '//*[@id="umcLoginButton_label"]')
			)
		).click()
	except BaseException as exc:
		selenium.save_screenshot()
	finally:
		print("UMC Logon with {} done".format(username))


def _copy_user(selenium, fqdn, orig_dn, orig_username, copied_name):
	print("copy")
	# click on testuser in user module
	selenium.driver.get("http://" + fqdn + "/univention/management/#module=udm:users/user:0:")

	WebDriverWait(selenium.driver, 30).until(
		expected_conditions.element_to_be_clickable(
		(By.XPATH, '//*[@id="dgrid_1-row-%s"]' % (orig_dn,))
		)
	).click()

	# open dropdown
	WebDriverWait(selenium.driver, 30).until(
		expected_conditions.element_to_be_clickable(
		(By.XPATH, '//*[@id="dijit_form_DropDownButton_4_label"]')
		)
	).click()

	# click "copy"
	header = selenium.driver.find_element_by_xpath('//*[@id="dgrid_1-row-%s"]' % (orig_dn,))
	child = header.find_elements_by_xpath('//*[@id="dijit_MenuItem_30_text"]')[0]
	time.sleep(20)
	child.click()
	time.sleep(10)
	# select a template, if a BaseException is raised here, there is not template to choose and we can just ignore this
	try:
		# select template
		WebDriverWait(selenium.driver, 30).until(
			expected_conditions.element_to_be_clickable(
			(By.XPATH, '//*[@id="widget_umc_widgets_ComboBox_9"]/div[1]/input')
			)
		).click()

		# submit selection of template
		WebDriverWait(selenium.driver, 30).until(
			expected_conditions.element_to_be_clickable(
			(By.XPATH, '//*[@id="umc_widgets_ComboBox_9_popup1"]')
			)
		).click()

		WebDriverWait(selenium.driver, 30).until(
			expected_conditions.element_to_be_clickable(
			(By.XPATH, '//*[@id="umc_widgets_Button_66_label"]')
			)
		).click()
	except BaseException:
		pass
	# username
	WebDriverWait(selenium.driver, 30).until(
		expected_conditions.element_to_be_clickable(
		(By.NAME, 'username')
		)
	).send_keys(copied_name)

	# lastname
	WebDriverWait(selenium.driver, 30).until(
		expected_conditions.element_to_be_clickable(
		(By.NAME, 'lastname')
		)
	).send_keys('testuser')

	# password
	WebDriverWait(selenium.driver, 30).until(
		expected_conditions.element_to_be_clickable(
		(By.XPATH, '//*[@id="umc_widgets_PasswordBox_2"]')
		)
	).send_keys('univention')

	# password 2
	WebDriverWait(selenium.driver, 30).until(
		expected_conditions.element_to_be_clickable(
		(By.XPATH, '//*[@id="umc_widgets_PasswordBox_3"]')
		)
	).send_keys('univention')

	# submit
	WebDriverWait(selenium.driver, 30).until(
		expected_conditions.element_to_be_clickable(
		(By.XPATH, '//*[@id="umc_widgets_SubmitButton_5_label"]')
		)
	).click()


def _check_copied_user(orig_dn, orig_username, copied_username):
	attribute_list = ['title', 'initials', 'preferredDeliveryMethod', 'pwdChangeNextLogin', 'employeeNumber',
		'homePostalAddress', 'mobileTelephoneNumber', 'pagerTelephoneNumber', 'birthday', 'jpegPhoto', 'unixhome',
		'userCertificate', 'certificateIssuerCountry', 'certificateIssuerState', 'certificateIssuerLocation', 'certificateIssuerOrganisation',
		'certificateIssuerMail', 'certificateSubjectCountry', 'certificateSubjectState', 'certificateSubjectLocation', 'certificateSubjectOrganisation',
		'certificateSubjectOrganisationalUnit', 'certificateSubjectCommonName', 'certificateSubjectMail', 'certificateDateNotBefore',
		'certificateDateNotAfter', 'certificateVersion', 'certificateSerial']

	udm_admin = UDM.admin().version(1)
	orig_user = list(udm_admin.get('users/user').search('username=%s' % (orig_username,)))[0]
	copied_user = list(udm_admin.get('users/user').search('username=%s' % (copied_username,)))[0]
	orig_user_props = orig_user.props.__dict__
	copied_user_props = copied_user.props.__dict__
	for attribute in attribute_list:
		print("Checking that %s is not copied" % (attribute,))
		if attribute != 'jpegPhoto':
			assert orig_user_props[attribute] != copied_user_props[attribute]
		else:
			assert copied_user_props[attribute] is None
	return copied_user.__dict__['dn']


def test_copy_user(selenium, ucr, udm):
	_dn, _username = _create_user(udm)
	_copied_username = "testcopy_%s" % (_username,)
	_copied_user_dn = "uid=%s,cn=users,%s" % (_copied_username, ucr.get("ldap/base"))
	udm._cleanup['users/user'].append(_copied_user_dn)
	try:
		_fqdn = "%s.%s" % (ucr.get("hostname"), ucr.get("domainname"))
		_umc_logon(selenium, 'Administrator', 'univention', _fqdn)
		_copy_user(selenium, _fqdn, _dn, _username, _copied_username)
		time.sleep(30)
	except BaseException:
		selenium.save_screenshot()
		raise
	_check_copied_user(_dn, _username, _copied_username)
