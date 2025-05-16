#!/usr/share/ucs-test/runner python3
## desc: Tests rate limit of Univention Self Service
## tags: [apptest, SKIP]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-self-service
##   - univention-self-service-passwordreset-umc

import contextlib
from subprocess import call
from time import sleep

from test_self_service import capture_mails, self_service_user

from univention.config_registry import handler_set, handler_unset
from univention.lib.umc import ServiceUnavailable
from univention.testing.ucr import UCSTestConfigRegistry as UCR


LIMIT_TOTAL_MINUTE = 'umc/self-service/passwordreset/limit/total/minute'
LIMIT_TOTAL_HOUR = 'umc/self-service/passwordreset/limit/total/hour'
LIMIT_TOTAL_DAY = 'umc/self-service/passwordreset/limit/total/day'
LIMIT_USER_MINUTE = 'umc/self-service/passwordreset/limit/per_user/minute'
LIMIT_USER_HOUR = 'umc/self-service/passwordreset/limit/per_user/hour'
LIMIT_USER_DAY = 'umc/self-service/passwordreset/limit/per_user/day'

TRUST_X_FORWARDED_HOST_UCR = 'umc/self-service/rate-limit/trust-x-forwarded-host'
TRUSTED_HOSTS_UCR = 'umc/self-service/rate-limit/trusted-hosts'


class Main:

    def __init__(self):
        handler_unset([LIMIT_TOTAL_MINUTE, LIMIT_TOTAL_HOUR, LIMIT_TOTAL_DAY, LIMIT_USER_MINUTE, LIMIT_USER_HOUR, LIMIT_USER_DAY, TRUST_X_FORWARDED_HOST_UCR, TRUSTED_HOSTS_UCR])
        with capture_mails():
            self.test_total_limits()
            self.test_user_limits()
            self.test_trusted_host_bypass_xfh_true_host_trusted()
            self.test_rate_limited_xfh_true_host_not_trusted()
            self.test_rate_limited_xfh_true_no_xfh_header()
            self.test_rate_limited_xfh_false_xfh_header_ignored()
            self.test_trusted_host_bypass_xfh_list_first_trusted()
            self.test_rate_limited_xfh_list_first_not_trusted()
            self.test_multiple_trusted_hosts_in_ucr_config()

    def test_total_limits(self):
        print('########################### test_total_limits ##############################')
        cuser = self_service_user(email='user@localhost')
        with cuser as user, set_limits(total_minute=1):
            assert fail_after(user, 1, 'one minute'), LIMIT_TOTAL_MINUTE
            wait(minutes=1)
            dont_fail(user)

    def test_user_limits(self):
        print('########################### test_user_limits ##############################')
        cuser1 = self_service_user(email='user1@localhost')
        cuser2 = self_service_user(email='user2@localhost')
        limits = set_limits(total_minute=7, user_minute=3)
        with cuser1 as user1, cuser2 as user2, limits:
            assert fail_after(user1, 3, 'one minute')
            assert fail_after(user2, 2, 'one minute')
            wait(minutes=1)
            dont_fail(user2)

    def test_trusted_host_bypass_xfh_true_host_trusted(self):
        print('##### test_trusted_host_bypass_xfh_true_host_trusted #####')
        test_email = "bypass@localhost"
        with set_limits(total_minute=1), \
             set_trust_configs(trust_x_forwarded=True, trusted_hosts_list=["proxy.example.com"]):
            # Assuming self_service_user can take a 'headers' kwarg
            # and the 'email' param is used as the username for send_token
            user_ctx = self_service_user(email=test_email, headers={'X-Forwarded-Host': 'proxy.example.com'})
            with user_ctx as user:
                make_requests_without_fail(user, 2)  # Should make 2 requests successfully

    def test_rate_limited_xfh_true_host_not_trusted(self):
        print('##### test_rate_limited_xfh_true_host_not_trusted #####')
        test_email = "ratelimit_untrusted_proxy@localhost"
        with set_limits(total_minute=1), \
             set_trust_configs(trust_x_forwarded=True, trusted_hosts_list=["other.proxy.com"]):
            user_ctx = self_service_user(email=test_email, headers={'X-Forwarded-Host': 'untrusted.proxy.com'})
            with user_ctx as user:
                assert fail_after(user, 1, 'one minute')

    def test_rate_limited_xfh_true_no_xfh_header(self):
        print('##### test_rate_limited_xfh_true_no_xfh_header #####')
        test_email = "ratelimit_no_xfh@localhost"
        with set_limits(total_minute=1), \
             set_trust_configs(trust_x_forwarded=True, trusted_hosts_list=["proxy.example.com"]):
            user_ctx = self_service_user(email=test_email, headers=None)  # No X-Forwarded-Host header
            with user_ctx as user:
                assert fail_after(user, 1, 'one minute')

    def test_rate_limited_xfh_false_xfh_header_ignored(self):
        print('##### test_rate_limited_xfh_false_xfh_header_ignored #####')
        test_email = "ratelimit_xfh_false@localhost"
        with set_limits(total_minute=1), \
             set_trust_configs(trust_x_forwarded=False, trusted_hosts_list=["proxy.example.com"]):
            user_ctx = self_service_user(email=test_email, headers={'X-Forwarded-Host': 'proxy.example.com'})
            with user_ctx as user:
                assert fail_after(user, 1, 'one minute')

    def test_trusted_host_bypass_xfh_list_first_trusted(self):
        print('##### test_trusted_host_bypass_xfh_list_first_trusted #####')
        test_email = "bypass_xfh_list@localhost"
        with set_limits(total_minute=1), \
             set_trust_configs(trust_x_forwarded=True, trusted_hosts_list=["first.proxy.com"]):
            user_ctx = self_service_user(email=test_email, headers={'X-Forwarded-Host': 'first.proxy.com, client.actual.ip'})
            with user_ctx as user:
                make_requests_without_fail(user, 2)

    def test_rate_limited_xfh_list_first_not_trusted(self):
        print('##### test_rate_limited_xfh_list_first_not_trusted #####')
        test_email = "ratelimit_xfh_list_untrusted@localhost"
        with set_limits(total_minute=1), \
             set_trust_configs(trust_x_forwarded=True, trusted_hosts_list=["client.actual.ip"]):  # Trust only the second one
            user_ctx = self_service_user(email=test_email, headers={'X-Forwarded-Host': 'first.proxy.com, client.actual.ip'})
            with user_ctx as user:
                assert fail_after(user, 1, 'one minute')  # First proxy in XFH is not trusted

    def test_multiple_trusted_hosts_in_ucr_config(self):
        print('##### test_multiple_trusted_hosts_in_ucr_config #####')
        email1 = "multi_host1@localhost"
        email2 = "multi_host2@localhost"
        email3 = "multi_host3@localhost"  # Untrusted
        with set_limits(total_minute=1), \
             set_trust_configs(trust_x_forwarded=True, trusted_hosts_list=["proxy1.com", " proxy2.com ", "proxy3.com"]):  # Note spaces for robustness
            user1_ctx = self_service_user(email=email1, headers={'X-Forwarded-Host': 'proxy1.com'})
            with user1_ctx as user1:
                make_requests_without_fail(user1, 2)

            user2_ctx = self_service_user(email=email2, headers={'X-Forwarded-Host': 'proxy2.com'})
            with user2_ctx as user2:
                make_requests_without_fail(user2, 2)

            user3_ctx = self_service_user(email=email3, headers={'X-Forwarded-Host': 'proxy4.com'})  # This one is not in the trusted list
            with user3_ctx as user3:
                assert fail_after(user3, 1, 'one minute')


@contextlib.contextmanager
def set_limits(total_minute=None, total_hour=None, total_day=None, user_minute=None, user_hour=None, user_day=None):
    print('setting limit to %s' % locals())
    with UCR(), resetting_limits():
        total_minute = (LIMIT_TOTAL_MINUTE, total_minute)
        total_hour = (LIMIT_TOTAL_HOUR, total_hour)
        total_day = (LIMIT_USER_DAY, total_day)
        user_minute = (LIMIT_USER_MINUTE, user_minute)
        user_hour = (LIMIT_USER_HOUR, user_hour)
        user_day = (LIMIT_USER_DAY, user_day)
        args = [total_minute, total_hour, total_day, user_minute, user_hour, user_day]
        handler_set([f'{key}={val}' for key, val in args if val is not None])
        handler_unset([key for key, val in args if val is None])
        yield


