#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  Resync object from AD to OpenLDAP
#
# Copyright 2018-2019 Univention GmbH
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

from optparse import OptionParser
import os
import ldap
import time
import sqlite3
import sys

from samba.dcerpc import misc
from samba.ndr import ndr_unpack

import univention.connector.ad
from univention.config_registry import ConfigRegistry


class GUIDNotFound(BaseException):
	pass


class DNNotFound(BaseException):
	pass


class ad(univention.connector.ad.ad):

	def __init__(self, CONFIGBASENAME, baseConfig, ad_ldap_host, ad_ldap_port, ad_ldap_base, ad_ldap_binddn, ad_ldap_bindpw, ad_ldap_certificate, listener_dir):

		self.CONFIGBASENAME = CONFIGBASENAME

		self.ad_ldap_host = ad_ldap_host
		self.ad_ldap_port = ad_ldap_port
		self.ad_ldap_base = ad_ldap_base
		self.ad_ldap_binddn = ad_ldap_binddn
		self.ad_ldap_bindpw = ad_ldap_bindpw
		self.ad_ldap_certificate = ad_ldap_certificate
		if baseConfig:
			self.baseConfig = baseConfig
		else:
			self.baseConfig = ConfigRegistry()
			self.baseConfig.load()

		self.open_ad()

	def _remove_cache_entries(self, guid):
		cache_filename = '/etc/univention/%s/cache.sqlite' % CONFIGBASENAME
		if os.path.exists(cache_filename):
			cache_db = sqlite3.connect(cache_filename)
			c = cache_db.cursor()
			c.execute("SELECT id FROM GUIDS WHERE guid='%s'" % guid)
			guid_ids = c.fetchone()
			if guid_ids:
				guid_id = guid_ids[0]
				c.execute("DELETE from DATA where guid_id = '%s'" % guid_id)
				c.execute("DELETE from GUIDS where id = '%s'" % guid_id)
				cache_db.commit()
			cache_db.close()

	def _add_object_to_rejected(self, ad_dn, usn):
		state_filename = '/etc/univention/%s/internal.sqlite' % CONFIGBASENAME
		db = sqlite3.connect(state_filename)
		c = db.cursor()
		c.execute("INSERT OR REPLACE INTO 'AD rejected' (key,value) VALUES ('%(key)s', '%(value)s');" % {'key': usn, 'value': ad_dn})
		db.commit()
		db.close()

	def resync(self, ad_dns=None, ldapfilter=None, ldapbase=None):
		if ad_dns and not type(ad_dns) in (type(()), type([])):
			raise ValueError("'ad_dns' is of type %s, must be list or tuple" % type(ad_dns))

		treated_dns = []
		for ad_dn, guid, usn in self.search_ad(ad_dns, ldapfilter, ldapbase):
			self._remove_cache_entries(guid)
			self._add_object_to_rejected(ad_dn, usn)
			treated_dns.append(ad_dn)

		return treated_dns

	def search_ad(self, ad_dns=None, ldapfilter=None, ldapbase=None):

		search_result = []
		if ad_dns:
			if not type(ad_dns) in (type(()), type([])):
				raise ValueError("'ad_dns' is of type %s, must be list or tuple" % type(ad_dns))

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
						usn = msg[1]["uSNChanged"][0]
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
				ldapbase = self.baseConfig['%s/ad/ldap/base' % CONFIGBASENAME]

			guid = None
			try:
				res = self.__search_ad(base=ldapbase, scope=ldap.SCOPE_SUBTREE, filter=ldapfilter, attrlist=["objectGUID", "uSNChanged"])

				for msg in res:
					if not msg[0]:  # Referral
						continue
					guid_blob = msg[1]["objectGUID"][0]
					guid = ndr_unpack(misc.GUID, guid_blob)
					usn = msg[1]["uSNChanged"][0]
					search_result.append((str(msg[0]), guid, usn))
			except (ldap.REFERRAL, ldap.INVALID_DN_SYNTAX) as ex:
				raise DNNotFound(2, ldapbase)

			if not guid:
				raise GUIDNotFound(2, "No match")

		return search_result


