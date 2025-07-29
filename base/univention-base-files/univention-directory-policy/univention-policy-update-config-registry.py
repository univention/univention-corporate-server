#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2007-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Apply LDAP UCR policy to local UCR."""


import argparse
import os
import sys

import univention.config_registry as confreg
from univention.config_registry import ucr
from univention.lib.policy_result import PolicyResultFailed, ucr_policy_result


def get_policy(host_dn, server=None, password_file="/etc/machine.secret", verbose=False):
    """Retrieve policy for host_dn."""
    try:
        (results, _) = ucr_policy_result(dn=host_dn, binddn=host_dn, bindpw=password_file, ldap_server=server)
    except PolicyResultFailed as ex:
        if verbose:
            print('WARN: failed to execute univention_policy_result: %s' % (ex,), file=sys.stderr)
        sys.exit(1)
    return results


def parse_cmdline() -> argparse.Namespace:
    """Parse command line and return options and DN."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-a', '--setall', action='store_true', help='write all variables set by policy')
    parser.add_argument('-s', '--simulate', action='store_true', help='simulate update and show values to be set')
    parser.add_argument('-v', '--verbose', action='store_true', help='print verbose information')
    parser.add_argument('-l', '--ldap-server', dest='server', help='connect to this ldap host')
    parser.add_argument('-y', '--password-file', type=argparse.FileType('r'), default='/etc/machine.secret', help='password file to connect to ldap host')
    parser.add_argument('hostdn', nargs='?', default=ucr.get('ldap/hostdn'), help='distinguished LDAP name of the host')
    args = parser.parse_args()

    if 'UNIVENTION_BASECONF' in os.environ:
        del os.environ['UNIVENTION_BASECONF']

    if args.hostdn is None:
        parser.error('ERROR: cannot get ldap/hostdn')

    if args.simulate:
        print('Simulating update...', file=sys.stderr)

    return args


def main() -> None:
    """Apply LDAP UCR policy to local UCR."""
    args = parse_cmdline()

    confregfn = os.path.join(confreg.ConfigRegistry.PREFIX, confreg.ConfigRegistry.BASES[confreg.ConfigRegistry.LDAP])
    ucr_ldap = confreg.ConfigRegistry(filename=confregfn)
    ucr_ldap.load()
    set_list = get_policy(args.hostdn, args.server, args.password_file.name, verbose=args.verbose)
    if set_list:
        new_set_list = []
        for key, values in set_list.items():
            value = values[0]
            record = '%s=%s' % (key, value)

            if ucr_ldap.get(key) != value or args.setall:
                new_set_list.append(record)

        if args.simulate or args.verbose:
            for item in new_set_list:
                print('Setting %s' % item, file=sys.stderr)
        if not args.simulate:
            confreg.handler_set(new_set_list, {'ldap-policy': True})

    unset_list = []
    for key, value in ucr_ldap.items():
        if key not in set_list:
            unset_list.append(key)
    if unset_list:
        if args.simulate or args.verbose:
            for item in unset_list:
                print('Unsetting %s' % item, file=sys.stderr)
        if not args.simulate:
            confreg.handler_unset(unset_list, {'ldap-policy': True})


if __name__ == '__main__':
    main()
