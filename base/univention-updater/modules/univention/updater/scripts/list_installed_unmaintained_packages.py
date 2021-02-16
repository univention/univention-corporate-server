#!/usr/bin/python3
#
# Copyright 2021 Univention GmbH
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

import os
import apt
import sys
import textwrap
import argparse

MAINTAINED_PACKAGES = '/usr/share/univention-errata/univention-maintained-packages.txt'


def get_installed_packages():
	cache = apt.Cache()
	return [package.name for package in cache if cache[package.name].is_installed]


def parse_args():
	parser = argparse.ArgumentParser(description=__doc__)
	return parser.parse_args()


def main():
	args = parse_args()
	size = os.get_terminal_size()
	try:
		with open(MAINTAINED_PACKAGES) as fd:
			installed_unmaintained_packages = list(set(get_installed_packages()) - set(fd.read().splitlines()))
			if installed_unmaintained_packages:
				print('The following packages are unmaintained:')
				text = ' '.join(installed_unmaintained_packages)
				for line in textwrap.wrap(text, width=int(size.columns - 20), break_long_words=False, break_on_hyphens=False):
					print('  ' + line)
				sys.exit(1)
			else:
				print('No unmaintained packages installed.')
	except FileNotFoundError:
		print(f'{MAINTAINED_PACKAGES} does not exist.', file=sys.stderr)
		sys.exit(1)


if __name__ == '__main__':
	main()
