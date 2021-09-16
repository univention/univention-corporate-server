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
import selenium.common.exceptions as selenium_exceptions


JPEG = '''
/9j/4AAQSkZJRgABAQAAAQABAAD/4QBiRXhpZgAATU0AKgAAAAgABQESAAMAAAABAAEAAAEaAAUAAAABAAAASgEbAA
UAAAABAAAAUgEoAAMAAAABAAEAAAITAAMAAAABAAEAAAAAAAAAAAABAAAAAQAAAAEAAAAB/9sAQwADAgICAgIDAgIC
AwMDAwQGBAQEBAQIBgYFBgkICgoJCAkJCgwPDAoLDgsJCQ0RDQ4PEBAREAoMEhMSEBMPEBAQ/9sAQwEDAwMEAwQIBA
QIEAsJCxAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQ/8AAEQgAAQABAwER
AAIRAQMRAf/EABQAAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFAEBAAAAAAAAAAAAAA
AAAAAACP/EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhEDEQA/ADBHP1//2Q=='''.strip().replace('\n', '')
CERT = '''
MIICEjCCAXsCAg36MA0GCSqGSIb3DQEBBQUAMIGbMQswCQYDVQQGEwJKUDEOMAwGA1UECBMFVG9reW8xEDAOBgNVBA
cTB0NodW8ta3UxETAPBgNVBAoTCEZyYW5rNEREMRgwFgYDVQQLEw9XZWJDZXJ0IFN1cHBvcnQxGDAWBgNVBAMTD0Zy
YW5rNEREIFdlYiBDQTEjMCEGCSqGSIb3DQEJARYUc3VwcG9ydEBmcmFuazRkZC5jb20wHhcNMTIwODIyMDUyNjU0Wh
cNMTcwODIxMDUyNjU0WjBKMQswCQYDVQQGEwJKUDEOMAwGA1UECAwFVG9reW8xETAPBgNVBAoMCEZyYW5rNEREMRgw
FgYDVQQDDA93d3cuZXhhbXBsZS5jb20wXDANBgkqhkiG9w0BAQEFAANLADBIAkEAm/xmkHmEQrurE/0re/jeFRLl8Z
PjBop7uLHhnia7lQG/5zDtZIUC3RVpqDSwBuw/NTweGyuP+o8AG98HxqxTBwIDAQABMA0GCSqGSIb3DQEBBQUAA4GB
ABS2TLuBeTPmcaTaUW/LCB2NYOy8GMdzR1mx8iBIu2H6/E2tiY3RIevV2OW61qY2/XRQg7YPxx3ffeUugX9F4J/iPn
nu1zAxxyBy2VguKv4SWjRFoRkIfIlHX0qVviMhSlNy2ioFLy7JcPZb+v3ftDGywUqcBiVDoea0Hn+GmxZACg=='''.strip().replace('\n', '')


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


@pytest.fixture
def user_info(udm):
	''' The created user will have all properties set that were removed from being copyable (Bug 49823)'''

	dn, username = udm.create_user(
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
		jpegPhoto=JPEG,
		unixhome='/home/username',
		userCertificate=CERT,
	)
	copied_username = "testcopy_%s" % (username,)
	yield {
		'orig_dn': dn,
		'orig_username': username,
		'copied_username': copied_username
	}
	for user in UDM.admin().version(1).get('users/user').search('username=%s' % (copied_username,)):
		user.delete()


def _copy_user(selenium, orig_dn, orig_username, copied_username):
	selenium.do_login()
	selenium.open_module('Users')
	selenium.click_checkbox_of_grid_entry(orig_username)
	selenium.click_button('more')
	selenium.click_text('Copy')

	try:
		selenium.wait_for_any_text_in_list(['Container', 'Template'], timeout=5)
		selenium.click_button('Next')
	except selenium_exceptions.TimeoutException:
		selenium.wait_until_standby_animation_appears_and_disappears()
	selenium.wait_until_standby_animation_appears_and_disappears()

	selenium.enter_input('username', copied_username)
	selenium.enter_input('lastname', 'testuser')
	selenium.enter_input("password_1", 'univention')
	selenium.enter_input("password_2", 'univention')
	selenium.click_button('Create user')
	selenium.wait_until_standby_animation_appears_and_disappears()


def _check_copied_user(orig_dn, copied_username):
	attribute_list = [
		'title', 'initials', 'preferredDeliveryMethod', 'pwdChangeNextLogin', 'employeeNumber',
		'homePostalAddress', 'mobileTelephoneNumber', 'pagerTelephoneNumber', 'birthday', 'jpegPhoto', 'unixhome',
		'userCertificate', 'certificateIssuerCountry', 'certificateIssuerState', 'certificateIssuerLocation', 'certificateIssuerOrganisation',
		'certificateIssuerMail', 'certificateSubjectCountry', 'certificateSubjectState', 'certificateSubjectLocation', 'certificateSubjectOrganisation',
		'certificateSubjectOrganisationalUnit', 'certificateSubjectCommonName', 'certificateSubjectMail', 'certificateDateNotBefore',
		'certificateDateNotAfter', 'certificateVersion', 'certificateSerial']

	users_module = UDM.admin().version(1).get('users/user')
	orig_user = users_module.get(orig_dn)
	copied_user = list(users_module.search('username=%s' % (copied_username,)))[0]
	orig_user_props = orig_user.props.__dict__
	copied_user_props = copied_user.props.__dict__
	for attribute in attribute_list:
		print("Checking that %s is not copied" % (attribute,))
		if attribute != 'jpegPhoto':
			assert orig_user_props[attribute] != copied_user_props[attribute]
		else:
			assert copied_user_props[attribute] is None
	return copied_user.__dict__['dn']


def test_copy_user(selenium, user_info):
	_copy_user(selenium, user_info['orig_dn'], user_info['orig_username'], user_info['copied_username'])
	_check_copied_user(user_info['orig_dn'], user_info['copied_username'])
