#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Debmirror
#  mirrors a repository server
#
# Copyright 2009-2015 Univention GmbH
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

import os
import errno
import re
import subprocess
import itertools
import logging

from tools import UniventionUpdater, UCS_Version, NullHandler
try:
	import univention.debug as ud
except ImportError:
	import univention.debug2 as ud

class UniventionMirror( UniventionUpdater ):
	def __init__(self, check_access=True):
		UniventionUpdater.__init__(self, check_access)
		self.log = logging.getLogger('updater.Mirror')
		self.log.addHandler(NullHandler())
		self.repository_path =  self.configRegistry.get( 'repository/mirror/basepath', '/var/lib/univention-repository' )

		version_end = self.configRegistry.get('repository/mirror/version/end') or self.current_version
		self.version_end = UCS_Version(version_end)
		version_start = self.configRegistry.get('repository/mirror/version/start') or (self.version_major, 0, 0)
		self.version_start = UCS_Version(version_start)
		# set architectures to mirror
		archs = self.configRegistry.get( 'repository/mirror/architectures', '' )
		if archs:
			self.architectures = archs.split( ' ' )

	def config_repository( self ):
		""" Retrieve configuration to access repository. Overrides UniventionUpdater. """
		self.online_repository = self.configRegistry.is_true('repository/mirror', True)
		self.repository_server = self.configRegistry.get( 'repository/mirror/server', 'updates.software-univention.de' )
		self.repository_port = self.configRegistry.get( 'repository/mirror/port', '80' )
		self.repository_prefix = self.configRegistry.get( 'repository/mirror/prefix', '' ).strip('/')
		self.sources = self.configRegistry.is_true('repository/mirror/sources', False)
		self.http_method = self.configRegistry.get('repository/mirror/httpmethod', 'HEAD').upper()
		self.script_verify = self.configRegistry.is_true('repository/mirror/verify', True)

	def release_update_available(self, ucs_version=None, errorsto='stderr'):
		'''Check if an update is available for the ucs_version'''
		if not ucs_version:
			ucs_version = self.current_version
		return self.get_next_version(UCS_Version(ucs_version), [], errorsto)

	def mirror_repositories( self ):
		'''uses apt-mirror to copy a repository'''
		# check if the repository directory structure exists, otherwise create it
		if not os.path.exists( self.repository_path ):
			os.makedirs( self.repository_path )

		# these sub-directories are required by apt-mirror
		for dir in ( 'skel', 'mirror', 'var' ):
			path = os.path.join( self.repository_path, dir )
			if not os.path.exists( path ):
				os.makedirs( path )
		path = os.path.join(self.repository_path, 'mirror', 'univention-repository')
		try:
			os.symlink('.', path)
		except OSError, ex:
			if ex.errno != errno.EEXIST:
				raise

		log = open('/var/log/univention/repository.log', 'a')
		try:
			return subprocess.call('/usr/bin/apt-mirror', stdout=log, stderr=log, shell=False)
		finally:
			log.close()

	def mirror_update_scripts( self ):
		'''mirrors the preup.sh and postup.sh scripts'''
		start = self.version_start
		end = self.version_end
		parts = self.parts
		archs = ('all',)

		repos = self._iterate_version_repositories(start, end, parts, archs) # returns generator

		start_errata = UCS_Version((start.major, start.minor, 1))  # errata updates start with 'errata1'
		end_errata = UCS_Version((end.major, end.minor, 999)) # get all available for mirror
		errata = self._iterate_errata_repositories(start_errata, end_errata, parts, archs) # returns generator

		components = self.get_components(only_localmirror_enabled=True)
		comp = self._iterate_component_repositories(components, start, end, archs, for_mirror_list=True) # returns generator

		all_repos = itertools.chain(repos, errata, comp) # concatenate all generators into a single one
		for server, struct, phase, path, script in UniventionUpdater.get_sh_files(all_repos, self.script_verify):
			self.log.info('Mirroring %s:%r/%s to %s', server, struct, phase, path)
			assert script is not None, 'No script'

			# use prefix if defined - otherwise file will be stored in wrong directory
			if server.prefix:
				filename = os.path.join(self.repository_path, 'mirror', server.prefix, path)
			else:
				filename = os.path.join(self.repository_path, 'mirror', path)

			# Check disabled, otherwise files won't get refetched if they change on upstream server
			#if os.path.exists(filename):
			#	ud.debug(ud.NETWORK, ud.ALL, "Script already exists, skipping: %s" % filename)
			#	continue

			dirname = os.path.dirname(filename)
			try:
				os.makedirs(dirname, 0755)
			except OSError, ex:
				if ex.errno != errno.EEXIST:
					raise
			fd = open(filename, "w")
			try:
				fd.write(script)
				ud.debug(ud.ADMIN, ud.INFO, "Successfully mirrored: %s" % filename)
			finally:
				fd.close()

	def list_local_repositories( self, start = None, end = None, maintained = True, unmaintained = False ):
		'''
		This function returns a sorted list of local (un)maintained repositories.
		Arguments: start: smallest version that shall be returned (type: UCS_Version)
				   end:   largest version that shall be returned (type: UCS_Version)
				   maintained:   True if list shall contain maintained repositories
				   unmaintained: True if list shall contain unmaintained repositories
		Returns: a list of ( directory, UCS_Version, is_maintained ) tuples.
		'''
		result = []
		repobase = os.path.join( self.repository_path, 'mirror')
		RErepo = re.compile('^%s/(\d+[.]\d)/(maintained|unmaintained)/(\d+[.]\d+-\d+)$' % (re.escape(repobase),))
		for dirname, subdirs, files in os.walk(repobase):
			match = RErepo.match(dirname)
			if match:
				if not maintained and match.group(2) == 'maintained':
					continue
				if not unmaintained and match.group(2) == 'unmaintained':
					continue

				version = UCS_Version( match.group(3) )
				# do not compare start with None by "!=" or "=="
				if not start is None and version < start:
					continue
				# do not compare end with None by "!=" or "=="
				if not end is None and end < version:
					continue

				result.append( ( dirname, version, match.group(2) == 'maintained' ) )

		result.sort(lambda x,y: cmp(x[1], y[1]))

		return result

	def update_dists_files( self ):
		last_version = None
		last_dirname = None
		repobase = os.path.join( self.repository_path, 'mirror')

		# iterate over all local repositories
		for dirname, version, is_maintained in self.list_local_repositories( start=self.version_start, end=self.version_end, unmaintained = False ):
			if version.patchlevel == 0:
				archlist = ( 'i386', 'amd64' )
				for arch in archlist:
					# create dists directory if missing
					d = os.path.join( dirname, 'dists/univention/main/binary-%s' % arch )
					if not os.path.exists( d ):
						os.makedirs( d, 0755 )

					# truncate dists packages file
					fn = os.path.join( d, 'Packages' )
					open(fn,'w').truncate(0)

					# fetch all downloaded repository packages files and ...
					for cur_packages in ( os.path.join( dirname, 'all/Packages' ), os.path.join( dirname, arch, 'Packages' ) ):
						# ...if it exists....
						if os.path.exists( cur_packages ):
							# ... convert that file and append it to new dists packages file
							subprocess.call( 'sed -re "s|^Filename: %s/|Filename: |" < %s >> %s' % (version, cur_packages, fn ), shell=True )

					# append existing Packages file of previous versions
					if not last_version is None: # do not compare last_version with None by "!=" or "=="
						# do not append Packages from other major versions
						if last_version.major == version.major:
							# get last three items of pathname and build prefix
							prefix = '../../../%s' % os.path.join( *( last_dirname.split('/')[-3:]) )
							subprocess.call( 'sed -re "s|^Filename: %s/|Filename: %s/%s/|" < %s/dists/univention/main/binary-%s/Packages >> %s' % (
								arch, prefix, arch, last_dirname, arch, fn ), shell=True )

					# create compressed copy of dists packages files
					subprocess.call( 'gzip < %s > %s.gz' % (fn, fn), shell=True )

				# remember last version and directory name
				last_version = version
				last_dirname = dirname


	def run( self ):
		'''starts the mirror process'''
		self.mirror_repositories()
		self.mirror_update_scripts()
		self.update_dists_files()

if __name__ == '__main__':
	import doctest
	doctest.testmod()
