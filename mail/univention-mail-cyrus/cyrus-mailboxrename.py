# -*- coding: utf-8 -*-
#
# Univention Mail Cyrus
#  listener module: renaming mailboxes
#
# Copyright 2010-2012 Univention GmbH
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
import os, string, pwd, grp, univention.debug, subprocess, glob, copy, cPickle

name='cyrus-mailboxrename'
description='Rename default imap folders'
filter='(&(objectClass=univentionMail)(uid=*))'
attributes=['uid', 'mailPrimaryAddress', 'univentionMailHomeServer']
FN_CACHE='/var/cache/univention-mail-cyrus/cyrus-mailboxrename.pickle'
modrdn='1'

def is_cyrus_murder_backend():
	if (listener.baseConfig.get('mail/cyrus/murder/master') and listener.baseConfig.get('mail/cyrus/murder/backend/hostname')):
	# ucr currently gives '' if not set, might change to None
		return True
	else:
		return False

def cyrus_userlogfile_rename(new, old):
	userlogfiles = listener.baseConfig.get('mail/cyrus/userlogfiles')
	if userlogfiles and userlogfiles.lower() in ['true', 'yes']:
		newpath='/var/lib/cyrus/log/%s' % (string.lower(new['mailPrimaryAddress'][0]))
		oldpath='/var/lib/cyrus/log/%s' % (string.lower(old['mailPrimaryAddress'][0]))

		cyrus_id=pwd.getpwnam('cyrus')[2]
		mail_id=grp.getgrnam('mail')[2]

		if os.path.exists( oldpath ):
			os.rename(oldpath, newpath)
		else:
			os.mkdir( newpath )
		os.chmod(newpath,0750)
		os.chown(newpath,cyrus_id, mail_id)

def cyrus_userlogfile_delete(old):
	userlogfiles = listener.baseConfig.get('mail/cyrus/userlogfiles')
	if userlogfiles and userlogfiles.lower() in ['true', 'yes']:
		oldpath='/var/lib/cyrus/log/%s' % (string.lower(old['mailPrimaryAddress'][0]))

		if os.path.exists( oldpath ):
			r = glob.glob('%s/*' % oldpath)
			for i in r:
	 			os.unlink(i)
			os.rmdir(oldpath)

def cyrus_usermailbox_rename(new, old):
	mailboxrename = listener.baseConfig.get('mail/cyrus/mailbox/rename')
	if mailboxrename and mailboxrename.lower() in ['true', 'yes']:
		try:
			listener.setuid(0)

			returncode = subprocess.call(['/usr/sbin/univention-cyrus-mailbox-rename', '--user', string.lower(old['mailPrimaryAddress'][0]), string.lower(new['mailPrimaryAddress'][0])])

			cyrus_userlogfile_rename(new, old)
		finally:
			listener.unsetuid()

def cyrus_usermailbox_delete(old):
	mailboxdelete = listener.baseConfig.get('mail/cyrus/mailbox/delete')
	if mailboxdelete and mailboxdelete.lower() in ['true', 'yes']:
		try:
			listener.setuid(0)

			returncode = subprocess.call(['/usr/sbin/univention-cyrus-mailbox-delete', '--user', string.lower(old['mailPrimaryAddress'][0])])

			cyrus_userlogfile_delete(old)
		finally:
			listener.unsetuid()


def handler(dn, new, old, command):
	# copy object "old" - otherwise it gets modified for other listener modules
	old = copy.deepcopy(old)

	if command == 'r':
		listener.setuid(0)
		try:
			with open(FN_CACHE, 'w+') as f:
				os.chmod(FN_CACHE, 0600)
				cPickle.dump(old, f)
		except Exception, e:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'cyrus-mailboxrename: failed to open/write pickle file: %s' % str(e))
		listener.unsetuid()
		# do nothing if command is 'r' ==> modrdn
		return

	if os.path.exists(FN_CACHE):
		listener.setuid(0)
		try:
			with open(FN_CACHE,'r') as f:
				old = cPickle.load(f)
		except Exception, e:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'cyrus-mailboxrename: failed to open/read pickle file: %s' % str(e))
		try:
			os.remove(FN_CACHE)
		except Exception, e:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'cyrus-mailboxrename: cannot remove pickle file: %s' % str(e))
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'cyrus-mailboxrename: for safty reasons cyrus-mailboxrename ignores change of LDAP object: %s' % dn)
			listener.unsetuid()
			return

		listener.unsetuid()

	fqdn = '%s.%s' % (listener.baseConfig['hostname'], listener.baseConfig['domainname'])
	if old:
		oldHomeserver = old.get('univentionMailHomeServer', [''])[0]
		old_mailPrimaryAddress = old.get('mailPrimaryAddress', [''])[0]
		if old_mailPrimaryAddress and oldHomeserver == fqdn:
			# Old mailbox is located on this host
			if new:
				newHomeserver = new.get('univentionMailHomeServer', [''])[0]
				if newHomeserver == fqdn:
					# this host continues hosting the mailbox
					new_mailPrimaryAddress = new.get('mailPrimaryAddress', [''])[0]
					if new_mailPrimaryAddress:
						# in this case cyrus.py will create a new mailbox
						univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'cyrus-mailboxrename: new_mailPrimaryAddress "%s" old_mailPrimaryAddress: "%s"' % (new_mailPrimaryAddress, old_mailPrimaryAddress))
						if string.lower(new_mailPrimaryAddress) != string.lower(old_mailPrimaryAddress):
							cyrus_usermailbox_rename(new, old)
					else:
						# old_mailPrimaryAddress was removed:
						univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'cyrus-mailboxrename: new_mailPrimaryAddress is empty ==> removing mailbox')
						cyrus_usermailbox_delete(old)
				else:
					# this is true if is_groupware_user(new) and newHomeserver != fqdn):
					# Must not delete mailbox without checking if newHomeServer might call move_cyrus_murder_mailbox
					#if not is_cyrus_murder_backend():
					#	cyrus_usermailbox_delete(old)
					pass
			else: # object was removed
				univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'cyrus-mailboxrename: new is empty ==> removing mailbox')
				cyrus_usermailbox_delete(old)
