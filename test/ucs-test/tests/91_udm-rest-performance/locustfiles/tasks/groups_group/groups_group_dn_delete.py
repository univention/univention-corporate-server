# Remove a Groups object
# Empty description
# # this file implements the Locust task for the following endpoints:
# # - DELETE /groups/group/{dn}
#


def groups_group_dn_delete(self):
    """DELETE /groups/group/{dn}"""
    dn = 'string'  # The (urlencoded) LDAP Distinguished Name (DN).
    # query parameters for this endpoint
    query = {
        'cleanup': True,  # Whether to perform a cleanup (e.g. of temporary objects, locks, etc). (boolean)
        'recursive': True,  # Whether to remove referring objects (e.g. DNS or DHCP references). (boolean)
    }
    # header parameters for this endpoint
    header = {
        'User-Agent': '',  # The user agent. (string)
        'Accept-Language': '',  # The accepted response languages. (string)
        'If-None-Match': '',  # Use request from cache by using the E-Tag entity tag if it matches. (string)
        'If-Modified-Since': '',  # Use request from cache by using the Last-Modified date if it matches. (string)
        'X-Request-Id': '',  # A request-ID used for logging and tracing. (string)
    }
    self.request('delete', f'/univention/udm/groups/group/{dn}', name='/groups/group/{dn}', headers=header, params=query, verify=False, response_codes=[204])
