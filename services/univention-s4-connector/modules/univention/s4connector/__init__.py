#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Basic class for the UCS connector part
#
# Copyright 2004-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

from __future__ import print_function

import cPickle
import copy
import os
import re
import random
import string
import sys
import time
import traceback
import types
import pprint
from signal import signal, SIGTERM, SIG_DFL

import ldap
from ldap.controls.readentry import PostReadControl
from samba.ndr import ndr_unpack
from samba.dcerpc import misc
import sqlite3 as lite

import univention.uldap
import univention.admin.uldap
import univention.admin.modules
import univention.admin.objects
import univention.debug as ud_c
import univention.debug2 as ud

from univention.s4connector.s4cache import S4Cache
from univention.s4connector.lockingdb import LockingDB

term_signal_caught = False

univention.admin.modules.update()

# update choices-lists which are defined in LDAP
univention.admin.syntax.update_choices()


# util functions defined during mapping

def make_lower(mlValue):
	'''
	lower string cases for mlValue which can be string or a list of values which can be given to mlValue
	'''
	if hasattr(mlValue, 'lower'):
		return mlValue.lower()
	if isinstance(mlValue, type([])):
		return [make_lower(x) for x in mlValue]
	return mlValue


password_charsets = [
	'abcdefghijklmnopqrstuvwxyz',
	'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
	'0123456789',
	'^!\$%&/()=?{[]}+~#-_.:,;<>|\\',
]


def generate_strong_password(length=24):
	pwd = []
	charset = random.choice(password_charsets)
	while len(pwd) < length:
		pwd.append(random.choice(charset))
		charset = random.choice(list(set(password_charsets) - set([charset])))
	return "".join(pwd)


def set_ucs_passwd_user(s4connector, key, ucs_object):
	'''
	set random password to fulfill required values
	'''
	ucs_object['password'] = generate_strong_password()


def check_ucs_lastname_user(s4connector, key, ucs_object):
	'''
	check if required values for lastname are set
	'''
	if not ucs_object.has_property('lastname') or not ucs_object['lastname']:
		ucs_object['lastname'] = 'none'


def set_primary_group_user(s4connector, key, ucs_object):
	'''
	check if correct primary group is set
	'''
	s4connector.set_primary_group_to_ucs_user(key, ucs_object)

# compare functions

# helper


def dictonary_lowercase(dict):
	if isinstance(dict, type({})):
		ndict = {}
		for key in dict.keys():
			ndict[key] = []
			for val in dict[key]:
				ndict[key].append(val.lower())
		return ndict
	elif isinstance(dict, type([])):
		nlist = []
		for d in dict:
			nlist.append(d.lower())
		return nlist
	else:
		try:  # should be string
			return dict.lower()
		except Exception:  # FIXME: which exception is to be caught?
			pass


def compare_normal(val1, val2):
	return val1 == val2


def compare_lowercase(val1, val2):
	try:  # TODO: failes if conversion to ascii-str raises exception
		if dictonary_lowercase(val1) == dictonary_lowercase(val2):
			return True
		else:
			return False
	except Exception:  # FIXME: which exception is to be caught?
		return False

# helper classes


class configdb:

	def __init__(self, filename):
		self.filename = filename
		self._dbcon = lite.connect(self.filename)

	def get_by_value(self, section, option):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				cur.execute("SELECT key FROM '%s' WHERE value=?" % section, (option,))
				rows = cur.fetchall()
				cur.close()
				if rows:
					return rows[0][0]
				return ''
			except lite.Error:
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = lite.connect(self.filename)

	def get(self, section, option):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				cur.execute("SELECT value FROM '%s' WHERE key=?" % section, (option,))
				rows = cur.fetchall()
				cur.close()
				if rows:
					return rows[0][0]
				return ''
			except lite.Error:
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = lite.connect(self.filename)

	def set(self, section, option, value):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				cur.execute("""
		INSERT OR REPLACE INTO '%s' (key,value)
			VALUES (  ?, ?
		);""" % section, [option, value])
				self._dbcon.commit()
				cur.close()
				return
			except lite.Error as e:
				ud.debug(ud.LDAP, ud.ERROR, "sqlite: %s" % e)
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = lite.connect(self.filename)

	def items(self, section):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				cur.execute("SELECT * FROM '%s'" % (section))
				rows = cur.fetchall()
				cur.close()
				return rows
			except lite.Error as e:
				ud.debug(ud.LDAP, ud.WARN, "sqlite: %s" % e)
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = lite.connect(self.filename)

	def remove_option(self, section, option):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				cur.execute("DELETE FROM '%s' WHERE key=?" % section, (option,))
				self._dbcon.commit()
				cur.close()
				return
			except lite.Error as e:
				ud.debug(ud.LDAP, ud.WARN, "sqlite: %s" % e)
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = lite.connect(self.filename)

	def has_section(self, section):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='%s';" % section)
				rows = cur.fetchone()
				cur.close()
				if rows:
					return True
				else:
					return False
			except lite.Error as e:
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
			except lite.Error as e:
				ud.debug(ud.LDAP, ud.WARN, "sqlite: %s" % e)
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = lite.connect(self.filename)

	def has_option(self, section, option):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				cur.execute("SELECT value FROM '%s' WHERE key=?" % section, (option,))
				rows = cur.fetchall()
				cur.close()
				if rows:
					return True
				else:
					return False
			except lite.Error as e:
				ud.debug(ud.LDAP, ud.WARN, "sqlite: %s" % e)
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = lite.connect(self.filename)


class configsaver:

	def __init__(self, filename):
		self.filename = filename
		try:
			f = file(filename, 'r')
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

		f = file(self.filename, 'w')
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
			ret.append((key, self.config[section][key]))
		return ret

	def remove_option(self, section, option):
		if option in self.config[section]:
			self.config[section].pop(option)
		self.write()

	def has_section(self, section):
		return section in self.config

	def add_section(self, section):
		self.config[section] = {}
		self.write()

	def has_option(self, section, option):
		return section in self.config and option in self.config[section]


class attribute:

	def __init__(self, ucs_attribute='', ldap_attribute='', con_attribute='', con_other_attribute='', required=0, single_value=False, compare_function=None, mapping=(), reverse_attribute_check=False, sync_mode='sync', udm_option=None):
		self.ucs_attribute = ucs_attribute
		self.ldap_attribute = ldap_attribute
		self.con_attribute = con_attribute
		self.con_other_attribute = con_other_attribute
		self.udm_option = udm_option
		self.required = required
		# If no compare_function is given, we default to `compare_normal()`
		self.compare_function = compare_function or compare_normal
		if mapping:
			self.mapping = mapping
		# Make a reverse check of this mapping. This is necassary if the attribute is
		# available in UCS and in AD but the mapping is not 1:1.
		# For example the homeDirectory attribute is in UCS and in AD, but the mapping is
		# from homeDirectory in AD to sambaHomePath in UCS. The homeDirectory in UCS is not
		# considered.
		# Seee https://forge.univention.org/bugzilla/show_bug.cgi?id=25823
		self.reverse_attribute_check = reverse_attribute_check
		self.sync_mode = sync_mode
		self.single_value = single_value

	def __repr__(self):
		return 'univention.s4connector.attribute(**%s)' % (pprint.pformat(dict(self.__dict__), indent=4, width=250),)


class property:

	def __init__(
		self,
		ucs_default_dn='',
		con_default_dn='',
		ucs_module='',
		ucs_module_others=[],
		sync_mode='',
		scope='',
		con_search_filter='',
		ignore_filter=None,
		match_filter=None,
		ignore_subtree=[],
		con_create_objectclass=[],
		con_create_attributes=[],
		dn_mapping_function=[],
		attributes=None,
		ucs_create_functions=[],
		con_create_extenstions=[],
		post_con_create_functions=[],
		post_con_modify_functions=[],
		post_ucs_modify_functions=[],
		post_attributes=None,
		mapping_table=None,
		position_mapping=[],
		con_sync_function=None,
		ucs_sync_function=None,
		disable_delete_in_ucs=False,
		identify=None,
		con_subtree_delete_objects=[]):

		self.ucs_default_dn = ucs_default_dn

		self.con_default_dn = con_default_dn

		self.ucs_module = ucs_module

		# allow a 1:n mapping, for example a Windows client
		# could be a computers/windows or a computers/memberserver
		# object
		self.ucs_module_others = ucs_module_others
		self.sync_mode = sync_mode

		self.scope = scope

		self.con_search_filter = con_search_filter
		self.ignore_filter = ignore_filter
		self.match_filter = match_filter
		self.ignore_subtree = ignore_subtree

		self.con_create_objectclass = con_create_objectclass
		self.con_create_attributes = con_create_attributes
		self.dn_mapping_function = dn_mapping_function
		self.attributes = attributes

		self.ucs_create_functions = ucs_create_functions
		self.con_create_extenstions = con_create_extenstions

		self.post_con_create_functions = post_con_create_functions
		self.post_con_modify_functions = post_con_modify_functions
		self.post_ucs_modify_functions = post_ucs_modify_functions

		self.post_attributes = post_attributes
		self.mapping_table = mapping_table
		self.position_mapping = position_mapping

		if con_sync_function:
			self.con_sync_function = con_sync_function
		if ucs_sync_function:
			self.ucs_sync_function = ucs_sync_function

		self.con_subtree_delete_objects = con_subtree_delete_objects

		# Overwrite the identify function from the ucs modules, at least needed for dns
		if identify:
			self.identify = identify

		self.disable_delete_in_ucs = disable_delete_in_ucs

	def __repr__(self):
		return 'univention.s4connector.property(**%s)' % (pprint.pformat(dict(self.__dict__), indent=4, width=250),)


