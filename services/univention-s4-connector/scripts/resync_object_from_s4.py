#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Resync object from S4 to OpenLDAP
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

import base64
import ldap
import subprocess
import sys
import univention.uldap
from optparse import OptionParser
import univention.config_registry

import sqlite3

import samba
import ldb
from samba import dsdb
from samba.samdb import SamDB
from samba.param import LoadParm
from samba.auth import system_session
from samba.credentials import Credentials

class GuidNotFound(BaseException): pass

class S4Resync:
	def __init__(self):
		self.configRegistry = univention.config_registry.ConfigRegistry()
		self.configRegistry.load()

	def _get_guid(self):
		self.guid = None

		lp = LoadParm()
		creds = Credentials()
		creds.guess(lp) 
		samdb = SamDB(url='/var/lib/samba/private/sam.ldb', session_info=system_session(), credentials=creds, lp=lp)

		domain_dn = samdb.domain_dn()
		res = samdb.search(self.s4_dn, scope=ldb.SCOPE_BASE, attrs=["objectGuid", "uSNChanged"])

		for msg in res:
			guid = msg.get("objectGuid", idx=0)
			self.guid = base64.encodestring(guid)[:-1]
			self.usn = msg.get("uSNChanged", idx=0)

		if not self.guid:
			raise GuidNotFound
				
	def _remove_cache_entries(self):
		cache_db = sqlite3.connect('/etc/univention/connector/s4cache.sqlite')
		c = cache_db.cursor()
		c.execute("SELECT id FROM GUIDS WHERE guid='%s'" % self.guid)
		guid_ids = c.fetchone()
		if guid_ids:
			guid_id = guid_ids[0]
			c.execute("DELETE from DATA where guid_id = '%s'" % guid_id)
			c.execute("DELETE from GUIDS where id = '%s'" % guid_id)
			cache_db.commit()
		cache_db.close()

	def _add_object_to_rejected(self):
		db = sqlite3.connect('/etc/univention/connector/s4internal.sqlite')
		c = db.cursor()
		c.execute("INSERT OR REPLACE INTO 'S4 rejected' (key,value) VALUES ('%(key)s', '%(value)s');" % {'key': self.usn, 'value': self.s4_dn})
		db.commit()
		db.close()
		

	def resync(self, s4_dn):
		self.s4_dn = s4_dn
		self._get_guid()
		self._remove_cache_entries()
		self._add_object_to_rejected()


if __name__ == '__main__':

	parser = OptionParser(usage='sync_object_new_from_ucs.py dn')
	(options, args) = parser.parse_args()
	
	if len(args) != 1:
		parser.print_help()
		sys.exit(2)
		

	s4_dn = args[0]

	try:
		resync = S4Resync()
		resync.resync(s4_dn)
	except ldb.LdbError:
		print 'ERROR: The S4 object %s was not found.' % s4_dn
		sys.exit(1)
	except GuidNotFound:
		print 'ERROR: The S4 search failed (objectGUID was not found.'
		sys.exit(1)
	
	print 'The resync of %s has been initialized.' % s4_dn

	sys.exit(0)

