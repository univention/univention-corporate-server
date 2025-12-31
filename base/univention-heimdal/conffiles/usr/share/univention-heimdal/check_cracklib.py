#!/usr/bin/python3
# @%@UCRWARNING=# @%@
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import sys

import univention.password


def main():
    params = {}
    end = False
    while not end:
        line = sys.stdin.readline()
        line = line[:-1]
        if line == 'end':
            end = True
            continue

        try:
            key, val = line.split(': ', 1)
        except Exception:
            print('key value pair is not correct: %s' % (line,))
            sys.exit(1)
        params[key] = val

    if 'new-password' not in params:
        print('missing password')
        sys.exit(1)

    if 'principal' in params:
        pwdCheck = univention.password.Check(None, params['principal'])
        try:
            pwdCheck.check(params['new-password'])
            print('APPROVED')
        except univention.password.CheckFailed as exc:
            print(str(exc))


try:
    main()
except Exception:
    import traceback
    print(traceback.format_exc().replace('\n', ' '))  # heimdal-kdc / kpasswd only displays the first line as error message.
    sys.exit(1)
