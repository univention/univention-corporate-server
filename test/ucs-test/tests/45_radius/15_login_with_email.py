#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: test radius login with mailPrimaryAddress
## tags: [apptest, radius]
## packages:
##   - univention-radius
## join: true
## bugs: [55757]
## exposure: dangerous

import subprocess

import univention.testing.strings as uts


def radius_auth(user_identificator, password):
    subprocess.check_call([
        'radtest',
        '-t',
        'mschap',
        user_identificator,
        password,
        '127.0.0.1:18120',
        '0',
        'testing123',
    ])


def test_email_login(ucr, udm_session, rad_user):
    dn, name, password = rad_user
    mail_domain = uts.random_domain_name()
    email = f"testuser-{name}@{mail_domain}"
    udm_session.create_object(
        'mail/domain',
        ignore_exists=True,
        wait_for_replication=True,
        check_for_drs_replication=False,
        name=mail_domain,
    )
    udm_session.modify_object(
        'users/user',
        wait_for_replication=True,
        dn=dn,
        mailPrimaryAddress=email,
    )

    radius_auth(name, password)
    radius_auth(email, password)
