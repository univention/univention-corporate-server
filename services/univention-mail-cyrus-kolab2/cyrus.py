# -*- coding: utf-8 -*-
#
# Univention Mail Cyrus Kolab2
#  listener module: creating mailboxes and sieve scripts
#
# Copyright (C) 2004, 2005, 2006, 2007, 2008 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import listener
import os, string, pwd, grp, univention.debug

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

def handler(dn, new, old):
	fqdn = '%s.%s' % (listener.baseConfig['hostname'], listener.baseConfig['domainname'])
	if new and not old:
		if (is_groupware_user(new) and new.has_key('kolabHomeServer') and new['kolabHomeServer'][0] == fqdn) or (not is_groupware_user(new)):
			if new.has_key('mailPrimaryAddress') and new['mailPrimaryAddress'][0]:
				try:
					listener.setuid(0)

					p = os.popen('/usr/sbin/univention-cyrus-mkdir %s' % (string.lower(new['mailPrimaryAddress'][0])))
					p.close()

					cyrus_id=pwd.getpwnam('cyrus')[2]
					mail_id=grp.getgrnam('mail')[2]

					if listener.baseConfig.has_key('mail/cyrus/userlogfiles') and listener.baseConfig['mail/cyrus/userlogfiles'].lower() in ['true', 'yes']:
						path='/var/lib/cyrus/log/%s' % (string.lower(new['mailPrimaryAddress'][0]))
						if not os.path.exists( path ):
							os.mkdir(path)
						os.chmod(path,0750)
						os.chown(path,cyrus_id, mail_id)

				finally:
					listener.unsetuid()
	elif new and old:
		if (listener.baseConfig.has_key('mail/cyrus/murder/master') and listener.baseConfig.has_key('mail/cyrus/murder/backend/hostname')):
			if (is_groupware_user(new) and new.has_key('kolabHomeServer') and new['kolabHomeServer'][0] == fqdn and ((not is_groupware_user(old)) or (old.has_key('kolabHomeServer') and old['kolabHomeServer'][0] != fqdn))):
				if new.has_key('mailPrimaryAddress') and new['mailPrimaryAddress'][0] and old.has_key('mailPrimaryAddress') and old['mailPrimaryAddress'][0]:
					try:
						listener.setuid(0)
						f=open('/etc/cyrus.secret')
						pw=f.read()
						f.close()

						oldemail=string.lower(old['mailPrimaryAddress'][0])
						newbackend = listener.baseConfig['mail/cyrus/murder/backend/hostname']
						p = os.popen("/usr/sbin/univention-cyrus-murder-movemailbox -o %s %s" % (oldemail, newbackend))
						if ( p.close() is not None ):
							 univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, '%s: Cyrus Murder mailbox rename failed for %s' % (name, oldemail))

						cyrus_id=pwd.getpwnam('cyrus')[2]
						mail_id=grp.getgrnam('mail')[2]

						if listener.baseConfig.has_key('mail/cyrus/userlogfiles') and listener.baseConfig['mail/cyrus/userlogfiles'].lower() in ['true', 'yes']:
							path='/var/lib/cyrus/log/%s' % (string.lower(new['mailPrimaryAddress'][0]))
							if not os.path.exists( path ):
								os.mkdir(path)
							os.chmod(path,0750)
							os.chown(path,cyrus_id, mail_id)
					finally:
						listener.unsetuid()
