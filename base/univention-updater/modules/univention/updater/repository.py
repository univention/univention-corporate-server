#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: helper functions for managing repositories
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

import gzip
import os
import shutil
import subprocess
import sys

import univention.config_registry as ucr

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

# constants
ARCHITECTURES = ( 'i386', 'amd64', 'all' )

class TeeFile( object ):
	'''Writes the given string to serveral files at once. Could by used
	with the print statement'''
	def __init__( self, fds = [] ):
		if not fds:
			self.fds = [ sys.stdout ]
		else:
			self._fds = fds

	def write( self, str ):
		for fd in self._fds:
			fd.write( str )
			fd.flush()

def gzip_file( filename ):
	f_in = open( filename, 'rb')
	f_out = gzip.open( '%s.gz' % filename, 'wb' )
	f_out.writelines( f_in )
	f_out.close()
	f_in.close()

def copy_package_files( source_dir, dest_dir ):
	# copy package files
	for filename in os.listdir( source_dir ):
		if os.path.isfile( os.path.join( source_dir, filename ) ) and filename.endswith( '.deb' ):
			try:
				arch = filename[ filename.rfind( '_' ) + 1 : -4 ]
			except:
				print >> sys.stderr, "Warning: Could not determine architecture of package '%s'" % filename
				continue
			src = os.path.join( source_dir, filename )
			src_size = os.stat( src )[ 6 ]
			dest = os.path.join( dest_dir, arch, filename )
			# package already exists with correct size
			if os.path.isfile( dest ) and os.stat( dest )[ 6 ] == src_size:
				continue
			try:
				shutil.copy2( src, dest )
			except shutil.Error, e:
				print >> sys.stderr, "Copying package '%s' failed." % filename
		if filename in ('preup.sh', 'preup.sh.gpg', 'postup.sh', 'postup.sh.gpg'):
			src = os.path.join( source_dir, filename )
			dest = os.path.join( dest_dir, 'all', filename )
			shutil.copy2( src, dest )
			

def update_indexes( base_dir, update_only = False, dists = False, stdout = None, stderr = None ):
	# redirekt output
	if not stdout:
		stdout = sys.stdout
	if not stderr:
		stderr = sys.stderr

	print >> stdout, 'Creating indexes ...',
	stdout.flush()
	for arch in ARCHITECTURES:
		if not os.path.isdir( os.path.join( base_dir, arch ) ):
			continue
		if update_only and not os.path.isfile( os.path.join( base_dir, arch, 'Packages' ) ):
			continue
		print >> stdout, arch,
		stdout.flush()
		# create Packages file
		packages_fd = open( os.path.join( base_dir, arch, 'Packages' ), 'w' )
		pwd, child = os.path.split( base_dir )
		ret = subprocess.call( [ 'apt-ftparchive', 'packages', os.path.join( child, arch ) ], stdout = packages_fd, stderr = stderr, cwd = pwd )
		packages_fd.close()

		if ret:
			print >> stderr, "Error: Failed to create Packages file for '%s'" % os.path.join( base_dir, arch )
			sys.exit( 1 )

		# create Packages.gz file
		gzip_file( os.path.join( base_dir, arch, 'Packages' ) )

		if ret:
			print >> stdout,'failed.'
			print >> stderr, "Error: Failed to create Packages.gz file for '%s'" % os.path.join( _repo_path, arch )
			sys.exit( 1 )

	# create Packages file in dists directory if it exists
	if dists and os.path.isdir( os.path.join(  base_dir, 'dists' ) ):
		version = configRegistry.get( 'version/version' )
		for arch in ( 'i386', 'amd64' ):
			if not os.path.isdir( os.path.join( base_dir, 'dists/univention/main', 'binary-%s' % arch ) ):
				continue
			packages_file = os.path.join( base_dir, 'dists/univention/main', 'binary-%s' % arch, 'Packages' )
			packages_fd = open( packages_file, 'w' )
			ret = subprocess.call( [ 'apt-ftparchive', 'packages', 'all' ], stdout = packages_fd, stderr = stderr, cwd = base_dir )
			packages_fd.close()
			packages_fd = open( packages_file, 'a' )
			ret = subprocess.call( [ 'apt-ftparchive', 'packages', '%s' % arch ], stdout = packages_fd, stderr = stderr, cwd = base_dir )
			packages_fd.close()
			gzip_file( packages_file )

	print >> stdout, 'done.'

