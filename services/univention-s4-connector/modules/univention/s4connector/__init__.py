#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Basic class for the UCS connector part
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

import sys, codecs, base64, string, os, cPickle, types, random, traceback, copy, time
import ldap
import pdb
import univention_baseconfig
import univention.uldap
import univention.admin.uldap
import univention.admin.modules
import univention.admin.objects
import univention.debug2 as ud
import base64
from signal import *
term_signal_caught = False

import sqlite3 as lite

univention.admin.modules.update()

# update choices-lists which are defined in LDAP
univention.admin.syntax.update_choices()


# util functions defined during mapping

def make_lower(mlValue):
	'''
	lower string cases for mlValue which can be string or a list of values which can be given to mlValue
	'''
	if hasattr(mlValue,'lower'):
		return mlValue.lower()
	if type(mlValue) == type([]):
		return [make_lower(x) for x in mlValue]
	return mlValue
									
def set_ucs_passwd_user(s4connector, key, ucs_object):
	'''
	set random password to fulfill required values
	'''
	ucs_object['password'] = str(int(random.random()*100000000))*8 # at least 8 characters

def check_ucs_lastname_user(s4connector, key, ucs_object):
	'''
	check if required values for lastname are set
	'''
	if not ucs_object.has_key('lastname') or not ucs_object['lastname']:
		ucs_object['lastname'] = 'none'

def set_primary_group_user(s4connector, key, ucs_object):
	'''
	check if correct primary group is set
	'''
	s4connector.set_primary_group_to_ucs_user(key, ucs_object)

# compare functions

# helper
def dictonary_lowercase(dict):
	if type(dict) == type({}):
		ndict={}
		for key in dict.keys():
			ndict[key]=[]
			for val in dict[key]:
				ndict[key].append(val.lower())
		return ndict
	elif type(dict) == type([]):
		nlist=[]
		for d in dict:
			nlist.append(d.lower())
		return nlist
	else:
		try: # should be string
			return dict.lower()
		except (ldap.SERVER_DOWN, SystemExit):
			raise
		except: # FIXME: which exception is to be caught?
			pass

def compare_lowercase(val1, val2):
	try: # TODO: failes if conversion to ascii-str raises exception
		if dictonary_lowercase(val1) == dictonary_lowercase(val2):
			return True
		else:
			return False
	except (ldap.SERVER_DOWN, SystemExit):
		raise
	except: # FIXME: which exception is to be caught?
		return False

# helper classes
class configdb:
	def __init__ (self, filename):
		self.filename = filename
		self._dbcon = lite.connect(self.filename)

	def get(self, section, option):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				cur.execute("SELECT value FROM '%s' WHERE key='%s'" % (section, option))
				self._dbcon.commit()
				rows = cur.fetchall()
				cur.close()
				if rows:
					return rows[0][0]
				return ''
			except lite.Error, e:
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = lite.connect(self.filename)
		

	def set(self, section, option, value):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				cur.execute("""
		INSERT OR REPLACE INTO '%(table)s' (key,value) 
			VALUES (  '%(key)s', '%(value)s'
		);""" % {'key': option, 'value': value, 'table': section})
				self._dbcon.commit()
				cur.close()
				return 
			except lite.Error, e:
				ud.debug(ud.LDAP, ud.WARN, "sqlite: %s" % e)
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = lite.connect(self.filename)

	def items(self, section):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				cur.execute("SELECT * FROM '%s'" % (section))
				self._dbcon.commit()
				rows = cur.fetchall()
				cur.close()
				return rows
			except lite.Error, e:
				ud.debug(ud.LDAP, ud.WARN, "sqlite: %s" % e)
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = lite.connect(self.filename)

	def remove_option(self, section, option):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				cur.execute("DELETE FROM '%s' WHERE key='%s'" % (section, option))
				self._dbcon.commit()
				cur.close()
				return
			except lite.Error, e:
				ud.debug(ud.LDAP, ud.WARN, "sqlite: %s" % e)
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = lite.connect(self.filename)

	def has_section(self, section):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='%s';" % section)
				self._dbcon.commit()
				rows = cur.fetchone()
				cur.close()
				if rows:
					return True
				else:
					return False
			except lite.Error, e:
				ud.debug(ud.LDAP, ud.WARN, "sqlite: %s" % e)
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = lite.connect(self.filename)
	
	def add_section(self, section):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				cur.execute("CREATE TABLE IF NOT EXISTS '%s'(Key TEXT PRIMARY KEY, Value TEXT)" % section)
				self._dbcon.commit()
				cur.close()
				return 
			except lite.Error, e:
				ud.debug(ud.LDAP, ud.WARN, "sqlite: %s" % e)
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = lite.connect(self.filename)
	
	def has_option(self, section, option):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				cur.execute("SELECT value FROM '%s' WHERE key='%s'" % (section, option))
				self._dbcon.commit()
				rows = cur.fetchall()
				cur.close()
				if rows:
					return True
				else:
					return False
			except lite.Error, e:
				ud.debug(ud.LDAP, ud.WARN, "sqlite: %s" % e)
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = lite.connect(self.filename)

class configsaver:
	def __init__ (self, filename):
		self.filename = filename
		try:
			f = file(filename,'r')
			self.config = cPickle.load(f)
		except IOError:
			self.config = {}
		except EOFError:
			self.config = {}

	def write(self, ignore=''):		
		def signal_handler(sig, frame):
			ud.debug(ud.LDAP, ud.INFO, "configsaver.write: SIGTERM caught")
			univention.s4connector.term_signal_caught = True

		signal(SIGTERM, signal_handler)

		f = file(self.filename,'w')
		cPickle.dump(self.config, f)
		f.flush()
		f.close()

		signal(SIGTERM, SIG_DFL)

		if univention.s4connector.term_signal_caught:
			ud.debug(ud.LDAP, ud.INFO, "configsaver.write: exit on SIGTERM")
			sys.exit(0)

	def get(self, section, option):
		try:
			return self.config[section][option]
		except KeyError:
			return ''

	def set(self, section, option, value):
		self.config[section][option] = value
		self.write()

	def items(self, section):
		ret = []
		for key in self.config[section].keys():
			ret.append((key,self.config[section][key]))
		return ret

	def remove_option(self, section, option):
		if self.config[section].has_key(option):
			self.config[section].pop(option)
		self.write()

	def has_section(self, section):
		return self.config.has_key(section)

	def add_section(self, section):
		self.config[section]={}
		self.write()
	
	def has_option(self, section, option):
		return self.config.has_key(section) and self.config[section].has_key(option)

class attribute:
	def __init__ ( self, ucs_attribute='', ldap_attribute='', con_attribute='', con_other_attribute='', required=0, compare_function='', mapping=(), reverse_attribute_check=False ):
		self.ucs_attribute=ucs_attribute
		self.ldap_attribute=ldap_attribute
		self.con_attribute=con_attribute
		self.con_other_attribute=con_other_attribute
		self.required=required
		self.compare_function=compare_function
		if mapping:
			self.mapping=mapping
		# Make a reverse check of this mapping. This is necassary if the attribute is
		# available in UCS and in AD but the mapping is not 1:1.
		# For example the homeDirectory attribute is in UCS and in AD, but the mapping is
		# from homeDirectory in AD to sambaHomePath in UCS. The homeDirectory in UCS is not
		# considered. 
		# Seee https://forge.univention.org/bugzilla/show_bug.cgi?id=25823
		self.reverse_attribute_check=reverse_attribute_check

