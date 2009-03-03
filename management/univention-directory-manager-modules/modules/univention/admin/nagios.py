# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  methods and defines for nagios attributes
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

import copy
import univention.admin
import univention.admin.localization
import univention.admin.syntax
import re

translation=univention.admin.localization.translation('univention.admin')
_=translation.translate



nagios_properties = {
	'nagiosContactEmail': univention.admin.property(
			short_description = _('Email addresses of Nagios contacts'),
			long_description = (''),
			syntax=univention.admin.syntax.emailAddress,
			multivalue=1,
			required=0,
			may_change=1,
			options=['nagios'],
			identifies=0
		),
	'nagiosParents': univention.admin.property(
			short_description = _('Parent hosts'),
			long_description = (''),
			syntax=univention.admin.syntax.nagiosHostsEnabledDn,
			multivalue=1,
			required=0,
			may_change=1,
			options=['nagios'],
			identifies=0
		),
	'nagiosServices': univention.admin.property(
			short_description = _('Assigned nagios services'),
			long_description = (''),
			syntax=univention.admin.syntax.nagiosServiceDn,
			multivalue=1,
			required=0,
			may_change=1,
			options=['nagios'],
			identifies=0
		)
}


nagios_tab_A = univention.admin.tab( _( 'Nagios services' ), _( 'Nagios Service Settings' ), [
		[ univention.admin.field( "nagiosServices" ) ],
	] )

nagios_tab_B = univention.admin.tab( _( 'Nagios notification' ), _( 'Nagios Notification Settings' ), [
		[ univention.admin.field( "nagiosContactEmail" ) ],
		[ univention.admin.field( "nagiosParents" ) ],
	] )


nagios_mapping = [
	[ 'nagiosContactEmail', 'univentionNagiosEmail', None, None ],
	]


nagios_options={
	'nagios': univention.admin.option(
			short_description=_('Nagios Support'),
			default=0,
			editable=1,
			objectClasses = ['univentionNagiosHostClass'],
		)
	}



def addPropertiesMappingOptionsAndLayout(new_property, new_mapping, new_options, new_layout):
	# add nagios properties
	for key, value in nagios_properties.items():
		new_property[ key ] = value

	# append tab with Nagios options
	new_layout.append( nagios_tab_A )
	new_layout.append( nagios_tab_B )

	# append nagios attribute mapping
	for (ucskey, ldapkey, mapto, mapfrom) in nagios_mapping:
		new_mapping.register(ucskey, ldapkey, mapto, mapfrom)

	for key, value in nagios_options.items():
		new_options[key] = value



