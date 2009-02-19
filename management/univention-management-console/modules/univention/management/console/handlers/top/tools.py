#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: like top
#
# Copyright (C) 2007-2009 Univention GmbH
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

import copy, re

import notifier.popen
import univention.management.console as umc

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.top' ).translate

_ps_regex = re.compile( ' *(?P<cpu>[0-9.]*) +(?P<vsize>[0-9]*) +(?P<rssize>[0-9]*) +(?P<mem>[0-9.]*) +(?P<user>[^ ]*) +(?P<pid>[0-9]*) +(?P<prog>[^ ]*)( +(?P<args>.*))?' )
_ps_cmd = 'ps h -eo pcpu,vsize,rssize,pmem,user,pid,command'

class Process( object ):
	def __init__( self, uid = '', pid = 0, vsize = 0, rssize = 0, mem = 0.0, cpu = 0.0, prog = '', args = [] ):
		self.uid = uid
		self.pid = pid
		self.mem = mem
		self.vsize = vsize
		self.rssize = rssize
		self.cpu = cpu
		self.prog = prog
		self.args = args

def run_ps( callback, sort = 'cpu', count = '50' ):
	global _ps_cmd

	cmd = copy.copy( _ps_cmd )
	if sort == 'cpu':
		cmd += ' --sort=-pcpu'
	elif sort == 'rssize':
		cmd += ' --sort=-rssize'
	elif sort == 'vsize':
		cmd += ' --sort=-vsize'
	elif sort == 'user':
		cmd += ' --sort=user'
	elif sort == 'pid':
		cmd += ' --sort=pid'
	if not count == 'all':
		cmd += ' | head -%s' % count
	ud.debug( ud.ADMIN, ud.INFO, cmd )
	proc = notifier.popen.Shell( cmd, stdout = True )
	proc.signal_connect( 'finished', callback )
	proc.start()

def parse_ps( result ):
	global _ps_regex

	processes = []
	for line in result:
		matches = _ps_regex.match( line )
		if not matches:
			break
		grp = matches.groupdict()
		if not grp[ 'args' ]:
			args = []
		else:
			args = grp[ 'args' ].split( ' ' )
		processes.append( Process( grp[ 'user' ], int( grp[ 'pid' ] ), int( grp[ 'vsize' ] ), int( grp[ 'rssize' ] ), float( grp[ 'mem' ] ),
								   float( grp[ 'cpu' ] ), grp[ 'prog' ], args ) )
	return processes
