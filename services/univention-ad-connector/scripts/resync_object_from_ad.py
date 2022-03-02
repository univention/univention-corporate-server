#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  Resync object from AD to OpenLDAP
#
# Copyright 2018-2022 Univention GmbH
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
import time
import sys
from argparse import ArgumentParser

import ldap
import sqlite3
from samba.dcerpc import misc
from samba.ndr import ndr_unpack

import univention.connector.ad
from univention.config_registry import ConfigRegistry


class GUIDNotFound(BaseException):
	pass


class DNNotFound(BaseException):
	pass


class ad(univention.connector.ad.ad):

	def _remove_cache_entries(self, guid):
		cache_filename = '/etc/univention/%s/adcache.sqlite' % CONFIGBASENAME
		if not os.path.exists(cache_filename):
			return
		cache_db = sqlite3.connect(cache_filename)
		c = cache_db.cursor()
		c.execute("SELECT id FROM GUIDS WHERE guid=?", (str(guid),))
		guid_ids = c.fetchone()
		if guid_ids:
			guid_id = guid_ids[0]
			c.execute("DELETE from DATA where guid_id = ?", (guid_id,))
			c.execute("DELETE from GUIDS where id = ?", (guid_id,))
			cache_db.commit()
		cache_db.close()

	def _add_object_to_rejected(self, ad_dn, usn):
		state_filename = '/etc/univention/%s/internal.sqlite' % CONFIGBASENAME
		db = sqlite3.connect(state_filename)
		c = db.cursor()
		c.execute("INSERT OR REPLACE INTO 'AD rejected' (key, value) VALUES (?, ?);", (usn, ad_dn))
		db.commit()
		db.close()

	def resync(self, ad_dns=None, ldapfilter=None, ldapbase=None):
		treated_dns = []
		for ad_dn, guid, usn in self.search_ad(ad_dns, ldapfilter, ldapbase):
			self._remove_cache_entries(guid)
			self._add_object_to_rejected(ad_dn, usn)
			treated_dns.append(ad_dn)

		return treated_dns

	def search_ad(self, ad_dns=None, ldapfilter=None, ldapbase=None):
		search_result = []
		if ad_dns:
			if not ldapfilter:
				ldapfilter = '(objectClass=*)'

			error_dns = []
			missing_dns = []
			for targetdn in ad_dns:
				guid = None
				try:
					res = self.__search_ad(base=targetdn, scope=ldap.SCOPE_BASE, filter=ldapfilter, attrlist=["objectGUID", "uSNChanged"])

					for msg in res:
						if not msg[0]:  # Referral
							continue
						guid_blob = msg[1]["objectGUID"][0]
						guid = ndr_unpack(misc.GUID, guid_blob)
						usn = msg[1]["uSNChanged"][0].decode('ASCII')
						search_result.append((str(msg[0]), guid, usn))
					if not guid:
						missing_dns.append(targetdn)
				except ldap.NO_SUCH_OBJECT as ex:
					error_dns.append((targetdn, str(ex)))
				except (ldap.REFERRAL, ldap.INVALID_DN_SYNTAX) as ex:
					error_dns.append((targetdn, str(ex)))
			if error_dns:
				raise DNNotFound(1, error_dns, [r[0] for r in search_result])
			if missing_dns:
				raise GUIDNotFound(1, missing_dns, [r[0] for r in search_result])
		else:
			if not ldapfilter:
				ldapfilter = '(objectClass=*)'

			if not ldapbase:
				ldapbase = self.configRegistry['%s/ad/ldap/base' % CONFIGBASENAME]

			guid = None
			try:
				res = self.__search_ad(base=ldapbase, scope=ldap.SCOPE_SUBTREE, filter=ldapfilter, attrlist=["objectGUID", "uSNChanged"])

				for msg in res:
					if not msg[0]:  # Referral
						continue
					guid_blob = msg[1]["objectGUID"][0]
					guid = ndr_unpack(misc.GUID, guid_blob)
					usn = msg[1]["uSNChanged"][0].decode('ASCII')
					search_result.append((str(msg[0]), guid, usn))
			except (ldap.REFERRAL, ldap.INVALID_DN_SYNTAX):
				raise DNNotFound(2, ldapbase)

			if not guid:
				raise GUIDNotFound(2, "No match")

		return search_result


if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument("-f", "--filter", dest="ldapfilter", help="LDAP search filter")
	parser.add_argument("-b", "--base", dest="ldapbase", help="LDAP search base")
	parser.add_argument("-c", "--configbasename", help="", metavar="CONFIGBASENAME", default="connector")
	parser.add_argument('dn')
	options = parser.parse_args()

	CONFIGBASENAME = options.configbasename
	state_directory = '/etc/univention/%s' % CONFIGBASENAME
	if not os.path.exists(state_directory):
		parser.error("Invalid configbasename, directory %s does not exist" % state_directory)

	if not options.dn and not options.ldapfilter:
		parser.print_help()
		sys.exit(2)

	configRegistry = ConfigRegistry()
	configRegistry.load()

	poll_sleep = int(configRegistry['%s/ad/poll/sleep' % CONFIGBASENAME])
	ad_init = None

	ad_dns = list(filter(None, [options.dn]))

	treated_dns = []

	try:
		resync = ad.main(configRegistry, CONFIGBASENAME)
		resync.init_ldap_connections()
		treated_dns = resync.resync(ad_dns, options.ldapfilter, options.ldapbase)
	except ldap.SERVER_DOWN:
		print("Warning: Can't initialize LDAP-Connections, wait...")
		sys.stdout.flush()
		time.sleep(poll_sleep)
	except DNNotFound as ex:
		print('ERROR: The AD object was not found: %s' % (ex.args[1],))
		if len(ex.args) == 3:
			treated_dns = ex.args[2]
		sys.exit(1)
	except GUIDNotFound as ex:
		print('ERROR: The AD search for objectGUID failed: %s' % (ex.args[1],))
		if len(ex.args) == 3:
			treated_dns = ex.args[2]
		sys.exit(1)
	finally:
		for dn in treated_dns:
			print('resync triggered for %s' % dn)

	if treated_dns:
		estimated_delay = 60
		try:
			estimated_delay = int(resync.configRegistry.get('%s/ad/retryrejected' % CONFIGBASENAME, 10)) * int(resync.configRegistry.get('%s/ad/poll/sleep' % CONFIGBASENAME, 5))
		except ValueError:
			pass

		print('Estimated sync in %s seconds.' % (estimated_delay,))
	else:
		print('No matching objects.')

	sys.exit(0)
