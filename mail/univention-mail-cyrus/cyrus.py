# -*- coding: utf-8 -*-
#
# Univention Mail Cyrus
#  listener module: creating mailboxes and sieve scripts
#
# Copyright 2004-2015 Univention GmbH
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

__package__='' 	# workaround for PEP 366

import listener
import univention.debug

import os
import pwd
import grp
import subprocess
import glob
import copy
import cPickle

name='cyrus'
description='manage imap folders'
filter='(&(objectClass=univentionMail)(uid=*))'
attributes=['uid', 'mailPrimaryAddress', 'univentionMailHomeServer']
FN_CACHE='/var/cache/univention-mail-cyrus/cyrus-mailboxrename.pickle'
modrdn='1'

def is_cyrus_murder_backend():
	if (listener.configRegistry.get('mail/cyrus/murder/master') and listener.configRegistry.get('mail/cyrus/murder/backend/hostname')):
	# ucr currently gives '' if not set, might change to None
		return True
	else:
		return False

def cyrus_usermailbox_delete(old):

	# delete mailbox and logfiles
	if listener.configRegistry.is_true('mail/cyrus/mailbox/delete', False):

		univention.debug.debug(
			univention.debug.LISTENER,
			univention.debug.INFO,
			'cyrus: delete mailbox %s' % old)

		try:
			listener.setuid(0)
			subprocess.call(['/usr/sbin/univention-cyrus-mailbox-delete', '--user', old])
			if listener.configRegistry.is_true('mail/cyrus/userlogfiles', False):
				oldpath = '/var/lib/cyrus/log/%s' % old
				if os.path.exists(oldpath):
					r = glob.glob('%s/*' % oldpath)
					for i in r:
						os.unlink(i)
					os.rmdir(oldpath)
		finally:
		    listener.unsetuid()

def cyrus_usermailbox_rename(old, new):

	# rename mailbox and rename/create logfiles
	if listener.configRegistry.is_true('mail/cyrus/mailbox/rename', False):

		univention.debug.debug(
			univention.debug.LISTENER,
			univention.debug.INFO,
			'cyrus: rename mailbox %s to %s' % (old, new))

		try:
			listener.setuid(0)
			returncode = subprocess.call(['/usr/sbin/univention-cyrus-mailbox-rename', '--user', old, new])
			if (returncode != 0):
				univention.debug.debug(
					univention.debug.LISTENER,
					univention.debug.ERROR,
					'%s: Cyrus mailbox rename failed for %s' % (name, old))
			if listener.configRegistry.is_true('mail/cyrus/userlogfiles', False):
				newpath = '/var/lib/cyrus/log/%s' % new
				oldpath = '/var/lib/cyrus/log/%s' % old
				cyrus_id = pwd.getpwnam('cyrus')[2]
				mail_id = grp.getgrnam('mail')[2]
				if os.path.exists(oldpath):
					os.rename(oldpath, newpath)
				else:
					os.mkdir(newpath)
				os.chmod(newpath, 0750)
				os.chown(newpath, cyrus_id, mail_id)
		finally:
			listener.unsetuid()

def create_cyrus_mailbox(new):

	univention.debug.debug(
		univention.debug.LISTENER,
		univention.debug.INFO,
		'cyrus: create mailbox %s' % new)

	try:
		# create mailbox
		listener.setuid(0)
		subprocess.call(("/usr/sbin/univention-cyrus-mkdir", new))
		create_cyrus_userlogfile(new)
	finally:
		listener.unsetuid()

def create_cyrus_userlogfile(mailaddress):

	# create log file directory
	if listener.configRegistry.is_true('mail/cyrus/userlogfiles', False):
		path = '/var/lib/cyrus/log/%s' % (mailaddress)
		cyrus_id = pwd.getpwnam('cyrus')[2]
		mail_id = grp.getgrnam('mail')[2]
		if not os.path.exists(path):
			os.mkdir(path)
		os.chmod(path, 0750)
		os.chown(path, cyrus_id, mail_id)

def move_cyrus_murder_mailbox(old, new):

	murderBackend = listener.configRegistry.get('mail/cyrus/murder/backend/hostname')
	if not "." in murderBackend:
		murderBackend = '%s.%s' % (murderBackend, listener.configRegistry.get('domainname'))

	univention.debug.debug(
		univention.debug.LISTENER,
		univention.debug.INFO,
		'cyrus: murder move mailbox %s to %s' % (old, murderBackend))

	try:
		listener.setuid(0)
		returncode = subprocess.call("/usr/sbin/univention-cyrus-murder-movemailbox %s %s" % (old, murderBackend), shell=True)
		if (returncode != 0):
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.ERROR,
				'%s: Cyrus Murder mailbox move failed for %s' % (name, old))
		create_cyrus_userlogfile(new)
	finally:
		listener.unsetuid()

