# -*- coding: utf-8 -*-
#
# Copyright 2004-2022 Univention GmbH
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

"""
|UDM| module for the trust accounts
"""

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.localization
import univention.admin.syntax
import univention.admin.mapping
import univention.admin.uexceptions
import univention.admin.handlers.dns.forward_zone
import univention.admin.handlers.dns.reverse_zone

translation = univention.admin.localization.translation('univention.admin.handlers.computers')
_ = translation.translate

module = 'computers/trustaccount'
operations = ['add', 'edit', 'remove', 'search', 'move']
docleanup = True
childs = False
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

	def getMachineSid(self, lo, position, uidNum, rid=None):
		# if rid is given, use it regardless of s4 connector
		if rid:
			searchResult = self.lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
			domainsid = searchResult[0][1]['sambaSID'][0]
			sid = domainsid + '-' + rid
			return self.request_lock('sid', sid)
		else:
			# if no rid is given, create a domain sid or local sid if connector is present
			if self.s4connector_present:
				return 'S-1-4-%s' % uidNum
			else:
				num = uidNum
				while True:
					try:
						return self.request_lock('sid+user', num)
					except univention.admin.uexceptions.noLock:
						num = str(int(num) + 1)

	def _ldap_addlist(self):
		acctFlags = univention.admin.samba.acctFlags(flags={'I': 1})

		al = super(object, self)._ldap_addlist()
		ocs = [b'top', b'person', b'sambaSamAccount']

		al.append(('sambaSID', [self.getMachineSid(self.lo, self.position, self.request_lock('uidNumber')).encode('ASCII')]))
		al.append(('sambaAcctFlags', [acctFlags.decode().encode('ASCII')]))
		al.append(('sn', self['name'].encode('UTF-8')))

		al.insert(0, ('objectClass', ocs))

		return al

	def _ldap_pre_modify(self):
		super(object, self)._ldap_pre_modify()
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
			requested_uid = "%s$" % self['name']
			try:
				ml.append(('uid', self.oldattr.get('uid', []), [self.request_lock('uid', requested_uid).encode('UTF-8')]))
			except univention.admin.uexceptions.noLock:
				raise univention.admin.uexceptions.uidAlreadyUsed(requested_uid)

		if self.modifypassword:
			password_nt, password_lm = univention.admin.password.ntlm(self['password'])
			ml.append(('sambaNTPassword', self.oldattr.get('sambaNTPassword', [b''])[0], password_nt.encode('ASCII')))
			ml.append(('sambaLMPassword', self.oldattr.get('sambaLMPassword', [b''])[0], password_lm.encode('ASCII')))

		return ml

	def _ldap_pre_remove(self):
		super(object, self)._ldap_pre_remove()
		if self.oldattr.get('uid'):
			self.alloc.append(('uid', self.oldattr['uid'][0].decode('UTF-8')))
		if self.oldattr.get('sambaSID'):
			self.alloc.append(('sid', self.oldattr['sambaSID'][0].decode('ASCII')))


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
	for dn, attrs in lo.search(str(filter), base, scope, [], unique, required, timeout, sizelimit, serverctrls, response):
		res.append(object(co, lo, None, dn, attributes=attrs))
	return res


def identify(dn, attr, canonical=False):
	return b'sambaSamAccount' in attr.get('objectClass', []) and b'[I          ]' in attr.get('sambaAcctFlags', [])