if __name__ == '__main__':

	parser = OptionParser(usage='resync_object_from_ad.py [--filter <LDAP search filter>] [--base  <LDAP search base>] [dn]')
	parser.add_option("-f", "--filter", dest="ldapfilter", help="LDAP search filter")
	parser.add_option("-b", "--base", dest="ldapbase", help="LDAP search base")
	parser.add_option("-c", "--configbasename", dest="configbasename", help="", metavar="CONFIGBASENAME", default="connector")
	(options, args) = parser.parse_args()

	CONFIGBASENAME = options.configbasename
	state_directory = '/etc/univention/%s' % CONFIGBASENAME
	if not os.path.exists(state_directory):
		print("Invalid configbasename, directory %s does not exist" % state_directory)
		sys.exit(1)

	if len(args) != 1 and not (options.ldapfilter or options.ldapbase):
		parser.print_help()
		sys.exit(2)

	baseConfig = ConfigRegistry()
	baseConfig.load()

	if '%s/ad/ldap/host' % CONFIGBASENAME not in baseConfig:
		print '%s/ad/ldap/host not set' % CONFIGBASENAME
		sys.exit(1)
	if '%s/ad/ldap/port' % CONFIGBASENAME not in baseConfig:
		print '%s/ad/ldap/port not set' % CONFIGBASENAME
		sys.exit(1)
	if '%s/ad/ldap/base' % CONFIGBASENAME not in baseConfig:
		print '%s/ad/ldap/base not set' % CONFIGBASENAME
		sys.exit(1)
	if '%s/ad/ldap/binddn' % CONFIGBASENAME not in baseConfig:
		print '%s/ad/ldap/binddn not set' % CONFIGBASENAME
		sys.exit(1)
	if '%s/ad/ldap/bindpw' % CONFIGBASENAME not in baseConfig:
		print '%s/ad/ldap/bindpw not set' % CONFIGBASENAME
		sys.exit(1)

	ca_file = baseConfig.get('%s/ad/ldap/certificate' % CONFIGBASENAME)
	if baseConfig.is_true('%s/ad/ldap/ssl' % CONFIGBASENAME, True) or baseConfig.is_true('%s/ad/ldap/ldaps' % CONFIGBASENAME, False):
		if ca_file:
			# create a new CAcert file, which contains the UCS CA and the AD CA,
			# see Bug #17768 for details
			#  https://forge.univention.org/bugzilla/show_bug.cgi?id=17768
			new_ca_filename = '/var/cache/univention-ad-connector/CAcert-%s.pem' % CONFIGBASENAME
			with open(new_ca_filename, 'w') as new_ca:
				with open('/etc/univention/ssl/ucsCA/CAcert.pem', 'r') as ca:
					new_ca.write(ca.read())

				with open(baseConfig['%s/ad/ldap/certificate' % CONFIGBASENAME]) as ca:
					new_ca.write(ca.read())

			ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, new_ca_filename)
		else:
			ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

	if '%s/ad/listener/dir' % CONFIGBASENAME not in baseConfig:
		print '%s/ad/listener/dir not set' % CONFIGBASENAME
		sys.exit(1)
	ad_ldap_bindpw = open(baseConfig['%s/ad/ldap/bindpw' % CONFIGBASENAME]).read()
	if ad_ldap_bindpw[-1] == '\n':
		ad_ldap_bindpw = ad_ldap_bindpw[0:-1]

	poll_sleep = int(baseConfig['%s/ad/poll/sleep' % CONFIGBASENAME])
	ad_init = None

	ad_dns = []
	if len(args) == 1:
		ad_dns.append(args[0])

	treated_dns = []

	try:
		resync = ad(
			CONFIGBASENAME,
			baseConfig,
			baseConfig['%s/ad/ldap/host' % CONFIGBASENAME],
			baseConfig['%s/ad/ldap/port' % CONFIGBASENAME],
			baseConfig['%s/ad/ldap/base' % CONFIGBASENAME],
			baseConfig['%s/ad/ldap/binddn' % CONFIGBASENAME],
			ad_ldap_bindpw,
			baseConfig['%s/ad/ldap/certificate' % CONFIGBASENAME],
			baseConfig['%s/ad/listener/dir' % CONFIGBASENAME]
		)
		treated_dns = resync.resync(ad_dns, options.ldapfilter, options.ldapbase)
	except ldap.SERVER_DOWN:
		print "Warning: Can't initialize LDAP-Connections, wait..."
		sys.stdout.flush()
		time.sleep(poll_sleep)
	except DNNotFound as ex:
		print 'ERROR: The AD object was not found: %s' % (ex.args[1],)
		if len(ex.args) == 3:
			treated_dns = ex.args[2]
		sys.exit(1)
	except GUIDNotFound as ex:
		print 'ERROR: The AD search for objectGUID failed: %s' % (ex.args[1],)
		if len(ex.args) == 3:
			treated_dns = ex.args[2]
		sys.exit(1)
	finally:
		for dn in treated_dns:
			print 'resync triggered for %s' % dn

	if treated_dns:
		estimated_delay = 60
		try:
			estimated_delay = int(resync.baseConfig.get('%s/ad/retryrejected' % CONFIGBASENAME, 10)) * int(resync.baseConfig.get('%s/ad/poll/sleep' % CONFIGBASENAME, 5))
		except ValueError:
			pass

		print 'Estimated sync in %s seconds.' % (estimated_delay,)
	else:
		print 'No matching objects.'

	sys.exit(0)
