# -*- coding: utf-8 -*-
#
# Univention Mail Dovecot - listener module: manages shared folders
#
# Copyright 2015-2019 Univention GmbH
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

#
#
# The listener module:
# * adds mailboxes with the type depending on existence of mailPrimaryAddress.
# * removes mailboxes of both types, deletes from disk only
#   if mail/dovecot/mailbox/delete=True.
# * renames mailboxes of both types, renames/moves on disk only
#   if mail/dovecot/mailbox/rename=True.
# * modifies of existing public mailboxes:
#   - add a mailPrimaryAddress: move mb from public to private/shared
#     namespace (or just create the private/shared mb if
#     mail/dovecot/mailbox/rename=False).
#   - rm a mailPrimaryAddress: move mb from private/shared to public
#     namespace (or just create the public mb
#     if mail/dovecot/mailbox/rename=False).
#   - change mailPrimaryAddress: rename private/shared mb (on disk only
#     if mail/dovecot/mailbox/rename=True).
# * tries to unsubscribes potential mb subscribers if a mb was renamed or
#   removed.
# * sets ACLs according to UDM. Uses "$ doveadm acl ..." for public mb,
#   imaplib.setacl() for private/shared mb.
# * uses a master-user to login as another user via IMAP. Credentials are
#   stored in clear text in /etc/dovecot/master-users.
# * sets the quota for public folders in the configuration file
#   /etc/dovecot/conf.d/10-mail.conf, the quota for private/shared mb is
#   taken from LDAP. Info is in objectClass=univentionMailSharedFolder
#    → univentionMailUserQuota. The quota info (and the name) for the public
#   folders are cached in the UCRV mail/dovecot/internal/sharedfolders.
# * runs "$ doveadm" commands as root, using the "Administrator" user as
#   login.
# * assumes Dovecot runs as dovecot:dovecot.
# * stores the list of shared (private) mailboxes in a flat text file:
#   /var/lib/dovecot/shared-mailboxes. It gets only updated when a ACL is
#   changed through IMAP. For large installations this should be changed to
#   a SQL dictionary.
#
#
# We use two different kinds of shared folders:
# - "public mailboxes" (http://wiki2.dovecot.org/SharedMailboxes/Public)
# - "shared mailboxes" (http://wiki2.dovecot.org/SharedMailboxes/Shared)
#
# In the case of the creation of a shared IMAP folder _without_ an email
# address, a mailbox in the "public" namespace will be used. We create a
# separate namespace for each public mailbox, as the quota is the same for all
# mailboxes of each public namespace. The namespace name is the cn.
# Those mailboxes' name will be <namespace>/<mailbox>, eg "pub1@uni.dtr/INBOX".
#
# In the case of the creation of a shared IMAP folder _with_ an email
# address, a private mailbox will be created and its INBOX will be shared.
# The mailbox will live in the "private" namespace, but the shared folder
# (the INBOX) will be accessed through the "shared" namespace. Being a
# common private mailbox, the user quota from LDAP will be used just like
# with a common email account. The only difference is, that a LDAP object of
# objectClass univentionMailSharedFolder contains the mailPrimaryAddress
# attribute, not a common user with objectClass univentionMail.
# Those mailboxes' name will be shared/<email>, eg "shared/pub1@uni.dtr". Just
# like any shared mailbox from a user.
#
# If multiple shared folders of both type are present, then in the users
# frontend it may look like this:
#
# /
# +--INBOX
# |
# +--pub1@uni.dtr
# |    +--INBOX
# |
# +--pub2@uni.dtr
# |    +--INBOX
# |
# +--shared
#     +--pub3@uni.dtr
#     +--pub4@uni.dtr
#
#
# In both cases it would be possible to create subfolders if a user gets the
# "k" (create) and "x" (delete) ACL flags. Currently those are not given to
# users even when in UDM the "all" permission is chosen. For creation "k" is
# sufficient, "x" is only needed for renaming, but it does allow mailbox
# deletion too.
#
#

from __future__ import absolute_import

import listener
from univention.mail.dovecot_shared_folder import DovecotSharedFolderListener


listener.configRegistry.load()
hostname = listener.configRegistry['hostname']
domainname = listener.configRegistry['domainname']

name = 'dovecot-shared-folder'
description = 'Create shared folders for Dovecot'
filter = '(&(objectClass=univentionMailSharedFolder)(univentionMailHomeServer=%s.%s))' % (hostname, domainname)


def handler(dn, new, old):
	global hostname, domainname
	hostname = hostname.lower()
	domainname = domainname.lower()

	listener.configRegistry.load()
	dl = DovecotSharedFolderListener(listener, name)

	#
	# Create a new shared folder
	#
	if (new and not old) \
		or ('univentionMailHomeServer' not in old) \
		or (
			'univentionMailHomeServer' in new and 'univentionMailHomeServer' in old and
			new['univentionMailHomeServer'][0].lower() != old['univentionMailHomeServer'][0].lower() and
			new['univentionMailHomeServer'][0].lower() in [hostname, '%s.%s' % (hostname, domainname)]):
		dl.add_shared_folder(new)
		return

	#
	# Delete existing shared folder
	#
	if (old and not new) \
		or ("univentionMailHomeServer" not in new) \
		or (not new["univentionMailHomeServer"][0].lower() in [hostname, "%s.%s" % (hostname, domainname)]):
		dl.del_shared_folder(old)
		return

	#
	# Modify a shared folder
	#
	if old and new:
		dl.mod_shared_folder(old, new)
		return
