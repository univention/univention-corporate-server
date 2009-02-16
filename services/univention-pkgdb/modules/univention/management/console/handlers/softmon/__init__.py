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
SYSTEMPREFIX='SavedSoftMonSystemSearch-'
PACKAGEPREFIX='SavedSoftMonPackageSearch-'
SUFFIX='.pickle'

name = 'softmon'
icon = 'softmon/module'
short_description = _( 'Software monitor' )
long_description = _( 'Monitor software status on all your systems' )
categories = [ 'all', 'system' ]

filter_type = umc.MultiDictValue( _( 'Search filters' ),
								  syntax = { 'key' : _syntax.SoftMonSystemSearchKey(),
											 'op' : _syntax.SoftMonSearchOperator(),
											 'pattern' : umc.String( '' ) } )
command_description = {
	'softmon/system/search' : umch.command(
		short_description = _( 'Search systems' ),
		method = 'softmon_system_search',
		values = { 'filter' : filter_type },
		startup = True,
	),
	'softmon/package/search' : umch.command(
		short_description = _( 'Search packages' ),
		method = 'softmon_package_search',
		values = { 'filter' : filter_type },
		startup = True,
	),
	'softmon/problem/identification' : umch.command(
		short_description = _( 'Problem identification' ),
		method = 'softmon_problem_identification',
		values = { 'filter' : filter_type },
		startup = True,
	),
}




