#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker Search1000UsersLoad
## desc: "UDM REST API performance test for user search operations"
## exposure: safe
## env:
##   LOCUST_SPAWN_RATE: "0.1"
##   LOCUST_RUN_TIME: "2m"
##   LOCUST_USERS: "20"
##   LOCUST_LOGLEVEL: INFO
##   TIMEOUT: "300"

from locustfile import CheckStats, UserSearchTest as Search1000UsersLoad  # noqa: F401


Search1000UsersLoad.filters_expected_results = [
    ('(uid=testuser11*)', 1111),
    ('(uid=testuser2*)', 1111),
    ('(uid=testuser3*)', 1111),
    ('(uid=testuser4*)', 1111),
    ('(uid=testuser5*)', 1111),
    ('(uid=testuser6*)', 1111),
    ('(uid=testuser7*)', 1111),
    ('(uid=testuser8*)', 1111),
    ('(uid=testuser9*)', 1111),
]


# CheckStats.min_num_requests = 10
