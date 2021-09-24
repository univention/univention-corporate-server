#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium-pytest -s -l -v --tb=native
## desc: check properties of copied users/user
## tags: [udm]
## roles: [domaincontroller_master]
## bugs: [49823]
## exposure: dangerous
## packages:
## - univention-management-console-module-udm

import sys

import pytest

import univention.testing.selenium.udm as selenium_udm
from univention.udm import UDM


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


def test_copy_user(selenium, user_info):
	orig_dn = user_info['orig_dn']
	orig_username = user_info['orig_username']
	copied_username = user_info['copied_username']

	# copy the user
	try:
		selenium.do_login()
		users = selenium_udm.Users(selenium)
		users.open_module()
		# users.wait_for_main_grid_load()
		users.copy(orig_username, copied_username, 'testuser')
	except Exception:  # workaround for pytest fixture
		selenium.__exit__(*sys.exc_info())
		raise

	# verify copying worked
	attribute_list = [
		'title', 'initials', 'preferredDeliveryMethod', 'pwdChangeNextLogin', 'employeeNumber',
		'homePostalAddress', 'mobileTelephoneNumber', 'pagerTelephoneNumber', 'birthday', 'jpegPhoto', 'unixhome',
		'userCertificate', 'certificateIssuerCountry', 'certificateIssuerState', 'certificateIssuerLocation', 'certificateIssuerOrganisation',
		'certificateIssuerMail', 'certificateSubjectCountry', 'certificateSubjectState', 'certificateSubjectLocation', 'certificateSubjectOrganisation',
		'certificateSubjectOrganisationalUnit', 'certificateSubjectCommonName', 'certificateSubjectMail', 'certificateDateNotBefore',
		'certificateDateNotAfter', 'certificateVersion', 'certificateSerial'
	]

	users_module = UDM.admin().version(1).get('users/user')
	orig_user = users_module.get(orig_dn)
	try:
		copied_user = users_module.get_by_id(copied_username)
	except Exception:  # workaround for pytest fixture
		selenium.__exit__(*sys.exc_info())
		raise

	orig_user_props = orig_user.props.__dict__
	copied_user_props = copied_user.props.__dict__
	for attribute in attribute_list:
		if attribute == 'jpegPhoto':
			assert copied_user_props[attribute] is None
		else:
			assert orig_user_props[attribute] != copied_user_props[attribute]
