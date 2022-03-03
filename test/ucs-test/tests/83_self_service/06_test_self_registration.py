#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
# -*- coding: utf-8 -*-
## desc: test self registration
## tags: [apptest]
## packages:
##  - univention-self-service
##  - univention-self-service-passwordreset-umc
## roles-not:
##  - memberserver
##  - basesystem
## join: true
## exposure: dangerous

import datetime
import email
from urllib.parse import parse_qs, urlparse

import pytest
from test_self_service import capture_mails

import univention.testing.strings as uts
import univention.testing.utils as utils
from univention.admin.uexceptions import noObject
from univention.admin.uldap import getAdminConnection
from univention.config_registry import handler_set as hs
from univention.lib.umc import HTTPError
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.umc import Client
from univention.udm import UDM

MAILS_TIMEOUT = 5


@pytest.fixture(scope="module", autouse=True)
def activate_self_registration():
	with UCSTestConfigRegistry() as ucr:
		hs(['umc/self-service/account-registration/backend/enabled=true'])
		hs(['umc/self-service/account-registration/frontend/enabled=true'])
		hs(['umc/self-service/account-verification/backend/enabled=true'])
		hs(['umc/self-service/account-verification/frontend/enabled=true'])
		hs(['umc/self-service/account-deregistration/enabled=true'])
		yield ucr


@pytest.fixture
def readudm():
	return UDM.machine().version(2)


@pytest.fixture
def mails():
	with capture_mails(timeout=MAILS_TIMEOUT) as mails:
		yield mails


@pytest.fixture
def umc_client():
	return Client(language="en_US")


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
	mail = email.message_from_string(mails.data[idx])
	body = mail.get_payload(decode=True).decode('utf-8')
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
			'token': verify_params.get('token', [''])[0],
			'method': verify_params.get('method', [''])[0],
		}
	}


def test_user_creation(umc_client, mails, get_registration_info):
	info = get_registration_info()
	umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	utils.verify_ldap_object(info['dn'], {
		'univentionPasswordSelfServiceEmail': [info['attributes']['PasswordRecoveryEmail']],
		'sn': [info['attributes']['lastname']],
		'uid': [info['attributes']['username']],
		'univentionPasswordRecoveryEmailVerified': ['FALSE'],
		'univentionRegisteredThroughSelfService': ['TRUE'],
	})
	verify_data = _get_mail(mails)['verify_data']
	res = umc_client.umc_command('passwordreset/verify_contact', verify_data)
	assert res.result['successType'] == 'VERIFIED'
	utils.verify_ldap_object(info['dn'], {'univentionPasswordRecoveryEmailVerified': ['TRUE']})
	res = umc_client.umc_command('passwordreset/verify_contact', verify_data)
	assert res.result['successType'] == 'ALREADY_VERIFIED'


def test_next_steps_ucr_var(umc_client, mails, ucr, get_registration_info):
	info = get_registration_info()
	umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	verify_data = _get_mail(mails)['verify_data']
	res = umc_client.umc_command('passwordreset/verify_contact', verify_data)
	assert res.result['data']['nextSteps'] == "Continue to the <a href='/univention/portal'>Univention Portal</a>."
	ucr.handler_set(['umc/self-service/account-verification/next-steps=foobar'])
	res = umc_client.umc_command('passwordreset/verify_contact', verify_data)
	assert res.result['data']['nextSteps'] == 'foobar'


def test_registration_backend_enabled_ucr_var(umc_client, ucr, get_registration_info):
	ucr.handler_set(['umc/self-service/account-registration/backend/enabled=false'])
	info = get_registration_info()
	with pytest.raises(HTTPError) as excinfo:
		umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	assert excinfo.value.message == 'The account registration was disabled via the Univention Configuration Registry.'


def test_verification_backend_enabled_ucr_var(umc_client, mails, ucr, get_registration_info):
	ucr.handler_set(['umc/self-service/account-verification/backend/enabled=false'])
	info = get_registration_info()
	umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	verify_data = _get_mail(mails)['verify_data']
	with pytest.raises(HTTPError) as excinfo:
		umc_client.umc_command('passwordreset/verify_contact', verify_data)
	assert excinfo.value.message == 'The account verification was disabled via the Univention Configuration Registry.'


