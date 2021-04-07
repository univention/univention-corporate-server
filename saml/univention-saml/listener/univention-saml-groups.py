# -*- coding: utf-8 -*-
#
# Univention SAML
# Listener module to set up SAML configuration
#
# Copyright 2020-2021 Univention GmbH
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

from __future__ import absolute_import

import grp
import json
import os
import pwd
from typing import Dict, List, Set  # noqa F401

import listener

name = 'univention-saml-groups'
description = 'Write SAML enabled groups to json file, to be read by the services metadata.php'
filter = '(objectClass=univentionSAMLEnabledGroup)'
attributes = ['enabledServiceProviderIdentifierGroup']

path = '/etc/simplesamlphp/serviceprovider_enabled_groups.json'
tmp_path = '/etc/simplesamlphp/serviceprovider_enabled_groups.json.tmp'
uid = None
gid = None


@listener.SetUID(0)
def handler(dn, new, old):
	# type: (str, dict, dict) -> None
	try:
		with open(path) as group_file:
			groups = json.load(group_file)
	except Exception:
		groups = {}

	update_groups(groups, dn, get_group(old), get_group(new))

	global uid
	global gid
	if uid is None:
		uid = pwd.getpwnam("samlcgi").pw_uid
		gid = grp.getgrnam("samlcgi").gr_gid

	with open(tmp_path, 'w') as outfile:
		os.fchmod(outfile.fileno(), 0o600)
		os.fchown(outfile.fileno(), uid, gid)
		json.dump(groups, outfile)

	os.rename(tmp_path, path)


def get_group(data):
	# type: (Dict[str, List[bytes]]) -> Set[str]
	return {group.decode('UTF-8') for group in data.get("enabledServiceProviderIdentifierGroup", [])}


def update_groups(groups, dn, old_sp, new_sp):
	# type: (Dict[str, List[str]], str, Set[str], Set[str]) -> None
	for sp in new_sp - old_sp:
		group = groups.setdefault(sp, [])
		if dn not in group:
			group.append(dn)

	for sp in old_sp - new_sp:
		group = groups.setdefault(sp, [])
		if dn in group:
			group.remove(dn)
