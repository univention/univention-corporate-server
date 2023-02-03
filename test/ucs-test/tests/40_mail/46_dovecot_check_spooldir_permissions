#!/usr/share/ucs-test/runner python3
## desc: Dovecot, check permissions of spool directory
## tags: [apptest]
## exposure: safe
## packages:
##  - univention-mail-dovecot

import grp
import os
import pwd

from univention.testing import utils


DIR_SPOOL_DOVECOT = '/var/spool/univention-mail-dovecot'
EXPECTED_USER = 'listener'
EXPECTED_GROUP = 'root'
EXPECTED_MODE = '0700'


def main():
    if not os.path.exists(DIR_SPOOL_DOVECOT):
        utils.fail(f'{DIR_SPOOL_DOVECOT!r} does not exist')

    result = os.stat(DIR_SPOOL_DOVECOT)

    username = pwd.getpwuid(result.st_uid).pw_name
    if username != EXPECTED_USER:
        utils.fail(f'{DIR_SPOOL_DOVECOT!r} is not owned by user {EXPECTED_USER!r}: currently owned by user {username!r}')

    grpname = grp.getgrgid(result.st_gid).gr_name
    if grpname != EXPECTED_GROUP:
        utils.fail(f'{DIR_SPOOL_DOVECOT!r} is not owned by user {EXPECTED_USER!r}; currently owned by group {grpname!r}')

    mode = oct(result.st_mode)[-4:]
    if mode != EXPECTED_MODE:
        utils.fail(f'{DIR_SPOOL_DOVECOT!r} has wrong permissions: expected={EXPECTED_MODE!r}  currently={mode!r}')


if __name__ == '__main__':
    main()
