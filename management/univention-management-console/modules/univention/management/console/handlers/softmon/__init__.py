#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module softmon: softeare monitor
#
# Copyright (C) 2007 Univention GmbH
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

import univention.management.console as umc
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct

import os, re, glob, pickle, sre

import notifier.popen

import _revamp
import _syntax
import _psql

import univention.debug as ud

import univention.pkgdb as updb

_ = umc.Translation( 'univention.management.console.handlers.softmon' ).translate

SAVEPATH="/var/lib/univention-management-console"
PREFIX='SavedSoftMonSearch-'
SUFFIX='.pickle'

name = 'softmon'
icon = 'softmon/module'
short_description = _( 'Software Monitor' )
long_description = _( 'Monitor Software Status on all Your Systems' )
categories = [ 'all', 'system' ]

filter_type = umc.MultiDictValue( _( 'Search Filters' ),
								  syntax = { 'key' : _syntax.SoftMonSystemSearchKey(),
											 'op' : _syntax.SoftMonSearchOperator(),
											 'pattern' : umc.String( '' ) } )
command_description = {
	'softmon/system/search' : umch.command(
		short_description = _( 'Search Systems' ),
		method = 'softmon_system_search',
		values = { 'filter' : filter_type,
					'maxresults' : filter_type },
		startup = True,
	),
	'softmon/package/search' : umch.command(
		short_description = _( 'Search Packages' ),
		method = 'softmon_package_search',
		values = { 'pattern' : umc.Boolean( _( 'Loaded modules only' ) ),
				    },
		startup = True,
	),
}




class handler( umch.simpleHandler, _revamp.Web ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )
		self._system_roles = None
		self._system_versions = None


	def _get_system_roles_and_versions( self ):
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: trying to get system roles and versions" )
		# load system roles
		try:
			pkgdb_connect_string = updb.sql_create_localconnectstring( umc.baseconfig['hostname']  )
			if len(pkgdb_connect_string) > 0:
				systemroles  = updb.sql_getall_systemroles( pkgdb_connect_string )
				if systemroles:
					self._system_roles = []
					for s in systemroles:
						self._system_roles.append( (s[0], s[0]) )

				# load system versions
				systemversions  = updb.sql_getall_systemversions( pkgdb_connect_string )
				if systemversions:
					self._system_versions = []
					for s in systemversions:
						self._system_versions.append( (s[0], s[0]) )
		except :
			import traceback, sys
			info = sys.exc_info()
			lines = traceback.format_exception(*info)
			ud.debug( ud.ADMIN, ud.ERROR, 'TRACEBACK IN SOFTMON\n%s' % ''.join(lines) )

		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: trying to get system roles and versions: done" )
		ud.debug( ud.ADMIN, ud.INFO, 'SOFTMON: system roles=%s' % self._system_roles )
		ud.debug( ud.ADMIN, ud.INFO, 'SOFTMON: system versions=%s' % self._system_versions )


	def softmon_system_search( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: object.options=%s" % object.options )
		cb = notifier.Callback( self._softmon_system_search2, object )
		func = notifier.Callback( self._get_system_roles_and_versions )
		thread = notifier.threads.Simple( 'softmon', func, cb )
		thread.run()


	def _softmon_system_search2( self, thread, result, object ):
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: object.options=%s" % object.options )

		# stop here if thread failed
		if self._system_versions == None or self._system_roles == None:
			report = _('Loading of system roles and system versions failed. Please check installation of univention-pkgdb and run ')
			self.finished( object.id(), {}, report = report, success = False )

		ss = SearchSavesets()
		result = {}

		# set system roles / versions
		result[ 'system_roles' ] = self._system_roles
		if self._system_roles:
			result[ 'system_roles_default' ] = self._system_roles[0]
		result[ 'system_versions' ] = self._system_versions
		if self._system_versions:
			result[ 'system_versions_default' ] = self._system_versions[0]


		# load search filters if selected
		searchname = object.options.get('searchname', None)
		if searchname:
			searchfilter = ss.load( searchname )
			object.incomplete = True
			result[ 'filter_items' ] = searchfilter
			result[ 'current_search' ] = searchname


		# save search filters
		if object.options.get('save', False):
			newsearchname = object.options.get('newsearchname', None)
			searchfilter = object.options.get('filter', None)
			if newsearchname:
				ss.save( newsearchname, searchfilter )
			object.incomplete = True
			result[ 'filter_items' ] = searchfilter


		max_results_default = object.options.get('max_results', None)
		if max_results_default:
			result[ 'max_results_default' ] = max_results_default

		# load existing searches
		result[ 'saved_searches' ] = ss.listfiles()

		if object.incomplete:
			self.finished( object.id(), result )
		else:
			ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: search for: %s" % object.options.get( 'filter', [] ) )

			if object.options.get('search', False):
				query = _psql.convertSearchFilterToQuery( object.options.get('filters',[]) )
				pkgdb_connect_string = updb.sql_create_localconnectstring( umc.baseconfig['hostname']  )
				if len(pkgdb_connect_string) > 0:
					query_result = updb.sql_get_systems_by_query( pkgdb_connect_string, query )
					ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: query_result = %s" % query_result )

# query_result = [['master200', '2.0-0-0', 'domaincontroller_master', '2007-11-02 15:26:30', 'cn=master200,cn=dc,cn=computers,dc=nstx,dc=de']]

#				cb = notifier.Callback( self._softmon_system_search2, object )
#				func = notifier.Callback( self._get_system_roles_and_versions )
#				thread = notifier.threads.Simple( 'softmon', func, cb )
#				thread.run()


	def _softmon_system_search3( self, thread, threadresult, object, result ):
		self.finished( object.id(), result )




class SearchSavesets:
	def __init__(self,path=SAVEPATH,prefix=PREFIX,suffix=SUFFIX):
		self.path=path
		self.prefix=prefix
		self.suffix=suffix

	def save(self, name, obj ):
		filename = os.path.join( self.path, self.prefix + name + self.suffix )
		try:
			fd = open( filename, 'w' )
		except Exception, e:
			ud.debug( ud.ADMIN, ud.ERROR, "SOFTMON: cannot save object to file %s" % filename )
		pickle.dump( obj, fd )
		fd.close()

	def load(self,name ):
		filename = os.path.join( self.path, self.prefix + name + self.suffix )
		obj = None
		try:
			fd = open( filename, 'r' )
			obj = pickle.load( fd )
		except Exception, e:
			ud.debug( ud.ADMIN, ud.ERROR, "SOFTMON: cannot read object from file %s" % filename )
		fd.close()
		return obj

	def listfiles(self):
		pattern = os.path.join( self.path, self.prefix + '*' + self.suffix )
		files=glob.glob(pattern)
		sets=[]
		for fn in files:
			if os.path.isfile(fn):
				tmp=sre.sub(self.path + '/' + self.prefix, '', fn)
				name=sre.sub(self.suffix, '', tmp)
				sets.append(name)
		return sets

	def delete(self,name ):
		filename = os.path.join( self.path, self.prefix + name + self.suffix )
		try:
			os.unlink( filename )
		except Exception, e:
			ud.debug( ud.ADMIN, ud.ERROR, "SOFTMON: cannot delete file %s" % filename )

