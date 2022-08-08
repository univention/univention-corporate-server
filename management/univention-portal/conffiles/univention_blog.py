#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Blog Portal Entry
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2017-2022 Univention GmbH
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
Create a portal entry for the Univention Blog for all Core Edition users.
"""

import sys
import subprocess


def handler(config_registry, changes):
	if config_registry.get('server/role') != 'domaincontroller_master':
		return
	ldap_base = config_registry.get('ldap/base')

	try:
		_, new_val = changes.get('license/base', [None, None])
	except ValueError:  # UCR module initialization
		new_val = changes['license/base']

	if new_val in ("UCS Core Edition", "Free for personal use edition"):
		cmd = ['univention-directory-manager', 'portals/category', 'modify', '--dn', 'cn=domain-admin,cn=category,cn=portals,cn=univention,%s' % (ldap_base,), '--ignore_not_exists', '--append', 'entries=cn=univentionblog,cn=entry,cn=portals,cn=univention,%s' % (ldap_base,)]
		process('Adding blog entry failed', cmd)
	else:
		cmd = ['univention-directory-manager', 'portals/category', 'modify', '--dn', 'cn=domain-admin,cn=category,cn=portals,cn=univention,%s' % (ldap_base,), '--ignore_not_exists', '--remove', 'entries=cn=univentionblog,cn=entry,cn=portals,cn=univention,%s' % (ldap_base,)]
		process('Removing blog entry failed', cmd)


def process(msg, cmd):
	process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
	stdout = process.communicate()[0].decode('UTF-8', 'replace')
	if process.returncode:
		print('%s: %d: %s %r' % (msg, process.returncode, stdout, cmd), file=sys.stderr)