def create_packages( base_dir, source_dir ):
	# recreate Packages file
	if not os.path.isdir( os.path.join( base_dir, source_dir ) ) or not os.path.isfile( os.path.join( base_dir, source_dir, 'Packages' ) ):
		return

	pkg_file = os.path.join( base_dir, source_dir, 'Packages' )
	pkg_file_lock = os.path.join( base_dir, source_dir, 'Packages.lock' )
	pkg_file_gz = os.path.join( base_dir, source_dir, 'Packages.gz' )
	# create a backup
	if os.path.exists( pkg_file ):
		shutil.copyfile( pkg_file, '%s.SAVE' % pkg_file )
	if os.path.exists( pkg_file_gz ):
		shutil.copyfile( pkg_file_gz, '%s.SAVE' % pkg_file_gz )

	packages_fd = open( os.path.join( base_dir, source_dir, 'Packages' ), 'w' )
	try:
		fd = open( pkg_file_lock, 'w' )
		fd.close()
	except:
		pass

	ret = subprocess.call( [ 'apt-ftparchive', 'packages', source_dir ], stdout = packages_fd, cwd = base_dir )
	packages_fd.close()

	if ret:
		print >> sys.stderr, "Error: Failed to create Packages file for '%s'" % os.path.join( base_dir, source_dir )
		# restore backup
		if os.path.exists( '%s.SAVE' % pkg_file ):
			shutil.copyfile( '%s.SAVE' % pkg_file, pkg_file )
		if os.path.exists( '%s.SAVE' % pkg_file_gz ):
			shutil.copyfile( '%s.SAVE' % pkg_file_gz, pkg_file_gz )
		if os.path.exists( pkg_file_lock ):
			os.unlink( pkg_file_lock )
		sys.exit( 1 )

	# create Packages.gz file
	gzip_file( os.path.join( base_dir, source_dir, 'Packages' ) )

	if os.path.exists( pkg_file_lock ):
		os.unlink( pkg_file_lock )

def get_repo_basedir( packages_dir ):
	# cut off trailing '/'
	if packages_dir[ -1 ] == '/':
		packages_dir = packages_dir[ : -1 ]

	# find repository base directory
	has_arch_dirs = False
	has_packages = False
	for entry in os.listdir( packages_dir ):
		if os.path.isdir( os.path.join( packages_dir, entry ) ) and entry in ( 'i386', 'all', 'amd64' ):
			has_arch_dirs = True
		elif os.path.isfile( os.path.join( packages_dir, entry ) ) and entry == 'Packages':
			has_packages = True

	if not has_arch_dirs:
		# might not be a repository
		if not has_packages:
			print >> sys.stderr, 'Error: %s does not seem to be a repository.' % packages_dir
			sys.exit( 1 )
		head, tail = os.path.split( packages_dir )
		if tail in ( 'i386', 'all', 'amd64' ):
			packages_path = head
		else:
			print >> sys.stderr, 'Error: %s does not seem to be a repository.' % packages_dir
			sys.exit( 1 )
	else:
		packages_path = packages_dir

	return packages_path

def is_debmirror_installed():
	devnull = open( os.path.devnull, 'w' )
	p = subprocess.Popen( [ 'dpkg-query', '-s', 'univention-debmirror' ], stdout = subprocess.PIPE, stderr = devnull )
	output = p.communicate()[ 0 ]

	devnull.close()
	# univention-debmirror is not installed
	if p.returncode:
		return ( False, 'Error: Please install the package univention-debmirror.' )

	# package status of univentionn-debmirror is not ok
	for line in output:
		if line.startswith( 'Status: ' ):
			if line.find( 'install ok installed' ) == -1:
				return ( False, "Please check the installation of the package univention-debmirror (status: %s). Aborted." % line[ 8: ] )

	return ( True, None )

def get_installation_version():
	version = None
	try:
		fd = open( os.path.join( configRegistry.get( 'repository/mirror/basepath' ), '.univention_install' ) )
	except:
		return None

	for line in fd.readlines():
		if not line.startswith( 'VERSION=' ):
			continue
		return line[ 8 : -1 ]

	return None
