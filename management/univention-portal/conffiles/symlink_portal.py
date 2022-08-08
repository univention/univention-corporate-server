#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Portal
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
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

import os
import os.path
from errno import EEXIST

portal_path = "/usr/share/univention-portal"


def handler(config_registry, changes):
	old, new = changes['portal/paths']
	if old:
		old = [o.strip() for o in old.split(",")]
	else:
		old = []
	if new:
		new = [n.strip() for n in new.split(",")]
	else:
		new = []
	for path in old:
		if path in new:
			continue
		path = os.path.normpath("/var/www" + path)
		if not os.path.islink(path) or os.path.realpath(path) != portal_path:
			print("{} does not link to the portal contents. Skipping...".format(path))
		else:
			print("Removing portal link to {}...".format(path))
			os.unlink(path)
	for path in new:
		if path in old:
			continue
		path = os.path.normpath("/var/www" + path)
		if os.path.islink(path):
			link_target = os.path.realpath(path)
			print("{} already links (to {}). Skipping...".format(path, link_target))
		else:
			print("Linking {} to portal content...".format(path))
			try:
				dirname = os.path.dirname(path)
				try:
					os.makedirs(dirname)
				except OSError as exc:
					if exc.errno != EEXIST:
						raise
			except OSError as exc:
				print("Error creating {}: {}!".format(dirname, exc))
			else:
				try:
					os.symlink(portal_path, path)
				except OSError as exc:
					print("Error creating a link from {} to {}: {}!".format(path, portal_path, exc))
