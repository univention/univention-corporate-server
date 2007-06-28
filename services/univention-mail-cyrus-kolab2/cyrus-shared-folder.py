# -*- coding: utf-8 -*-
#
# Univention Mail Cyrus Kolab2
#  listener module: manages shared folders
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
import os, univention.debug, cPickle

hostname=listener.baseConfig['hostname']
domainname=listener.baseConfig['domainname']
ip=listener.baseConfig['interfaces/eth0/address']

name='cyrus-shared-folder'
description='Create shared folders'
filter='(&(objectClass=kolabSharedFolder)(|(kolabHomeServer=%s)(kolabHomeServer=%s.%s)))' % (ip, hostname, domainname)

directory='/var/cache/univention-mail-cyrus-kolab2/'

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

	# is this a outlook compatible folder?
	if ( new and new[ 'univentionKolabUserNamespace' ][ 0 ] == 'TRUE' ) or \
			( old and old[ 'univentionKolabUserNamespace' ][ 0 ] == 'TRUE' ):
		outlook = '-o'
	else:
		outlook = ''

	# Done as function because it is called quite often
	def setacl(mailbox, email, policy):
		try:
			listener.setuid(0)
			p = os.popen( '/usr/sbin/univention-cyrus-set-acl %s %s \'%s\' %s' % ( outlook, mailbox, email, policy ) )
			p.close()
			listener.unsetuid()
		except:
			pass

	def setquota(mailbox, quota):
		try:
			listener.setuid(0)
			p = os.popen('/usr/sbin/univention-cyrus-set-quota-shared %s %s %s' % ( outlook, mailbox, quota ) )
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

	# split acl entry into mail adress/group name and access right
	def split_acl_entry(entry):
		last_space = entry.rfind(" ")
		return (entry[:last_space], entry[last_space+1:])

	# Create a new shared folder
	if (new and not old) or (not old.has_key('kolabHomeServer')) or (new.has_key('kolabHomeServer') and old.has_key('kolabHomeServer') and new['kolabHomeServer'] != old['kolabHomeServer']\
									 and new['kolabHomeServer'][0].lower() in [hostname, '%s.%s' % (hostname,domainname)]):

		if new.has_key('cn') and new['cn'][0]:

			try:
				listener.setuid(0)
				name = '"%s"' % new['cn'][0]

				if not old_dn:
					p = os.popen( '/usr/sbin/univention-cyrus-mkdir-shared %s %s' % (outlook, name) )
					p.close()
				else:
					p = os.popen( '/usr/sbin/univention-cyrus-rename-mailbox %s %s %s' % (outlook, old_dn, name) )
					p.close()

				if new.has_key('acl'):
					for entry in new['acl']:
						(email, policy) = split_acl_entry(entry)

						# Set our new policy
						policy = getpolicy(policy)

						if policy < 0:
							univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'cyrus-shared-folder: Wrong policy entry "%s" for email %s' % (policy, email))
							continue
						else:
							setacl(name, email, policy)
				if new.has_key('cyrus-userquota') and new['cyrus-userquota'][0]:
					setquota(name, new['cyrus-userquota'][0])

				listener.unsetuid()

			except:
				pass

	# Delete existing shared folder
	if (old and not new) or (not new.has_key('kolabHomeServer')) or (not new['kolabHomeServer'][0].lower() in [hostname, '%s.%s' % (hostname,domainname)]):

		try:
			listener.setuid(0)
			name = '"%s"' % old['cn'][0]
			p = os.popen( '/usr/sbin/univention-cyrus-delete-folder %s %s' % (outlook, name) )
			p.close()

			listener.unsetuid()
		except:
			pass

	# Now comes the long complex part
	# Different possibilities
	# 1. The shared folder name changed
	# 2. the quota changed
	# 3. the kolabdeleteflag changed
	# 4. readers were added
	# 5. readers were removed
	# 6. reader permissions were changed
	if old and new:
		name = '"%s"' % new['cn'][0]
		if old.has_key('cyrus-userquota') and old['cyrus-userquota'][0] and not new.has_key('cyrus-userquota'):
			setquota(name, "none")

		if new.has_key('cyrus-userquota') and new['cyrus-userquota'][0]:
			setquota(name, new['cyrus-userquota'][0])

		if old.has_key('acl') and old['acl'] and not new.has_key('acl'):
			for line in old['acl']:
				(email, policy) = split_acl_entry(line)
				setacl(name, email, 'none')

		#convert new acls to dict
		curacl={}
		if new.has_key('acl'):
			for entry in new['acl']:
				(email, policy) = split_acl_entry(entry)
				curacl[email]=policy

		if old.has_key('acl'):
			for entry in old['acl']:
				(email, policy) = split_acl_entry(entry)
				if not curacl.has_key(email):
					setacl(name, email, 'none')

		for key in curacl.keys():
			setacl(name, key, curacl[key])
