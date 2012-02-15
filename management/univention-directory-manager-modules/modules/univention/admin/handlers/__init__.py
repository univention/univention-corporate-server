# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  base class for the handlers
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

import copy
import types
import re
import string
import ldap
import ipaddr

import univention.debug

from univention.admin.layout import Tab
import univention.admin.filter
import univention.admin.uldap
import univention.admin.mapping
import univention.admin.modules
import univention.admin.uexceptions
import univention.admin.localization
from univention.admin import configRegistry

translation=univention.admin.localization.translation('univention/admin/handlers')
_=translation.translate

# global caching variable
if configRegistry.is_true('directory/manager/samba3/legacy', False):
	s4connector_present = False
elif configRegistry.is_false('directory/manager/samba3/legacy', False):
	s4connector_present = True
else:
	s4connector_present = None

s4connector_search = False

# FIXME: What is the use of the following line?
# __path__.append("users")

# manages properties
class base(object):
	def __init__(self, co, lo, position, dn='', superordinate = None ):
		self.co = co
		self.lo = lo
		self.dn = dn
		self.superordinate = superordinate

		self.set_defaults = 0
		if not self.dn: # this object is newly created and so we can use the default values
			self.set_defaults = 1

		if not hasattr(self, 'position'):
			self.position=position
		if not hasattr(self, 'info'):
			self.info={}
		if not hasattr(self, 'oldinfo'):
			self.oldinfo={}
		if not hasattr(self, 'policies'):
			self.policies=[]
		if not hasattr(self, 'oldpolicies'):
			self.oldpolicies=[]
		if not hasattr(self, 'policyObjects'):
			self.policyObjects={}
		self.__no_default=[]

		if not self.position:
			self.position=univention.admin.uldap.position(lo.base)
			if dn:
				self.position.setDn(dn)
		self._open = 0

	def open(self):
		self._open = 1

	def save(self):
		'''saves current state as old state'''

		self.oldinfo=copy.deepcopy(self.info)
		self.oldpolicies=copy.deepcopy(self.policies)

	def diff(self):
		'''returns differences between old and current state'''

		changes=[]
		for key, value in self.oldinfo.items():
			# FIXME: should be method of class property
			if self.descriptions[key].multivalue:
				null=[]
			else:
				null=None
			if not self.info.has_key(key):
				changes.append((key, value, null))
			elif self.info[key] != value:
				changes.append((key, value, self.info[key]))
		for key, value in self.info.items():
			# FIXME: should be method of class property
			if self.descriptions[key].multivalue:
				null=[]
			else:
				null=None
			if not self.oldinfo.has_key(key):
				changes.append((key, null, value))

		# verify that no key is listed that requires an disabled option (Bug #13964)
		if hasattr( self, 'options' ):
			for item in changes[ : ]:
				key, old, new = item
				# removing a key is ok
				if new in (None, []):
					continue
				if self.descriptions[ key ].options:
					for opt in self.descriptions[ key ].options:
						if opt in self.options:
							break
					else:
						univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, "simpleLdap.diff: key %s not valid (option not set)" % key )
						changes.remove( item )

		return changes

	def hasChanged(self, key):
		'''checks if the given attribute(s) was (were) changed; key can either be a
		string (scalar) or a list'''

		if type(key) == types.StringType or type(key) == types.UnicodeType:
			if (not self.oldinfo.get(key, '') or self.oldinfo[key] == ['']) \
				and (not self.info.get(key, '') or self.info[key] == ['']):
				return False
			else:
				return not univention.admin.mapping.mapCmp(self.mapping, key, self.oldinfo.get(key, ''), self.info.get(key, ''))
		elif type(key) == types.ListType:
			for i in key:
				if self.hasChanged(i):
					return True
		return False

	def ready(self):
		'''checks if all properties marked required are set'''

		for name, p in self.descriptions.items():

			# check if this property is present in the current option set,
			# skip otherwise
			if hasattr(self, 'options') and p.options:
				in_options=0
				for o in p.options:
					if o in self.options:
						in_options=1
						break
				if not in_options:
					continue

			if p.required and not self[name]:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "property %s is required but not set." % name)
				return 0
		return 1

	def has_key(self, key):
		if not self.descriptions.has_key(key):
			return 0
		p=self.descriptions[key]
		if hasattr(self, 'options') and p.options:
			for o in p.options:
				if o in self.options:
					return 1
			return 0
		return 1

	def __setitem__(self, key, value):
		# property does not exist
		options=0
		if not self.has_key(key):
			if self.descriptions[key].options:
				if hasattr(self, 'options'):
					options=1
					for o in self.descriptions[key].options:
						if o in self.options:
							raise univention.admin.uexceptions.noProperty, key
			if options:
				return
			raise univention.admin.uexceptions.noProperty, key
		# attribute may not be changed
		elif (not self.descriptions[key].may_change and self.oldinfo.has_key(key) and self.oldinfo[key] != value) or not self.descriptions[key].editable:
			raise univention.admin.uexceptions.valueMayNotChange, _('key=%s old=%s new=%s') % (key, self[key], value)
		# required attribute may not be removed
		elif self.descriptions[key].required and not value:
			raise univention.admin.uexceptions.valueRequired, _('The property %s is required') % self.descriptions[key].short_description
		# do nothing
		if self.info.get(key, None) == value:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'values are identical: %s:%s' % (key, value))
			return

		if self.info.get(key, None) == self.descriptions[key].default(self):
			self.__no_default.append(key)

		if self.descriptions[key].multivalue:

			# make sure value is list
			if type(value) == types.StringType or type(value) == types.UnicodeType:
				value=[value]
			elif not type(value) == types.ListType:
				raise univention.admin.uexceptions.valueInvalidSyntax, key

			self.info[key]=[]
			for v in value:
				if not v:
					continue
				err=""
				p=None
				try:
					s=self.descriptions[key].syntax
					p=s.parse(v)

				except univention.admin.uexceptions.valueError,emsg:
					err=emsg
				if not p:
					if not err:
						err=""
					try:
						raise univention.admin.uexceptions.valueInvalidSyntax, "%s: %s"%(key,err)
					except UnicodeEncodeError, e: # raise fails if err contains umlauts or other non-ASCII-characters
						raise univention.admin.uexceptions.valueInvalidSyntax( self.descriptions[key].short_description )
				self.info[key].append(p)

		elif not value and self.info.has_key(key):
			del self.info[key]

		elif value:
			err=""
			p=None
			try:
				s=self.descriptions[key].syntax
				p=s.parse(value)
			except univention.admin.uexceptions.valueError,e:
				err=e
			if not p:
				if not err:
					err=""
				try:
					raise univention.admin.uexceptions.valueInvalidSyntax, "%s: %s"%(self.descriptions[key].short_description,err)
				except UnicodeEncodeError, e: # raise fails if err contains umlauts or other non-ASCII-characters
					raise univention.admin.uexceptions.valueInvalidSyntax, "%s"%self.descriptions[key].short_description
			self.info[key]=p

	def __getitem__(self, key):
		_d=univention.debug.function('admin.handlers.base.__getitem__ key = %s'%key)
		if not key:
			return None

		if key in self.info:
			if self.descriptions[key].multivalue and not type(self.info[key]) == types.ListType:
				# why isn't this correct in the first place?
				self.info[ key ] = [ self.info[ key ] ]
			return self.info[ key ]
		elif not key in self.__no_default and self.descriptions[key].editable:
			self.info[key]=self.descriptions[key].default(self)
			return self.info[key]
		elif self.descriptions[key].multivalue:
			return []
		else:
			return None

	def get( self, key, default = None ):
		if key in self.info:
			return self.info[ key ]
		return default

	def __contains__( self, key ):
		return key in self.descriptions

	def keys(self):
		return self.descriptions.keys()

	def items(self):

		# this returns emtpy strings resp. empty lists for attributes not set
		r=[]
		for key in self.keys():
			if not self.has_key(key): # may happen if key is disabled by option, i.e. if share is no samba-share or user is no samba-user
				if self.descriptions.has_key(key) and hasattr(self.descriptions[key],'options'):
					option_set=0
					for o in self.descriptions[key].options:
						if o in self.options:
							option_set=1
					if option_set:
						raise univention.admin.uexceptions.noProperty, key # because key is enabled but not in self
					else:
						pass # because key is disabled by option
				else: raise univention.admin.uexceptions.noProperty, key # because given key is either in self nor in options
			else: # key is OK
				r.append((key, self[key]))
		return r

	def create(self):
		'''create object'''

		if self.exists():
			raise univention.admin.uexceptions.objectExists, self.dn
		if hasattr(self,"_ldap_pre_ready"):
			self._ldap_pre_ready()

		if not self.ready():
			raise univention.admin.uexceptions.insufficientInformation

		return self._create()

	def modify(self, modify_childs=1,ignore_license=0):
		'''modify object'''

		if not self.exists():
			raise univention.admin.uexceptions.noObject
		if hasattr(self,"_ldap_pre_ready"):
			self._ldap_pre_ready()

		if not self.ready():
			raise univention.admin.uexceptions.insufficientInformation
		return self._modify(modify_childs,ignore_license=ignore_license)

	def move(self, newdn, ignore_license=0):
		'''move object'''
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'move: called for %s'%self.dn)

		if not (univention.admin.modules.supports(self.module,'move')
				or univention.admin.modules.supports(self.module,'subtree_move')): # this should have been checked before, but I want to be sure...
			raise univention.admin.uexceptions.invalidOperation

		if not self.exists():
			raise univention.admin.uexceptions.noObject

		if self.dn.lower() == newdn.lower():
			raise univention.admin.uexceptions.ldapError, _('Moving not possible: old and new DN are identical.')
		if self.dn.lower() == newdn.lower()[-len(self.dn):]:
			raise univention.admin.uexceptions.ldapError, _("Moving into one's own sub container not allowed.")

		goaldn = newdn[newdn.find(',')+1:]
		goalmodule = univention.admin.modules.identifyOne(goaldn, self.lo.get(goaldn))
		goalmodule = univention.admin.modules.get(goalmodule)
		if not goalmodule or not hasattr(goalmodule,'childs') or not goalmodule.childs == 1:
			raise univention.admin.uexceptions.invalidOperation, _("Destination object can't have sub objects.")

		if univention.admin.modules.supports(self.module,'subtree_move'):
			# check if is subtree:
			subelements = self.lo.search(base=self.dn, scope='one', attr=[])
			if subelements:
				olddn = self.dn
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'move: found subelements, do subtree move')
				# create copy of myself
				module = univention.admin.modules.get(self.module)
				position = univention.admin.uldap.position(self.lo.base)
				position.setDn(newdn[newdn.find(',')+1:])
				copyobject = module.object(None, self.lo, position)
				copyobject.open()
				for key in self.keys():
					copyobject[key]=self[key]
				copyobject.policies=self.policies
				copyobject.create()
				moved=[]
				try:
					for subolddn, suboldattrs in subelements:
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'move: subelement %s' % subolddn)
						subnewdn = subolddn.replace(self.dn,newdn)
						submodule = univention.admin.modules.identifyOne(subolddn, suboldattrs)
						submodule = univention.admin.modules.get(submodule)
						subobject = univention.admin.objects.get(submodule, None, self.lo, position='', dn=subolddn)
						if not subobject or not (univention.admin.modules.supports(submodule,'move') or
												 univention.admin.modules.supports(submodule,'subtree_move')):
							raise univention.admin.uexceptions.invalidOperation, _('Unable to move object %s (%s) in subtree, trying to revert changes.' ) % (subolddn[:subolddn.find(',')],univention.admin.modules.identifyOne(subolddn, suboldattrs))
						subobject.open()
						subobject.move(subnewdn)
						moved.append((subolddn,subnewdn))
					self.remove()
				except:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'move: subtree move failed, trying to move back.')
					position=univention.admin.uldap.position(self.lo.base)
					position.setDn(newdn[olddn.find(',')+1:])
					for subolddn, subnewdn in moved:
						submodule = univention.admin.modules.identifyOne(subnewdn, self.lo.get(subnewdn))
						submodule = univention.admin.modules.get(submodule)
						subobject = univention.admin.objects.get(submodule, None, self.lo, position='', dn=subnewdn)
						subobject.open()
						subobject.move(subolddn)
					copyobject.remove()
					raise
			else:
				# normal move, fails on subtrees
				return self._move(newdn, ignore_license=ignore_license)

		else:
			return self._move(newdn, ignore_license=ignore_license)

	def move_subelements(self, olddn, newdn, subelements, ignore_license = False):
		if subelements:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'move: found subelements, do subtree move')
			moved = []
			try:
				for subolddn, suboldattrs in subelements:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'move: subelement %s' % subolddn)
					subnewdn = subolddn.replace(olddn, newdn)
					submodule = univention.admin.modules.identifyOne(subolddn, suboldattrs)
					submodule = univention.admin.modules.get(submodule)
					subobject = univention.admin.objects.get(submodule, None, self.lo, position='', dn=subolddn)
					if not subobject or not (univention.admin.modules.supports(submodule, 'move') or
								 univention.admin.modules.supports(submodule, 'subtree_move')):
						raise univention.admin.uexceptions.invalidOperation, _('Unable to move object %s (%s) in subtree, trying to revert changes.') % (subolddn[:subolddn.find(',')], univention.admin.modules.identifyOne(subolddn, suboldattrs))
					subobject.open()
					subobject._move(subnewdn)
					moved.append((subolddn,subnewdn))
					return moved
			except:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'move: subtree move failed, try to move back')
				for subolddn, subnewdn in moved:
					submodule = univention.admin.modules.identifyOne(subnewdn, self.lo.get(subnewdn))
					submodule = univention.admin.modules.get(submodule)
					subobject = univention.admin.objects.get(submodule, None, self.lo, position='', dn=subnewdn)
					subobject.open()
					subobject.move(subolddn)
				raise

	def remove(self, remove_childs=0):
		'''remove object'''

		# FIXME: the following check doesn't work anymore if we set _exists in open()
		# as an object naturally doesn't need to open to be removed; for now, let's
		# see what happens without it
		#if not self.exists():
		#	raise univention.admin.uexceptions.noObject

		return self._remove(remove_childs)


