#!/usr/share/ucs-test/runner python3
## desc: schedule cronjobs via UCR
## bugs: [16541]
## tags: [basic]
## packages:
##   - python3-univention-config-registry
## exposure: dangerous
## roles: [domaincontroller_master]

import datetime
import subprocess
import time

import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
from univention.config_registry import handler_set, handler_unset
from univention.testing import utils


def ucr_cron(name, time_s, command, description=None, mailto=None, user=None):
    ret = [
        f"cron/{name}/command={command}",
        f"cron/{name}/time={time_s}",
    ]
    for field in ["description", "mailto", "user"]:
        if locals()[field]:
            ret.append(f"cron/{name}/{field}={locals()[field]}")
    return ret


def main():

    # sometimes this test fails with
    #   [2020-09-03 00:19:09.488622] ### FAIL ###
    #   [2020-09-03 00:19:09.490058] Token '1599085118.08' not found in /var/mail/root at 2020-09-03 00:19:09.488447,
    #                                UCRs: ['cron/knfs4av2lt/command=echo 1599085118.08', 'cron/knfs4av2lt/time=19 0 * * *',
    #                               'cron/knfs4av2lt/description=knfs4av2lt', 'cron/knfs4av2lt/mailto=root'].
    #   [2020-09-03 00:19:09.490227] ###      ###
    # mail.log says
    #   00:19:01 master091 postfix/cleanup[2143]: warning: dict_ldap_connect: Unable to bind to server ldap://master091.AutoTest091.test:7389
    #     with dn cn=master091,cn=dc,cn=computers,dc=AutoTest091,dc=test: 49 (Invalid credentials)
    #   00:19:01 master091 postfix/cleanup[2143]: warning: ldap:/etc/postfix/ldap.groups lookup error for "root@master091.AutoTest091.test"
    #   00:19:01 master091 postfix/cleanup[2143]: warning: C83DF343006: virtual_alias_maps map lookup problem for root@master091.AutoTest091.test -- message not accepted, try again later
    #   00:19:37 master091 postfix/pickup[1895]: D2EC8342CD8: uid=0 from=<root>
    #   00:19:37 master091 postfix/cleanup[2143]: warning: dict_ldap_connect: Unable to bind to server ldap://master091.AutoTest091.test:7389
    #     with dn cn=master091,cn=dc,cn=computers,dc=AutoTest091,dc=test: 49 (Invalid credentials)
    #   00:19:37 master091 postfix/cleanup[2143]: warning: ldap:/etc/postfix/ldap.groups lookup error for "root@master091.AutoTest091.test"
    #   00:19:37 master091 postfix/cleanup[2143]: warning: D2EC8342CD8: virtual_alias_maps map lookup problem for root@master091.AutoTest091.test -- message not accepted, try again later
    #   00:19:38 master091 postfix/anvil[2239]: statistics: max connection rate 1/60s for (smtp:10.207.187.45) at Sep  3 00:16:18
    # the idea is that postfix missed a server pw change, so restart the goddamn thing before the test
    print('restart postfix')
    subprocess.call(('systemctl', 'restart', 'postfix'))

    # find next minute at least 30s from now
    now = datetime.datetime.now()
    for somemore in range(30, 80, 10):
        then = now + datetime.timedelta(seconds=somemore)
        if then.minute > now.minute:
            break

    time_s = f"{then.minute} {then.hour} * * *"
    token = str(time.time())
    name = uts.random_name()
    ucrs = ucr_cron(name, time_s, f"echo {token}", name, "root")
    try:
        handler_set(ucrs)

        # wait for cron
        cron_plus_ten = datetime.datetime(
            year=then.year,
            month=then.month,
            day=then.day,
            hour=then.hour,
            minute=then.minute,
            second=10,
        )
        if not now > cron_plus_ten:
            print(f"Sleeping {(cron_plus_ten - now).seconds} seconds...")
            time.sleep((cron_plus_ten - now).seconds)
    finally:
        if ucrs:
            handler_unset(map(lambda x: x.split("=")[0], ucrs))

    # look for mail
    with ucr_test.UCSTestConfigRegistry() as ucr:
        root_mail_alias = ucr.get("mail/alias/root", "")
    if "systemmail" in root_mail_alias:
        mailbox = "/var/mail/systemmail"
    else:
        mailbox = "/var/mail/root"

    with open(mailbox, 'rb') as f:
        for line in f:
            if token in line.decode('UTF-8', 'replace'):
                break
        else:
            utils.fail(f"Token '{token}' not found in /var/mail/root at {datetime.datetime.now()}, UCRs: {ucrs}.")


if __name__ == '__main__':
    main()
