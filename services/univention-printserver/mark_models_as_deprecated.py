#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import optparse
import univention.config_registry
import univention.admin.modules
import univention.admin.config
import univention.admin.uldap

class obsoletePrinterModels(object):

	def __init__(self, options, obsolete):
		self.options = options
		self.ucr = univention.config_registry.ConfigRegistry()
		self.ucr.load()
		self.obsolete = obsolete
		self.get_ldap_connection()
		univention.admin.modules.update()
		self.models = univention.admin.modules.get('settings/printermodel')
		univention.admin.modules.init(self.lo, self.position, self.models)

	def get_ldap_connection(self):
		self.co = univention.admin.config.config()
		if self.options.binddn and self.options.bindpwd:
			self.lo = univention.admin.uldap.access(
				host=self.ucr['ldap/master'],
				port=int(self.ucr.get('ldap/master/port', '7389')),
				base=self.ucr['ldap/base'],
				binddn=self.options.binddn,
				bindpw=self.options.bindpwd,
				start_tls=1)
			self.position = univention.admin.uldap.position(self.ucr['ldap/base'])
		else:
			self.lo, self.position = univention.admin.uldap.getAdminConnection()
 
	def mark_as_obsolete(self):
		obj = self.models.lookup(self.co, self.lo, 'name=%s' % options.name)
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
						print 'info: %s model "%s" removed' % (obj.dn, model_item)
					model_item[1] = 'deprecated (only available in %s and older) - ' % self.options.version + model_item[1]
					obj['printmodel'].append(model_item)
					if options.verbose:
						print 'info: %s model "%s" added' % (obj.dn, model_item)
			if changed:
				if not options.dry_run:
					obj.modify()
				if options.verbose:
					print 'info: %s modified' % obj.dn
			
if __name__ == '__main__':
	usage = '%prog [options] MODEL, MODEL, ...'
	parser = optparse.OptionParser(usage=usage)
	parser.add_option('--dry-run', '-d', action='store_true', dest='dry_run', help='Do not modify objects')
	parser.add_option('--verbose', '-v', action='store_true', dest='verbose', help='Enable verbose output')
	parser.add_option('--binddn', action='store', dest='binddn', help='LDAP bind dn for UDM CLI operation')
	parser.add_option('--bindpwd', action='store', dest='bindpwd', help='LDAP bind password for bind dn')
	parser.add_option('--name', action='store', dest='name', help='name of the settings/printermodel object to modify')
	parser.add_option('--version', action='store', dest='version', help='only available in this version or older', default='4.1')
	options, args = parser.parse_args()
	if options.name and args:
		opm = obsoletePrinterModels(options, args)
		opm.mark_as_obsolete()
	else:
		if options.verbose:
			print 'info: do nothing, no model and/or name given'
