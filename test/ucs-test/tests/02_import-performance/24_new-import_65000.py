#!/usr/share/ucs-test/runner python3
## desc: Import 65.000 users in 128 schools 2560 class with the new import script and test the performance
## tags: [newimport65000,performance]
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
    CSV_IMPORT_FILE = '/tmp/import65000.csv'
    ous = 99
    teachers = 512
    staff = 150
    staffteachers = 60
    students = 64278
    classes = 2560

    MAX_SECONDS_OU_CREATION = 30 * 60
    MAX_SECONDS_IMPORT = 16 * 3600
    MAX_SECONDS_SAMBA_IMPORT = 31 * 3600 + CONNECTOR_WAIT_TIME
    MAX_SECONDS_ADMIN_AUTH = 8
    MAX_SECONDS_ADMIN_AUTH_UDM_LOAD = 13
    MAX_SECONDS_USER_CREATION = 110 + CONNECTOR_WAIT_TIME
    MAX_SECONDS_USER_AUTH = 2
    MAX_SECONDS_PASSWORD_RESET = 120 + CONNECTOR_WAIT_TIME


if __name__ == '__main__':
    sys.exit(run_performance(Data()))

# vim: set filetype=python
