#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2017-2019 Univention GmbH
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

import subprocess
import itertools as it

import univention.uldap
import univention.admin.uldap
import univention.admin.modules as udm_modules

import univention.config_registry
from univention.management.console.modules.diagnostic import Warning, MODULE
from univention.management.console.modules.diagnostic import util

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check IMAP shared folder ACLs')
description = _('All shared folder ACLs are in sync with UDM.')
run_descr = ['Checks if all IMAP shared Folder ACLs are in sync with UDM']


class ACLError(Exception):
	pass


class MailboxNotExistentError(ACLError):
	def __init__(self, mailbox):
		super(ACLError, self).__init__(mailbox)
		self.mailbox = mailbox

	def __str__(self):
		msg = _('Mail folder {folder!r} does not exist in IMAP.')
		return msg.format(folder=self.mailbox)


class ACLIdentifierError(Exception):
	def __init__(self, identifier):
		super(ACLIdentifierError, self).__init__(identifier)
		self.identifier = identifier


class DuplicateIdentifierACLError(ACLIdentifierError):
	def __str__(self):
		msg = _('Multiple ACL entries for {id!r} in UDM.')
		return msg.format(id=self.identifier)


class ACLDifferenceError(ACLIdentifierError):
	def __init__(self, identifier, udm_right, actual_right):
		super(ACLDifferenceError, self).__init__(identifier)
		self.udm_right = udm_right
		self.actual_right = actual_right


class UserACLError(ACLDifferenceError):
	def __str__(self):
		msg = _('ACL right for user {id!r} is {udm!r} in UDM, but {imap!r} in IMAP.')
		return msg.format(id=self.identifier, udm=self.udm_right, imap=self.actual_right)


class GroupACLError(ACLDifferenceError):
	def __str__(self):
		msg = _('ACL right for group {id!r} is {udm!r} in UDM, but {imap!r} in IMAP.')
		return msg.format(id=self.identifier, udm=self.udm_right, imap=self.actual_right)


class MailFolder(object):
	def __init__(self, udm_folder):
		self.dn = udm_folder.dn
		self.name = udm_folder.get('name')
		self.mail_domain = udm_folder.get('mailDomain')
		self.mail_address = udm_folder.get('mailPrimaryAddress')
		self._user_acl = udm_folder.get('sharedFolderUserACL')
		self._group_acl = udm_folder.get('sharedFolderGroupACL')

	@property
	def common_name(self):
		return '{}@{}'.format(self.name, self.mail_domain)

	def acl(self):
		return ACL.from_udm(self._user_acl, self._group_acl)

	@classmethod
	def from_udm(cls):
		univention.admin.modules.update()
		(ldap_connection, position) = univention.admin.uldap.getMachineConnection()
		module = udm_modules.get('mail/folder')
		for instance in module.lookup(None, ldap_connection, ''):
			instance.open()
			yield cls(instance)


class ACL(object):
	RIGHTS = ('all', 'write', 'append', 'post', 'read', 'none')

	def __init__(self, user_acl, group_acl):
		self.user_acl = user_acl
		self.group_acl = group_acl

	@classmethod
	def from_udm(cls, user_acl, group_acl):
		'''
		Transform the udm acls from [[id, right], [id, right], ..] to a dict
		from identifier to right, where right is the highest right in the acl.
		'''
		def simplify(acl_list):
			merged = dict()
			for (identifier, right) in acl_list:
				merged.setdefault(identifier, set()).add(right)
			for (identifier, rights) in merged.items():
				if len(rights) > 1:
					raise DuplicateIdentifierACLError(identifier)
				else:
					udm_right = next(right for right in cls.RIGHTS if right in rights)
					yield (identifier, udm_right)
		return cls(dict(simplify(user_acl)), dict(simplify(group_acl)))

	def difference(self, other):
		user_diff = self._diff(UserACLError, self.user_acl, other.user_acl)
		group_diff = self._diff(GroupACLError, self.group_acl, other.group_acl)
		return it.chain(user_diff, group_diff)

	def _diff(self, exception, expected, actual):
		all_id = expected.viewkeys() | actual.viewkeys()
		for identifier in all_id:
			exp = expected.get(identifier, 'none')
			act = actual.get(identifier, 'none')
			if exp != act:
				yield exception(identifier, exp, act)


class DovecotACL(ACL):
	DOVECOT_RIGHT_TRANSLATION = (
		('all', set(('lookup', 'read', 'write', 'write-seen', 'post', 'insert',
			'write-deleted', 'expunge', 'admin'))),
		('write', set(('lookup', 'read', 'write', 'write-seen', 'post', 'insert',
			'write-deleted', 'expunge'))),
		('append', set(('lookup', 'read', 'write', 'write-seen', 'post', 'insert'))),
		('post', set(('lookup', 'read', 'write', 'write-seen', 'post'))),
		('read', set(('lookup', 'read', 'write', 'write-seen'))),
		('none', set()),
	)

	@classmethod
	def from_folder(cls, folder):
		acl_list = cls._get_dovecot_acl(folder)
		merged = dict()
		for (identifier, rights) in acl_list.items():
			acl_type = 'group' if identifier.startswith('group=') else 'user'
			udm_id = identifier.replace('user=', '', 1) if identifier.startswith('user=') \
				else identifier.replace('group=', '', 1) if identifier.startswith('group=') \
				else identifier
			udm_right = next(udm_right for (udm_right, dovecot_rights) in cls.DOVECOT_RIGHT_TRANSLATION if rights.issuperset(dovecot_rights))
			merged.setdefault(acl_type, dict())[udm_id] = udm_right
		return cls(merged.get('user', {}), merged.get('group', {}))

	@staticmethod
	def _get_dovecot_acl(folder):
		mailbox = 'shared/{pm}' if folder.mail_address else '{cn}/INBOX'
		cmd = ('doveadm', 'acl', 'get', '-u', 'Administrator', mailbox.format(cn=folder.common_name, pm=folder.mail_address))
		output = subprocess.check_output(cmd, stderr=subprocess.PIPE).splitlines()
		return {identifier.strip(): set(rights.strip().split()) for (identifier, rights) in (line.rsplit('  ', 1) for line in output)}


def all_differences(acl_class):
	for folder in MailFolder.from_udm():
		try:
			udm_acl = folder.acl()
			imap_acl = acl_class.from_folder(folder)
			for difference in udm_acl.difference(imap_acl):
				yield (folder, difference)
		except ACLError as error:
			yield (folder, error)


def udm_mail_link(folder):
	return {
		'module': 'udm',
		'flavor': 'mail/mail',
		'props': {
			'openObject': {
				'objectDN': folder.dn,
				'objectType': 'mail/folder'
			}
		}
	}


def run(_umc_instance):
	if not util.is_service_active('IMAP'):
		return

	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	if configRegistry.is_true('mail/dovecot'):
		acl_class = DovecotACL
	else:
		return

	differences = list(all_differences(acl_class))
	ed = [
		_('Found differences in the ACLs for IMAP shared folders between UDM and IMAP.') + ' ' +
		_('This is not necessarily a problem, if the the ACL got changed via IMAP.')]

	modules = list()
	for (folder, group) in it.groupby(differences, lambda x: x[0]):
		name = folder.common_name
		ed.append('')
		ed.append(_('In mail folder {name} (see {{udm:mail/mail}}):').format(name=name))
		ed.extend(str(error) for (_, error) in group)
		modules.append(udm_mail_link(folder))

	if modules:
		MODULE.error('\n'.join(ed))
		raise Warning(description='\n'.join(ed), umc_modules=modules)


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
