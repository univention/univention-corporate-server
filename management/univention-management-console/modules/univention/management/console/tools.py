#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  icon loader: tries to load icon file identified by a tag and size
#
# Copyright 2006-2010 Univention GmbH
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
import subprocess
import tempfile
import time

import notifier

__all__ = [ 'image_get', 'image_path_append', 'run_process', 'kill_process', 'CountDown',
	    'SIZE_MICROSCOPIC', 'SIZE_TINY', 'SIZE_SMALL', 'SIZE_MEDIUM',
	    'SIZE_NORMAL', 'SIZE_LARGE', 'SIZE_HUGE' ]

_image_theme = 'default'
_image_prefix = '/usr/share/univention-management-console/www'
_image_pathes = [ 'themes/images', ]

SIZE_MICROSCOPIC = 8
SIZE_TINY = 12
SIZE_SMALL = 16
SIZE_MEDIUM = 24
SIZE_NORMAL = 32
SIZE_LARGE = 64
SIZE_HUGE = 92

class ImageLoader( object ):
	def __init__( self ):
		self.__cache = {}

	def load( self, tag, size = SIZE_NORMAL ):
		if not self.__cache.has_key( tag ):
			filename = self.find( tag, size )
			if filename:
				fd = open( filename, 'r' )
				data = fd.read()
				self.__cache[ tag ] = data
			else:
				return None
		return self.__cache[ tag ]

	def find( self, tag, size = SIZE_NORMAL ):
		global _image_pathes, _image_prefix, _image_theme
		for theme in [ _image_theme ]:
			for path in _image_pathes:
				f = os.path.join( _image_prefix, path, _image_theme,
								  "%dx%d" % ( size, size ), tag )
				for ext in ( 'png', 'gif', 'jpg' ):
					filename = '%s.%s' % ( f, ext )
					if os.path.isfile( filename ):
						return filename[ len( _image_prefix ) + 1 : ]

		return None

_image_loader = ImageLoader()

def image_get( tag, size = SIZE_NORMAL ):
	global _image_loader
	return _image_loader.find( tag, size )

def image_path_append( path ):
	global _image_pathes
	if not path or path[ 0 ] != '/' or not os.path.isdir( path ):
		raise Exception( 'error: image path must be an absolute path' )
	_image_pathes.append( path )

## sub-process handling

class CountDown( object ):
	def __init__( self, timeout ):
		self.start = time.time() * 1000
		self.timeout = timeout
		
	def __call__( self ):
		now = time.time() * 1000
		return not self.timeout or ( now - self.start < self.timeout )
			
def run_process( command, timeout = 0, shell = True, output = True ):
	# we need to provide a dispatcher function to activate the minimal timeout
	def fake_dispatcher(): return True
	notifier.dispatcher_add( fake_dispatcher )

	countdown = CountDown( timeout )
	if output:
		out = tempfile.NamedTemporaryFile()
		err = tempfile.NamedTemporaryFile()
		child = subprocess.Popen( command, shell = shell, stdout = out, stderr = err )
	else:
		out = err = None
		child = subprocess.Popen( command, shell = shell )

	while countdown():
		exitcode = child.poll()
		if exitcode != None:
			break
		notifier.step()

	# remove dspatcher function
	notifier.dispatcher_remove( fake_dispatcher )

	# prepare return code
	ret = { 'pid' : None, 'exit' : None, 'stdout' : out, 'stderr' : err }
	if child.returncode == None:
		ret[ 'pid' ] = child.pid
	else:
		# move to beginning of files
		out.seek( 0 )
		err.seek( 0 )
		ret[ 'exit' ] = child.returncode
	
	return ret

def kill_process( pid, signal = 15, timeout = 0 ):
	# we need to provide a dispatcher function to activate the minimal timeout
	def fake_dispatcher(): return True
	notifier.dispatcher_add( fake_dispatcher )

	countdown = CountDown( timeout )
	os.kill( pid, signal )
	while countdown():
		dead_pid, sts = os.waitpid( pid, os.WNOHANG )
		if dead_pid == pid:
			break
		notifier.step()
	else:
		# remove dspatcher function
		notifier.dispatcher_remove( fake_dispatcher )
		return None
	
	# remove dspatcher function
	notifier.dispatcher_remove( fake_dispatcher )

	if os.WIFSIGNALED( sts ) and os.WIFEXITED( sts ):
		returncode = os.WTERMSIG( sts ) + os.WEXITSTATUS( sts )
	else:
		if os.WIFSIGNALED( sts ):
			returncode = -os.WTERMSIG( sts )
		else:
			returncode = os.WEXITSTATUS( sts )

	return returncode
	
if __name__ == '__main__':
	notifier.init()

	def test_run_process():
		print run_process( 'ls -latr' )
		ret = run_process( [ 'ls', '-latr' ], timeout = 2000, shell = False )
		print ret
		print ret[ 'stdout' ].read()

		ret = run_process( 'echo test;sleep 10', timeout = 5000 )
		print ret
		print kill_process( ret[ 'pid' ] )
		print ret[ 'stdout' ].read()
		return False

	notifier.timer_add( 1000, test_run_process )

	notifier.loop()
