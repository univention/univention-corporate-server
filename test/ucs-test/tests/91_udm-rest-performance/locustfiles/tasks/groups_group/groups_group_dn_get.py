# Get a representation of the Group object with all its properties, policies, options, metadata and references.
# Includes also instructions how to modify, remove or move the object.
# Empty description
# # this file implements the Locust task for the following endpoints:
# # - GET /groups/group/{dn}
#
import urllib.parse


def groups_group_dn_get(self):
    """GET /groups/group/{dn}"""
    dn = self.test_data.random_group(only_dn=True)  # The (urlencoded) LDAP Distinguished Name (DN).
    # header parameters for this endpoint
    header = {
        # 'User-Agent': '',  # The user agent. (string)
        # 'Accept-Language': '',  # The accepted response languages. (string)
        # 'If-None-Match': '',  # Use request from cache by using the E-Tag entity tag if it matches. (string)
        # 'If-Modified-Since': '',  # Use request from cache by using the Last-Modified date if it matches. (string)
        'X-Request-Id': '218d9124-c0dc-415e-8417-a0fa197ee099',  # A request-ID used for logging and tracing. (string)
    }
    url_encoded_dn = urllib.parse.quote(dn)
    self.request('get', f'/univention/udm/groups/group/{url_encoded_dn}', name='/groups/group/{dn}', headers=header, verify=False, response_codes=[200])
