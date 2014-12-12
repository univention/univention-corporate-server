# -*- coding: utf-8 -*-
#
# Univention Management Console
#  logging module for UMC
#
# Copyright 2011-2014 Univention GmbH
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

"""
Logging
=======

This module provides a wrapper for univention.debug
"""

import univention.debug as ud
import logging
import grp
import os
from univention.config_registry import ConfigRegistry

# no exceptions from logging
# otherwise shutdown the server will raise an exception that the logging stream could not be closed
logging.raiseExceptions = 0

#: list of available debugging components
COMPONENTS = ( ud.MAIN, ud.NETWORK, ud.SSL, ud.ADMIN, ud.MODULE, ud.AUTH, ud.PARSER, ud.LOCALE, ud.ACL, ud.RESOURCES, ud.PROTOCOL )

_ucr = ConfigRegistry()
_ucr.load()
_debug_ready = False
_debug_loglevel = max(int(_ucr.get('umc/server/debug/level', 2)), int(_ucr.get('umc/module/debug/level', 2)))

def log_init( filename, log_level = 2 ):
	"""Initializes Univention debug.

	:param str filename: The filename just needs to be a relative name. The directory /var/log/univention/ is prepended and the suffix '.log' is appended.
	:param int log_level: log level to use (1-4)
	"""

	if filename[ 0 ] != '/':
		filename = '/var/log/univention/%s.log' % filename
	fd = ud.init( filename, ud.FLUSH, ud.NO_FUNCTION )
	adm = grp.getgrnam( 'adm' )
	os.chown( filename, 0, adm.gr_gid )
	os.chmod( filename, 0640 )
	log_set_level( log_level )

	global _debug_ready
	_debug_ready = True

	return fd

def log_set_level( level = 0 ):
	"""Sets the log level for all components.

	:param int level: log level to set
	"""
	for component in COMPONENTS:
		ud.set_level( component, level )

def log_reopen():
	if _debug_ready:
		ud.reopen()

class ILogger( object ):
	"""This class provides a simple interface to access the univention
	debug function for the given component.

	:param int id: id of the component to use
	"""
	def __init__( self, id ):
		self._id = getattr(ud, id)
		fallbackLoggingFormatter = logging.Formatter('%%(asctime)s.%%(msecs)03d  %(component)-11s ( %%(level)-7s ) : %%(message)s' % {'component' : id}, '%d.%m.%y %H:%M:%S')
		fallbackLoggingHandler = logging.StreamHandler()
		fallbackLoggingHandler.setFormatter(fallbackLoggingFormatter)
		self._fallbackLogger = logging.Logger(logging.DEBUG)
		self._fallbackLogger.addHandler(fallbackLoggingHandler)
		self._extras = [
			{'level': 'ERROR'},
			{'level': 'WARN'},
			{'level': 'PROCESS'},
			{'level': 'INFO'},
		]

	def error( self, message ):
		"""Write a debug message with level ERROR"""
		if _debug_ready:
			ud.debug( self._id, ud.ERROR, message )
		elif _debug_loglevel >= ud.ERROR:
			self._fallbackLogger.error(message, extra=self._extras[ud.ERROR])

	def warn( self, message ):
		"""Write a debug message with level WARN"""
		if _debug_ready:
			ud.debug( self._id, ud.WARN, message )
		elif _debug_loglevel >= ud.WARN:
			self._fallbackLogger.warning(message, extra=self._extras[ud.WARN])

	def process( self, message ):
		"""Write a debug message with level PROCESS"""
		if _debug_ready:
			ud.debug( self._id, ud.PROCESS, message )
		elif _debug_loglevel >= ud.PROCESS:
			self._fallbackLogger.info(message, extra=self._extras[ud.PROCESS])

	def info( self, message ):
		"""Write a debug message with level INFO"""
		if _debug_ready:
			ud.debug( self._id, ud.INFO, message )
		elif _debug_loglevel >= ud.INFO:
			self._fallbackLogger.debug(message, extra=self._extras[ud.INFO])

CORE = ILogger( 'MAIN' )
NETWORK = ILogger( 'NETWORK' )
CRYPT = ILogger( 'SSL' )
UDM = ILogger( 'ADMIN' )
MODULE = ILogger( 'MODULE' )
AUTH = ILogger( 'AUTH' )
PARSER = ILogger( 'PARSER' )
LOCALE = ILogger( 'LOCALE' )
ACL = ILogger( 'ACL' )
RESOURCES = ILogger( 'RESOURCES' )
PROTOCOL = ILogger( 'PROTOCOL' )
