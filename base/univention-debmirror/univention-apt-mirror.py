#!/usr/bin/python
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

import os
import subprocess
import urllib

from univention.management.console.handlers.update.tools import UniventionUpdater

class UniventionMirror( UniventionUpdater ):
	def __init__( self ):
		UniventionUpdater.__init__( self )
		self.repository_server = self.configRegistry.get( 'repository/mirror/server', 'apt.univention.de' )
		self.repository_path =  self.configRegistry.get( 'repository/mirror/basepath', '/var/lib/univention-repository' 		self.repository_prefix =  self.configRegistry.get( 'repository/mirror/prefix', 'univention-repository' )

	def retrieve_url( self, path ):
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
		if not os.path.exists( self.repository_path ):
			os.makedirs( self.repository_path )
		for dir in ( 'skel', 'mirror', 'var' ):
			path = os.path.join( self.repository_path, dir )
			if not os.path.exists( path ):
				os.makedirs( path )

		return subprocess.call( '/usr/bin/apt-mirror', shell = True )

	def mirror_update_scripts( self ):
		repos = self.print_version_repositories()

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
				self.copy_script( script, uri, os.path.join( self.repository_path, path[ 1 : ] ) )

	def run( self ):
		self.mirror_repositories()
		self.mirror_update_scripts()

if __name__ == '__main__':
	mirror = UniventionMirror()
	mirror.run()
