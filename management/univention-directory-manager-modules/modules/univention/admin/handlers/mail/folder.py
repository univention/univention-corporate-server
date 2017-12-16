# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for mail imap folders
#
# Copyright 2004-2017 Univention GmbH
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

import ldap

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.allocators
import univention.admin.localization

import univention.debug as ud

translation = univention.admin.localization.translation('univention.admin.handlers.mail')
_ = translation.translate

module = 'mail/folder'
operations = ['add', 'edit', 'remove', 'search']  # removed 'move' as a workaround for bug #11664
childs = 0
short_description = _('Mail folder (IMAP)')
long_description = ''

module_search_filter = univention.admin.filter.conjunction('&', [
	univention.admin.filter.expression('objectClass', 'univentionMailSharedFolder'),
])


ldap_search_maildomain = univention.admin.syntax.LDAP_Search(
	filter='(objectClass=univentionMailDomainname)',
	attribute=['mail/domain: name'],
	value='mail/domain: name')

options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['univentionMailSharedFolder'],
	),
}

property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.mail_folder_name,
		multivalue=False,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True
	),
	'mailDomain': univention.admin.property(
		short_description=_('Mail domain'),
		long_description='',
		syntax=ldap_search_maildomain,
		multivalue=False,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True
	),
	'sharedFolderUserACL': univention.admin.property(
		short_description=_('User ACL'),
		long_description='',
		syntax=univention.admin.syntax.SharedFolderUserACL,
		multivalue=True,
		required=False,
		may_change=True,
		identifies=False,
	),
	'sharedFolderGroupACL': univention.admin.property(
		short_description=_('Group ACL'),
		long_description='',
		syntax=univention.admin.syntax.SharedFolderGroupACL,
		multivalue=True,
		required=False,
		may_change=True,
		identifies=False,
	),
	'cyrus-userquota': univention.admin.property(
		short_description=_('Quota in MB'),
		long_description='',
		syntax=univention.admin.syntax.integer,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False,
	),
	'mailHomeServer': univention.admin.property(
		short_description=_('Mail home server'),
		long_description='',
		syntax=univention.admin.syntax.MailHomeServer,
		nonempty_is_default=True,
		multivalue=False,
		required=True,
		may_change=True,
		identifies=False,
	),
	'mailPrimaryAddress': univention.admin.property(
		short_description=_('E-Mail address'),
		long_description='',
		syntax=univention.admin.syntax.emailAddressValidDomain,
		multivalue=False,
		include_in_default_search=True,
		required=False,
		dontsearch=False,
		may_change=True,
		identifies=False,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General IMAP mail folder settings'), layout=[
			["name", "mailDomain"],
			["mailHomeServer"],
			["cyrus-userquota"],
			["mailPrimaryAddress"],
		]),
	]),
	Tab(_('Access Rights'), _('Access rights for shared folder'), layout=[
		Group(_('Access Rights'), layout=[
			"sharedFolderUserACL",
			"sharedFolderGroupACL",
		]),
	])
]

