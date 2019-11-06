# -*- coding: utf-8 -*-
#
# Univention Mail Dovecot - listener module: add/edit/remove mailboxes
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


from __future__ import absolute_import

import os
import cPickle

import listener
from univention.mail.dovecot import DovecotListener


name = 'dovecot'
description = 'manage imap folders'
filter = '(&(objectClass=univentionMail)(uid=*))'
attributes = ['mailPrimaryAddress', 'univentionMailHomeServer']
modrdn = "1"

DOVECOT_OLD_PICKLE = "/var/spool/univention-mail-dovecot/dovecot_old_dn"


class DovecotUserListener(DovecotListener):

	def new_email_account2(self, email):
		try:
			self.new_email_account(email)
		except Exception as ex:
			self.log_e("Failed creating email account %r: %r" % (email, ex))
			raise
		self.log_p("Added mail account %r." % (email,))

	def delete_email_account2(self, dn, email):
		try:
			self.delete_email_account(dn, email)
		except Exception as ex:
			self.log_e("Failed removing old email account %r of dn %r: %r" % (email, dn, ex))
			raise
		self.log_p("Deleted mail home of %r." % (email,))

	def move_email_account2(self, dn, old_mail, new_mail):
		if listener.configRegistry.is_true('mail/dovecot/mailbox/rename', False):
			# rename/move
			try:
				self.move_user_home(new_mail, old_mail)
			except Exception as ex:
				self.log_e("Failed moving mail home from %r to %r: %r" % (old_mail, new_mail, ex))
				raise
		else:
			# create new, delete old
			self.log_p("Mailbox renaming disabled, creating new, deleting old mailbox.")
			self.new_email_account2(new_mail)
			self.delete_email_account2(dn, old_mail)
		# flush cache to prevent login with previous email address
		self.flush_auth_cache()
		self.log_p("Renamed/moved mailbox %r to %r." % (old_mail, new_mail))

	@staticmethod
	def flush_auth_cache():
		try:
			listener.setuid(0)
			listener.run('/usr/bin/doveadm', ["/usr/bin/doveadm", "auth", "cache", "flush"], uid=0)
		finally:
			listener.unsetuid()


def load_old(old):
	if os.path.exists(DOVECOT_OLD_PICKLE):
		f = open(DOVECOT_OLD_PICKLE, "r")
		p = cPickle.Unpickler(f)
		old = p.load()
		f.close()
		os.unlink(DOVECOT_OLD_PICKLE)
		return old
	else:
		return old


def save_old(old):
	f = open(DOVECOT_OLD_PICKLE, "w+")
	os.chmod(DOVECOT_OLD_PICKLE, 0o600)
	p = cPickle.Pickler(f)
	p.dump(old)
	p.clear_memo()
	f.close()


def handler(dn, new, old, command):
	if command == 'r':
		save_old(old)
		# flush auth cache in case of modrdn: the cached PAM entry would
		# create a LDAP query with the previous username
		DovecotUserListener.flush_auth_cache()
		return
	elif command == 'a':
		old = load_old(old)

	listener.configRegistry.load()
	dl = DovecotUserListener(listener, name)
	oldMailPrimaryAddress = old.get('mailPrimaryAddress', [""])[0].lower()
	newMailPrimaryAddress = new.get('mailPrimaryAddress', [""])[0].lower()
	oldHomeServer = old.get('univentionMailHomeServer', [''])[0].lower()
	newHomeServer = new.get('univentionMailHomeServer', [''])[0].lower()
	fqdn = '%s.%s' % (listener.configRegistry['hostname'], listener.configRegistry['domainname'])
	fqdn = fqdn.lower()
	# If univentionMailHomeServer is not set, all servers are responsible.
	is_old_home_server = oldHomeServer == "" or oldHomeServer == fqdn
	is_new_home_server = newHomeServer == "" or newHomeServer == fqdn

	#
	# NEW email account
	#
	if new and not old and is_new_home_server:
		if newMailPrimaryAddress.strip():
			dl.new_email_account2(newMailPrimaryAddress)
		return

	#
	# DELETE email account
	#
	if oldMailPrimaryAddress and is_old_home_server \
		and (not newMailPrimaryAddress or not is_new_home_server):
		dl.delete_email_account2(dn, oldMailPrimaryAddress)
		return

	#
	# MODIFY email address / univentionMailHomeServer
	#
	if old and new:
		# new mailPrimaryAddress
		if is_new_home_server and \
			not oldMailPrimaryAddress and newMailPrimaryAddress:
			dl.new_email_account2(newMailPrimaryAddress)
			return

		# mailPrimaryAddress changed, but same home server
		if is_old_home_server and is_new_home_server \
			and oldMailPrimaryAddress and newMailPrimaryAddress \
			and oldMailPrimaryAddress != newMailPrimaryAddress:
			dl.move_email_account2(dn, oldMailPrimaryAddress, newMailPrimaryAddress)
			return

		# new univentionMailHomeServer
		if is_new_home_server and not is_old_home_server and newMailPrimaryAddress:
			dl.new_email_account2(newMailPrimaryAddress)
			return

		# univentionMailHomeServer changed
		if is_new_home_server \
			and newHomeServer != oldHomeServer \
			and newMailPrimaryAddress:
			# create a new mailbox, moving between servers is not supported
			dl.new_email_account2(newMailPrimaryAddress)
			return
