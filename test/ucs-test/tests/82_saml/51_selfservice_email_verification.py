#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: SSO Login at UMC as Service Provider
## tags: [saml]
## join: true
## exposure: dangerous
## packages:
##   - univention-self-service-passwordreset-umc
## tags:
##  - skip_admember

from __future__ import print_function
import pytest

import univention.testing.udm as udm_test
import univention.testing.ucr as ucr_test
from univention.config_registry import handler_set

import samltest


def test_check_disabled_email_unverified():
	with ucr_test.UCSTestConfigRegistry():
		handler_set(['saml/idp/selfservice/check_email_verification=False'])
		check_login(activated_email=False)


def test_check_disabled_email_verified():
	with ucr_test.UCSTestConfigRegistry():
		handler_set(['saml/idp/selfservice/check_email_verification=False'])
		check_login(activated_email=True)


def test_check_enabled_email_unverified():
	with ucr_test.UCSTestConfigRegistry():
		handler_set(['saml/idp/selfservice/check_email_verification=True'])
		with pytest.raises(samltest.SamlAccountNotVerified):
			check_login(activated_email=False)


def test_check_enabled_email_verified():
	with ucr_test.UCSTestConfigRegistry():
		handler_set(['saml/idp/selfservice/check_email_verification=True'])
		check_login(activated_email=True)


def check_login(activated_email=False):
	with udm_test.UCSTestUDM() as udm:
		testcase_user_name = udm.create_user(
			RegisteredThroughSelfService='TRUE',
			PasswordRecoveryEmailVerified='TRUE' if activated_email else 'FALSE',
		)[1]
		SamlSession = samltest.SamlTest(testcase_user_name, 'univention')
		SamlSession.login_with_new_session_at_IdP()
		SamlSession.test_login()
		SamlSession.logout_at_IdP()
		SamlSession.test_logout_at_IdP()
		SamlSession.test_logout()
