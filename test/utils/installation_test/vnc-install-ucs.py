#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
UCS installation via vnc
"""

from argparse import ArgumentParser

from components.components import components_with_steps as components
from installation import UCSInstallation


def main():  # type: () -> None
	parser = ArgumentParser(description=__doc__)
	parser.add_argument('--screenshot-dir', default='./screenshots', help="Directory for storing screenshots")
	parser.add_argument('--language', default='deu', choices=['deu', 'eng', 'fra'], help="Select text language")
	group = parser.add_argument_group("Virtual machine settings")
	group.add_argument('--vnc', required=True, help="VNC screen to connect to")
	group.add_argument('--no-second-interface', help='no not set configure second interface', action='store_true')
	group = parser.add_argument_group("Host settings")
	group.add_argument('--fqdn', default='master.ucs.local', help="Fully qualified host name to use")
	group.add_argument('--password', default='univention', help="Password to setup for user 'root' and/or 'Administrator'")
	group.add_argument('--organisation', default='ucs', help="Oranisation name to setup")
	group.add_argument('--role', default='master', choices=['master', 'slave', 'member', 'backup', 'admember', 'basesystem', 'applianceEC2', 'applianceLVM'], help="UCS system role")
	group.add_argument('--components', default=[], choices=list(components) + ['all'], action='append', help="UCS components to install")
	group.add_argument('--school-dep', default=[], choices=['central', 'edu', 'adm'], help="Select UCS@school role")
	group = parser.add_argument_group("Network settings")
	group.add_argument('--ip', help="IPv4 address if DHCP is unavailable")
	group.add_argument('--netmask', help="Network netmask")
	group.add_argument('--gateway', help="Default router address")
	group = parser.add_argument_group("Join settings")
	group.add_argument('--dns', help="DNS server of UCS domain")
	group.add_argument('--join-user', help="User name for UCS domain join")
	group.add_argument('--join-password', help="Password for UCS domain join")
	args = parser.parse_args()

	if args.role in ['slave', 'backup', 'member', 'admember']:
		assert args.dns is not None
		assert args.join_user is not None
		assert args.join_password is not None

	inst = UCSInstallation(args=args)
	inst.installation()


if __name__ == '__main__':
	main()
