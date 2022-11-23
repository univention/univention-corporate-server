# Remove a Users object
# Empty description
# # this file implements the Locust task for the following endpoints:
# # - DELETE /users/user/{dn}
#
import urllib.parse


def users_user_dn_delete(self):
    """DELETE /users/user/{dn}"""
    dn = self.test_data.random_user(only_dn=True, pop=True, role=self.role)  # The (urlencoded) LDAP Distinguished Name (DN).
    # query parameters for this endpoint
    query = {
        'cleanup': 'true',  # Whether to perform a cleanup (e.g. of temporary objects, locks, etc). (boolean)
        'recursive': 'true',  # Whether to remove referring objects (e.g. DNS or DHCP references). (boolean)
    }
    # header parameters for this endpoint
    header = {
        # 'User-Agent': '',  # The user agent. (string)
        # 'Accept-Language': '',  # The accepted response languages. (string)
        # 'If-None-Match': '',  # Use request from cache by using the E-Tag entity tag if it matches. (string)
        # 'If-Modified-Since': '',  # Use request from cache by using the Last-Modified date if it matches. (string)
        'X-Request-Id': '218d9124-c0dc-415e-8417-a0fa197ee099',  # A request-ID used for logging and tracing. (string)
    }
    url_encode_dn = urllib.parse.quote(dn)
    self.request('delete', f'/univention/udm/users/user/{url_encode_dn}', name=f'/users/user/{"dn_" + self.role}', headers=header, params=query, verify=False, response_codes=[204])
