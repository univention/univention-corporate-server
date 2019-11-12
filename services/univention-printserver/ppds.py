#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Print Server
#  helper script: prints out a list of univention admin commands to create
#  settings/printermodel objects for all existing PPDs
#
# Copyright 2004-2019 Univention GmbH
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

from __future__ import print_function

import os
import gzip
import univention.uldap


def get_ppd_infos(filename):
	nickname = manufacturer = None

	if filename.endswith('.ppd.gz'):
		file = gzip.open(filename)
	else:
		file = open(filename)
	for line in file:
		if line.startswith('*NickName:'):
			nickname = line.split('"')[1]
		if line.startswith('*Manufacturer:'):
			manufacturer = line.split('"')[1].replace('(', '').replace(')', '').replace(' ', '')
		if manufacturer and nickname:
			break
	return (manufacturer, nickname)


def get_udm_command(manufacturer, models):
	models.sort()
	create = 'univention-directory-manager settings/printermodel create "$@" --ignore_exists --position "cn=cups,cn=univention,$ldap_base" --set name="%s"' % manufacturer
	modify = 'univention-directory-manager settings/printermodel modify "$@" --ignore_exists --dn "cn=%s,cn=cups,cn=univention,$ldap_base"' % manufacturer
	rest = [r'--append printmodel="\"%s\" \"%s\""' % (path, name) for path, name in models]
	rest.insert(0, modify)
	return '# Manufacturer: %s Printers: %d\n' % (manufacturer, len(models)) + create + '\n' + ' \\\n\t'.join(rest)


def __check_dir(commands, dirname, files):
	for file in files:
		filename = os.path.join(dirname, file)
		if os.path.isfile(filename) and (filename.endswith('.ppd') or filename.endswith('.ppd.gz')):
			rel_path = filename[len('/usr/share/ppd/'):]
			manu, nick = get_ppd_infos(filename)
			commands.setdefault(manu, []).append((rel_path, nick))
	return files


def check_obsolete():
	# check old models
	lo = univention.uldap.getMachineConnection()
	res = lo.search(filter='(objectClass=univentionPrinterModels)', attr=['printerModel', 'cn'])
	print('# mark old ppd\'s as obsolete\n')
	for dn, attr in res:
		cn = attr.get('cn')[0]
		obsolete = dict()
		for i in attr.get('printerModel'):
			if i in ['"None" "None"', '"smb" "smb"']:
				continue
			ppd = i.split('"')[1]
			ppd_path = os.path.join('/usr', 'share', 'ppd', ppd)
			if not os.path.isfile(ppd_path):
				if cn not in obsolete:
					obsolete[cn] = list()
				obsolete[cn].append(i)
		for cn in obsolete:
			print('/usr/lib/univention-printserver/univention-ppds/mark_models_as_deprecated.py "$@" --name "%s" \\' % cn)
			print('\t\'' + '\' \\\n\t\''.join(obsolete[cn]) + '\'')


if __name__ == '__main__':
	printers = {}
	cmds = []
	os.path.walk('/usr/share/ppd/', __check_dir, printers)
	for manu, models in list(printers.items()):
		cmds.append(get_udm_command(manu, models))
	print('\n\n'.join(cmds))
	check_obsolete()
