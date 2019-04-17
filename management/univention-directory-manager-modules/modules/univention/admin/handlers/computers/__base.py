# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for generic computer objects
#
# Copyright 2019 Univention GmbH
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

import time
import functools
from ldap.filter import filter_format

import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.allocators
import univention.admin.localization
import univention.admin.uldap
import univention.admin.nagios as nagios
import univention.admin.handlers.groups.group
import univention.admin.handlers.dns.forward_zone
import univention.admin.handlers.dns.reverse_zone
import univention.admin.handlers.networks.network

import univention.debug as ud

translation = univention.admin.localization.translation('univention.admin.handlers.computers')
_ = translation.translate


class ComputerObject(univention.admin.handlers.simpleComputer, nagios.Support):
	"""
	|UDM| module for generic computer objects.
	"""
	CONFIG_NAME = None  # type: str
	SERVER_ROLE = None  # type: str
	SAMBA_ACCOUNT_FLAG = None  # type: str

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=None):
		univention.admin.handlers.simpleComputer.__init__(self, co, lo, position, dn, superordinate, attributes)
		nagios.Support.__init__(self)

	def open(self):
		univention.admin.handlers.simpleComputer.open(self)
		self.nagios_open()

		if self.exists():
			if 'posix' in self.options and not self.info.get('primaryGroup'):
				primaryGroupNumber = self.oldattr.get('gidNumber', [''])[0]
				ud.debug(ud.ADMIN, ud.INFO, 'primary group number = %s' % (primaryGroupNumber))
				if primaryGroupNumber:
					primaryGroupResult = self.lo.searchDn(filter_format('(&(objectClass=posixGroup)(gidNumber=%s))', [primaryGroupNumber]))
					if primaryGroupResult:
						self['primaryGroup'] = primaryGroupResult[0]
						ud.debug(ud.ADMIN, ud.INFO, 'Set primary group = %s' % (self['primaryGroup']))
					else:
						self['primaryGroup'] = None
						self.save()
						raise univention.admin.uexceptions.primaryGroup
				else:
					self['primaryGroup'] = None
					self.save()
					raise univention.admin.uexceptions.primaryGroup
			if 'samba' in self.options:
				sid = self.oldattr.get('sambaSID', [''])[0]
				pos = sid.rfind('-')
				self.info['sambaRID'] = sid[pos + 1:]

		self.modifypassword = 0
		if self.exists():
			userPassword = self.oldattr.get('userPassword', [''])[0]
			if userPassword:
				self.info['password'] = userPassword
				self.modifypassword = 0
			self.save()
		else:
			self.modifypassword = 0
			if 'posix' in self.options:
				res = univention.admin.config.getDefaultValue(self.lo, self.CONFIG_NAME, position=self.position)
				if res:
					self['primaryGroup'] = res

	def _ldap_pre_create(self):
		super(ComputerObject, self)._ldap_pre_create()
		if not self['password']:
			self['password'] = self.oldattr.get('password', [''])[0]
			self.modifypassword = 0

	def _ldap_addlist(self):
		al = super(ComputerObject, self)._ldap_addlist()
		self.check_required_options()
		if 'kerberos' in self.options:
			domain = univention.admin.uldap.domain(self.lo, self.position)
			realm = domain.getKerberosRealm()

			if realm:
				al.append(('krb5MaxLife', '86400'))
				al.append(('krb5MaxRenew', '604800'))
				al.append(('krb5KDCFlags', '126'))
				krb_key_version = str(int(self.oldattr.get('krb5KeyVersionNumber', ['0'])[0]) + 1)
				al.append(('krb5KeyVersionNumber', self.oldattr.get('krb5KeyVersionNumber', []), krb_key_version))
			elif self.SERVER_ROLE not in ('master', 'windows_domaincontroller'):
				# can't do kerberos
				self._remove_option('kerberos')
		if 'posix' in self.options:
			self.uidNum = univention.admin.allocators.request(self.lo, self.position, 'uidNumber')
			self.alloc.append(('uidNumber', self.uidNum))
			gidNum = self.get_gid_for_primary_group()
			al.append(('uidNumber', [self.uidNum]))
			al.append(('gidNumber', [gidNum]))

		if self.modifypassword or self['password']:
			if 'kerberos' in self.options:
				krb_keys = univention.admin.password.krb5_asn1(self.krb5_principal(), self['password'])
				al.append(('krb5Key', self.oldattr.get('password', ['1']), krb_keys))
			if 'posix' in self.options:
				password_crypt = "{crypt}%s" % (univention.admin.password.crypt(self['password']))
				al.append(('userPassword', self.oldattr.get('userPassword', [''])[0], password_crypt))
			if 'samba' in self.options:
				password_nt, password_lm = univention.admin.password.ntlm(self['password'])
				al.append(('sambaNTPassword', self.oldattr.get('sambaNTPassword', [''])[0], password_nt))
				al.append(('sambaLMPassword', self.oldattr.get('sambaLMPassword', [''])[0], password_lm))
				sambaPwdLastSetValue = str(long(time.time()))
				al.append(('sambaPwdLastSet', self.oldattr.get('sambaPwdLastSet', [''])[0], sambaPwdLastSetValue))
			self.modifypassword = 0
		if 'samba' in self.options:
			acctFlags = univention.admin.samba.acctFlags(flags={self.SAMBA_ACCOUNT_FLAG: 1})
			self.machineSid = self.getMachineSid(self.lo, self.position, self.uidNum, self.get('sambaRID'))
			self.alloc.append(('sid', self.machineSid))
			al.append(('sambaSID', [self.machineSid]))
			al.append(('sambaAcctFlags', [acctFlags.decode()]))
			al.append(('displayName', self.info['name']))

		if self.SERVER_ROLE:
			al.append(('univentionServerRole', '', self.SERVER_ROLE))
		return al

	def check_required_options(self):
		pass

	def _ldap_post_create(self):
		if 'posix' in self.options:
			if hasattr(self, 'uid') and self.uid:
				univention.admin.allocators.confirm(self.lo, self.position, 'uid', self.uid)
			univention.admin.handlers.simpleComputer.primary_group(self)
		univention.admin.handlers.simpleComputer._ldap_post_create(self)
		self.nagios_ldap_post_create()

	def _ldap_pre_remove(self):
		self.open()
		if 'posix' in self.options and self.oldattr.get('uidNumber'):
			self.uidNum = self.oldattr['uidNumber'][0]

	def _ldap_post_remove(self):
		if 'posix' in self.options:
			univention.admin.allocators.release(self.lo, self.position, 'uidNumber', self.uidNum)
		groupObjects = univention.admin.handlers.groups.group.lookup(self.co, self.lo, filter_s=filter_format('uniqueMember=%s', [self.dn]))
		if groupObjects:
			for i in range(0, len(groupObjects)):
				groupObjects[i].open()
				if self.dn in groupObjects[i]['users']:
					groupObjects[i]['users'].remove(self.dn)
					groupObjects[i].modify(ignore_license=1)

		self.nagios_ldap_post_remove()
		univention.admin.handlers.simpleComputer._ldap_post_remove(self)
		# Need to clean up oldinfo. If remove was invoked, because the
		# creation of the object has failed, the next try will result in
		# a 'object class violation' (Bug #19343)
		self.oldinfo = {}

	def krb5_principal(self):
		domain = univention.admin.uldap.domain(self.lo, self.position)
		realm = domain.getKerberosRealm()
		if 'domain' in self.info and self.info['domain']:
			kerberos_domain = self.info['domain']
		else:
			kerberos_domain = domain.getKerberosRealm()
		return 'host/' + self['name'] + '.' + kerberos_domain.lower() + '@' + realm

	def _ldap_post_modify(self):
		univention.admin.handlers.simpleComputer.primary_group(self)
		univention.admin.handlers.simpleComputer._ldap_post_modify(self)
		self.nagios_ldap_post_modify()

	def _ldap_pre_modify(self):
		if self.hasChanged('password'):
			if not self['password']:
				self['password'] = self.oldattr.get('password', [''])[0]
				self.modifypassword = 0
			elif not self.info['password']:
				self['password'] = self.oldattr.get('password', [''])[0]
				self.modifypassword = 0
			else:
				self.modifypassword = 1
		self.nagios_ldap_pre_modify()
		univention.admin.handlers.simpleComputer._ldap_pre_modify(self)

	def _ldap_modlist(self):
		ml = univention.admin.handlers.simpleComputer._ldap_modlist(self)

		self.nagios_ldap_modlist(ml)

		if self.hasChanged('name'):
			if 'posix' in self.options:
				if hasattr(self, 'uidNum'):
					univention.admin.allocators.confirm(self.lo, self.position, 'uidNumber', self.uidNum)
				requested_uid = "%s$" % self['name']
				try:
					self.uid = univention.admin.allocators.request(self.lo, self.position, 'uid', value=requested_uid)
				except Exception:
					self.cancel()
					raise univention.admin.uexceptions.uidAlreadyUsed(': %s' % requested_uid)

				self.alloc.append(('uid', self.uid))

				ml.append(('uid', self.oldattr.get('uid', [None])[0], self.uid))

			if 'samba' in self.options:
				ml.append(('displayName', self.oldattr.get('displayName', [None])[0], self['name']))

			if 'kerberos' in self.options:
				ml.append(('krb5PrincipalName', self.oldattr.get('krb5PrincipalName', []), [self.krb5_principal()]))

		if self.modifypassword and self['password']:
			if 'kerberos' in self.options:
				krb_keys = univention.admin.password.krb5_asn1(self.krb5_principal(), self['password'])
				krb_key_version = str(int(self.oldattr.get('krb5KeyVersionNumber', ['0'])[0]) + 1)
				ml.append(('krb5Key', self.oldattr.get('password', ['1']), krb_keys))
				ml.append(('krb5KeyVersionNumber', self.oldattr.get('krb5KeyVersionNumber', []), krb_key_version))
			if 'posix' in self.options:
				password_crypt = "{crypt}%s" % (univention.admin.password.crypt(self['password']))
				ml.append(('userPassword', self.oldattr.get('userPassword', [''])[0], password_crypt))
			if 'samba' in self.options:
				password_nt, password_lm = univention.admin.password.ntlm(self['password'])
				ml.append(('sambaNTPassword', self.oldattr.get('sambaNTPassword', [''])[0], password_nt))
				ml.append(('sambaLMPassword', self.oldattr.get('sambaLMPassword', [''])[0], password_lm))
				sambaPwdLastSetValue = str(long(time.time()))
				ml.append(('sambaPwdLastSet', self.oldattr.get('sambaPwdLastSet', [''])[0], sambaPwdLastSetValue))

		# add samba option
		if self.exists() and self.option_toggled('samba') and 'samba' in self.options:
			acctFlags = univention.admin.samba.acctFlags(flags={self.SAMBA_ACCOUNT_FLAG: 1})
			self.machineSid = self.getMachineSid(self.lo, self.position, self.oldattr['uidNumber'][0], self.get('sambaRID'))
			self.alloc.append(('sid', self.machineSid))
			ml.append(('sambaSID', '', [self.machineSid]))
			ml.append(('sambaAcctFlags', '', [acctFlags.decode()]))
			ml.append(('displayName', '', self.info['name']))
			sambaPwdLastSetValue = str(long(time.time()))
			ml.append(('sambaPwdLastSet', self.oldattr.get('sambaPwdLastSet', [''])[0], sambaPwdLastSetValue))
		if self.exists() and self.option_toggled('samba') and 'samba' not in self.options:
			for key in ['sambaSID', 'sambaAcctFlags', 'sambaNTPassword', 'sambaLMPassword', 'sambaPwdLastSet', 'displayName']:
				if self.oldattr.get(key, []):
					ml.insert(0, (key, self.oldattr.get(key, []), ''))

		if self.hasChanged('sambaRID') and not hasattr(self, 'machineSid'):
			self.machineSid = self.getMachineSid(self.lo, self.position, self.oldattr['uidNumber'][0], self.get('sambaRID'))
			ml.append(('sambaSID', self.oldattr.get('sambaSID', ['']), [self.machineSid]))

		return ml

	def cleanup(self):
		self.open()
		self.nagios_cleanup()
		univention.admin.handlers.simpleComputer.cleanup(self)

	def cancel(self):
		for i, j in self.alloc:
			ud.debug(ud.ADMIN, ud.WARN, 'cancel: release (%s): %s' % (i, j))
			univention.admin.allocators.release(self.lo, self.position, i, j)

	def link(self):
		result = []
		if self['ip'] and len(self['ip']) > 0 and self['ip'][0]:
			result = [{
				'url': 'https://%s/univention-management-console/' % self['ip'][0],
				'ipaddr': self['ip'][0],
			}]
		if 'dnsEntryZoneForward' in self and self['dnsEntryZoneForward'] and len(self['dnsEntryZoneForward']) > 0:
			zone = univention.admin.uldap.explodeDn(self['dnsEntryZoneForward'][0], 1)[0]
			if not result:
				result = [{'url': 'https://%s.%s/univention-management-console/' % (self['name'], zone)}]
			result[0]['fqdn'] = '%s.%s' % (self['name'], zone)
		if result:
			result[0]['name'] = _('Open Univention Management Console on this computer')
			return result
		return None

	@classmethod
	def unmapped_lookup_filter(cls):  # type: () -> univention.admin.filter.conjunction
		filter_p = super(ComputerObject, cls).unmapped_lookup_filter()
		if cls.SERVER_ROLE and cls.SERVER_ROLE != 'member':
			filter_p.expressions.append(univention.admin.filter.expression('univentionServerRole', cls.SERVER_ROLE, escape=True))
		return filter_p

	@classmethod
	def rewrite_filter(cls, filter, mapping, lo=None):
		if filter.variable == 'ip':
			filter.transform_to_conjunction(univention.admin.filter.conjunction('|', [
				univention.admin.filter.expression('aRecord', filter.value, escape=False),
				univention.admin.filter.expression('aAAARecord', filter.value, escape=False),
			]))
		elif filter.variable == 'dnsAlias':
			found = univention.admin.filter.parse(univention.admin.handlers.dns.alias.lookup_alias_filter(lo, unicode(filter)))
			if isinstance(found, univention.admin.filter.conjunction):
				filter.transform_to_conjunction(found)
			else:
				filter.variable = found.variable
				filter.value = found.value
		elif filter.variable == 'fqdn':
			filter.transform_to_conjunction(univention.admin.filter.parse(univention.admin.filter.replace_fqdn_filter(str(filter))))
		else:
			super(ComputerObject, cls).rewrite_filter(filter, mapping)

	@classmethod
	def lookup_filter(cls, filter_s=None, lo=None):
		lookup_filter_obj = cls.unmapped_lookup_filter()
		module = univention.admin.modules.get_module(cls.module)
		# ATTENTION: has its own rewrite function.
		lookup_filter_obj.append_unmapped_filter_string(filter_s, functools.partial(cls.rewrite_filter, lo=lo), module.mapping)
		return lookup_filter_obj

	@classmethod
	def identify(cls, dn, attr, canonical=False):
		if cls.SERVER_ROLE and cls.SERVER_ROLE != 'member' and cls.SERVER_ROLE not in attr.get('univentionServerRole', []):
			return False
		return super(ComputerObject, cls).identify(dn, attr, canonical)
