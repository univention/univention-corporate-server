#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Resync object from OpenLDAP to S4
#
# Copyright 2014 Univention GmbH
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

import cPickle, pickle, time, os
import ldap
import sys
import univention.uldap
from optparse import OptionParser
import univention.config_registry

class UCSResync:
	def __init__(self):
		self.configRegistry = univention.config_registry.ConfigRegistry()
		self.configRegistry.load()

	def _get_listener_dir(self):
		return self.configRegistry.get('connector/s4/listener/dir', '/var/lib/univention-connector/s4')
		
	def _generate_filename(self):
		directory = self._get_listener_dir()
		return os.path.join(directory, "%f" % time.time())

	def _dump_object_to_file(self):
		filename = self._generate_filename()
		f = open(filename, 'w+')
		os.chmod(filename, 0600)
		p = cPickle.Pickler(f)
		p.dump(self.object_data)
		p.clear_memo()
		f.close()

	def _search_ldap_object(self):
		lo = univention.uldap.getMachineConnection()
		return lo.get(self.ucs_dn, attr=['*', '+'], required=True)

	def resync(self, ucs_dn):
		self.ucs_dn = ucs_dn
		new = self._search_ldap_object()
		self.object_data = (ucs_dn, new, {}, None)
		self._dump_object_to_file()


if __name__ == '__main__':

	parser = OptionParser(usage='resync_object_from_ucs.py dn')
	(options, args) = parser.parse_args()
	
	if len(args) != 1:
		parser.print_help()
		sys.exit(2)
		

	ucs_dn = args[0]

	try:
		resync = UCSResync()
		resync.resync(ucs_dn)
	except ldap.NO_SUCH_OBJECT:
		print 'ERROR: The LDAP object %s was not found.' % ucs_dn
		sys.exit(1)
	
	print 'The resync of %s has been initialized.' % ucs_dn

	sys.exit(0)

