#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  Univention LDAP Listener script for the ad connector
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

import listener, cPickle, time, os

name='ad-connector'
description='AD Connector replication'
filter='(objectClass=*)'
attributes=[]

# use the modrdn listener extension
modrdn="1"

dir=listener.baseConfig['connector/ad/listener/dir']

def handler(dn, new, old, command):

	listener.setuid(0)
	if not os.path.exists(os.path.join(dir, 'tmp')):
		os.mkdir(os.path.join(dir, 'tmp'))
	try:
		old_dn=None
		if os.path.exists(os.path.join(dir, 'tmp','old_dn')):
			f=open(os.path.join(dir, 'tmp','old_dn'),'r')
			old_dn=cPickle.load(f)
			f.close()
		if command == 'r':
			filename=os.path.join(dir, 'tmp','old_dn')

			f=open(filename, 'w+')
			os.chmod(filename, 0600)
			cPickle.dump(dn, f)
			f.close()
		else:
			object=(dn, new, old, old_dn)

			filename=os.path.join(dir,"%f"%time.time())

			f=open(filename, 'w+')
			os.chmod(filename, 0600)
			cPickle.dump(object, f)
			f.close()

			if os.path.exists(os.path.join(dir, 'tmp','old_dn')):
				os.unlink(os.path.join(dir, 'tmp','old_dn'))
				pass

	finally:
		listener.unsetuid()


def clean():
	listener.setuid(0)
	try:
		for filename in os.listdir(dir):
			if filename != "tmp":
				os.remove(os.path.join(dir,filename))
		for filename in os.listdir(os.path.join(dir,'tmp')):
			os.remove(os.path.join(dir,filename))
	finally:
		listener.unsetuid()


def initialize():
	clean()

