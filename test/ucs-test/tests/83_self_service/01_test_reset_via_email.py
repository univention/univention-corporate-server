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
import pytest

from test_self_service import capture_mails, self_service_user

from univention.testing.strings import random_username, random_string
from univention.testing.utils import package_installed


@pytest.fixture(scope='class')
def close_all_processes():
	"""force all module processes to close"""
	yield
	subprocess.call(['systemctl', 'restart', 'univention-management-console-server'], close_fds=True)
	time.sleep(3)


@pytest.mark.parametrize(
	'login_with_mail', [False, True],
	ids=['test with login per username', 'test with login per mail address']
)
def test_reset_via_email(ucr, login_with_mail):
	ucr.handler_set(["umc/self-service/passwordreset/limit/per_user/minute=120"])
	user_mail = '%s@%s' % (random_username(), random_username())
	with self_service_user(mailPrimaryAddress=user_mail) as user:
		if login_with_mail:
			user.username = user_mail

		# def contact(user):
		email = 'foo@example.com'
		mobile = '+0176123456'
		user.set_contact(email=email, mobile=mobile)
		assert user.get_contact().get('email') == email, 'Setting mail address failed'

		# def reset_method_email(user):
		email = 'testuser@example.com'
		user.set_contact(email=email)
		assert 'email' in user.get_reset_methods()

		timeout = 5
		with capture_mails(timeout=timeout) as mails:
			user.send_token('email')

		mail = mails.data and mails.data[0]

		assert mail, 'No email has been received in %s seconds' % (timeout,)
		token = mail.split('and enter the following token manually:')[-1].split('Greetings from your password self service system.')[0].strip()
		assert token, 'Could not parse token from mail. Is there a token in it? %r' % (mail,)

		user.password = random_string()
		user.set_password(token, user.password)

		assert user.get_contact() == {'email': email}, 'Login with the new password seems to have failed'

		time.sleep(2)
