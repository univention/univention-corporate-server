# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for mail imap folders
#
# Copyright (C) 2004-2009 Univention GmbH
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

import sys, string, sre
import univention.admin.filter
import univention.admin.handlers
import univention.admin.allocators
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.mail')
_=translation.translate

module='mail/folder'
operations=['add','edit','remove','search'] # removed 'move' as a workaround for bug #11664
#operations=['add','edit','remove','search','move']
usewizard=1


childs=0
short_description=_('Mail: IMAP folder')
long_description=''

module_search_filter=univention.admin.filter.conjunction('&', [
	univention.admin.filter.expression('objectClass', 'kolabSharedFolder'),
	])

property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.mail_folder_name,
			multivalue=0,
			required=1,
			may_change=0,
			identifies=1
		),
	'mailDomain': univention.admin.property(
			short_description=_('Mail domain'),
			long_description='',
			syntax=univention.admin.syntax.mailDomain,
			multivalue=0,
			required=1,
			may_change=0,
			identifies=1
		),
	'sharedFolderUserACL': univention.admin.property(
			short_description=_('User ACL'),
			long_description='',
			syntax=univention.admin.syntax.sharedFolderUserACL,
			multivalue=1,
			required=0,
			may_change=1,
			identifies=0,
		),
	'sharedFolderGroupACL': univention.admin.property(
			short_description=_('Group ACL'),
			long_description='',
			syntax=univention.admin.syntax.sharedFolderGroupACL,
			multivalue=1,
			required=0,
			may_change=1,
			identifies=0,
		),
	'cyrus-userquota': univention.admin.property(
			short_description=_('Quota in MB'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			required=0,
			may_change=1,
			identifies=0,
		),
	'kolabHomeServer': univention.admin.property(
			short_description=_('Kolab home server'),
			long_description='',
			syntax=univention.admin.syntax.kolabHomeServer,
			multivalue=0,
			required=1,
			may_change=1,
			identifies=0,
		),
	'userNamespace': univention.admin.property(
			short_description=_( 'Should be visible for Outlook' ),
			long_description=_( "Outlook does not display folders outside of the 'user' namespace." ),
			syntax=univention.admin.syntax.TrueFalseUp,
			multivalue=0,
			required=0,
			may_change=0,
			identifies=0,
			default=''
		),
	'mailPrimaryAddress': univention.admin.property(
			short_description=_('E-Mail address'),
			long_description='',
			syntax=univention.admin.syntax.emailAddress,
			multivalue=0,
			required=0,
			dontsearch=0,
			may_change=1,
			identifies=0,
		),
	'folderType': univention.admin.property(
			short_description=_('IMAP folder type'),
			long_description='',
			syntax=univention.admin.syntax.mail_folder_type,
			multivalue=0,
			required=0,
			dontsearch=0,
			may_change=1,
			identifies=0,
		),
}

layout=[
	univention.admin.tab(_('General'),_('Basic settings'),[
	[univention.admin.field("name"), univention.admin.field("mailDomain")],
	[univention.admin.field("kolabHomeServer"), univention.admin.field("cyrus-userquota")],
	[univention.admin.field("folderType"), univention.admin.field("mailPrimaryAddress")],
	[univention.admin.field("userNamespace"), ],
	] ),
	univention.admin.tab(_('Access Rights'),_('Access rights for shared folder'),[
	[univention.admin.field("sharedFolderUserACL")],
	[univention.admin.field("sharedFolderGroupACL")],
	] )
]

