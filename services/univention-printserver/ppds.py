#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Print Server
#  helper script: prints out a list of UDM commands to create
#  settings/printermodel objects for all existing PPDs
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

from __future__ import print_function

import os
import sys
import gzip
import pipes
import shlex
import subprocess

import ldap.dn

import univention.uldap


def _sanitize_printer_manufacturer(manufacturer):
	"""in the past developers were unable to correctly escape shell commands.
	Therefore we need to escape the manufacturer here to match object names with prior UCS versions."""
	return manufacturer.replace('(', '').replace(')', '').replace(' ', '')


def get_ppd_infos(filename):
	with (gzip.open(filename, 'rb') if filename.endswith('.ppd.gz') else open(filename, 'rb')) as fd:
		nickname = manufacturer = None
		for line in fd:
			if line.startswith(b'*NickName:'):
				line = line.decode('UTF-8', 'replace').split(':', 1)[1]
				nickname = shlex.split(line)[0]
			elif line.startswith(b'*Manufacturer:'):
				line = line.decode('UTF-8', 'replace').split(':', 1)[1]
				manufacturer = shlex.split(line)[0]
			if manufacturer and nickname:
				break
		return (manufacturer, nickname)


def get_udm_command(manufacturer, models):
	manufacturer = _sanitize_printer_manufacturer(manufacturer)
	models.sort()
	create = 'univention-directory-manager settings/printermodel create "$@" --ignore_exists --position "cn=cups,cn=univention,$ldap_base" --set name=%s || rc=$?' % (pipes.quote(manufacturer),)
	modify = 'univention-directory-manager settings/printermodel modify "$@" --ignore_exists --dn %s"$ldap_base"' % (pipes.quote('cn=%s,cn=cups,cn=univention,' % (ldap.dn.escape_dn_chars(manufacturer),)),)
	rest = [modify] + ['--append printmodel=%s' % (pipes.quote('"%s" "%s"' % (path, name)),) for path, name in models]
	return '# Manufacturer: %s Printers: %d\n' % (manufacturer, len(models)) + create + '\n' + ' \\\n\t'.join(rest) + ' || rc=$?'


def check_dir(commands):
	for dirname, dirs, files in os.walk('/usr/share/ppd/'):
		for filename in files:
			filename = os.path.join(dirname, filename)
			if os.path.isfile(filename) and (filename.endswith('.ppd') or filename.endswith('.ppd.gz')):
				rel_path = filename[len('/usr/share/ppd/'):]
				manu, nick = get_ppd_infos(filename)
				if not manu or not nick:
					# Some ppd files don't include a manufacturer:
					# hp-ppd/HP/HP_ColorLaserJet_5-5M.ppd
					# hp-ppd/HP/HP_LaserJet_5.ppd
					# hp-ppd/HP/HP_LaserJet_5P.ppd
					print('No manufacturer/nickname found for %s: %s %s' % (rel_path, manu, nick), file=sys.stderr)
					manu = str(manu)
					nick = str(nick)
				commands.setdefault(manu, []).append((rel_path, nick))


def get_compressed_driver():
	lines = subprocess.check_output(['/usr/lib/cups/driver/foomatic-db-compressed-ppds', 'list']).decode('UTF-8').splitlines()
	return [shlex.split(line) for line in lines]


def check_compressed(commands):
	for driver, lang, manufacturer, nickname, comments in get_compressed_driver():
		commands.setdefault(manufacturer, []).append((driver, nickname))


def check_obsolete():
	# check old models
	lo = univention.uldap.getMachineConnection()
	res = lo.search(filter='(objectClass=univentionPrinterModels)', attr=['printerModel', 'cn'])
	print('\n# mark old ppd\'s as obsolete\n')
	compressed_ppds = [driver[0] for driver in get_compressed_driver()]
	for dn, attr in res:
		cn = attr['cn'][0].decode('UTF-8')
		obsolete = {}
		for i in attr.get('printerModel', []):
			i = i.decode('UTF-8')
			if i in ['"None" "None"', '"smb" "smb"']:
				continue
			ppd = shlex.split(i)[0]
			ppd_path = os.path.join('/usr/share/ppd/', ppd)
			if not os.path.isfile(ppd_path) and ppd not in compressed_ppds:
				obsolete.setdefault(cn, []).append(i)
		for cn in obsolete:
			print('/usr/lib/univention-printserver/univention-ppds/mark_models_as_deprecated.py "$@" --verbose --name %s \\' % (pipes.quote(cn),))
			print('\t' + ' \\\n\t'.join(map(pipes.quote, obsolete[cn])) + ' || rc=$?\n')


def main():
	printers = {}
	cmds = []
	check_dir(printers)
	check_compressed(printers)
	for manu, models in printers.items():
		cmds.append(get_udm_command(manu, models))
	print('\n\n'.join(cmds))
	check_obsolete()


if __name__ == '__main__':
	main()
