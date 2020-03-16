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
from univention.lib.umc import Client
from univention.config_registry import handler_set

from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.udm import UCSTestUDM
from test_self_service import capture_mails
import univention.testing.strings as uts
import univention.testing.utils as utils


@pytest.fixture
def ucr():
	with UCSTestConfigRegistry() as ucr:
		yield ucr


@pytest.fixture
def testudm():
	with UCSTestUDM() as udm:
		yield udm


@pytest.fixture
def mails_timeout():
	return 5


@pytest.fixture
def mails(mails_timeout):
	with capture_mails(timeout=mails_timeout) as mails:
		yield mails


@pytest.fixture
def umc_client():
	return Client()


@pytest.fixture
def registration_info_different_container(ucr):
	container = 'cn=users,%s' % (ucr.get('ldap/base'),)
	handler_set(['umc/self-service/account-registration/usercontainer=%s' % (container,)])
	ucr.load()
	data = _registration_info(ucr)
	yield data
	_cleanup_registration_info(data)


@pytest.fixture
def registration_info(ucr):
	data = _registration_info(ucr)
	yield data
	_cleanup_registration_info(data)


def _registration_info(ucr):
	container = ucr.get('umc/self-service/account-registration/usercontainer')
	username = uts.random_name()
	dn = "uid=%s,%s" % (username, container)
	data = {
		'attributes': {
			'username': username,
			'lastname': username,
			'password': 'univention',
			'PasswordRecoveryEmail': 'root@localhost'
		}
	}
	return {
		'dn': dn,
		'data': data
	}


def _cleanup_registration_info(data):
	lo, po = getAdminConnection()
	try:
		lo.delete(data['dn'])
	except noObject:
		pass


def _get_mail(mails):
	mail = email.message_from_string(mails.data and mails.data[0])
	body = mail.get_payload(decode=True)
	assert body, 'No email has been received in %s seconds' % (mails_timeout,)
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


def test_user_creation(mails, mails_timeout, umc_client, registration_info):
	umc_client.umc_command('passwordreset/create_self_registered_account', registration_info['data'])
	utils.verify_ldap_object(registration_info['dn'], {
		'univentionPasswordRecoveryEmailVerified': ['FALSE'],
		'univentionRegisteredThroughSelfService': ['TRUE'],
	})
	params = _get_mail(mails)['params']
	umc_client.umc_command('passwordreset/verify_contact', {
		'username': params['username'][0],
		'token': params['token'][0],
		'method': params['method'][0],
	})
	utils.verify_ldap_object(registration_info['dn'], {'univentionPasswordRecoveryEmailVerified': ['TRUE']})


def test_container(umc_client, registration_info_different_container):
	umc_client.umc_command('passwordreset/create_self_registered_account', registration_info_different_container['data'])
	utils.verify_ldap_object(registration_info_different_container['dn'], {
		'univentionPasswordRecoveryEmailVerified': ['FALSE'],
		'univentionRegisteredThroughSelfService': ['TRUE'],
	})


def test_template(umc_client, testudm, ucr, registration_info):
	template_dn = testudm.create_object('settings/usertemplate', name=uts.random_name(), title="<username>")
	handler_set(['umc/self-service/account-registration/usertemplate=%s' % (template_dn,)])
	umc_client.umc_command('passwordreset/create_self_registered_account', registration_info['data'])
	utils.verify_ldap_object(registration_info['dn'], {
		'univentionPasswordRecoveryEmailVerified': ['FALSE'],
		'univentionRegisteredThroughSelfService': ['TRUE'],
		'title': [registration_info['data']['attributes']['username']],
	})


def test_email_test_file(umc_client, mails, ucr, registration_info, tmpdir):
	p = tmpdir.mkdir("sub").join("body.txt")
	body = "This is mail"
	p.write(body)
	handler_set(['umc/self-service/account-verification/email/text_file=%s' % (p,)])
	umc_client.umc_command('passwordreset/create_self_registered_account', registration_info['data'])
	mail_body = _get_mail(mails)['body']
	assert mail_body == body


def test_email_token_length(umc_client, mails, ucr, registration_info):
	length = 4
	handler_set(['umc/self-service/account-verification/email/token_length=%s' % (length,)])
	umc_client.umc_command('passwordreset/create_self_registered_account', registration_info['data'])
	params = _get_mail(mails)['params']
	assert len(params['token'][0]) == length


def test_email_webserver_addresss(umc_client, mails, ucr, registration_info):
	address = 'foo.bar.com'
	handler_set(['umc/self-service/account-verification/email/webserver_address=%s' % (address,)])
	umc_client.umc_command('passwordreset/create_self_registered_account', registration_info['data'])
	link = _get_mail(mails)['link']
	assert link.startswith('https://%s' % (address,))


def test_email_sender_address(umc_client, mails, ucr, registration_info):
	address = 'foobar@mail.com'
	handler_set(['umc/self-service/account-verification/email/sender_address=%s' % (address,)])
	umc_client.umc_command('passwordreset/create_self_registered_account', registration_info['data'])
	mail = _get_mail(mails)['mail']
	assert mail.get('from') == address
