# -*- coding: utf-8 -*-
#
# Univention Apache
#  baseconfig module: modifies the memory limit for PHP applications run
#  by apache
#
# Copyright 2004-2015 Univention GmbH
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

import os, sys

def handler(bc,changes):
	if bc.get('php/memory/limit') or bc.get('php/limit/filesize') or bc.get('php/limit/postsize') \
	or bc.get('php/memory/executiontime') or bc.get('php/limit/inputtime') or bc.get('php/limit/sockettimeout'):
		memlimit = bc.get('php/memory/limit')
		if memlimit and memlimit[-1:].lower() == 'm':
			memlimit = memlimit[:-1]

		postsize = bc.get('php/limit/postsize')
		if postsize and postsize[-1:].lower() == 'm':
			postsize = postsize[:-1]

		filesize = bc.get('php/limit/filesize')
		if filesize and filesize[-1:].lower() == 'm':
			filesize = filesize[:-1]

		executiontime = bc.get('php/memory/executiontime')
		if executiontime and executiontime[-1:].lower() == 's':
			executiontime = executiontime[:-1]

		inputtime = bc.get('php/limit/inputtime') 
		if inputtime and inputtime[-1:].lower() == 's':
			inputtime = inputtime[:-1]

		sockettimeout = bc.get('php/limit/sockettimeout')
		if sockettimeout and sockettimeout[-1:].lower() == 's':
			sockettimeout = sockettimeout[:-1]

		try:
			f = open('/etc/php5/apache2/php.ini', 'r')
		except IOError, e:
			print e
			sys.exit(1)
		tmp = []
		line = f.readline()

		while line:
			if memlimit and line[:15] == 'memory_limit = ':
				line = 'memory_limit = %sM  ; Maximum amount of memory a script may consume (8MB)\n' % str(memlimit)

			if postsize and line[:16] == 'post_max_size = ':
				line = 'post_max_size = %sM  ; Maximum size of POST data that PHP will accept. (8MB)\n' % str(postsize)

			if filesize and line[:22] == 'upload_max_filesize = ':
				line = 'upload_max_filesize = %sM  ; Maximum allowed size for uploaded files. (2MB)\n' % str(filesize)

			if executiontime and line[:21] == 'max_execution_time = ':
				line = 'max_execution_time = %s  ; Maximum execution time of each script, in seconds\n' % str(executiontime)

			if inputtime and line[:17] == 'max_input_time = ':
				line = 'max_input_time = %s ; Maximum amount of time each script may spend parsing request data \n' % str(inputtime)

			if sockettimeout and line[:25] == 'default_socket_timeout = ':
				line = 'default_socket_timeout = %s\n ' % str(sockettimeout)

			tmp.append(line)
			line = f.readline()

		f.close()
		# rewrite file
		try:
			f = open('/etc/php5/apache2/php.ini', 'w')
		except IOError, e:
			print e
			sys.exit(1)
		f.truncate()
		f.writelines(tmp)
		f.close()
