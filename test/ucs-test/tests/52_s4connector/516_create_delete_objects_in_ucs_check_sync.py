#!/usr/share/ucs-test/runner pytest-3 -s -vv --log-level=INFO
## desc: "Create and delete objects in ucs, check for leftovers or falsely removed objects"
## exposure: dangerous
## timeout: 7200
## packages:
## - univention-s4-connector
## bugs:
##  - 50593

import subprocess
import sys
import time

import pytest
from ldap.dn import str2dn
from ldap.filter import filter_format

from univention.admin import configRegistry, modules
from univention.admin.uexceptions import noObject
from univention.admin.uldap import position
from univention.config_registry import handler_set
from univention.s4connector import configdb
from univention.testing.strings import random_name
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.ucs_samba import wait_for_drs_replication
from univention.testing.udm import verify_udm_object
from univention.testing.utils import fail, get_ldap_connection

from s4connector import connector_running_on_this_host, connector_setup, wait_for_sync


def stderr(msg):
    print(msg, file=sys.stderr)


class Users:

    def __init__(self):
        configRegistry.load()  # why is this necessary? shouldn't modules.update or init be enough
        self.lo = get_ldap_connection()
        self.pos = position(self.lo.base)
        modules.update()
        self.udm_users = modules.get('users/user')
        modules.init(self.lo, self.pos, self.udm_users)
        self.users = []
        self.uuids = []

    def create_user(self, username):
        user = self.udm_users.object(None, self.lo, self.pos)
        user.open()
        user["lastname"] = username
        user["password"] = "univention"
        user["username"] = username
        userdn = user.create()
        uuid = self.lo.get(userdn, attr=['+'])['entryUUID'][0].decode('UTF-8')
        self.uuids.append(uuid)
        self.users.append((userdn, user))
        stderr(f'create user {username} ({uuid})')

    def delete_users(self):
        for dn, user in self.users:
            try:
                stderr(f'delete user {dn}')
                user.remove()
            except KeyError:
                '''
                self = <univention.admin.handlers.users.user.object object at 0x7f0552046f60>

                    def _ldap_post_remove(self):
                >       self.alloc.append(('sid', self.oldattr['sambaSID'][0].decode('ASCII')))
                E    KeyError
                '''
            except noObject:
                pass

    def check_every_user_is_deleted(self):
        for dn, _user in self.users:
            try:
                verify_udm_object('users/user', dn, None)
            except AssertionError:
                stderr('%s still exists in UCS LDAP' % dn)
                return False
        return True

    def check_every_user_is_exists(self):
        for dn, _user in self.users:
            try:
                verify_udm_object('users/user', dn, {'username': str2dn(dn)[0][0][1]})
            except noObject:
                stderr('%s does not exist in UCS LDAP' % dn)
                return False
        return True

    def check_UCS_added_table_is_clean(self):
        db = configdb('/etc/univention/connector/s4internal.sqlite')
        for uuid in self.uuids:
            if db.get('UCS added', uuid):
                stderr('%s found in UCS added database' % uuid)
                return False
        return True


@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention S4 Connector not configured.")
@pytest.mark.skipif(configRegistry.is_true("connector/ad/autostart"), reason="This issue is not fixed in the ad connector yet.")
def test_no_leftovers_after_delete_in_ucs():
    """
    check that all objects are deleted if the (UCS) delete happens during
    the sync_to_ucs modify (as reaction to the add)

    openLDAP     S4Connector       S4
    delete                         modify
    add        <modify / add object does not exist
                delete>             delete
                <delete (dont delete, different entryUUID)
    object left over
    """
    wait_for_sync()
    with connector_setup("sync"), UCSTestConfigRegistry():
        # do not update domain users, this changes to timing
        handler_set(['directory/manager/user/primarygroup/update=false'])
        user_objects = Users()
        create_users = 30
        name = random_name()
        try:
            # create users
            for i in range(create_users):
                username = f"{name}{i}"
                user_objects.create_user(username)
            # wait for the connector to pick up these changes
            for i in range(20):
                if subprocess.call(['grep', f'sync AD > UCS:.*user.*modify.*uid={name}.*', '/var/log/univention/connector-s4.log']) == 0:
                    break
                time.sleep(3)
            # delete users during the modify sync AD > UCS
            user_objects.delete_users()
            # now check that everything is removed
            assert user_objects.check_every_user_is_deleted(), "not all users, have been removed, but should be"
            wait_for_sync()
            assert user_objects.check_UCS_added_table_is_clean(), "some uuid were not removed from s4internal.sqlite->UCS added"
            logentry = f'uid={name}{create_users - 1},.* sync ignored: does not exist in UCS but has already been added in the past'
            logfile = '/var/log/univention/connector-s4.log'
            if subprocess.call(['grep', '-q', logentry, logfile]) != 0:
                print(f'The log message that indicates that we really hit the problem is missing in {logfile}: {logentry}')
            assert user_objects.check_every_user_is_deleted(), "not all users, have been removed, but should be"
        finally:
            # cleanup
            user_objects.delete_users()


@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention S4 Connector not configured.")
@pytest.mark.skipif(configRegistry.is_true("connector/ad/autostart"), reason="This issue is not fixed in the ad connector yet.")
def test_do_not_delete_objects_with_different_id():
    '''
    Check if Users in UCS wont be deleted in sync_to_ucs if deleted "by" UCS
    to prevent

    openLDAP     S4Connector       S4
    add A (id 1)
                 -> added A (id 1)
    remove A (id 1)
    create A (id 2)
                 remove (A id 1) registred
                 <- removed A (id 2)
    '''
    with connector_setup("sync"), UCSTestConfigRegistry():
        # do not update domain users, this changes to timing
        handler_set(['directory/manager/user/primarygroup/update=false'])
        user_objects = Users()
        name = random_name()
        create_users = 10
        try:
            # create users
            for i in range(create_users):
                username = f"{name}{i}"
                user_objects.create_user(username)
            # wait for the connector to pick up these changes
            wait_for_drs_replication(filter_format('(sAMAccountName=%s)', (username,)))
            time.sleep(10)
            # new delete everything and (re) create, without wait
            user_objects.delete_users()
            for i in range(create_users):
                username = f"{name}{i}"
                user_objects.create_user(username)
            # wait for the connector to pick up these changes
            wait_for_drs_replication(filter_format('(sAMAccountName=%s)', (username,)))
            time.sleep(10)
            # now check that all users exists
            if not user_objects.check_every_user_is_exists():
                fail("not all users (uid=%s*) exists, but should" % name)
            # check if we really hit the problem (by checking for a specific log message)
            logentry = f'delete_in_ucs: object uid={name}{create_users - 1},.* already deleted in UCS, ignoring delete'
            logfile = '/var/log/univention/connector-s4.log'
            if subprocess.call(['grep', '-q', logentry, logfile]) != 0:
                print(f'The log message that indicates that we really hit the problem is missing in {logfile}: {logentry}')

        finally:
            # cleanup
            user_objects.delete_users()
