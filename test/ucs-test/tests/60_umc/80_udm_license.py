#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test the UMC license management
## bugs: [34620]
## roles:
##  - domaincontroller_master
## tags: [skip_admember]
## exposure: dangerous

from os import path
from shutil import copy as file_copy, rmtree
from subprocess import PIPE, Popen, check_call
from tempfile import mkdtemp
from time import localtime, sleep, strftime, time

import ldap.dn
import pytest

import univention.admin.license as udm_license
import univention.admin.uldap as udm_uldap
from univention import uldap
from univention.testing.license_client import TestLicenseClient
from univention.testing.strings import random_username
from univention.udm import UDM

from umc import UDMModule


udm_users = UDM.admin().version(2).get('users/user')
users = len(list(udm_users.search()))

check_no_users = pytest.mark.skipif(users > 5, reason='test makes no sense in pre-filled environment')


@pytest.fixture(scope='session')
def udm_license_module():
    _udm_license_module = UDMLicenseManagement()
    _udm_license_module.dump_current_license_to_file()
    _udm_license_module.create_connection_authenticate()
    try:
        yield _udm_license_module
    finally:
        _udm_license_module.restore_initial_license()
        print("\nRemoving created test computers and users (if any):")
        _udm_license_module.delete_created_computers()
        _udm_license_module.delete_created_users()


@check_no_users
def test_expired_license(udm_license_module):
    """
    Uploads an expired license, attempts to create computers and users
    with it
    """
    udm_license_module.get_expired_license()

    print("\nUploading an expired license 'ExpiredTest.license' for the test")
    udm_license_module.import_new_license(udm_license_module.temp_license_folder + '/ExpiredTest.license')

    print("\nAttempting to create 10 computers with an expired license")
    udm_license_module.expired_license_limits_check('computer')

    print("\nAttempting to create 10 users with an expired license")
    udm_license_module.expired_license_limits_check('user')
    udm_license_module.restart_umc_server()


@check_no_users
def test_valid_license(udm_license_module):
    """Uploads a valid license, creates 10 computers and users with it"""
    udm_license_module.get_valid_license()

    print("\nUploading a valid license 'ValidTest.license' for the test")
    udm_license_module.import_new_license(udm_license_module.temp_license_folder + '/ValidTest.license')

    print("\nAttempting to create 10 computers with a valid license")
    udm_license_module.valid_license_limits_check('computer')

    print("\nRemoving created test computers for the next test case:")
    udm_license_module.delete_created_computers()

    print("\nAttempting to create 10 users with a valid license")
    udm_license_module.valid_license_limits_check('user')

    print("\nRemoving created test users for the next test case:")
    udm_license_module.delete_created_users()


@check_no_users
def test_modified_signature(udm_license_module):
    """
    Modifies the current license LDAP object and tries to create
    a number of computers and users after
    """
    print("\nModifing license signature in LDAP to a random value")
    udm_license_module.modify_license_signature(random_username(50))

    print("\nAttempting to create 10 computers with a modified license signature")
    udm_license_module.modified_license_limits_check('computer')

    print("\nAttempting to create 10 users with a modified license signature")
    udm_license_module.modified_license_limits_check('user')


@check_no_users
def test_junk_license(udm_license_module):
    """
    Uploads a 'junk' license and tries to create computers
    and users with it
    """
    udm_license_module.generate_junk_license()

    print("\nUploading a 'junk' license 'JunkTest.license' for the test")
    udm_license_module.import_new_license(udm_license_module.temp_license_folder + '/JunkTest.license')

    print("\nAttempting to create 10 computers with a 'junk' license")
    udm_license_module.junk_license_limits_check('computer')

    print("\nAttempting to create 10 users with a 'junk' license")
    udm_license_module.junk_license_limits_check('user')


def test_license_info_request(udm_license_module):
    """Verifies that the udm/license/info request returns a valid response"""
    udm_license_module.create_connection_authenticate()
    license_info = udm_license_module.request('udm/license/info')
    assert license_info['baseDN'] == udm_license_module.ldap_base
    assert 'endDate' in license_info
    assert 'licenses' in license_info
    assert 'real' in license_info


