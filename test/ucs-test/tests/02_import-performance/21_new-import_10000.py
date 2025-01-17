#!/usr/share/ucs-test/runner python3
## desc: Import 10.000 users in 20 schools with the new import script and test the performance
## tags: [newimport10000,performance]
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
    CSV_IMPORT_FILE = '/tmp/import10000.csv'
    ous = 20
    teachers = 800
    staff = 500
    staffteachers = 200
    students = 8500
    classes = 400

    MAX_SECONDS_OU_CREATION = 30 * 60
    MAX_SECONDS_IMPORT = 4 * 3600
    MAX_SECONDS_SAMBA_IMPORT = 4 * 3600 + CONNECTOR_WAIT_TIME
    MAX_SECONDS_ADMIN_AUTH_UDM_LOAD = 13
    MAX_SECONDS_ADMIN_AUTH = 8
    MAX_SECONDS_USER_CREATION = 135 + CONNECTOR_WAIT_TIME
    MAX_SECONDS_USER_AUTH = 20
    MAX_SECONDS_PASSWORD_RESET = 335 + CONNECTOR_WAIT_TIME


if __name__ == '__main__':
    sys.exit(run_performance(Data()))

# vim: set filetype=python
