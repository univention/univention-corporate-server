#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Tests the Univention Self Service
## tags: [apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-self-service
##   - univention-self-service-passwordreset-umc

import pytest
from test_self_service import SelfServiceUser

from univention.lib.umc import HTTPError
from univention.testing import utils


error_get_contact = 'Either username or password is incorrect or you are not allowed to use this service.'
error_set_contact = 'Either username or password is incorrect or you are not allowed to use this service.'
send_token_message = 'A message containing a token has been sent to the user (if the user exists and is allowed to use this service).'
error_set_password = 'The token you supplied is either expired or invalid. Please request a new one.'


def test_blacklist():
    account = utils.UCSTestDomainAdminCredentials()
    user = SelfServiceUser(account.username, account.bindpw, language='en-US')

    with pytest.raises(HTTPError) as exc:
        user.get_contact()
    assert error_get_contact in str(exc.value)

    with pytest.raises(HTTPError) as exc:
        user.set_contact()
    assert error_set_contact in str(exc.value)

    # due to Bug #55346 get_reset_methods send_token always returns the same result
    assert user.get_reset_methods() == ["email"]

    message = user.request('passwordreset/send_token', method='email').data['message']
    assert message == send_token_message

    with pytest.raises(HTTPError) as exc:
        user.set_password(token='A', password='B')
    assert error_set_password in str(exc.value)
