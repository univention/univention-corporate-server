# Modify or move an Replica Directory Node object
# Empty description
# # this file implements the Locust task for the following endpoints:
# # - PUT /computers/domaincontroller_slave/{dn}
#
import urllib.parse


def computers_domaincontroller_slave_dn_put(self):
    """PUT /computers/domaincontroller_slave/{dn}"""
    dn = self.test_data.random_domain_controller_slave(only_dn=True, pop=True)  # The (urlencoded) LDAP Distinguished Name (DN).
    # header parameters for this endpoint
    header = {
        # 'If-Match': '',  # Provide entity tag to make a conditional request to not overwrite any values in a race condition. (string)
        # 'If-Unmodified-Since': '',  # Provide last modified time to make a conditional request to not overwrite any values in a race condition. (string)
        # 'User-Agent': '',  # The user agent. (string)
        # 'Accept-Language': '',  # The accepted response languages. (string)
        # 'If-None-Match': '',  # Use request from cache by using the E-Tag entity tag if it matches. (string)
        # 'If-Modified-Since': '',  # Use request from cache by using the Last-Modified date if it matches. (string)
        'X-Request-Id': '218d9124-c0dc-415e-8417-a0fa197ee099',  # A request-ID used for logging and tracing. (string)
    }
    # body for this endpoint
    data = {
        "position": self.data["position"],
        "properties": {}
    }
    url_encoded_dn = urllib.parse.quote(dn)
    self.request('put', f'/univention/udm/computers/domaincontroller_slave/{url_encoded_dn}', name='/computers/domaincontroller_slave/{dn}', headers=header, json=data, verify=False, response_codes=[201, 202, 204])
