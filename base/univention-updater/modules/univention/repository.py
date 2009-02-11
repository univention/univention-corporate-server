#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: helper functions for managing repositories
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
import shutil
import subprocess
import sys

# constants
ARCHITECTURES = ( 'i386', 'amd64', 'all', 'extern' )

def create_packages( base_dir, source_dir ):
	# create Packages file
	if not os.path.isfile( os.path.join( base_dir, source_dir, 'Packages' ) ):
		return True

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
		return False

	# create Packages.gz file
	packages_fd = open( os.path.join( base_dir, source_dir, 'Packages' ), 'r' )
	packagesgz_fd = open( os.path.join( base_dir, source_dir, 'Packages.gz' ), 'w' )
	ret = subprocess.call( [ 'gzip' ], stdout = packagesgz_fd, stdin = packages_fd )
	packages_fd.close()
	packagesgz_fd.close()

	if os.path.exists( pkg_file_lock ):
		os.unlink( pkg_file_lock )

	return True

def get_repo_basedir( packages_dir ):
	# cut off trailing '/'
	if packages_dir[ -1 ] == '/':
		packages_dir = packages_dir[ : -1 ]

	# find repository base directory
	has_arch_dirs = False
	has_packages = False
	for entry in os.listdir( packages_dir ):
		if os.path.isdir( os.path.join( packages_dir, entry ) ) and entry in ( 'i386', 'all', 'amd64', 'extern' ):
			has_arch_dirs = True
		elif os.path.isfile( os.path.join( packages_dir, entry ) ) and entry == 'Packages':
			has_packages = True

	if not has_arch_dirs:
		# might not be a repository
		if not has_packages:
			print >> sys.stderr, 'Error: %s does not seem to be a repository.' % packages_dir
			sys.exit( 1 )
		head, tail = os.path.split( packages_dir )
		if tail in ( 'i386', 'all', 'amd64', 'extern' ):
			packages_path = head
		else:
			print >> sys.stderr, 'Error: %s does not seem to be a repository.' % packages_dir
			sys.exit( 1 )
	else:
		packages_path = packages_dir

	return packages_path
