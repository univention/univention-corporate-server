#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017-2022 Univention GmbH
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
import shlex
import argparse
import subprocess
import ldap.filter

import univention.config_registry
import univention.admin.modules
import univention.admin.uldap


class UpdatePrinterModels(object):

	def __init__(self, options):
		self.options = options
		self.ucr = univention.config_registry.ConfigRegistry()
		self.ucr.load()
		self.obsolete = options.models
		if self.options.bindpwdfile:
			with open(self.options.bindpwdfile) as f:
				self.options.bindpwd = f.readline().strip()
		self.ldap_connection()
		univention.admin.modules.update()
		self.models = univention.admin.modules.get('settings/printermodel')
		univention.admin.modules.init(self.lo, self.position, self.models)

	def ldap_connection(self):
		if self.options.binddn and self.options.bindpwd:
			self.lo = univention.admin.uldap.access(
				host=self.ucr['ldap/master'],
				port=int(self.ucr.get('ldap/master/port', '7389')),
				base=self.ucr['ldap/base'],
				binddn=self.options.binddn,
				bindpw=self.options.bindpwd,
				start_tls=2)
			self.position = univention.admin.uldap.position(self.ucr['ldap/base'])
		else:
			self.lo, self.position = univention.admin.uldap.getAdminConnection()

	def get_nickname_from_ppd(self, ppd):
		filename = os.path.join('/usr/share/ppd/', ppd)
		if not os.path.isfile(filename):
			if ':' in ppd:
				try:
					return self._get_nickname_from_ppd(subprocess.check_output([
						'/usr/lib/cups/driver/foomatic-db-compressed-ppds', 'cat', ppd
					]).splitlines())
				except subprocess.CalledProcessError:
					pass
			return
		with (gzip.open(filename, 'rb') if filename.endswith('.ppd.gz') else open(filename, 'rb')) as fd:
			return self._get_nickname_from_ppd(fd)

	def _get_nickname_from_ppd(self, fd):
		nickname = None
		for line in fd:
			if line.startswith(b'*NickName:'):
				line = line.decode('UTF-8', 'replace').split(':', 1)[1]
				nickname = shlex.split(line)[0]
				return nickname

	def check_duplicates(self):
		for obj in self.models.lookup(None, self.lo, ''):
			ppds = {}
			for model in obj['printmodel']:
				ppd = model[0]
				ppds.setdefault(ppd, []).append(model)

			duplicated_ppds = [_ppd for _ppd, model in ppds.items() if len(model) > 1]
			replacement_ppds = [
				[_ppd, str(self.get_nickname_from_ppd(_ppd))]
				for _ppd in duplicated_ppds
			]

			if duplicated_ppds:
				if self.options.verbose:
					print('removing duplicate models for %s:' % obj.dn)
					print('replace:', [' '.join(ppd_model) for ppd_model in obj['printmodel'] if ppd_model[0] in duplicated_ppds])
					print('with:', [' '.join(ppd_model) for ppd_model in replacement_ppds])

				if not options.dry_run:
					obj.open()
					obj['printmodel'] = [ppd_model for ppd_model in obj['printmodel'] if ppd_model[0] not in duplicated_ppds] + replacement_ppds
					obj.modify()

	def mark_as_obsolete(self):
		obj = self.models.lookup(None, self.lo, ldap.filter.filter_format('name=%s', [options.name]))
		if obj:
			obj = obj[0]
			obj.open()
			changed = False
			for model in self.obsolete:
				ppd, des = shlex.split(model)
				model_item = [ppd, des]
				if model_item in obj['printmodel']:
					changed = True
					obj['printmodel'].remove(model_item)
					if options.verbose:
						print('info: %s model "%s" removed' % (obj.dn, model_item))
					model_item[1] = 'deprecated (only available in %s and older) - ' % self.options.version + model_item[1]
					obj['printmodel'].append(model_item)
					if options.verbose:
						print('info: %s model "%s" added' % (obj.dn, model_item))
			if changed:
				if not options.dry_run:
					obj.modify()
				if options.verbose:
					print('info: %s modified' % obj.dn)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--dry-run', '-d', action='store_true', help='Do not modify objects')
	parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
	parser.add_argument('--check-duplicate', '-c', action='store_true', help='Check for duplicate models')
	parser.add_argument('--binddn', help='LDAP bind dn for UDM CLI operation')
	parser.add_argument('--bindpwd', help='LDAP bind password for bind dn')
	parser.add_argument('--bindpwdfile', help='LDAP bind password file for bind dn')
	parser.add_argument('--name', help='name of the settings/printermodel object to modify')
	parser.add_argument('--version', help='only available in this version or older', default='4.4')
	parser.add_argument('models', nargs='*')
	options = parser.parse_args()

	if options.name and options.models:
		upm = UpdatePrinterModels(options)
		upm.mark_as_obsolete()
	elif options.check_duplicate:
		upm = UpdatePrinterModels(options)
		upm.check_duplicates()
	else:
		if options.verbose:
			print('info: do nothing, no model and/or name given')
