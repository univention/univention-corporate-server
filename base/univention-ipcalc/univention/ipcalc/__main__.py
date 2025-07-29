#!/usr/bin/python3
# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Univention IP Calculator for DNS records (IPv6 edition)."""


import ipaddress
import sys
from argparse import ArgumentParser, Namespace

from univention import ipcalc


def parse_options(args: list[str] | None = None) -> Namespace:
    """Parse command line options."""
    epilog = 'Calculate network values from network address for DNS records.'
    parser = ArgumentParser(epilog=epilog)
    parser.add_argument(
        '--ip', dest='address',
        required=True,
        type=ipaddress.ip_address,
        help='IPv4 or IPv6 address')
    parser.add_argument(
        '--netmask', dest='netmask',
        required=True,
        help='Netmask or prefix length')
    parser.add_argument(
        '--output', dest='output',
        required=True,
        choices=('network', 'reverse', 'pointer'),
        help='Specify requested output type')
    parser.add_argument(
        '--calcdns', dest='calcdns',
        action='store_true',
        required=True,
        help='Request to calcuale DNS record entries')

    opt = parser.parse_args(args)

    try:
        opt.network = ipaddress.ip_interface('%s/%s' % (opt.address, opt.netmask))
    except ValueError as ex:
        parser.error("Invalid --netmask: %s" % (ex,))

    return opt


def main(args: list[str] | None = None) -> None:
    """Calculate IP address parameters-"""
    options = parse_options(args)

    if isinstance(options.network, ipaddress.IPv6Interface):
        family = 'ipv6'
    elif isinstance(options.network, ipaddress.IPv4Interface):
        family = 'ipv4'
    else:  # pragma: no cover
        sys.exit("Unknown address format")

    func = getattr(ipcalc, 'calculate_%s_%s' % (family, options.output))
    result = func(options.network)
    print(result)


if __name__ == "__main__":
    main()
