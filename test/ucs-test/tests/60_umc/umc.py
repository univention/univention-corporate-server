from __future__ import annotations

import os
import shutil
import sys
from time import sleep
from typing import Any, NoReturn

from univention.config_registry import ConfigRegistry
from univention.lib.misc import custom_groupname
from univention.lib.umc import ConnectionError, HTTPError
from univention.testing import utils
from univention.testing.codes import Reason
from univention.testing.umc import Client


class UMCBase:
    """A base class for testing UMC-system"""

    def __init__(self) -> None:
        """Test Class constructor"""
        self.client: Client | None = None
        self.ucr = ConfigRegistry()
        self.ucr.load()
        self.ldap_base = self.ucr.get('ldap/base')

    def request(self, *args: Any, **kwargs: Any) -> Any:
        assert self.client is not None
        return self.client.umc_command(*args, **kwargs).result

    def create_connection_authenticate(self) -> None:
        """Create UMC connection and authenticate"""
        try:
            self.client = Client.get_test_connection()
        except (HTTPError, ConnectionError) as exc:
            print("An error while trying to authenticate to UMC: %r" % exc)
            print("Waiting 5 seconds and making another attempt")
            sleep(5)
            self.client = Client.get_test_connection()

    @property
    def username(self) -> str:
        assert self.client is not None
        return self.client.username

    @property
    def password(self) -> str:
        assert self.client is not None
        return self.client.password

    @property
    def hostname(self) -> str:
        assert self.client is not None
        return self.client.hostname

    def check_obj_exists(self, name: str, obj_type: str, flavor: str | None = None) -> bool:
        """
        Checks if user, group or policy object with provided 'name' exists
        via UMC 'udm/query' request, returns True when exists.
        Object type selected by 'obj_type' argument.
        """
        options = {
            "container": "all",
            "objectType": obj_type,
            "objectProperty": "None",
            "objectPropertyValue": "",
            "hidden": True,
        }
        return any(result['name'] == name for result in self.request('udm/query', options, flavor or obj_type))

    def get_object(self, dns: list[str], flavor: str) -> list[dict[str, Any]]:
        """
        Returns the request result of the 'udm/get' UMC connection,
        made with provided 'options' and 'flavor'
        """
        assert self.client is not None
        request_result = self.client.umc_command('udm/get', dns, flavor).result
        assert request_result is not None
        return request_result

    def modify_object(self, options: list[dict[str, Any]], flavor: str) -> None:
        """
        Modifies the 'flavor' object as given in 'options' by making a
        UMC request 'udm/put', checks for 'success' in the response
        """
        assert self.client is not None
        request_result = self.client.umc_command('udm/put', options, flavor).result
        assert request_result
        assert request_result[0].get('success')

    def delete_obj(self, name: str, obj_type: str, flavor: str) -> None:
        """
        Deletes object with a 'name' by making UMC-request 'udm/remove'
        with relevant options and flavor depending on 'obj_type'
        Supported types are: users, groups, policies, extended attributes,
        networks and computers.
        """
        assert self.client is not None
        print("Deleting test object '%s' with a name: '%s'" % (obj_type, name))

        if obj_type in ('users', 'users/user', 'users/ldap'):
            obj_type = 'users'
            obj_identifier = "uid=" + name + ",cn=" + obj_type + ","
        elif obj_type == 'policies':
            obj_identifier = "cn=" + name + ",cn=UMC,cn=" + obj_type + ","
        elif obj_type == 'custom attributes':
            obj_identifier = "cn=" + name + ",cn=" + obj_type + ",cn=univention,"
        elif obj_type in ('groups', 'networks', 'computers'):
            obj_identifier = "cn=" + name + ",cn=" + obj_type + ","
        else:
            utils.fail("The object identifier format is unknown for the provided object type '%s'" % obj_type)

        obj_identifier = obj_identifier + self.ldap_base
        options = [{
            "object": obj_identifier,
            "options": {
                "cleanup": True,
                "recursive": True,
            },
        }]
        request_result = self.client.umc_command('udm/remove', options, flavor).result
        assert request_result
        assert request_result[0].get('success')

    def return_code_result_skip(self) -> NoReturn:
        """Method to stop the test with the code 77, RESULT_SKIP"""
        sys.exit(int(Reason.SKIP))