def handler(dn, new, old, command):

	fqdn = '%s.%s' % (listener.configRegistry['hostname'], listener.configRegistry['domainname'])
	fqdn = fqdn.lower()

	# copy object "old" - otherwise it gets modified for other listener modules
	old = copy.deepcopy(old)

	# do nothing if command is 'r' ==> modrdn
	if command == 'r':
		listener.setuid(0)
		try:
			with open(FN_CACHE, 'w+') as f:
				os.chmod(FN_CACHE, 0600)
				cPickle.dump(old, f)
		except Exception, e:
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.ERROR,
				'cyrus: failed to open/write pickle file: %s' % str(e))
		listener.unsetuid()
		return

	# check modrdn changes
	if os.path.exists(FN_CACHE):
		listener.setuid(0)
		try:
			with open(FN_CACHE,'r') as f:
				old = cPickle.load(f)
		except Exception, e:
		    univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.ERROR,
				'cyrus: failed to open/read pickle file: %s' % str(e))
		try:
			os.remove(FN_CACHE)
		except Exception, e:
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.ERROR,
				'cyrus: cannot remove pickle file: %s' % str(e))
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.ERROR,
				'cyrus: for safty reasons cyrus-mailboxrename ignores change of LDAP object: %s' % dn)
			listener.unsetuid()
			return

		listener.unsetuid()	


	# new
	if new and not old:
		newHomeServer = new.get('univentionMailHomeServer', [''])[0]
		newMailPrimaryAddress = new.get('mailPrimaryAddress', [''])[0]
		if newHomeServer.lower() == fqdn:
			# create mailbox if we are the home server 
			if newMailPrimaryAddress:
				create_cyrus_mailbox(newMailPrimaryAddress.lower())

	# modified
	if new and old:
		oldMailPrimaryAddress = old.get('mailPrimaryAddress', [''])[0]
		oldHomeServer = old.get('univentionMailHomeServer', [''])[0]
		newMailPrimaryAddress = new.get('mailPrimaryAddress', [''])[0]
		newHomeServer = new.get('univentionMailHomeServer', [''])[0]

		# mailPrimaryAddress new
		if not oldMailPrimaryAddress and newMailPrimaryAddress:
			if newHomeServer.lower() == fqdn:
				create_cyrus_mailbox(newMailPrimaryAddress.lower())

		# mailPrimaryAddress changed, but same home server
		if oldMailPrimaryAddress and newMailPrimaryAddress:
			if oldMailPrimaryAddress.lower() != newMailPrimaryAddress.lower():
				if newHomeServer.lower() == oldHomeServer.lower() == fqdn:
					if listener.configRegistry.is_true('mail/cyrus/mailbox/rename', False):
						# rename
						cyrus_usermailbox_rename(oldMailPrimaryAddress.lower(), newMailPrimaryAddress.lower())
					else:
						# create new, delete old
						create_cyrus_mailbox(newMailPrimaryAddress.lower())
						cyrus_usermailbox_delete(oldMailPrimaryAddress.lower())

		# univentionMailHomeServer new
		if not oldHomeServer and newHomeServer.lower() == fqdn:
			if newMailPrimaryAddress:
				create_cyrus_mailbox(newMailPrimaryAddress.lower())

		# univentionMailHomeServer changed
		if oldHomeServer and newHomeServer:
			if newHomeServer.lower() != oldHomeServer.lower():
				if newHomeServer.lower() == fqdn:
					# univentionMailHomeServer has changed, create a new mailbox
					# or move murder mailbox
					if not is_cyrus_murder_backend():
						if newMailPrimaryAddress:
							create_cyrus_mailbox(newMailPrimaryAddress.lower())
					else:
						if oldMailPrimaryAddress and newMailPrimaryAddress:
							move_cyrus_murder_mailbox(oldMailPrimaryAddress.lower(), newMailPrimaryAddress.lower())
							# did the mailbox name change when moving between servers?
							if oldMailPrimaryAddress != newMailPrimaryAddress:
								if listener.configRegistry.is_true('mail/cyrus/mailbox/rename', False):
									cyrus_usermailbox_rename(oldMailPrimaryAddress.lower(), newMailPrimaryAddress.lower())
								#else tree is already handled above(if not is_cyrus_murder_backend())

				if oldHomeServer.lower() == fqdn:
					# delete mailbox on old home server
					# if we are not a cyrus murder
					if not is_cyrus_murder_backend():
						if oldMailPrimaryAddress:
							cyrus_usermailbox_delete(oldMailPrimaryAddress.lower())

		# univentionMailHomeServer or MailPrimaryAddress deleted
		if not newHomeServer or not newMailPrimaryAddress:
			if oldHomeServer.lower() == fqdn and oldMailPrimaryAddress:
				cyrus_usermailbox_delete(oldMailPrimaryAddress.lower())

	# delete
	if old and not new:
		oldHomeServer = old.get('univentionMailHomeServer', [''])[0]
		oldMailPrimaryAddress = old.get('mailPrimaryAddress', [''])[0]
		# delete maibox if we are the home server
		if oldHomeServer == fqdn and oldMailPrimaryAddress:
			cyrus_usermailbox_delete(oldMailPrimaryAddress.lower())