class simpleLdap(base):

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global s4connector_present
		global s4connector_search

		self._exists = False
		self.exceptions=[]
		base.__init__(self, co, lo, position, dn, superordinate )
		base.open(self)

		if not s4connector_search:
			s4connector_search = True
			# s4connector_present is a global caching variable than can be
			# None ==> ldap has not been checked for servers with service "S4 Connector"
			# True ==> at least one server with IP address (aRecord) is present
			# False ==> no server is present
			if s4connector_present == None:
				searchResult = self.lo.search('(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(univentionService=S4 Connector))', attr = ['aRecord'])
				s4connector_present = True
				if not [ ddn for (ddn, attr) in searchResult if attr.has_key('aRecord') ]:
					s4connector_present = False
		self.s4connector_present = s4connector_present

		if attributes:
			self.oldattr = attributes
		else:
			self.oldattr=self.lo.get(self.dn)
		if self.oldattr:
			self._exists = True
			oldinfo=univention.admin.mapping.mapDict(self.mapping, self.oldattr)
			oldinfo = self._post_unmap( oldinfo, self.oldattr )
			if 'univentionPolicyReference' in self.oldattr.get('objectClass', []):
				self.policies=self.oldattr.get('univentionPolicyReference', [])
		else:
			oldinfo={}
		self.info=oldinfo

		self.save()

	def exists( self ):
		return self._exists

	def call_udm_property_hook(self, hookname, module, changes = None):
		m = univention.admin.modules.get( module.module )
		if hasattr(m, 'extended_udm_attributes'):
			for prop in m.extended_udm_attributes:
				if prop.hook != None:
					func = getattr(prop.hook, hookname, None)
					if changes == None:
						func(module)
					else:
						changes = func(module, changes)
		return changes

	def open(self):
		self.exceptions=[]
		self.call_udm_property_hook('hook_open', self)
		self.save()

	def _remove_option( self, name ):
		if name in self.options:
			self.options.remove( name )

	def _define_options( self, module_options ):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modules/__init__.py _define_options: reset to default options')
		for name, opt in module_options.items():
			if not opt.disabled and opt.default:
				self.options.append( name )

	def description(self):
		if self.dn:
			rdn = self.lo.explodeDn(self.dn)[0]
			return rdn[rdn.find('=')+1:]
		else:
			return 'none'

	def _post_unmap( self, info, values ):
		"""This method can be overwritten to define special un-map
		methods that can not be done with the default mapping API"""
		return info

	def _post_map( self, modlist, diff ):
		"""This method can be overwritten to define special map methods
		that can not be done with the default mapping API"""
		return modlist

	def _ldap_modlist(self):
		self.exceptions=[]

		# remove all properties which do not belong to chosen options

		chosen_options = None
		descriptions = None

		try:
			# these might not be set by an inheriting module
			chosen_options = self.options
			descriptions = self.descriptions
		except:
			pass

		if chosen_options and descriptions:
			for desc in descriptions:
				propoptions = descriptions[desc].options

				if (propoptions==[]):
					# property applies to all options
					continue

				shortcut = False

				for i in propoptions:
					if i in chosen_options:
						# this property applies to one of the chosen options,
						# jump to next option
						shortcut = True
						continue
				if shortcut:
					continue

				# if we've come here, we found a property that does not apply
				# to the chosen options and may cause harm when writing to
				# the LDAP.
				# see Bug #8386, if we remove this value from the mapping table,
				# we can't modify this value during the session.
				#self.mapping.unregister(desc)

		diff_ml = self.diff()
		ml = univention.admin.mapping.mapDiff( self.mapping, diff_ml )
		ml = self._post_map( ml, diff_ml )

		# policies
		if self.policies != self.oldpolicies:
			classes=self.oldattr.get('objectClass', [])
			if not classes or not 'univentionPolicyReference' in classes:
				ml.append(('objectClass', self.oldattr.get('objectClass', []), self.oldattr.get('objectClass', [])+['univentionPolicyReference']))
			ml.append(('univentionPolicyReference', self.oldpolicies, self.policies))


		return ml

	def _create(self):
		self.exceptions=[]
		if hasattr(self,"_ldap_pre_create"):
			self._ldap_pre_create()

		if hasattr(self,"_update_policies"):
			self._update_policies()

		self.call_udm_property_hook('hook_ldap_pre_create', self)

		# Make sure all default values are set...
		for name, p in self.descriptions.items():
			# check if this property is present in the current option set,
			# skip otherwise
			if hasattr(self, 'options') and self.options and p.options:
				has_option = 0
				for o in p.options:
					if o in self.options:
						if self.descriptions[name].default(self):
							has_option = 1
				if has_option:
					self[name]
			else: # items without options should be touched also
				if self.descriptions[name].default(self):
					self[name]


		al=self._ldap_addlist()
		al.extend(self._ldap_modlist())
		# custom attributes
		# FIXME: fails if same objectClass is used for more than one attribute
		# I'm not sure if it still fails (must be tested)
		m=univention.admin.modules.get(self.module)
		if hasattr(m, 'ldap_extra_objectclasses'):
			seen={}
			for oc, pname, syntax, ldapMapping, deleteValues, deleteObjectClass in m.ldap_extra_objectclasses:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'oc = %s, pname = %s'% (oc,pname))
				if self.info.has_key(pname) and self.info[pname]:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'pname: info[%s] = %s'% (pname,self.info[pname]))
					if syntax == 'boolean' and self.info[pname] == '0':
						pos=-1
						for i in range(0,len(al)):
							if al[i][0] == ldapMapping:
								pos=i
						if pos != -1:
							al.remove(al[pos])
						continue

					objectClasses=[]
					for i in al:
						if i[0] == 'objectClass':
							if i[-1]:
								for objectClass in range(0,len(i[-1])):
									objectClasses.append(i[-1][objectClass])
					if oc in objectClasses:
						continue
					if seen.get(oc):
						continue
					seen[oc]=1
					#objectClasses.append(oc)
					al.append(('objectClass', [oc]))

		# UDM PROPERTIES
		if hasattr(m, 'extended_udm_attributes'):
			seen={}
			for prop in m.extended_udm_attributes:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'simpleLdap._create: prop.objClass = %s, prop.name = %s'% (prop.objClass, prop.name))
				if self.info.get(prop.name):
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'simpleLdap._create: prop.name: info[%s] = %s'% (prop.name, self.info.get(prop.name)))

					# do not add object class and value if syntax is boolean and checkbox is disabled
					if prop.syntax == 'boolean' and self.info.get(prop.name) == '0':
						dellist = []
						for i in range(0,len(al)):
							if al[i][0] == prop.ldapMapping:
								dellist.append( al[i] )
						for item in dellist:
							al.remove(item)
						continue

					# in all other cases add object class
					if seen.get(prop.objClass):
						continue
					objectClasses=[]
					for i in al:
						if i[0] == 'objectClass' and i[1]:
							objectClasses.extend( i[1] )
					if prop.objClass in objectClasses:
						continue
					seen[prop.objClass]=1
					al.append(('objectClass', [prop.objClass]))

		al = self.call_udm_property_hook('hook_ldap_addlist', self, al)

		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "trying to add object at: %s" % self.dn)
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "dn: %s" % (self.dn))

		# ensure univentionObject is set
		al.append( ( 'objectClass', [ 'univentionObject', ] ) )
		al.append( ( 'univentionObjectType', [ self.module, ] ) )

		self.lo.add(self.dn, al)

		if hasattr(self,'_ldap_post_create'):
			# if anything goes wrong we need to remove the already created object, otherwise we run into 'already exists' errors
			try:
				self._ldap_post_create()
			except Exception, e:
				# ensure that there is no lock left
				import sys, traceback
				univention.debug.debug( univention.debug.ADMIN, univention.debug.ERROR, "Post-modify operation failed: %s" % '\n'.join( traceback.format_tb( sys.exc_info()[ 2 ] ) ) )
				self.cancel()
				self.remove()
				raise e

		self.call_udm_property_hook('hook_ldap_post_create', self)

		self.save()
		return self.dn

#+++# MODIFY #+++#
	def _modify(self, modify_childs=1, ignore_license=0):
		self.exceptions=[]

		if hasattr(self,"_ldap_pre_modify"):
			self._ldap_pre_modify()
		if hasattr(self,'_update_policies'):
			self._update_policies()

		self.call_udm_property_hook('hook_ldap_pre_modify', self)

		# Make sure all default values are set...
		for name, p in self.descriptions.items():
			# check if this property is present in the current option set,
			# skip otherwise
			if hasattr(self, 'options') and self.options and p.options:
				for o in p.options:
					if o in self.options:
						if self.descriptions[name].default(self):
							self[name]
							break

#+++# MODLIST #+++#
		ml=self._ldap_modlist()
		# custom attributes
		m=univention.admin.modules.get(self.module)
		if hasattr(m, 'ldap_extra_objectclasses'):
			seen={}
			for oc, pname, syntax, ldapMapping, deleteValues, deleteObjectClass in m.ldap_extra_objectclasses:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'simpleLdap._modify: oc = %s, pname = %s'% (oc,pname))
				if self.info.has_key(pname) and self.info[pname] and not (syntax == 'boolean' and self.info[pname] == '0'):
					if oc in self.oldattr.get('objectClass', []):
						continue
					if seen.get(oc):
						continue
					seen[oc]=1
					current_ocs=self.oldattr.get('objectClass')
					for i in ml:
						if i[0] == 'objectClass' and i[2]:
							if type(i[2]) == type(''):
								current_ocs = [ i[2] ]
							elif type(i[2]) == type([]):
								current_ocs = i[2]
							else:
								univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'ERROR in simpleLDAP._modify: i=%s'%i)
					ml.append(('objectClass',self.oldattr.get('objectClass'), current_ocs+[oc]))

				else:
					if syntax == 'boolean' and self.info.has_key(pname) and self.info[pname] == '0':
						dellist = []
						addlist = []
						for i in ml:
							if i[0] == ldapMapping:
								dellist.append(i)
								addlist.append((i[0],i[1],''))
						for i in dellist:
							ml.remove(i)
						ml.extend( addlist )


					else:
						if deleteObjectClass == '1' and not self.info.has_key(pname):
							# value is empty, should delete objectClass and Values
							if oc in self.oldattr.get('objectClass', []):
								current_ocs=self.oldattr.get('objectClass')[0:]
								for i in ml:
									if i[0] == 'objectClass' and i[2]:
										current_ocs=i[2]
								current_ocs.remove(oc)
								ml.append(('objectClass',self.oldattr.get('objectClass'), current_ocs))
								# delete value entry, may be part of ml if it changed
								found_entry = 0
								for i in ml:
									if i[0] == ldapMapping:
										i=(ldapMapping,i[1],0)
										found_entry=1
								if not found_entry:
									ml.append((ldapMapping,['not_important'],0))

		# UDM PROPERTIES
		if hasattr(m, 'extended_udm_attributes'):
			seen={}

			for prop in m.extended_udm_attributes:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'simpleLdap._modify: c_u_p: pname = "%s"  oc = "%s"'% (prop.name, prop.objClass))

				# if value is set then add object class if neccessary
				# exception is syntax==boolean ==> remove attribute and object class if value==0
				if self.info.get(prop.name) and not (prop.syntax == 'boolean' and self.info.get(prop.name) == '0'):

					if prop.objClass.lower() in map(lambda x:x.lower(), self.oldattr.get('objectClass', [])):
						continue
					if seen.get(prop.objClass):
						continue
					seen[prop.objClass] = 1
					current_ocs = self.oldattr.get('objectClass')
					for i in ml:
						if i[0] == 'objectClass' and i[2]:
							if type(i[2]) == type(''):
								current_ocs = [ i[2] ]
							elif type(i[2]) == type([]):
								current_ocs = i[2]
							else:
								univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'ERROR in simpleLDAP._modify: i=%s'%i)
					ml.append( ('objectClass', self.oldattr.get('objectClass'), current_ocs+[prop.objClass]) )

				else:

					if prop.syntax == 'boolean' and self.info.has_key(prop.name) and self.info[prop.name] == '0':
						# syntax is boolean and value == 0 ==> remove
						dellist = []
						addlist = []
						for i in ml:
							if i[0] == prop.ldapMapping:
								dellist.append(i)
								addlist.append((i[0],i[1],''))
						for i in dellist:
							ml.remove(i)
						ml.extend( addlist )

					else:
						# no value is set
						if prop.deleteObjClass == '1' and not self.info.has_key(prop.name):
							# value is empty, should delete objectClass and Values
							if prop.objClass in self.oldattr.get('objectClass', []):
								current_ocs = self.oldattr.get('objectClass')[0:]
								for i in ml:
									if i[0] == 'objectClass' and i[2]:
										current_ocs = i[2]
								current_ocs.remove( prop.objClass )
								ml.append( ('objectClass', self.oldattr.get('objectClass'), current_ocs) )
								# delete value entry, may be part of ml if it changed
								found_entry = 0
								for i in ml:
									if i[0] == prop.ldapMapping:
										i = (prop.ldapMapping, i[1], 0)
										found_entry = 1
								if not found_entry:
									ml.append( (prop.ldapMapping, ['not_important'], 0) )

		ml = self.call_udm_property_hook('hook_ldap_modlist', self, ml)

		#FIXME: timeout without exception if objectClass of Object is not exsistant !!
		self.lo.modify(self.dn, ml, ignore_license=ignore_license)

		if hasattr(self,'_ldap_post_modify'):
			self._ldap_post_modify()

		self.call_udm_property_hook('hook_ldap_post_modify', self)

		self.save()
		return self.dn

	def _move_in_subordinates(self, olddn):
		searchFilter='(&(objectclass=person)(secretary=%s))'% univention.admin.filter.escapeForLdapFilter(olddn)
		result=self.lo.search(base=self.lo.base, filter=searchFilter, attr=['dn'])
		for subordinate, attr in result:
			self.lo.modify(subordinate, [('secretary', olddn, self.dn)])

	def _move_in_groups(self, olddn):
		for group in self.oldinfo.get('groups', []) + [self.oldinfo.get('machineAccountGroup', '')]:
			if group != '':
				members=self.lo.getAttr(group, 'uniqueMember')
				newmembers=[]
				for member in members:
					if not member.lower() in (olddn.lower(), self.dn.lower(), ):
						newmembers.append(member)
				newmembers.append(self.dn)
				self.lo.modify(group, [('uniqueMember', members, newmembers)])

	def _move(self, newdn, modify_childs=1, ignore_license=0):
		if hasattr(self,'_ldap_pre_move'):
			self._ldap_pre_move(newdn)

		olddn = self.dn
		self.lo.rename(self.dn, newdn)
		self.dn = newdn

		try:
			self._move_in_groups(olddn) # can be done always, will do nothing if oldinfo has no attribute 'groups'
			self._move_in_subordinates(olddn)
			if hasattr(self,'_ldap_post_move'):
				self._ldap_post_move(olddn)
		except:
			# move back
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN,
								   'simpleLdap._move: self._ldap_post_move failed, move object back to %s'%olddn)
			self.lo.rename(self.dn, olddn)
			self.dn = olddn
			raise

	def _remove(self, remove_childs=0):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,'handlers/__init__._remove() called for %s' % self.dn)
		self.exceptions=[]
		if hasattr(self,"_ldap_pre_remove"):
			univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL,'_ldap_pre_remove() called')
			self._ldap_pre_remove()

		self.call_udm_property_hook('hook_ldap_pre_remove', self)

		if remove_childs:
			if not self.dn:
				raise univention.admin.uexceptions.noObject
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,'handlers/__init__._remove() childs of base dn %s' % self.dn)
			subelements = self.lo.search(base=self.dn, scope='one', attr=[])
			if subelements:
				try:
					for subolddn, suboldattrs in subelements:
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'remove: subelement %s' % subolddn)
						submodule = univention.admin.modules.identifyOne(subolddn, suboldattrs)
						submodule = univention.admin.modules.get(submodule)
						subobject = univention.admin.objects.get(submodule, None, self.lo, position='', dn=subolddn)
						subobject.remove(remove_childs)
				except:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'remove: could not remove subelements')

		self.lo.delete(self.dn)

		if hasattr(self,"_ldap_post_remove"):
			self._ldap_post_remove()

		self.call_udm_property_hook('hook_ldap_post_remove', self)

	def loadPolicyObject(self, policy_type, reset=0):
		pathlist=[]
		errors=0
		pathResult=None

		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "loadPolicyObject: policy_type: %s" % policy_type)
		policy_module=univention.admin.modules.get(policy_type)

		# overwrite property descriptions
		univention.admin.ucr_overwrite_properties( policy_module, self.lo )
		# re-build layout if there any overwrites defined
		univention.admin.ucr_overwrite_module_layout( policy_module )

		# retrieve path info from 'cn=directory,cn=univention,<current domain>' object
		try:
			pathResult = self.lo.get('cn=directory,cn=univention,'+self.position.getDomain())
			if not pathResult:
				pathResult = self.lo.get('cn=default containers,cn=univention,'+self.position.getDomain())
		except:
			errors=1
		infoattr="univentionPolicyObject"
		if pathResult.has_key(infoattr) and pathResult[infoattr]:
			for i in pathResult[infoattr]:
				try:
					self.lo.searchDn(base=i, scope='base')
					pathlist.append(i)
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "loadPolicyObject: added path %s" % i)
				except Exception, e:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "loadPolicyObject: invalid path setting: %s does not exist in LDAP" % i)
					continue  # looking for next policy container
				break # at least one item has been found; so we can stop here since only pathlist[0] is used

		if not pathlist or errors:
			policy_position=self.position
		else:
			policy_position=univention.admin.uldap.position(self.position.getBase())
			policy_path=pathlist[0]
			try:
				prefix=univention.admin.modules.policyPositionDnPrefix(policy_module)
				self.lo.searchDn(base="%s,%s" % (prefix, policy_path), scope='base')
				policy_position.setDn("%s,%s" % (prefix, policy_path))
			except:
				policy_position.setDn(policy_path)

		for dn in self.policies:
			if univention.admin.modules.recognize(policy_module, dn, self.lo.get(dn)) and self.policyObjects.get(policy_type, None) and self.policyObjects[policy_type].cloned == dn and not reset:
				return self.policyObjects[policy_type]

		for dn in self.policies:
			modules=univention.admin.modules.identify(dn, self.lo.get(dn))
			for module in modules:
				if univention.admin.modules.name(module) == policy_type:
					self.policyObjects[policy_type]=univention.admin.objects.get(module, None, self.lo, policy_position, dn=dn)
					self.policyObjects[policy_type].clone(self)
					self._init_ldap_search( self.policyObjects[ policy_type ] )

					return self.policyObjects[policy_type]
			if not modules:
				self.policies.remove(dn)

		if not self.policyObjects.get(policy_type, None) or reset:
			self.policyObjects[policy_type]=univention.admin.objects.get(policy_module, None, self.lo, policy_position)
			self.policyObjects[policy_type].copyIdentifier(self)
			self._init_ldap_search( self.policyObjects[ policy_type ] )
		else:
			pass

		return self.policyObjects[policy_type]

	def _init_ldap_search( self, policy ):
		properties = {}
		if hasattr( policy, 'property_descriptions' ):
			properties = policy.property_descriptions
		elif hasattr( policy, 'descriptions' ):
			properties = policy.descriptions
		for pname, prop in properties.items():
			if prop.syntax.name == 'LDAP_Search':
				prop.syntax._load( self.lo )
				if prop.syntax.viewonly:
					policy.mapping.unregister( pname )

	def _update_policies(self):
		_d=univention.debug.function('admin.handlers.simpleLdap._update_policies')
		for policy_type, policy_object in self.policyObjects.items():
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "simpleLdap._update_policies: processing policy of type: %s" % policy_type)
			if policy_object.changes:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "simpleLdap._update_policies: trying to create policy of type: %s" % policy_type)
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "simpleLdap._update_policies: policy_object.info=%s" % policy_object.info)
				policy_object.create()
				univention.admin.objects.replacePolicyReference(self, policy_type, policy_object.dn)

	def closePolicyObjects(self):
		self.policyObjects={}

	def savePolicyObjects(self):
		self._update_policies()
		self.closePolicyObjects()

	def cancel(self):
		# method stub which is implemented by subclasses (see Bug #21070)
		pass