class JoinModule(UMCBase):

    def query_joinscripts(self) -> list[dict[str, Any]]:
        return self.request('join/scripts/query', {"*": "*"})

    def join(self, hostname: str) -> None:
        options = {
            "hostname": hostname,
            "username": self.username,
            "password": self.password,
        }
        self._join('join/join', options)

    def run_scripts(self, script_names: str, force: bool = False) -> None:
        options = {
            "scripts": script_names,
            "force": force,
            "username": self.username,
            "password": self.password,
        }
        self._join('join/run', options)

    def _join(self, path: str, options: dict[str, Any]) -> None:
        assert self.client is not None
        response = self.client.umc_command(path, options)

        if response.status != 202:
            utils.fail("Request 'join/%s' did not return status 202, hostname: '%s', response '%s'" % (path, self.hostname, response.status))
        if not response.result['success']:
            utils.fail("Request 'join/%s' did not return success=True in the response: '%s',hostname '%s'" % (path, response.result, self.hostname))

    def wait_rejoin_to_complete(self, poll_attempts: int) -> None:
        """
        Polls the join process via UMC 'join/running' request to make
        sure joining is still going on, sleeps 10 secs after every poll
        attempt, fails in case process still going after the given
        'poll_attempts'. Returns when process is not reported as running.
        """
        assert self.client is not None
        for _attempt in range(poll_attempts):
            request_result = self.client.umc_command('join/running').result
            if request_result is None:
                utils.fail("No response on UMC 'join/running' request")
            elif request_result is False:
                return
            print("Waiting 10 seconds before next poll request...")
            sleep(10)
        utils.fail("Failed to wait for join script(-s) to finish")

    def copy_file(self, src: str, dst: str) -> None:
        """Makes a copy of the 'src' file to 'dst' file if 'src' exists"""
        try:
            if os.path.exists(src):
                shutil.copy2(src, dst)
                if not os.path.exists(dst):
                    utils.fail("The 'shutil' did not copy file '%s' to '%s'" % (src, dst))
            else:
                utils.fail("Failed to find the file at the provided path '%s'" % src)
        except (OSError, shutil.Error) as exc:
            utils.fail("An exception while coping the file from '%s', to '%s', error '%s'" % (src, dst, exc))

    def delete_file(self, path: str) -> None:
        """Checks if 'path' file exists and deletes it"""
        try:
            if os.path.exists(path):
                os.remove(path)
            else:
                print("Failed to find the file at the provided path '%s'" % path)
        except OSError as exc:
            utils.fail("An exception occurred while deleting a file located at '%s': '%s'" % (path, exc))


class UDMModule(UMCBase):

    # for getting the default English names of users/groups:
    _default_names = {
        'domainadmins': "Domain Admins",
        'domainusers': "Domain Users",
        'windowshosts': "Windows Hosts",
        'dcbackuphosts': "DC Backup Hosts",
        'dcslavehosts': "DC Slave Hosts",
        'computers': "Computers",
        'printoperators': "Printer-Admins",
        'administrator': "Administrator",
    }

    test_network_dn = ''

    def create_computer(self, computer_name: str, ip_address: list[str], dns_forward: list[str], dns_reverse: list[str]) -> list[dict[str, Any]]:
        """
        Creates a computer with given arguments and self.ldap_base,
        self.test_network_dn via 'udm/add' UMC request
        """
        options = [{
            "object": {
                "ip": ip_address,
                "network": self.test_network_dn,
                "unixhome": "/dev/null",
                "ntCompatibility": False,
                "shell": "/bin/false",
                "primaryGroup": "cn=Windows Hosts,cn=groups," + self.ldap_base,
                "dnsEntryZoneForward": dns_forward,
                "name": computer_name,
                "dnsEntryZoneReverse": dns_reverse,
                "$options$": {
                            "samba": True,
                            "kerberos": True,
                            "posix": True,
                            "nagios": False,
                },
                "$policies$": {},
            },
            "options": {"container": "cn=computers," + self.ldap_base, "objectType": "computers/windows"},
        }]
        return self.request("udm/add", options, "computers/computer")

    def get_groupname_translation(self, groupname: str) -> str:
        """
        Returns the localized translation for the given 'groupname'.
        Groupname should be the UCR variable name (e.g. domainadmins).
        """
        return custom_groupname(self._default_names.get(groupname), self.ucr)
