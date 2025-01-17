#!/usr/share/ucs-test/runner python3
## desc: Import 500 users in 1 schools with the new import script and test the performance
## tags: [newimport500,performance]
## roles: [domaincontroller_master]
## exposure: dangerous
## timeout: 0
## packages:
##   - ucs-school-import
##   - univention-s4-connector
##   - univention-samba4
## bugs: [43936]

import sys

from performanceutils import CONNECTOR_WAIT_TIME, run_performance


test = set()
test.update()


class Data:
    CSV_IMPORT_FILE = '/tmp/import500.csv'
    ous = 1
    teachers = 8
    staff = 5
    staffteachers = 2
    students = 485
    classes = 20

    MAX_SECONDS_OU_CREATION = 30 * 60
    MAX_SECONDS_IMPORT = 8 * 60
    MAX_SECONDS_SAMBA_IMPORT = 15 * 60 + CONNECTOR_WAIT_TIME
    MAX_SECONDS_ADMIN_AUTH = 5
    MAX_SECONDS_ADMIN_AUTH_UDM_LOAD = 10
    MAX_SECONDS_USER_CREATION = 25 + CONNECTOR_WAIT_TIME
    MAX_SECONDS_USER_AUTH = 5
    MAX_SECONDS_PASSWORD_RESET = 90 + CONNECTOR_WAIT_TIME


if __name__ == '__main__':
    sys.exit(run_performance(Data()))

# vim: set filetype=python