class simpleComputer( simpleLdap ):
	MAC_REGEX = re.compile( '^([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}$' )

	def __init__( self, co, lo, position, dn = '', superordinate = None, attributes = [] ):
		simpleLdap.__init__( self, co, lo, position, dn, superordinate, attributes )

		self.ip = [ ]
		self.network_object = False
		self.old_network = 'None'
		self.__saved_dhcp_entry = None
		# read-only attribute containing the FQDN of the host
		self.descriptions[ 'fqdn' ] = univention.admin.property(
			short_description = 'FQDN',
			long_description = '',
			syntax=univention.admin.syntax.string,
			multivalue = False,
			options = [],
			required = False,
			may_change = False,
			identifies = 0
		)
		self[ 'dnsAlias' ] = [ ]	# defined here to avoid pseudo non-None value of [''] in modwizard search

	def getMachineSid(self, lo, position, uidNum):
		num = uidNum
		machineSid = ""
		while not machineSid or machineSid == 'None':
			try:
				machineSid = univention.admin.allocators.requestUserSid(lo, position, num)
			except univention.admin.uexceptions.noLock, e:
				num = str(int(num)+1)
		return machineSid

	# HELPER
	def __ip_from_ptr( self, zoneName, relativeDomainName ):
		if 'ip6' in zoneName:
			return self.__ip_from_ptr_ipv6(zoneName, relativeDomainName)
		else:
			return self.__ip_from_ptr_ipv4(zoneName, relativeDomainName)

	def __ip_from_ptr_ipv4( self, zoneName, relativeDomainName ):
		zoneName = zoneName.replace(  '.in-addr.arpa', '' ).split( '.' )
		zoneName.reverse( )
		relativeDomainName = relativeDomainName.split( '.' )
		relativeDomainName.reverse( )
		return '%s.%s' % ( string.join( zoneName, '.' ) , string.join( relativeDomainName, '.' ) )

	def __ip_from_ptr_ipv6( self, zoneName, relativeDomainName ):
		fullName = relativeDomainName + '.' + zoneName.replace('.ip6.arpa', '')
		fullName = fullName.split('.')
		fullName = [''.join(reversed(fullName[i:i+4])) for i in xrange(0, len(fullName), 4)]
		fullName.reverse( )
		return ':'.join(fullName)

	def __is_mac( self, mac ):
		return mac is not None and simpleComputer.MAC_REGEX.match( mac ) is not None

	def __is_ip( self, ip ):
		# return True if valid IPv4 (0.0.0.0 is allowed) or IPv6 address
		try:
			ipaddr.IPAddress(ip)
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'IP[%s]? -> Yes' % ip )
			return True
		except ValueError:
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'IP[%s]? -> No' % ip )
			return False

	def open( self ):
		simpleLdap.open( self )
		self.oldinfo['ip'] = []
		self.info['ip'] = []
		if 'aRecord' in self.oldattr:
			self.oldinfo['ip'].extend(self.oldattr['aRecord'])
			self.info['ip'].extend(   self.oldattr['aRecord'])
		if 'aAAARecord' in self.oldattr:
			self.oldinfo['ip'].extend(map(lambda x: ipaddr.IPv6Address(x).exploded, self.oldattr['aAAARecord']))
			self.info['ip'].extend(   map(lambda x: ipaddr.IPv6Address(x).exploded, self.oldattr['aAAARecord']))

		self.ip_alredy_requested = 0
		self.ip_freshly_set = False

		self.open_warning = None
		open_warnings = [ ]

		self.__multiip = False
		if len ( self[ 'mac' ] ) > 1 or len( self[ 'ip' ] ) > 1:
			self.__multiip = True

		self[ 'dnsEntryZoneForward' ] = [ ]
		self[ 'dnsEntryZoneReverse' ] = [ ]
		self[ 'dhcpEntryZone' ] = [ ]
		self[ 'groups' ] = [ ]
		self[ 'dnsEntryZoneAlias' ] = [ ]

		# search forward zone and insert into the object
		if self [ 'name' ]:
			tmppos = univention.admin.uldap.position( self.position.getDomain( ) )

			searchFilter = '(&(objectClass=dNSZone)(relativeDomainName=%s)(!(cNAMERecord=*)))' % self[ 'name' ]
			try:
				result = self.lo.search( base = tmppos.getBase( ),scope = 'domain', filter = searchFilter, attr = [ 'zoneName', 'aRecord', 'aAAARecord' ], unique = 0 )

				zoneNames = [ ]

				if result:
					for dn, attr in result:
						if attr.has_key( 'aRecord' ):
							zoneNames.append( ( attr[ 'zoneName' ][ 0 ], attr[ 'aRecord' ] ) )
						if attr.has_key( 'aAAARecord' ):
							zoneNames.append( ( attr[ 'zoneName' ][ 0 ], map(lambda x: ipaddr.IPv6Address(x).exploded, attr[ 'aAAARecord' ] )) )

				univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'zoneNames: %s' % zoneNames )

				if zoneNames:
					for zoneName in zoneNames:
						searchFilter = '(&(objectClass=dNSZone)(zoneName=%s)(relativeDomainName=@))'% zoneName[ 0 ]

						try:
							results = self.lo.searchDn( base = tmppos.getBase( ),scope = 'domain', filter = searchFilter, unique = 0 )
						except univention.admin.uexceptions.insufficientInformation, msg:
							raise univention.admin.uexceptions.insufficientInformation, msg

						univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'results: %s' % results )
						if results:
							for result in results:
								for ip in zoneName[ 1 ]:
									self[ 'dnsEntryZoneForward' ].append( [ result, ip ] )
							univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'dnsEntryZoneForward: %s' % str( self[ 'dnsEntryZoneForward' ] ) )

			except univention.admin.uexceptions.insufficientInformation, msg:
				self[ 'dnsEntryZoneForward' ] = [ ]
				raise univention.admin.uexceptions.insufficientInformation, msg

			if zoneNames:
				for zoneName in zoneNames:
					searchFilter = '(&(objectClass=dNSZone)(|(PTRRecord=%s)(PTRRecord=%s.%s.)))' % ( self[ 'name' ], self[ 'name' ], zoneName[ 0 ] )
					try:
						results = self.lo.search( base = tmppos.getBase( ),scope = 'domain', attr = [ 'relativeDomainName', 'zoneName' ], filter = searchFilter, unique = 0 )
						for dn, attr in results:
							poscomponents = univention.admin.uldap.explodeDn( dn,0 )
							poscomponents.pop( 0 )
							ip = self.__ip_from_ptr( attr[ 'zoneName' ][ 0 ], attr[ 'relativeDomainName' ][ 0 ] )
							entry = [ string.join( poscomponents, ',' ), ip ]
							if not entry in self[ 'dnsEntryZoneReverse' ]:
								self[ 'dnsEntryZoneReverse' ].append( entry )
					except univention.admin.uexceptions.insufficientInformation, msg:
						self[ 'dnsEntryZoneReverse' ] = [ ]
						raise univention.admin.uexceptions.insufficientInformation, msg
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'simpleComputer: dnsEntryZoneReverse: %s' % self[ 'dnsEntryZoneReverse' ] )

			if zoneNames:
				for zoneName in zoneNames:
					searchFilter = '(&(objectClass=dNSZone)(|(cNAMERecord=%s)(cNAMERecord=%s.%s.)))' % ( self[ 'name' ], self[ 'name' ], zoneName[ 0 ] )
					try:
						results = self.lo.search( base = tmppos.getBase( ),scope = 'domain', attr = [ 'relativeDomainName', 'cNAMERecord', 'zoneName' ], filter = searchFilter, unique = 0 )
						for dn, attr in results:
							dnsAlias = attr[ 'relativeDomainName' ][0]
							self[ 'dnsAlias' ].append(dnsAlias)
							poscomponents = univention.admin.uldap.explodeDn( dn,0 )
							poscomponents.pop( 0 )
							dnsAliasZoneContainer = string.join( poscomponents,',' )
							if attr[ 'cNAMERecord' ][0] == self[ 'name' ]:
								dnsForwardZone = attr[ 'zoneName' ][0]
							else:
								dnsForwardZone = zoneName[0]

							entry = [ dnsForwardZone, dnsAliasZoneContainer, dnsAlias ]
							if not entry in self[ 'dnsEntryZoneAlias' ]:
								self[ 'dnsEntryZoneAlias' ].append( entry )
					except univention.admin.uexceptions.insufficientInformation, msg:
						self[ 'dnsEntryZoneAlias' ] = [ ]
						raise univention.admin.uexceptions.insufficientInformation, msg
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'simpleComputer: dnsEntryZoneAlias: %s' % self[ 'dnsEntryZoneAlias' ] )

			if self[ 'mac' ]:
				for macAddress in self[ 'mac' ]:
					# mac address may be an empty string (Bug #21958)
					if not macAddress:
						continue

					univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'open: DHCP; we have a mac address: %s' % macAddress )
					ethernet = 'ethernet '+ macAddress
					searchFilter = '(&(dhcpHWAddress=%s)(objectClass=univentionDhcpHost))'% ( ethernet )
					univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'open: DHCP; we search for "%s"' % searchFilter )
					try:
						results = self.lo.search( base = tmppos.getBase( ),scope = 'domain', attr = [ 'univentionDhcpFixedAddress' ], filter = searchFilter, unique = 0 )
						univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'open: DHCP; the result: "%s"' % results )
						for dn, attr in results:
							poscomponents = univention.admin.uldap.explodeDn( dn,0 )
							poscomponents.pop( 0 )
							if attr.has_key( 'univentionDhcpFixedAddress' ):
								for ip in attr[ 'univentionDhcpFixedAddress' ]:
									entry = [ string.join( poscomponents,',' ), ip, macAddress ]
									if not entry in self[ 'dhcpEntryZone' ]:
										self[ 'dhcpEntryZone' ].append( entry )

							else:
								entry = [ string.join( poscomponents,',' ), macAddress ]
								if not entry in self[ 'dhcpEntryZone' ]:
									self[ 'dhcpEntryZone' ].append( entry )
						univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'open: DHCP; self[ dhcpEntryZone ] = "%s"' % self[ 'dhcpEntryZone' ] )

					except univention.admin.uexceptions.insufficientInformation, msg:
						raise univention.admin.uexceptions.insufficientInformation, msg

		if self.dn:
			if self.has_key( 'network' ):
				self.old_network = self[ 'network' ]

			# get groupmembership
			searchFilter='(&(objectclass=univentionGroup)(uniqueMember=%s))'% univention.admin.filter.escapeForLdapFilter(self.dn)
			result=self.lo.search(base=self.lo.base, filter=searchFilter, attr=['dn'])
			self['groups'] = [(x[0]) for x in result]

		if len( open_warnings ) > 0:
			self.open_warning = ''
			for warn in open_warnings:
				self.open_warning += '\n'+warn

		if 'name' in self.info and 'domain' in self.info:
			self.info[ 'fqdn' ] = '%s.%s' % ( self[ 'name' ], self[ 'domain' ] )

	def __modify_dhcp_object( self, position, name, ip, mac ):
		# identify the dhcp object with the mac address

		univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, '__modify_dhcp_object: position: "%s"; name: "%s"; mac: "%s"; ip: "%s"' % ( position, name, mac, ip ) )

		ethernet = 'ethernet %s' % mac

		tmppos = univention.admin.uldap.position( self.position.getDomain( ) )
		if not position:
			univention.debug.debug( univention.debug.ADMIN, univention.debug.WARN, 'could not access network object and given position is "None", using LDAP root as position for DHCP entry')
			position = tmppos.getBase( )
		results = self.lo.search( base = position, scope = 'domain', attr = [ 'univentionDhcpFixedAddress' ], filter = 'dhcpHWAddress=%s' % ethernet, unique = 0 )

		if not results:
			# if the dhcp object doesn't exists, then we create it
			# but we it is possible, that the hostname for the dhcp object alreay used, so we use the _uv$NUM extension

			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'the dhcp object with the mac addresss "%s" does not exists, we create one' % ethernet )

			results = self.lo.searchDn( base = position, scope = 'domain', filter = '(&(objectClass=univentionDhcpHost)(|(cn=%s)(cn=%s_uv*)))' % ( name, name ), unique = 0 )
			if not results:
				self.lo.add( 'cn = %s,%s'% ( name, position ), [
						( 'objectClass', [ 'top', 'univentionDhcpHost' ] ),\
						( 'cn', name ),\
						( 'univentionDhcpFixedAddress', [ ip ] ),\
						( 'dhcpHWAddress', [ ethernet ] ) ] )
				univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'we just added the object "%s,%s"' % ( name, position ) )
			else:
				univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'the host "%s" already has a dhcp object, so we searh for the next free uv name' % ( name ) )
				n = 0
				for result in results:
					val = result.split( ',' )[ 0 ].split( "_uv" )
					if len( val ) > 1:
						try:
							n = int( val[ 1 ] )
							n += 1
						except ValueError:
							if n == 0:
								n = 1

				self.lo.add( 'cn = %s_uv%d,%s'% ( name, n, position ), [
						( 'objectClass', [ 'top', 'univentionDhcpHost' ] ),\
						( 'cn', '%s_uv%d' % ( name,n ) ),\
						( 'univentionDhcpFixedAddress', [ ip ] ),\
						( 'dhcpHWAddress', [ ethernet ] ) ] )
				univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'we just added the object "%s_uv%d,%s"' % ( name, n, position ) )
		else:
			# if the object already exists, we append or remove the ip address
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'the dhcp object with the mac addresss "%s" exists, we change the ip' % ethernet )
			for dn, attr in results:
				if ip:
					if attr.has_key( 'univentionDhcpFixedAddress' ) and ip in attr[ 'univentionDhcpFixedAddress' ]:
						continue
					self.lo.modify( dn, [ ( 'univentionDhcpFixedAddress', '',  ip ) ] )
					univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'we added the ip "%s"' % ip )
				else:
					self.lo.modify( dn, [ ( 'univentionDhcpFixedAddress', ip,  '' ) ] )
					univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'we removed the ip "%s"' % ip )

	def __rename_dns_object( self, position = None, old_name = None, new_name = None ):
		for dns_line in self[ 'dnsEntryZoneForward' ]:
			# dns_line may be the empty string
			if not dns_line:
				continue
			dn, ip = self.__split_dns_line( dns_line )
			if ':' in ip: # IPv6
				results = self.lo.searchDn( base = dn, scope = 'domain', filter = '(&(relativeDomainName=%s)(aAAARecord=%s))' % (old_name, ip), unique = 0 )
			else:
				results = self.lo.searchDn( base = dn, scope = 'domain', filter = '(&(relativeDomainName=%s)(aRecord=%s))' % (old_name, ip), unique = 0 )
			for result in results:
				object = univention.admin.objects.get( univention.admin.modules.get( 'dns/host_record' ), self.co, self.lo, position = self.position, dn = result )
				object.open( )
				object[ 'name' ] = new_name
				object.modify( )
		for dns_line in self[ 'dnsEntryZoneReverse' ]:
			# dns_line may be the empty string
			if not dns_line:
				continue
			dn, ip = self.__split_dns_line( dns_line )
			results = self.lo.searchDn( base = dn, scope = 'domain', filter = '(|(pTRRecord=%s)(pTRRecord=%s.*))' % (old_name, old_name), unique = 0 )
			for result in results:
				object = univention.admin.objects.get( univention.admin.modules.get( 'dns/ptr_record' ), self.co, self.lo, position = self.position, dn = result )
				object.open( )
				object[ 'ptr_record' ] = object[ 'ptr_record' ].replace( old_name, new_name )
				object.modify( )
		for entry in self[ 'dnsEntryZoneAlias' ]:
			# entry may be the empty string
			if not entry:
				continue
			dnsforwardzone, dnsaliaszonecontainer, alias = entry
			results = self.lo.searchDn( base = dnsaliaszonecontainer, scope = 'domain', filter = 'relativedomainname=%s' % alias, unique = 0 )
			for result in results:
				object = univention.admin.objects.get( univention.admin.modules.get( 'dns/alias' ), self.co, self.lo, position = self.position, dn = result )
				object.open( )
				object[ 'cname' ] = '%s.%s.' % (new_name, dnsforwardzone)
				object.modify( )

	def __rename_dhcp_object( self, position = None, old_name = None, new_name = None ):
		module = univention.admin.modules.get( 'dhcp/host' )
		tmppos = univention.admin.uldap.position( self.position.getDomain( ) )
		for mac in self[ 'mac' ]:
			# mac may be the empty string
			if not mac:
				continue
			ethernet = 'ethernet %s' % mac

			results = self.lo.searchDn( base = tmppos.getBase( ), scope = 'domain', filter = 'dhcpHWAddress=%s' % ethernet, unique = 0 )
			if not results:
				continue
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'simpleComputer: filter [ dhcpHWAddress = %s ]; results: %s' % ( ethernet, results ) )

			for result in results:
				object = univention.admin.objects.get( univention.admin.modules.get( 'dhcp/host' ), self.co, self.lo, position = self.position, dn = result )
				object.open( )
				object[ 'host' ] = object[ 'host' ].replace( old_name, new_name )
				object.modify( )


	def __remove_from_dhcp_object( self, position = None, name = None, oldname = None, mac = None, ip = None ):
		# if we got the mac addres, then we remove the object
		# if we only got the ip addres, we remove the ip address

		univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'we should remove a dhcp object: position="%s", name="%s", oldname="%s", mac="%s", ip="%s"' % ( position, name, oldname, mac, ip ) )
		
		dn = None

		tmppos = univention.admin.uldap.position( self.position.getDomain( ) )
		if ip and mac:
			ethernet = 'ethernet %s' % mac
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'we only remove the ip "%s" from the dhcp object' % ip )
			results = self.lo.search( base = tmppos.getBase( ), scope = 'domain', attr = [ 'univentionDhcpFixedAddress' ], filter = '(&(dhcpHWAddress=%s)(univentionDhcpFixedAddress=%s))' % ( ethernet, ip), unique = 0 )
			for dn, attr in results:
				object = univention.admin.objects.get( univention.admin.modules.get( 'dhcp/host' ), self.co, self.lo, position = self.position, dn = dn )
				object.open( )
				if ip in object[ 'fixedaddress' ]:
					univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'fixedaddress: "%s"' % object[ 'fixedaddress' ] )
					object[ 'fixedaddress' ].remove( ip )
					if len( object[ 'fixedaddress' ] ) == 0:
						object.remove( )
					else:
						object.modify( )
					dn = object.dn

		elif mac:
			ethernet = 'ethernet %s' % mac
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'Remove the following mac: ethernet: "%s"' % ethernet )
			results = self.lo.search( base = tmppos.getBase( ), scope = 'domain', attr = [ 'univentionDhcpFixedAddress' ], filter = 'dhcpHWAddress=%s' % ethernet, unique = 0 )
			for dn, attr in results:
				univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, '... done' )
				object = univention.admin.objects.get( univention.admin.modules.get( 'dhcp/host' ), self.co, self.lo, position = self.position, dn = dn )
				object.remove( )
				dn = object.dn

		elif ip:
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'Remove the following ip: "%s"' % ip )
			results = self.lo.search( base = tmppos.getBase( ), scope = 'domain', attr = [ 'univentionDhcpFixedAddress' ], filter = 'univentionDhcpFixedAddress=%s' % ip, unique = 0 )
			for dn, attr in results:
				univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, '... done' )
				object = univention.admin.objects.get( univention.admin.modules.get( 'dhcp/host' ), self.co, self.lo, position = self.position, dn = dn )
				object.remove( )
				dn = object.dn

		return dn

	def __split_dhcp_line( self, entry ):
		if self.__is_mac ( entry[ -1 ] ):
			if self.__is_ip ( entry[ -2 ] ):
				return entry
			else:
				return ( entry[ 0 ], None, entry[ -1 ] )

		return ( entry[ 0 ], None, None )

	def __split_dns_line( self, entry ):
		zone = entry[ 0 ]
		if len( entry ) > 1:
			ip = self.__is_ip( entry[ 1 ] ) and entry[ 1 ] or None
		else:
			ip = None

		univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'Split entry %s into zone %s and ip %s' % ( entry, zone, ip ) )
		return ( zone, ip )

	def __remove_dns_reverse_object( self, name, dnsEntryZoneReverse , ip ):
		univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'we should remove a dns reverse object: dnsEntryZoneReverse="%s", name="%s", ip="%s"' % ( dnsEntryZoneReverse, name, ip ) )
		if dnsEntryZoneReverse:
			rdn = self.calc_dns_reverse_entry_name( ip, dnsEntryZoneReverse )
			if rdn:
				self.lo.delete( 'relativeDomainName=%s,%s' % ( rdn, dnsEntryZoneReverse ) )
				zone = univention.admin.handlers.dns.reverse_zone.object( self.co, self.lo, self.position, dnsEntryZoneReverse )
				zone.open( )
				zone.modify( )
		elif ip:
			tmppos = univention.admin.uldap.position( self.position.getDomain( ) )
			results = self.lo.search( base = tmppos.getBase( ), scope = 'domain', attr = [ 'zoneDn' ], filter = '(&(objectClass=dNSZone)(|(pTRRecord=%s)(pTRRecord=%s.*)))' % ( name, name ), unique = 0 )
			for dn, attr in results:
				univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'DEBUG: dn: "%s"' % dn )
				zone = string.join( ldap.explode_dn( dn )[ 1: ], ',' )
				univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'DEBUG: zone: "%s"' % zone )
				rdn = self.calc_dns_reverse_entry_name( ip, zone )
				univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'DEBUG: rdn: "%s"' % rdn )
				if rdn:
					try:
						self.lo.delete( 'relativeDomainName=%s,%s' % ( rdn, zone ) )
						zone = univention.admin.handlers.dns.reverse_zone.object( self.co, self.lo, self.position, zone )
						zone.open( )
						zone.modify( )
					except univention.admin.uexceptions.noObject:
						pass
			pass
	def __add_dns_reverse_object( self, name, zoneDn, ip ):
		univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'we should create a dns reverse object: zoneDn="%s", name="%s", ip="%s"' % ( zoneDn, name, ip ) )
		if name and zoneDn and ip:
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'dns reverse object: start' )
			if ':' in ip: # IPv6, e.g. ip=2001:db8:100::5
				# 0.1.8.b.d.0.1.0.0.2.ip6.arpa → 0.1.8.b.d.1.0.0.2 → ['0', '1', '8', 'b', 'd', '0', '1', '0', '0', '2', ]
				subnet = ldap.explode_dn(zoneDn, 1)[0].replace('.ip6.arpa', '').split('.')
				# ['0', '1', '8', 'b', 'd', '0', '1', '0', '0', '2', ] → ['2', '0', '0', '1', '0', 'd', 'b', '8', '1', '0', ]
				subnet.reverse()
				# ['2', '0', '0', '1', '0', 'd', 'b', '8', '1', '0', ] → ['2001', '0db8', '10', ] → '2001:0db8:10'
				subnet = ':'.join([''.join(subnet[i:i+4]) for i in xrange(0, len(subnet), 4)])
				# '2001:db8:100:5' → '2001:0db8:0100:0000:0000:0000:0000:0005'
				ip = ipaddr.IPv6Address(ip).exploded
				if not ip.startswith(subnet):
					raise univention.admin.uexceptions.missingInformation, _( 'Reverse zone and IP address are incompatible.' )
				# '2001:0db8:0100:0000:0000:0000:0000:0005' → '00:0000:0000:0000:0000:0005'
				ipPart = ip[len(subnet):]
				# '00:0000:0000:0000:0000:0005' → '0000000000000000000005' → ['0', '0', …, '0', '0', '5', ]
				pointer = list(ipPart.replace(':', ''))
				# ['0', '0', …, '0', '0', '5', ] → ['5', '0', '0', …, '0', '0', ]
				pointer.reverse()
				# ['5', '0', '0', …, '0', '0', ] → '5.0.0.….0.0'
				ipPart = '.'.join(pointer)
				tmppos = univention.admin.uldap.position( self.position.getDomain( ) )
				# check in which forward zone the ip is set
				hostname_list = []
				results = self.lo.search( base = tmppos.getBase( ) , scope = 'domain', attr = [ 'zoneName' ], filter = '(&(relativeDomainName=%s)(aAAARecord=%s))' % ( name, ip ), unique = 0 )
			else:
				subnet = ldap.explode_dn( zoneDn, 1 )[ 0 ].replace( '.in-addr.arpa', '' ).split( '.' )
				subnet.reverse( )
				subnet = string.join( subnet, '.' ) + '.'
				ipPart = ip.replace( subnet, '' )
				if ipPart == ip:
					raise univention.admin.uexceptions.InvalidDNS_Information, _( 'Reverse zone and IP address are incompatible.' )
				pointer = string.split( ipPart, '.' )
				pointer.reverse( )
				ipPart = string.join( pointer, '.' )
				tmppos = univention.admin.uldap.position( self.position.getDomain( ) )
				# check in which forward zone the ip is set
				hostname_list = []
				results = self.lo.search( base = tmppos.getBase( ) , scope = 'domain', attr = [ 'zoneName' ], filter = '(&(relativeDomainName=%s)(aRecord=%s))' % ( name, ip ), unique = 0 )
			if results:
				for dn,attr in results:
					if attr.has_key( 'zoneName' ):
						if not '%s.%s.' % ( name, attr[ 'zoneName' ][ 0 ] ) in hostname_list:
							hostname_list.append( '%s.%s.' % ( name, attr[ 'zoneName' ][ 0 ] ) )

			if len( hostname_list ) < 1:
				hostname_list.append ( name )

			# check if the object exists
			results = self.lo.search( base = tmppos.getBase() , scope = 'domain', attr = [ 'dn' ], filter = '(&(relativeDomainName=%s)(%s))' % ( ipPart, ldap.explode_dn(zoneDn)[0] ), unique = 0 )
			if not results:
				self.lo.add( 'relativeDomainName=%s,%s' % ( ipPart, zoneDn ), [ \
						( 'objectClass', [ 'top', 'dNSZone' ] ), \
						( 'zoneName', [ ldap.explode_dn( zoneDn, 1 )[ 0 ] ] ), \
						( 'relativeDomainName', [ ipPart ] ) ,
						( 'PTRRecord',  hostname_list  ) ] )

				#update Serial
				zone = univention.admin.handlers.dns.reverse_zone.object( self.co, self.lo, self.position, zoneDn )
				zone.open( )
				zone.modify( )

	def __remove_dns_forward_object( self, name, zoneDn, ip = None ):
		univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'we should remove a dns forward object: zoneDn="%s", name="%s", ip="%s"' % ( zoneDn, name, ip ) )
		if name:
			# check if dns forward object has more than one ip address
			if not ip:
				if zoneDn:
					self.lo.delete( 'relativeDomainName=%s,%s'% ( name, zoneDn ) )
					zone=univention.admin.handlers.dns.forward_zone.object( self.co, self.lo, self.position, zoneDn )
					zone.open( )
					zone.modify( )
			else:
				if zoneDn:
					base = zoneDn
				else:
					tmppos = univention.admin.uldap.position( self.position.getDomain( ) )
					base = tmppos.getBase( )
				univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'search base="%s"' % base )
				if ':' in ip:
					ip = ipaddr.IPv6Address(ip).exploded
					(attrEdit, attrOther, ) = ('aAAARecord', 'aRecord', )
				else:
					(attrEdit, attrOther, ) = ('aRecord', 'aAAARecord', )
				results = self.lo.search(base=base, scope='domain', attr=['aRecord', 'aAAARecord', ], filter='(&(relativeDomainName=%s)(%s=%s))' % (name, attrEdit, ip, ), unique=0, required=0)
				for dn, attr in results:
					if attr[attrEdit] == [ip, ] and not attr.get(attrOther): # the <ip> to be removed is the last on the object
						# remove the object
						self.lo.delete( dn )
						if not zoneDn:
							zone = string.join( ldap.explode_dn( dn )[ 1: ], ',' )
						else:
							zone = zoneDn

						zone=univention.admin.handlers.dns.forward_zone.object( self.co, self.lo, self.position, zone )
						zone.open( )
						zone.modify( )
					else:
						# remove only the ip address attribute
						new_ip_list = copy.deepcopy(attr[attrEdit])
						new_ip_list.remove( ip )

						self.lo.modify(dn, [(attrEdit, attr[attrEdit], new_ip_list, ), ])

						if not zoneDn:
							zone = string.join( ldap.explode_dn( dn )[ 1: ], ',' )
						else:
							zone = zoneDn

						zone=univention.admin.handlers.dns.forward_zone.object( self.co, self.lo, self.position, zone )
						zone.open( )
						zone.modify( )

	def check_common_name_length(self):
		univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'check_common_name_length with self["ip"] = %r and self["dnsEntryZoneForward"] = %r' % (self['ip'], self['dnsEntryZoneForward'], ))
		if len(self['ip']) > 0 and len(self['dnsEntryZoneForward']) > 0:
			for zone in self['dnsEntryZoneForward']:
				if zone == '':
					continue
				zoneName = univention.admin.uldap.explodeDn( zone[ 0 ], 1 )[ 0 ]
				if len(zoneName) + len(self['name']) >= 63:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'simpleComputer: length of Common Name is too long: %d' % (len(zoneName) + len(self['name']) + 1))
					raise univention.admin.uexceptions.commonNameTooLong

	def __modify_dns_forward_object( self, name, zoneDn, new_ip, old_ip ):
		univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'we should modify a dns forward object: zoneDn="%s", name="%s", new_ip="%s", old_ip="%s"' % ( zoneDn, name, new_ip, old_ip ) )
		zone = None
		if old_ip and new_ip:
			if not zoneDn:
				tmppos = univention.admin.uldap.position( self.position.getDomain( ) )
				base = tmppos.getBase( )
			else:
				base = zoneDn
			if ':' in old_ip: # IPv6
				old_ip = ipaddr.IPv6Address(old_ip).exploded
				results = self.lo.search( base = base, scope = 'domain', attr = [ 'aAAARecord' ], filter = '(&(relativeDomainName=%s)(aAAARecord=%s))' % ( name, old_ip ), unique = 0 )
			else:
				results = self.lo.search( base = base, scope = 'domain', attr = [ 'aRecord' ], filter = '(&(relativeDomainName=%s)(aRecord=%s))' % ( name, old_ip ), unique = 0 )
			for dn, attr in results:
				old_aRecord    =               attr.get('aRecord', [])
				new_aRecord    = copy.deepcopy(attr.get('aRecord', []))
				old_aAAARecord =               attr.get('aAAARecord', [])
				new_aAAARecord = copy.deepcopy(attr.get('aAAARecord', []))
				if ':' in old_ip: # IPv6
					new_aAAARecord.remove(old_ip)
				else:
					new_aRecord.remove(old_ip)
				if ':' in new_ip: # IPv6
					new_ip = ipaddr.IPv6Address(new_ip).exploded
					if new_ip not in new_aAAARecord:
						new_aAAARecord.append(new_ip)
				else:
					if new_ip not in new_aRecord:
						new_aRecord.append(new_ip)
				modlist = []
				if ':' in old_ip or ':' in new_ip:
					if old_aAAARecord != new_aAAARecord:
						modlist.append( ('aAAARecord', old_aAAARecord, new_aAAARecord, ) )
				if ':' not in old_ip or ':' not in new_ip:
					if old_aRecord != new_aRecord:
						modlist.append( ('aRecord', old_aRecord, new_aRecord, ) )
				self.lo.modify(dn, modlist)
				if not zoneDn:
					zone = string.join( ldap.explode_dn( dn )[ 1: ], ',' )

			if zoneDn:
				zone = zoneDn

			if zone:
				univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'update the zon sOARecord for the zone: %s' % zone)

				zone=univention.admin.handlers.dns.forward_zone.object( self.co, self.lo, self.position, zone )
				zone.open( )
				zone.modify( )

	def __add_dns_forward_object( self, name, zoneDn, ip ):
		univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'we should add a dns forward object: zoneDn="%s", name="%s", ip="%s"' % ( zoneDn, name, ip ) )
		if ip.find(':')!=-1: #IPv6
			self.__add_dns_forward_object_ipv6(name, zoneDn, ipaddr.IPv6Address(ip).exploded)
		else:
			self.__add_dns_forward_object_ipv4(name, zoneDn, ip)

	def __add_dns_forward_object_ipv6( self, name, zoneDn, ip ):
		if name and ip and zoneDn:
			ip = ipaddr.IPv6Address(ip).exploded
			results = self.lo.search( base = zoneDn, scope = 'domain', attr = [ 'aAAARecord' ], filter = '(&(relativeDomainName=%s)(!(cNAMERecord=*)))' % ( name ), unique = 0 )
			if not results:
				try:
					self.lo.add( 'relativeDomainName=%s,%s'% ( name, zoneDn ), [\
										( 'objectClass', [ 'top', 'dNSZone' ]),\
										( 'zoneName', univention.admin.uldap.explodeDn( zoneDn, 1 )[ 0 ]),\
										( 'aAAARecord', [ ip ]),\
										( 'relativeDomainName', [ name ])])
				except univention.admin.uexceptions.objectExists, dn:
					raise univention.admin.uexceptions.dnsAliasRecordExists, dn
				# TODO: check if zoneDn really a forwardZone, maybe it is a container under a zone
				zone = univention.admin.handlers.dns.forward_zone.object( self.co, self.lo, self.position, zoneDn )
				zone.open()
				zone.modify()
			else:
				for dn, attr in results:
					if attr.has_key( 'aAAARecord' ):
						new_ip_list = copy.deepcopy( attr[ 'aAAARecord' ] )
						if not ip in new_ip_list:
							new_ip_list.append( ip )
							self.lo.modify( dn, [ ( 'aAAARecord', attr[ 'aAAARecord' ],  new_ip_list ) ] )
					else:
						self.lo.modify( dn, [ ( 'aAAARecord', '' ,  ip ) ] )

	def __add_dns_forward_object_ipv4( self, name, zoneDn, ip ):
		if name and ip and zoneDn:
			results = self.lo.search( base = zoneDn, scope = 'domain', attr = [ 'aRecord' ], filter = '(&(relativeDomainName=%s)(!(cNAMERecord=*)))' % ( name ), unique = 0 )
			if not results:
				try:
					self.lo.add( 'relativeDomainName=%s,%s'% ( name, zoneDn ), [\
										( 'objectClass', [ 'top', 'dNSZone' ]),\
										( 'zoneName', univention.admin.uldap.explodeDn( zoneDn, 1 )[ 0 ]),\
										( 'ARecord', [ ip ]),\
										( 'relativeDomainName', [ name ])])
				except univention.admin.uexceptions.objectExists, dn:
					raise univention.admin.uexceptions.dnsAliasRecordExists, dn
				# TODO: check if zoneDn really a forwardZone, maybe it is a container under a zone
				zone = univention.admin.handlers.dns.forward_zone.object( self.co, self.lo, self.position, zoneDn )
				zone.open()
				zone.modify()
			else:
				for dn, attr in results:
					if attr.has_key( 'aRecord' ):
						new_ip_list = copy.deepcopy( attr[ 'aRecord' ] )
						if not ip in new_ip_list:
							new_ip_list.append( ip )
							self.lo.modify( dn, [ ( 'aRecord', attr[ 'aRecord' ],  new_ip_list ) ] )
					else:
						self.lo.modify( dn, [ ( 'aRecord', '' ,  ip ) ] )


	def __add_dns_alias_object( self, name, dnsForwardZone, dnsAliasZoneContainer, alias ):
		univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'add a dns alias object: name="%s", dnsForwardZone="%s", dnsAliasZoneContainer="%s", alias="%s"' % ( name, dnsForwardZone, dnsAliasZoneContainer, alias ) )
		if name and dnsForwardZone and dnsAliasZoneContainer and alias:
			results = self.lo.search( base = dnsAliasZoneContainer, scope = 'domain', attr = [ 'cNAMERecord' ], filter = 'relativeDomainName=%s' % ( alias ), unique = 0 )
			if not results:
				self.lo.add( 'relativeDomainName=%s,%s'% ( alias, dnsAliasZoneContainer ), [\
									( 'objectClass', [ 'top', 'dNSZone' ]),\
									( 'zoneName', univention.admin.uldap.explodeDn( dnsAliasZoneContainer, 1 )[ 0 ]),\
									( 'cNAMERecord', [ "%s.%s." % (name, dnsForwardZone) ]),\
									( 'relativeDomainName', [ alias ])])

				# TODO: check if dnsAliasZoneContainer really is a forwardZone, maybe it is a container under a zone
				zone = univention.admin.handlers.dns.forward_zone.object( self.co, self.lo, self.position, dnsAliasZoneContainer )
				zone.open()
				zone.modify()
			else:
				# thow exeption, cNAMERecord is single value
				raise univention.admin.uexceptions.dnsAliasAlreadyUsed, _('DNS alias is already in use.')
		pass

	def __remove_dns_alias_object( self, name, dnsForwardZone, dnsAliasZoneContainer, alias = None ):
		univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'remove a dns alias object: name="%s", dnsForwardZone="%s", dnsAliasZoneContainer="%s", alias="%s"' % ( name, dnsForwardZone, dnsAliasZoneContainer, alias ) )
		if name:
			if alias:
				if dnsAliasZoneContainer:
					self.lo.delete( 'relativeDomainName=%s,%s'% ( alias, dnsAliasZoneContainer ) )
					zone=univention.admin.handlers.dns.forward_zone.object( self.co, self.lo, self.position, dnsAliasZoneContainer )
					zone.open( )
					zone.modify( )
				elif dnsForwardZone:
					tmppos = univention.admin.uldap.position( self.position.getDomain( ) )
					base = tmppos.getBase( )
					univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'search base="%s"' % base )
					results = self.lo.search( base = base, scope = 'domain', attr = [ 'zoneName' ], filter = '(&(objectClass=dNSZone)(relativeDomainName=%s)(cNAMERecord=%s.%s.))' % ( alias, name, dnsForwardZone ), unique = 0, required = 0 )
					for dn, attr in results:
						# remove the object
						self.lo.delete( dn )
						# and update the SOA version number for the zone
						results = self.lo.searchDn( base = tmppos.getBase( ), scope = 'domain', filter = '(&(objectClass=dNSZone)(zoneName=%s)(relativeDomainName=@))' % attr[ 'zoneName' ][0], unique = 0 )
						for zoneDn in results:
							zone=univention.admin.handlers.dns.forward_zone.object( self.co, self.lo, self.position, zoneDn )
							zone.open( )
							zone.modify( )
					else:
						# could thow some exeption
						pass
			else:
				if dnsForwardZone:
					tmppos = univention.admin.uldap.position( self.position.getDomain( ) )
					base = tmppos.getBase( )
					univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'search base="%s"' % base )
					results = self.lo.search( base = base, scope = 'domain', attr = [ 'zoneName' ], filter = '(&(objectClass=dNSZone)(&(cNAMERecord=%s)(cNAMERecord=%s.%s.))' % ( name, name, dnsForwardZone ), unique = 0, required = 0 )
					for dn, attr in results:
						# remove the object
						self.lo.delete( dn )
						# and update the SOA version number for the zone
						results = self.lo.searchDn( base = tmppos.getBase( ), scope = 'domain', filter = '(&(objectClass=dNSZone)(zoneName=%s)(relativeDomainName=@))' % attr[ 'zoneName' ][0], unique = 0 )
						for zoneDn in results:
							zone=univention.admin.handlers.dns.forward_zone.object( self.co, self.lo, self.position, zoneDn )
							zone.open( )
							zone.modify( )
				else: # not enough info to remove alias entries
					pass

	def _ldap_post_modify( self ):

		if len ( self[ 'mac' ] ) > 1 or len( self[ 'ip' ] ) > 1:
			self.__multiip = True

		for entry in self.__changes[ 'dhcpEntryZone' ][ 'remove' ]:
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'simpleComputer: dhcp check: removed: %s' % entry )
			dn, ip, mac = self.__split_dhcp_line( entry )
			if not ip and not mac and not self.__multiip:
				self.__remove_from_dhcp_object( dn,  mac = self[ 'mac' ][ 0 ] )
			else:
				self.__remove_from_dhcp_object( dn, ip = ip, mac = mac )

		for entry in self.__changes[ 'dhcpEntryZone' ][ 'add' ]:
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'simpleComputer: dhcp check: added: %s' % entry )
			dn, ip, mac = self.__split_dhcp_line( entry )
			if not ip and not mac and not self.__multiip:
				self.__modify_dhcp_object( dn, self[ 'name' ], self[ 'ip' ][ 0 ], self[ 'mac' ][ 0 ] )
			else:
				self.__modify_dhcp_object( dn, self[ 'name' ], ip, mac )

		for entry in self.__changes[ 'dnsEntryZoneForward' ][ 'remove' ]:
			dn, ip = self.__split_dns_line( entry )
			if not ip and not self.__multiip:
				self.__remove_dns_forward_object( self[ 'name' ], dn, self[ 'ip' ][ 0 ] )
			else:
				self.__remove_dns_forward_object( self[ 'name' ], dn, ip )

		for entry in self.__changes[ 'dnsEntryZoneForward' ][ 'add' ]:
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'we should add a dns forward object "%s"' % entry )
			dn, ip = self.__split_dns_line( entry )
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'changed the object to dn="%s" and ip="%s"' % ( dn, ip ) )
			if not ip and not self.__multiip:
				univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'no multiip environment')
				self.__add_dns_forward_object( self[ 'name' ], dn, self[ 'ip' ][ 0 ] )
			else:
				self.__add_dns_forward_object( self[ 'name' ], dn, ip )

		for entry in self.__changes[ 'dnsEntryZoneReverse' ][ 'remove' ]:
			dn, ip = self.__split_dns_line( entry )
			if not ip and not self.__multiip:
				self.__remove_dns_reverse_object( self[ 'name' ], dn, self[ 'ip' ][ 0 ] )
			else:
				self.__remove_dns_reverse_object( self[ 'name' ], dn, ip )

		for entry in self.__changes[ 'dnsEntryZoneReverse' ][ 'add' ]:
			dn, ip = self.__split_dns_line( entry )
			if not ip and not self.__multiip:
				self.__add_dns_reverse_object( self[ 'name' ], dn, self[ 'ip' ][ 0 ] )
			else:
				self.__add_dns_reverse_object( self[ 'name' ], dn, ip )


		for entry in self.__changes[ 'dnsEntryZoneAlias' ][ 'remove' ]:
			dnsForwardZone, dnsAliasZoneContainer, alias = entry
			if not alias:
				# nonfunctional code since self[ 'alias' ] should be self[ 'dnsAlias' ], but ths case does not seem to occur
				self.__remove_dns_alias_object( self[ 'name' ], dnsForwardZone, dnsAliasZoneContainer, self[ 'alias' ][ 0 ] )
			else:
				self.__remove_dns_alias_object( self[ 'name' ], dnsForwardZone, dnsAliasZoneContainer, alias )

		for entry in self.__changes[ 'dnsEntryZoneAlias' ][ 'add' ]:
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'we should add a dns alias object "%s"' % entry )
			dnsForwardZone, dnsAliasZoneContainer, alias = entry
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'changed the object to dnsForwardZone [%s], dnsAliasZoneContainer [%s] and alias [%s]' % (dnsForwardZone, dnsAliasZoneContainer, alias))
			if not alias:
				self.__add_dns_alias_object( self[ 'name' ], dnsForwardZone, dnsAliasZoneContainer, self[ 'alias' ][ 0 ] )
			else:
				self.__add_dns_alias_object( self[ 'name' ], dnsForwardZone, dnsAliasZoneContainer, alias )

		for entry in self.__changes[ 'mac' ][ 'remove' ]:
			self.__remove_from_dhcp_object(  mac = entry )

		changed_ip = False
		for entry in self.__changes[ 'ip' ][ 'remove' ]:
			# self.__remove_from_dhcp_object(  ip = entry )
			if not self.__multiip:
				if len( self.__changes[ 'ip' ][ 'add' ]) > 0:
					# we change
					self.__modify_dns_forward_object( self[ 'name' ], None, self.__changes[ 'ip' ][ 'add' ][ 0 ], self.__changes[ 'ip' ][ 'remove' ][ 0 ] )
					changed_ip = True
					if len (self[ 'mac' ] ) > 0:
						dn = self.__remove_from_dhcp_object(  None, self[ 'name' ], entry,  self[ 'mac' ][ 0 ])
						try:
							dn = string.join(dn.split(',')[1:],',')
							self.__modify_dhcp_object( dn, self[ 'name' ], self.__changes[ 'ip' ][ 'add' ][ 0 ],  self[ 'mac' ][ 0 ] )
						except:
							pass
				else:
					# remove the dns objects
					self.__remove_dns_forward_object( self[ 'name' ], None, entry )
			else:
				self.__remove_dns_forward_object( self[ 'name' ], None, entry )
				self.__remove_from_dhcp_object(  ip = entry )

			self.__remove_dns_reverse_object( self[ 'name' ], None, entry )

		for entry in self.__changes[ 'ip' ][ 'add' ]:
			if not self.__multiip:
				if self.has_key( 'dnsEntryZoneForward' ) and len( self[ 'dnsEntryZoneForward' ] ) > 0:
					if not changed_ip:
						self.__add_dns_forward_object( self[ 'name' ], self[ 'dnsEntryZoneForward' ][ 0 ][ 0 ], entry )
				if self.has_key( 'dnsEntryZoneReverse' ) and len( self[ 'dnsEntryZoneReverse' ] ) > 0:
					for dnsEntryZoneReverse in self['dnsEntryZoneReverse']:
						x, ip = self.__split_dns_line(dnsEntryZoneReverse)
						zoneIsV6 = ldap.explode_dn(x, 1)[0].endswith('.ip6.arpa')
						entryIsV6 = ':' in entry
						if zoneIsV6 == entryIsV6:
							self.__add_dns_reverse_object( self[ 'name' ], x, entry )

		if self.__changes[ 'name' ]:
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'simpleComputer: name has changed' )
			self.__update_groups_after_namechange()
			self.__rename_dhcp_object( position = None, old_name = self.__changes[ 'name' ][ 0 ], new_name = self.__changes[ 'name' ][ 1 ] )
			self.__rename_dns_object( position = None, old_name = self.__changes[ 'name' ][ 0 ], new_name = self.__changes[ 'name' ][ 1 ] )
			pass

		if self.ipRequest == 1 and self[ 'ip' ]:
			for ipAddress in self[ 'ip' ]:
				if ipAddress:
					univention.admin.allocators.confirm( self.lo, self.position, 'aRecord', ipAddress )
			self.ipRequest = 0
		if self[ 'mac' ]:
			for macAddress in self[ 'mac' ]:
				if macAddress:
					univention.admin.allocators.confirm( self.lo, self.position, 'mac', macAddress )

		self.update_groups()

	def __remove_associated_domain( self, entry ):
		dn, ip = self.__split_dns_line( entry )
		domain = string.join(ldap.explode_rdn(dn)[0].split('=')[1:], '=')
		if self.info.get('domain', None) == domain:
			self.info['domain'] = None

	def __set_associated_domain( self, entry ):
		dn, ip = self.__split_dns_line( entry )
		domain = string.join(ldap.explode_rdn(dn)[0].split('=')[1:], '=')
		if not self.info.get('domain', None):
			self.info['domain'] = domain


	def _ldap_modlist( self ):
		self.__changes =  {	'mac': {'remove': [ ], 'add': [ ]}, 'ip': {'remove': [ ], 'add': [ ]}, 'name': None,
							'dnsEntryZoneForward': { 'remove': [ ], 'add': [ ] },
							'dnsEntryZoneReverse': { 'remove': [ ], 'add': [ ] },
							'dnsEntryZoneAlias': { 'remove': [ ], 'add': [ ] },
							'dhcpEntryZone': { 'remove': [ ], 'add': [ ] } }
		ml = [ ]
		if self.hasChanged( 'mac' ):
			for macAddress in self.info.get( 'mac', [] ):
				if self.oldinfo.has_key( 'mac' ) and macAddress in self.oldinfo[ 'mac' ]:
					continue
				try:
					mac = univention.admin.allocators.request( self.lo, self.position, 'mac', value = macAddress )
					if not mac:
						self.cancel( )
						raise univention.admin.uexceptions.noLock
					self.alloc.append( ( 'mac', macAddress ) )
					self.__changes[ 'mac' ][ 'add' ].append( macAddress )
				except univention.admin.uexceptions.noLock:
					self.cancel( )
					raise univention.admin.uexceptions.macAlreadyUsed, ' %s' % macAddress
			if self.oldinfo.has_key( 'mac' ):
				for macAddress in self.oldinfo[ 'mac' ]:
					if macAddress in self.info.get( 'mac', [] ):
						continue
					self.__changes[ 'mac' ][ 'remove' ].append( macAddress )

		oldAddresses = self.oldinfo.get('ip')
		newAddresses = self.info.get('ip')
		oldARecord = []
		newARecord = []
		oldAaaaRecord = []
		newAaaaRecord = []
		if oldAddresses != newAddresses:
			if oldAddresses:
			    for address in oldAddresses:
					if ':' in address: # IPv6
						oldAaaaRecord.append(address)
					else:
						oldARecord.append(address)
			if newAddresses:
			    for address in newAddresses:
					if ':' in address: # IPv6
						newAaaaRecord.append(ipaddr.IPv6Address(address).exploded)
					else:
						newARecord.append(address)
			ml.append(('aRecord',    oldARecord,    newARecord, ))
			ml.append(('aAAARecord', oldAaaaRecord, newAaaaRecord, ))

		if self.hasChanged( 'ip' ):
			for ipAddress in self[ 'ip' ]:
				if self.oldinfo.has_key( 'ip' ) and ipAddress in self.oldinfo[ 'ip' ]:
					continue
				if not self.ip_alredy_requested:
					try:
						IpAddr = univention.admin.allocators.request( self.lo, self.position, 'aRecord', value = ipAddress )
						if not IpAddr:
							self.cancel( )
							raise univention.admin.uexceptions.noLock
					except univention.admin.uexceptions.noLock:
						self.cancel( )
						self.ip_alredy_requested = 0
						raise univention.admin.uexceptions.ipAlreadyUsed, ' %s' % ipAddress
				else:
					IpAddr = ipAddress

				self.alloc.append( ( 'aRecord', IpAddr ) )

				self.ipRequest = 1
				self.__changes[ 'ip' ][ 'add' ].append( ipAddress )

			if self.oldinfo.has_key( 'ip' ):
				for ipAddress in self.oldinfo[ 'ip' ]:
					if ipAddress in self.info[ 'ip' ]:
						continue
					self.__changes[ 'ip' ][ 'remove' ].append( ipAddress )


		if self.hasChanged( 'name' ):
			ml.append( ( 'sn', self.oldattr.get( 'sn', [ None ] )[ 0 ], self[ 'name' ] ) )
			self.__changes[ 'name' ] = ( self.oldattr.get( 'sn', [ None ] )[ 0 ], self[ 'name' ] )

		if self.hasChanged('ip') or self.hasChanged('mac'):

			if len(self.info['ip']) == 1 and len(self.info['mac']) == 1 and len(self.info['dhcpEntryZone']):
				# In this special case, we assume the mapping between ip/mac address to be
				# unique. The dhcp entry needs to contain the mac address (as sepcified by
				# the ldap search for dhcp entries), the ip address may not correspond to 
				# the ip address associated with the computer ldap object, but this would 
				# be erroneous anyway. We therefore update the dhcp entry to correspond to 
				# the current ip and mac address. (Bug #20315)
				dn, ip, mac = self.__split_dhcp_line( self.info['dhcpEntryZone'][0] )

				if dn and ip and mac:
					self.info['dhcpEntryZone'] = [ [ dn, self.info['ip'][0], self.info['mac'][0] ] ]
				else:
					self.info['dhcpEntryZone'] = []
			else:
				# in all other cases, we remove old dhcp entries that do not match ip or
				# mac addresses (Bug #18966)

				# get all IP addresses that have been removed
				removedIPs = []
				if self.oldinfo.has_key('ip'):
					removedIPs = [ ip for ip in self.oldinfo['ip'] if ip and ip not in self['ip'] ]

				# get all MAC addresses that have been removed
				removedMACs = []
				if self.oldinfo.has_key('mac'):
					removedMACs = [ mac for mac in self.oldinfo['mac'] if mac and mac not in self['mac'] ]

				# remove all DHCP-entries that have been associated with any of these IP/MAC addresses
				newDhcpEntries = []
				for entry in self['dhcpEntryZone']:
					dn, ip, mac = self.__split_dhcp_line( entry )
					if ip not in removedIPs and mac not in removedMACs:
						newDhcpEntries.append(entry)

				# update the value
				self.info['dhcpEntryZone'] = newDhcpEntries

		if self.hasChanged( 'dhcpEntryZone' ):
			if self.oldinfo.has_key( 'dhcpEntryZone' ):
				if 'dhcpEntryZone' in self.info:
					for entry in self.oldinfo[ 'dhcpEntryZone' ]:
						if not entry in self.info[ 'dhcpEntryZone' ]:
							self.__changes[ 'dhcpEntryZone' ][ 'remove' ].append( entry )
				else:
					for entry in self.oldinfo[ 'dhcpEntryZone' ]:
						self.__changes[ 'dhcpEntryZone' ][ 'remove' ].append( entry )
			if 'dhcpEntryZone' in self.info:
				for entry in self.info[ 'dhcpEntryZone' ]:
					#check if line is valid
					dn, ip, mac = self.__split_dhcp_line( entry )
					if dn and ip and mac:
						if not self.oldinfo.has_key( 'dhcpEntryZone' ) or not entry in self.oldinfo[ 'dhcpEntryZone' ]:
							self.__changes[ 'dhcpEntryZone' ][ 'add' ].append( entry )
					else:
						raise univention.admin.uexceptions.invalidDhcpEntry, _('The DHCP entry for this host should contain the zone LDAP-DN, the IP address and the MAC address.')

		if self.hasChanged( 'dnsEntryZoneForward' ):
			if self.oldinfo.has_key( 'dnsEntryZoneForward' ):
				for entry in self.oldinfo[ 'dnsEntryZoneForward' ]:
					if not entry in self.info[ 'dnsEntryZoneForward' ]:
						self.__changes[ 'dnsEntryZoneForward' ][ 'remove' ].append( entry )
						self.__remove_associated_domain ( entry )
			for entry in self.info[ 'dnsEntryZoneForward' ]:
				if entry == '':
					continue
				if not self.oldinfo.has_key( 'dnsEntryZoneForward' ) or not entry in self.oldinfo[ 'dnsEntryZoneForward' ]:
					self.__changes[ 'dnsEntryZoneForward' ][ 'add' ].append( entry )
				self.__set_associated_domain( entry )

		if self.hasChanged( 'dnsEntryZoneReverse' ):
			if self.oldinfo.has_key( 'dnsEntryZoneReverse' ):
				for entry in self.oldinfo[ 'dnsEntryZoneReverse' ]:
					if not 'dnsEntryZoneReverse' in self.info or not entry in self.info[ 'dnsEntryZoneReverse' ]:
						self.__changes[ 'dnsEntryZoneReverse' ][ 'remove' ].append( entry )
			if 'dnsEntryZoneReverse' in self.info:
				for entry in self.info[ 'dnsEntryZoneReverse' ]:
					if not self.oldinfo.has_key( 'dnsEntryZoneReverse' ) or not entry in self.oldinfo[ 'dnsEntryZoneReverse' ]:
						self.__changes[ 'dnsEntryZoneReverse' ][ 'add' ].append( entry )

		if self.hasChanged( 'dnsEntryZoneAlias' ):
			if self.oldinfo.has_key( 'dnsEntryZoneAlias' ):
				for entry in self.oldinfo[ 'dnsEntryZoneAlias' ]:
					if not entry in self.info[ 'dnsEntryZoneAlias' ]:
						self.__changes[ 'dnsEntryZoneAlias' ][ 'remove' ].append( entry )
			for entry in self.info[ 'dnsEntryZoneAlias' ]:
				#check if line is valid
				dnsForwardZone, dnsAliasZoneContainer, alias = entry
				if dnsForwardZone and dnsAliasZoneContainer and alias:
					if not self.oldinfo.has_key( 'dnsEntryZoneAlias' ) or not entry in self.oldinfo[ 'dnsEntryZoneAlias' ]:
						self.__changes[ 'dnsEntryZoneAlias' ][ 'add' ].append( entry )
				else:
					raise univention.admin.uexceptions.invalidDNSAliasEntry, _('The DNS alias entry for this host should contain the zone name, the alias zone container LDAP-DN and the alias.')

		if len ( self[ 'mac' ] ) < 2 and len( self[ 'ip' ] ) < 2:
			self.__multiip = False
		else:
			self.__multiip = True

		ml = ml + super( simpleComputer, self )._ldap_modlist( )

		return ml

	# for ip='10.200.2.5' and subnet='2.200.10.in-addr.arpa' -> rmIP='5' ('5.2' for 200.10.in-addr.arpa)
	def calc_dns_reverse_entry_name(self, sip, reverseDN):
		if ':' in sip:
			subnet=ldap.explode_dn(reverseDN, 1)[0].replace('.ip6.arpa','').split('.')
			# '2001::db8::3' → '2001:0db8:0000:…:003' → '20010db800…003' → ['2', '0', '0', '1', …]
			ip=list(ipaddr.IPv6Address(sip).exploded.replace(':', ''))
			return self.calc_dns_reverse_entry_name_do(32, subnet, ip)
		else:
			subnet=ldap.explode_dn(reverseDN, 1)[0].replace('.in-addr.arpa','').split('.')
			ip=sip.split('.')
			return self.calc_dns_reverse_entry_name_do(4, subnet, ip)
	def calc_dns_reverse_entry_name_do(self, maxLength, zoneNet, ip):
		zoneNet.reverse()
		if not ip[:len(zoneNet)] == zoneNet:
			return 0
		ip.reverse()
		return '.'.join(ip[ : maxLength-len(zoneNet) ])

	def _ldap_pre_create(self):
		self.check_common_name_length()

	def _ldap_pre_modify(self):
		self.check_common_name_length()

	def _ldap_post_create(self):
		for entry in self.__changes[ 'dhcpEntryZone' ][ 'remove' ]:
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'simpleComputer: dhcp check: removed: %s' % entry )
			dn, ip, mac = self.__split_dhcp_line( entry )
			if not ip and not mac and not self.__multiip:
				self.__remove_from_dhcp_object( dn,  mac = self[ 'mac' ][ 0 ] )
			else:
				self.__remove_from_dhcp_object( dn, ip = ip, mac = mac )

		for entry in self.__changes[ 'dhcpEntryZone' ][ 'add' ]:
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'simpleComputer: dhcp check: added: %s' % entry )
			dn, ip, mac = self.__split_dhcp_line( entry )
			if not ip and not mac and not self.__multiip:
				if len( self[ 'ip' ] ) > 0 and len( self[ 'mac' ] ) > 0:
					self.__modify_dhcp_object( dn, self[ 'name' ], self[ 'ip' ][ 0 ], self[ 'mac' ][ 0 ] )
			else:
				self.__modify_dhcp_object( dn, self[ 'name' ], ip, mac )


		for entry in self.__changes[ 'dnsEntryZoneForward' ][ 'remove' ]:
			dn, ip = self.__split_dns_line( entry )
			if not ip and not self.__multiip:
				self.__remove_dns_forward_object( self[ 'name' ], dn, self[ 'ip' ][ 0 ] )
			else:
				self.__remove_dns_forward_object( self[ 'name' ], dn, ip )

		for entry in self.__changes[ 'dnsEntryZoneForward' ][ 'add' ]:
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'we should add a dns forward object "%s"' % entry )
			dn, ip = self.__split_dns_line( entry )
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'changed the object to dn="%s" and ip="%s"' % ( dn, ip ) )
			if not ip and not self.__multiip:
				univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'no multiip environment')
				self.__add_dns_forward_object( self[ 'name' ], dn, self[ 'ip' ][ 0 ] )
			else:
				self.__add_dns_forward_object( self[ 'name' ], dn, ip )

		for entry in self.__changes[ 'dnsEntryZoneReverse' ][ 'remove' ]:
			dn, ip = self.__split_dns_line( entry )
			if not ip and not self.__multiip:
				self.__remove_dns_reverse_object( self[ 'name' ], dn, self[ 'ip' ][ 0 ] )
			else:
				self.__remove_dns_reverse_object( self[ 'name' ], dn, ip )

		for entry in self.__changes[ 'dnsEntryZoneReverse' ][ 'add' ]:
			dn, ip = self.__split_dns_line( entry )
			if not ip and not self.__multiip:
				self.__add_dns_reverse_object( self[ 'name' ], dn, self[ 'ip' ][ 0 ] )
			else:
				self.__add_dns_reverse_object( self[ 'name' ], dn, ip )

		if not self.__multiip:
			if self.has_key('dhcpEntryZone') and len(self['dhcpEntryZone']) > 0:
				dn, ip, mac =  self[ 'dhcpEntryZone' ][ 0 ]
				for entry in self.__changes[ 'mac' ][ 'add' ]:
					if len( self[ 'ip' ] ) > 0:
						self.__modify_dhcp_object( dn , self[ 'name' ], mac = entry, ip = self[ 'ip' ][ 0 ] )
					else:
						self.__modify_dhcp_object( dn , self[ 'name' ], mac = entry )
				for entry in self.__changes[ 'ip' ][ 'add' ]:
					if len( self[ 'mac' ] ) > 0:
						self.__modify_dhcp_object( dn, self[ 'name' ], mac = self[ 'mac' ][ 0 ], ip = entry )

		for entry in self.__changes[ 'dnsEntryZoneAlias' ][ 'remove' ]:
			dnsForwardZone, dnsAliasZoneContainer, alias = entry
			if not alias:
				# nonfunctional code since self[ 'alias' ] should be self[ 'dnsAlias' ], but ths case does not seem to occur
				self.__remove_dns_alias_object( self[ 'name' ], dnsForwardZone, dnsAliasZoneContainer, self[ 'alias' ][ 0 ] )
			else:
				self.__remove_dns_alias_object( self[ 'name' ], dnsForwardZone, dnsAliasZoneContainer, alias )
		for entry in self.__changes[ 'dnsEntryZoneAlias' ][ 'add' ]:
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'we should add a dns alias object "%s"' % entry )
			dnsForwardZone, dnsAliasZoneContainer, alias = entry
			univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, 'changed the object to dnsForwardZone [%s], dnsAliasZoneContainer [%s] and alias [%s]' % (dnsForwardZone, dnsAliasZoneContainer, alias))
			if not alias:
				self.__add_dns_alias_object( self[ 'name' ], dnsForwardZone, dnsAliasZoneContainer, self[ 'alias' ][ 0 ] )
			else:
				self.__add_dns_alias_object( self[ 'name' ], dnsForwardZone, dnsAliasZoneContainer, alias )

		self.update_groups()

	def _ldap_post_remove(self):
		if self['mac']:
			for macAddress in self['mac']:
				if macAddress:
					univention.admin.allocators.release( self.lo, self.position, 'mac', macAddress )
		if self['ip']:
			for ipAddress in self['ip']:
				if ipAddress:
					univention.admin.allocators.release( self.lo, self.position, 'aRecord', ipAddress )

		# remove computer from groups
		groups = copy.deepcopy(self['groups'])
		if self.oldinfo.get('primaryGroup'):
			groups.append( self.oldinfo.get('primaryGroup') )
		for group in groups:
			groupObject = univention.admin.objects.get(univention.admin.modules.get('groups/group'), self.co, self.lo, self.position, group)
			groupObject.fast_member_remove( [ self.dn ], self.oldattr.get('uid',[]), ignore_license=1 )


	def __update_groups_after_namechange(self):
		oldname = self.oldinfo.get('name')
		newname = self.info.get('name')
		if not oldname:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, '__update_groups_after_namechange: oldname is empty')
			return

		# Since self.dn is not updated yet, self.dn contains still the old DN.
		# Thats why olddn and newdn get reassebled from scratch.
		olddn = 'cn=%s,%s' % (oldname, ','.join(univention.admin.uldap.explodeDn( self.dn, 0 )[1:]))
		newdn = 'cn=%s,%s' % (newname, ','.join(univention.admin.uldap.explodeDn( self.dn, 0 )[1:]))

		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, '__update_groups_after_namechange: olddn=%s' % olddn)
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, '__update_groups_after_namechange: newdn=%s' % newdn)

		for group in self.info.get('groups',[]):
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, '__update_groups_after_namechange: grp=%s' % group)

			# Using the UDM groups/group object does not work at this point. The computer object has already been renamed.
			# During open() of groups/group each member is checked if it exists. Because the computer object with "olddn" is missing,
			# it won't show up in groupobj['hosts']. That's why the uniqueMember/memberUid updates is done directly via
			# self.lo.modify()

			oldUniqueMembers = self.lo.getAttr(group, 'uniqueMember')
			newUniqueMembers = copy.deepcopy(oldUniqueMembers)
			if olddn in newUniqueMembers:
				newUniqueMembers.remove(olddn)
			if not newdn in newUniqueMembers:
				newUniqueMembers.append(newdn)

			oldUid = '%s$' % oldname
			newUid = '%s$' % newname
			oldMemberUids = self.lo.getAttr(group, 'memberUid')
			newMemberUids = copy.deepcopy(oldMemberUids)
			if oldUid in newMemberUids:
				newMemberUids.remove(oldUid)
			if not newUid in newMemberUids:
				newMemberUids.append(newUid)

			self.lo.modify(group, [('uniqueMember', oldUniqueMembers, newUniqueMembers), ('memberUid', oldMemberUids, newMemberUids)])


	def update_groups(self):
		if not self.hasChanged('groups') and \
			   not ('oldPrimaryGroupDn' in self.__dict__ and self.oldPrimaryGroupDn) and \
			   not ('newPrimaryGroupDn' in self.__dict__ and self.newPrimaryGroupDn):
			return
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'updating groups')

		add_to_group=[]
		remove_from_group=[]
		for group in self.oldinfo.get('groups', []):
			if not group in self.info.get('groups', []):
				remove_from_group.append(group)
		for group in self.info.get('groups', []):
			if not group in self.oldinfo.get('groups', []):
				add_to_group.append(group)

		if 'oldPrimaryGroupDn' in self.__dict__:
			if self.oldPrimaryGroupDn:
				remove_from_group.append(self.oldPrimaryGroupDn)
		if 'newPrimaryGroupDn' in self.__dict__:
			if self.newPrimaryGroupDn:
				add_to_group.append(self.newPrimaryGroupDn)

		# prevent machineAccountGroup from being removed
		if self.has_key('machineAccountGroup'):
			add_to_group.append(self['machineAccountGroup'])
			if self['machineAccountGroup'] in remove_from_group:
				remove_from_group.remove(self['machineAccountGroup'])

		for group in add_to_group:
			groupObject=univention.admin.objects.get(univention.admin.modules.get('groups/group'), self.co, self.lo, self.position, group)
			groupObject.open()
			if not self.dn in groupObject['hosts']:
				groupObject['hosts'].append(self.dn)
				groupObject.modify(ignore_license=1)

		for group in remove_from_group:
			groupObject=univention.admin.objects.get(univention.admin.modules.get('groups/group'), self.co, self.lo, self.position, group)
			groupObject.open()
			if self.dn in groupObject['hosts']:
				groupObject['hosts'].remove(self.dn)
				groupObject.modify(ignore_license=1)


	def primary_group(self):
		if not self.hasChanged('primaryGroup'):
			return
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'updating primary groups')

		searchResult=self.lo.search(base=self['primaryGroup'], attr=['gidNumber'])
		for tmp,number in searchResult:
			primaryGroupNumber = number['gidNumber']
		self.newPrimaryGroupDn=self['primaryGroup']

		if 'samba' in self.options:
			searchResult=self.lo.search(base=self['primaryGroup'], attr=['sambaSID'])
			for tmp,number in searchResult:
				primaryGroupSambaNumber = number['sambaSID']

		if self.oldinfo.has_key('primaryGroup'):
			self.oldPrimaryGroupDn=self.oldinfo['primaryGroup']
			searchResult=self.lo.search(base=self.oldinfo['primaryGroup'], attr=['gidNumber'])
			for tmp,number in searchResult:
				oldPrimaryGroup = number['gidNumber']
			self.lo.modify(self.dn, [('gidNumber',oldPrimaryGroup[0], primaryGroupNumber[0])])
			if 'samba' in self.options:
				self.lo.modify(self.dn, [('sambaPrimaryGroupSID',oldPrimaryGroup[0], primaryGroupSambaNumber[0])])
		else:
			searchResult=self.lo.search(base=self.dn, scope='base', attr=['gidNumber'])
			for tmp,number in searchResult:
				oldNumber = number['gidNumber']
			self.lo.modify(self.dn, [('gidNumber',oldNumber, primaryGroupNumber[0])])
			if 'samba' in self.options:
				self.lo.modify(self.dn, [('sambaPrimaryGroupSID',oldNumber, primaryGroupSambaNumber[0])])

	def cleanup(self):
		self.open()
		if self['dnsEntryZoneForward']:
			for dnsEntryZoneForward in self['dnsEntryZoneForward']:
				dn, ip = self.__split_dns_line( dnsEntryZoneForward )
				try:
					self.__remove_dns_forward_object( self[ 'name' ], dn, None )
				except Exception,e:
					self.exceptions.append([_('DNS forward zone'), _('delete'), e])

		if self['dnsEntryZoneReverse']:
			for dnsEntryZoneReverse in self['dnsEntryZoneReverse']:
				dn, ip = self.__split_dns_line( dnsEntryZoneReverse )
				try:
					self.__remove_dns_reverse_object( self[ 'name' ], dn , ip )
				except Exception,e:
					self.exceptions.append([_('DNS reverse zone'), _('delete'), e])

		if self['dhcpEntryZone']:
			for dhcpEntryZone in self['dhcpEntryZone']:
				dn, ip, mac = self.__split_dns_line( dhcpEntryZone )
				try:
					self.__remove_from_dhcp_object( dn, self[ 'name' ],  None, mac )
				except Exception,e:
					self.exceptions.append([_('DHCP'), _('delete'), e])

		if self['dnsEntryZoneAlias']:
			for entry in self['dnsEntryZoneAlias']:
				dnsForwardZone, dnsAliasZoneContainer, alias = entry
				try:
					self.__remove_dns_alias_object( self[ 'name' ], dnsForwardZone, dnsAliasZoneContainer, alias )
				except Exception,e:
					self.exceptions.append([_('DNS Alias'), _('delete'), e])

	def __setitem__(self, key, value):
		raise_after = None
		if key == 'network':
			if self.old_network != value:
				if value and value != 'None':
					network_object=univention.admin.handlers.networks.network.object(self.co, self.lo, self.position, value)
					network_object.open()

					if not self['ip'] or len( self['ip'] ) < 1 or not self['ip'][ 0 ] or  not univention.admin.ipaddress.ip_is_in_network(network_object['network'],
													     network_object['netmask'], self['ip'][ 0 ]):
						if self.ip_freshly_set:
							raise_after = univention.admin.uexceptions.ipOverridesNetwork
						else:
							#get next IP
							if not network_object['nextIp']:
								network_object.stepIp()

							IpAddr=''
							FirstIp=''		#to prevent an endless loop
							while not IpAddr:
								self['ip']=network_object['nextIp']
								if not FirstIp:
									FirstIp=self['ip']
								else:
									if FirstIp == self['ip']:
										#next free IP Address not found
										raise univention.admin.uexceptions.nextFreeIp

								if not self['ip']:
									raise univention.admin.uexceptions.nextFreeIp
									return

								if '.' in self['ip'][0] and self['ip'][0].split('.')[-1] in ["0", "1", "254"]:
									network_object.stepIp()
									network_object.modify()
									continue

								network_object.stepIp()
								network_object.modify()
								try:
									IpAddr=univention.admin.allocators.request(self.lo, self.position, 'aRecord', value=self['ip'][ 0 ])
									self.ip_alredy_requested=1
									self.alloc.append(('aRecord',IpAddr))
									self.ip=IpAddr
								except:
									pass

						self.network_object = network_object
					if network_object['dnsEntryZoneForward']:
						if self.has_key( 'ip' ) and self[ 'ip' ] and len( self[ 'ip' ]) == 1:
							self[ 'dnsEntryZoneForward' ] = [ [ network_object['dnsEntryZoneForward'], self[ 'ip' ][ 0 ] ], ]
					if network_object['dnsEntryZoneReverse']:
						if self.has_key( 'ip' ) and self[ 'ip' ] and len( self[ 'ip' ]) == 1:
							self['dnsEntryZoneReverse'] = [ [ network_object['dnsEntryZoneReverse'], self[ 'ip' ][ 0 ] ], ]
					if network_object['dhcpEntryZone']:
						if self.has_key( 'ip' ) and self[ 'ip' ] and len( self[ 'ip' ]) == 1 and self.has_key('mac') and self[ 'mac' ] and len( self[ 'mac' ] ) == 1:
							self[ 'dhcpEntryZone' ] = [ [ network_object['dhcpEntryZone'], self[ 'ip' ][ 0 ], self[ 'mac' ][ 0 ] ], ]
						else:
							self.__saved_dhcp_entry = network_object['dhcpEntryZone']

					self.old_network=value
				else:
					pass


		elif key == 'ip':
			self.ip_freshly_set = True
			if not self.ip or self.ip != value:
				if self.ip_alredy_requested:
					univention.admin.allocators.release(self.lo, self.position, 'aRecord', self.ip)
					self.ip_alredy_requested=0
				if value and self.network_object:
					if self.network_object['dnsEntryZoneForward']:
						if self.has_key( 'ip' ) and self[ 'ip' ] and len( self[ 'ip' ]) == 1:
							self[ 'dnsEntryZoneForward' ] = [ [ self.network_object['dnsEntryZoneForward'], self[ 'ip' ][ 0 ] ], ]
					if self.network_object['dnsEntryZoneReverse']:
						if self.has_key( 'ip' ) and self[ 'ip' ] and len( self[ 'ip' ]) == 1:
							self['dnsEntryZoneReverse'] = [ [ self.network_object['dnsEntryZoneReverse'], self[ 'ip' ][ 0 ] ] ]
					if self.network_object['dhcpEntryZone']:
						if self.has_key( 'ip' ) and self[ 'ip' ] and len( self[ 'ip' ]) == 1 and self.has_key('mac') and self[ 'mac' ] and len( self[ 'mac' ] ) > 0:
							self['dhcpEntryZone'] = [ [ self.network_object['dhcpEntryZone'], self[ 'ip' ][ 0 ], self[ 'mac' ][ 0 ] ], ]
						else:
							self.__saved_dhcp_entry = self.network_object['dhcpEntryZone']
			if not self.ip or self.ip == None:
				self.ip_freshly_set = False

		elif key == 'mac' and self.__saved_dhcp_entry:
			if self.has_key( 'ip' ) and self[ 'ip' ] and len( self[ 'ip' ]) == 1 and self[ 'mac' ] and len( self[ 'mac' ] ) > 0:
				if type( value ) == type( [ ] ):
					self['dhcpEntryZone'] = [ [ self.__saved_dhcp_entry, self[ 'ip' ][ 0 ], value[ 0 ] ], ]
				else:
					self['dhcpEntryZone'] = [ [ self.__saved_dhcp_entry, self[ 'ip' ][ 0 ], value ], ]

		super(simpleComputer, self).__setitem__(key, value)
		if raise_after:
			raise raise_after

