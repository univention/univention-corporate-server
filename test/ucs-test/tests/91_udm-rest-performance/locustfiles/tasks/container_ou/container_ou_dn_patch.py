# Modify an Organisational Unit object (moving is currently not possible)
# Empty description
# # this file implements the Locust task for the following endpoints:
# # - PATCH /container/ou/{dn}
#


def container_ou_dn_patch(self):
    """PATCH /container/ou/{dn}"""
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
    self.request('patch', f'/univention/udm/container/ou/{dn}', name='/container/ou/{dn}', headers=header, json=data, verify=False, response_codes=[204])
