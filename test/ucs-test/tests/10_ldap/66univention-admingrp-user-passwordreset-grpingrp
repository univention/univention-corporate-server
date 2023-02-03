#!/usr/share/ucs-test/runner python3
## desc: Tests functionality of nested groups
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## packages:
## - univention-admingrp-user-passwordreset
## exposure: dangerous

import univention.config_registry
import univention.testing.strings as uts
from univention.testing import utils
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.udm import UCSTestUDM
from univention.testing.utils import fail


default_password = 'univention'


class Account:

    def __init__(self, description, dn, name, password=default_password):
        self.description = description
        self.dn = dn
        self.name = name
        self.password = password

    def __str__(self):
        return f'{self.description} "{self.name}"'


try:
    with UCSTestConfigRegistry() as ucr, UCSTestUDM() as udm:

        # Create new helpdesk group
        try:
            what = 'Helpdesk group'
            helpdesk_group1_dn, helpdesk_group1_name = udm.create_group()
            helpdesk_group1 = Account(what, helpdesk_group1_dn, helpdesk_group1_name)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {helpdesk_group1}')

        # Create new helpdesk user
        try:
            what = 'Helpdesk user'
            helpdesk_user1_dn, helpdesk_user1_name = udm.create_user()
            helpdesk_user1 = Account(what, helpdesk_user1_dn, helpdesk_user1_name)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {helpdesk_user1}')

        # Create new helpdesk user
        try:
            what = 'Helpdesk user'
            helpdesk_user2_dn, helpdesk_user2_name = udm.create_user()
            helpdesk_user2 = Account(what, helpdesk_user2_dn, helpdesk_user2_name)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {helpdesk_user2}')

        # Create new unprotected user
        try:
            what = 'Unprotected user'
            unprotected_user_dn, unprotected_user_name = udm.create_user()
            unprotected_user = Account(what, unprotected_user_dn, unprotected_user_name)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {unprotected_user}')

        # Add helpdesk user to helpdesk group
        try:
            what = 'helpdesk user'
            udm.modify_object('groups/group', dn=helpdesk_group1.dn, append={
                'users': [helpdesk_user1.dn],
            })
        except Exception as exc:
            fail(f'Adding {helpdesk_user1} to corresponding group {helpdesk_group1.name} failed: {exc}')
        else:
            print('Added %s to corresponding group' % what)

        # Create second helpdesk group
        try:
            what = 'Helpdesk group'
            helpdesk_group2_dn, helpdesk_group2_name = udm.create_group()
            helpdesk_group2 = Account(what, helpdesk_group2_dn, helpdesk_group2_name)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {helpdesk_group2}')

        # Add second helpdesk user to second helpdesk group
        try:
            what = 'helpdesk user'
            udm.modify_object('groups/group', dn=helpdesk_group2.dn, append={
                'users': [helpdesk_user2.dn],
            })
        except Exception as exc:
            fail(f'Adding {helpdesk_user2} to corresponding group {helpdesk_group2.name} failed: {exc}')
        else:
            print('Added %s to corresponding group' % what)

        # Create nested group
        try:
            udm.modify_object('groups/group', dn=helpdesk_group1.dn, append={
                'nestedGroup': [helpdesk_group2.dn],
            })
        except Exception as exc:
            fail(f'Cannot create nested group: {exc}')
        else:
            print('Created nested group')

        # Allow users to modify their password in Univention Directory Manager
        univention.config_registry.handler_set([
            f'ldap/acl/user/passwordreset/accesslist/groups/helpdesk-a={helpdesk_group1.dn}',
            'ldap/acl/user/passwordreset/protected/uid=Administrator',
            'ldap/acl/nestedgroups=no',
        ])

        # Activate passwordreset ACLs:
        utils.restart_slapd()

        # Test if Helpdesk user can reset password of unprotected user
        try:
            udm.modify_object('users/user', binddn=helpdesk_user1.dn, bindpwd=helpdesk_user1.password, dn=unprotected_user.dn, set={
                'password': 'univention2',
                'overridePWHistory': 1,
                'overridePWLength': 1,
            })
        except Exception as exc:
            fail(f'{helpdesk_user1} cannot reset password of {unprotected_user}: {exc}')
        else:
            print(f'OK: {helpdesk_user1} reset password of {unprotected_user} successfully')

        # Test if nested helpdesk user can reset password of unprotected user
        try:
            udm.modify_object('users/user', binddn=helpdesk_user2.dn, bindpwd=helpdesk_user2.password, dn=unprotected_user.dn, set={
                'password': 'univention2',
                'overridePWHistory': 1,
                'overridePWLength': 1,
            })
        except Exception:
            print(f'OK: Nested {helpdesk_user2} cannot reset password of {unprotected_user}, as it should be')
        else:
            fail(f'Nested {helpdesk_user2} can reset password of {unprotected_user}, but should not be able to')

        # Enable nested group tests
        univention.config_registry.handler_set(['ldap/acl/nestedgroups=yes'])
        utils.restart_slapd()

        # Test if helpdesk user can still reset password of unprotected user
        try:
            udm.modify_object('users/user', binddn=helpdesk_user1.dn, bindpwd=helpdesk_user1.password, dn=unprotected_user.dn, set={
                'password': uts.random_string(),
                'overridePWHistory': 1,
                'overridePWLength': 1,
            })
        except Exception as exc:
            fail(f'{helpdesk_user1} can not set password of {unprotected_user}: {exc}')
        else:
            print(f'OK: {helpdesk_user1} set password of {unprotected_user} successfully')

        # Test if nested helpdesk user can reset password of unprotected user
        try:
            udm.modify_object('users/user', binddn=helpdesk_user2.dn, bindpwd=helpdesk_user2.password, dn=unprotected_user.dn, set={
                'password': uts.random_string(),
                'overridePWHistory': 1,
                'overridePWLength': 1,
            })
        except Exception as exc:
            fail(f'{helpdesk_user2} user can not reset password of {unprotected_user}: {exc}')
        else:
            print(f'OK: {helpdesk_user2} user set password of {unprotected_user} successfully')
finally:
    # Important: deactivate LDAP ACLs again
    utils.restart_slapd()
