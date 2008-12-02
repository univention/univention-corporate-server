# -*- coding: utf-8 -*-
#
# Univention Apache
#  baseconfig module: modifies the memory limit for PHP applications run
#  by apache
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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

import os, sys

def handler(bc,changes):
	if bc.get('php/memory/limit') or bc.get('php/limit/filesize') or bc.get('php/limit/postsize'):
		memlimit = bc.get('php/memory/limit')
		if memlimit and memlimit[-1:].lower() == 'm':
			memlimit = memlimit[:-1]

		postsize = bc.get('php/limit/postsize')
		if postsize and postsize[-1:].lower() == 'm':
			postsize = postsize[:-1]

		filesize = bc.get('php/limit/filesize')
		if filesize and filesize[-1:].lower() == 'm':
			filesize = filesize[:-1]

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