mapping = univention.admin.mapping.mapping()
mapping.register('cyrus-userquota', 'univentionMailUserQuota', None, univention.admin.mapping.ListToString)
mapping.register('mailHomeServer', 'univentionMailHomeServer', None, univention.admin.mapping.ListToString)
mapping.register('mailPrimaryAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[]):
		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes=attributes)
		self.open()

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)
		if self.exists():
			cn = self.oldattr.get('cn', [])
			if cn:
				# 'name' is not a ldap attribute and oldinfo['name'] is
				# always empty, that is way searching for 'name' causes trouble
				# we delete the 'name' key in oldinfo so that the "change test"
				# succeeds
				if self.oldinfo.has_key('name') and not self.oldinfo['name']:
					del self.oldinfo['name']
				self['name'] = cn[0].split('@')[0]
				self['mailDomain'] = cn[0].split('@')[1]

			# fetch values for ACLs
			acls = self.oldattr.get('univentionMailACL', [])
			self['sharedFolderUserACL'] = []
			self['sharedFolderGroupACL'] = []
			if acls:
				for acl in acls:
					if acl.find('@') > 0 or acl.startswith('anyone'):
						self['sharedFolderUserACL'].append(acl.rsplit(' ', 1))
					else:
						self['sharedFolderGroupACL'].append(acl.rsplit(' ', 1))
		self.save()

	def description(self):
		"""Returns a name that identifies the object. This may be used
		to override the default value that is the property marked with identifies = True"""
		return '%s@%s' % (self['name'], self['mailDomain'])

	def _ldap_dn(self):
		name = '%s@%s' % (self.info['name'], self.info['mailDomain'])
		return 'cn=%s,%s' % (ldap.dn.escape_dn_chars(name), self.position.getDn())

	def _ldap_post_create(self):
		if self['mailPrimaryAddress']:
			univention.admin.allocators.release(self.lo, self.position, 'mailPrimaryAddress', value=self['mailPrimaryAddress'])

	def _ldap_addlist(self):
		al = []

		if self['mailPrimaryAddress']:
			al.append(('univentionMailSharedFolderDeliveryAddress', 'univentioninternalpostuser+shared/%s@%s' % (self['name'].lower(), self['mailDomain'].lower())))

			address = '%s@%s' % (self['name'], self['mailDomain'])
			if self['mailPrimaryAddress'] != address:
				try:
					self.alloc.append(('mailPrimaryAddress', self['mailPrimaryAddress']))
					univention.admin.allocators.request(self.lo, self.position, 'mailPrimaryAddress', value=self['mailPrimaryAddress'])
				except:
					univention.admin.allocators.release(self.lo, self.position, 'mailPrimaryAddress', value=self['mailPrimaryAddress'])
					raise univention.admin.uexceptions.mailAddressUsed

		al.append(('cn', "%s@%s" % (self.info['name'], self.info['mailDomain'])))

		return al

	def _ldap_post_modify(self):
		if self['mailPrimaryAddress']:
			univention.admin.allocators.release(self.lo, self.position, 'mailPrimaryAddress', value=self['mailPrimaryAddress'])

	def _ldap_modlist(self):
		# we get a list of modifications to be done (called 'ml' down below)
		# this lists looks like this:
		# [('univentionMailHomeServer', [u'ugs-master.hosts.invalid'], u'ugs-master.hosts.invalid'), ('univentionMailUserQuota', u'100', u'101')]
		# we can modify those entries to conform to the LDAP schema

		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)

		if self.hasChanged('mailPrimaryAddress') and self['mailPrimaryAddress']:
			for i, j in self.alloc:
				if i == 'mailPrimaryAddress':
					break
			else:
				ml.append((
					'univentionMailSharedFolderDeliveryAddress',
					self.oldattr.get('univentionMailSharedFolderDeliveryAddress', []),
					['univentioninternalpostuser+shared/%s@%s' % (self['name'].lower(), self['mailDomain'].lower())]
				))

				address = '%s@%s' % (self['name'], self['mailDomain'])
				if self['mailPrimaryAddress'] != address:
					try:
						self.alloc.append(('mailPrimaryAddress', self['mailPrimaryAddress']))
						univention.admin.allocators.request(self.lo, self.position, 'mailPrimaryAddress', value=self['mailPrimaryAddress'])
					except:
						univention.admin.allocators.release(self.lo, self.position, 'mailPrimaryAddress', value=self['mailPrimaryAddress'])
						raise univention.admin.uexceptions.mailAddressUsed

		if not self['mailPrimaryAddress']:
			ml.append(('univentionMailSharedFolderDeliveryAddress', self.oldattr.get('univentionMailSharedFolderDeliveryAddress', []), []))

		rewrite_acl = False
		new_acls_tmp = []
		for attr in ['sharedFolderUserACL', 'sharedFolderGroupACL']:
			ud.debug(ud.ADMIN, ud.INFO, 'ACLs: %s' % str(self[attr]))
			if self.hasChanged(attr):
				rewrite_acl = True
				# re-use regular expressions from syntax definitions
				if attr == 'sharedFolderUserACL':
					_sre = univention.admin.syntax.UserMailAddress.regex
				else:
					_sre = univention.admin.syntax.GroupName.regex
				for acl in self[attr]:
					if acl == '':
						continue
					if _sre.match(acl[0]):
						new_acls_tmp.append(' '.join(acl))
			else:
				for acl in self[attr]:
					if acl == '':
						continue
					new_acls_tmp.append(' '.join(acl))

		if rewrite_acl:
			for (a, b, c) in ml:
				if a in ['sharedFolderUserACL', 'sharedFolderGroupACL']:
					ml.remove((a, b, c))
			ml.append(('univentionMailACL', self.oldattr.get('univentionMailACL', []), new_acls_tmp))

		return ml


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):

	filter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('cn', '*'),
		univention.admin.filter.expression('objectClass', 'univentionMailSharedFolder')
	])

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res = []
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn, attributes=attrs))
	return res


def identify(dn, attr, canonical=0):
	return 'univentionMailSharedFolder' in attr.get('objectClass', [])
