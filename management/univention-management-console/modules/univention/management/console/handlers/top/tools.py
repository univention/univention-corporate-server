#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: like top
#
# Copyright 2007-2010 Univention GmbH
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

import copy, re

import notifier.popen
import univention.management.console as umc
import univention.management.console.tools as umct

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.top' ).translate

_ps_regex = re.compile( ' *(?P<cpu>[0-9.]*) +(?P<vsize>[0-9]*) +(?P<rssize>[0-9]*) +(?P<mem>[0-9.]*) +(?P<user>[^ ]*) +(?P<pid>[0-9]*) +(?P<prog>[^ ]*)( +(?P<args>.*))?' )
_ps_cmd = [ 'ps', 'h', '-eo', 'pcpu,vsize,rssize,pmem,user,pid,command']

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

def run_ps( sort = 'cpu', count = '50' ):
	global _ps_cmd

	cmd = copy.copy( _ps_cmd )
	if sort == 'cpu':
		cmd.append('--sort=-pcpu')
	elif sort == 'rssize':
		cmd.append('--sort=-rssize')
	elif sort == 'vsize':
		cmd.append('--sort=-vsize')
	elif sort == 'user':
		cmd.append('--sort=user')
	elif sort == 'pid':
		cmd.append('--sort=pid')

	ud.debug( ud.ADMIN, ud.INFO, 'top: cmd=%s' % cmd )
	result = umct.run_process( cmd, timeout=0, shell=False, output=True )

	stdout = result['stdout'].read()
	ud.debug( ud.ADMIN, ud.INFO, 'output=\n%s' % stdout )

	stdout_lines = [ x.rstrip('\n\r') for x in stdout.splitlines() ]

	if not count == 'all':
		stdout_lines = stdout_lines[0:int(count)]

	return parse_ps( stdout_lines )


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
