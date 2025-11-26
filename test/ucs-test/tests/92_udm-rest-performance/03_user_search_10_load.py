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
    ('(uid=testuser1)', 1),
    ('(uid=testuser10)', 1),
    ('(uid=testuser100)', 1),
    ('(uid=testuser1000)', 1),
    ('(uid=testuser10000)', 1),
    ('(uid=testuser2)', 1),
    ('(uid=testuser20)', 1),
    ('(uid=testuser200)', 1),
    ('(uid=testuser2000)', 1),
]


# CheckStats.min_num_requests = 10
