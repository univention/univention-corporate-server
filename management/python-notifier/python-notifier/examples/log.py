#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Author: Andreas Büsching <crunchy@bitkipper.net>
#
# logger
#
# Copyright (C) 2005, 2006, 2009
#	Andreas Büsching <crunchy@bitkipper.net>
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version
# 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA

import os

import logging
import notifier.log as nflog

if __name__ == '__main__':
	# use default handlers
	print '>>> default handlers'
	# nflog.open() -> the default handlers are opened during import
	for level in ( nflog.CRITICAL, nflog.ERROR, nflog.WARN, nflog.INFO, nflog.DEBUG ):
		nflog.set_level( level )
		print 'LEVEL: %d' % level
		nflog.critical( 'critical' )
		nflog.error( 'error' )
		nflog.warn( 'warn' )
		nflog.info( 'info' )
		nflog.debug( 'debug' )

	# use custom handlers
	print '>>> custom handlers'
	handler = logging.FileHandler( 'test.log' )
	handler.setFormatter( nflog.formatter )
	nflog.open( handler )
	for level in ( nflog.CRITICAL, nflog.ERROR, nflog.WARN, nflog.INFO, nflog.DEBUG ):
		nflog.set_level( level )
		nflog.critical( 'LEVEL: %d' % level )
		nflog.critical( 'critical' )
		nflog.error( 'error' )
		nflog.warn( 'warn' )
		nflog.info( 'info' )
		nflog.debug( 'debug' )
	for line in open( 'test.log' ).readlines():
		print line,
	os.unlink( 'test.log' )
