# Create a new Organisational Unit object
# Empty description
# # this file implements the Locust task for the following endpoints:
# # - POST /container/ou/
#
import copy
import uuid


def container_ou_post(self):
    """POST /container/ou/"""
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
    data['properties']['name'] = self.fake.word() + str(uuid.uuid4())
    data['properties']['description'] = self.fake.sentence()
    self.request('post', '/univention/udm/container/ou/', name='/container/ou/', headers=header, json=data, verify=False, response_codes=[201])
