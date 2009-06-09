#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Python Heimdal
#  setup description for the python distutils
#
# Copyright (C) 2003, 2004, 2005, 2006 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	USA

from distutils.core import setup, Extension
from ConfigParser import ConfigParser
import sys,os,string,time

setup(
	name='python-heimdal',
	version='0.1',
	description='Heimdal Python bindings',
	author='Univention GmbH',
	author_email='packages@univention.de',
	url='http://www.univention.de/',

	ext_modules=[
		Extension(
			'heimdal',
			['module.c', 'error.c', 'context.c', 'principal.c',
				'creds.c', 'ticket.c', 'keytab.c', 'ccache.c',
				'salt.c', 'enctype.c', 'keyblock.c', 'asn1.c'],
			libraries=['krb5', 'kadm5clnt', 'hdb', 'asn1', 'com_err', 'roken' ]
		)
	],
)
