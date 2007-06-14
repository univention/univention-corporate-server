#
# Univention Mail Cyrus
#  listener module: creating mailboxes
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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
description='Create default imap folders and sieve mail filters'
filter='(&(objectClass=univentionMail)(uid=*))'
attributes=['uid', 'mailPrimaryAddress', 'mailGlobalSpamFolder']

def handler(dn, new, old):
	if new.has_key('mailPrimaryAddress') and new['mailPrimaryAddress'][0]:
		listener.setuid(0)

		try:
			p = os.popen('/usr/sbin/univention-cyrus-mkdir %s' % (string.lower(new['mailPrimaryAddress'][0])))
			p.close()

			path='/var/lib/cyrus/log/%s' % (string.lower(new['mailPrimaryAddress'][0]))
			try:
				os.mkdir(path)
			except:
				pass
			os.chmod(path,0750)
			cyrus_id=pwd.getpwnam('cyrus')[2]
			mail_id=grp.getgrnam('mail')[2]
			os.chown(path,cyrus_id, mail_id)

			listener.unsetuid()
		except:
			pass


		if listener.baseConfig.has_key('mail/cyrus/version') and listener.baseConfig['mail/cyrus/version']=='2.2':
			user_name = new['mailPrimaryAddress'][0]
		else:
			user_name = (new['mailPrimaryAddress'][0]).replace('.','^')
		if listener.baseConfig.has_key('mail/cyrus/version') and listener.baseConfig['mail/cyrus/version']=='2.2':
			userpart=user_name.split('@')[0]
			domainpart=user_name.split('@')[1]
			userpart=userpart.replace('.', '^')
			sieve_path = '/var/spool/cyrus/sieve/domain/%s/%s/%s/%s' % (domainpart[0], domainpart, userpart[0], userpart)
		else:
			sieve_path = '/var/spool/sieve/%s/%s' % (user_name[0], user_name)
		active_spam_rule = 'default'
		global_spam_rule = 'global.sieve.script'
		local_spam_rule  = 'local.sieve.script'

		sieve_script = ''
		if new.has_key('mailGlobalSpamFolder') and new['mailGlobalSpamFolder'][0] == '1':
			sieve_script = '%s/%s' % (sieve_path, global_spam_rule)
		else:
			sieve_script = '%s/%s' % (sieve_path, local_spam_rule)

		listener.setuid(0)
		try:
			active_symlink = '%s/%s' % (sieve_path, active_spam_rule)
			try:
				os.remove(active_symlink)
			except:
				pass
			cyrus_id = pwd.getpwnam('cyrus')[2]
			mail_id  = grp.getgrnam('mail')[2]
			os.symlink(sieve_script, active_symlink)
			os.chown(sieve_script, cyrus_id, mail_id)

			if listener.baseConfig.has_key('mail/cyrus/version') and listener.baseConfig['mail/cyrus/version']=='2.2':
				os.system('/usr/lib/cyrus/bin/sievec %s %s%s >/tmp/foo' % (active_symlink, active_symlink, "bc"))
				os.chown("%s%s"%(active_symlink,'bc'), cyrus_id, mail_id)
				os.chown("%s%s"%(active_symlink,'bc'), cyrus_id, mail_id)
		finally:
			listener.unsetuid()
