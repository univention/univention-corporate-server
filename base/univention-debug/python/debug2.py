# -*- coding: utf-8 -*-
#
# Univention Debug2
#  debug2.py
#
# Copyright 2008-2014 Univention GmbH
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

import logging
#import logging.handlers

ERROR = 0
WARN = 1
PROCESS = 2
INFO = 3
ALL = 4
DEFAULT = WARN

# The default levels provided are DEBUG(10), INFO(20), WARNING(30), ERROR(40) and CRITICAL(50).
# Mapping old levels to new ones
_map_lvl_old2new = {
	0: logging.ERROR,    # 40
	1: logging.WARNING,  # 30
	2: 25,               # 25
	3: logging.INFO,     # 20
	4: 15,               # 15
}

MAIN = 0x00
LDAP = 0x01
USERS = 0x02
NETWORK = 0x03
SSL = 0x04
SLAPD = 0x05
SEARCH = 0x06
TRANSFILE = 0x07
LISTENER = 0x08
POLICY = 0x09
ADMIN = 0x0A
CONFIG = 0x0B
LICENSE = 0x0C
KERBEROS = 0x0D
DHCP = 0x0E

_map_id_old2new = {
	MAIN: "MAIN",
	LDAP: "LDAP",
	USERS: "USERS",
	NETWORK: "NETWORK",
	SSL: "SSL",
	SLAPD: "SLAPD",
	SEARCH: "SEARCH",
	TRANSFILE: "TRANSFILE",
	LISTENER: "LISTENER",
	POLICY: "POLICY",
	ADMIN: "ADMIN",
	CONFIG: "CONFIG",
	LICENSE: "LICENSE",
	KERBEROS: "KERBEROS",
	DHCP: "DHCP",
}


#13.08.08 13:13:57  LISTENER    ( ERROR   ) : listener: 1
#13.08.08 13:13:57  LISTENER    ( WARN    ) : received signal 2
#13.08.08 13:14:02  DEBUG_INIT
_outfmt = '%(asctime)s,%(msecs)d %(name)-11s (%(levelname)-7s): %(message)s'
_outfmt_syslog = '%(name)-11s (%(levelname)-7s): %(message)s'
_datefmt = '%d.%m.%Y %H:%M:%S'

_logfilename = None
_handler_console = None
_handler_file = None
_handler_syslog = None
_do_flush = False
_enable_function = False
_enable_syslog = False
_logger_level = {}

# set default level for each logger
for key in _map_id_old2new.values():
	_logger_level[key] = _map_lvl_old2new[DEFAULT]

def init( logfilename, do_flush=0, enable_function=0, enable_syslog=0 ):
	global _logfilename, _handler_console, _handler_file, _handler_syslog, _do_flush, _enable_function, _enable_syslog, _logger_level

	_logfilename = logfilename

	# create root logger
	logging.basicConfig(level=logging.DEBUG,
						filename = '/dev/null',       # disabled
						format = _outfmt,
						datefmt = _datefmt)

	formatter = logging.Formatter( _outfmt, _datefmt )
	if logfilename == 'stderr' or logfilename == 'stdout':
		# add stderr or stdout handler
		try:
			if _handler_console:
				logging.getLogger('').removeHandler(_handler_console)
				_handler_console = None

			if logfilename == 'stdout':
				_handler_console = logging.StreamHandler( sys.stdout )
			else:
				_handler_console = logging.StreamHandler( sys.stderr )
			_handler_console.setLevel( logging.DEBUG )
			_handler_console.setFormatter(formatter)
			logging.getLogger('').addHandler(_handler_console)
		except:
			print 'opening %s failed' % logfilename
	else:
		if _handler_file:
			logging.getLogger('').removeHandler(_handler_file)
			_handler_file = None
		try:
			# add file handler
			_handler_file = logging.FileHandler( logfilename, 'a+' )
			_handler_file.setLevel( logging.DEBUG )
			_handler_file.setFormatter(formatter)
			logging.getLogger('').addHandler(_handler_file)
		except:
			print 'opening %s failed' % logfilename

# 	if enable_syslog:
# 		try:
# 			# add syslog handler
# 			_handler_syslog = logging.handlers.SysLogHandler( ('localhost', 514), logging.handlers.SysLogHandler.LOG_ERR )
# 			_handler_syslog.setLevel( _map_lvl_old2new[ERROR] )
# 			_handler_syslog.setFormatter(formatter)
# 			logging.getLogger('').addHandler(_handler_syslog)
# 		except:
# 			raise
# 			print 'opening syslog failed'

	logging.addLevelName( 25, 'PROCESS' )
	logging.addLevelName( 15, 'ALL' )
	logging.addLevelName( 100, '------' )

	logging.getLogger('MAIN').log( 100, 'DEBUG_INIT' )

	_do_flush = do_flush
	_enable_function = enable_function
	_enable_syslog = enable_syslog


def reopen():
	global _logfilename, _handler_console, _handler_file, _handler_syslog, _do_flush, _enable_function, _enable_syslog, _logger_level
	logging.getLogger('MAIN').log( 100, 'DEBUG_REINIT' )
	init( _logfilename, _do_flush, _enable_function, _enable_syslog )

def set_level( id, level ):
	global _logfilename, _handler_console, _handler_file, _handler_syslog, _do_flush, _enable_function, _enable_syslog, _logger_level
	new_id = _map_id_old2new.get(id, 'MAIN')
	if level > ALL:
		level = ALL
	elif level < ERROR:
		level = ERROR
	new_level = _map_lvl_old2new[ level ]
	_logger_level[ new_id ] = new_level

def set_function( activated ):
	global _logfilename, _handler_console, _handler_file, _handler_syslog, _do_flush, _enable_function, _enable_syslog, _logger_level
	_enable_function = activated

def debug( id, level, msg, utf8=True):
	global _logfilename, _handler_console, _handler_file, _handler_syslog, _do_flush, _enable_function, _enable_syslog, _logger_level
	new_id = _map_id_old2new.get(id, 'MAIN')
	new_level = _map_lvl_old2new[ level ]
	if new_level >= _logger_level[ new_id ]:
		logging.getLogger( new_id ).log( new_level, msg )
		# flush if requested
		if _do_flush:
			for handler in [ _handler_console, _handler_file, _handler_syslog ]:
				if handler:
					handler.flush()

class function:
	def __init__(self, text, utf8=True):
		global _logfilename, _handler_console, _handler_file, _handler_syslog, _do_flush, _enable_function, _enable_syslog, _logger_level
		self.text=text
		if _enable_function:
			logging.getLogger('MAIN').log( 100, 'UNIVENTION_DEBUG_BEGIN : ' + self.text )
			# flush if requested
			if _do_flush:
				for handler in [ _handler_console, _handler_file, _handler_syslog ]:
					if handler:
						handler.flush()

	def __del__(self):
		global _logfilename, _handler_console, _handler_file, _handler_syslog, _do_flush, _enable_function, _enable_syslog, _logger_level
		if _enable_function:
			logging.getLogger('MAIN').log( 100, 'UNIVENTION_DEBUG_END   : ' + self.text )
			# flush if requested
			if _do_flush:
				for handler in [ _handler_console, _handler_file, _handler_syslog ]:
					if handler:
						handler.flush()
