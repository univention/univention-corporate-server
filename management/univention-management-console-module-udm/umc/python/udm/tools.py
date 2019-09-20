#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages UDM modules
#
# Copyright 2011-2019 Univention GmbH
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

import urllib2
import ldap
import ldap.modlist
import ldif
import binascii

import univention.admin.uldap
import univention.admin.uexceptions as udm_errors
from univention.lib.i18n import Translation

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
			raise LicenseError(_("The license can not be applied. The LDAP base does not match (expected %(expected)s, found: %(found)s).") % {'expected': base, 'found': self.base})

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

	def write(self, ldap_connection):
		ldap_con = ldap_connection.lo.lo
		try:
			ldap_con.add_s(self.dn, self.addlist)
		except ldap.ALREADY_EXISTS:
			ldap_con.delete_s(self.dn)
			ldap_con.add_s(self.dn, self.addlist)


def check_license(ldap_connection, ignore_core_edition=False):
	try:
		try:
			_check_license(ldap_connection)
		except udm_errors.freeForPersonalUse:
			if ignore_core_edition:
				return
	except udm_errors.licenseNotFound:
		raise LicenseError(_('License not found. During this session add and modify are disabled.'))
	except udm_errors.licenseAccounts:  # UCS license v1
		raise LicenseError(_('You have too many user accounts for your license. Add and modify are disabled. Disable or delete <a href="javascript:void(0)" onclick="require(\'umc/app\').openModule(\'udm\', \'users/user\', {})"> user accounts</a> to re-enable editing.'))
	except udm_errors.licenseUsers:  # UCS license v2
		raise LicenseError(_('You have too many user accounts for your license. Add and modify are disabled. Disable or delete <a href="javascript:void(0)" onclick="require(\'umc/app\').openModule(\'udm\', \'users/user\', {})"> user accounts</a> to re-enable editing.'))
	except udm_errors.licenseClients:  # UCS license v1
		raise LicenseError(_('You have too many client accounts for your license. During this session add and modify are disabled.'))
	except udm_errors.licenseServers:  # UCS license v2
		raise LicenseError(_('You have too many server accounts for your license. During this session add and modify are disabled.'))
	except udm_errors.licenseManagedClients:  # UCS license v2
		raise LicenseError(_('You have too many managed client accounts for your license. During this session add and modify are disabled.'))
	except udm_errors.licenseCorporateClients:  # UCS license v2
		raise LicenseError(_('You have too many corporate client accounts for your license. During this session add and modify are disabled.'))
	except udm_errors.licenseDesktops:  # UCS license v1
		raise LicenseError(_('You have too many desktop accounts for your license. During this session add and modify are disabled.'))
	except udm_errors.licenseGroupware:  # UCS license v1
		raise LicenseError(_('You have too many groupware accounts for your license. During this session add and modify are disabled.'))
	except udm_errors.licenseDVSUsers:  # UCS license v2
		raise LicenseError(_('You have too many DVS user accounts for your license. During this session add and modify are disabled.'))
	except udm_errors.licenseDVSClients:  # UCS license v2
		raise LicenseError(_('You have too many DVS client accounts for your license. During this session add and modify are disabled.'))
	except udm_errors.licenseExpired:
		raise LicenseError(_('Your license is expired. During this session add and modify are disabled.'))
	except udm_errors.licenseWrongBaseDn:
		raise LicenseError(_('Your license is not valid for your LDAP-Base. During this session add and modify are disabled.'))
	except udm_errors.licenseInvalid:
		raise LicenseError(_('Your license is not valid. During this session add and modify are disabled.'))
	except udm_errors.licenseDisableModify:
		raise LicenseError(_('Your license does not allow modifications. During this session add and modify are disabled.'))
	except udm_errors.freeForPersonalUse:
		raise LicenseError(_('You are currently using the "Free for personal use" edition of Univention Corporate Server.'))


def _check_license(ldap_connection):
	mapping = {
		1: udm_errors.licenseClients,
		2: udm_errors.licenseAccounts,
		3: udm_errors.licenseDesktops,
		4: udm_errors.licenseGroupware,
		5: udm_errors.freeForPersonalUse,
		6: udm_errors.licenseUsers,
		7: udm_errors.licenseServers,
		8: udm_errors.licenseManagedClients,
		9: udm_errors.licenseCorporateClients,
		10: udm_errors.licenseDVSUsers,
		11: udm_errors.licenseDVSClients,
	}
	code = univention.admin.license.init_select(ldap_connection, 'admin')
	ldap_connection._validateLicense()  # throws more exceptions in case the license could not be found
	if code in mapping:
		raise mapping[code]


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
