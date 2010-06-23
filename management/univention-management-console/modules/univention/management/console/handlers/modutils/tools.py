#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: like top
#
# Copyright 2007-2010 Univention GmbH
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
import os
import re
from fnmatch import *

import notifier.popen
import univention.management.console as umc

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.top' ).translate

_kernel_categories = []
_kernel_version = ''
_loaded_modules = []

class KernelModule( object ):
	def __init__( self, name, loaded = False, usedby = [] ):
		self.name = name
		self.loaded = loaded
		self.usedby = usedby

def get_kernel_version():
	global _kernel_version
	if _kernel_version:
		return _kernel_version
	regex = re.compile( 'Linux version (?P<version>[^ ]*)' )
	fd = open( '/proc/version' )
	line = fd.readline()
	fd.close()
	match = regex.match( line )
	if not match:
		return ''
	grp = match.groupdict()
	_kernel_version = grp.get( 'version', '' )
	return _kernel_version

def _walk_cats( arg, dirname, fnames ):
	prefix, dirs = arg
	if dirname != prefix:
		dirs.append( dirname[ len( prefix ) : ] )

def get_kernel_categories():
	global _kernel_version, _kernel_categories

	if _kernel_categories:
		return _kernel_categories
	if not _kernel_version:
		get_kernel_version()
	prefix = '/lib/modules/%s/kernel/' % _kernel_version
	dirs = []
	os.path.walk( prefix, _walk_cats, ( prefix, dirs ) )
	cats = []
	for d in dirs:
		parts = d.split( '/', 2 )
		if len( parts ) > 2:
			parts = parts[ : 2 ]
		cat = '/'.join( parts )
		if not cat in cats:
			cats.append( cat )
	_kernel_categories = cats

	return _kernel_categories

def _walk_mods( arg, dirname, fnames ):
	mods, cat, prefix, pattern, loaded_only = arg
	if cat and cat != 'all' and not dirname[ len( prefix ) : ].startswith( cat ):
		return
	for fname in fnames:
		if os.path.isfile( os.path.join( dirname, fname ) ) and fnmatch( fname, pattern ) and \
			   fname.endswith( '.ko' ):
			if not loaded_only or is_kernel_module_loaded( fname[ : -3 ] ):
				mods.append( fname[ : -3 ] )

def get_kernel_modules( category, pattern, loaded_only = False ):
	global _kernel_version, _kernel_categories

	if not _kernel_version:
		get_kernel_version()
	prefix = '/lib/modules/%s/kernel/' % _kernel_version
	mods = []
	os.path.walk( prefix, _walk_mods, ( mods, category, prefix, pattern, loaded_only ) )
	return mods

def _read_loaded_modules():
	global _loaded_modules
	regex = re.compile( '^(?P<module>[^ ]*) (?P<size>[^ ]*) (?P<ref>[^ ]*) (?P<used>[^ ]*) .*' )
	_loaded_modules = []

	mods = []
	fd = open( '/proc/modules' )
	for line in fd:
		match = regex.match( line )
		if not match:
			continue
		grp = match.groupdict()
		if grp[ 'used' ] == '-':
			u = []
		else:
			u = grp[ 'used' ].split( ',' )[ : -1 ]
		_loaded_modules.append( KernelModule( grp[ 'module' ], True, u ) )

def is_kernel_module_loaded( name ):
	global _loaded_modules

	if not _loaded_modules:
		_read_loaded_modules()

	for mod in _loaded_modules:
		if name == mod.name:
			return mod
	return None

def get_kernel_module_info( mods ):
	global _loaded_modules

	_loaded_modules = []
	infos = []
	for mod in mods:
		m = is_kernel_module_loaded( mod )
		if m:
			infos.append( m )
		else:
			infos.append( KernelModule( mod ) )

	return infos
