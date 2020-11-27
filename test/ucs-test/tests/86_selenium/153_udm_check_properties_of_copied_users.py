#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium-pytest -s
## desc: check properties of copied users/user
## tags: [udm]
## roles: [domaincontroller_master]
## bugs: [49823]
## exposure: dangerous
## packages:
## - univention-management-console-module-udm

import pytest
import time
import ldap
import univention.testing.selenium as sel
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
import univention.testing.selenium.udm as selenium_udm
from univention.udm import UDM


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
		jpegPhoto='/9j/4AAQSkZJRgABAQAAAQABAAD/4QBiRXhpZgAATU0AKgAAAAgABQESAAMAAAABAAEAAAEaAAUAAAABAAAASgEbAAUAAAABAAAAUgEoAAMAAAABAAEAAAITAAMAAAABAAEAAAAAAAAAAAABAAAAAQAAAAEAAAAB/9sAQwADAgICAgIDAgICAwMDAwQGBAQEBAQIBgYFBgkICgoJCAkJCgwPDAoLDgsJCQ0RDQ4PEBAREAoMEhMSEBMPEBAQ/9sAQwEDAwMEAwQIBAQIEAsJCxAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQ/8AAEQgAAQABAwERAAIRAQMRAf/EABQAAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFAEBAAAAAAAAAAAAAAAAAAAACP/EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhEDEQA/ADBHP1//2Q==',
		unixhome='/home/username',
		userCertificate="MIICEjCCAXsCAg36MA0GCSqGSIb3DQEBBQUAMIGbMQswCQYDVQQGEwJKUDEOMAwGA1UECBMFVG9reW8xEDAOBgNVBAcTB0NodW8ta3UxETAPBgNVBAoTCEZyYW5rNEREMRgwFgYDVQQLEw9XZWJDZXJ0IFN1cHBvcnQxGDAWBgNVBAMTD0ZyYW5rNEREIFdlYiBDQTEjMCEGCSqGSIb3DQEJARYUc3VwcG9ydEBmcmFuazRkZC5jb20wHhcNMTIwODIyMDUyNjU0WhcNMTcwODIxMDUyNjU0WjBKMQswCQYDVQQGEwJKUDEOMAwGA1UECAwFVG9reW8xETAPBgNVBAoMCEZyYW5rNEREMRgwFgYDVQQDDA93d3cuZXhhbXBsZS5jb20wXDANBgkqhkiG9w0BAQEFAANLADBIAkEAm/xmkHmEQrurE/0re/jeFRLl8ZPjBop7uLHhnia7lQG/5zDtZIUC3RVpqDSwBuw/NTweGyuP+o8AG98HxqxTBwIDAQABMA0GCSqGSIb3DQEBBQUAA4GBABS2TLuBeTPmcaTaUW/LCB2NYOy8GMdzR1mx8iBIu2H6/E2tiY3RIevV2OW61qY2/XRQg7YPxx3ffeUugX9F4J/iPnnu1zAxxyBy2VguKv4SWjRFoRkIfIlHX0qVviMhSlNy2ioFLy7JcPZb+v3ftDGywUqcBiVDoea0Hn+GmxZACg==",
)
	return dn, username


def _check_copied_user(username, username_copy):
	attribute_list = ['title', 'initials', 'preferredDeliveryMethod', 'pwdChangeNextLogin', 'employeeNumber',
		'homePostalAddress', 'mobileTelephoneNumber', 'pagerTelephoneNumber', 'birthday', 'jpegPhoto', 'unixhome',
		'userCertificate', 'certificateIssuerCountry', 'certificateIssuerState', 'certificateIssuerLocation', 'certificateIssuerOrganisation',
		'certificateIssuerMail', 'certificateSubjectCountry', 'certificateSubjectState', 'certificateSubjectLocation', 'certificateSubjectOrganisation',
		'certificateSubjectOrganisationalUnit', 'certificateSubjectCommonName', 'certificateSubjectMail', 'certificateDateNotBefore',
		'certificateDateNotAfter', 'certificateVersion', 'certificateSerial']

	udm_admin = UDM.admin().version(1)
	orig_user = list(udm_admin.get('users/user').search('username=%s' % (username,)))[0]
	copied_user = list(udm_admin.get('users/user').search('username=%s' % (username_copy,)))[0]
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
	_, _username = _create_user(udm)
	selenium.do_login()
	_users = selenium_udm.Users(selenium)
	selenium.open_module(_users.name)
	_users.wait_for_main_grid_load()
	_username_copy = _users.copy(_username)
	_check_copied_user(_username, _username_copy)
	_dn_copy = 'uid=%s,cn=users,%s' % (ldap.dn.escape_dn_chars(_username_copy), ucr.get('ldap/base'))
	udm._cleanup['users/user'].append(_dn_copy)