def test_license_cache_attributes_written(udm_license_module):
    """
    Verifies that update_cache() writes univentionUsedLicense* attributes
    to the license LDAP object with numeric values
    """
    print("\nTesting license cache attribute writes")
    udm_license_module.check_license_cache_attributes_written()


def test_stale_cache_triggers_recount(udm_license_module):
    """
    Verifies that a stale cache triggers a re-count: calling update_cache()
    a second time must update modifyTimestamp on the license object
    """
    print("\nTesting stale cache re-count")
    udm_license_module.check_stale_cache_recount()


class UDMLicenseManagement(UDMModule):

    def __init__(self):
        super().__init__()
        self.LicenseClient = None
        self.ldap_base = self.ucr.get('ldap/base')
        self.license_dn = "cn=admin,cn=license,cn=univention," + self.ldap_base
        self.test_network_dn = "cn=default,cn=networks," + self.ldap_base
        self.select_ip_address_subnet()
        self.temp_license_folder = mkdtemp()
        print("Temporary folder to be used to store obtained test licenses: '%s'" % self.temp_license_folder)
        self.initial_license_file = self.temp_license_folder + '/InitiallyInstalled.license'

        self.users_to_delete = []
        self.computers_to_delete = []

    def check_license_cache_attributes_written(self):
        """
        Calls update_cache() with an admin LDAP connection and verifies that
        univentionUsedLicense* attributes are written to the license object
        with numeric values
        """
        lo, _ = udm_uldap.getAdminConnection()
        udm_license.license.initialize(lo)
        counts = udm_license.license.update_cache(lo)

        result = lo.search(
            base=self.license_dn,
            attr=['univentionUsedLicenseUsers', 'univentionUsedLicenseServers', 'univentionUsedLicenseManagedClients'],
        )
        assert result, 'License object not found in LDAP at %s' % self.license_dn
        attrs = result[0][1]

        for attr in ('univentionUsedLicenseUsers', 'univentionUsedLicenseServers', 'univentionUsedLicenseManagedClients'):
            assert attr in attrs, '%s not found on license object after update_cache()' % attr
            assert attrs[attr][0].decode('ASCII').isdigit(), '%s value is not numeric: %r' % (attr, attrs[attr][0])

        assert isinstance(counts, dict), 'update_cache() must return a dict'
        assert set(counts) >= {'users', 'servers', 'clients'}, 'counts dict missing expected keys'

    def check_stale_cache_recount(self):
        """
        Calls update_cache() twice with a 1-second gap and verifies that
        modifyTimestamp on the license object is updated on the second call
        """
        lo, _ = udm_uldap.getAdminConnection()
        udm_license.license.initialize(lo)

        # initial cache write
        udm_license.license.update_cache(lo)

        result = lo.search(base=self.license_dn, attr=['modifyTimestamp'])
        assert result, 'License object not found in LDAP at %s' % self.license_dn
        ts_before = result[0][1].get('modifyTimestamp', [b''])[0]

        sleep(1)

        # second update that mirrors what _update_cache_and_recheck does on staleness
        udm_license.license.update_cache(lo)

        result = lo.search(base=self.license_dn, attr=['modifyTimestamp'])
        ts_after = result[0][1].get('modifyTimestamp', [b''])[0]

        assert ts_after != ts_before, (
            'modifyTimestamp was not updated on re-count (before=%r, after=%r); '
            'cache write may have silently failed' % (ts_before, ts_after)
        )

    def restart_umc_server(self):
        """
        Restarts the UMC Server (to release active connections and memory),
        waits and creates a new connection after
        """
        print("\nRestarting the UMC Server to release active connections")
        check_call(("deb-systemd-invoke", "restart", "univention-management-console-server"))
        sleep(10)  # wait while server is restarting
        self.create_connection_authenticate()

    def select_ip_address_subnet(self):
        """
        Selects the ip addresses subnet for the test by getting 'eth0' network
        UCR variable and removing its ending
        """
        test_network_ip = self.ucr['interfaces/%s/network' % self.ucr.get('interfaces/primary', 'eth0')]
        self.test_network_ip = test_network_ip[:test_network_ip.rfind('.') + 1]

    def create_many_users_computers(self, obj_type, amount):
        """
        Creates a given 'amount' of computers or users depending on given
        'obj_type', returns number of objects totally created
        (i.e. before the first failed attempt or full 'amount')
        Recreates the UMC connection before every attempt.
        """
        obj_name_base = 'umc_test_%s_%s_' % (obj_type, random_username(6))

        for obj in range(amount):
            # the UMC connection is recreated every step in order to get the
            # license limitations working during this loop:
            self.create_connection_authenticate()
            obj_name = obj_name_base + str(obj)
            if obj_type == 'computer':
                request_result = self.create_computer(obj_name, [self.test_network_ip + str(obj + 51)], [], [])
            elif obj_type == 'user':
                # use translated group name for non-Enlish AD case: Bug #37921
                domain_users = self.get_groupname_translation('domainusers')
                request_result = self.create_user(obj_name, 'Univention@99', domain_users)
            if request_result[0].get("success"):
                if obj_type == 'computer':
                    self.computers_to_delete.append(obj_name)
                elif obj_type == 'user':
                    self.users_to_delete.append(obj_name)
            else:
                print(f"The creation of a {obj_type} (attempt {obj + 1}) failed, request result: '{request_result[0]}', ")
                return obj
        return amount

    def create_user(self, username, password, groupname, group_container="groups"):
        """
        Creates a test user by making a UMC-request 'udm/add'
        with a provided 'username', 'password' and 'groupname'
        as a primary group.
        """
        options = [{
            "object": {
                "disabled": "0",
                "lastname": username,
                "password": password,
                "overridePWHistory": False,
                "pwdChangeNextLogin": False,
                "primaryGroup": "cn=" + ldap.dn.escape_dn_chars(groupname) + ",cn=" + ldap.dn.escape_dn_chars(group_container) + "," + self.ldap_base,
                "username": username,
                "shell": "/bin/bash",
                "locked": "0",
                "homeSharePath": username,
                "unixhome": "/home/" + username,
                "overridePWLength": False,
                "displayName": username,
                "$options$": {
                    "person": True,
                    "mail": True,
                    "pki": False,
                },
            },
            "options": {"container": "cn=users," + self.ldap_base, "objectType": "users/user"},
        }]
        return self.request("udm/add", options, "users/user")

    def import_new_license(self, license_file):
        """
        Reads the given 'license_file' and makes a 'udm/license/import' UMC
        request with the license details in options to import it
        """
        if not path.exists(license_file):
            print("The '%s' license file cannot be found" % license_file)
            self.return_code_result_skip()
        with open(license_file) as license:
            license_text = license.read()

        options = {"license": license_text}
        request_result = self.request('udm/license/import', options)
        assert request_result[0]["success"]

    def dump_current_license_to_file(self):
        """
        Opens a given 'license_file' for writing and puts in the output of
        launched 'univention-ldapsearch' with self.license_dn argument
        """
        license_file = self.initial_license_file
        print("\nSaving initial license to file: '%s'" % license_file)
        with open(license_file, 'w') as license:
            proc = Popen(("univention-ldapsearch", "-LLLb", self.license_dn), stdout=license, stderr=PIPE)
            _stdout, stderr = proc.communicate()
            assert not stderr
            assert proc.returncode == 0

    def modify_license_signature(self, new_signature):
        """Modifies the license signature to a given 'new_signature'"""
        # in changes "foo" stands as a dummy for 'old-values':
        changes = [('univentionLicenseSignature', b"foo", new_signature.encode("UTF-8"))]
        admin_ldap_conn = uldap.getAdminConnection()
        admin_ldap_conn.modify(self.license_dn, changes)

    def delete_created_computers(self):
        """
        Deletes all the computers that are in the 'self.computers_to_delete'
        list with a check if each of them exists
        """
        for computer in self.computers_to_delete:
            if self.check_obj_exists(computer, "computers/windows"):
                self.delete_obj(computer, 'computers', 'computers/windows')
        self.computers_to_delete = []

    def delete_created_users(self):
        """
        Deletes all the users that are in the 'self.users_to_delete'
        list with a check if each of them exists
        """
        for user in self.users_to_delete:
            if self.check_obj_exists(user, "users/user", "users/user"):
                self.delete_obj(user, 'users/user', 'users/user')
        self.users_to_delete = []

    def expired_license_limits_check(self, obj_type):
        """Checks the expired license user/computer creation limits"""
        amount_created = self.create_many_users_computers(obj_type, 10)
        assert amount_created == 0

    def valid_license_limits_check(self, obj_type):
        """Checks the valid license user/computer creation"""
        amount_created = self.create_many_users_computers(obj_type, 10)
        assert amount_created == 10

    def modified_license_limits_check(self, obj_type):
        """Checks the modified license user/computer creation"""
        amount_created = self.create_many_users_computers(obj_type, 10)
        assert amount_created == 0

    def junk_license_limits_check(self, obj_type):
        """Checks the 'junk' license user/computer creation"""
        amount_created = self.create_many_users_computers(obj_type, 10)
        assert amount_created == 0

    def get_valid_license(self):
        """
        Gets a 'ValidTest.license' by ordering and downloading it
        from the licensing server via LicenseClient tool
        """
        print("\nObtaining a valid license for the test:")
        end_date = time()
        end_date += 2630000  # approx. amount of seconds in 1 month
        end_date = strftime('%d.%m.%Y', localtime(end_date))

        if self.LicenseClient is None:
            self.LicenseClient = TestLicenseClient()
        valid_license_file = self.temp_license_folder + '/ValidTest.license'
        if not path.exists(valid_license_file):
            self.LicenseClient.main(base_dn=self.ldap_base, end_date=end_date, license_file=valid_license_file)

    def get_expired_license(self):
        """
        Gets an 'ExpiredTest.license' by ordering and downloading it
        from the licensing server via LicenseClient tool
        """
        print("\nObtaining an expired license for the test:")
        if self.LicenseClient is None:
            self.LicenseClient = TestLicenseClient()
        end_date = time()
        end_date -= 2630000  # approx. amount of seconds in 1 month
        end_date = strftime('%d.%m.%Y', localtime(end_date))

        expired_license_file = (self.temp_license_folder + '/ExpiredTest.license')
        if not path.exists(expired_license_file):
            self.LicenseClient.main(base_dn=self.ldap_base, end_date=end_date, license_file=expired_license_file)

    def generate_junk_license(self):
        """
        Copies the 'ValidTest.license' file to a 'JunkTest.license' file and
        changes a line with license signature.
        """
        print("\nGenerating a junk license based on valid license for the test")
        self.get_valid_license()
        junk_license_file = self.temp_license_folder + '/JunkTest.license'
        file_copy(self.temp_license_folder + '/ValidTest.license', junk_license_file)
        with open(junk_license_file, 'r+') as junk_license:
            lines = junk_license.readlines()
            junk_license.seek(0)
            for line in lines:
                if line.startswith("univentionLicenseSignature: "):
                    line = "univentionLicenseSignature: pWvKcjqCoalaf1DtYjcvYPRpxRfopKsEUtxRa+1nIFKKtQ==\n"
                junk_license.write(line)
            junk_license.truncate()

    def restore_initial_license(self):
        """
        Restores the initially dumped license, removes created
        computers and users if there were any
        """
        license_file = self.initial_license_file
        if path.exists(license_file):
            self.restart_umc_server()
            print("\nRestoring initially dumped license from file '%s' and removing temp folder with license files" % license_file)
            self.import_new_license(license_file)
        try:
            rmtree(self.temp_license_folder)
        except OSError as exc:
            print("An OSError while deleting the temporaryfolder with license files: '%s'" % exc)