def test_udm_attributes_ucr_var(umc_client, readudm, ucr, get_registration_info):
	# test that only the attributes in umc/self-service/account-registration/udm_attributes can be set
	ucr.handler_set(['umc/self-service/account-registration/udm_attributes=lastname,username,description'])
	info = get_registration_info(attributes={
		'description': 'This is description',
		'uidNumber': '1',
	})
	umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	utils.verify_ldap_object(info['dn'], {
		'description': [info['attributes']['description']],
	})
	u = readudm.obj_by_dn(info['dn'])
	assert u.props.uidNumber != info['attributes']['uidNumber']


def test_udm_attributes_required_ucr_var(umc_client, ucr, get_registration_info):
	ucr.handler_set(['umc/self-service/account-registration/udm_attributes=lastname,username,title', 'umc/self-service/account-registration/udm_attributes/required=lastname,username,title'])
	info = get_registration_info()
	del info['data']['attributes']['username']
	with pytest.raises(HTTPError) as excinfo:
		umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	assert excinfo.value.message.startswith('The account could not be created:\nInformation provided is not sufficient. The following properties are missing:\n')
	for attr in ['username', 'title']:
		assert '\n%s' % (attr,) in excinfo.value.message


def test_usercontainer_ucr_var(umc_client, get_registration_info):
	info = get_registration_info(container_without_base='cn=users')
	umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	utils.verify_ldap_object(info['dn'], {
		'univentionPasswordRecoveryEmailVerified': ['FALSE'],
		'univentionRegisteredThroughSelfService': ['TRUE'],
	})


def test_usercontainer_ucr_var_not_existing(umc_client, get_registration_info):
	info = get_registration_info(container_without_base='cn=not_existing')
	with pytest.raises(HTTPError) as excinfo:
		umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	container_dn = ','.join(info['dn'].split(',')[1:])
	msg = 'The container "{}" set by the "umc/self-service/account-registration/usercontainer" UCR variable does not exist. A user account can not be created. Please contact your system administrator.'.format(container_dn)
	assert excinfo.value.message == msg


def test_usertemplate_ucr_var(umc_client, udm, ucr, get_registration_info):
	# TODO test all fields
	template_dn = udm.create_object('settings/usertemplate', name=uts.random_name(), title="<username>")
	ucr.handler_set(['umc/self-service/account-registration/usertemplate=%s' % (template_dn,)])
	info = get_registration_info()
	umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	utils.verify_ldap_object(info['dn'], {
		'univentionPasswordRecoveryEmailVerified': ['FALSE'],
		'univentionRegisteredThroughSelfService': ['TRUE'],
		'title': [info['attributes']['username']],
	})


def test_usertemplate_ucr_var_not_existing(umc_client, ucr, get_registration_info):
	usertemplate_dn = "cn=not_existing,dc=foo,dc=bar"
	ucr.handler_set(['umc/self-service/account-registration/usertemplate={}'.format(usertemplate_dn)])
	info = get_registration_info()
	with pytest.raises(HTTPError) as excinfo:
		umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	msg = (
		'The user template "{}" set by the "umc/self-service/account-registration/usertemplate" UCR variable does not exist. '
		'A user account can not be created. Please contact your system administrator.'
	).format(usertemplate_dn)
	assert excinfo.value.message == msg


def test_text_file_ucr_var(umc_client, mails, ucr, get_registration_info, tmpdir):
	file_path = tmpdir.mkdir("sub").join("mail_body.txt")
	mail_body = "This is mail"
	file_path.write(mail_body)
	ucr.handler_set(['umc/self-service/account-verification/email/text_file=%s' % (file_path,)])
	info = get_registration_info()
	umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	assert _get_mail(mails)['body'] == mail_body


def test_token_length_ucr_var(umc_client, mails, ucr, get_registration_info):
	token_length = 4
	ucr.handler_set(['umc/self-service/account-verification/email/token_length=%s' % (token_length,)])
	info = get_registration_info()
	umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	verify_data = _get_mail(mails)['verify_data']
	assert len(verify_data['token']) == token_length


def test_webserver_addresss_ucr_var(umc_client, mails, ucr, get_registration_info):
	webserver_address = 'foo.bar.com'
	ucr.handler_set(['umc/self-service/account-verification/email/webserver_address=%s' % (webserver_address,)])
	info = get_registration_info()
	umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	mail = _get_mail(mails)
	assert mail['auto_verify_link'].startswith('https://%s' % (webserver_address,))
	assert mail['verify_link'].startswith('https://%s' % (webserver_address,))


def test_sender_address_ucr_var(umc_client, mails, ucr, get_registration_info):
	sender_address = 'foobar@mail.com'
	ucr.handler_set(['umc/self-service/account-verification/email/sender_address=%s' % (sender_address,)])
	info = get_registration_info()
	umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	mail = _get_mail(mails)['mail']
	assert mail.get('from') == sender_address


