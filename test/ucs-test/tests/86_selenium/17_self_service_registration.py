#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium-pytest
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


import time
import email

import pytest
import selenium.common.exceptions as selenium_exceptions
from selenium.common.exceptions import TimeoutException
from six.moves.urllib_parse import parse_qs, urlparse
from test_self_service import capture_mails

import univention.testing.strings as uts
import univention.testing.utils as utils
from univention.admin.uexceptions import noObject
from univention.admin.uldap import getAdminConnection
from univention.config_registry import handler_set as hs
from univention.testing.ucr import UCSTestConfigRegistry

MAILS_TIMEOUT = 5


@pytest.fixture(scope="module", autouse=True)
def activate_self_registration():
	with UCSTestConfigRegistry() as ucr:
		hs(['umc/self-service/account-registration/backend/enabled=true'])
		hs(['umc/self-service/account-registration/frontend/enabled=true'])
		hs(['umc/self-service/account-verification/backend/enabled=true'])
		hs(['umc/self-service/account-verification/frontend/enabled=true'])
		yield ucr


@pytest.fixture
def mails():
	with capture_mails(timeout=MAILS_TIMEOUT) as mails:
		yield mails


@pytest.fixture
def get_registration_info(ucr):
	class local:
		dns = []

	def _get_registration_info(attributes=None, container_without_base=None):
		if container_without_base:
			container_dn = '%s,%s' % (container_without_base, ucr.get('ldap/base'),)
			ucr.handler_set(['umc/self-service/account-registration/usercontainer=%s' % (container_dn,)])
			ucr.load()
		container_dn = ucr.get('umc/self-service/account-registration/usercontainer')
		username = uts.random_name()
		_attributes = {
			'username': username,
			'lastname': username,
			'password': 'univention',
			'PasswordRecoveryEmail': 'root@localhost'
		}
		if attributes:
			_attributes.update(attributes)
		dn = "uid=%s,%s" % (_attributes['username'], container_dn)
		local.dns.append(dn)
		return {
			'dn': dn,
			'attributes': _attributes,
			'data': {
				'attributes': _attributes
			}
		}
	yield _get_registration_info
	lo, po = getAdminConnection()
	for dn in local.dns:
		try:
			lo.delete(dn)
		except noObject:
			pass


def _get_mail(mails, idx=-1):
	assert mails.data, 'No mails have been captured in %s seconds' % (MAILS_TIMEOUT,)
	assert idx < len(mails.data), 'Not enough mails have been captured to get mail of index: {}'.format(idx)
	mail = email.message_from_string(mails.data[idx].decode("utf-8"))
	body = mail.get_payload(decode=True).decode("utf-8")
	verification_links = []
	for line in body.split():
		if line.startswith('https://'):
			verification_links.append(line)
	auto_verify_link = verification_links[0] if len(verification_links) else ''
	verify_link = verification_links[1] if len(verification_links) else ''
	verify_fragment = urlparse(auto_verify_link).fragment
	verify_params = parse_qs(verify_fragment)
	return {
		'mail': mail,
		'body': body,
		'auto_verify_link': auto_verify_link,
		'verify_link': verify_link,
		'verify_data': {
			'username': verify_params.get('username', [''])[0],
			'token': verify_params.get('/selfservice/verifyaccount/?token', [''])[0],
			'method': verify_params.get('method', [''])[0],
		}
	}


def click_submit(selenium):
	try:
		selenium.driver.find_elements_by_css_selector(".primary")[0].click()
	except IndexError:
		selenium.driver.find_element_by_xpath("//*[@id='modal-wrapper--isVisible-1']/section/form/footer/button").click()


def _enter_attributes(selenium, attributes, button=True):
	for k, v in attributes.items():
		if k == 'password':
			selenium.enter_input('password', v)
			selenium.enter_input('password--retype', v)
		else:
			selenium.enter_input(k, v)
	if button:
		click_submit(selenium)