class property:
	def __init__(	self, ucs_default_dn='', con_default_dn='', ucs_module='', ucs_module_others=[], sync_mode='', scope='', con_search_filter='', ignore_filter=None, match_filter=None, ignore_subtree=[],
					con_create_objectclass=[], con_create_attributes=[], dn_mapping_function=[], attributes=None, ucs_create_functions=[], post_con_create_functions=[],
					post_con_modify_functions=[], post_ucs_modify_functions=[], post_attributes=None, mapping_table=None, position_mapping=[], con_sync_function = None, ucs_sync_function = None, disable_delete_in_ucs = False,
					identify = None, con_subtree_delete_objects = [] ):

		self.ucs_default_dn=ucs_default_dn

		self.con_default_dn=con_default_dn

		self.ucs_module=ucs_module

		# allow a 1:n mapping, for example a Windows client
		# could be a computers/windows or a computers/memberserver
		# object
		self.ucs_module_others=ucs_module_others
		self.sync_mode=sync_mode

		self.scope=scope

		self.con_search_filter=con_search_filter
		self.ignore_filter=ignore_filter
		self.match_filter=match_filter
		self.ignore_subtree=ignore_subtree

		self.con_create_objectclass=con_create_objectclass
		self.con_create_attributes=con_create_attributes
		self.dn_mapping_function=dn_mapping_function
		self.attributes=attributes

		self.ucs_create_functions=ucs_create_functions

		self.post_con_create_functions=post_con_create_functions
		self.post_con_modify_functions=post_con_modify_functions
		self.post_ucs_modify_functions=post_ucs_modify_functions

		self.post_attributes=post_attributes
		self.mapping_table=mapping_table
		self.position_mapping=position_mapping

		if con_sync_function:
			self.con_sync_function = con_sync_function
		if ucs_sync_function:
			self.ucs_sync_function = ucs_sync_function

		self.con_subtree_delete_objects = con_subtree_delete_objects

		# Overwrite the identify function from the ucs modules, at least needed for dns
		if identify:
			self.identify = identify

		self.disable_delete_in_ucs = disable_delete_in_ucs

		pass
	
