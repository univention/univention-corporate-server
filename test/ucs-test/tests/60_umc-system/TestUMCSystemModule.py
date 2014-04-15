import sys

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
            print "Failed to get the UCR username and/or a password for test"
            self.return_code_result_skip()
        if self.hostname is None:
            print "The hostname in the UCR should not be 'None'"
            self.return_code_result_skip()

    def create_connection_authenticate(self):
        """Create UMC connection and authenticate"""
        try:
            self.Connection = UMCConnection(self.hostname)
            self.Connection.auth(self.username, self.password)
        except Exception as exc:
            utils.fail("Failed to authenticate, hostname '%s' : %s" %
                       (self.hostname, exc))

    def make_service_query_request(self):
        """Make a service/query request and return result"""
        try:
            request_result = self.Connection.request('services/query')
            if not request_result:
                utils.fail("Request 'services/query' failed, hostname %s" %
                           self.hostname)
        except Exception as exc:
            utils.fail("Exception while making services/query request: %s" %
                       exc)
        return request_result

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

    def return_code_result_skip(self):
        """Method to stop the test with the code 77, RESULT_SKIP """
        sys.exit(TestCodes.RESULT_SKIP)
