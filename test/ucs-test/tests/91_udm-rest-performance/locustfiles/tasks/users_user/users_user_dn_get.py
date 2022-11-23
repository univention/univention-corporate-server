# Get a representation of the User object with all its properties, policies, options, metadata and references.
# Includes also instructions how to modify, remove or move the object.

# Empty description
# # this file implements the Locust task for the following endpoints:
# # - GET /users/user/{dn}
#
import urllib.parse


def users_user_dn_get(self):
    """GET /users/user/{dn}"""
    dn = self.test_data.random_user(only_dn=True)  # The (urlencoded) LDAP Distinguished Name (DN).
    # header parameters for this endpoint
    header = {
        # 'User-Agent': '',  # The user agent. (string)
        # 'Accept-Language': '',  # The accepted response languages. (string)
        # 'If-None-Match': '',  # Use request from cache by using the E-Tag entity tag if it matches. (string)
        # 'If-Modified-Since': '',  # Use request from cache by using the Last-Modified date if it matches. (string)
        'X-Request-Id': '218d9124-c0dc-415e-8417-a0fa197ee099',  # A request-ID used for logging and tracing. (string)
    }
    url_encode_dn = urllib.parse.quote(dn)
    self.request('get', f'/univention/udm/users/user/{url_encode_dn}', name='/users/user/{dn}', headers=header, verify=False, response_codes=[200])
