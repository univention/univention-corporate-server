#!/usr/share/ucs-test/runner /usr/bin/py.test
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

import pytest
import email
from urlparse import urlparse, parse_qs

from univention.admin.uldap import getAdminConnection
from univention.admin.uexceptions import noObject
from univention.config_registry import handler_set as hs
from univention.udm import UDM
from univention.lib.umc import HTTPError

from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.udm import UCSTestUDM
from test_self_service import capture_mails
import univention.testing.strings as uts
import univention.testing.utils as utils
from univention.testing.umc import Client


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
def ucr():
	with UCSTestConfigRegistry() as ucr:
		setattr(ucr, 'handler_set', hs)
		yield ucr


@pytest.fixture
def testudm():
	with UCSTestUDM() as udm:
		yield udm


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
		dn = None

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
		local.dn = "uid=%s,%s" % (_attributes['username'], container_dn)
		return {
			'dn': local.dn,
			'attributes': _attributes,
			'data': {
				'attributes': _attributes
			}
		}
	yield _get_registration_info
	lo, po = getAdminConnection()
	try:
		lo.delete(local.dn)
	except noObject:
		pass


def _get_mail(mails):
	assert mails.data, 'No mails have been captured in %s seconds' % (MAILS_TIMEOUT,)
	mail = email.message_from_string(mails.data[0])
	body = mail.get_payload(decode=True)
	assert body, 'No email has been received in %s seconds' % (MAILS_TIMEOUT,)
	verify_link = ''
	for line in body.split():
		if line.startswith('https://'):
			verify_link = line
			break
	verify_fragment = urlparse(verify_link).fragment
	verify_params = parse_qs(verify_fragment)
	return {
		'mail': mail,
		'body': body,
		'link': verify_link,
		'params': verify_params,
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
	params = _get_mail(mails)['params']
	umc_client.umc_command('passwordreset/verify_contact', {
		'username': params['username'][0],
		'token': params['token'][0],
		'method': params['method'][0],
	})
	utils.verify_ldap_object(info['dn'], {'univentionPasswordRecoveryEmailVerified': ['TRUE']})


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
	params = _get_mail(mails)['params']
	with pytest.raises(HTTPError) as excinfo:
		umc_client.umc_command('passwordreset/verify_contact', {
			'username': params['username'][0],
			'token': params['token'][0],
			'method': params['method'][0],
		})
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


def test_usertemplate_ucr_var(umc_client, testudm, ucr, get_registration_info):
	# TODO test all fields
	template_dn = testudm.create_object('settings/usertemplate', name=uts.random_name(), title="<username>")
	ucr.handler_set(['umc/self-service/account-registration/usertemplate=%s' % (template_dn,)])
	info = get_registration_info()
	umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	utils.verify_ldap_object(info['dn'], {
		'univentionPasswordRecoveryEmailVerified': ['FALSE'],
		'univentionRegisteredThroughSelfService': ['TRUE'],
		'title': [info['attributes']['username']],
	})


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
	params = _get_mail(mails)['params']
	assert len(params['token'][0]) == token_length


def test_webserver_addresss_ucr_var(umc_client, mails, ucr, get_registration_info):
	webserver_address = 'foo.bar.com'
	ucr.handler_set(['umc/self-service/account-verification/email/webserver_address=%s' % (webserver_address,)])
	info = get_registration_info()
	umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	link = _get_mail(mails)['link']
	assert link.startswith('https://%s' % (webserver_address,))


def test_sender_address_ucr_var(umc_client, mails, ucr, get_registration_info):
	sender_address = 'foobar@mail.com'
	ucr.handler_set(['umc/self-service/account-verification/email/sender_address=%s' % (sender_address,)])
	info = get_registration_info()
	umc_client.umc_command('passwordreset/create_self_registered_account', info['data'])
	mail = _get_mail(mails)['mail']
	assert mail.get('from') == sender_address