def _navigate_self_service(selenium, _hash=None):
	url = selenium.base_url + 'univention/portal/#/selfservice/'
	selenium.driver.get(url)
	if _hash:
		selenium.driver.get(url + _hash)


# test the umc/self-service/registration/enabled ucr variable
def test_registration_enabled(selenium, ucr, get_registration_info):
	ucr.handler_set(['umc/self-service/account-registration/frontend/enabled=false'])
	_navigate_self_service(selenium)
	with pytest.raises(selenium_exceptions.TimeoutException):
		selenium.wait_for_text('Create an account', 2)
	ucr.handler_set([
		'umc/self-service/account-registration/frontend/enabled=true',
		'umc/self-service/account-registration/backend/enabled=false',
	])
	_navigate_self_service(selenium, 'createaccount')
	selenium.wait_for_text('Create an account', 2)
	info = get_registration_info()
	time.sleep(3)
	_enter_attributes(selenium, info['attributes'])
	selenium.wait_for_text('The account registration was disabled via the Univention Configuration Registry.')


# tests existence of all attributes umc/self-service/registration/udm_attributes
def test_udm_attributes(selenium, ucr):
	_navigate_self_service(selenium, 'createaccount')
	selenium.wait_for_text('Create an account', 2)
	selenium.wait_until_element_visible('//label[contains(text(), "Email")]')
	selenium.wait_until_element_visible('//label[contains(text(), "Password")]')
	selenium.wait_until_element_visible('//label[contains(text(), "Password (retype)")]')
	selenium.wait_until_element_visible('//label[contains(text(), "First name")]')
	selenium.wait_until_element_visible('//label[contains(text(), "Last name")]')
	selenium.wait_until_element_visible('//label[contains(text(), "User name")]')
	ucr.handler_set(['umc/self-service/account-registration/udm_attributes=description,title'])
	ucr.handler_set(['umc/self-service/account-registration/udm_attributes/required=title'])
	_navigate_self_service(selenium, 'createaccount')
	selenium.wait_for_text('Create an account', 2)
	selenium.wait_until_element_visible('//label[contains(text(), "Email")]')
	selenium.wait_until_element_visible('//label[contains(text(), "Password")]')
	selenium.wait_until_element_visible('//label[contains(text(), "Password (retype)")]')
	selenium.wait_until_element_visible('//label[contains(text(), "Description")]')
	selenium.wait_until_element_visible('//label[contains(text(), "Title")]')


# tests whether a user is created and put into the right container
@pytest.mark.parametrize("verification_process", ['automatic', 'manual'])
def test_user_creation(selenium, mails, get_registration_info, verification_process):
	# creates user
	_navigate_self_service(selenium, 'createaccount')
	info = get_registration_info()
	time.sleep(2)
	_enter_attributes(selenium, info['attributes'])
	time.sleep(2)
	utils.verify_ldap_object(info['dn'], {
		'univentionRegisteredThroughSelfService': ['TRUE'],
		'univentionPasswordRecoveryEmailVerified': ['FALSE'],
	}, retry_count=1, delay=2)
	selenium.wait_for_text('Account creation successful')
	# tests email
	mail = _get_mail(mails)
	if verification_process == 'automatic':
		# tests automatic link
		selenium.driver.get(mail['auto_verify_link'])
		selenium.wait_until_standby_animation_appears_and_disappears()
		click_submit(selenium)
		time.sleep(2)
	elif verification_process == 'manual':
		# tests manual link
		selenium.driver.get(mail['verify_link'])
		print(mail['verify_data']['token'])
		_enter_attributes(selenium, {
			'username': mail['verify_data']['username'],
			'token': mail['verify_data']['token'],
		})
	selenium.wait_for_text('Your account has been successfully verified')
	utils.verify_ldap_object(info['dn'], {
		'univentionRegisteredThroughSelfService': ['TRUE'],
		'univentionPasswordRecoveryEmailVerified': ['TRUE'],
	}, retry_count=1, delay=2)


