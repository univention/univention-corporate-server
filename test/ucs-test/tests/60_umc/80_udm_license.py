#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test the UMC license management
## bugs: [34620]
## roles:
##  - domaincontroller_master
## tags: [skip_admember]
## exposure: dangerous

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from subprocess import run
from time import sleep
from typing import Iterator

import ldap.dn
import pytest

from univention import uldap
from univention.config_registry.interfaces import Interfaces
from univention.testing.license_client import TestLicenseClient
from univention.testing.strings import random_username

from umc import UDMModule


@pytest.fixture(scope='session')
def udm_license_module(tmp_path_factory) -> Iterator[UDMLicenseManagement]:
    _udm_license_module = UDMLicenseManagement(tmp_path_factory.mktemp(__name__))
    _udm_license_module.dump_current_license_to_file()
    _udm_license_module.create_connection_authenticate()
    try:
        yield _udm_license_module
    finally:
        _udm_license_module.restore_initial_license()
        print("\nRemoving created test computers and users (if any):")
        _udm_license_module.delete_created_computers()
        _udm_license_module.delete_created_users()


def test_free_license(udm_license_module: UDMLicenseManagement) -> None:
    """
    Uploads a free license, checks its info, attempts to create
    computers and users and removes those that were created after
    """
    path = udm_license_module.modify_free_license_template()

    print("\nUploading a 'Free' license: 'FreeForPersonalUseTest.license'")
    udm_license_module.import_new_license(path)

    print("\nChecking the 'Free' license info")
    udm_license_module.check_free_license_info()

    print("\nAttempting to create 10 computers with a 'Free' license")
    udm_license_module.free_license_limits_check('computer')

    print("\nRemoving created test computers for the next test case:")
    udm_license_module.delete_created_computers()

    print("\nAttempting to create 10 users with a 'Free' license")
    udm_license_module.free_license_limits_check('user')

    print("\nRemoving created test users for the next test case:")
    udm_license_module.delete_created_users()


@pytest.mark.skipif(not Path(TestLicenseClient.secret_file).exists(), reason="Missing license secret file")
def test_expired_license(udm_license_module: UDMLicenseManagement) -> None:
    """
    Uploads an expired license, attempts to create computers and users
    with it
    """
    path = udm_license_module.get_expired_license()

    print("\nUploading an expired license 'ExpiredTest.license' for the test")
    udm_license_module.import_new_license(path)

    print("\nAttempting to create 10 computers with an expired license")
    udm_license_module.expired_license_limits_check('computer')

    print("\nAttempting to create 10 users with an expired license")
    udm_license_module.expired_license_limits_check('user')
    udm_license_module.restart_umc_server()


@pytest.mark.skipif(not Path(TestLicenseClient.secret_file).exists(), reason="Missing license secret file")
def test_valid_license(udm_license_module: UDMLicenseManagement) -> None:
    """Uploads a valid license, creates 10 computers and users with it"""
    path = udm_license_module.get_valid_license()

    print("\nUploading a valid license 'ValidTest.license' for the test")
    udm_license_module.import_new_license(path)

    print("\nAttempting to create 10 computers with a valid license")
    udm_license_module.valid_license_limits_check('computer')

    print("\nRemoving created test computers for the next test case:")
    udm_license_module.delete_created_computers()

    print("\nAttempting to create 10 users with a valid license")
    udm_license_module.valid_license_limits_check('user')

    print("\nRemoving created test users for the next test case:")
    udm_license_module.delete_created_users()


def test_modified_signature(udm_license_module: UDMLicenseManagement) -> None:
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


@pytest.mark.skipif(not Path(TestLicenseClient.secret_file).exists(), reason="Missing license secret file")
def test_junk_license(udm_license_module: UDMLicenseManagement) -> None:
    """
    Uploads a 'junk' license and tries to create computers
    and users with it
    """
    path = udm_license_module.generate_junk_license()

    print("\nUploading a 'junk' license 'JunkTest.license' for the test")
    udm_license_module.import_new_license(path)

    print("\nAttempting to create 10 computers with a 'junk' license")
    udm_license_module.junk_license_limits_check('computer')

    print("\nAttempting to create 10 users with a 'junk' license")
    udm_license_module.junk_license_limits_check('user')


