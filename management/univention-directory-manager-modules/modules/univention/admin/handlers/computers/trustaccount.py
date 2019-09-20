# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the trust accounts
#
# Copyright 2004-2019 Univention GmbH
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

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.config
import univention.admin.handlers
import univention.admin.password
import univention.admin.localization
import univention.admin.uldap
import univention.admin.handlers.dns.forward_zone
import univention.admin.handlers.dns.reverse_zone

import univention.debug as ud

translation = univention.admin.localization.translation('univention.admin.handlers.computers')
_ = translation.translate

module = 'computers/trustaccount'
operations = ['add', 'edit', 'remove', 'search', 'move']
docleanup = 1
childs = 0
short_description = _('Computer: Domain trust account')
object_name = _('Domain trust account')
object_name_plural = _('Domain trust accounts')
long_description = ''
options = {
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.dnsName_umlauts,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
	),
	'password': univention.admin.property(
		short_description=_('Machine Password'),
		long_description='',
		syntax=univention.admin.syntax.passwd,
		required=True,
		dontsearch=True,
	),
}

layout = [
	Tab(_('General'), _('Basic values'), layout=[
		Group(_('Trust account'), layout=[
			["name", "description"],
			"password"
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def open(self):
		super(object, self).open()

		self.options = ['samba']  # FIXME/TODO
		self.modifypassword = 1
		if self.exists():
			self['password'] = '********'
			self.modifypassword = 0

		self.save()

	def _ldap_addlist(self):

		self.uidNum = None
		self.machineSid = None
		while not self.uidNum or not self.machineSid:
			self.uidNum = univention.admin.allocators.request(self.lo, self.position, 'uidNumber')
			if self.uidNum:
				self.alloc.append(('uidNumber', self.uidNum))
				self.machineSid = univention.admin.allocators.requestUserSid(self.lo, self.position, self.uidNum)
				if not self.machineSid:
					univention.admin.allocators.release(self.lo, self.position, 'uidNumber', self.uidNum)
			else:
				self.machineSid = None

		self.alloc.append(('sid', self.machineSid))
		acctFlags = univention.admin.samba.acctFlags(flags={'I': 1})

		al = []
		ocs = ['top', 'person', 'sambaSamAccount']

		al.append(('sambaSID', [self.machineSid]))
		al.append(('sambaAcctFlags', [acctFlags.decode()]))
		al.append(('sn', self['name']))

		al.insert(0, ('objectClass', ocs))

		return al

	def _ldap_post_create(self):
		if hasattr(self, 'uidNum') and self.uidNum and hasattr(self, 'machineSid') and self.machineSid:
			univention.admin.allocators.confirm(self.lo, self.position, 'uidNumber', self.uidNum)
			univention.admin.allocators.confirm(self.lo, self.position, 'sid', self.machineSid)

		if hasattr(self, 'uid') and self.uid:
			univention.admin.allocators.confirm(self.lo, self.position, 'uid', self.uid)

	def _ldap_pre_modify(self):
		if self.hasChanged('password'):
			if not self['password']:
				self.modifypassword = 0
			elif not self.info['password']:
				self.modifypassword = 0
			else:
				self.modifypassword = 1

	def _ldap_modlist(self):
		ml = super(object, self)._ldap_modlist()

		if self.hasChanged('name') and self['name']:
			error = 0
			requested_uid = "%s$" % self['name']
			self.uid = None
			try:
				self.uid = univention.admin.allocators.request(self.lo, self.position, 'uid', value=requested_uid)
			except Exception:
				error = 1

			if not self.uid or error:
				del(self.info['name'])
				self.oldinfo = {}
				self.dn = None
				self._exists = 0
				raise univention.admin.uexceptions.uidAlreadyUsed(': %s' % requested_uid)
				return []

			self.alloc.append(('uid', self.uid))
			ml.append(('uid', self.oldattr.get('uid', [None])[0], self.uid))

		if self.modifypassword:
			password_nt, password_lm = univention.admin.password.ntlm(self['password'])
			ml.append(('sambaNTPassword', self.oldattr.get('sambaNTPassword', [''])[0], password_nt))
			ml.append(('sambaLMPassword', self.oldattr.get('sambaLMPassword', [''])[0], password_lm))

		return ml

	def cancel(self):
		for i, j in self.alloc:
			ud.debug(ud.ADMIN, ud.WARN, 'cancel: release (%s): %s' % (i, j))
			univention.admin.allocators.release(self.lo, self.position, i, j)


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):
	filter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'sambaSamAccount'),
		univention.admin.filter.expression('sambaAcctFlags', '[I          ]'),
	])

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res = []
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit, serverctrls, response):
		res.append(object(co, lo, None, dn, attributes=attrs))
	return res


def identify(dn, attr, canonical=0):
	return 'sambaSamAccount' in attr.get('objectClass', []) and '[I          ]' in attr.get('sambaAcctFlags', [])