class ucs:
	def __init__(self, CONFIGBASENAME, _property, baseConfig, listener_dir):
		_d=ud.function('ldap.__init__')

		self.CONFIGBASENAME = CONFIGBASENAME

		self.ucs_no_recode=['krb5Key','userPassword','pwhistory','sambaNTPassword','sambaLMPassword', 'userCertificate']

		self.baseConfig=baseConfig
		self.property=_property

		self.init_debug()
		
		self.co=univention.admin.config.config()
		self.listener_dir=listener_dir

		configdbfile='/etc/univention/%s/s4internal.sqlite' % self.CONFIGBASENAME
		self.config = configdb(configdbfile)

		configfile='/etc/univention/%s/s4internal.cfg' % self.CONFIGBASENAME
		if os.path.exists(configfile):
			ud.debug(ud.LDAP, ud.PROCESS, "Converting %s into a sqlite database" % configfile)
			config = configsaver(configfile)
			ud.debug(ud.LDAP, ud.INFO, "Sections to convert: %s" % config.config.keys())
			for section in config.config.keys():
				ud.debug(ud.LDAP, ud.PROCESS, "Converting section %s" % section)
				self.config.add_section(section)
				for key in config.config[section].keys():                                                                                                                                                  
					ud.debug(ud.LDAP, ud.INFO, "Adding key: %s" % key)
					self.config.set(section, key, config.get(section, key))

			new_file='%s_converted_%f' % (configfile,time.time())
			os.rename(configfile, new_file)
			ud.debug(ud.LDAP, ud.PROCESS, "Converting done")
		
		self.open_ucs()

		for section in ['DN Mapping UCS','DN Mapping CON','UCS rejected']:
			if not self.config.has_section(section):
				self.config.add_section(section)				

		ud.debug(ud.LDAP, ud.INFO, "init finished")

	def __del__(self):
		self.close_debug()

	def open_ucs( self ):
		bindpw_file = self.baseConfig.get('%s/ldap/bindpw' % self.CONFIGBASENAME, '/etc/ldap.secret')
		binddn = self.baseConfig.get('%s/ldap/binddn' % self.CONFIGBASENAME, 'cn=admin,'+self.baseConfig['ldap/base'])
		bindpw=open(bindpw_file).read()
		if bindpw[-1] == '\n':
			bindpw=bindpw[0:-1]

		host = self.baseConfig.get('%s/ldap/server' % self.CONFIGBASENAME, self.baseConfig.get('ldap/master'))

		try:
			port = int(self.baseConfig.get('%s/ldap/port' % self.CONFIGBASENAME, self.baseConfig.get('ldap/master/port')))
		except:
			port = 7389

		self.lo=univention.admin.uldap.access(host=host, port=port, base=self.baseConfig['ldap/base'], binddn=binddn, bindpw=bindpw, start_tls=2, follow_referral=True)

	def search_ucs( self, filter = '(objectClass=*)', base = '', scope = 'sub', attr = [], unique = 0, required = 0, timeout = -1, sizelimit = 0 ):
		try:
			result = self.lo.search( filter = filter, base = base, scope = scope, attr = attr, unique = unique, required = required, timeout = timeout, sizelimit = sizelimit )
			return result
		except univention.admin.uexceptions.ldapError, search_exception:
			ud.debug( ud.LDAP, ud.INFO, 'Lost connection to the LDAP server. Trying to reconnect ...' )
			try:
				self.open_ucs()
			except ldap.SERVER_DOWN, e:
				ud.debug( ud.LDAP, ud.INFO, 'LDAP-Server seems to be down' )
				raise search_exception
					
				
	def init_debug(self):
		_d=ud.function('ldap.init_debug')
		if self.baseConfig.has_key('%s/debug/function' % self.CONFIGBASENAME):
			try:
				function_level=int(self.baseConfig['%s/debug/function' % self.CONFIGBASENAME])
			except (ldap.SERVER_DOWN, SystemExit):
				raise
			except: # FIXME: which exception is to be caught?
				function_level = 0
		else:
			function_level=0
		ud.init('/var/log/univention/%s-s4.log' % self.CONFIGBASENAME, 1, function_level)
		if self.baseConfig.has_key('%s/debug/level' % self.CONFIGBASENAME):
			debug_level=self.baseConfig['%s/debug/level' % self.CONFIGBASENAME]
		else:
			debug_level=2
		ud.set_level(ud.LDAP, int(debug_level))

	def close_debug(self):
		_d=ud.function('ldap.close_debug')
		ud.debug(ud.LDAP, ud.INFO, "close debug")

	def _get_config_option(self, section, option):
		_d=ud.function('ldap._get_config_option')
		return self.config.get(section,option)

	def _set_config_option(self, section, option, value):
		_d=ud.function('ldap._set_config_option')
		self.config.set(section,option, value)

	def _remove_config_option(self, section, option):
		_d=ud.function('ldap._remove_config_option')
		self.config.remove_option(section, option)

	def _get_config_items(self, section):
		_d=ud.function('ldap._get_config_items')
		return self.config.items(section)
	
	def _save_rejected_ucs(self, filename, dn):
		_d=ud.function('ldap._save_rejected_ucs')
		self._set_config_option('UCS rejected',filename,dn)

	def _get_rejected_ucs(self, filename):
		_d=ud.function('ldap._get_rejected_ucs')
		return self._get_config_option('UCS rejected',filename)

	def _remove_rejected_ucs(self,filename):
		_d=ud.function('ldap._remove_rejected_ucs')
		self._remove_config_option('UCS rejected',filename)

	def _list_rejected_ucs(self):
		_d=ud.function('ldap._list_rejected_ucs')
		result = []
		for i in self._get_config_items('UCS rejected'):
			result.append(i)
		return result

	def _list_rejected_filenames_ucs(self):
		_d=ud.function('ldap._list_rejected_filenames_ucs')
		result = []
		for filename, dn in self._get_config_items('UCS rejected'):
			result.append(filename)
		return result

	def list_rejected_ucs(self):
		return self._get_config_items('UCS rejected')
		
	def _encode_dn_as_config_option(self, dn):
		return dn

	def _decode_dn_from_config_option(self, dn):
		return dn

	def _set_dn_mapping(self, dn_ucs, dn_con):
		_d=ud.function('ldap._set_dn_mapping')
		self._set_config_option('DN Mapping UCS',
					self._encode_dn_as_config_option(dn_ucs.lower()),
					self._encode_dn_as_config_option(dn_con.lower()))
		self._set_config_option('DN Mapping CON',
					self._encode_dn_as_config_option(dn_con.lower()),
					self._encode_dn_as_config_option(dn_ucs.lower()))

	def _remove_dn_mapping(self, dn_ucs, dn_con):
		_d=ud.function('ldap._remove_dn_mapping')
		# delete all if mapping failed in the past
		dn_con_mapped = self._get_dn_by_ucs(dn_ucs.lower())
		dn_ucs_mapped = self._get_dn_by_con(dn_con.lower())
		dn_con_re_mapped = self._get_dn_by_ucs(dn_ucs_mapped.lower())
		dn_ucs_re_mapped = self._get_dn_by_con(dn_con_mapped.lower())
		
		for ucs, con in [(dn_ucs, dn_con), (dn_ucs_mapped, dn_con_mapped), (dn_ucs_re_mapped, dn_con_re_mapped)]:
			if con:
				self._remove_config_option('DN Mapping CON',
							   self._encode_dn_as_config_option(con.lower()))
			if ucs:
				self._remove_config_option('DN Mapping UCS',
							   self._encode_dn_as_config_option(ucs.lower()))

	def _get_dn_by_ucs(self, dn_ucs):
		_d=ud.function('ldap._get_dn_by_ucs')
		return self._decode_dn_from_config_option(self._get_config_option('DN Mapping UCS', self._encode_dn_as_config_option(dn_ucs.lower())))

	def get_dn_by_ucs(self, dn_ucs):
		if not dn_ucs:
			return dn_ucs
		return 	self._get_dn_by_ucs(dn_ucs)

	def _get_dn_by_con(self, dn_con):
		_d=ud.function('ldap._get_dn_by_con')
		if not dn_con:
			return dn_con
		return self._decode_dn_from_config_option(self._get_config_option('DN Mapping CON', self._encode_dn_as_config_option(dn_con.lower())))

	def get_dn_by_con(self, dn_con):
		return 	self._get_dn_by_con(dn_con)

	def _check_dn_mapping(self, dn_ucs, dn_con):
		_d=ud.function('ldap._check_dn_mapping')
		dn_con_mapped = self._get_dn_by_ucs(dn_ucs.lower())
		dn_ucs_mapped = self._get_dn_by_con(dn_con.lower())
		if dn_con_mapped != dn_con.lower() or dn_ucs_mapped != dn_ucs.lower():
			self._remove_dn_mapping(dn_ucs.lower(), dn_con_mapped.lower())
			self._remove_dn_mapping(dn_ucs_mapped.lower(), dn_con.lower())
			self._set_dn_mapping(dn_ucs.lower(), dn_con.lower())

	def _list_dn_mappings(self, config_space):
		ret =[]
		for d1, d2 in self._get_config_items(config_space):
			return_update = False
			count = 0
			while not return_update and count<3:
				try:
					ret.append((self._decode_dn_from_config_option(d1),self._decode_dn_from_config_option(self._get_config_option(config_space, d1))))
					return_update = True
				except (ldap.SERVER_DOWN, SystemExit):
					raise				
				except: # FIXME: which exception is to be caught?
					count = count + 1
					d1=d1+" ="
			ret.append(("failed",self._decode_dn_from_config_option(d1)))
		return ret

	def list_dn_mappings_by_con(self):
		return self._list_dn_mappings('DN Mapping CON')

	def list_dn_mappings_by_ucs(self):
		return self._list_dn_mappings('DN Mapping UCS')


	def _debug_traceback(self, level, text):
		'''
		print traceback with ud.debug, level is i.e. ud.INFO
		'''
		_d=ud.function('ldap._debug_traceback')
		exc_info = sys.exc_info()

		ud.debug(ud.LDAP, level, text)
		ud.debug(ud.LDAP, level, traceback.format_exc())


	def _get_rdn(self,dn):
		_d=ud.function('ldap._get_rdn')
		'''
		return rdn from dn
		'''
		return dn.split(',',1)[0]

	def _get_subtree(self,dn):
		_d=ud.function('ldap._get_subtree')
		'''
		return subtree from dn
		'''
		return dn.split(',',1)[1]

	def __sync_file_from_ucs(self, filename, append_error='', traceback_level=ud.WARN):
		_d=ud.function('ldap._sync_file_from_ucs')
		'''
		sync changes from UCS stored in given file
		'''
		try:
			f=file(filename,'r')
		except IOError: # file not found so there's nothing to sync
			return True
			
		dn,new,old,old_dn=cPickle.load(f)

		def recode_attribs(attribs):
			nattribs={}
			for key in attribs.keys():
				if key in self.ucs_no_recode:
					nattribs[key] = attribs[key]
				else:
					try:
						nvals = []
						for val in attribs[key]:
							nvals.append(unicode(val,'utf8'))
						nattribs[unicode(key,'utf8')]=nvals
					except UnicodeDecodeError:
						nattribs[key] = attribs[key]

			return nattribs
		new = recode_attribs(new)
		old = recode_attribs(old)

		key=None

		# if the object was moved into a ignored tree
		# we should delete this object
		ignore_subtree_match = False
		
		if not new:
			change_type="delete"
			ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: objected was deleted")
			for k in self.property.keys():
				if self.modules[k].identify(unicode(dn,'utf8'), old):
					key=k
					break
				elif self.modules_others[k]:
					for m in self.modules_others[k]:
						if m.identify(unicode(dn,'utf8'), old):
							key=k
							break
				if key:
					break
		else:
			for k in self.property.keys():
				if self.modules[k].identify(unicode(dn,'utf8'), new):
					key=k
					break
				elif self.modules_others[k]:
					for m in self.modules_others[k]:
						if m.identify(unicode(dn,'utf8'), new):
							key=k
							break
				if key:
					break
				
			#ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: old: %s" % old)
			#ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: new: %s" % new)
			if old and new:
				change_type = "modify"
				ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: objected was modified")
				if old_dn and not old_dn == dn:
					ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: objected was moved")
					# object was moved
					new_object = { 'dn': unicode(dn,'utf8'), 'modtype': change_type, 'attributes': new}
					old_object = { 'dn': unicode(old_dn,'utf8'), 'modtype': change_type, 'attributes': old}
					if self._ignore_object(key, new_object):
						# moved into ignored subtree, delete:
						ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: moved object is now ignored, will delete it")
						change_type = 'delete'
						ignore_subtree_match = True
					
					if self._ignore_object(key, old_object):
						# moved from ignored subtree, add:
						ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: moved object was ignored, will add it")
						change_type = 'add'
				
			else:
				object = { 'dn': unicode(dn,'utf8'), 'modtype': 'modify', 'attributes': new}
				try:
					if self._ignore_object(key, object):
						ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: new object is ignored, nothing to do")
						change_type = 'modify'
						ignore_subtree_match = True
						return True
					else:
						if old_dn and not old_dn == dn:
							change_type="modify"
							ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: objected was moved")
						else:
							change_type="add"
							old_dn = '' # there may be an old_dn if object was moved from ignored container
							ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: objected was added: %s" % dn)
				except (ldap.SERVER_DOWN, SystemExit):
					raise
				except:
					# the ignore_object method might throw an exception if the subschema will be synced
					change_type="add"
					old_dn = '' # there may be an old_dn if object was moved from ignored container
					ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: objected was added: %s" % dn)

		if key:
			if change_type == 'delete':
				if old_dn:
					object = { 'dn': unicode(old_dn,'utf8'), 'modtype': change_type, 'attributes': old}
				else:
					object = { 'dn': unicode(dn,'utf8'), 'modtype': change_type, 'attributes': old}
			else:
				object = { 'dn': unicode(dn,'utf8'), 'modtype': change_type, 'attributes': new}

			if change_type == 'modify' and old_dn:
				object['olddn'] = unicode(old_dn, 'utf8') # needed for correct samaccount-mapping

			if not self._ignore_object(key,object) or ignore_subtree_match:
				premapped_ucs_dn = object['dn']
				object = self._object_mapping(key, object, 'ucs')
				if not self._ignore_object(key,object) or ignore_subtree_match:
					ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: finished mapping")
					try:				
						if ((old_dn and not self.sync_from_ucs(key, object, premapped_ucs_dn, unicode(old_dn,'utf8'), old))
							or (not old_dn and not self.sync_from_ucs(key, object, premapped_ucs_dn, old_dn, old))):
							self._save_rejected_ucs(filename, dn)
							return False
						else:
							return True
					except (ldap.SERVER_DOWN, SystemExit):
						raise
					except ldap.NO_SUCH_OBJECT:
						self._save_rejected_ucs(filename, dn)
						if traceback_level == ud.INFO:
							self._debug_traceback(traceback_level, "The sync failed. This could be because the parent object does not exist. This object will be synced in next sync step.")
						else:
							self._debug_traceback(traceback_level, "sync failed, saved as rejected")
						return False
					except:
						self._save_rejected_ucs(filename, dn)
						self._debug_traceback(traceback_level, "sync failed, saved as rejected")
						return False
				else:
					return True
			else:
				return True
		else:				
			ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: No mapping was found for dn: %s" % dn)
			return True

	def get_ucs_ldap_object(self, dn):
		_d=ud.function('ldap.get_ucs_ldap_object')

		if type(dn) == type(u''):
			searchdn = dn
		else:
			searchdn = unicode(dn)
		try:			
			return self.lo.get(searchdn,required=1)
		except ldap.NO_SUCH_OBJECT:
			return None
		except ldap.INVALID_DN_SYNTAX:
			return None
		except ldap.INVALID_SYNTAX:
			return None

	def get_ucs_object(self, property_type, dn):
		_d=ud.function('ldap.get_ucs_object')
		ucs_object = None
		if type(dn) == type(u''):
			searchdn = dn
		else:
			searchdn = unicode(dn)
		try:
			if not self.get_ucs_ldap_object(searchdn): # fails if object doesn't exist
				ud.debug(ud.LDAP, ud.INFO,"get_ucs_object: object not found: %s"%searchdn)
				return None
			module = self.modules[property_type]
			ucs_object = univention.admin.objects.get(module, co='', lo=self.lo, position='', dn=searchdn) # does not fail if object doesn't exist
			ud.debug(ud.LDAP, ud.INFO,"get_ucs_object: object found: %s"%searchdn)
		except (ldap.SERVER_DOWN, SystemExit):
			raise
		except: # FIXME: which exception is to be caught?
			ud.debug(ud.LDAP, ud.INFO,"get_ucs_object: object search failed: %s"%searchdn)
			self._debug_traceback(ud.WARN, "get_ucs_object: failure was: \n\t")
			return None

		return ucs_object

	def initialize_ucs(self):
		_d=ud.function('ldap.initialize_ucs')
		print "--------------------------------------"
		print "Initialize sync from UCS"
		sys.stdout.flush()

		# load UCS Modules
		self.modules={}
		self.modules_others={}
		for key in self.property.keys():
			if self.property[key].ucs_module:
				self.modules[key]=univention.admin.modules.get(self.property[key].ucs_module)
				if hasattr(self.property[key], 'identify'):
					ud.debug(ud.LDAP, ud.INFO,"Override identify function for %s" % key)
					self.modules[key].identify = self.property[key].identify
			else:
				self.modules[key]=None

			self.modules_others[key]=[]
			if self.property[key].ucs_module_others:
				for m in self.property[key].ucs_module_others:
					self.modules_others[key].append(univention.admin.modules.get(m))
		
		# try to resync rejected changes
		self.resync_rejected_ucs()
		# call poll_ucs to sync
		self.poll_ucs()
		print "--------------------------------------"
		sys.stdout.flush()
		
	def initialize(self):
		# dummy
		pass

	def resync_rejected_ucs(self):
		'''
		tries to resync rejected changes from UCS
		'''
		_d=ud.function('ldap.resync_rejected_ucs')
		rejected = self._list_rejected_ucs()
		change_counter = 0
		print "--------------------------------------"
		print "Sync %s rejected changes from UCS" % len(rejected)
		sys.stdout.flush()

		if rejected:
			for filename, dn in rejected:
				ud.debug(ud.LDAP, ud.PROCESS, 'sync from ucs:   Resync rejected file: %s' % (filename))
				try:
					if self.__sync_file_from_ucs(filename, append_error=' rejected'):
						try:
							os.remove(os.path.join(filename))
						except OSError: # file not found
							pass
						self._remove_rejected_ucs(filename)
						change_counter += 1
				except (ldap.SERVER_DOWN, SystemExit):
					raise
				except: # FIXME: which exception is to be caught?
					self._save_rejected_ucs(filename, dn)
					self._debug_traceback(ud.WARN,
										  "sync failed, saved as rejected \n\t%s" % filename)

		print "restored %s rejected changes" % change_counter
		print "--------------------------------------"
		sys.stdout.flush()		

	def resync_rejected(self):
		# dummy
		pass

	def _generate_dn_list_from(self, files):
		'''
		Save all filenames in a dictonary with dn as key
		If more than one pickle file was created for one DN we could skip the first one
		'''
		if len(files) > 200:
			# Show an info if it takes some time
			ud.debug(ud.LDAP, ud.PROCESS, 'Scan all changes from UCS ...')
		self.dn_list = {}
		for listener_file in files:
			filename = os.path.join(self.listener_dir, listener_file)
			if not filename == "%s/tmp" % self.baseConfig['%s/s4/listener/dir' % self.CONFIGBASENAME]:
				if not filename in self.rejected_files:
					try:
						f=file(filename,'r')
					except IOError: # file not found so there's nothing to sync
						continue

					dn,new,old,old_dn=cPickle.load(f)
					if not self.dn_list.get(dn):
						self.dn_list[dn]=[filename]
					else:
						self.dn_list[dn].append(filename)

	def poll_ucs(self):
		'''
		poll changes from UCS: iterates over files exported by directory-listener module
		'''
		_d=ud.function('ldap.poll_ucs')
		# check for changes from ucs ldap directory

		change_counter = 0

		self.rejected_files = self._list_rejected_filenames_ucs()

		print "--------------------------------------"
		print "try to sync %s changes from UCS" % (len(os.listdir(self.listener_dir))-1)
		print "done:",
		sys.stdout.flush()
		done_counter = 0
		files = os.listdir(self.listener_dir)
		files.sort()

		# Create a dictonary with all DNs
		self._generate_dn_list_from(files)

		# We may dropped the parent object, so don't show the traceback in any case
		traceback_level = ud.WARN

		for listener_file in files:
			sync_successfull = False
			filename = os.path.join(self.listener_dir, listener_file)
			if not filename == "%s/tmp" % self.baseConfig['%s/s4/listener/dir' % self.CONFIGBASENAME]:
				if not filename in self.rejected_files:
					try:
						f=file(filename,'r')
					except IOError: # file not found so there's nothing to sync
						if self.dn_list.get(dn):
							self.dn_list[dn].remove(filename)
						continue

					dn,new,old,old_dn=cPickle.load(f)

					if len(self.dn_list.get(dn, [])) < 2 or not old or not new:
						# If the list contains more then one file, the DN will be synced later
						# But if the object was added or remoed, the synchonization is required
						for i in [0, 1]: # do it twice if the LDAP connection was closed
							try:
								sync_successfull = self.__sync_file_from_ucs(filename, traceback_level=traceback_level)
							except (ldap.SERVER_DOWN, SystemExit):
								# once again, ldap idletimeout ...
								if i == 0:
									self.open_ucs()
									continue
								raise
							except:
								self._save_rejected_ucs(filename, dn)
								# We may dropped the parent object, so don't show this warning
								self._debug_traceback(traceback_level, "sync failed, saved as rejected \n\t%s" % filename)					
							if sync_successfull:
								os.remove(os.path.join(self.listener_dir,listener_file))
								change_counter += 1
							break
					else:
						os.remove(os.path.join(filename))
						traceback_level = ud.INFO
						try:
							ud.debug(ud.LDAP, ud.PROCESS, 'Drop %s. The DN %s will synced later' % (filename, dn))
						except:
							ud.debug(ud.LDAP, ud.PROCESS, 'Drop %s. The object will synced later' % (filename))

					if self.dn_list.get(dn):
						self.dn_list[dn].remove(filename)

				done_counter += 1
				print "%s"%done_counter,
				sys.stdout.flush()

		print ""	
		
		self.rejected_files = self._list_rejected_filenames_ucs()
		
		if self.rejected_files:
			print "Changes from UCS: %s (%s saved rejected)" % (change_counter, len(self.rejected_files))
		else:
			print "Changes from UCS: %s (%s saved rejected)" % (change_counter, '0')
		print "--------------------------------------"
		sys.stdout.flush()
		return change_counter	

	def poll(self, show_deleted=True):
		# dummy
		pass

	def __set_values(self, property_type, object, ucs_object, modtype='modify'):
		_d=ud.function('ldap.__set_value')
		if not modtype == 'add':
			ucs_object.open()
		def set_values(attributes):
			if object['attributes'].has_key(attributes.ldap_attribute):
				ucs_key = attributes.ucs_attribute
				if ucs_key:
					value = object['attributes'][attributes.ldap_attribute]
					ud.debug(ud.LDAP, ud.INFO, '__set_values: set attribute, ucs_key: %s - value: %s' % (ucs_key,value))

					# check if ucs_key is an custom attribute
					detected_ca = False

					ucs_module = self.modules[property_type]
					position=univention.admin.uldap.position(self.lo.base)
					position.setDn(object['dn'])
					univention.admin.modules.init(self.lo,position,ucs_module)
					
					if hasattr(ucs_module, 'ldap_extra_objectclasses'):
						ud.debug(ud.LDAP, ud.INFO, '__set_values: module %s has custom attributes' % ucs_object.module)
						for oc, pname, syntax, ldapMapping, deleteValues, deleteObjectClass in ucs_module.ldap_extra_objectclasses:
							if ucs_key == ucs_module.property_descriptions[pname].short_description:
								ud.debug(ud.LDAP, ud.INFO, '__set_values: detected a custom attribute')
								detected_ca = True
								old_value = ''
								if modtype == 'modify':
									old_value_result = self.search_ucs(base=ucs_object.dn, attr=[ldapMapping])
									if len(old_value_result) >0 and old_value_result[0][1].has_key(ldapMapping):
										old_value = old_value_result[0][1][ldapMapping]
										
								if object.has_key('custom_attributes'):
									object['custom_attributes']['modlist'].append( (ldapMapping,old_value,value) )
								else:
									object['custom_attributes'] = {'modlist' : [(ldapMapping,old_value,value)], 'extraOC' : []}
								object['custom_attributes']['extraOC'].append(oc);
								ud.debug(ud.LDAP, ud.INFO, '__set_values: extended list of custom attributes: %s' % object['custom_attributes'])
								continue
					else:
						ud.debug(ud.LDAP, ud.INFO, '__set_values: module %s has no custom attributes' % ucs_object.module)

					if not detected_ca:					
						if type(value) == type(types.ListType()) and len(value) == 1:
							value = value[0]
						equal = False

						# set encoding
						compare=[ucs_object[ucs_key],value]
						for i in [0,1]:
							if type(compare[i]) == type([]):
								compare[i] = univention.s4connector.s4.compatible_list(compare[i])
							else:
								compare[i] = univention.s4connector.s4.compatible_modstring(compare[i])

						if attributes.compare_function != '':
							equal = attributes.compare_function(compare[0],compare[1])
						else:
							equal = compare[0] == compare[1]
						if not equal:
							ucs_object[ucs_key] = value
							ud.debug(ud.LDAP, ud.INFO,
											   "set key in ucs-object: %s" % ucs_key)
				else:
					ud.debug(ud.LDAP, ud.INFO, '__set_values: no ucs_attribute found in %s' % attributes)
			else:
				
				# prevent value resets of mandatory attributes
				mandatory_attrs = ['lastname']

				ucs_key = attributes.ucs_attribute
				if ucs_object.has_key(ucs_key):
					ucs_module = self.modules[property_type]
					position=univention.admin.uldap.position(self.lo.base)
					position.setDn(object['dn'])
					univention.admin.modules.init(self.lo,position,ucs_module)

					# Special handling for con other attributes, see Bug #20599
					if attributes.con_other_attribute:
						if object['attributes'].get(attributes.con_other_attribute):
							ucs_object[ucs_key] = object['attributes'].get(attributes.con_other_attribute)
							ud.debug(ud.LDAP, ud.INFO, '__set_values: no ldap_attribute defined in %s, we set the key %s in the ucs-object to con_other_attribute %s' % (attributes, ucs_key, attributes.con_other_attribute))
						elif ucs_key not in mandatory_attrs:
							ucs_object[ucs_key] = []
							ud.debug(ud.LDAP, ud.INFO, '__set_values: no ldap_attribute defined in %s, we unset the key %s in the ucs-object' % (attributes, ucs_key))
						else:
							ud.debug(ud.LDAP, ud.WARN, '__set_values: The attributes for %s have not been removed as it represents a mandatory attribute' % ucs_key)
					else:
						ud.debug(ud.LDAP, ud.INFO, '__set_values: no ldap_attribute defined in %s, we unset the key %s in the ucs-object' % (attributes, ucs_key))

						if ucs_key not in mandatory_attrs:
							ucs_object[ucs_key] = []
						else:
							ud.debug(ud.LDAP, ud.WARN, '__set_values: The attributes for %s have not been removed as it represents a mandatory attribute' % ucs_key)


		for attr_key in self.property[property_type].attributes.keys():
			set_values(self.property[property_type].attributes[attr_key])

		# post-values
		if not self.property[property_type].post_attributes:
			return
		for attr_key in self.property[property_type].post_attributes.keys():
			ud.debug(ud.LDAP, ud.INFO, '__set_values: mapping for attribute: %s' % attr_key)
			if hasattr(self.property[property_type].post_attributes[attr_key], 'mapping'):
				set_values(self.property[property_type].post_attributes[attr_key].mapping[1](self, property_type, object))
			else:
				if self.property[property_type].post_attributes[attr_key].reverse_attribute_check:
					if object['attributes'].get(self.property[property_type].post_attributes[attr_key].ldap_attribute):
						set_values(self.property[property_type].post_attributes[attr_key])
					else:
						ucs_object[self.property[property_type].post_attributes[attr_key].ucs_attribute] = ''
				else:
					set_values(self.property[property_type].post_attributes[attr_key])

	def __modify_custom_attributes(self, property_type, object, ucs_object, module, position, modtype = "modify"):
		if object.has_key('custom_attributes'):
			ud.debug(ud.LDAP, ud.INFO, '__modify_custom_attributes: custom attributes found: %s' % object['custom_attributes'])
			modlist = object['custom_attributes']['modlist']
			extraOC = object['custom_attributes']['extraOC']

			# set extra objectClasses
			if len(extraOC) > 0:
				oc = self.search_ucs(base = ucs_object.dn, scope='base', attr=['objectClass'])
				ud.debug(ud.LDAP, ud.INFO, '__modify_custom_attributes: should have extraOC %s, got %s' % (extraOC, oc))
				noc = []
				for i in range(len(oc[0][1]['objectClass'])):
					noc.append(oc[0][1]['objectClass'][i])

				for i in range(len(extraOC)):
					if extraOC[i] not in noc:
						noc.append(extraOC[i])

				if oc[0][1]['objectClass'] != noc:
					ud.debug(ud.LDAP, ud.INFO, '__modify_custom_attributes: modify objectClasses' )
					modlist.append(('objectClass',oc[0][1]['objectClass'],noc))

			ud.debug(ud.LDAP, ud.INFO, '__modify_custom_attributes: modlist: %s' % modlist)
			self.lo.modify(ucs_object.dn,modlist)
			
			return True
		else:
			ud.debug(ud.LDAP, ud.INFO, '__modify_custom_attributes: no custom attributes found')
			return True

	def add_in_ucs(self, property_type, object, module, position):
		_d=ud.function('ldap.add_in_ucs')
		ucs_object=module.object(None, self.lo, position=position)
		if property_type == 'group':
			ucs_object.open()
			self.group_members_cache_ucs[object['dn'].lower()] = []
		else:
			ucs_object.open()
		self.__set_values(property_type,object,ucs_object, modtype='add')
		for function in self.property[property_type].ucs_create_functions:
			function(self, property_type, ucs_object)
		return ucs_object.create() and self.__modify_custom_attributes(property_type, object, ucs_object, module, position)
		
	def modify_in_ucs(self, property_type, object, module, position):
		_d=ud.function('ldap.modify_in_ucs')
		module = self.modules[property_type]
		if object.has_key('olddn'):
			ucs_object=univention.admin.objects.get(module, None, self.lo, dn=object['olddn'], position='')
		else:
			ucs_object=univention.admin.objects.get(module, None, self.lo, dn=object['dn'], position='')
		self.__set_values(property_type,object,ucs_object)
		return ucs_object.modify() and self.__modify_custom_attributes(property_type, object, ucs_object, module, position)

	def move_in_ucs(self, property_type, object, module, position):
		_d=ud.function('ldap.move_in_ucs')
		module = self.modules[property_type]
		try:
			if object['olddn'].lower() == object['dn'].lower():
				ud.debug(ud.LDAP, ud.WARN,
						       "move_in_ucs: cancel move, old and new dn are the same ( %s to %s)"%(object['olddn'],object['dn']))
				return True
			else:
				ud.debug(ud.LDAP, ud.INFO,"move_in_ucs: move object from %s to %s"%(object['olddn'],object['dn']))
		except (ldap.SERVER_DOWN, SystemExit):
			raise
		except: # FIXME: which exception is to be caught?
			ud.debug(ud.LDAP, ud.INFO,"move_in_ucs: move object in UCS")			
		ucs_object = univention.admin.objects.get(module, None, self.lo, dn=object['olddn'], position='')
		ucs_object.open()
		ucs_object.move(object['dn'])
		return True

	def delete_in_ucs(self, property_type, object, module, position):
		_d=ud.function('ldap.delete_in_ucs')		

		if self.property[property_type].disable_delete_in_ucs:
			ud.debug(ud.LDAP, ud.PROCESS, "Delete of %s was disabled in mapping" % object['dn'])
			return True

		module = self.modules[property_type]
		ucs_object = univention.admin.objects.get(module, None, self.lo, dn=object['dn'], position='')

		try:
			ucs_object.open()
			ucs_object.remove()
			return True
		except Exception, e:
			ud.debug(ud.LDAP, ud.INFO,"delete object exception: %s"%e)
			if str(e) == "Operation not allowed on non-leaf": # need to delete subtree
				ud.debug(ud.LDAP, ud.INFO,"remove object from UCS failed, need to delete subtree")
				for result in self.search_ucs(base=object['dn']):
					if compare_lowercase(result[0], object['dn']):
						continue
					ud.debug(ud.LDAP, ud.INFO,"delete: %s"% result[0])
					subobject={'dn': result[0], 'modtype': 'delete', 'attributes': result[1]}
					key = None
					for k in self.property.keys():
						if self.modules[k].identify(result[0], result[1]):
							key=k
							break
					object_mapping = self._object_mapping(key, subobject, 'ucs')
					ud.debug(ud.LDAP, ud.WARN,"delete subobject: %s"% object_mapping['dn'])
					if not self._ignore_object(key,object_mapping):
						if not self.sync_to_ucs(key, subobject, object_mapping['dn']):
							try:
								ud.debug(ud.LDAP, ud.WARN,"delete of subobject failed: %s"% result[0])
							except (ldap.SERVER_DOWN, SystemExit):
								raise							
							except: # FIXME: which exception is to be caught?
								ud.debug(ud.LDAP, ud.WARN,"delete of subobject failed")
							return False


				return delete_in_ucs(property_type, object, module, position)
			elif str(e) == "noObject": #already deleted #TODO: check if it's really match
				return True
			else:
				raise

	def sync_to_ucs(self, property_type, object, premapped_s4_dn):
		_d=ud.function('ldap.sync_to_ucs')
		# this function gets an object from the s4 class, which should be converted into a ucs modul

		# if sync is write (sync to S4) or none, there is nothing to do
		if self.property[property_type].sync_mode in ['write', 'none']:
			ud.debug(ud.LDAP, ud.INFO, "sync_to_ucs ignored, sync_mode is %s" % self.property[property_type].sync_mode)
			return True

		if object.has_key('olddn'):
			old_object = self.get_ucs_object(property_type,object['olddn'])
		else:
			old_object = self.get_ucs_object(property_type,object['dn'])
		if old_object and object['modtype'] == 'add':
			object['modtype'] = 'modify'
		if not old_object and object['modtype'] == 'modify':
			object['modtype'] = 'add'
		if not old_object and object['modtype'] == 'move':
			object['modtype'] = 'add'

		if self.group_mapping_cache_ucs.get(object['dn'].lower()) and object['modtype'] != 'delete':
			ud.debug(ud.LDAP, ud.INFO, "sync_to_ucs: remove %s from group cache" % object['dn'])
			self.group_mapping_cache_ucs[object['dn'].lower()] = None

		try:
			ud.debug(ud.LDAP, ud.PROCESS,
							   'sync to ucs:   [%14s] [%10s] %s' % (property_type,object['modtype'], object['dn']))
		except (ldap.SERVER_DOWN, SystemExit):
			raise
		except: # FIXME: which exception is to be caught?
			ud.debug(ud.LDAP, ud.PROCESS,'sync to ucs...')
		
		module = self.modules[property_type]
		position=univention.admin.uldap.position(self.baseConfig['ldap/base'])

		ud.debug(ud.LDAP, ud.INFO,
				       'sync_to_ucs: set position to %s' % string.join( ldap.explode_dn( object['dn'] )[1:], "," ) )
		position.setDn( string.join( ldap.explode_dn( object['dn'] )[1:], "," ) ) 

		try:
			result = False
			if hasattr(self.property[property_type],"ucs_sync_function"):
				result = self.property[property_type].ucs_sync_function(self, property_type, object)
			else:
				if object['modtype'] == 'add':
					result = self.add_in_ucs(property_type, object, module, position)
					self._check_dn_mapping(object['dn'], premapped_s4_dn)
				if object['modtype'] == 'delete':
					if not old_object:
						ud.debug(ud.LDAP, ud.WARN,
											   "Object to delete doesn't exsist, ignore (%s)" % object['dn'])
						result = True
					else:
						result = self.delete_in_ucs(property_type, object, module, position)
					self._remove_dn_mapping(object['dn'], premapped_s4_dn)
				if object['modtype'] == 'move':
					result = self.move_in_ucs(property_type, object, module, position)
					self._remove_dn_mapping(object['olddn'],  '') # we don't know the old s4-dn here anymore, will be checked by remove_dn_mapping
					self._check_dn_mapping(object['dn'], premapped_s4_dn)

				if object['modtype'] == 'modify':
					result = self.modify_in_ucs(property_type, object, module, position)
					self._check_dn_mapping(object['dn'], premapped_s4_dn)
					
			if not result:
				ud.debug(ud.LDAP, ud.WARN,
						       "Failed to get Result for DN (%s)" % object['dn'])
				return False

			try:
				if object['modtype'] in ['add','modify']:
					for f in self.property[property_type].post_ucs_modify_functions:
						ud.debug(ud.LDAP, ud.INFO, "Call post_ucs_modify_functions: %s" % f)
						f(self, property_type, object)
						ud.debug(ud.LDAP, ud.INFO, "Call post_ucs_modify_functions: %s (done)" % f)
			except (ldap.SERVER_DOWN, SystemExit):
				raise
			except: # FIXME: which exception is to be caught?
				self._debug_traceback(ud.ERROR,
									  "failed in post_con_modify_functions")
				result = False				

			ud.debug(ud.LDAP, ud.INFO,
					       "Return  result for DN (%s)" % object['dn'])
			return result
		
		except univention.admin.uexceptions.valueInvalidSyntax, msg:
			try:
				ud.debug(ud.LDAP, ud.ERROR, "InvalidSyntax: %s (%s)" % (msg,object['dn']))
			except: # FIXME: which exception is to be caught?
				ud.debug(ud.LDAP, ud.ERROR, "InvalidSyntax: %s" % msg)
			return False
		except univention.admin.uexceptions.valueMayNotChange, msg:
			ud.debug(ud.LDAP, ud.ERROR, "Value may not change: %s (%s)" % (msg,object['dn']))
			return False
		except (ldap.SERVER_DOWN, SystemExit):
			raise
		except: # FIXME: which exception is to be caught?
			self._debug_traceback(ud.ERROR, "Unknown Exception during sync_to_ucs")
			return False

	def sync_from_ucs(self, property_type, object, old_dn=None):
		# dummy
		return False

	# internal functions

	def _subtree_match(self, dn, subtree):
		_d=ud.function('ldap._subtree_match')
		if len(subtree) > len(dn):
			return False
		if subtree.lower() == dn[len(dn)-len(subtree):].lower():
			return True
		return False

	def _subtree_replace(self, dn, subtree, subtreereplace): #FIXME: may raise an exception if called with umlauts
		_d=ud.function('ldap._subtree_replace')
		if len(subtree) > len(dn):
			return dn
		if subtree.lower() == dn[len(dn)-len(subtree):].lower():
			return dn[:len(dn)-len(subtree)]+subtreereplace
		return dn

	# attributes ist ein dictionary von LDAP-Attributen und den zugeordneten Werten
	def _filter_match(self, filter, attributes):
		'''
		versucht eine liste von attributen auf einen LDAP-Filter zu matchen
		Besonderheiten des Filters:
		- immer case-sensitive
		- nur * als Wildcard
		- geht "lachser" mit Verschachtelten Klammern um
		'''
		_d=ud.function('ldap._filter_match')

		filter_connectors=['!','&','|']

		def list_lower(elements):
			if type(elements) == type([]):
				retlist=[]
				for l in elements:
					retlist.append(l.lower())
				return retlist
			else:
				return elements
		def dict_lower(dict):
			if type(dict) == type({}):
				retdict = {}
				for key in dict:
					retdict[key.lower()] = dict[key]
				return retdict
			else:
				return dict

		def attribute_filter(filter, attributes):
			attributes = dict_lower(attributes)

			pos = string.find(filter,'=')
			if pos < 0:
				raise ValueError,'missing "=" in filter: %s' % filter
			attribute = filter[:pos].lower()
			if not attribute:
				raise ValueError,'missing attribute in filter: %s' % filter
			value = filter[pos+1:]

			if attribute.endswith(':1.2.840.113556.1.4.803:'):
				# bitwise filter
				attribute_name=attribute.replace(':1.2.840.113556.1.4.803:','')
				attribute_value=attributes.get(attribute_name)
				if attribute_value:
					try:
						if type(attribute_value) == type([]):
							attribute_value=int(attribute_value[0])
						int_value=int(value)
						if ((attribute_value & int_value) == int_value):
							return True
						else:
							return False
					except (ldap.SERVER_DOWN, SystemExit):
						raise
					except:
						ud.debug(ud.LDAP, ud.WARN, "attribute_filter: Failed to convert attributes for bitwise filter")
						return False

			if value == '*':
				return attribute in list_lower(attributes.keys())
			elif attributes.has_key(attribute):
				return value.lower() in list_lower(attributes[attribute])
			else:
				return False

		def connecting_filter(filter, attributes):

			def walk(filter, attributes):

				def split(filter):
					opened=[]
					closed=[]
					pos = 0
					level = 0
					for char in filter:
						if char == '(' :
							if level == 0: opened.append(pos)						
							level += 1
						elif char == ')':
							if level == 1: closed.append(pos)
							level -= 1
						if level < 0: raise ValueError,"too many ')' in filter: %s" % filter			
						pos += 1

					if len(opened) != len(closed): raise ValueError,"'(' and ')' don't match in filter: %s" % filter
					filters = []
					for i in range(len(opened)):
						filters.append(filter[opened[i]+1:closed[i]])
					return filters

				if filter[0] == '(':
					if not filter[-1] == ')':
						raise ValueError,"matching ) missing in filter: %s" % filter
					else:
						filters = split(filter)
						results=[]
						for filter in filters:
							results.append(subfilter(filter, attributes))
						return results
				else:
					return [subfilter(filter, attributes)]

			if filter[0] == '!':
				return not subfilter(filter[1:], attributes)
			elif filter[0] == '|':
				return 1 in walk(filter[1:],attributes)
			elif filter[0] == '&':
				return not 0 in walk(filter[1:],attributes)


		def subfilter(filter, attributes):

			if filter[0] == '(':
				if not filter[-1] == ')':
					raise ValueError,"matching ) missing in filter: %s" % filter
				else:
					return subfilter(filter[1:-1],attributes)

			elif filter[0] in filter_connectors:
				return connecting_filter(filter, attributes)

			else:
				return attribute_filter(filter, attributes)

		return subfilter(filter, attributes)


	def _ignore_object(self, key, object):
		'''
		parse if object should be ignored because of ignore_subtree or ignore_filter
		'''
		_d=ud.function('ldap._ignore_object')
		if not object.has_key('dn'):
			ud.debug(ud.LDAP, ud.INFO, "_ignore_object: ignore object without DN")
			return True # ignore not existing object

		if self.property.get(key):
			for subtree in self.property[key].ignore_subtree:
				if self._subtree_match(object['dn'], subtree):
					ud.debug(ud.LDAP, ud.INFO, "_ignore_object: ignore object because of subtree match: [%s]" % object['dn'])
					return True		

			if self.property[key].ignore_filter and self._filter_match(self.property[key].ignore_filter,object['attributes']):
				ud.debug(ud.LDAP, ud.INFO, "_ignore_object: ignore object because of ignore_filter")
				return True

			if self.property[key].match_filter and not self._filter_match(self.property[key].match_filter,object['attributes']):
				ud.debug(ud.LDAP, ud.INFO, "_ignore_object: ignore object because of match_filter")
				return True

		ud.debug(ud.LDAP, ud.INFO, "_ignore_object: Do not ignore %s" % object['dn'])

		return False


	def _object_mapping(self, key, old_object, object_type='con'):
		_d=ud.function('ldap._object_mapping')
		ud.debug(ud.LDAP, ud.INFO,"_object_mapping: map with key %s and type %s" % (key,object_type))
		object = copy.deepcopy(old_object)
		# Eingehendes Format object:
		#	'dn': dn
		#	'modtype': 'add', 'delete', 'modify', 'move'
		#	'attributes': { attr: [values] }
		#       'olddn' : dn (nur bei move)
		# Ausgehendes Format object_out:
		#	'dn': dn
		#	'modtype':  'add', 'delete', 'modify', 'move'
		#	'attributes': { attr: [values] }
		#       'olddn' : dn (nur bei move)

		# sync mode
		# dn mapping
		# ignore_filter
		# attributes
		# post_attributes
		object_out={}
		object_out['attributes']={}
		if object and object.has_key('modtype'):
			object_out['modtype']=object['modtype']
		else:
			object_out['modtype']=''

		# DN mapping

		dn_mapping_stored = []
		for dntype in ['dn','olddn']: # check if all available dn's are already mapped
			if object.has_key(dntype):
				ud.debug(ud.LDAP, ud.INFO,"_dn_type %s" % (object_type)) # don't send str(object) to debug, may lead to segfaults

				if (object_type == 'ucs' and self._get_dn_by_ucs(object[dntype]) != ''):
					object[dntype] = self._get_dn_by_ucs(object[dntype])
					dn_mapping_stored.append(dntype)
				if (object_type != 'ucs' and self._get_dn_by_con(object[dntype]) != ''):
					object[dntype] = self._get_dn_by_con(object[dntype])
					dn_mapping_stored.append(dntype)		
		
		if self.property.has_key(key):
			if hasattr(self.property[key], 'dn_mapping_function'):
				# DN mapping functions
				for function in self.property[key].dn_mapping_function:
					object=function(self, object, dn_mapping_stored, isUCSobject=(object_type == 'ucs'))

		if object_type == 'ucs':
			if self.property.has_key(key):
				if hasattr(self.property[key], 'position_mapping'):
					for dntype in ['dn','olddn']:
						if object.has_key(dntype) and dntype not in dn_mapping_stored:
							# save the old rdn with the correct upper and lower case
							rdn_store = self._get_rdn(object[dntype])
							for mapping in self.property[key].position_mapping:
								object[dntype]=self._subtree_replace(object[dntype].lower(),mapping[0].lower(),mapping[1].lower())

							if self.lo_s4.base.lower() == object[dntype][len(object[dntype])-len(self.lo_s4.base):].lower() and len(self.lo_s4.base) > len(self.lo.base):
								ud.debug(ud.LDAP, ud.INFO,"The dn %s is already converted to the S4 base, don't do this again." % object[dntype])
							else:	
								object[dntype] = self._subtree_replace(object[dntype].lower(),self.lo.base.lower(),self.lo_s4.base.lower()) # FIXME: lo_s4 may change with other connectors
							# write the correct upper and lower case back to the DN
							object[dntype] = object[dntype].replace(object[dntype][0:len(rdn_store)], rdn_store, 1)
		else:
			if self.property.has_key(key):
				if hasattr(self.property[key], 'position_mapping'):
					for dntype in ['dn','olddn']:
						if object.has_key(dntype) and dntype not in dn_mapping_stored:
							# save the old rdn with the correct upper and lower case
							rdn_store = self._get_rdn(object[dntype])
							for mapping in self.property[key].position_mapping:
								object[dntype]=self._subtree_replace(object[dntype].lower(),mapping[1].lower(),mapping[0].lower())

							if self.lo.base.lower() == object[dntype][len(object[dntype])-len(self.lo.base):].lower() and len(self.lo.base) > len(self.lo_s4.base):
								ud.debug(ud.LDAP, ud.INFO,"The dn %s is already converted to the UCS base, don't do this again." % object[dntype])
							else:
								object[dntype] = self._subtree_replace(object[dntype].lower(),self.lo_s4.base.lower(),self.lo.base.lower()) # FIXME: lo_s4 may change with other connectors
							# write the correct upper and lower case back to the DN
							object[dntype] = object[dntype].replace(object[dntype][0:len(rdn_store)], rdn_store, 1)

		object_out = object

		# other mapping
		if object_type == 'ucs':
			if self.property.has_key(key):
				for attribute, values in object['attributes'].items():
					if self.property[key].attributes:
						for attr_key in self.property[key].attributes.keys():
							if attribute == self.property[key].attributes[attr_key].ldap_attribute:
								# mapping function
								if hasattr(self.property[key].attributes[attr_key], 'mapping'):
									object_out['attributes'][self.property[key].attributes[attr_key].con_attribute]=self.property[key].attributes[attr_key].mapping[0](self, key, object)
								# direct mapping
								else:
									if self.property[key].attributes[attr_key].con_other_attribute:
										object_out['attributes'][self.property[key].attributes[attr_key].con_attribute]=[values[0]]
										object_out['attributes'][self.property[key].attributes[attr_key].con_other_attribute]=values[1:]
									else:
										object_out['attributes'][self.property[key].attributes[attr_key].con_attribute]=values

								# mapping_table	
								if self.property[key].mapping_table and attr_key in self.property[key].mapping_table.keys():
									for ucsval, conval in self.property[key].mapping_table[attr_key]:
										if type(object_out['attributes'][self.property[key].attributes[attr_key].con_attribute]) == type([]):

											ucsval_lower = make_lower(ucsval)
											objectval_lower = make_lower(object_out['attributes'][self.property[key].attributes[attr_key].con_attribute])
												
											if ucsval_lower in objectval_lower:
												object_out['attributes'][self.property[key].attributes[attr_key].con_attribute][ objectval_lower.index(ucsval_lower) ] = conval
											elif ucsval_lower == objectval_lower:
												object_out['attributes'][self.property[key].attributes[attr_key].con_attribute] = conval

					if hasattr(self.property[key], 'post_attributes') and self.property[key].post_attributes != None:
						for attr_key in self.property[key].post_attributes.keys():
							if attribute == self.property[key].post_attributes[attr_key].ldap_attribute:
								if hasattr(self.property[key].post_attributes[attr_key], 'mapping'):
									object_out['attributes'][self.property[key].post_attributes[attr_key].con_attribute]=self.property[key].post_attributes[attr_key].mapping[0](self, key, object)
								else:
									if self.property[key].post_attributes[attr_key].con_other_attribute:
										object_out['attributes'][self.property[key].post_attributes[attr_key].con_attribute]=[values[0]]
										object_out['attributes'][self.property[key].post_attributes[attr_key].con_other_attribute]=values[1:]
									else:
										object_out['attributes'][self.property[key].post_attributes[attr_key].con_attribute]=values

		else:
			if self.property.has_key(key):
				# Filter out Configuration objects w/o DN
				if object['dn'] != None:
					for attribute, values in object['attributes'].items():
						if self.property[key].attributes:
							for attr_key in self.property[key].attributes.keys():
								if attribute == self.property[key].attributes[attr_key].con_attribute:
									# mapping function
									if hasattr(self.property[key].attributes[attr_key], 'mapping'):
										object_out['attributes'][self.property[key].attributes[attr_key].ldap_attribute]=self.property[key].attributes[attr_key].mapping[1](self, key, object)
										# direct mapping
									else:
										if self.property[key].attributes[attr_key].con_other_attribute and object['attributes'].get(self.property[key].attributes[attr_key].con_other_attribute):
											object_out['attributes'][self.property[key].attributes[attr_key].ldap_attribute]=values+object['attributes'].get(self.property[key].attributes[attr_key].con_other_attribute)
										else:
											object_out['attributes'][self.property[key].attributes[attr_key].ldap_attribute]=values

										# mapping_table	
									if self.property[key].mapping_table and attr_key in self.property[key].mapping_table.keys():
										for ucsval, conval in self.property[key].mapping_table[attr_key]:
											if type(object_out['attributes'][self.property[key].attributes[attr_key].con_attribute]) == type([]):

												conval_lower = make_lower(conval)
												objectval_lower = make_lower(object_out['attributes'][self.property[key].attributes[attr_key].ldap_attribute])
											
												if conval_lower in objectval_lower:
													object_out['attributes'][self.property[key].attributes[attr_key].ldap_attribute][ objectval_lower.index(conval_lower) ] = ucsval
												elif conval_lower == objectval_lower:
													object_out['attributes'][self.property[key].attributes[attr_key].ldap_attribute] = ucsval

						if hasattr(self.property[key], 'post_attributes') and self.property[key].post_attributes != None:
							for attr_key in self.property[key].post_attributes.keys():
								if attribute == self.property[key].post_attributes[attr_key].con_attribute:
									if hasattr(self.property[key].post_attributes[attr_key], 'mapping'):
										object_out['attributes'][self.property[key].post_attributes[attr_key].ldap_attribute]=self.property[key].post_attributes[attr_key].mapping[1](self, key, object)
									else:
										if self.property[key].post_attributes[attr_key].con_other_attribute and object['attributes'].get(self.property[key].post_attributes[attr_key].con_other_attribute):
											object_out['attributes'][self.property[key].post_attributes[attr_key].ldap_attribute]=values+object['attributes'].get(self.property[key].post_attributes[attr_key].con_other_attribute)
										else:
											object_out['attributes'][self.property[key].post_attributes[attr_key].ldap_attribute]=values

		return object_out