class UDMLicenseManagement(UDMModule):

    FFPUT = Path(__file__).with_name("FreeForPersonalUseTest.license")
    SIGNATURE = "pWvKcjqCoalaf1DtYjcvYPRpxRfopKsEUtxRa+1nIFKKtQ=="

    def __init__(self, tmp: Path) -> None:
        super(UDMLicenseManagement, self).__init__()
        self._license_client: TestLicenseClient | None = None
        self.ldap_base = self.ucr.get('ldap/base')
        self.license_dn = f"cn=admin,cn=license,cn=univention,{self.ldap_base}"
        self.test_network_dn = f"cn=default,cn=networks,{self.ldap_base}"
        self.test_network = Interfaces(self.ucr).get_default_ipv4_address().network
        self.tmp = tmp
        self.initial_license_file = tmp / 'InitiallyInstalled.license'

        self.users_to_delete: list[str] = []
        self.computers_to_delete: list[str] = []

    @property
    def license_client(self) -> TestLicenseClient:
        if self._license_client is None:
            self._license_client = TestLicenseClient()
            if not Path(self._license_client.secret_file).exists():
                pytest.skip("Missing license.secret file")
        return self._license_client

    def restart_umc_server(self) -> None:
        """
        Restarts the UMC Server (to release active connections and memory),
        waits and creates a new connection after
        """
        print("\nRestarting the UMC Server to release active connections")
        run(("systemctl", "restart", "univention-management-console-server"), check=True)
        sleep(10)  # wait while server is restarting
        self.create_connection_authenticate()

    def create_many_users_computers(self, obj_type: str, amount: int) -> int:
        """
        Creates a given 'amount' of computers or users depending on given
        'obj_type', returns number of objects totally created
        (i.e. before the first failed attempt or full 'amount')
        Recreates the UMC connection before every attempt.
        """
        obj_name_base = f'umc_test_{obj_type}_{random_username(6)}'

        for obj in range(amount):
            # the UMC connection is recreated every step in order to get the
            # license limitations working during this loop:
            self.create_connection_authenticate()
            obj_name = f"{obj_name_base}_{obj}"
            if obj_type == 'computer':
                request_result = self.create_computer(obj_name, [self.test_network[51 + obj].exploded], [], [])
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

    def create_user(self, username: str, password: str, groupname: str, group_container: str = "groups"):
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
                "primaryGroup": f"cn={ldap.dn.escape_dn_chars(groupname)},cn={ldap.dn.escape_dn_chars(group_container)},{self.ldap_base}",
                "username": username,
                "shell": "/bin/bash",
                "locked": "0",
                "homeSharePath": username,
                "unixhome": f"/home/{username}",
                "overridePWLength": False,
                "displayName": username,
                "$options$": {
                    "person": True,
                    "mail": True,
                    "pki": False,
                },
            },
            "options": {"container": f"cn=users,{self.ldap_base}", "objectType": "users/user"},
        }]
        return self.request("udm/add", options, "users/user")

    def check_free_license_info(self) -> None:
        """
        Makes a check of the free license info, assuming
        it is active at the moment. Request is 'udm/license/info'.
        """
        # recreating the UMC connection to get the current license info:
        self.create_connection_authenticate()
        license_info = self.request('udm/license/info')
        assert license_info['baseDN'] == self.ldap_base
        assert not license_info['keyID']
        assert license_info['support'] in ('0', 0)  # str possible
        assert license_info['premiumSupport'] in ('0', 0)  # str poss.
        assert license_info['endDate'] == "unlimited"

        license_info = license_info['licenses']
        assert not license_info['corporateclients']
        assert license_info['managedclients'] == 5
        assert not license_info.get('virtualdesktopclients')
        assert not license_info.get('virtualdesktopusers')
        assert license_info['users'] == 5
        assert not license_info['servers']

    def import_new_license(self, license_file: Path) -> None:
        """
        Reads the given 'license_file' and makes a 'udm/license/import' UMC
        request with the license details in options to import it
        """
        assert license_file.exists()
        license_text = license_file.read_text()

        options = {"license": license_text}
        request_result = self.request('udm/license/import', options)
        assert request_result[0]["success"]

    def dump_current_license_to_file(self) -> None:
        """
        Opens a given 'license_file' for writing and puts in the output of
        launched 'univention-ldapsearch' with self.license_dn argument
        """
        print(f"Saving initial license to file: {self.initial_license_file!r}")
        with self.initial_license_file.open('w') as license:
            run(("univention-ldapsearch", "-LLLb", self.license_dn), stdout=license, check=True)

    def modify_license_signature(self, new_signature: str) -> None:
        """Modifies the license signature to a given 'new_signature'"""
        # in changes "foo" stands as a dummy for 'old-values':
        changes = [('univentionLicenseSignature', b"foo", new_signature.encode("UTF-8"))]
        admin_ldap_conn = uldap.getAdminConnection()
        admin_ldap_conn.modify(self.license_dn, changes)

    def delete_created_computers(self) -> None:
        """
        Deletes all the computers that are in the 'self.computers_to_delete'
        list with a check if each of them exists
        """
        for computer in self.computers_to_delete:
            if self.check_obj_exists(computer, "computers/windows"):
                self.delete_obj(computer, 'computers', 'computers/windows')
        self.computers_to_delete.clear()

    def delete_created_users(self) -> None:
        """
        Deletes all the users that are in the 'self.users_to_delete'
        list with a check if each of them exists
        """
        for user in self.users_to_delete:
            if self.check_obj_exists(user, "users/user", "users/user"):
                self.delete_obj(user, 'users/user', 'users/user')
        self.users_to_delete.clear()

    def free_license_limits_check(self, obj_type: str) -> None:
        """Checks the free license user/computer creation limits"""
        amount_created = self.create_many_users_computers(obj_type, 10)
        # 6 since license won't lock with only 5 users/computers
        assert amount_created <= 6

    def expired_license_limits_check(self, obj_type: str) -> None:
        """Checks the expired license user/computer creation limits"""
        amount_created = self.create_many_users_computers(obj_type, 10)
        assert amount_created == 0

    def valid_license_limits_check(self, obj_type: str) -> None:
        """Checks the valid license user/computer creation"""
        amount_created = self.create_many_users_computers(obj_type, 10)
        assert amount_created == 10

    def modified_license_limits_check(self, obj_type: str) -> None:
        """Checks the modified license user/computer creation"""
        amount_created = self.create_many_users_computers(obj_type, 10)
        assert amount_created == 0

    def junk_license_limits_check(self, obj_type: str) -> None:
        """Checks the 'junk' license user/computer creation"""
        amount_created = self.create_many_users_computers(obj_type, 10)
        assert amount_created == 0

    def get_valid_license(self) -> Path:
        """
        Gets a 'ValidTest.license' by ordering and downloading it
        from the licensing server via LicenseClient tool
        """
        path = self.tmp / 'ValidTest.license'
        if not path.exists():
            end_date = f"{date.today() + timedelta(days=30):%d.%m.%Y}"
            print("Obtaining a valid license for the test:")
            self.license_client.main(base_dn=self.ldap_base, end_date=end_date, license_file=path.as_posix())
        return path

    def get_expired_license(self) -> Path:
        """
        Gets an 'ExpiredTest.license' by ordering and downloading it
        from the licensing server via LicenseClient tool
        """
        path = self.tmp / 'ExpiredTest.license'
        if not path.exists():
            end_date = f"{date.today() - timedelta(days=30):%d.%m.%Y}"
            print("Obtaining an expired license for the test:")
            self.license_client.main(base_dn=self.ldap_base, end_date=end_date, license_file=path.as_posix())
        return path

    def modify_free_license_template(self) -> Path:
        """
        Modifies the 'FreeForPersonalUseTest.license' to have a correct
        BaseDN. Skipps the test if Free license template was not found.
        """
        print("\nModifing the Free license template for the test")
        path = self.tmp / 'Modified.license'
        with self.FFPUT.open('r') as fd, path.open("w") as out:
            for line in fd:
                key, sep, val = line.rstrip("\n").partition(": ")
                out.write(f"{key}{sep}{self.license_dn if key == 'dn' else val}\n")
        return path

    def generate_junk_license(self) -> Path:
        """
        Copies the 'ValidTest.license' file to a 'JunkTest.license' file and
        changes a line with license signature.
        """
        print("\nGenerating a junk license based on valid license for the test")
        valid = self.get_valid_license()
        path = self.tmp / 'JunkTest.license'
        with valid.open('r') as fd, path.open("w") as out:
            for line in fd:
                key, sep, val = line.rstrip("\n").partition(": ")
                out.write(f"{key}{sep}{self.SIGNATURE if key == 'univentionLicenseSignature' else val}\n")
        return path

    def restore_initial_license(self) -> None:
        """Restores the initially dumped license."""
        if self.initial_license_file.exists():
            self.restart_umc_server()
            print(f"Restoring initially dumped license from file {self.initial_license_file}")
            self.import_new_license(self.initial_license_file)
