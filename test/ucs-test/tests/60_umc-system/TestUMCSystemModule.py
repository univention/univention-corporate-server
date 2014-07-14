import sys

import simplejson as json
from time import sleep
from httplib import HTTPException

from univention.config_registry import ConfigRegistry
from univention.testing.codes import TestCodes
import univention.testing.utils as utils
from univention.lib.umc_connection import UMCConnection


class TestUMCSystem(object):
    """
    A base class for testing UMC-system
    """

    def __init__(self):
        """Test Class constructor"""
        self.username = None
        self.password = None
        self.hostname = None
        self.Connection = None
        self.ldap_base = ''
        self.test_network_dn = ''

        self.UCR = ConfigRegistry()

    def reload_ucr(self):
        """Reload the UCR variables """
        self.UCR.load()

    def get_ucr_credentials(self):
        """Get credentials from the registry"""
        try:
            self.reload_ucr()
            self.username = self.UCR['tests/domainadmin/account']
            self.password = self.UCR['tests/domainadmin/pwd']
            self.hostname = self.UCR['hostname']

            # extracting the 'uid' value of the username string
            self.username = self.username.split(',')[0][len('uid='):]
        except Exception as exc:
            print("Failed to get the UCR username and/or a password for test,"
                  " '%s'" % exc)
            self.return_code_result_skip()
        if self.hostname is None:
            print "The hostname in the UCR should not be 'None'"
            self.return_code_result_skip()

    def create_connection_authenticate(self):
        """Create UMC connection and authenticate"""
        try:
            self.Connection = UMCConnection(self.hostname)
            self.Connection.auth(self.username, self.password)
        except HTTPException as exc:
            print("An HTTPException while trying to authenticate to UMC: %r"
                  % exc)
            print "Waiting 5 seconds and making another attempt"
            sleep(5)
            self.Connection.auth(self.username, self.password)
        except Exception as exc:
            utils.fail("Failed to authenticate, hostname '%s' : %s" %
                       (self.hostname, exc))

    def make_custom_request(self, request_url, options):
        """
        Makes a custom UMC 'POST' request with a given
        'request_url' and given 'options' to avoid exceptions
        (for anything other than response with status 200)
        raised in the UMCConnection module. Returns formatted
        response.
        """
        options = {"options": options}
        options = json.dumps(options)
        try:
            umc_connection = self.Connection.get_connection()
            umc_connection.request('POST',
                                   request_url,
                                   options,
                                   self.Connection._headers)
            request_result = umc_connection.getresponse()
            request_result = request_result.read()
            if not request_result:
                utils.fail("Request '%s' with options '%s' failed, "
                           "hostname '%s'"
                           % (request_url, options, self.hostname))
            return json.loads(request_result)
        except Exception as exc:
            utils.fail("Exception while making '%s' request: %s"
                       % (request_url, exc))

    def make_query_request(self, prefix, options=None, flavor=None):
        """
        Makes a '/query' UMC request with a provided 'prefix' argument,
        optional 'flavor' and 'options', returns request result.
        """
        request_result = None
        try:
            request_result = self.Connection.request(prefix + '/query',
                                                     options, flavor)
            if request_result is None:
                utils.fail("Request '%s/query' failed, no result, hostname %s"
                           % (prefix, self.hostname))
            return request_result
        except Exception as exc:
            utils.fail("Exception while making '%s/query' request: %s"
                       % (prefix, exc))

    def make_top_query_request(self):
        """Makes a 'top/query' UMC request and returns result"""
        return self.make_query_request('top')

    def make_service_query_request(self):
        """Makes a 'services/query' UMC request and returns result"""
        return self.make_query_request('services')

    def check_service_presence(self, request_result, service_name):
        """
        Check if the service with 'service_name' was listed in the response
        'request_result'. Returns 'missing software' code 137 when missing.
        """
        for result in request_result:
            if result['service'] == service_name:
                break
        else:
            print("The '%s' service is missing in the UMC response: "
                  "%s" % (service_name, request_result))
            sys.exit(TestCodes.REASON_INSTALL)

    def make_udm_request(self, suffix, options=None, flavor=None):
        """
        Makes 'umcp/command/udm/' + 'suffix' request with a given
        'options' and a 'flavor' if any
        """
        try:
            request_result = self.Connection.request('udm/' + suffix,
                                                     options, flavor)
            if not request_result:
                utils.fail("Request 'umcp/command/udm/%s' with "
                           "options='%s' and flavor='%s' failed, "
                           "no response or response is empty"
                           % (suffix, options, flavor))
            return request_result
        except Exception as exc:
            utils.fail("Exception while making 'udm/%s' request with "
                       "options '%s': %s" % (suffix, options, exc))

    def create_computer(self, computer_name, ip_address,
                        dns_forward, dns_reverse):
        """
        Creates a computer with given arguments and self.ldap_base,
        self.test_network_dn via 'udm/add' UMC request
        """
        options = [{"object": {"ip": ip_address,
                               "network": self.test_network_dn,
                               "unixhome": "/dev/null",
                               "ntCompatibility": False,
                               "shell": "/bin/false",
                               "primaryGroup": "cn=Windows Hosts,cn=groups," +
                                               self.ldap_base,
                               "dnsEntryZoneForward": dns_forward,
                               "name": computer_name,
                               "dnsEntryZoneReverse": dns_reverse,
                               "$options$": {"samba": True,
                                             "kerberos": True,
                                             "posix": True,
                                             "nagios": False},
                                             "$policies$": {}},
                    "options": {"container": "cn=computers," + self.ldap_base,
                                "objectType": "computers/windows"}}]
        return self.make_udm_request("add", options, "computers/computer")

    def check_obj_exists(self, name, obj_type):
        """
        Checks if user, group or policy object with provided 'name' exists
        via UMC 'udm/query' request, returns True when exists.
        Object type selected by 'obj_type' argument.
        """
        options = {"container": "all",
                   "objectType": obj_type,
                   "objectProperty": "None",
                   "objectPropertyValue": "",
                   "hidden": True}
        try:
            for result in self.make_query_request('udm', options, obj_type):
                if result['name'] == name:
                    return True
        except KeyError as exc:
            utils.fail("KeyError exception while parsing 'udm/query' "
                       "request result: %s" % exc)

    def get_object(self, options, flavor):
        """
        Returns the request result of the 'udm/get' UMC connection,
        made with provided 'options' and 'flavor'
        """
        try:
            request_result = self.Connection.request('udm/get', options,
                                                     flavor)
            if request_result is None:
                utils.fail("Request 'udm/get' with options '%s' failed, "
                           "hostname '%s'" % (options, self.hostname))
            return request_result
        except Exception as exc:
            utils.fail("Exception while making 'udm/get' request: %s" %
                       exc)

    def modify_object(self, options, flavor):
        """
        Modifies the 'flavor' object as given in 'options' by making a
        UMC request 'udm/put', checks for 'success' in the response
        """
        try:
            request_result = self.Connection.request('udm/put', options,
                                                     flavor)
            if not request_result:
                utils.fail("Request 'udm/put' to modify an object "
                           "with options '%s' failed, hostname %s"
                           % (options, self.hostname))
            if not request_result[0].get('success'):
                utils.fail("Request 'udm/put' to modify an object "
                           "with options '%s' failed, no success = True in "
                           "response, hostname %s, response '%s'"
                           % (options, self.hostname, request_result))
        except Exception as exc:
            utils.fail("Exception while making 'udm/put' request with options "
                       "'%s': %s" % (options, exc))

    def delete_obj(self, name, obj_type, flavor):
        """
        Deletes object with a 'name' by making UMC-request 'udm/remove'
        with relevant options and flavor depending on 'obj_type'
        Supported types are: users, groups, policies, extended attributes,
        networks and computers.
        """
        print "Deleting test object '%s' with a name: '%s'" % (obj_type, name)

        if obj_type == 'users':
            obj_identifier = "uid=" + name + ",cn=" + obj_type + ","
        elif obj_type == 'policies':
            obj_identifier = "cn=" + name + ",cn=UMC,cn=" + obj_type + ","
        elif obj_type == 'custom attributes':
            obj_identifier = "cn=" + name + ",cn=" + obj_type + ",cn=univention,"
        elif obj_type in ('groups', 'networks', 'computers'):
            obj_identifier = "cn=" + name + ",cn=" + obj_type + ","
        else:
            utils.fail("The object identifier format is unknown for the "
                       "provided object type '%s'" % obj_type)

        obj_identifier = obj_identifier + self.ldap_base
        options = [{"object": obj_identifier,
                    "options": {"cleanup": True,
                                "recursive": True}}]
        try:
            request_result = self.Connection.request('udm/remove',
                                                     options,
                                                     flavor)
            if not request_result:
                utils.fail("Request 'udm/remove' to delete object with options"
                           " '%s' failed, hostname %s"
                           % (options, self.hostname))
            if not request_result[0].get('success'):
                utils.fail("Request 'udm/remove' to delete object with options"
                           " '%s' failed, no success = True in response, "
                           "hostname '%s', response '%s'"
                           % (options, self.hostname, request_result))
        except Exception as exc:
            utils.fail("Exception while making 'udm/remove' request: %s" %
                       exc)

    def return_code_result_skip(self):
        """Method to stop the test with the code 77, RESULT_SKIP """
        sys.exit(TestCodes.RESULT_SKIP)
