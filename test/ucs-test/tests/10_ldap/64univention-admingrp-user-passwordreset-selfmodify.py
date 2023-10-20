#!/usr/share/ucs-test/runner python3
## desc: tests if users can change their own passwords
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## packages:
##  - univention-admingrp-user-passwordreset
## exposure: dangerous

import univention.config_registry
import univention.testing.strings as uts
from univention.testing import utils
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


try:
    with UCSTestConfigRegistry() as ucr, UCSTestUDM() as udm:

        def change_own_password_to_random(account,):
            try:
                udm.modify_object('users/user', binnddn=account.dn, bindpwd=account.password, dn=account.dn, set={
                    'password': uts.random_string(),
                },)
            except Exception:
                fail('%s can not change its own password' % account)
            else:
                print('%s changed its password successfully' % account)

        # Create new helpdesk group
        try:
            what = "Helpdesk group"
            helpdesk_group_dn, helpdesk_group_name = udm.create_group()
            helpdesk_group = Account(what, helpdesk_group_dn, helpdesk_group_name,)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {helpdesk_group}')

        # Create new user
        try:
            what = "Helpdesk user"
            helpdesk_user_dn, helpdesk_user_name = udm.create_user()
            helpdesk_user = Account(what, helpdesk_user_dn, helpdesk_user_name,)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {helpdesk_user}')

        # Create new user
        try:
            what = "Protected user"
            protected_user_dn, protected_user_name = udm.create_user()
            protected_user = Account(what, protected_user_dn, protected_user_name,)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {protected_user}')

        # Create new unprotected user
        try:
            what = "Unprotected user"
            unprotected_user_dn, unprotected_user_name = udm.create_user()
            unprotected_user = Account(what, unprotected_user_dn, unprotected_user_name,)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {unprotected_user}')

        # Add user to corresponding group
        try:
            udm.modify_object('groups/group', dn=helpdesk_group.dn, append={
                'users': [helpdesk_user.dn],
            },)
        except Exception as exc:
            fail(f'Adding {helpdesk_user} to corresponding group {helpdesk_group} failed: {exc}')
        else:
            print('Added %s to corresponding group' % helpdesk_user)

        # Allow users to modify their password in Univention Directory Manager
        univention.config_registry.handler_set([
            'ldap/acl/user/password/change=yes',
            f'ldap/acl/user/passwordreset/accesslist/groups/helpdesk={helpdesk_group.dn}',
            f'ldap/acl/user/passwordreset/protected/uid=Administrator,{protected_user.name}',
        ])

        # Activate passwordreset ACLs:
        utils.restart_slapd()

        # Check if helpdesk account can set its own password
        change_own_password_to_random(helpdesk_user)

        # Check if protected user account can set its own password
        change_own_password_to_random(protected_user)

        # Check if unprotected user account can set its own password
        change_own_password_to_random(unprotected_user)
finally:
    # Important: deactivate LDAP ACLs again
    utils.restart_slapd()
