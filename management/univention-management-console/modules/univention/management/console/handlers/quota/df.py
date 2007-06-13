#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: provides size information about a hard drive partition
#
# Copyright (C) 2006 Univention GmbH
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

'''This module provides a similar functionality as the UNIX tool df'''

import os

class DeviceInfo:
	def __init__( self, path ):
		self.path = path
		self._statvfs = os.statvfs( self.path )

	def free( self ):
		return ( self._statvfs.f_bfree * self._statvfs.f_bsize )

	def available( self ):
		return ( self._statvfs.f_bavail * self._statvfs.f_bsize )

	def size( self ):
		return ( self._statvfs.f_blocks * self._statvfs.f_bsize )

	def block_size( self ):
		return self._statvfs.f_bsize
