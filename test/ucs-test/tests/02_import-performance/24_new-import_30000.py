#!/usr/share/ucs-test/runner python3
## desc: Import 30000 users in 60 schools 1200 class with the new import script and test the performance
## tags: [newimport30000,performance]
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
    CSV_IMPORT_FILE = '/tmp/import30000.csv'
    ous = 60
    teachers = 240
    staff = 150
    staffteachers = 60
    students = 29550
    classes = 20

    MAX_SECONDS_OU_CREATION = 30 * 60
    MAX_SECONDS_IMPORT = 22 * 3600
    MAX_SECONDS_SAMBA_IMPORT = 128 * 3600 + CONNECTOR_WAIT_TIME
    MAX_SECONDS_ADMIN_AUTH = 8
    MAX_SECONDS_ADMIN_AUTH_UDM_LOAD = 13
    MAX_SECONDS_USER_CREATION = 135 + CONNECTOR_WAIT_TIME
    MAX_SECONDS_USER_AUTH = 20
    MAX_SECONDS_PASSWORD_RESET = 335 + CONNECTOR_WAIT_TIME


if __name__ == '__main__':
    sys.exit(run_performance(Data()))

# vim: set filetype=python
