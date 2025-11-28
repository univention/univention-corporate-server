#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker Search10UsersLoad
## desc: "UDM REST API performance test for user search operations"
## exposure: safe
## env:
##   LOCUST_SPAWN_RATE: "0.1"
##   LOCUST_RUN_TIME: "2m"
##   LOCUST_USERS: "20"
##   LOCUST_LOGLEVEL: INFO
##   TIMEOUT: "300"

from locustfile import CheckStats, UserSearchTest as Search10UsersLoad  # noqa: F401


Search10UsersLoad.filters_expected_results = [
    ('(uid=testuser1111*)', 10),
    ('(uid=testuser2222*)', 10),
    ('(uid=testuser3333*)', 10),
    ('(uid=testuser4444*)', 10),
    ('(uid=testuser5555*)', 10),
    ('(uid=testuser6666*)', 10),
    ('(uid=testuser7777*)', 10),
    ('(uid=testuser8888*)', 10),
    ('(uid=testuser9999*)', 10),
]


# CheckStats.min_num_requests = 10
