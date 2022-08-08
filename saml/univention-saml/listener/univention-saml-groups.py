# -*- coding: utf-8 -*-
#
# Univention SAML
# Listener module to set up SAML configuration
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2022 Univention GmbH
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
import listener
import os
import json
import pwd
import grp
import shutil

name = 'univention-saml-groups'
description = 'Write SAML enabled groups to json file, to be read by the services metadata.php'
filter = '(objectClass=univentionSAMLEnabledGroup)'
attributes = ['enabledServiceProviderIdentifierGroup']
path = '/etc/simplesamlphp/serviceprovider_enabled_groups.json'
tmp_path = '/etc/simplesamlphp/serviceprovider_enabled_groups.json.tmp'
uid = pwd.getpwnam("samlcgi").pw_uid
gid = grp.getgrnam("samlcgi").gr_gid


def handler(dn, new, old):
	# type: (str, dict, dict) -> None
	listener.setuid(0)

	try:
		if os.path.exists(path):
			with open(path) as group_file:
				data = json.load(group_file)
		else:
			data = {}

		new_sp = new.get('enabledServiceProviderIdentifierGroup', [])
		old_sp = old.get('enabledServiceProviderIdentifierGroup', [])
		sp_to_add = []
		sp_to_rm = []

		if new_sp != old_sp:
			if len(new_sp) > len(old_sp):
				for sp in list(set(new_sp) - set(old_sp)):
					sp_to_add.append(sp)
			else:
				for sp in list(set(old_sp) - set(new_sp)):
					sp_to_rm.append(sp)

		for sp in sp_to_add:
			sp = sp.decode('UTF-8')
			data.setdefault(sp, [])
			if dn not in data[sp]:
				data[sp].append(dn)
		for sp in sp_to_rm:
			sp = sp.decode('UTF-8')
			data.setdefault(sp, [])
			if dn in data[sp]:
				data[sp].remove(dn)

		with open(tmp_path, 'w+') as outfile:
			json.dump(data, outfile)

		shutil.move(tmp_path, path)
		os.chmod(path, 0o600)
		os.chown(path, uid, gid)
	finally:
		listener.unsetuid()
