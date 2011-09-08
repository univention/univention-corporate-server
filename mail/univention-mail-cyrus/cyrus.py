# -*- coding: utf-8 -*-
#
# Univention Mail Cyrus Kolab2
#  listener module: creating mailboxes and sieve scripts
#
# Copyright 2004-2010 Univention GmbH
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

import listener
import os, string, pwd, grp, univention.debug, subprocess

name='cyrus'
description='Create default imap folders'
filter='(&(objectClass=univentionMail)(uid=*))'
attributes=['uid', 'mailPrimaryAddress', 'mailGlobalSpamFolder', 'kolabHomeServer']

def is_groupware_user(new):
	if new.has_key('objectClass'):
		for oc in new['objectClass']:
			if oc.lower() == 'kolabinetorgperson':
				return True
	return False

def is_cyrus_murder_backend():
	if (listener.baseConfig.get('mail/cyrus/murder/master') and listener.baseConfig.get('mail/cyrus/murder/backend/hostname')):
	# ucr currently gives '' if not set, might change to None
		return True
	else:
		return False

def create_cyrus_userlogfile(mailaddress):
	userlogfiles = listener.baseConfig.get('mail/cyrus/userlogfiles')
	if userlogfiles and userlogfiles.lower() in ['true', 'yes']:
		path='/var/lib/cyrus/log/%s' % (mailaddress)

		cyrus_id=pwd.getpwnam('cyrus')[2]
		mail_id=grp.getgrnam('mail')[2]

		if not os.path.exists( path ):
			os.mkdir(path)
		os.chmod(path,0750)
		os.chown(path,cyrus_id, mail_id)

def create_cyrus_mailbox(new):
	if new.has_key('mailPrimaryAddress') and new['mailPrimaryAddress'][0]:
		try:
			listener.setuid(0)

			p = os.popen('/usr/sbin/univention-cyrus-mkdir %s' % (string.lower(new['mailPrimaryAddress'][0])))
			p.close()

			create_cyrus_userlogfile(string.lower(new['mailPrimaryAddress'][0]))
		finally:
			listener.unsetuid()

def move_cyrus_murder_mailbox(new, old):
	if new.has_key('mailPrimaryAddress') and new['mailPrimaryAddress'][0] and old.has_key('mailPrimaryAddress') and old['mailPrimaryAddress'][0]:
		try:
			listener.setuid(0)

			oldemail=string.lower(old['mailPrimaryAddress'][0])
			localCyrusMurderBackendFQDN = listener.baseConfig.get('mail/cyrus/murder/backend/hostname')
			if ( localCyrusMurderBackendFQDN.find('.') == -1 ):
				localCyrusMurderBackendFQDN = '%s.%s' % (listener.baseConfig.get('mail/cyrus/murder/backend/hostname'), listener.baseConfig.get('domainname'))

			returncode = subprocess.call("/usr/sbin/univention-cyrus-murder-movemailbox %s %s" % (oldemail, localCyrusMurderBackendFQDN), shell=True)

			if ( returncode != 0 ):
				univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, '%s: Cyrus Murder mailbox rename failed for %s' % (name, oldemail))

			create_cyrus_userlogfile(string.lower(new['mailPrimaryAddress'][0]))
		finally:
			listener.unsetuid()

def handler(dn, new, old):
	fqdn = '%s.%s' % (listener.baseConfig['hostname'], listener.baseConfig['domainname'])
	if new and (is_groupware_user(new) and new.has_key('kolabHomeServer') and new['kolabHomeServer'][0] == fqdn) or (not is_groupware_user(new)):
		if not old:
				create_cyrus_mailbox(new)
		else:
			old_mailPrimaryAddress = old.get('mailPrimaryAddress', [''])[0]
			if not is_cyrus_murder_backend():
				mailboxrename = listener.baseConfig.get('mail/cyrus/mailbox/rename')
				if old_mailPrimaryAddress and mailboxrename and mailboxrename.lower() in ['true', 'yes']:
					# cyrus-mailboxrename.py will take care of this case
					pass
				else:
					create_cyrus_mailbox(new)
			else:
				if (is_groupware_user(new) and (not is_groupware_user(old))):
				# if the groupware option changed to yes
					create_cyrus_mailbox(new)
					# FIXME: case for mailbox rename
				else: # the groupware option is unchanged or changed to no
					# no behaviour change here just a bit improved readability
					old_kolabHomeServer = old.get('kolabHomeServer', [''])[0]
					if (old_kolabHomeServer and old_kolabHomeServer != fqdn):
						# the kolabHomeServer changed:
						move_cyrus_murder_mailbox(new, old)
					#elif (old_kolabHomeServer == fqdn):
						# cyrus-mailboxrename.py will take care of this case

