#!/usr/share/ucs-test/runner python3
## desc: Tests that Domain Admins members are protected by default
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## packages:
##  - univention-admingrp-user-passwordreset
## exposure: dangerous

import time

import univention.testing.strings as uts
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.udm import UCSTestUDM
from univention.testing.utils import fail


default_password = 'univention'


class Account:
    def __init__(self, description, dn, name, password=default_password,):
        self.description = description
        self.dn = dn
        self.name = name
        self.password = password

    def __str__(self):
        return f'{self.description} "{self.name}"'


with UCSTestConfigRegistry() as ucr:
    with UCSTestUDM() as udm:
        # TODO: Better don't guess DN, use ldapsearch to get DN of "cn=Domain Admins"
        domain_admins_dn = "cn=Domain Admins,cn=groups,%(ldap/base)s" % ucr
        user_password_admins_dn = "cn=User Password Admins,cn=groups,%(ldap/base)s" % ucr

        # create user
        try:
            what = 'Plain user'
            user_dn, user_name = udm.create_user()
            plain_user = Account(what, user_dn, user_name,)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {plain_user}')

        # create helpdesk user
        try:
            what = 'Helpdesk user'
            helpdesk_user_dn, helpdesk_user_name = udm.create_user()
            helpdesk_user = Account(what, helpdesk_user_dn, helpdesk_user_name,)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {helpdesk_user}')

        # Create domainadmin1
        try:
            what = 'Domain Admin 1'
            domainadmin1_dn, domainadmin1_name = udm.create_user()
            domainadmin1 = Account(what, domainadmin1_dn, domainadmin1_name,)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {domainadmin1}')

        # Make domainadmin1 a group member of "Domain Admins"
        try:
            udm.modify_object("users/user", dn=domainadmin1.dn, set={
                'groups': [domain_admins_dn],
            },)
        except Exception as exc:
            fail(f'Could not add {domainadmin1} to the group "Domain Admins": {exc}')
        else:
            print(f'Added {domainadmin1} to the group "Domain Admins"')

        # Create domainadmin2
        try:
            what = 'Domain Admin 2'
            domainadmin2_dn, domainadmin2_name = udm.create_user()
            domainadmin2 = Account(what, domainadmin2_dn, domainadmin2_name,)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {domainadmin2}')

        # Make domainadmin2 a *primary* member of group "Domain Admins"
        try:
            udm.modify_object("users/user", dn=domainadmin2.dn, set={
                'primaryGroup': [domain_admins_dn],
            },)
        except Exception as exc:
            fail(f'Cannot set the  primary group of {domainadmin2} to "Domain Admins": {exc}')
        else:
            print(f'Primary group of {domainadmin2} set to "Domain Admins"')

        # Set group of helpdesk user to User Password Admins
        try:
            udm.modify_object("users/user", dn=helpdesk_user.dn, set={
                "groups": user_password_admins_dn,
            },)
        except Exception as exc:
            fail(f'Could not add {helpdesk_user} to group "User Password Admins": {exc}')
        else:
            print(f'OK: Added {helpdesk_user} to group "User Password Admins"')

        # It takes a lot of time for this change to take effect unfortunately.. and it seems to take longer and longer ..
        time.sleep(60)

        # Test if Helpdesk user can reset password of admin
        try:
            udm.modify_object('users/user', binddn=helpdesk_user.dn, bindpwd=helpdesk_user.password, dn=domainadmin1.dn, set={
                'password': uts.random_string(),
            },)
        except Exception:
            print(f'OK: {helpdesk_user} cannot reset password of {domainadmin1}, as expected')
        else:
            fail(f'{helpdesk_user} reset password of {domainadmin1}, but should not be able to')

        # Test if Helpdesk user can reset password of admin2
        try:
            udm.modify_object('users/user', binddn=helpdesk_user.dn, bindpwd=helpdesk_user.password, dn=domainadmin2.dn, set={
                'password': uts.random_string(),
            },)
        except Exception:
            print(f'OK: {helpdesk_user} cannot reset password of {domainadmin2}')
        else:
            fail(f'{helpdesk_user} reset password of {domainadmin2}, but should not be able to')

        # Test if Helpdesk user can reset password of user
        try:
            udm.modify_object('users/user', binddn=helpdesk_user.dn, bindpwd=helpdesk_user.password, dn=plain_user.dn, set={
                'password': uts.random_string(),
            },)
        except Exception as exc:
            fail(f'{helpdesk_user} cannot reset password of {plain_user}: {exc}')
        else:
            print(f'OK: {helpdesk_user} reset password of {plain_user}')
