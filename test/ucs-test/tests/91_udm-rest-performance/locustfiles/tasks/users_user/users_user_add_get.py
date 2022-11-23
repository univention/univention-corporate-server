# Get a template for creating an User object (contains all properties and their default values)
# Empty description
# # this file implements the Locust task for the following endpoints:
# # - GET /users/user/add
#


def users_user_add_get(self):
    """GET /users/user/add"""
    # query parameters for this endpoint
    query = {
        'position': '',  # Position which is used as search base. (string)
        'superordinate': '',  # The superordinate DN of the object to create. `position` is sufficient. (string)
        'template': '',  # **Experimental**: A |UDM| template object. (string)
    }
    # header parameters for this endpoint
    header = {
        'User-Agent': '',  # The user agent. (string)
        'Accept-Language': '',  # The accepted response languages. (string)
        'If-None-Match': '',  # Use request from cache by using the E-Tag entity tag if it matches. (string)
        'If-Modified-Since': '',  # Use request from cache by using the Last-Modified date if it matches. (string)
        'X-Request-Id': '',  # A request-ID used for logging and tracing. (string)
    }
    self.request('get', '/univention/udm/users/user/add', name='/users/user/add', headers=header, params=query, verify=False, response_codes=[200])
