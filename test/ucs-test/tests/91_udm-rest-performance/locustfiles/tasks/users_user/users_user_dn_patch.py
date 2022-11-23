# Modify an User object (moving is currently not possible)
# Empty description
# # this file implements the Locust task for the following endpoints:
# # - PATCH /users/user/{dn}
#
import urllib.parse


def users_user_dn_patch(self):
    """PATCH /users/user/{dn}"""
    dn = self.test_data.random_user(only_dn=True)  # The (urlencoded) LDAP Distinguished Name (DN).
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
        "position": ",".join(dn.split(",")[1:]),
        "properties": {
            "firstname": self.fake.first_name(),
            "lastname": self.fake.last_name(),
        }
    }
    url_encode_dn = urllib.parse.quote(dn)
    self.request('patch', f'/univention/udm/users/user/{url_encode_dn}', name='/users/user/{dn}', headers=header, json=data, verify=False, response_codes=[204])
