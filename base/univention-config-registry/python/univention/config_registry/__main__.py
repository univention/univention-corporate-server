# -*- coding: utf-8 -*-
#
#  main configuration registry classes
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2022 Univention GmbH
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

"""Univention Configuration Registry."""

from __future__ import print_function

import sys

from univention.config_registry.backend import StrictModeException
from univention.config_registry.frontend import main

if __name__ == '__main__':
	try:
		sys.exit(main(sys.argv[1:]))
	except StrictModeException as ex2:
		print(('E: UCR is running in strict mode and thus cannot accept the given input:'), file=sys.stderr)
		print(ex2, file=sys.stderr)
		sys.exit(1)

# vim:set sw=4 ts=4 noet:
