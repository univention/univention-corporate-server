#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
UCS installation via vnc
"""

from argparse import ArgumentParser
from installation import UCSInstallation
from components.components import components_with_steps as components

import sys


def main():
	''' python %prog% --vnc 'utby:1' '''
	parser = ArgumentParser(description=__doc__)
	parser.add_argument('--vnc', required=True)
	parser.add_argument('--fqdn', default='master.ucs.local')
	parser.add_argument('--ip', help='Give an IP address, if DHCP is unavailable.')
	parser.add_argument('--password', default='univention')
	parser.add_argument('--organisation', default='ucs')
	parser.add_argument('--screenshot-dir', default='./screenshots')
	parser.add_argument('--dns')
	parser.add_argument('--netmask')
	parser.add_argument('--gateway')
	parser.add_argument('--join-user')
	parser.add_argument('--join-password')
	parser.add_argument('--school-dep', default=[], choices=['central', 'edu', 'adm'])
	parser.add_argument('--language', default='deu', choices=['deu', 'eng', 'fra'])
	parser.add_argument('--role', default='master', choices=['master', 'slave', 'member', 'backup', 'admember', 'basesystem', 'applianceEC2', 'applianceLVM'])
	parser.add_argument('--components', default=[], choices=components.keys() + ['all'], action='append')
	parser.add_argument('--no-second-interface', help='no not set configure second interface', action='store_true')
	args = parser.parse_args()

	if args.role in ['slave', 'backup', 'member', 'admember']:
		assert args.dns is not None
		assert args.join_user is not None
		assert args.join_password is not None

	inst = UCSInstallation(args=args)
	inst.installation()


if __name__ == '__main__':
	main()
