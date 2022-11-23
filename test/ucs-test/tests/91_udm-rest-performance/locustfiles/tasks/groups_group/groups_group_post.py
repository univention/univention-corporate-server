# Create a new Group object
# Empty description
# # this file implements the Locust task for the following endpoints:
# # - POST /groups/group/
#
import copy
import uuid


def groups_group_post(self):
    """POST /groups/group/"""
    # header parameters for this endpoint
    header = {
        # 'User-Agent': '',  # The user agent. (string)
        # 'Accept-Language': '',  # The accepted response languages. (string)
        # 'If-None-Match': '',  # Use request from cache by using the E-Tag entity tag if it matches. (string)
        # 'If-Modified-Since': '',  # Use request from cache by using the Last-Modified date if it matches. (string)
        'X-Request-Id': '218d9124-c0dc-415e-8417-a0fa197ee099',  # A request-ID used for logging and tracing. (string)
    }
    # body for this endpoint
    name = self.fake.word() + str(uuid.uuid4())
    data = copy.deepcopy(self.data)
    data["properties"]["name"] = name
    data["properties"]["description"] = f"Test group {name}"
    self.request('post', '/univention/udm/groups/group/', name='/groups/group/', headers=header, json=data, verify=False, response_codes=[201])
