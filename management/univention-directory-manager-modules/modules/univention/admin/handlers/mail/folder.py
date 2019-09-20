# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for mail imap folders
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
object_name = _('IMAP mail folder')
object_name_plural = _('IMAP mail folders')
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
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True
	),
	'mailDomain': univention.admin.property(
		short_description=_('Mail domain'),
		long_description='',
		syntax=ldap_search_maildomain,
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
	),
	'sharedFolderGroupACL': univention.admin.property(
		short_description=_('Group ACL'),
		long_description='',
		syntax=univention.admin.syntax.SharedFolderGroupACL,
		multivalue=True,
	),
	'mailQuota': univention.admin.property(
		short_description=_('Quota in MB'),
		long_description=_('How many MB of emails can be stored in the shared folder (independent of the users that stored them).'),
		syntax=univention.admin.syntax.integer,
	),
	'mailHomeServer': univention.admin.property(
		short_description=_('Mail home server'),
		long_description='',
		syntax=univention.admin.syntax.MailHomeServer,
		nonempty_is_default=True,
		required=True,
	),
	'mailPrimaryAddress': univention.admin.property(
		short_description=_('E-Mail address'),
		long_description='',
		syntax=univention.admin.syntax.emailAddressValidDomain,
		include_in_default_search=True,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General IMAP mail folder settings'), layout=[
			["name", "mailDomain"],
			["mailHomeServer"],
			["mailQuota"],
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
mapping.register('mailQuota', 'univentionMailUserQuota', None, univention.admin.mapping.ListToString)
mapping.register('mailHomeServer', 'univentionMailHomeServer', None, univention.admin.mapping.ListToString)
mapping.register('mailPrimaryAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _get_admin_diary_args(self, event):
		return {'module': self.module, 'nameWithMailDomain': self.description()}

	def _post_unmap(self, oldinfo, oldattr):
		cn = oldattr.get('cn', [])
		if cn:
			oldinfo['name'] = cn[0].split('@', 1)[0]
			oldinfo['mailDomain'] = cn[0].split('@', 1)[1]

		# fetch values for ACLs
		acls = oldattr.get('univentionMailACL', [])
		oldinfo['sharedFolderUserACL'] = []
		oldinfo['sharedFolderGroupACL'] = []
		if acls:
			for acl in acls:
				if acl.find('@') > 0 or acl.startswith('anyone'):
					oldinfo['sharedFolderUserACL'].append(acl.rsplit(' ', 1))
				else:
					oldinfo['sharedFolderGroupACL'].append(acl.rsplit(' ', 1))
		return oldinfo

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


lookup = object.lookup
identify = object.identify