class ucs:

	def __init__(self, CONFIGBASENAME, _property, baseConfig, listener_dir):
		_d = ud.function('ldap.__init__')  # noqa: F841

		self.CONFIGBASENAME = CONFIGBASENAME

		self.ucs_no_recode = ['krb5Key', 'userPassword', 'pwhistory', 'sambaNTPassword', 'sambaLMPassword', 'userCertificate', 'msieee80211-Data', 'ms-net-ieee-8023-GP-PolicyReserved', 'ms-net-ieee-80211-GP-PolicyReserved', 'msiScript', 'productCode', 'upgradeProductCode', 'categoryId', 'ipsecData']

		self.baseConfig = baseConfig
		self.property = _property  # this is the mapping!

		self.init_debug()

		self.co = None
		self.listener_dir = listener_dir

		configdbfile = '/etc/univention/%s/s4internal.sqlite' % self.CONFIGBASENAME
		self.config = configdb(configdbfile)

		s4cachedbfile = '/etc/univention/%s/s4cache.sqlite' % self.CONFIGBASENAME
		self.s4cache = S4Cache(s4cachedbfile)

		lockingdbfile = '/etc/univention/%s/lockingdb.sqlite' % self.CONFIGBASENAME
		self.lockingdb = LockingDB(lockingdbfile)

		configfile = '/etc/univention/%s/s4internal.cfg' % self.CONFIGBASENAME
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

			new_file = '%s_converted_%f' % (configfile, time.time())
			os.rename(configfile, new_file)
			ud.debug(ud.LDAP, ud.PROCESS, "Converting done")

		self.open_ucs()

		for section in ['DN Mapping UCS', 'DN Mapping CON', 'UCS rejected', 'UCS deleted', 'UCS entryCSN']:
			if not self.config.has_section(section):
				self.config.add_section(section)

		ud.debug(ud.LDAP, ud.INFO, "init finished")

	def __del__(self):
		self.close_debug()

	def dn_mapped_to_base(self, dn, base):
		"""Introduced for Bug #33110: Fix case of base part of DN"""
		if dn.endswith(base):
			return dn
		elif dn.lower().endswith(base.lower()):  # FIXME
			return ''.join((dn[:-len(base)], base))
		else:
			return dn

	def open_ucs(self):
		bindpw_file = self.baseConfig.get('%s/ldap/bindpw' % self.CONFIGBASENAME, '/etc/ldap.secret')
		binddn = self.baseConfig.get('%s/ldap/binddn' % self.CONFIGBASENAME, 'cn=admin,' + self.baseConfig['ldap/base'])
		bindpw = open(bindpw_file).read()
		if bindpw[-1] == '\n':
			bindpw = bindpw[0:-1]

		host = self.baseConfig.get('%s/ldap/server' % self.CONFIGBASENAME, self.baseConfig.get('ldap/master'))

		try:
			port = int(self.baseConfig.get('%s/ldap/port' % self.CONFIGBASENAME, self.baseConfig.get('ldap/master/port')))
		except ValueError:
			port = 7389

		self.lo = univention.admin.uldap.access(host=host, port=port, base=self.baseConfig['ldap/base'], binddn=binddn, bindpw=bindpw, start_tls=2, follow_referral=True)

	def search_ucs(self, filter='(objectClass=*)', base='', scope='sub', attr=[], unique=0, required=0, timeout=-1, sizelimit=0):
		try:
			result = self.lo.search(filter=filter, base=base, scope=scope, attr=attr, unique=unique, required=required, timeout=timeout, sizelimit=sizelimit)
			return result
		except univention.admin.uexceptions.ldapError as search_exception:
			ud.debug(ud.LDAP, ud.INFO, 'Lost connection to the LDAP server. Trying to reconnect ...')
			try:
				self.open_ucs()
				result = self.lo.search(filter=filter, base=base, scope=scope, attr=attr, unique=unique, required=required, timeout=timeout, sizelimit=sizelimit)
				return result
			except ldap.SERVER_DOWN:
				ud.debug(ud.LDAP, ud.INFO, 'LDAP-Server seems to be down')
				raise search_exception

	def init_debug(self):
		_d = ud.function('ldap.init_debug')  # noqa: F841
		if '%s/debug/function' % self.CONFIGBASENAME in self.baseConfig:
			try:
				function_level = int(self.baseConfig['%s/debug/function' % self.CONFIGBASENAME])
			except ValueError:
				function_level = 0
		else:
			function_level = 0
		ud.init('/var/log/univention/%s-s4.log' % self.CONFIGBASENAME, 1, function_level)
		if '%s/debug/level' % self.CONFIGBASENAME in self.baseConfig:
			debug_level = self.baseConfig['%s/debug/level' % self.CONFIGBASENAME]
		else:
			debug_level = 2
		ud.set_level(ud.LDAP, int(debug_level))

		try:
			udm_function_level = int(self.baseConfig.get('%s/debug/udm/function' % self.CONFIGBASENAME, 0))
		except ValueError:
			udm_function_level = 0
		ud_c.init('/var/log/univention/%s-s4.log' % self.CONFIGBASENAME, 1, udm_function_level)

		try:
			udm_debug_level = int(self.baseConfig.get('%s/debug/udm/level' % self.CONFIGBASENAME, 1))
		except ValueError:
			udm_debug_level = 1
		for category in (ud.ADMIN, ud.LDAP):
			ud_c.set_level(category, int(udm_debug_level))

	def close_debug(self):
		_d = ud.function('ldap.close_debug')  # noqa: F841
		ud.debug(ud.LDAP, ud.INFO, "close debug")

	def _get_config_option(self, section, option):
		_d = ud.function('ldap._get_config_option')  # noqa: F841
		return self.config.get(section, option)

	def _set_config_option(self, section, option, value):
		_d = ud.function('ldap._set_config_option')  # noqa: F841
		self.config.set(section, option, value)

	def _remove_config_option(self, section, option):
		_d = ud.function('ldap._remove_config_option')  # noqa: F841
		self.config.remove_option(section, option)

	def _get_config_items(self, section):
		_d = ud.function('ldap._get_config_items')  # noqa: F841
		return self.config.items(section)

	def _save_rejected_ucs(self, filename, dn, resync=True, reason=''):
		_d = ud.function('ldap._save_rejected_ucs')  # noqa: F841
		if not resync:
			# Note that unescaped <> are invalid in DNs. See also:
			# `_list_rejected_ucs()`.
			dn = '<NORESYNC{}:{}>;{}'.format('=' + reason if reason else '', os.path.basename(filename), dn)
		unicode_dn = univention.s4connector.s4.encode_attrib(dn)
		self._set_config_option('UCS rejected', filename, unicode_dn)

	def _get_rejected_ucs(self, filename):
		_d = ud.function('ldap._get_rejected_ucs')  # noqa: F841
		return self._get_config_option('UCS rejected', filename)

	def _remove_rejected_ucs(self, filename):
		_d = ud.function('ldap._remove_rejected_ucs')  # noqa: F841
		self._remove_config_option('UCS rejected', filename)

	def list_rejected_ucs(self, filter_noresync=False):
		rejected = self._get_config_items('UCS rejected')
		if filter_noresync:
			no_resync = re.compile('^<NORESYNC(=.*?)?>;')
			return [(fn, dn) for (fn, dn) in rejected if no_resync.match(dn) is None]
		return rejected

	def _list_rejected_ucs(self):
		_d = ud.function('ldap._list_rejected_ucs')  # noqa: F841
		return self.list_rejected_ucs(filter_noresync=True)

	def _list_rejected_filenames_ucs(self):
		_d = ud.function('ldap._list_rejected_filenames_ucs')  # noqa: F841
		return [fn for (fn, dn) in self.list_rejected_ucs()]

	def _encode_dn_as_config_option(self, dn):
		return dn

	def _decode_dn_from_config_option(self, dn):
		return dn

	def _set_dn_mapping(self, dn_ucs, dn_con):
		_d = ud.function('ldap._set_dn_mapping')  # noqa: F841
		self._set_config_option('DN Mapping UCS', self._encode_dn_as_config_option(dn_ucs.lower()), self._encode_dn_as_config_option(dn_con.lower()))
		self._set_config_option('DN Mapping CON', self._encode_dn_as_config_option(dn_con.lower()), self._encode_dn_as_config_option(dn_ucs.lower()))

	def _remove_dn_mapping(self, dn_ucs, dn_con):
		_d = ud.function('ldap._remove_dn_mapping')  # noqa: F841
		# delete all if mapping failed in the past
		dn_con_mapped = self._get_dn_by_ucs(dn_ucs.lower())
		dn_ucs_mapped = self._get_dn_by_con(dn_con.lower())
		dn_con_re_mapped = self._get_dn_by_ucs(dn_ucs_mapped.lower())
		dn_ucs_re_mapped = self._get_dn_by_con(dn_con_mapped.lower())

		for ucs, con in [(dn_ucs, dn_con), (dn_ucs_mapped, dn_con_mapped), (dn_ucs_re_mapped, dn_con_re_mapped)]:
			if con:
				self._remove_config_option('DN Mapping CON', self._encode_dn_as_config_option(con.lower()))
			if ucs:
				self._remove_config_option('DN Mapping UCS', self._encode_dn_as_config_option(ucs.lower()))

	def _remember_entryCSN_commited_by_connector(self, entryUUID, entryCSN):
		"""Remember the entryCSN of a change committed by the S4-Connector itself"""
		_d = ud.function('ldap._remember_entryCSN_commited_by_connector')  # noqa: F841
		value = self._get_config_option('UCS entryCSN', entryUUID)
		if value:
			entryCSN_set = set(value.split(','))
			entryCSN_set.add(entryCSN)
			value = ','.join(entryCSN_set)
		else:
			value = entryCSN
		self._set_config_option('UCS entryCSN', entryUUID, value)

	def _get_last_entryCSN_commited_by_connector(self, entryUUID):
		"""Remember the entryCSN of a change committed by the S4-Connector itself"""
		_d = ud.function('ldap._get_last_entryCSN_commited_by_connector')  # noqa: F841
		return self._get_config_option('UCS entryCSN', entryUUID)

	def _forget_entryCSN(self, entryUUID, entryCSN):
		_d = ud.function('ldap._forget_entryCSN')  # noqa: F841
		value = self._get_config_option('UCS entryCSN', entryUUID)
		if not value:
			return False

		entryCSN_set = set(value.split(','))
		if entryCSN not in entryCSN_set:
			return False

		entryCSN_set.remove(entryCSN)
		if entryCSN_set:
			value = ','.join(entryCSN_set)
			self._set_config_option('UCS entryCSN', entryUUID, value)
		else:
			self._remove_config_option('UCS entryCSN', entryUUID)
		return True

	def _get_dn_by_ucs(self, dn_ucs):
		_d = ud.function('ldap._get_dn_by_ucs')  # noqa: F841
		return self._decode_dn_from_config_option(self._get_config_option('DN Mapping UCS', self._encode_dn_as_config_option(dn_ucs.lower())))

	def get_dn_by_ucs(self, dn_ucs):
		if not dn_ucs:
			return dn_ucs
		dn = self._get_dn_by_ucs(dn_ucs)
		return self.dn_mapped_to_base(dn, self.lo_s4.base)

	def _get_dn_by_con(self, dn_con):
		_d = ud.function('ldap._get_dn_by_con')  # noqa: F841
		if not dn_con:
			return dn_con
		return self._decode_dn_from_config_option(self._get_config_option('DN Mapping CON', self._encode_dn_as_config_option(dn_con.lower())))

	def get_dn_by_con(self, dn_con):
		dn = self._get_dn_by_con(dn_con)
		return self.dn_mapped_to_base(dn, self.lo.base)

	def _check_dn_mapping(self, dn_ucs, dn_con):
		_d = ud.function('ldap._check_dn_mapping')  # noqa: F841
		dn_con_mapped = self._get_dn_by_ucs(dn_ucs.lower())
		dn_ucs_mapped = self._get_dn_by_con(dn_con.lower())
		if dn_con_mapped != dn_con.lower() or dn_ucs_mapped != dn_ucs.lower():
			self._remove_dn_mapping(dn_ucs.lower(), dn_con_mapped.lower())
			self._remove_dn_mapping(dn_ucs_mapped.lower(), dn_con.lower())
			self._set_dn_mapping(dn_ucs.lower(), dn_con.lower())

	def _debug_traceback(self, level, text):
		'''
		print traceback with ud.debug, level is i.e. ud.INFO
		'''
		_d = ud.function('ldap._debug_traceback')  # noqa: F841
		ud.debug(ud.LDAP, level, text)
		ud.debug(ud.LDAP, level, traceback.format_exc())

	def _get_rdn(self, dn):
		_d = ud.function('ldap._get_rdn')  # noqa: F841
		'''
		return rdn from dn
		'''
		return dn.split(',', 1)[0]  # FIXME

	def _get_subtree(self, dn):
		_d = ud.function('ldap._get_subtree')  # noqa: F841
		'''
		return subtree from dn
		'''
		return dn.split(',', 1)[1]  # FIXME

	def __sync_file_from_ucs(self, filename, append_error='', traceback_level=ud.WARN):
		_d = ud.function('ldap._sync_file_from_ucs')  # noqa: F841
		'''
		sync changes from UCS stored in given file
		'''

		try:
			with open(filename) as fob:
				(dn, new, old, old_dn) = cPickle.load(fob)
		except IOError:
			return True  # file not found so there's nothing to sync
		except (cPickle.UnpicklingError, EOFError) as e:
			message = 'file emtpy' if isinstance(e, EOFError) else e.message
			ud.debug(ud.LDAP, ud.ERROR, '__sync_file_from_ucs: invalid pickle file {}: {}'.format(filename, message))
			# ignore corrupted pickle file, but save as rejected to not try again
			self._save_rejected_ucs(filename, 'unknown', resync=False, reason='broken file')
			return False

		if dn == 'cn=Subschema':
			return True

		def recode_attribs(attribs):
			nattribs = {}
			for key in attribs.keys():
				if key in self.ucs_no_recode:
					nattribs[key] = attribs[key]
				else:
					try:
						nvals = []
						for val in attribs[key]:
							nvals.append(unicode(val, 'utf8'))
						nattribs[unicode(key, 'utf8')] = nvals
					except UnicodeDecodeError:
						nattribs[key] = attribs[key]

			return nattribs
		new = recode_attribs(new)
		old = recode_attribs(old)

		key = None

		# if the object was moved into a ignored tree
		# we should delete this object
		ignore_subtree_match = False

		_attr = new or old
		key = self.identify_udm_object(dn, _attr)

		if not new:
			change_type = "delete"
			ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: object was deleted")
			if key == 'msGPO':
				entryUUID = old.get('entryUUID', [None])[0]
				entryCSN = old.get('entryCSN', [None])[0]
				self._forget_entryCSN(entryUUID, entryCSN)
		else:
			entryUUID = new.get('entryUUID', [None])[0]
			if entryUUID:
				if self.was_entryUUID_deleted(entryUUID):
					if self._get_entryUUID(dn) == entryUUID:
						ud.debug(ud.LDAP, ud.PROCESS, "__sync_file_from_ucs: Object with entryUUID %s has been removed before but became visible again." % entryUUID)
					else:
						ud.debug(ud.LDAP, ud.PROCESS, "__sync_file_from_ucs: Object with entryUUID %s has been removed before. Don't re-create." % entryUUID)
						return True
			else:
				ud.debug(ud.LDAP, ud.ERROR, "__sync_file_from_ucs: Object without entryUUID: %s" % (dn,))
				return False

			if key == 'msGPO':
				entryCSN = new.get('entryCSN', [None])[0]
				if self._forget_entryCSN(entryUUID, entryCSN):
					ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: Skipping back-sync of %s %s" % (key, dn))
					ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: because entryCSN %s was written by sync_to_ucs" % (entryCSN,))
					return True

			# ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: old: %s" % old)
			# ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: new: %s" % new)
			if old and new:
				change_type = "modify"
				ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: object was modified")
				if old_dn and not old_dn == dn:
					ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: object was moved")
					# object was moved
					new_object = {'dn': unicode(dn, 'utf8'), 'modtype': change_type, 'attributes': new}
					old_object = {'dn': unicode(old_dn, 'utf8'), 'modtype': change_type, 'attributes': old}
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
				object = {'dn': unicode(dn, 'utf8'), 'modtype': 'modify', 'attributes': new}
				try:
					if self._ignore_object(key, object):
						ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: new object is ignored, nothing to do")
						change_type = 'modify'
						ignore_subtree_match = True
						return True
					else:
						if old_dn and not old_dn == dn:
							change_type = "modify"
							ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: object was moved")
						else:
							change_type = "add"
							old_dn = ''  # there may be an old_dn if object was moved from ignored container
							ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: object was added: %s" % dn)
				except (ldap.SERVER_DOWN, SystemExit):
					raise
				except Exception:  # FIXME: which exception is to be caught?
					# the ignore_object method might throw an exception if the subschema will be synced
					change_type = "add"
					old_dn = ''  # there may be an old_dn if object was moved from ignored container
					ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: object was added: %s" % dn)

		if key:
			if change_type == 'delete':
				if old_dn:
					object = {'dn': unicode(old_dn, 'utf8'), 'modtype': change_type, 'attributes': old}
				else:
					object = {'dn': unicode(dn, 'utf8'), 'modtype': change_type, 'attributes': old}
			else:
				object = {'dn': unicode(dn, 'utf8'), 'modtype': change_type, 'attributes': new}

			if change_type == 'modify' and old_dn:
				object['olddn'] = unicode(old_dn, 'utf8')  # needed for correct samaccount-mapping

			if not self._ignore_object(key, object) or ignore_subtree_match:
				pre_mapped_ucs_dn = object['dn']
				# NOTE: pre_mapped_ucs_dn means: original ucs_dn (i.e. before _object_mapping)
				mapped_object = self._object_mapping(key, object, 'ucs')
				if not self._ignore_object(key, object) or ignore_subtree_match:
					ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: finished mapping")
					try:
						if ((old_dn and not self.sync_from_ucs(key, mapped_object, pre_mapped_ucs_dn, unicode(old_dn, 'utf8'), old, new)) or (not old_dn and not self.sync_from_ucs(key, mapped_object, pre_mapped_ucs_dn, old_dn, old, new))):
							self._save_rejected_ucs(filename, dn)
							return False
						else:
							return True
					except ldap.SERVER_DOWN:
						raise
					except ldap.NO_SUCH_OBJECT:
						self._save_rejected_ucs(filename, dn)
						if traceback_level == ud.INFO:
							self._debug_traceback(traceback_level, "The sync failed. This could be because the parent object does not exist. This object will be synced in next sync step.")
						else:
							self._debug_traceback(traceback_level, "sync failed, saved as rejected\n\t%s" % (filename,))
						return False
					except Exception:
						self._save_rejected_ucs(filename, dn)
						self._debug_traceback(traceback_level, "sync failed, saved as rejected\n\t%s" % (filename,))
						return False
				else:
					return True
			else:
				return True
		else:
			ud.debug(ud.LDAP, ud.INFO, "__sync_file_from_ucs: No mapping was found for dn: %s" % dn)
			return True

	def get_ucs_ldap_object_dn(self, dn):
		_d = ud.function('ldap.get_ucs_ldap_object_dn')  # noqa: F841

		for i in [0, 1]:  # do it twice if the LDAP connection was closed
			if isinstance(dn, type(u'')):
				searchdn = dn
			else:
				searchdn = unicode(dn)
			try:
				return self.lo.lo.lo.search_s(searchdn, ldap.SCOPE_BASE, '(objectClass=*)', ('dn',))[0][0]
			except ldap.NO_SUCH_OBJECT:
				return None
			except ldap.INVALID_DN_SYNTAX:
				return None
			except ldap.INVALID_SYNTAX:
				return None
			except (ldap.SERVER_DOWN, SystemExit):
				self.open_ucs()
				continue

	def get_ucs_ldap_object(self, dn):
		_d = ud.function('ldap.get_ucs_ldap_object')  # noqa: F841

		for i in [0, 1]:  # do it twice if the LDAP connection was closed
			if isinstance(dn, type(u'')):
				searchdn = dn
			else:
				searchdn = unicode(dn)
			try:
				return self.lo.get(searchdn, required=1)
			except ldap.NO_SUCH_OBJECT:
				return None
			except ldap.INVALID_DN_SYNTAX:
				return None
			except ldap.INVALID_SYNTAX:
				return None
			except (ldap.SERVER_DOWN, SystemExit):
				self.open_ucs()
				continue

	def get_ucs_object(self, property_type, dn):
		_d = ud.function('ldap.get_ucs_object')  # noqa: F841
		ucs_object = None
		if isinstance(dn, unicode):
			searchdn = dn
		else:
			searchdn = unicode(dn)
		try:
			attr = self.get_ucs_ldap_object(searchdn)
			if not attr:
				ud.debug(ud.LDAP, ud.INFO, "get_ucs_object: object not found: %s" % searchdn)
				return None

			module = self.modules[property_type]  # default, determined by mapping filter
			if not module.identify(searchdn, attr):
				for m in self.modules_others.get(property_type, []):
					if m and m.identify(searchdn, attr):
						module = m
						break
				else:
					ud.debug(ud.LDAP, ud.ERROR, "get_ucs_object: could not identify UDM object type: %s" % searchdn)
					ud.debug(ud.LDAP, ud.PROCESS, "get_ucs_object: using default: %s" % module.module)

			ucs_object = univention.admin.objects.get(module, co=None, lo=self.lo, position='', dn=searchdn)
			ud.debug(ud.LDAP, ud.INFO, "get_ucs_object: object found: %s" % searchdn)
		except ldap.SERVER_DOWN:
			raise
		except Exception:  # FIXME: which exception is to be caught?
			ud.debug(ud.LDAP, ud.INFO, "get_ucs_object: object search failed: %s" % searchdn)
			self._debug_traceback(ud.WARN, "get_ucs_object: failure was: \n\t")
			return None

		return ucs_object

	def initialize_ucs(self):
		_d = ud.function('ldap.initialize_ucs')  # noqa: F841
		print("--------------------------------------")
		print("Initialize sync from UCS")
		sys.stdout.flush()

		# load UCS Modules
		self.modules = {}
		self.modules_others = {}
		position = univention.admin.uldap.position(self.lo.base)

		for key, mapping in self.property.items():
			if mapping.ucs_module:
				self.modules[key] = univention.admin.modules.get(mapping.ucs_module)
				if hasattr(mapping, 'identify'):
					ud.debug(ud.LDAP, ud.INFO, "Override identify function for %s" % key)
					self.modules[key].identify = mapping.identify
			else:
				self.modules[key] = None
			univention.admin.modules.init(self.lo, position, self.modules[key])

			self.modules_others[key] = []
			if mapping.ucs_module_others:
				for m in mapping.ucs_module_others:
					if m:
						self.modules_others[key].append(univention.admin.modules.get(m))
				for m in self.modules_others[key]:
					if m:
						univention.admin.modules.init(self.lo, position, m)

		# try to resync rejected changes
		self.resync_rejected_ucs()
		# call poll_ucs to sync
		self.poll_ucs()
		print("--------------------------------------")
		sys.stdout.flush()

	def initialize(self):
		# dummy
		pass

	def resync_rejected_ucs(self):
		'''
		tries to resync rejected changes from UCS
		'''
		_d = ud.function('ldap.resync_rejected_ucs')  # noqa: F841
		rejected = self._list_rejected_ucs()
		change_counter = 0
		print("--------------------------------------")
		print("Sync %s rejected changes from UCS" % len(rejected))
		sys.stdout.flush()

		if rejected:
			for filename, dn in rejected:
				ud.debug(ud.LDAP, ud.PROCESS, 'sync from ucs:   Resync rejected file: %s' % (filename))
				try:
					if self.__sync_file_from_ucs(filename, append_error=' rejected'):
						try:
							os.remove(os.path.join(filename))
						except OSError:  # file not found
							pass
						self._remove_rejected_ucs(filename)
						change_counter += 1
				except ldap.SERVER_DOWN:
					raise
				except Exception:  # FIXME: which exception is to be caught?
					self._save_rejected_ucs(filename, dn)
					self._debug_traceback(ud.WARN, "sync failed, saved as rejected \n\t%s" % filename)

		print("restored %s rejected changes" % change_counter)
		print("--------------------------------------")
		sys.stdout.flush()

	def resync_rejected(self):
		# dummy
		pass

	def poll_ucs(self):
		'''
		poll changes from UCS: iterates over files exported by directory-listener module
		'''
		_d = ud.function('ldap.poll_ucs')  # noqa: F841
		# check for changes from ucs ldap directory

		change_counter = 0
		MAX_SYNC_IN_ONE_INTERVAL = 50000

		self.rejected_files = self._list_rejected_filenames_ucs()

		print("--------------------------------------")
		print("try to sync %s changes from UCS" % (min(len(os.listdir(self.listener_dir)) - 1, MAX_SYNC_IN_ONE_INTERVAL)))
		print("done:", end=' ')
		sys.stdout.flush()
		done_counter = 0
		files = sorted(os.listdir(self.listener_dir))

		# Only synchronize the first MAX_SYNC_IN_ONE_INTERVAL changes otherwise
		# the change list is too long and it took too much time
		files = files[:MAX_SYNC_IN_ONE_INTERVAL]

		# We may dropped the parent object, so don't show the traceback in any case
		traceback_level = ud.WARN

		for listener_file in files:
			sync_successfull = False
			filename = os.path.join(self.listener_dir, listener_file)
			if not filename == "%s/tmp" % self.baseConfig['%s/s4/listener/dir' % self.CONFIGBASENAME]:
				if filename not in self.rejected_files:
					try:
						with open(filename) as fob:
							(dn, new, old, old_dn) = cPickle.load(fob)
					except IOError:
						continue  # file not found so there's nothing to sync
					except (cPickle.UnpicklingError, EOFError) as e:
						message = 'file emtpy' if isinstance(e, EOFError) else e.message
						ud.debug(ud.LDAP, ud.ERROR, 'poll_ucs: invalid pickle file {}: {}'.format(filename, message))
						# ignore corrupted pickle file, but save as rejected to not try again
						self._save_rejected_ucs(filename, 'unknown', resync=False, reason='broken file')
						continue

					for i in [0, 1]:  # do it twice if the LDAP connection was closed
						try:
							sync_successfull = self.__sync_file_from_ucs(filename, traceback_level=traceback_level)
						except (ldap.SERVER_DOWN, SystemExit):
							# once again, ldap idletimeout ...
							if i == 0:
								self.open_ucs()
								continue
							raise
						except Exception:
							self._save_rejected_ucs(filename, dn)
							# We may dropped the parent object, so don't show this warning
							self._debug_traceback(traceback_level, "sync failed, saved as rejected \n\t%s" % filename)
						if sync_successfull:
							os.remove(os.path.join(self.listener_dir, listener_file))
							change_counter += 1
						break

				done_counter += 1
				print("%s" % done_counter, end=' ')
				sys.stdout.flush()

		print("")

		self.rejected_files = self._list_rejected_filenames_ucs()

		if self.rejected_files:
			print("Changes from UCS: %s (%s saved rejected)" % (change_counter, len(self.rejected_files)))
		else:
			print("Changes from UCS: %s (%s saved rejected)" % (change_counter, '0'))
		print("--------------------------------------")
		sys.stdout.flush()
		return change_counter

	def poll(self, show_deleted=True):
		# dummy
		pass

	def __set_values(self, property_type, object, ucs_object, modtype='modify'):
		_d = ud.function('ldap.__set_value')  # noqa: F841
		if not modtype == 'add':
			ucs_object.open()
		ud.debug(ud.LDAP, ud.INFO, '__set_values: object: %s' % object)

		def set_values(attributes):
			if attributes.ldap_attribute in object['attributes']:
				ucs_key = attributes.ucs_attribute
				if ucs_key:
					value = object['attributes'][attributes.ldap_attribute]
					ud.debug(ud.LDAP, ud.INFO, '__set_values: set attribute, ucs_key: %s - value: %s' % (ucs_key, value))

					ucs_module = self.modules[property_type]
					position = univention.admin.uldap.position(self.lo.base)
					position.setDn(object['dn'])
					univention.admin.modules.init(self.lo, position, ucs_module)

					if isinstance(value, type(types.ListType())) and len(value) == 1:
						value = value[0]

					# set encoding
					compare = [ucs_object[ucs_key], value]
					for i in [0, 1]:
						if isinstance(compare[i], type([])):
							compare[i] = univention.s4connector.s4.compatible_list(compare[i])
						else:
							compare[i] = univention.s4connector.s4.compatible_modstring(compare[i])

					if not attributes.compare_function(compare[0], compare[1]):
						# This is deduplication of LDAP attribute values for S4 -> UCS.
						# It destroys ordering of multi-valued attributes. This seems problematic
						# as the handling of `con_other_attribute` assumes preserved ordering
						# (this is not guaranteed by LDAP).
						# See the MODIFY-case in `sync_from_ucs()` for more.
						ud.debug(ud.LDAP, ud.INFO, "set key in ucs-object %s to value: %r" % (ucs_key, value))
						try:
							if attributes.udm_option not in ucs_object.options:
								ud.debug(ud.LDAP, ud.INFO, "set option in ucs-object %s to value: %r" % (ucs_key, attributes.udm_option))
								ucs_object.options.append(attributes.udm_option)
						except AttributeError:
							pass
						if isinstance(value, list):
							ucs_object[ucs_key] = list(set(value))
						else:
							ucs_object[ucs_key] = value
						ud.debug(ud.LDAP, ud.INFO, "result key in ucs-object %s: %r" % (ucs_key, ucs_object[ucs_key]))
				else:
					ud.debug(ud.LDAP, ud.INFO, '__set_values: no ucs_attribute found in %s' % attributes)
			else:
				# prevent value resets of mandatory attributes
				mandatory_attrs = ['lastname', 'unixhome', 'gidNumber', 'uidNumber']

				ucs_key = attributes.ucs_attribute
				if ucs_object.has_property(ucs_key):
					ucs_module = self.modules[property_type]
					position = univention.admin.uldap.position(self.lo.base)
					position.setDn(object['dn'])
					univention.admin.modules.init(self.lo, position, ucs_module)

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
			if self.property[property_type].attributes[attr_key].sync_mode in ['read', 'sync']:

				con_attribute = self.property[property_type].attributes[attr_key].con_attribute
				con_other_attribute = self.property[property_type].attributes[attr_key].con_other_attribute

				if not object.get('changed_attributes') or con_attribute in object.get('changed_attributes') or (con_other_attribute and con_other_attribute in object.get('changed_attributes')):
					ud.debug(ud.LDAP, ud.INFO, '__set_values: Set: %s' % con_attribute)
					set_values(self.property[property_type].attributes[attr_key])
				else:
					ud.debug(ud.LDAP, ud.INFO, '__set_values: Skip: %s' % con_attribute)

		# post-values
		if not self.property[property_type].post_attributes:
			return
		for attr_key in self.property[property_type].post_attributes.keys():
			ud.debug(ud.LDAP, ud.INFO, '__set_values: mapping for attribute: %s' % attr_key)
			if self.property[property_type].post_attributes[attr_key].sync_mode in ['read', 'sync']:

				con_attribute = self.property[property_type].post_attributes[attr_key].con_attribute
				con_other_attribute = self.property[property_type].post_attributes[attr_key].con_other_attribute

				if not object.get('changed_attributes') or con_attribute in object.get('changed_attributes') or (con_other_attribute and con_other_attribute in object.get('changed_attributes')):
					ud.debug(ud.LDAP, ud.INFO, '__set_values: Set: %s' % con_attribute)
					if self.property[property_type].post_attributes[attr_key].reverse_attribute_check:
						if object['attributes'].get(self.property[property_type].post_attributes[attr_key].ldap_attribute):
							set_values(self.property[property_type].post_attributes[attr_key])
						else:
							ucs_object[self.property[property_type].post_attributes[attr_key].ucs_attribute] = ''
					else:
						set_values(self.property[property_type].post_attributes[attr_key])
				else:
					ud.debug(ud.LDAP, ud.INFO, '__set_values: Skip: %s' % con_attribute)

	def add_in_ucs(self, property_type, object, module, position):
		_d = ud.function('ldap.add_in_ucs')  # noqa: F841
		ucs_object = module.object(None, self.lo, position=position)
		if property_type == 'group':
			ucs_object.open()
			ud.debug(ud.LDAP, ud.INFO, "sync_to_ucs: remove %s from ucs group cache" % object['dn'])
			self.group_members_cache_ucs[object['dn'].lower()] = set()
		else:
			ucs_object.open()
		self.__set_values(property_type, object, ucs_object, modtype='add')
		for function in self.property[property_type].ucs_create_functions:
			function(self, property_type, ucs_object)

		serverctrls = []
		response = {}
		if property_type == 'msGPO':
			serverctrls = [PostReadControl(True, ['entryUUID', 'entryCSN'])]
		res = ucs_object.create(serverctrls=serverctrls, response=response)
		if res:
			for c in response.get('ctrls', []):
				if c.controlType == PostReadControl.controlType:
					entryUUID = c.entry['entryUUID'][0]
					entryCSN = c.entry['entryCSN'][0]
					self._remember_entryCSN_commited_by_connector(entryUUID, entryCSN)
			res = True
		return res

	def modify_in_ucs(self, property_type, object, module, position):
		_d = ud.function('ldap.modify_in_ucs')  # noqa: F841

		ucs_object_dn = object.get('olddn', object['dn'])
		ucs_object = univention.admin.objects.get(module, None, self.lo, dn=ucs_object_dn, position='')
		self.__set_values(property_type, object, ucs_object)

		serverctrls = []
		response = {}
		if property_type == 'msGPO':
			serverctrls = [PostReadControl(True, ['entryUUID', 'entryCSN'])]
		res = ucs_object.modify(serverctrls=serverctrls, response=response)
		if res:
			for c in response.get('ctrls', []):
				if c.controlType == PostReadControl.controlType:  # If the modify actually did something
					entryUUID = c.entry['entryUUID'][0]
					entryCSN = c.entry['entryCSN'][0]
					self._remember_entryCSN_commited_by_connector(entryUUID, entryCSN)
			res = True
		return res

	def move_in_ucs(self, property_type, object, module, position):
		_d = ud.function('ldap.move_in_ucs')  # noqa: F841
		if self.lo.compare_dn(object['olddn'].lower(), object['dn'].lower()):
			ud.debug(ud.LDAP, ud.WARN, "move_in_ucs: cancel move, old and new dn are the same (%r to %r)" % (object['olddn'], object['dn']))
			return True

		ud.debug(ud.LDAP, ud.INFO, "move_in_ucs: move object from %r to %r" % (object['olddn'], object['dn']))
		ucs_object = univention.admin.objects.get(module, None, self.lo, dn=object['olddn'], position='')
		ucs_object.open()
		ucs_object.move(object['dn'])
		return True

	def _get_entryUUID(self, dn):
		try:
			result = self.search_ucs(base=dn, scope='base', attr=['entryUUID'], unique=True)
			if result:
				return result[0][1].get('entryUUID')[0]
			else:
				return None
		except univention.admin.uexceptions.noObject:
			return None

	def update_deleted_cache_after_removal(self, entryUUID, objectGUID):
		if not entryUUID:
			return
		# use a dummy value
		if not objectGUID:
			objectGUID_str = 'objectGUID'
		else:
			objectGUID_str = str(ndr_unpack(misc.GUID, objectGUID))
		ud.debug(ud.LDAP, ud.INFO, "update_deleted_cache_after_removal: Save entryUUID %s as deleted to UCS deleted cache. ObjectGUUID: %s" % (entryUUID, objectGUID_str))
		self._set_config_option('UCS deleted', entryUUID, objectGUID_str)

	def was_entryUUID_deleted(self, entryUUID):
		objectGUID = self.config.get('UCS deleted', entryUUID)
		if objectGUID:
			return True
		else:
			return False

	def was_objectGUID_deleted_by_ucs(self, objectGUID):
		try:
			objectGUID = str(ndr_unpack(misc.GUID, objectGUID))
			entryUUID = self.config.get_by_value('UCS deleted', objectGUID)
			if entryUUID:
				return True
		except Exception as err:
			ud.debug(ud.LDAP, ud.ERROR, "was_objectGUID_deleted_by_ucs: failed to look for objectGUID %s in 'UCS deleted': %s" % (objectGUID, str(err)))
		return False

	def delete_in_ucs(self, property_type, object, module, position):
		"""Removes an Samba-4 object in UCS-LDAP"""
		_d = ud.function('ldap.delete_in_ucs')  # noqa: F841

		if self.property[property_type].disable_delete_in_ucs:
			ud.debug(ud.LDAP, ud.PROCESS, "Delete of %s was disabled in mapping" % object['dn'])
			return True

		objectGUID = object['attributes'].get('objectGUID', [None])[0]  # to compensate for __object_from_element
		entryUUID = self._get_entryUUID(object['dn'])

		if property_type in ['ou', 'container']:
			if objectGUID and self.was_objectGUID_deleted_by_ucs(objectGUID):
				ud.debug(ud.LDAP, ud.PROCESS, "delete_in_ucs: object %s already deleted in UCS, ignoring delete" % object['dn'])
				return True

		if property_type == 'windowscomputer':
			# Special handling for windows computer:
			#  In AD the computer is a windows computer in UCS the computer is a DC.
			#  If Samba 4 will be installed on the Slave, Samba 4 deletes the object
			#  and this deletion must not be synced to OpenLDAP.
			#  https://forge.univention.org/bugzilla/show_bug.cgi?id=35563
			try:
				result = self.search_ucs(base=object['dn'], scope='base', attr=['objectClass'], unique=True)
			except univention.admin.uexceptions.noObject:
				ud.debug(ud.LDAP, ud.PROCESS, "The object was not found in UCS: %s" % object['dn'])
				return True

			if 'univentionDomainController' in result[0][1].get('objectClass'):
				ud.debug(ud.LDAP, ud.PROCESS, "The windows computer %s is a Domain Controller in OpenLDAP. The deletion will be skipped." % object['dn'])
				return True

		try:
			ucs_object = univention.admin.objects.get(module, None, self.lo, dn=object['dn'], position='')
		except univention.admin.uexceptions.noObject:
			raise  # object is already removed... TODO: enable if wanted!
			return True

		ucs_object.open()

		try:
			try:
				ucs_object.remove()
				self.update_deleted_cache_after_removal(entryUUID, objectGUID)
				return True
			except univention.admin.uexceptions.ldapError as exc:
				if isinstance(exc.original_exception, ldap.NOT_ALLOWED_ON_NONLEAF):
					raise exc.original_exception
				raise
		except ldap.NOT_ALLOWED_ON_NONLEAF:
			ud.debug(ud.LDAP, ud.INFO, "remove object from UCS failed, need to delete subtree")
			if self._remove_subtree_in_ucs(object):
				# FIXME: endless recursion if there is one subtree-object which is ignored, not identifyable or can't be removed.
				return self.delete_in_ucs(property_type, object, module, position)
			return False

	def _remove_subtree_in_ucs(self, parent_ucs_object):
		for subdn, subattr in self.search_ucs(base=parent_ucs_object['dn'], attr=['*', '+']):
			if self.lo.compare_dn(unicode(subdn).lower(), unicode(parent_ucs_object['dn']).lower()):  # TODO: search with scope=children and remove this check
				continue

			ud.debug(ud.LDAP, ud.INFO, "delete: %r" % (subdn,))

			key = self.identify_udm_object(subdn, subattr)
			subobject_ucs = {'dn': subdn, 'modtype': 'delete', 'attributes': subattr}
			back_mapped_subobject = self._object_mapping(key, subobject_ucs, 'ucs')
			ud.debug(ud.LDAP, ud.WARN, "delete subobject: %r" % (back_mapped_subobject['dn'],))

			if not self._ignore_object(key, back_mapped_subobject):
				# FIXME: this call is wrong!: sync_to_ucs() must be called with a samba_object not with a ucs_object!
				if not self.sync_to_ucs(key, subobject_ucs, back_mapped_subobject['dn'], parent_ucs_object):
					ud.debug(ud.LDAP, ud.WARN, "delete of subobject failed: %r" % (subdn,))
					return False
		return True

	def sync_to_ucs(self, property_type, object, pre_mapped_s4_dn, original_object):
		"""
		Synchronize an object from Samba4-LDAP to UCS Open-LDAP.

		:param property_type:
			the type of the object to be synced, must be part of the mapping. (e.g. "user", "group", "dc", "windowscomputer", etc.)
		:param object:
			A dictionary describing the Samba object.
			modtype: A modification type ("add", "modify", "move", "delete")
			dn: The DN of the object in the UCS-LDAP
			olddn: The olddn of the object object in UCS-LDAP (e.g. on "move" operation)
		:ptype object: dict
		:param pre_mapped_s4_dn:
			pass
		:param original_object:
			pass
		"""
		# NOTE: pre_mapped_s4_dn means: original s4_dn (i.e. before _object_mapping)
		_d = ud.function('ldap.sync_to_ucs')  # noqa: F841
		# this function gets an object from the s4 class, which should be converted into a ucs module

		# if sync is write (sync to S4) or none, there is nothing to do
		if self.property[property_type].sync_mode in ['write', 'none']:
			ud.debug(ud.LDAP, ud.INFO, "sync_to_ucs ignored, sync_mode is %s" % self.property[property_type].sync_mode)
			return True

		ucs_object_dn = object.get('olddn', object['dn'])
		old_object = self.get_ucs_object(property_type, ucs_object_dn)
		if old_object and object['modtype'] == 'add':
			object['modtype'] = 'modify'
		if not old_object and object['modtype'] == 'modify':
			object['modtype'] = 'add'
		if not old_object and object['modtype'] == 'move':
			object['modtype'] = 'add'

		ud.debug(ud.LDAP, ud.PROCESS, 'sync to ucs:   [%14s] [%10s] %r' % (property_type, object['modtype'], object['dn']))

		if object['modtype'] in ('delete', 'move'):
			try:
				del self.group_member_mapping_cache_ucs[object['dn'].lower()]
				ud.debug(ud.LDAP, ud.INFO, "sync_to_ucs: %s removed from UCS group member mapping cache" % object['dn'])
			except KeyError:
				pass
			try:
				del self.group_member_mapping_cache_con[pre_mapped_s4_dn.lower()]
				ud.debug(ud.LDAP, ud.INFO, "sync_to_ucs: %s removed from S4 group member mapping cache" % pre_mapped_s4_dn)
			except KeyError:
				pass

		position = univention.admin.uldap.position(self.baseConfig['ldap/base'])

		if object['dn'] != self.baseConfig['ldap/base']:
			try:
				parent_dn = self.lo.parentDn(object['dn'])
				position.setDn(parent_dn)
				ud.debug(ud.LDAP, ud.INFO, 'sync_to_ucs: set position to %s' % parent_dn)
			except univention.admin.uexceptions.noObject:
				# In this case we use the base DN
				pass

		if old_object:
			uuid = self.lo.getAttr(old_object.dn, 'entryUUID')
			if uuid:
				if self.lockingdb.is_ucs_locked(uuid[0]):
					ud.debug(ud.LDAP, ud.PROCESS, "Unable to sync %s (UUID: %s). The object is currently locked." % (old_object.dn, uuid[0]))
					return False

		try:
			guid_blob = original_object.get('attributes').get('objectGUID')[0]
			guid = str(ndr_unpack(misc.GUID, guid_blob))

			object['changed_attributes'] = []
			if object['modtype'] == 'modify' and original_object:
				old_s4_object = self.s4cache.get_entry(guid)
				ud.debug(ud.LDAP, ud.INFO, "sync_to_ucs: old_s4_object: %s" % old_s4_object)
				ud.debug(ud.LDAP, ud.INFO, "sync_to_ucs: new_s4_object: %s" % original_object['attributes'])
				if old_s4_object:
					object['old_s4_object'] = old_s4_object
					for attr in original_object['attributes']:
						if old_s4_object.get(attr) != original_object['attributes'].get(attr):
							object['changed_attributes'].append(attr)
					for attr in old_s4_object:
						if old_s4_object.get(attr) != original_object['attributes'].get(attr):
							if attr not in object['changed_attributes']:
								object['changed_attributes'].append(attr)
				else:
					object['changed_attributes'] = original_object['attributes'].keys()
			ud.debug(ud.LDAP, ud.INFO, "The following attributes have been changed: %s" % object['changed_attributes'])

			result = False
			if object['modtype'] == 'add':
				ud.debug(ud.LDAP, ud.INFO, "sync_to_ucs: lock S4 guid: %s" % guid)
				if not self.lockingdb.is_s4_locked(guid):
					self.lockingdb.lock_s4(guid)

			if hasattr(self.property[property_type], "ucs_sync_function"):
				result = self.property[property_type].ucs_sync_function(self, property_type, object)
			else:
				module = self.modules[property_type]  # default, determined by mapping filter
				if old_object:
					ud.debug(ud.LDAP, ud.INFO, "sync_to_ucs: using existing target object type: %s" % (old_object.module,))
					module = univention.admin.modules.get(old_object.module)
				if object['modtype'] == 'add':
					result = self.add_in_ucs(property_type, object, module, position)
					self._check_dn_mapping(object['dn'], pre_mapped_s4_dn)
					self.s4cache.add_entry(guid, original_object.get('attributes'))
				if object['modtype'] == 'delete':
					if not old_object:
						ud.debug(ud.LDAP, ud.WARN, "Object to delete doesn't exists, ignore (%r)" % object['dn'])
						result = True
					else:
						result = self.delete_in_ucs(property_type, object, module, position)
					self._remove_dn_mapping(object['dn'], pre_mapped_s4_dn)
					self.s4cache.remove_entry(guid)
				if object['modtype'] == 'move':
					result = self.move_in_ucs(property_type, object, module, position)
					self._remove_dn_mapping(object['olddn'], '')  # we don't know the old s4-dn here anymore, will be checked by remove_dn_mapping
					self._check_dn_mapping(object['dn'], pre_mapped_s4_dn)
					# Check S4cache

				if object['modtype'] == 'modify':
					result = self.modify_in_ucs(property_type, object, module, position)
					self._check_dn_mapping(object['dn'], pre_mapped_s4_dn)
					self.s4cache.add_entry(guid, original_object.get('attributes'))

			if not result:
				ud.debug(ud.LDAP, ud.WARN, "Failed to get Result for DN (%r)" % (object['dn'],))
				return False

			try:
				if object['modtype'] in ['add', 'modify']:
					for f in self.property[property_type].post_ucs_modify_functions:
						ud.debug(ud.LDAP, ud.INFO, "Call post_ucs_modify_functions: %s" % f)
						f(self, property_type, object)
						ud.debug(ud.LDAP, ud.INFO, "Call post_ucs_modify_functions: %s (done)" % f)
			except ldap.SERVER_DOWN:
				raise
			except Exception:  # FIXME: which exception is to be caught?
				self._debug_traceback(ud.ERROR, "failed in post_con_modify_functions")
				result = False

			if result:
				# Always unlock if the sync was successful
				ud.debug(ud.LDAP, ud.INFO, "sync_to_ucs: unlock S4 guid: %s" % guid)
				self.lockingdb.unlock_s4(guid)

			ud.debug(ud.LDAP, ud.INFO, "Return  result for DN (%s)" % object['dn'])
			return result

		except univention.admin.uexceptions.valueInvalidSyntax as msg:
			ud.debug(ud.LDAP, ud.ERROR, "InvalidSyntax: %s (%r)" % (msg, object['dn']))
			return False
		except univention.admin.uexceptions.valueMayNotChange as msg:
			ud.debug(ud.LDAP, ud.ERROR, "Value may not change: %s (%r)" % (msg, object['dn']))
			return False
		except ldap.SERVER_DOWN:
			raise
		except Exception:  # FIXME: which exception is to be caught?
			self._debug_traceback(ud.ERROR, "Unknown Exception during sync_to_ucs")
			return False

	def sync_from_ucs(self, property_type, object, pre_mapped_ucs_dn, old_dn=None, old_ucs_object=None, new_ucs_object=None):
		# dummy: implemented in s4/__init__.py
		return False

	# internal functions

	def _subtree_match(self, dn, subtree):
		_d = ud.function('ldap._subtree_match')  # noqa: F841
		if len(subtree) > len(dn):
			return False
		if subtree.lower() == dn[-len(subtree):].lower():  # FIXME
			return True
		return False

	def _subtree_replace(self, dn, subtree, subtreereplace):  # FIXME: may raise an exception if called with umlauts
		_d = ud.function('ldap._subtree_replace')  # noqa: F841
		if len(subtree) > len(dn):
			return dn
		if subtree.lower() == dn[-len(subtree):].lower():  # FIXME
			return dn[:-len(subtree)] + subtreereplace
		return dn

	# attributes ist ein dictionary von LDAP-Attributen und den zugeordneten Werten
	def _filter_match(self, filter, attributes):
		'''
		versucht eine Liste von Attributen auf einen LDAP-Filter zu matchen
		Besonderheiten des Filters:
		- immer case-sensitive
		- nur * als Wildcard
		- geht "lachser" mit Verschachtelten Klammern um
		'''
		_d = ud.function('ldap._filter_match')  # noqa: F841

		filter_connectors = ['!', '&', '|']

		def list_lower(elements):
			if isinstance(elements, type([])):
				retlist = []
				for l in elements:
					retlist.append(l.lower())
				return retlist
			else:
				return elements

		def dict_lower(dict):
			if isinstance(dict, type({})):
				retdict = {}
				for key in dict:
					retdict[key.lower()] = dict[key]
				return retdict
			else:
				return dict

		def attribute_filter(filter, attributes):
			attributes = dict_lower(attributes)

			pos = string.find(filter, '=')
			if pos < 0:
				raise ValueError('missing "=" in filter: %s' % filter)
			attribute = filter[:pos].lower()
			if not attribute:
				raise ValueError('missing attribute in filter: %s' % filter)
			value = filter[pos + 1:]

			if attribute.endswith(':1.2.840.113556.1.4.803:'):
				# bitwise filter
				attribute_name = attribute.replace(':1.2.840.113556.1.4.803:', '')
				attribute_value = attributes.get(attribute_name)
				if attribute_value:
					try:
						if isinstance(attribute_value, type([])):
							attribute_value = int(attribute_value[0])
						int_value = int(value)
						if ((attribute_value & int_value) == int_value):
							return True
						else:
							return False
					except ldap.SERVER_DOWN:
						raise
					except Exception:
						ud.debug(ud.LDAP, ud.WARN, "attribute_filter: Failed to convert attributes for bitwise filter")
						return False

			if value == '*':
				return attribute in list_lower(attributes.keys())
			elif attribute in attributes:
				return value.lower() in list_lower(attributes[attribute])
			else:
				return False

		def connecting_filter(filter, attributes):

			def walk(filter, attributes):

				def split(filter):
					opened = []
					closed = []
					pos = 0
					level = 0
					for char in filter:
						if char == '(':
							if level == 0:
								opened.append(pos)
							level += 1
						elif char == ')':
							if level == 1:
								closed.append(pos)
							level -= 1
						if level < 0:
							raise ValueError("too many ')' in filter: %s" % filter)
						pos += 1

					if len(opened) != len(closed):
						raise ValueError("'(' and ')' don't match in filter: %s" % filter)
					filters = []
					for i in range(len(opened)):
						filters.append(filter[opened[i] + 1:closed[i]])
					return filters

				if filter[0] == '(':
					if not filter[-1] == ')':
						raise ValueError("matching ) missing in filter: %s" % filter)
					else:
						filters = split(filter)
						results = []
						for filter in filters:
							results.append(subfilter(filter, attributes))
						return results
				else:
					return [subfilter(filter, attributes)]

			if filter[0] == '!':
				return not subfilter(filter[1:], attributes)
			elif filter[0] == '|':
				return 1 in walk(filter[1:], attributes)
			elif filter[0] == '&':
				return 0 not in walk(filter[1:], attributes)

		def subfilter(filter, attributes):

			if filter[0] == '(':
				if not filter[-1] == ')':
					raise ValueError("matching ) missing in filter: %s" % filter)
				else:
					return subfilter(filter[1:-1], attributes)

			elif filter[0] in filter_connectors:
				return connecting_filter(filter, attributes)

			else:
				return attribute_filter(filter, attributes)

		return subfilter(filter, attributes)

	def _ignore_object(self, key, object):
		'''
		parse if object should be ignored because of ignore_subtree or ignore_filter

		:param key: the property_type from the mapping
		:param object: a mapped or unmapped S4 or UCS object
		'''
		_d = ud.function('ldap._ignore_object')  # noqa: F841
		if 'dn' not in object:
			ud.debug(ud.LDAP, ud.INFO, "_ignore_object: ignore object without DN")
			return True  # ignore not existing object

		if self.property.get(key):
			for subtree in self.property[key].ignore_subtree:
				if self._subtree_match(object['dn'], subtree):
					ud.debug(ud.LDAP, ud.INFO, "_ignore_object: ignore object because of subtree match: [%s]" % object['dn'])
					return True

			if self.property[key].ignore_filter and self._filter_match(self.property[key].ignore_filter, object['attributes']):
				ud.debug(ud.LDAP, ud.INFO, "_ignore_object: ignore object because of ignore_filter")
				return True

			if self.property[key].match_filter and not self._filter_match(self.property[key].match_filter, object['attributes']):
				ud.debug(ud.LDAP, ud.INFO, "_ignore_object: ignore object because of match_filter")
				return True

		ud.debug(ud.LDAP, ud.INFO, "_ignore_object: Do not ignore %s" % object['dn'])

		return False

	def _object_mapping(self, key, old_object, object_type='con'):
		"""Create a mapped object from Samba or UCS object definition.

		:param key:
			the mapping key
		:param old_object:
			the object definition in univention directory listener style
		:ptype old_object: dict
		:param object_type:
			"con" if `old_object` is a S4 object.
			"ucs" if `old_object` is a UCS object.
		:ptype object_type: str
		"""
		_d = ud.function('ldap._object_mapping')  # noqa: F841
		ud.debug(ud.LDAP, ud.INFO, "_object_mapping: map with key %s and type %s" % (key, object_type))
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
		object_out = {}
		object_out['attributes'] = {}
		if object and 'modtype' in object:
			object_out['modtype'] = object['modtype']
		else:
			object_out['modtype'] = ''

		# DN mapping

		dn_mapping_stored = []
		for dntype in ['dn', 'olddn']:  # check if all available dn's are already mapped
			if dntype in object:
				ud.debug(ud.LDAP, ud.INFO, "_dn_type %s" % (object_type))  # don't send str(object) to debug, may lead to segfaults

				if (object_type == 'ucs' and self._get_dn_by_ucs(object[dntype])):
					object[dntype] = self._get_dn_by_ucs(object[dntype])
					object[dntype] = self.dn_mapped_to_base(object[dntype], self.lo_s4.base)
					dn_mapping_stored.append(dntype)
				if (object_type != 'ucs' and self._get_dn_by_con(object[dntype])):
					object[dntype] = self._get_dn_by_con(object[dntype])
					object[dntype] = self.dn_mapped_to_base(object[dntype], self.lo.base)
					dn_mapping_stored.append(dntype)

		if key in self.property:
			if hasattr(self.property[key], 'dn_mapping_function'):
				# DN mapping functions
				for function in self.property[key].dn_mapping_function:
					object = function(self, object, dn_mapping_stored, isUCSobject=(object_type == 'ucs'))

		if object_type == 'ucs':
			if key in self.property:
				if hasattr(self.property[key], 'position_mapping'):
					for dntype in ['dn', 'olddn']:
						if dntype in object and dntype not in dn_mapping_stored:
							dn_mapped = object[dntype]
							# note: position_mapping == [] by default
							for mapping in self.property[key].position_mapping:
								dn_mapped = self._subtree_replace(dn_mapped, mapping[0], mapping[1])
							if dn_mapped == object[dntype]:
								if self.lo_s4.base.lower() == dn_mapped[-len(self.lo_s4.base):].lower() and len(self.lo_s4.base) > len(self.lo.base):
									ud.debug(ud.LDAP, ud.INFO, "The dn %s is already converted to the S4 base, don't do this again." % dn_mapped)
								else:
									dn_mapped = self._subtree_replace(object[dntype], self.lo.base, self.lo_s4.base)  # FIXME: lo_s4 may change with other connectors
							object[dntype] = dn_mapped
		else:
			if key in self.property:
				if hasattr(self.property[key], 'position_mapping'):
					for dntype in ['dn', 'olddn']:
						if dntype in object and dntype not in dn_mapping_stored:
							dn_mapped = object[dntype]
							# note: position_mapping == [] by default
							for mapping in self.property[key].position_mapping:
								dn_mapped = self._subtree_replace(dn_mapped, mapping[1], mapping[0])
							if dn_mapped == object[dntype]:
								if self.lo.base.lower() == dn_mapped[-len(self.lo.base):].lower() and len(self.lo.base) > len(self.lo_s4.base):
									ud.debug(ud.LDAP, ud.INFO, "The dn %s is already converted to the UCS base, don't do this again." % dn_mapped)
								else:
									dn_mapped = self._subtree_replace(dn_mapped, self.lo_s4.base, self.lo.base)  # FIXME: lo_s4 may change with other connectors
							object[dntype] = dn_mapped

		object_out = object

		# other mapping
		if object_type == 'ucs':
			if key in self.property:
				for attribute, values in object['attributes'].items():
					if self.property[key].attributes:
						for attr_key in self.property[key].attributes.keys():
							if attribute.lower() == self.property[key].attributes[attr_key].ldap_attribute.lower():
								# mapping function
								if hasattr(self.property[key].attributes[attr_key], 'mapping'):
									if self.property[key].attributes[attr_key].mapping[0]:
										object_out['attributes'][self.property[key].attributes[attr_key].con_attribute] = self.property[key].attributes[attr_key].mapping[0](self, key, object)
								# direct mapping
								else:
									if self.property[key].attributes[attr_key].con_other_attribute:
										object_out['attributes'][self.property[key].attributes[attr_key].con_attribute] = [values[0]]
										object_out['attributes'][self.property[key].attributes[attr_key].con_other_attribute] = values[1:]
									else:
										object_out['attributes'][self.property[key].attributes[attr_key].con_attribute] = values

								# mapping_table
								if self.property[key].mapping_table and attr_key in self.property[key].mapping_table.keys():
									for ucsval, conval in self.property[key].mapping_table[attr_key]:
										if isinstance(object_out['attributes'][self.property[key].attributes[attr_key].con_attribute], type([])):

											ucsval_lower = make_lower(ucsval)
											objectval_lower = make_lower(object_out['attributes'][self.property[key].attributes[attr_key].con_attribute])

											if ucsval_lower in objectval_lower:
												object_out['attributes'][self.property[key].attributes[attr_key].con_attribute][objectval_lower.index(ucsval_lower)] = conval
											elif ucsval_lower == objectval_lower:
												object_out['attributes'][self.property[key].attributes[attr_key].con_attribute] = conval

					if hasattr(self.property[key], 'post_attributes') and self.property[key].post_attributes is not None:
						for attr_key in self.property[key].post_attributes.keys():
							if attribute.lower() == self.property[key].post_attributes[attr_key].ldap_attribute.lower():
								if hasattr(self.property[key].post_attributes[attr_key], 'mapping'):
									if self.property[key].post_attributes[attr_key].mapping[0]:
										object_out['attributes'][self.property[key].post_attributes[attr_key].con_attribute] = self.property[key].post_attributes[attr_key].mapping[0](self, key, object)
								else:
									if self.property[key].post_attributes[attr_key].con_other_attribute:
										object_out['attributes'][self.property[key].post_attributes[attr_key].con_attribute] = [values[0]]
										object_out['attributes'][self.property[key].post_attributes[attr_key].con_other_attribute] = values[1:]
									else:
										object_out['attributes'][self.property[key].post_attributes[attr_key].con_attribute] = values

		else:
			if key in self.property:
				# Filter out Configuration objects w/o DN
				if object['dn'] is not None:
					for attribute, values in object['attributes'].items():
						if self.property[key].attributes:
							for attr_key in self.property[key].attributes.keys():
								if attribute.lower() == self.property[key].attributes[attr_key].con_attribute.lower():
									# mapping function
									if hasattr(self.property[key].attributes[attr_key], 'mapping'):
										# direct mapping
										if self.property[key].attributes[attr_key].mapping[1]:
											object_out['attributes'][self.property[key].attributes[attr_key].ldap_attribute] = self.property[key].attributes[attr_key].mapping[1](self, key, object)
									else:
										if self.property[key].attributes[attr_key].con_other_attribute and object['attributes'].get(self.property[key].attributes[attr_key].con_other_attribute):
											object_out['attributes'][self.property[key].attributes[attr_key].ldap_attribute] = values + \
												object['attributes'].get(self.property[key].attributes[attr_key].con_other_attribute)
										else:
											object_out['attributes'][self.property[key].attributes[attr_key].ldap_attribute] = values

										# mapping_table
									if self.property[key].mapping_table and attr_key in self.property[key].mapping_table.keys():
										for ucsval, conval in self.property[key].mapping_table[attr_key]:
											if isinstance(object_out['attributes'][self.property[key].attributes[attr_key].con_attribute], type([])):

												conval_lower = make_lower(conval)
												objectval_lower = make_lower(object_out['attributes'][self.property[key].attributes[attr_key].ldap_attribute])

												if conval_lower in objectval_lower:
													object_out['attributes'][self.property[key].attributes[attr_key].ldap_attribute][objectval_lower.index(conval_lower)] = ucsval
												elif conval_lower == objectval_lower:
													object_out['attributes'][self.property[key].attributes[attr_key].ldap_attribute] = ucsval

						if hasattr(self.property[key], 'post_attributes') and self.property[key].post_attributes is not None:
							for attr_key in self.property[key].post_attributes.keys():
								if attribute.lower() == self.property[key].post_attributes[attr_key].con_attribute.lower():
									if hasattr(self.property[key].post_attributes[attr_key], 'mapping'):
										if self.property[key].post_attributes[attr_key].mapping[1]:
											object_out['attributes'][self.property[key].post_attributes[attr_key].ldap_attribute] = self.property[key].post_attributes[attr_key].mapping[1](self, key, object)
									else:
										if self.property[key].post_attributes[attr_key].con_other_attribute and object['attributes'].get(self.property[key].post_attributes[attr_key].con_other_attribute):
											object_out['attributes'][self.property[key].post_attributes[attr_key].ldap_attribute] = values + \
												object['attributes'].get(self.property[key].post_attributes[attr_key].con_other_attribute)
										else:
											object_out['attributes'][self.property[key].post_attributes[attr_key].ldap_attribute] = values

		return object_out

	def identify_udm_object(self, dn, attrs):
		"""Get the type of the specified UCS object"""
		dn = unicode(dn, 'utf-8')
		for k in self.property.keys():
			if self.modules[k].identify(dn, attrs):
				return k
			for m in self.modules_others.get(k, []):
				if m and m.identify(dn, attrs):
					return k