@contextlib.contextmanager
def set_trust_configs(trust_x_forwarded=None, trusted_hosts_list=None):
    # Ensure UCR is in a context if not already handled by an outer scope
    # For these tests, set_limits already establishes a UCR context.
    print(f'Setting trust configs: trust_x_forwarded={trust_x_forwarded}, trusted_hosts_list={trusted_hosts_list}')
    original_trust_x = UCR().get(TRUST_X_FORWARDED_HOST_UCR, None)
    original_trusted_hosts = UCR().get(TRUSTED_HOSTS_UCR, None)

    ucr_to_set = []
    ucr_to_unset = []

    if trust_x_forwarded is not None:
        ucr_to_set.append(f'{TRUST_X_FORWARDED_HOST_UCR}={str(trust_x_forwarded).lower()}')
    else:
        ucr_to_unset.append(TRUST_X_FORWARDED_HOST_UCR)

    if trusted_hosts_list is not None:
        ucr_to_set.append(f'{TRUSTED_HOSTS_UCR}={",".join(trusted_hosts_list)}')
    else:
        ucr_to_unset.append(TRUSTED_HOSTS_UCR)

    if ucr_to_set:
        handler_set(ucr_to_set)
    if ucr_to_unset:
        handler_unset(ucr_to_unset)

    reset_server_limits_for_trust_config()  # Restart UMC server to pick up new trust UCR values

    try:
        yield
    finally:
        print('Restoring original trust configs')
        ucr_to_set_restore = []
        ucr_to_unset_restore = []

        if original_trust_x is not None:
            ucr_to_set_restore.append(f'{TRUST_X_FORWARDED_HOST_UCR}={original_trust_x}')
        else:
            ucr_to_unset_restore.append(TRUST_X_FORWARDED_HOST_UCR)

        if original_trusted_hosts is not None:
            ucr_to_set_restore.append(f'{TRUSTED_HOSTS_UCR}={original_trusted_hosts}')
        else:
            ucr_to_unset_restore.append(TRUSTED_HOSTS_UCR)

        if ucr_to_set_restore:
            handler_set(ucr_to_set_restore)
        if ucr_to_unset_restore:
            handler_unset(ucr_to_unset_restore)

        reset_server_limits_for_trust_config()  # Restart again to restore original state


def make_requests_without_fail(user, count):
    print(f'Attempting {count} successful requests (bypass expected) for user {user.email_addr if hasattr(user, "email_addr") else user.username}')
    for i in range(count):
        print(f'Attempt (should succeed due to bypass) {i + 1}')
        user.send_token('email')
    print(f'Successfully made {count} requests without rate limiting.')


def fail_after(user, x, retry_after):
    print('We should fail after', x)
    for i in range(x):
        print('Attempt (we shall not fail)', i + 1)
        user.send_token('email')

    try:
        print('We should fail now...')
        user.send_token('email')
    except ServiceUnavailable as exc:
        retry_after = f'Please retry in {retry_after}.'
        assert str(exc)
        print('Yippie, failed!')
        return True
    raise AssertionError('limit not evaluated')


def dont_fail(user):
    print('Now we should not fail anymore')
    user.send_token('email')
    print('Did not fail ;)')


@contextlib.contextmanager
def resetting_limits():
    # This function is called by set_limits
    reset_server_limits_for_rate_config()
    try:
        yield
    finally:
        reset_server_limits_for_rate_config()


def reset_server_limits_for_rate_config():
    print("Resetting server state for rate limit UCR changes (memcached, umc-server restart)")
    # Restart memcached to clear rate limit counters
    assert call(['deb-systemd-invoke', 'restart', 'memcached'], close_fds=True) == 0
    # Restart UMC server for it to re-read rate limit UCR variables during its module init
    assert call(['deb-systemd-invoke', 'restart', 'univention-management-console-server'], close_fds=True) == 0
    print('Waiting for UMC server restart (3s)...')
    sleep(3)


def reset_server_limits_for_trust_config():
    print("Resetting server state for trust UCR changes (umc-server restart only needed)")
    # Only UMC server needs restart to re-read TRUSTED_HOSTS_UCR and TRUST_X_FORWARDED_HOST_UCR
    # Memcached counters are not affected by these settings directly, but by the limits.
    assert call(['deb-systemd-invoke', 'restart', 'univention-management-console-server'], close_fds=True) == 0
    print('Waiting for UMC server restart (3s)...')
    sleep(3)


def wait(minutes):
    # TODO: set the server time otherwise this test blocks that long
    print('Waiting %d minutes' % (minutes,))
    sleep((minutes * 60) + 1)


if __name__ == '__main__':
    Main()
