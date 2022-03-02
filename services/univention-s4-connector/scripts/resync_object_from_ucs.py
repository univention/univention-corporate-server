#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Resync object from OpenLDAP to S4
#
# Copyright 2014-2022 Univention GmbH
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

from six.moves import cPickle as pickle
import time
import os
import ldap
import sys
import univention.uldap
from argparse import ArgumentParser
from univention.config_registry import ConfigRegistry


class UCSResync(object):

	def __init__(self):
		self.configRegistry = ConfigRegistry()
		self.configRegistry.load()

		self.lo = univention.uldap.getMachineConnection()

	def _get_listener_dir(self):
		return self.configRegistry.get('connector/s4/listener/dir', '/var/lib/univention-connector/s4')

	def _generate_filename(self):
		directory = self._get_listener_dir()
		return os.path.join(directory, "%f" % time.time())

	def _dump_object_to_file(self, object_data):
		filename = self._generate_filename()
		with open(filename, 'wb+') as fd:
			os.chmod(filename, 0o600)
			p = pickle.Pickler(fd)
			p.dump(object_data)
			p.clear_memo()

	def _search_ldap_object_orig(self, ucs_dn):
		return self.lo.get(ucs_dn, attr=['*', '+'], required=True)

	def resync(self, ucs_dns=None, ldapfilter=None):
		treated_dns = []
		for dn, new in self.search_ldap(ucs_dns, ldapfilter):
			object_data = (dn, new, {}, None)
			self._dump_object_to_file(object_data)
			treated_dns.append(dn)

		return treated_dns

	def search_ldap(self, ucs_dns=None, ldapfilter=None):
		attr = ('*', '+')

		if ucs_dns:
			if not ldapfilter:
				ldapfilter = '(objectClass=*)'

			ldap_result = []
			missing_dns = []
			for targetdn in ucs_dns:
				try:
					result = self.lo.search(base=targetdn, scope='base', filter=ldapfilter, attr=attr)
					ldap_result.extend(result)
				except ldap.NO_SUCH_OBJECT:
					missing_dns.append(targetdn)
			if missing_dns:
				raise ldap.NO_SUCH_OBJECT(1, 'No object: %s' % (missing_dns,), [r[0] for r in ldap_result])
		else:
			ldap_result = self.lo.search(filter=ldapfilter, attr=attr)

		return ldap_result


if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument("--filter", dest="ldapfilter", help="LDAP Filter")
	parser.add_argument("dn", nargs='?', default=None)
	options = parser.parse_args()

	if not options.dn and not options.ldapfilter:
		parser.print_help()
		sys.exit(2)

	ucs_dns = list(filter(None, [options.dn]))

	treated_dns = []
	try:
		resync = UCSResync()
		treated_dns = resync.resync(ucs_dns, options.ldapfilter)
	except ldap.NO_SUCH_OBJECT as ex:
		print('ERROR: The LDAP object not found : %s' % ex.args[1])
		if len(ex.args) == 3:
			treated_dns = ex.args[2]
		sys.exit(1)
	finally:
		for dn in treated_dns:
			print('resync triggered for %s' % dn)

	if not treated_dns:
		print('No matching objects.')

	sys.exit(0)