class simpleLdapSub(simpleLdap):

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		base.__init__(self, co, lo, position, dn, superordinate )

	def _create(self):
		self._modify()

	def _remove(self, remove_childs=0):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,'_remove() called')
		if hasattr(self,"_ldap_pre_remove"):
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,'_ldap_pre_remove() called')
			self._ldap_pre_remove()

		ml=self._ldap_dellist()
		self.lo.modify(self.dn, ml)

		if hasattr(self,"_ldap_post_remove"):
			self._ldap_post_remove()

class simplePolicy(simpleLdap):
	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):

		self.resultmode=0
		self.dn=dn

		if not hasattr(self, 'cloned'):
			self.cloned=None

		if not hasattr(self, 'changes'):
			self.changes=0

		if not hasattr(self, 'policy_attrs'):
			self.policy_attrs={}

		if not hasattr(self, 'referring_object_dn'):
			self.referring_object_dn=None

		simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes )

		# append attribute and layout information for a list of objects
		# referencing this policy (if it exists)
		self.layout = copy.copy( univention.admin.modules.layout( self.module ) )
		self.__add_reference_list()

	def __add_reference_list( self ):
		if self.dn:
			# create syntax object
			ldap_search = univention.admin.syntax.LDAP_Search(
				filter = '(&(objectClass=univentionPolicyReference)(univentionPolicyReference=%s))' % self.dn,
				viewonly = True )

			# create property
			prop = univention.admin.property( \
				short_description = '',
				long_description = '',
				syntax = ldap_search,
				multivalue = 1,
				dontsearch = 1,
				required = 0,
				may_change = 0,
				identifies = 0 )

			# add property to list
			self.descriptions[ '_view_referencing_objects' ] = prop

			# add property to layout
			tab = Tab( _( 'Referencing objects' ), _( 'Objects referencing this policy object' ),
					   layout = [ '_view_referencing_objects' ] )
			self.layout.append( tab )
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'simplePolicy.__add_reference_list: appended tab with referencing objects' )
		else:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'simplePolicy.__add_reference_list: No object DN set!' )

	def copyIdentifier(self, from_object):
		"""Activate the result mode and set the referring object"""

		self.resultmode=1
		for key, property in from_object.descriptions.items():
			if property.identifies:
				for key2, property2 in self.descriptions.items():
					if property2.identifies:
						self.info[key2]=from_object.info[key]
		self.referring_object_dn=from_object.dn
		if not self.referring_object_dn:
			self.referring_object_dn=from_object.position.getDn()
		self.referring_object_position_dn=from_object.position.getDn()

	def clone (self, referring_object ):
		"""Marks the object as a not existing one containing values
		retrieved by evaluating the policies for the given object"""

		self.cloned = self.dn
		self.dn = ''
		self.copyIdentifier( referring_object )

	def getIdentifier(self):
		for key, property in self.descriptions.items():
			if property.identifies and key in self.info and self.info[ key ]:
				return key

	def __makeUnique(self):
		_d=univention.debug.function('admin.handlers.simplePolicy.__makeUnique')
		identifier=self.getIdentifier()
		components=self.info[identifier].split("_uv")
		if len(components) > 1:
			try:
				n=int(components[1])
				n+=1
			except ValueError:
				n=1
		else:
			n=0
		self.info[identifier]="%s_uv%d" % (components[0], n)
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'simplePolicy.__makeUnique: result: %s' % self.info[identifier])

	def create(self):
		if not self.resultmode:
			simpleLdap.create(self)
			return

		self._exists = False
		try:
			self.oldinfo={}
			simpleLdap.create(self)
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'simplePolicy.create: created object: info=%s' % (self.info))
		except univention.admin.uexceptions.objectExists, dn:
			self.__makeUnique()
			self.create()

	def policy_result( self, faked_policy_reference = None ):
		"""This method retrieves the policy values currently effective
		for this object. If the 'resultmode' is not active the evaluation
		is cancelled.

		If faked_policy_reference is given at the top object
		(referring_object_dn) this policy object temporarily referenced"""

		if not self.resultmode:
			return

		self.polinfo_more={}
		if not self.policy_attrs:
			policies = []
			if faked_policy_reference:
				policies.append( faked_policy_reference )

			# the referring object does not exist yet
			if not self.referring_object_dn == self.referring_object_position_dn:
				result = self.lo.getPolicies( self.lo.parentDn( self.referring_object_dn ), policies = policies )
			else:
				result = self.lo.getPolicies( self.referring_object_position_dn, policies = policies )
			for policy_oc, attrs in result.items():
				if univention.admin.objects.ocToType(policy_oc) == self.module:
					self.policy_attrs=attrs

		if hasattr( self, '_custom_policy_result_map' ):
			self._custom_policy_result_map()
		else:
			values = {}
			for attr_name, value_dict in self.policy_attrs.items():
				values[ attr_name ] = value_dict[ 'value' ]
				self.polinfo_more[ self.mapping.unmapName( attr_name ) ] = value_dict

			self.polinfo = univention.admin.mapping.mapDict( self.mapping, values )
			self.polinfo = self._post_unmap( self.polinfo, values )

	def __getitem__(self, key):
		if not self.resultmode:
			if self.has_key('emptyAttributes') and self.mapping.mapName(key) and self.mapping.mapName(key) in simpleLdap.__getitem__(self,'emptyAttributes'):
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'simplePolicy.__getitem__: empty Attribute %s'%key)
				if self.descriptions[key].multivalue:
					return []
				else:
					return ''
			return simpleLdap.__getitem__(self, key)

		dict={}
		self.policy_result()

		if ( key in self.polinfo and not ( key in self.info or key in self.oldinfo ) ) or ( key in self.polinfo_more and 'fixed' in self.polinfo_more[ key ] and self.polinfo_more[ key ][ 'fixed' ] ):
			if self.descriptions[key].multivalue and not type(self.polinfo[key]) == types.ListType:
				# why isn't this correct in the first place?
				self.polinfo[key]=[self.polinfo[key]]
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'simplePolicy.__getitem__: presult: %s=%s' % (key, self.polinfo[key]))
			return self.polinfo[key]

		result=simpleLdap.__getitem__(self, key)
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'simplePolicy.__getitem__: result: %s=%s' % (key, result))
		return result

	def fixedAttributes(self):
		'''return effectively fixed attributes. '''

		if not self.resultmode:
			return {}

		fixed_attributes={}
		if not self.policy_attrs:
			if not self.referring_object_dn == self.referring_object_position_dn:
				result=self.lo.getPolicies(self.lo.parentDn(self.referring_object_dn))
			else:
				result=self.lo.getPolicies(self.referring_object_position_dn)
			for key, value in result.items():
				if univention.admin.objects.ocToType(key) == self.module:
					self.policy_attrs=value

		for attr_name, value_dict in self.policy_attrs.items():
			if value_dict.has_key( 'fixed' ):
				fixed_attributes[self.mapping.unmapName(attr_name)]=value_dict['fixed']
			else:
				fixed_attributes[self.mapping.unmapName(attr_name)]=0

		return fixed_attributes

	def emptyAttributes(self):
		'''return effectively empty attributes. '''

		empty_attributes={}

		if self.has_key('emptyAttributes'):
			for attrib in simpleLdap.__getitem__(self,'emptyAttributes'):
				empty_attributes[self.mapping.unmapName(attrib)]=1

		return empty_attributes

	def __setitem__(self, key, newvalue):
		if not self.resultmode:
			simpleLdap.__setitem__(self, key, newvalue)
			return

		dict={}
		self.policy_result()

		if self.polinfo.has_key(key):

			if self.polinfo[key] != newvalue or self.polinfo_more[key]['policy'] == self.cloned or ( self.info.has_key( key ) and self.info[ key ] != newvalue ):
				if self.polinfo_more[key]['fixed'] and self.polinfo_more[key]['policy'] != self.cloned:
					raise univention.admin.uexceptions.policyFixedAttribute, key
				simpleLdap.__setitem__(self, key, newvalue)
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'polinfo: set key %s to newvalue %s' % (key,newvalue) )
				if self.hasChanged(key):
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'polinfo: key:%s hasChanged' % (key) )
					self.changes=1
				return
			else:
				return

		# this object did not exist before
		if not self.oldinfo:
			# if this attribute is of type boolean and the new value is equal to the default, than ignore this "change"
			if isinstance( self.descriptions[ key ].syntax, univention.admin.syntax.boolean ):
				if self.descriptions.has_key( key ):
					default = self.descriptions[ key ].base_default
					if type( self.descriptions[ key ].base_default ) in ( tuple, list ):
						default = self.descriptions[ key ].base_default[ 0 ]
					if ( not default and newvalue == '0' ) or default == newvalue:
						return

		simpleLdap.__setitem__(self, key, newvalue)
		if self.hasChanged(key):
			self.changes=1
