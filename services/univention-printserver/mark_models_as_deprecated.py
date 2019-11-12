#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017-2019 Univention GmbH
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
import optparse
import ldap.filter

import univention.config_registry
import univention.admin.modules
import univention.admin.uldap


class UpdatePrinterModels(object):

	def __init__(self, options, obsolete):
		self.options = options
		self.ucr = univention.config_registry.ConfigRegistry()
		self.ucr.load()
		self.obsolete = obsolete
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

	def get_description_from_ppd(self, ppd):
		ppd_path = os.path.join('/usr/share/ppd/', ppd)
		nickname = manufacturer = None
		if os.path.isfile(ppd_path):
			if ppd_path.endswith('.ppd.gz'):
				fh = gzip.open(ppd_path)
			else:
				fh = open(ppd_path)
			for line in fh:
				if line.startswith('*NickName:'):
					nickname = line.split('"')[1]
				if line.startswith('*Manufacturer:'):
					manufacturer = line.split('"')[1].replace('(', '').replace(')', '').replace(' ', '')
				if manufacturer and nickname:
					break
			fh.close()
		return (manufacturer, nickname)

	def check_duplicates(self):
		for dn, attr in self.lo.search('(&(printermodel=*)(objectClass=univentionPrinterModels))'):
			ldap_models = attr.get('printerModel', [])
			new_ldap_models = list()
			ppds = dict()
			for model in ldap_models:
				ppd = model.split('"')[1]
				if ppd in ppds:
					ppds[ppd].append(model)
				else:
					ppds[ppd] = [model]
			for ppd in ppds:
				if len(ppds[ppd]) > 1:
					_tmp, new_description = self.get_description_from_ppd(ppd)
					new_ldap_models.append('"%s" "%s"' % (ppd, new_description))
				else:
					new_ldap_models.append(ppds[ppd][0])
			model_diff = set(ldap_models).difference(new_ldap_models)
			if model_diff:
				if self.options.verbose:
					print('removing duplicate models for %s:' % dn)
					print('\t' + '\n\t'.join(model_diff))
				if not options.dry_run:
					changes = [('printerModel', ldap_models, new_ldap_models)]
					self.lo.modify(dn, changes)

	def mark_as_obsolete(self):
		obj = self.models.lookup(None, self.lo, ldap.filter.filter_format('name=%s', [options.name]))
		if obj:
			obj = obj[0]
			obj.open()
			changed = False
			for model in self.obsolete:
				ppd = model.split('"')[1]
				des = model.split('"')[3]
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
	usage = '%prog [options] [MODEL, MODEL, ...]'
	parser = optparse.OptionParser(usage=usage)
	parser.add_option('--dry-run', '-d', action='store_true', dest='dry_run', help='Do not modify objects')
	parser.add_option('--verbose', '-v', action='store_true', dest='verbose', help='Enable verbose output')
	parser.add_option('--check-duplicate', '-c', action='store_true', dest='check_duplicate', help='Check for duplicate models')
	parser.add_option('--binddn', action='store', dest='binddn', help='LDAP bind dn for UDM CLI operation')
	parser.add_option('--bindpwd', action='store', dest='bindpwd', help='LDAP bind password for bind dn')
	parser.add_option('--bindpwdfile', action='store', dest='bindpwdfile', help='LDAP bind password file for bind dn')
	parser.add_option('--name', action='store', dest='name', help='name of the settings/printermodel object to modify')
	parser.add_option('--version', action='store', dest='version', help='only available in this version or older', default='4.2')
	options, args = parser.parse_args()
	if options.name and args:
		upm = UpdatePrinterModels(options, args)
		upm.mark_as_obsolete()
	elif options.check_duplicate:
		upm = UpdatePrinterModels(options, args)
		upm.check_duplicates()
	else:
		if options.verbose:
			print('info: do nothing, no model and/or name given')
