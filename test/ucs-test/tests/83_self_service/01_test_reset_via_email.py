#!/usr/share/ucs-test/runner python3
## desc: Tests the Univention Self Service
## tags: [apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-self-service
##   - univention-self-service-passwordreset-umc

import subprocess
import time
from email import header

import pytest

from test_self_service import capture_mails, self_service_user
from univention.testing.strings import random_string, random_username


@pytest.fixture(scope='class')
def close_all_processes():
	"""force all module processes to close"""
	yield
	subprocess.call(['systemctl', 'restart', 'univention-management-console-server'], close_fds=True)
	time.sleep(3)


@pytest.mark.parametrize(
	'login_with_mail, subject', [
		(False, False),
		(True, 'Passwort zurücksetzen'),
	]
)
def test_reset_via_email(ucr, login_with_mail, subject):
	# don't explicitly set the default to test non-existant ucr variable
	if subject:
		ucr.handler_set([f"umc/self-service/passwordreset/email/subject={subject}"])
	else:
		subject = "Password reset"

	ucr.handler_set(["umc/self-service/passwordreset/limit/per_user/minute=120"])
	reset_mail_address = '%s@%s' % (random_username(), random_username())
	with self_service_user(mailPrimaryAddress=reset_mail_address) as user:
		if login_with_mail:
			user.username = reset_mail_address
			print('test with login per mail address')
		else:
			print('test with login per username')

		# def contact(user): @florian: will be deleted!
		email = 'foo@example.com'
		mobile = '+0176123456'
		user.set_contact(email=email, mobile=mobile)
		assert user.get_contact().get('email') == email, 'Setting mail address failed'

		# def reset_method_email(user): @florian will be deleted!
		email = 'testuser@example.com'
		user.set_contact(email=email)
		assert 'email' in user.get_reset_methods()

		timeout = 5
		with capture_mails(timeout=timeout) as mails:
			user.send_token('email')

		mail = mails.data and mails.data[0]
		assert mail, 'No email has been received in %s seconds' % (timeout,)

		# test configurable mail header
		# decode special characters from MIME format to utf-8
		mail_subject = header.decode_header(mail)[1][0].decode('utf-8')
		assert mail_subject == subject

		# test password change
		token = mail.split('and enter the following token manually:')[-1].split('Greetings from your password self service system.')[0].strip()
		assert token, 'Could not parse token from mail. Is there a token in it? %r' % (mail,)

		user.password = random_string()
		user.set_password(token, user.password)

		assert user.get_contact() == {'email': email}, 'Login with the new password seems to have failed'

		time.sleep(2)
