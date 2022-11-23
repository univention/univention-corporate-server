# Create a new User object
# Empty description
# # this file implements the Locust task for the following endpoints:
# # - POST /users/user/
#
import copy
import uuid


def users_user_post(self):
    """POST /users/user/"""
    # header parameters for this endpoint
    header = {
        # 'User-Agent': '',  # The user agent. (string)
        # 'Accept-Language': '',  # The accepted response languages. (string)
        # 'If-None-Match': '',  # Use request from cache by using the E-Tag entity tag if it matches. (string)
        # 'If-Modified-Since': '',  # Use request from cache by using the Last-Modified date if it matches. (string)
        'X-Request-Id': '218d9124-c0dc-415e-8417-a0fa197ee099',  # A request-ID used for logging and tracing. (string)
    }
    # body for this endpoint
    data = copy.deepcopy(self.data)

    data["properties"]["firstname"] = self.fake.first_name() + str(uuid.uuid4())
    data["properties"]["lastname"] = self.fake.last_name()
    data["properties"]["password"] = self.fake.password()
    data["properties"]["username"] = self.fake.user_name() + str(uuid.uuid4())

    self.request('post', '/univention/udm/users/user/', name='/users/user/', headers=header, json=data, verify=False, response_codes=[201])