def test_account_verifyaccount_page_errors(selenium, udm, get_registration_info):
	_navigate_self_service(selenium, 'verifyaccount')
	_enter_attributes(selenium, {
		'username': 'not_existing',
		'token': 'xxxx'
	})
	time.sleep(2)
	selenium.wait_for_text('The account could not be verified. Please verify your input.')
	_navigate_self_service(selenium, 'verifyaccount')
	_enter_attributes(selenium, {
		'username': 'not_existing'
	})
	selenium.wait_for_text('The verification token could not be sent. Please verify your input.')
	_, username = udm.create_user(**{'PasswordRecoveryEmail': None})
	_navigate_self_service(selenium, 'verifyaccount')
	_enter_attributes(selenium, {
		'username': username,
		'token': 'xxxx'
	})
	selenium.wait_for_text('The token you supplied is either expired or invalid. Please request a new one.')


def test_request_new_token(selenium, mails, get_registration_info):
	_navigate_self_service(selenium, 'createaccount')
	info = get_registration_info()
	_enter_attributes(selenium, info['attributes'])
	_navigate_self_service(selenium, 'verifyaccount')
	time.sleep(2)
	_enter_attributes(selenium, {
		'username': info['attributes']['username'],
	})
	time.sleep(3)
	selenium.wait_for_text('Please follow the instructions in the email to verify your account')
	mail = _get_mail(mails)
	selenium.driver.refresh()
	selenium.driver.get(mail['auto_verify_link'])
	selenium.wait_until_standby_animation_appears_and_disappears()
	click_submit(selenium)
	selenium.wait_for_text('Your account has been successfully verified')


def test_next_steps(selenium, mails, ucr, get_registration_info):
	ucr.handler_set(['umc/self-service/account-verification/next-steps=Foo Bar'])
	_navigate_self_service(selenium, 'createaccount')
	info = get_registration_info()
	_enter_attributes(selenium, info['attributes'])
	selenium.wait_until_standby_animation_appears_and_disappears()
	mail = _get_mail(mails)
	selenium.driver.get(mail['auto_verify_link'])
	click_submit(selenium)
	time.sleep(1)
	selenium.wait_for_text('Your account has been successfully verified')


@pytest.mark.parametrize("change_email", [True, False])
def test_email_change(selenium, mails, get_registration_info, change_email):
	_navigate_self_service(selenium, 'createaccount')
	info = get_registration_info()
	_enter_attributes(selenium, info['attributes'])
	selenium.wait_until_standby_animation_appears_and_disappears()
	mail = _get_mail(mails)
	selenium.driver.get(mail['auto_verify_link'])
	selenium.wait_until_standby_animation_appears_and_disappears()
	click_submit(selenium)
	utils.verify_ldap_object(info['dn'], {
		'univentionRegisteredThroughSelfService': ['TRUE'],
		'univentionPasswordRecoveryEmailVerified': ['TRUE'],
	}, retry_count=1, delay=2)
	_navigate_self_service(selenium, 'protectaccount')
	selenium.wait_until_standby_animation_appears_and_disappears()
	selenium.enter_input('username', info['attributes']['username'])
	selenium.enter_input('password', info['attributes']['password'])
	click_submit(selenium)
	selenium.wait_for_text('Email')
	if change_email:
		new_email = 'foo@bar.com'
		e = selenium.driver.find_element_by_name('email')
		e.clear()
		e.send_keys(new_email)
		e = selenium.driver.find_element_by_name('email--retype')
		e.clear()
		e.send_keys(new_email)
		click_submit(selenium)
		time.sleep(2)
		selenium.wait_for_text('Your account recovery options have been updated.. Your account has to be verified again')
	else:
		click_submit(selenium)
		with pytest.raises(TimeoutException):
			selenium.wait_for_text('Your account recovery options have been updated.. Your account has to be verified again')
