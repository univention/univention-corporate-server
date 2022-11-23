# Search for Groups objects
# Information about the object type and links to search for objects. The found objects are either referenced as HAL links or embedded via HAL embedded resources.
# # this file implements the Locust task for the following endpoints:
# # - GET /groups/group/
#


def groups_group_get(self):
    """GET /groups/group/"""
    # query parameters for this endpoint
    query = {
        'filter': '',  # A LDAP filter which may contain `UDM` property names instead of `LDAP` attribute names. (string)
        'position': '',  # Position which is used as search base. (string)
        'scope': '',  # The LDAP search scope (sub, base, one). (string)
        'query': '',  # The values to search for (propertyname and search filter value). Alternatively with `filter` a raw LDAP filter can be given. (object)
        'hidden': True,  # Include hidden/system objects in the response. (boolean)
        'properties': '',  # The properties which should be returned, if not given all properties are returned. (array)
        'limit': '',  # **Broken/Experimental**: How many results should be shown per page. (integer)
        'page': 1,  # **Broken/Experimental**: The search page, starting at one. (integer)
        'dir': '',  # **Broken/Experimental**: The Sort direction (ASC or DESC). (string)
        'by': '',  # **Broken/Experimental**: Sort the search result by the specified property. (string)
    }
    # header parameters for this endpoint
    header = {
        'User-Agent': '',  # The user agent. (string)
        'Accept-Language': '',  # The accepted response languages. (string)
        'If-None-Match': '',  # Use request from cache by using the E-Tag entity tag if it matches. (string)
        'If-Modified-Since': '',  # Use request from cache by using the Last-Modified date if it matches. (string)
        'X-Request-Id': '',  # A request-ID used for logging and tracing. (string)
    }
    self.request('get', '/univention/udm/groups/group/', name='/groups/group/', headers=header, params=query, verify=False, response_codes=[200])
