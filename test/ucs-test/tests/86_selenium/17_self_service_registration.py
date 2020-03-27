#!/usr/share/ucs-test/runner /usr/bin/py.test
# -*- coding: utf-8 -*-
## desc: test self registration
## tags: [apptest]
## packages:
##  - univention-self-service
##  - univention-self-service-master
##  - univention-self-service-passwordreset-umc
## roles-not:
##  - memberserver
##  - basesystem
## join: true
## exposure: dangerous

import pytest
import email
from urlparse import urlparse, parse_qs

from univention.config_registry import handler_set
from univention.lib.umc import Client
from univention.admin.uldap import getAdminConnection
from univention.admin.uexceptions import noObject

from univention.testing import selenium as sel
from univention.testing.ucr import UCSTestConfigRegistry
from test_self_service import capture_mails
import univention.testing.strings as uts
import selenium.common.exceptions as selenium_exceptions
import univention.testing.utils as utils


@pytest.fixture
def selenium():
	with sel.UMCSeleniumTest() as s:
		yield s


@pytest.fixture
def ucr():
	with UCSTestConfigRegistry() as ucr:
		yield ucr


@pytest.fixture
def umc_client():
	return Client()


@pytest.fixture
def mails():
	with capture_mails(timeout=5) as mails:
		yield mails


@pytest.fixture
def registration_info(ucr):
	container = ucr.get('umc/self-service/account-registration/usercontainer')
	username = uts.random_name()
	dn = "uid=%s,%s" % (username, container)
	attributes = {
		'username': username,
		'lastname': username,
		'password': 'univention',
		'PasswordRecoveryEmail': 'root@localhost'
	}
	yield {
		'dn': dn,
		'attributes': attributes
	}
	lo, po = getAdminConnection()
	try:
		lo.delete(dn)
	except noObject:
		pass


# test the umc/self-service/registration/enabled ucr variable
def test_registration_enabled(ucr, selenium):
	# test that the default is false
	selenium.driver.get(selenium.base_url + 'univention/self-service')
	with pytest.raises(selenium_exceptions.TimeoutException):
		selenium.wait_for_text('Create an account', 2)
	handler_set(['umc/self-service/account-registration/enabled=true'])
	selenium.driver.get(selenium.base_url + 'univention/self-service')
	selenium.wait_for_text('Create an account', 2)
	handler_set(['umc/self-service/account-registration/enabled=false'])
	selenium.driver.get(selenium.base_url + 'univention/self-service')
	with pytest.raises(selenium_exceptions.TimeoutException):
		selenium.wait_for_text('Create an account', 2)


# tests existence of all attributes umc/self-service/registration/udm_attributes
def test_udm_attributes(ucr, selenium):
	selenium.driver.get(selenium.base_url + 'univention/self-service/#page=createaccount')
	selenium.wait_until_element_visible('//h2[text()="Create an account"]')
	selenium.wait_until_element_visible('//label[text()="Email *"]')
	selenium.wait_until_element_visible('//label[text()="Password *"]')
	selenium.wait_until_element_visible('//label[text()="Password (retype) *"]')
	selenium.wait_until_element_visible('//label[text()="First name"]')
	selenium.wait_until_element_visible('//label[text()="Last name *"]')
	selenium.wait_until_element_visible('//label[text()="User name *"]')
	handler_set(['umc/self-service/account-registration/udm_attributes=description,title'])
	handler_set(['umc/self-service/account-registration/udm_attributes/required=title'])
	selenium.driver.refresh()
	selenium.wait_until_element_visible('//h2[text()="Create an account"]')
	selenium.wait_until_element_visible('//label[text()="Email *"]')
	selenium.wait_until_element_visible('//label[text()="Password *"]')
	selenium.wait_until_element_visible('//label[text()="Password (retype) *"]')
	selenium.wait_until_element_visible('//label[text()="Description"]')
	selenium.wait_until_element_visible('//label[text()="Title *"]')


# tests whether a user is created and put into the right container
@pytest.mark.parametrize("verification_process", ['automatic', 'manual'])
def test_user_creation(mails, selenium, umc_client, registration_info, verification_process):
	#creates user
	selenium.driver.get(selenium.base_url + 'univention/self-service/#page=createaccount')
	selenium.driver.refresh()
	dn = registration_info['dn']
	attributes = registration_info['attributes']
	selenium.enter_input('PasswordRecoveryEmail', attributes['PasswordRecoveryEmail'])
	selenium.enter_input('password_1', attributes['password'])
	selenium.enter_input('password_2', attributes['password'])
	selenium.enter_input('lastname', attributes['username'])
	selenium.enter_input('username', attributes['username'])
	selenium.click_button('Create account')
	selenium.wait_until_standby_animation_appears_and_disappears()
	utils.verify_ldap_object(dn, {
		'univentionRegisteredThroughSelfService': ['TRUE'],
		'univentionPasswordRecoveryEmailVerified': ['FALSE'],
	})
	#tests email
	mail = email.message_from_string(mails.data and mails.data[0]).get_payload(decode=True)
	assert mail, 'No email has been received in 5 seconds'
	verification_links = [line for line in mail.split() if line.startswith('https://')]
	if verification_process == 'automatic':
		#tests automatic link
		selenium.driver.get(verification_links[0])
		selenium.wait_for_text('Account verification')
		selenium.wait_until_standby_animation_appears_and_disappears()
		selenium.driver.find_element_by_xpath('//text()[contains(., "your account has been successfully verified")]//parent::*')
	elif verification_process == 'manual':
		#tests manual link
		selenium.driver.get(verification_links[1])
		verify_fragment = urlparse(verification_links[0]).fragment
		verify_params = parse_qs(verify_fragment)
		selenium.enter_input('username', attributes['username'])
		selenium.enter_input('token', verify_params['token'][0])
		selenium.click_button('Verify account')
		selenium.wait_for_text('Account verification')
		selenium.wait_until_standby_animation_appears_and_disappears()
		selenium.driver.find_element_by_xpath('//text()[contains(., "your account has been successfully verified")]//parent::*')
	utils.verify_ldap_object(dn, {
		'univentionRegisteredThroughSelfService': ['TRUE'],
		'univentionPasswordRecoveryEmailVerified': ['TRUE'],
	})
