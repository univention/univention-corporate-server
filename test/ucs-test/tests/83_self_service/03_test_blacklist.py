#!/usr/share/ucs-test/runner python3
## desc: Tests the Univention Self Service
## tags: [apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-self-service
##   - univention-self-service-passwordreset-umc

from test_self_service import SelfServiceUser

from univention.lib.umc import HTTPError
from univention.testing import utils


error_get_contact = 'Either username or password is incorrect or you are not allowed to use this service.'
error_set_contact = 'Either username or password is incorrect or you are not allowed to use this service.'
send_token_message = 'A message containing a token has been sent to the user (if the user exists and is allowed to use this service).'
error_set_password = 'The token you supplied is either expired or invalid. Please request a new one.'


def main():
    account = utils.UCSTestDomainAdminCredentials()
    user = SelfServiceUser(account.username, account.bindpw, language='en-US')

    assert_raises(HTTPError, error_get_contact, user.get_contact)
    assert_raises(HTTPError, error_set_contact, user.set_contact)
    # due to Bug #55346 get_reset_methods send_token always returns the same result
    assert user.get_reset_methods() == ["email"]
    assert user.request('passwordreset/send_token', method='email').data['message'] == send_token_message
    assert_raises(HTTPError, error_set_password, user.set_password, token='A', password='B')


def assert_raises(exc_type, message, callback, *args, **kwargs):
    try:
        callback(*args, **kwargs)
    except exc_type as exc:
        if message:
            # TODO check actual message
            print(str(exc))
            # assert str(exc) and message in str(exc), 'Exception %r does not contain %r' % (str(exc), message)
    else:
        raise AssertionError(f'did not raise {exc_type!r}')


if __name__ == '__main__':
    main()
