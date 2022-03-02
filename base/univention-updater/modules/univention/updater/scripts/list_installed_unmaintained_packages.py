#!/usr/bin/python3
#
# Copyright 2021-2022 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

"""
This script lists all currently installed packages that are not maintained by Univention.
"""

from argparse import ArgumentParser, FileType, Namespace
from os import get_terminal_size
from sys import exit, stdout
from textwrap import TextWrapper
from typing import IO, Set, Tuple

import apt

MAINTAINED_PACKAGES = '/usr/share/univention-errata-level/maintained-packages.txt'


def main() -> int:
	args = parse_args()
	installed_unmaintained_packages = get_unmaintained_packages(args.maintained)
	print_packages(installed_unmaintained_packages)

	return 1 if installed_unmaintained_packages else 0


def parse_args() -> Namespace:
	parser = ArgumentParser(description=__doc__)
	parser.add_argument(
		"--maintained", "-m",
		default=MAINTAINED_PACKAGES,
		type=FileType("r"),
		help="List of maintained packages [%(default)s]")

	return parser.parse_args()


def get_unmaintained_packages(maintained: IO[str]) -> Set[str]:
	installed_packages, installed_from_maintained_repo = get_installed_packages()
	maintained_packages = get_maintained_packages(maintained)
	return installed_packages - maintained_packages - installed_from_maintained_repo


def get_installed_packages() -> Tuple[Set[str], Set[str]]:
	cache = apt.Cache()
	installed_packages = set()
	from_maintained_repo = set()
	for package in cache:
		if cache[package.name].is_installed:
			installed_packages.add(package.name)
			# maintained components
			if next((True for i in package.candidate.uris if '/maintained/component/' in i), False):
				# TODO also test package.candidate.origins
				#  [<Origin component:'' archive:'' origin:'Univention' label:'Univention' site:'appcenter.software-univention.de' isTrusted:True>,
				#   <Origin component:'now' archive:'now' origin:'' label:'' site:'' isTrusted:False>]
				# e.g. site is appcenter.software-univention.de or service.univention.de, or isTrusted is True
				from_maintained_repo.add(package.name)
	return installed_packages, from_maintained_repo


def get_maintained_packages(maintained: IO[str]) -> Set[str]:
	return set(line.strip() for line in maintained)


def print_packages(packages: Set[str]) -> None:
	if packages:
		print_unmaintained_packages(packages)
	else:
		print_all_maintained()


def print_unmaintained_packages(packages: Set[str]) -> None:
	print('The following packages are unmaintained:')
	print_wrapped(' '.join(sorted(packages)))


def print_wrapped(text: str) -> None:
	wrapper = TextWrapper(
		width=get_columns() - 20,
		initial_indent=' ',
		subsequent_indent=' ',
		break_long_words=False,
		break_on_hyphens=False,
	)
	print('\n'.join(wrapper.wrap(text)))


def get_columns() -> int:
	return get_terminal_size().columns if stdout.isatty() else 80


def print_all_maintained():
	print('No unmaintained packages installed.')


if __name__ == '__main__':
	exit(main())