class Support( object ):
	def __init__( self ):
		self.nagiosRemoveFromServices = False

		if self.oldattr.has_key('objectClass'):
			ocs = set(self.oldattr['objectClass'])
			for opt in [ 'nagios' ]:
				if nagios_options[opt].matches(ocs):
					self.options.append(opt)

		if 'nagios' in self.options:
			self.old_nagios_option = True
		else:
			self.old_nagios_option = False



	def nagiosGetAssignedServices(self):
		if self.oldattr.has_key('aRecord') and self.oldattr['aRecord']:
			res=self.lo.search('(&(objectClass=dNSZone)(aRecord=%s)(zoneName=*)(relativeDomainName=*))' % self.oldattr['aRecord'][0])
			if not res:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'nagios.py: NGAS: couldn''t find fqdn of %s' % self.dn)
			else:
				# found my own fqdn
				fqdn = res[0][1]['relativeDomainName'][0]+'.'+res[0][1]['zoneName'][0]

				searchResult=self.lo.search( filter = '(&(objectClass=univentionNagiosServiceClass)(univentionNagiosHostname=%s))' % fqdn,
											 base = self.position.getDomain(), attr = [] )
				dnlist = []
				for (dn, attrs) in searchResult:
					dnlist.append(dn)
				return dnlist

		return []



	def nagiosGetParentHosts(self):
		# univentionNagiosParent
		_re = re.compile('^([^.]+)\.(.+?)$')

		parentlist = []
		parents = self.oldattr.get('univentionNagiosParent', [])
		for parent in parents:
			if parent and _re.match(parent) != None:
				(relDomainName, zoneName) = _re.match(parent).groups()

				res=self.lo.search('(&(objectClass=dNSZone)(zoneName=%s)(relativeDomainName=%s)(aRecord=*))' % (zoneName, relDomainName))
				if not res:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'nagios.py: NGPH: couldn''t find dNSZone of %s' % parent)
				else:
					# found dNSZone
					filter='(&(objectClass=univentionHost)'
					for aRecord in res[0][1]['aRecord']:
						filter += '(aRecord=%s)' % aRecord
					filter += '(cn=%s))' % relDomainName
					res=self.lo.search(filter)
					if res:
						parentlist.append( res[0][0] )

		return parentlist



	def nagios_open(self):
		if 'nagios' in self.options:
			self['nagiosServices'] = self.nagiosGetAssignedServices()
			self['nagiosParents'] = self.nagiosGetParentHosts()



	def nagiosSaveParentHostList(self, ml):
		if self.hasChanged('nagiosParents'):
			parentlist = []
			for parentdn in self.info['nagiosParents']:
				aRecords = self.lo.getAttr(parentdn, 'aRecord')
				if aRecords and aRecords[0]:
					res=self.lo.search('(&(objectClass=dNSZone)(aRecord=%s)(zoneName=*)(relativeDomainName=*))' % aRecords[0])
					if res:
						fqdn = res[0][1]['relativeDomainName'][0]+'.'+res[0][1]['zoneName'][0]
						parentlist.append(fqdn)

			ml.insert(0, ('univentionNagiosParent', self.oldattr.get('univentionNagiosParent', []), parentlist))



	def nagios_ldap_modlist(self, ml):
		if 'nagios' in self.options:
			if (not self.info.has_key('ip')) or (not self.info['ip']) or (len(self.info['ip'])==1 and self.info['ip'][0]==''):
				for i,j in self.alloc:
					univention.admin.allocators.release(self.lo, self.position, i, j)
				raise univention.admin.uexceptions.nagiosARecordRequired
			if (not self.info.has_key('dnsEntryZoneForward')) or (not self.info['dnsEntryZoneForward']) or (len(self.info['dnsEntryZoneForward'])==1 and self.info['dnsEntryZoneForward'][0]==''):
				for i,j in self.alloc:
					univention.admin.allocators.release(self.lo, self.position, i, j)
				raise univention.admin.uexceptions.nagiosDNSForwardZoneEntryRequired

		#	add nagios option
		if 'nagios' in self.options and not self.old_nagios_option:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'added nagios option')
			ocs=self.oldattr.get('objectClass', [])
			if not 'univentionNagiosHostClass' in ocs:
				ml.insert(0, ('objectClass', '', 'univentionNagiosHostClass'))
				ml.insert(0, ('univentionNagiosEnabled', '', '1'))

		#	remove nagios option
		if not 'nagios' in self.options and self.old_nagios_option:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'remove nagios option')
			ocs=self.oldattr.get('objectClass', [])
			if 'univentionNagiosHostClass' in ocs:
				ml.insert(0, ('objectClass', 'univentionNagiosHostClass', ''))

			for key in [ 'univentionNagiosParent', 'univentionNagiosEmail', 'univentionNagiosEnabled' ]:
				if self.oldattr.get(key, []):
					ml.insert(0, (key, self.oldattr.get(key, []), ''))

			# trigger deletion from services
			self.nagiosRemoveFromServices = True


		if 'nagios' in self.options:
			self.nagiosSaveParentHostList(ml)



	def nagios_ldap_pre_modify(self):
		pass

	def nagios_ldap_pre_create(self):
		pass

	def nagiosModifyServiceList(self):
		fqdn = ''

		arecord = None
		if self.oldattr.has_key('aRecord') and self.oldattr['aRecord']:
			arecord = self.oldattr['aRecord'][0]
		elif self.has_key('aRecord') and self['aRecord']:
			arecord = self['aRecord'][0]
		elif self.has_key('ip') and self['ip']:
			arecord = self['ip'][0]
		if not arecord:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'nagios.py: NMSL: couldn\'t get aRecord of %s' % self.dn)
			return

		res=self.lo.search('(&(objectClass=dNSZone)(aRecord=%s)(zoneName=*)(relativeDomainName=*))' % arecord)
		if not res:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'nagios.py: NMSL: couldn''t find fqdn of %s (aRecord=%s)' % (self.dn, arecord))
			for i,j in self.alloc:
				univention.admin.allocators.release(self.lo, self.position, i, j)
			raise univention.admin.uexceptions.noObject, _('cannot find fqdn of ') + str(self.dn) + ' (' + arecord + ')'
		else:
			# found my own fqdn
			fqdn = res[0][1]['relativeDomainName'][0]+'.'+res[0][1]['zoneName'][0]

		# remove host from services
		if self.old_nagios_option:
			for servicedn in self.oldinfo['nagiosServices']:
				if servicedn not in self.info['nagiosServices']:
					oldmembers = self.lo.getAttr(servicedn, 'univentionNagiosHostname')
					newmembers = filter(lambda x: x != fqdn, oldmembers)
					self.lo.modify(servicedn, [ ('univentionNagiosHostname', oldmembers, newmembers) ])

		if 'nagios' in self.options:
			# add host to new services
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'nagios.py: NMSL: nagios in options')
			if self.info.has_key('nagiosServices'):
				for servicedn in self.info['nagiosServices']:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'nagios.py: NMSL: servicedn %s' % servicedn)
					if len(servicedn):
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'nagios.py: NMSL: servicedn %s' % servicedn)
						if not self.old_nagios_option or servicedn not in self.oldinfo['nagiosServices']:
							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'nagios.py: NMSL: add')
							# option nagios was freshly enabled or service has been enabled just now
							oldmembers = self.lo.getAttr(servicedn, 'univentionNagiosHostname')
							newmembers = copy.deepcopy( oldmembers )
							newmembers.append(fqdn)
							self.lo.modify(servicedn, [ ('univentionNagiosHostname', oldmembers, newmembers) ])



	def nagiosRemoveHostFromServices(self):
		self.nagiosRemoveFromServices = False

		if self.oldattr.has_key('aRecord') and self.oldattr['aRecord']:
			res=self.lo.search('(&(objectClass=dNSZone)(aRecord=%s)(zoneName=*)(relativeDomainName=*))' % self.oldattr['aRecord'][0])
			if not res:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'nagios.py: NRHFS: couldn''t find fqdn of %s' % self.dn)
			else:
				# found my own fqdn
				fqdn = res[0][1]['relativeDomainName'][0]+'.'+res[0][1]['zoneName'][0]

				searchResult=self.lo.search( filter = '(&(objectClass=univentionNagiosServiceClass)(univentionNagiosHostname=%s))' % fqdn,
											 base = self.position.getDomain(), attr = [ 'univentionNagiosHostname' ] )

				for (dn, attrs) in searchResult:
					oldattrs = attrs['univentionNagiosHostname']
					newattrs = filter(lambda x: x != fqdn, attrs['univentionNagiosHostname'])
					self.lo.modify(dn, [ ('univentionNagiosHostname', oldattrs, newattrs) ])

	def nagiosRemoveHostFromParent(self):
		self.nagiosRemoveFromParent = False

		if self.oldattr.has_key('aRecord') and self.oldattr['aRecord']:
			res=self.lo.search('(&(objectClass=dNSZone)(aRecord=%s)(zoneName=*)(relativeDomainName=*))' % self.oldattr['aRecord'][0])
			if not res:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'nagios.py: NRHFP: couldn''t find fqdn of %s' % self.dn)
			else:
				# found my own fqdn
				fqdn = res[0][1]['relativeDomainName'][0]+'.'+res[0][1]['zoneName'][0]

				searchResult=self.lo.search( filter = '(&(objectClass=univentionNagiosHostClass)(univentionNagiosParent=%s))' % fqdn,
											 base = self.position.getDomain(), attr = [ 'univentionNagiosParent' ] )

				for (dn, attrs) in searchResult:
					oldattrs = attrs['univentionNagiosParent']
					newattrs = filter(lambda x: x != fqdn, attrs['univentionNagiosParent'])
					self.lo.modify(dn, [ ('univentionNagiosParent', oldattrs, newattrs) ])


	def nagios_ldap_post_modify(self):
		if self.nagiosRemoveFromServices:
			# nagios support has been disabled
			self.nagiosRemoveHostFromServices()
			self.nagiosRemoveHostFromParent()
		else:
			# modify service objects if needed
			if 'nagios' in self.options:
				self.nagiosModifyServiceList()



	def nagios_ldap_post_create(self):
		if 'nagios' in self.options:
			self.nagiosModifyServiceList()



	def nagios_ldap_post_remove(self):
		self.nagiosRemoveHostFromServices()
		self.nagiosRemoveHostFromParent()


	def nagios_cleanup(self):
		self.nagiosRemoveHostFromServices()
		self.nagiosRemoveHostFromParent()
