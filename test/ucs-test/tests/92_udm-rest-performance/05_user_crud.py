#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker UserCRUDTest
## desc: "UDM REST API performance test for user CRUD operations"
## exposure: dangerous
## env:
##   LOCUST_SPAWN_RATE: "0.1"
##   LOCUST_RUN_TIME: "2m"
##   LOCUST_USERS: "20"
##   LOCUST_LOGLEVEL: "INFO"
##   TIMEOUT: "300"

from locustfile import UserCRUDTest  # noqa: F401
