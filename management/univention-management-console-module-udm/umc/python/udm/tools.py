#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages UDM modules
#
# Copyright 2011-2015 Univention GmbH
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

import urllib2
import ldap
import ldap.modlist
import ldif
import binascii

import univention.admin.uldap
from univention.lib.i18n import Translation

from univention.management.console.config import ucr
from univention.management.console.log import MODULE

_ = Translation('univention-management-console-module-udm').translate


class LicenseError(Exception):
	pass


class LicenseImport(ldif.LDIFParser):
	dn = None
	mod_list = []
	dncount = 0
	base = None

	def check(self, base):
		# call parse from ldif.LDIFParser
		try:
			self.parse()
		except binascii.Error:
			raise LicenseError(_("No license has been found."))

		# there should be exactly one object in the the ldif file
		if self.dncount == 0:
			raise LicenseError(_("No license has been found."))
		elif self.dncount > 1:
			raise LicenseError(_("More than one object has been found."))

		# a free license does not have the ldap base in its dn
		if not self.dn.endswith(base) and self.base.lower() in ('free for personal use edition', 'ucs core edition'):
			self.dn = '%s,%s' % (self.dn, base)

		# check whether DN matches the LDAP base
		dnWithoutBase = self.dn[:-len(base)]
		if not self.dn.endswith(base) or not dnWithoutBase.endswith('cn=univention,'):
			raise LicenseError(_('The LDAP base of the license does not match the LDAP base of the UCS domain (%s).') % base)

		# check LDAP base
		if self.base.lower() not in [base.lower(), 'free for personal use edition', 'ucs core edition']:
			raise LicenseError(_("The license can not be applied. The LDAP base does not match (expected %s, found: %s).") % (base, self.base))

	def handle(self, dn, entry):
		"""This method is invoked bei LDIFParser.parse for each object
		in the ldif file"""

		if dn is None or dn == "":
			return

		self.dn = dn
		self.dncount += 1

		if 'univentionLicenseBaseDN' in entry:
			self.base = str(entry['univentionLicenseBaseDN'][0])
		else:
			return

		# create modification list
		self.addlist = ldap.modlist.addModlist(entry)
		# for atr in entry:
		# 	self.mod_list.insert( 0, ( ldap.MOD_REPLACE, atr, entry[ atr ] ) )

	def write(self, user_dn, passwd):
		ldap_con = ldap.open("localhost", port=int(ucr.get('ldap/server/port', 7389)))
		ldap_con.simple_bind_s(user_dn, passwd)
		try:
			ldap_con.add_s(self.dn, self.addlist)
		except ldap.ALREADY_EXISTS:
			ldap_con.delete_s(self.dn)
			ldap_con.add_s(self.dn, self.addlist)
		ldap_con.unbind_s()

# TODO: this should probably go into univention-lib
# and hide urllib/urllib2 completely
# i.e. it should be unnecessary to import them directly
# in a module


def install_opener(ucr):
	proxy_http = ucr.get('proxy/http')
	if proxy_http:
		proxy = urllib2.ProxyHandler({'http': proxy_http, 'https': proxy_http})
		opener = urllib2.build_opener(proxy)
		urllib2.install_opener(opener)


def urlopen(request):
	# use this in __init__
	# to have the proxy handler installed globally
	return urllib2.urlopen(request)


def dump_license():
	try:
		_lo, _pos = univention.admin.uldap.getMachineConnection(ldap_master=False)
		data = _lo.search('objectClass=univentionLicense')
		del _lo
		del _pos
		# just one license (should be always the case)
		# return the dictionary without the dn
		data = ldif.CreateLDIF(data[0][0], data[0][1])
		return data
	except Exception as e:
		# no udm, no ldap, malformed return value, whatever
		MODULE.error('getting License from LDAP failed: %s' % e)
		return None
