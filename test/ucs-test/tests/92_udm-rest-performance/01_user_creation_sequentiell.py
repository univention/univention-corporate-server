#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker UserCreationSequentiell
## desc: "UDM REST API performance test for sequentiell user creation operations"
## exposure: dangerous
## env:
##   LOCUST_SPAWN_RATE: "1"
##   LOCUST_RUN_TIME: "2m"
##   LOCUST_USERS: "1"
##   LOCUST_LOGLEVEL: "INFO"
##   TIMEOUT: "300"

from locustfile import CheckStats, UserCreationTest as UserCreationSequentiell  # noqa: F401


# CheckStats.min_num_requests = 600
