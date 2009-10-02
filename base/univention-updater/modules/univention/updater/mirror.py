#!/usr/bin/python2.4
#
# Univention Debmirror
#  mirrors a repository server
#
# Copyright (C) 2009 Univention GmbH
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

import os, re
import subprocess
import urllib

from tools import UniventionUpdater, UCS_Version

class UniventionMirror( UniventionUpdater ):
	def __init__( self ):
		UniventionUpdater.__init__( self )
		self.online_repository = self.configRegistry.get( 'repository/mirror', 'yes' )
		self.repository_server = self.configRegistry.get( 'repository/mirror/server', 'apt.univention.de' )
		self.repository_path =  self.configRegistry.get( 'repository/mirror/basepath', '/var/lib/univention-repository' )
		self.repository_prefix = self.configRegistry.get( 'repository/mirror/prefix', '' )
		if not self.repository_prefix and self.net_path_exists( '/univention-repository/' ):
			self.repository_prefix = 'univention-repository'
			
		if self.configRegistry.has_key( 'repository/mirror/version/end' ):
			self.version_end = UCS_Version( self.configRegistry.get( 'repository/mirror/version/end' ) )
		else:
			self.version_end = UCS_Version( ( self.version_major, self.version_minor, self.patchlevel ) )
		if self.configRegistry.has_key( 'repository/mirror/version/start' ):
			self.version_start = UCS_Version( self.configRegistry.get( 'repository/mirror/version/start' ) )
		else:
			self.version_start = UCS_Version( ( self.version_major, 0, 0 ) )
		# set architectures to mirror
		archs = self.configRegistry.get( 'repository/mirror/architectures', '' )
		if archs:
			self.architectures = archs.split( ' ' )

	def retrieve_url( self, path ):
		'''downloads the given path from the repository server'''
		# path MUST NOT contain the schema and hostname
		proxy_headers = self.open_connection()
		site = '%s/%s/%s' % (self.proxy_prefix, self.repository_prefix, path)

		replace_slash = re.compile ('[/]{2,}')
		site = replace_slash.sub ('/', site)
		if not site.startswith ('http://') and proxy_headers:
			site = 'http://%s' % site

		if proxy_headers:
			self.connection.putrequest('GET', site, skip_host=1, skip_accept_encoding=1)
		else:
			self.connection.putrequest('GET', site)

		if proxy_headers:
			for k, v in proxy_headers.items ():
				self.connection.putheader (k, v)
		try:
			self.connection.endheaders ()
			response = self.connection.getresponse()
			body = response.read()

			if response.status == 200:
				self.close_connection()
				return body
		except:
			import traceback
			print traceback.format_exc ()

		self.close_connection()
		return None

	def copy_script( self, script, repository, directory ):
		'''retriebes a script from a remote repository and copies it to
		the local repository'''
		filename = os.path.join( directory, script )
		if os.path.exists( filename ):
			return False
		body = self.retrieve_url( '%s/%s' % ( repository, script ) )
		if not body:
			return False
		fd = open( filename, 'w' )
		fd.write( body )
		fd.close()

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

		return subprocess.call( '/usr/bin/apt-mirror >>/var/log/univention/repository.log', shell = True )

	def mirror_update_scripts( self ):
		'''mirrors the preup.sh and postup.sh scripts'''
		# check the main repositories for preup and postup scripts
		repos = self.print_version_repositories( start = self.version_start, end = self.version_end )

		for repo in repos.split( '\n' ):
			if not repo:
				continue
			deb, url, comp = repo.split( ' ' )
			if deb != 'deb':
				continue

			uri = '%s%s' % ( url, comp )
			schema, rest = urllib.splittype( uri )
			host, path = urllib.splithost( rest )
			for script in ( 'preup.sh', 'postup.sh' ):
				self.copy_script( script, path, os.path.join( self.repository_path, 'mirror', path[ 1 : ] ) )

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
		RErepo = re.compile('^%s/(\d+[.]\d)/(maintained|unmaintained)/(\d+[.]\d+-\d+)$' % repobase )
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
