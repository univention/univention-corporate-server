# -*- coding: utf-8 -*-
#
# Univention Mail Cyrus
#  listener module: manages shared folders
#
# Copyright 2004-2011 Univention GmbH
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
import os, univention.debug, cPickle

hostname=listener.baseConfig['hostname']
domainname=listener.baseConfig['domainname']
ip=listener.baseConfig['interfaces/eth0/address']

name='cyrus-shared-folder'
description='Create shared folders'
filter='(&(objectClass=univentionMailSharedFolder)(|(univentionMailHomeServer=%s)(univentionMailHomeServer=%s.%s)))' % (ip, hostname, domainname)

directory='/var/cache/univention-mail-cyrus/'

modrdn='1'

def handler(dn, new, old, command):

	try:
		old_dn=None

		filename = directory+'/old_dn'

		try:
			if os.path.exists(filename):
				f=open(filename,'r')
				old_dn=cPickle.load(f)
				f.close()

		except:
			pass

		if command == 'r':

			f=open(filename, 'w+')
			os.chmod(filename, 0600)
			cPickle.dump(dn, f)
			f.close()

	except:
		pass

	# Done as function because it is called quite often
	def setacl(mailbox, email, policy):
		try:
			listener.setuid(0)
			p = os.popen( '/usr/sbin/univention-cyrus-set-acl %s \'%s\' %s' % ( mailbox, email, policy ) )
			p.close()
			listener.unsetuid()
		except:
			pass

	def setquota(mailbox, quota):
		try:
			listener.setuid(0)
			p = os.popen('/usr/sbin/univention-cyrus-set-quota-shared %s %s' % ( mailbox, quota ) )
			p.close()
			listener.unsetuid()
		except:
			pass

	# Gets needed cyrus vars for a certain policy
	def getpolicy(policy):
		if policy == 'read':
			policy = 'lrs'
		elif policy == 'write':
			policy = 'lrswipcd'
		elif policy == 'all':
			policy = 'lrswipcda'
		elif policy == 'post':
			policy = 'lrps'
		elif policy == 'append':
			policy = 'lrsip'
		# No change then
		elif policy == 'none':
			pass
		else:
			policy = -1

		return policy

	def fix_anyone_acl( new, email, policy ):
		if email == 'anyone' and new.has_key('mailPrimaryAddress') and new['mailPrimaryAddress'][0]:
			for flag in 'p':
				if not flag in policy:
					policy += flag
		return policy

	# split acl entry into mail adress/group name and access right
	def split_acl_entry(entry):
		last_space = entry.rfind(" ")
		return (entry[:last_space], entry[last_space+1:])

	# Create a new shared folder
	if (new and not old) or (not old.has_key('univentionMailHomeServer')) or (new.has_key('univentionMailHomeServer') and old.has_key('univentionMailHomeServer') and new['univentionMailHomeServer'] != old['univentionMailHomeServer']\
									 and new['univentionMailHomeServer'][0].lower() in [hostname, '%s.%s' % (hostname,domainname)]):

		if new.has_key('cn') and new['cn'][0]:

			try:
				listener.setuid(0)
				name = '"%s"' % new['cn'][0]

				if not old_dn:
					p = os.popen( '/usr/sbin/univention-cyrus-mkdir-shared  %s' % name )
					p.close()
				else:
					p = os.popen( '/usr/sbin/univention-cyrus-rename-mailbox %s %s' % (old_dn, name) )
					p.close()

				anyone_acl_set = False

				if new.has_key('univentionMailACL'):
					for entry in new['univentionMailACL']:
						(email, policy) = split_acl_entry(entry)

						# Set our new policy
						policy = getpolicy(policy)

						# add permissions "lrps" for user anyone if missing for mail delivery to shared folders
						policy = fix_anyone_acl(new, email, policy)

						if policy < 0:
							univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'cyrus-shared-folder: Wrong policy entry "%s" for email %s' % (policy, email))
							continue
						else:
							if email == 'anyone':
								anyone_acl_set = True
							setacl(name, email, policy)

				# set at least "anyone lrps" permissions for mail delivery to shared folders
				if not anyone_acl_set and new.has_key('mailPrimaryAddress') and new['mailPrimaryAddress'][0]:
					email = 'anyone'
					policy = ''
					policy = fix_anyone_acl( new, email, policy )
					setacl(name, email, policy)

				if new.has_key('cyrus-userquota') and new['cyrus-userquota'][0]:
					setquota(name, new['cyrus-userquota'][0])

				listener.unsetuid()

			except:
				pass

	# Delete existing shared folder
	if (old and not new) or (not new.has_key('univentionMailHomeServer')) or (not new['univentionMailHomeServer'][0].lower() in [hostname, '%s.%s' % (hostname,domainname)]):

		try:
			listener.setuid(0)
			name = '"%s"' % old['cn'][0]
			p = os.popen( '/usr/sbin/univention-cyrus-delete-folder %s' % name )
			p.close()

			listener.unsetuid()
		except:
			pass

	# Now comes the long complex part
	# Different possibilities
	# 1. The shared folder name changed
	# 2. the quota changed
	# 3. the deleteflag changed
	# 4. readers were added
	# 5. readers were removed
	# 6. reader permissions were changed
	if old and new:
		name = '"%s"' % new['cn'][0]

		if old.has_key('cyrus-userquota') and old['cyrus-userquota'][0] and not new.has_key('cyrus-userquota'):
			setquota(name, "none")

		if new.has_key('cyrus-userquota') and new['cyrus-userquota'][0]:
			setquota(name, new['cyrus-userquota'][0])

		if old.has_key('univentionMailACL') and old['univentionMailACL'] and not new.has_key('univentionMailACL'):
			for line in old['univentionMailACL']:
				(email, policy) = split_acl_entry(line)
				setacl(name, email, 'none')

		# convert new acls to dict
		anyone_acl_set = False
		curacl={}
		if new.has_key('univentionMailACL'):
			for entry in new['univentionMailACL']:
				(email, policy) = split_acl_entry(entry)
				policy = getpolicy(policy)
				policy = fix_anyone_acl(new, email, policy)
				curacl[email]=policy

		if old.has_key('univentionMailACL'):
			for entry in old['univentionMailACL']:
				(email, policy) = split_acl_entry(entry)
				if not curacl.has_key(email):
					setacl(name, email, 'none')

		for key in curacl.keys():
			setacl(name, key, curacl[key])
