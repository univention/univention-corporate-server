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
    ('(uid=testuser1111*)', 11),
    ('(uid=testuser222*)', 11),
    ('(uid=testuser333*)', 11),
    ('(uid=testuser444*)', 11),
    ('(uid=testuser555*)', 11),
    ('(uid=testuser666*)', 11),
    ('(uid=testuser777*)', 11),
    ('(uid=testuser888*)', 11),
    ('(uid=testuser999*)', 11),
]


# CheckStats.min_num_requests = 10