class handler( umch.simpleHandler, _revamp.Web ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )
		self._system_roles = None
		self._system_versions = None
		self.selectedStates={ '0': 'unkown', '1':'install', '2':'hold', '3':'deinstall', '4':'purge' }
		self.instStates={ '0': 'ok', '1': 'reinst required', '2': 'hold', '3': 'hold reinst required' }
		self.currentStates={ '0': 'not installed', '1': 'unpacked', '2': 'half-configured', '3': 'uninstalled', '4': 'half-installed', '5': 'config-files', '6': 'installed' }


	def _get_system_roles_and_versions( self ):
		if not self._system_versions == None and not self._system_roles == None:
			ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: system roles and versions already set" )
			return

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
		except:
			import traceback, sys
			info = sys.exc_info()
			lines = traceback.format_exception(*info)
			ud.debug( ud.ADMIN, ud.ERROR, 'TRACEBACK IN SOFTMON\n%s' % ''.join(lines) )

		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: trying to get system roles and versions: done" )
		ud.debug( ud.ADMIN, ud.INFO, 'SOFTMON: system roles=%s' % self._system_roles )
		ud.debug( ud.ADMIN, ud.INFO, 'SOFTMON: system versions=%s' % self._system_versions )


	def softmon_system_search( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: softmon_system_search: object.options=%s" % object.options )
		cb = notifier.Callback( self._softmon_system_search2, object )
		func = notifier.Callback( self._get_system_roles_and_versions )
		thread = notifier.threads.Simple( 'softmon', func, cb )
		thread.run()


	def _softmon_system_search2( self, thread, result, object ):
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: _softmon_system_search2: object.options=%s" % object.options )

		# stop here if thread failed
		if self._system_versions == None or self._system_roles == None:
			report = _('Loading system roles and system versions from Univention PKGDB failed. Please check installation of univention-pkgdb and run "univention-pkgdb-check" and "univention-pkgdb-scan".')
			self.finished( object.id(), {}, report = report, success = False )

		ss = SearchSavesets(prefix=SYSTEMPREFIX)
		result = {}

		# set system roles / versions
		result[ 'system_roles' ] = self._system_roles
		if self._system_roles:
			result[ 'system_roles_default' ] = self._system_roles[0]
		result[ 'system_versions' ] = self._system_versions
		if self._system_versions:
			result[ 'system_versions_default' ] = self._system_versions[0]

		# delete search filter
		if object.options.get('delete', False):
			searchname = object.options.get('searchname', None)
			if searchname:
				ss.delete( searchname )
			object.incomplete = True
			object.options['searchname'] = None

		# load search filters if selected
		searchname = object.options.get('searchname', None)
		if searchname:
			searchfilter = ss.load( searchname )
			object.incomplete = True
			result[ 'filter_items' ] = searchfilter
			result[ 'current_search' ] = searchname

		# save search filter
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
			result[ 'filter_items' ] = object.options.get('filter', None)

			if object.options.get('search', False):
				query, tmp1 = _psql.convertSearchFilterToQuery( object.options.get('filter',[]) )
				ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: query: %s" % query )

				cb = notifier.Callback( self._softmon_system_search3, object, result )
				func = notifier.Callback( self._get_systems_by_query, query )
				thread = notifier.threads.Simple( 'softmon', func, cb )
				thread.run()


	def _softmon_system_search3( self, thread, threadresult, object, result ):
		search_results = []
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: _softmon_system_search3: query_result: %s" % threadresult )
		for item in threadresult:
			search_results.append( { 'name': item[0],
									 'version': item[1],
									 'role': item[2],
									 'date': item[3],
									 'dn': item[4] } )
		result[ 'search_results' ] = search_results
		self.finished( object.id(), result )


	def _get_systems_by_query( self, query ):
		try:
			pkgdb_connect_string = updb.sql_create_localconnectstring( umc.baseconfig['hostname']  )
			if len(pkgdb_connect_string) < 1:
				ud.debug( ud.ADMIN, ud.ERROR, "SOFTMON: cannot get localconnectstring")
				return None

			query_result = updb.sql_get_systems_by_query( pkgdb_connect_string, query )
		except:
			import traceback
			info = sys.exc_info()
			lines = traceback.format_exception(*info)
			ud.debug(ud.ADMIN, ud.ERROR, 'CAUGHT EXCEPTION!\n%s' % ''.join(lines))
			return None
		# query_result = [['master200', '2.0-0-0', 'domaincontroller_master', '2007-11-02 15:26:30', 'cn=master200,cn=dc,cn=computers,dc=nstx,dc=de']]
		return query_result



	def softmon_package_search( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: object.options=%s" % object.options )
		cb = notifier.Callback( self._softmon_package_search2, object )
		func = notifier.Callback( self._get_system_roles_and_versions )
		thread = notifier.threads.Simple( 'softmon', func, cb )
		thread.run()


	def _softmon_package_search2( self, thread, result, object ):
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: object.options=%s" % object.options )

		# stop here if thread failed
		if self._system_versions == None or self._system_roles == None:
			report = _('Loading system roles and system versions from Univention PKGDB failed. Please check installation of univention-pkgdb and run "univention-pkgdb-check" and "univention-pkgdb-scan".')
			self.finished( object.id(), {}, report = report, success = False )

		ss = SearchSavesets(prefix=PACKAGEPREFIX)
		result = {}

		# set system roles / versions
		result[ 'system_versions' ] = self._system_versions
		if self._system_versions:
			result[ 'system_versions_default' ] = self._system_versions[0]

		# delete search filter
		if object.options.get('delete', False):
			searchname = object.options.get('searchname', None)
			if searchname:
				ss.delete( searchname )
			object.incomplete = True
			object.options['searchname'] = None

		# load search filters if selected
		searchname = object.options.get('searchname', None)
		if searchname:
			searchfilter = ss.load( searchname )
			object.incomplete = True
			result[ 'filter_items' ] = searchfilter
			result[ 'current_search' ] = searchname

		# save search filter
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
			result[ 'filter_items' ] = object.options.get('filter', None)

			ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: search for: %s" % object.options.get( 'filter', [] ) )

			if object.options.get('search', False):
				query, need_join_systems = _psql.convertSearchFilterToQuery( object.options.get('filter',[]) )
				ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: query: %s" % query )

				cb = notifier.Callback( self._softmon_system_search4, object, result )
				func = notifier.Callback( self._get_packages_by_query, query, need_join_systems )
				thread = notifier.threads.Simple( 'softmon', func, cb )
				thread.run()


	def _softmon_system_search4( self, thread, threadresult, object, result ):
		search_results = []
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: query_result: %s" % threadresult )
		for item in threadresult:
			search_results.append( { 'sysname': item[0],
									 'pkgname': item[1],
									 'version': item[2],
									 'date': item[3],
									 'selected_state': self.selectedStates[ str(item[5]) ],
									 'installation_state': self.instStates[ str(item[6]) ],
									 'current_state': self.currentStates[ str(item[7]) ],
									 } )
		result[ 'search_results' ] = search_results
		self.finished( object.id(), result )


	def _get_packages_by_query( self, query, need_join_systems ):
		try:
			pkgdb_connect_string = updb.sql_create_localconnectstring( umc.baseconfig['hostname']  )
			if len(pkgdb_connect_string) < 1:
				ud.debug( ud.ADMIN, ud.ERROR, "SOFTMON: cannot get localconnectstring")
				return None

			query_result = updb.sql_get_packages_in_systems_by_query( pkgdb_connect_string, query, need_join_systems )
		except:
			import traceback
			info = sys.exc_info()
			lines = traceback.format_exception(*info)
			ud.debug(ud.ADMIN, ud.ERROR, 'CAUGHT EXCEPTION!\n%s' % ''.join(lines))
			return None

		# query_result = [['master200', 'univention-pkgdb', '1.0.5-1.51.200710191112', '2007-11-06 09:49:59', 'i', 1, 0, 6], ... ]
		return query_result



	def softmon_problem_identification( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: softmon_problem_identification: object.options=%s" % object.options )
		result = {}
		result['current_check'] = object.options.get('check', None)
		result['max_results_default'] = object.options.get('max_results', None)

		# get outdated_systems_version
		outdated_systems_version = '2.0-0'
		if umc.baseconfig.has_key('version/version') and umc.baseconfig.has_key('version/patchlevel'):
			outdated_systems_version = '%s-%s' % (umc.baseconfig['version/version'], umc.baseconfig['version/patchlevel'])
			if umc.baseconfig.has_key('version/security-patchlevel'):
				outdated_systems_version = '%s-%s' % (outdated_systems_version, umc.baseconfig['version/security-patchlevel'])
		result['outdated_systems_version'] = object.options.get('outdated_systems_version', outdated_systems_version)

		if object.incomplete or not result['current_check'] or not object.options.get('search', False):
			ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: incomplete" )
			self.finished( object.id(), result )
			return

		if result['current_check'] == 'outdated_systems':
			query = "sysversion<'%s'" % result['outdated_systems_version']
			func = notifier.Callback( self._get_systems_by_query, query )

		elif result['current_check'] == 'failed_packages':
			query = "currentstate!='0' and currentstate!='6' and selectedstate!='3'"
			func = notifier.Callback( self._get_packages_by_query, query, '1' )

		cb = notifier.Callback( self._softmon_problem_identification2, object, result )
		thread = notifier.threads.Simple( 'softmon', func, cb )
		thread.run()



	def _softmon_problem_identification2( self, thread, threadresult, object, result ):
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: _softmon_problem_identification2: object.options=%s" % object.options )
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: query_result: %s" % threadresult )

		check_results = []

		if result['current_check'] == 'outdated_systems' and threadresult:
			for item in threadresult:
				check_results.append( { 'name': item[0],
										 'version': item[1],
										 'role': item[2],
										 'date': item[3],
										 'dn': item[4] } )
		elif result['current_check'] == 'failed_packages' and threadresult:
			for item in threadresult:
				check_results.append( { 'sysname': item[0],
										 'pkgname': item[1],
										 'version': item[2],
										 'date': item[3],
										 'selected_state': self.selectedStates[ str(item[5]) ],
										 'installation_state': self.instStates[ str(item[6]) ],
										 'current_state': self.currentStates[ str(item[7]) ],
										 } )

		result[ 'check_results' ] = check_results
		self.finished( object.id(), result )






class SearchSavesets:
	def __init__(self, path=SAVEPATH, prefix=SYSTEMPREFIX, suffix=SUFFIX):
		self.path=path
		self.prefix=prefix
		self.suffix=suffix

	def save(self, name, obj):
		filename = os.path.join( self.path, self.prefix + name + self.suffix )
		try:
			fd = open( filename, 'w' )
		except Exception, e:
			ud.debug( ud.ADMIN, ud.ERROR, "SOFTMON: cannot save object to file %s" % filename )
		pickle.dump( obj, fd )
		fd.close()

	def load(self, name):
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

	def delete(self, name):
		filename = os.path.join( self.path, self.prefix + name + self.suffix )
		try:
			os.unlink( filename )
		except Exception, e:
			ud.debug( ud.ADMIN, ud.ERROR, "SOFTMON: cannot delete file %s" % filename )