mapping=univention.admin.mapping.mapping()
mapping.register('cyrus-userquota', 'cyrus-userquota', None, univention.admin.mapping.ListToString)
mapping.register('kolabHomeServer', 'kolabHomeServer', None, univention.admin.mapping.ListToString)
mapping.register('userNamespace', 'univentionKolabUserNamespace', None, univention.admin.mapping.ListToString)
mapping.register('mailPrimaryAddress', 'mailPrimaryAddress', None, univention.admin.mapping.ListToString)
mapping.register('folderType', 'univentionKolabSharedFolderType', None, univention.admin.mapping.ListToString)

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, arg=None):
		global mapping
		global property_descriptions

		self.co=co
		self.lo=lo
		self.dn=dn
		self.position=position
		self._exists=0
		self.mapping=mapping
		self.descriptions=property_descriptions

		self.alloc=[]

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)


	def open(self):
		univention.admin.handlers.simpleLdap.open(self)
		if self.dn:
			cn=self.oldattr.get('cn',[])
			if cn:
				# 'name' is not a ldap attribute and oldinfo['name'] is
				# always empty, that is way searching for 'name' causes trouble
				# we delete the 'name' key in oldinfo so that the "change test"
				# succeeds
				if self.oldinfo.has_key('name') and not self.oldinfo['name']:
					del self.oldinfo['name']
				self['name']=cn[0].split('@')[0]
				self['mailDomain']=cn[0].split('@')[1]

			# fetch values for ACLs
			acls=self.oldattr.get('acl',[])
			self['sharedFolderUserACL']=[]
			self['sharedFolderGroupACL']=[]
			if acls:
				_sre_user = univention.admin.syntax.sharedFolderUserACL._re
				_sre_group = univention.admin.syntax.sharedFolderGroupACL._re
				for acl in acls:
					if _sre_user.match(acl):
						self['sharedFolderUserACL'].append(acl)
					elif _sre_group.match(acl):
						self['sharedFolderGroupACL'].append(acl)
		self.save()


	def exists(self):
		return self._exists

	def _ldap_pre_create(self):
		self.dn='cn=%s@%s,%s' % (self.info['name'], self.info['mailDomain'], self.position.getDn())

	def _ldap_post_create(self):
		if self[ 'userNamespace' ] == 'TRUE':
			address = '%s@%s' % ( self[ 'name' ], self[ 'mailDomain' ] )
			univention.admin.allocators.release( self.lo, self.position, 'mailPrimaryAddress', value = address )
		if self[ 'mailPrimaryAddress' ]:
			univention.admin.allocators.release( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailPrimaryAddress' ] )

	def _ldap_addlist(self):
		ocs=[]
		al=[]

		# if the 'user' namespace should be used the folder name must be a unique mail address
		if self[ 'userNamespace' ] == 'TRUE':
			address = '%s@%s' % ( self[ 'name' ], self[ 'mailDomain' ] )
			try:
				self.alloc.append( ( 'mailPrimaryAddress', address ) )
				univention.admin.allocators.request( self.lo, self.position, 'mailPrimaryAddress', value = address )
			except:
				univention.admin.allocators.release( self.lo, self.position, 'mailPrimaryAddress', value = address )
				raise univention.admin.uexceptions.mailAddressUsed

		if self[ 'mailPrimaryAddress' ]:
			if self[ 'userNamespace' ] == 'TRUE':
				al.append(('univentionKolabSharedFolderDeliveryAddress', '%s+%s@%s' % ( self['name'].split('/',1)[0], self[ 'name' ], self[ 'mailDomain' ] ) ) )
			else:
				al.append(('univentionKolabSharedFolderDeliveryAddress', 'univentioninternalpostuser+shared/%s@%s' % ( self[ 'name' ], self[ 'mailDomain' ] ) ) )

			address = '%s@%s' % ( self[ 'name' ], self[ 'mailDomain' ] )
			if self[ 'userNamespace' ] != 'TRUE' or self[ 'mailPrimaryAddress' ] != address:
				try:
					self.alloc.append( ( 'mailPrimaryAddress', self[ 'mailPrimaryAddress' ] ) )
					univention.admin.allocators.request( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailPrimaryAddress' ] )
				except:
					univention.admin.allocators.release( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailPrimaryAddress' ] )
					raise univention.admin.uexceptions.mailAddressUsed

		ocs.append('kolabSharedFolder')
		ocs.append('univentionKolabSharedFolder')

		al.insert(0, ('objectClass', ocs))
		al.append(('cn', "%s@%s" % (self.info['name'], self.info['mailDomain'])))

		return al

	def _ldap_post_modify(self):
		if self[ 'userNamespace' ] == 'TRUE':
			address = '%s@%s' % ( self[ 'name' ], self[ 'mailDomain' ] )
			univention.admin.allocators.release( self.lo, self.position, 'mailPrimaryAddress', value = address )
		if self[ 'mailPrimaryAddress' ]:
			univention.admin.allocators.release( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailPrimaryAddress' ] )

	def _ldap_modlist(self):
		# we get a list of modifications to be done (called 'ml' down below)
		# this lists looks like this:
		# [('kolabHomeServer', [u'ugs-master.hosts.invalid'], u'ugs-master.hosts.invalid'), ('cyrus-userquota', u'100', u'101')]
		# we can modify those entries to conform to the LDAP schema

		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)

		if self.hasChanged( 'userNamespace' ) and self[ 'userNamespace' ] == 'TRUE':
			for i, j in self.alloc:
				if i == 'mailPrimaryAddress': break
			else:
				address = '%s@%s' % ( self[ 'name' ], self[ 'mailDomain' ] )

				try:
					univention.admin.allocators.request( self.lo, self.position, 'mailPrimaryAddress', value = address )
				except:
					univention.admin.allocators.release( self.lo, self.position, 'mailPrimaryAddress', value = address )
					raise univention.admin.uexceptions.mailAddressUsed

		if self.hasChanged( 'mailPrimaryAddress' ) and self[ 'mailPrimaryAddress' ]:
			for i, j in self.alloc:
				if i == 'mailPrimaryAddress': break
			else:
				if self[ 'userNamespace' ] == 'TRUE':
					ml.append( ( 'univentionKolabSharedFolderDeliveryAddress',
								 self.oldattr.get( 'univentionKolabSharedFolderDeliveryAddress', [] ),
								 [ '%s+%s@%s' % ( self['name'].split('/',1)[0], self[ 'name' ], self[ 'mailDomain' ] ) ] ) )
				else:
					ml.append( ( 'univentionKolabSharedFolderDeliveryAddress',
								 self.oldattr.get( 'univentionKolabSharedFolderDeliveryAddress', [] ),
								 [ 'univentioninternalpostuser+shared/%s@%s' % ( self[ 'name' ], self[ 'mailDomain' ] ) ] ) )

				address = '%s@%s' % ( self[ 'name' ], self[ 'mailDomain' ] )
				if self[ 'userNamespace' ] != 'TRUE' or self[ 'mailPrimaryAddress' ] != address:
					try:
						self.alloc.append( ( 'mailPrimaryAddress', self[ 'mailPrimaryAddress' ] ) )
						univention.admin.allocators.request( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailPrimaryAddress' ] )
					except:
						univention.admin.allocators.release( self.lo, self.position, 'mailPrimaryAddress', value = self[ 'mailPrimaryAddress' ] )
						raise univention.admin.uexceptions.mailAddressUsed

		if not self[ 'mailPrimaryAddress' ]:
			ml.append( ( 'univentionKolabSharedFolderDeliveryAddress', self.oldattr.get( 'univentionKolabSharedFolderDeliveryAddress', [] ), [] ) )

		rewrite_acl = False
		new_acls_tmp = []
		for attr in [ 'sharedFolderUserACL', 'sharedFolderGroupACL' ]:
			if self.hasChanged( attr ):
				rewrite_acl = True
				# re-use regular expressions from syntax definitions
				if attr=='sharedFolderUserACL':
					_sre = univention.admin.syntax.sharedFolderUserACL._re
				else:
					_sre = univention.admin.syntax.sharedFolderGroupACL._re
				for acl in self[ attr ]:
					if _sre.match( acl ):
						new_acls_tmp.append( acl )
			else:
				for acl in self[attr]:
					new_acls_tmp.append(acl)

		if rewrite_acl:
			for (a, b, c) in ml:
				if a in ['sharedFolderUserACL', 'sharedFolderGroupACL']:
					ml.remove((a, b, c))
			ml.append( ( 'acl', self.oldattr.get( 'acl', [] ), new_acls_tmp ) )

		return ml

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('cn', '*'),
		univention.admin.filter.expression('objectClass', 'kolabSharedFolder')
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn))
	return res

def identify(dn, attr, canonical=0):
	return 'kolabSharedFolder' in attr.get('objectClass', [])