def test_send_verification_token(umc_client, mails, ucr, udm, get_registration_info):
	ucr.handler_set(['umc/self-service/account-verification/backend/enabled=false'])
	with pytest.raises(HTTPError) as excinfo:
		umc_client.umc_command('passwordreset/send_verification_token', {'username': 'xxxxx'})
	assert excinfo.value.message == 'The account verification was disabled via the Univention Configuration Registry.'
	ucr.handler_set(['umc/self-service/account-verification/backend/enabled=true'])
	res = umc_client.umc_command('passwordreset/send_verification_token', {'username': 'xxxxx'})
	# user should not exist
	assert res.result['failType'] == 'INVALID_INFORMATION'
	_, username = udm.create_user(**{'PasswordRecoveryEmail': None})
	res = umc_client.umc_command('passwordreset/send_verification_token', {'username': username})
	# user has no email
	assert res.result['failType'] == 'INVALID_INFORMATION'
	mail = 'foo@bar.com'
	_, username = udm.create_user(**{'PasswordRecoveryEmail': mail})
	res = umc_client.umc_command('passwordreset/send_verification_token', {'username': username})
	assert res.result['data']['username'] == username
	mail = _get_mail(mails)
	assert mail['verify_data']['username'] == username


def test_deregistration_enabled(umc_client, ucr):
	ucr.handler_set(['umc/self-service/account-deregistration/enabled=false'])
	with pytest.raises(HTTPError) as excinfo:
		umc_client.umc_command('passwordreset/deregister_account', {
			'username': 'xxx',
			'password': 'xxx'
		})
	assert excinfo.value.message == 'The account deregistration was disabled via the Univention Configuration Registry.'


def test_deregistration_wrong_auth(umc_client, ucr):
	with pytest.raises(HTTPError) as excinfo:
		umc_client.umc_command('passwordreset/deregister_account', {
			'username': 'xxx',
			'password': 'xxx'
		})
	assert excinfo.value.message == 'Either username or password is incorrect or you are not allowed to use this service.'


def test_deregistration(umc_client, mails, udm, readudm):
	password = 'univention'
	dn, username = udm.create_user(**{
		'PasswordRecoveryEmail': 'root@localhost',
		'password': password,
	})
	utils.verify_ldap_object(dn, {
		'univentionDeregisteredThroughSelfService': [],
		'univentionDeregistrationTimestamp': []
	})
	timestamp = datetime.datetime.strftime(datetime.datetime.utcnow(), '%Y%m%d%H%M%SZ')
	umc_client.umc_command('passwordreset/deregister_account', {
		'username': username,
		'password': password
	})
	user = readudm.obj_by_dn(dn)
	assert user.props.disabled is True
	assert user.props.DeregisteredThroughSelfService == 'TRUE'
	assert user.props.DeregistrationTimestamp.startswith(timestamp[:3])  # checking seconds from the timestamp is too flaky
	mail = _get_mail(mails)
	with open('/usr/share/univention-self-service/email_bodies/deregistration_notification_email_body.txt', 'r') as fd:
		expected_body = fd.read().format(username=username)
	assert mail['body'].strip() == expected_body.strip()


def test_deregistration_text_file_ucr_var(umc_client, mails, ucr, udm, tmpdir):
	file_path = tmpdir.mkdir("sub").join("mail_body.txt")
	mail_body = "This is mail"
	file_path.write(mail_body)
	ucr.handler_set(['umc/self-service/account-deregistration/email/text_file=%s' % (file_path,)])
	password = 'univention'
	_, username = udm.create_user(**{
		'PasswordRecoveryEmail': 'root@localhost',
		'password': password,
	})
	umc_client.umc_command('passwordreset/deregister_account', {
		'username': username,
		'password': password
	})
	assert _get_mail(mails)['body'] == mail_body


def test_deregistration_sender_address_ucr_var(umc_client, mails, ucr, udm):
	sender_address = 'foobar@mail.com'
	ucr.handler_set(['umc/self-service/account-deregistration/email/sender_address=%s' % (sender_address,)])
	password = 'univention'
	_, username = udm.create_user(**{
		'PasswordRecoveryEmail': 'root@localhost',
		'password': password,
	})
	umc_client.umc_command('passwordreset/deregister_account', {
		'username': username,
		'password': password
	})
	mail = _get_mail(mails)['mail']
	assert mail.get('from') == sender_address
