# Path: test/ucs-test/tests/91_udm-performance-test/locustfiles/tasks/locustfiles/tasks/computers_domaincontroller_slave/computers_domaincontroller_slave_dn_put.py
# Modify or move an Replica Directory Node object
# Empty description
# # this file implements the Locust task for the following endpoints:
# # - PUT /computers/domaincontroller_slave/{dn}
#


def computers_domaincontroller_slave_dn_put(self):
    """PUT /computers/domaincontroller_slave/{dn}"""
    dn = 'string'  # The (urlencoded) LDAP Distinguished Name (DN).
    # header parameters for this endpoint
    header = {
        'If-Match': '',  # Provide entity tag to make a conditional request to not overwrite any values in a race condition. (string)
        'If-Unmodified-Since': '',  # Provide last modified time to make a conditional request to not overwrite any values in a race condition. (string)
        'User-Agent': '',  # The user agent. (string)
        'Accept-Language': '',  # The accepted response languages. (string)
        'If-None-Match': '',  # Use request from cache by using the E-Tag entity tag if it matches. (string)
        'If-Modified-Since': '',  # Use request from cache by using the Last-Modified date if it matches. (string)
        'X-Request-Id': '',  # A request-ID used for logging and tracing. (string)
    }
    # body for this endpoint
    data = {
    }
    self.request('put', f'/univention/udm/computers/domaincontroller_slave/{dn}', name='/computers/domaincontroller_slave/{dn}', headers=header, json=data, verify=False, response_codes=[201, 202, 204])
