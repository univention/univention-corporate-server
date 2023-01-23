#!/usr/share/ucs-test/runner python3
## desc: Test that ldap/acl/user/passwordreset/protected/gid members are protected
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## packages:
##  - univention-admingrp-user-passwordreset
## exposure: dangerous

import time

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
        # TODO: Better don't guess DN, use ldapsearch to get DN of "cn=User Domain Admins"
        user_password_admins_dn = "cn=User Password Admins,cn=groups,%(ldap/base)s" % ucr

        # Create helpdesk user
        try:
            what = 'Helpdesk user'
            helpdesk_user_dn, helpdesk_user_name = udm.create_user()
            helpdesk_user = Account(what, helpdesk_user_dn, helpdesk_user_name)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {helpdesk_user}')

        # Create first admin user
        try:
            what = 'Domain Admin 1'
            domainadmin1_dn, domainadmin1_name = udm.create_user()
            domainadmin1 = Account(what, domainadmin1_dn, domainadmin1_name)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {domainadmin1}')

        # Create user
        try:
            what = 'Plain user'
            user_dn, user_name = udm.create_user()
            plain_user = Account(what, user_dn, user_name)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {plain_user}')

        # Create second admin user
        try:
            what = 'Domain Admin 2'
            domainadmin2_dn, domainadmin2_name = udm.create_user()
            domainadmin2 = Account(what, domainadmin2_dn, domainadmin2_name)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {domainadmin2}')

        # Create new admin group
        try:
            what = 'Domain Admin Group'
            domainadmin_group_dn, domainadmin_group_name = udm.create_group()
            domainadmin_group = Account(what, domainadmin_group_dn, domainadmin_group_name)
        except Exception as exc:
            fail(f'Creating {what} failed: {exc}')
        else:
            print(f'Created {domainadmin_group}')

        # add helpdesk user to User Password Admins group
        try:
            udm.modify_object("users/user", dn=helpdesk_user.dn, set={
                'groups': [user_password_admins_dn],
            })
        except Exception as exc:
            fail(f'Cannot add {helpdesk_user} to group "User Password Admins": {exc}')
        else:
            print(f'Added {helpdesk_user} to group "User Password Admins"')

        # Make domainadmin1 a group member of the domainadmin_group
        try:
            udm.modify_object("groups/group", dn=domainadmin_group.dn, append={
                'users': [domainadmin1.dn],
            })
        except Exception as exc:
            fail(f'Cannot add {domainadmin1} to {domainadmin_group}: {exc}')
        else:
            print(f'Added {domainadmin1} to {domainadmin_group}')

        # Make domainadmin2 a *primary* member of the domainadmin_group
        try:
            udm.modify_object("users/user", dn=domainadmin2.dn, set={
                'primaryGroup': [domainadmin_group.dn],
            })
        except Exception as exc:
            fail(f'Cannot set the  primary group of {domainadmin2} to {domainadmin_group}: {exc}')
        else:
            print(f'Primary group of {domainadmin2} set to {domainadmin_group}')

        univention.config_registry.handler_set([
            f'ldap/acl/user/passwordreset/protected/gid={domainadmin_group.name}',
        ])

        # Wait for slapd restart triggered by seeting ldap/acl/user/passwordreset/protected/gid
        time.sleep(35)

        # Test if Helpdesk user can reset password of admin
        try:
            udm.modify_object('users/user', binddn=helpdesk_user.dn, bindpwd=helpdesk_user.password, dn=domainadmin1.dn, set={
                'password': uts.random_string(),
                'overridePWHistory': 1,
                'overridePWLength': 1,
            })
        except Exception:
            print(f'OK: {helpdesk_user} cannot reset password of {domainadmin1}')
        else:
            fail(f'{helpdesk_user} can reset password of {domainadmin1}, but should not be able to')

        # Test if Helpdesk user can reset password of admin2
        try:
            udm.modify_object('users/user', binddn=helpdesk_user.dn, bindpwd=helpdesk_user.password, dn=domainadmin2.dn, set={
                'password': uts.random_string(),
                'overridePWHistory': 1,
                'overridePWLength': 1,
            })
        except Exception:
            print(f'OK: {helpdesk_user} cannot reset password of {domainadmin2}')
        else:
            fail(f'{helpdesk_user} can reset password of {domainadmin2}, but should not be able to')

        # Test if Helpdesk user can reset password of user
        try:
            udm.modify_object('users/user', binddn=helpdesk_user.dn, bindpwd=helpdesk_user.password, dn=plain_user.dn, set={
                'password': uts.random_string(),
                'overridePWHistory': 1,
                'overridePWLength': 1,
            })
        except Exception as exc:
            fail(f'{helpdesk_user} cannot reset password of {plain_user}: {exc}')
        else:
            print(f'OK: {helpdesk_user} reset password of {plain_user} successfully')
finally:
    # Important: deactivate LDAP ACLs again
    utils.restart_slapd()
