#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Print Server
#  helper script: prints out a list of univention admin commands to create
#  settings/printermodel objects for all existing PPDs
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

import sys, os, gzip

def getPath(manufacturer, filename):
	base = 'foomatic-ppds'
	return os.path.join(base, manufacturer, filename)

def getName(filename):
	nickname = '*NickName:'
	file = gzip.open(filename)
	names = [ line.split('"')[1] for line in file if line.startswith(nickname) ]
	if not names:
		# report malformed PPD
		print >>sys.stderr, "Something went wrong in %s...\n" % filename
		return 'Unknown'
	return names[0]

def getCommand(manufacturer, models):
	first = 'univention-admin settings/printermodel create $@ --ignore_exists --position "cn=cups,cn=univention,$ldap_base" --set name=%s' % manufacturer
	rest = [ r'--append printmodel="\"%s\" \"%s\""' % (path, name) for path, name in models ]
	rest.insert(0, first)
	return ' \\\n\t'.join(rest)

def createPrinterModels(ppdPath):
	def create(dir):
		path = os.path.join(ppdPath, dir)
		files = os.listdir(path)
		files.sort()
		models = [ (getPath(dir, file), getName(os.path.join(path, file))) for file in files ]
		return getCommand(dir, models)
	dirs = os.listdir(ppdPath)
	dirs.sort()
	cmds = [ create(dir) for dir in dirs ]
	return '\n\n'.join(cmds)

if __name__ == '__main__':
	ppdPath = '/usr/share/ppd'
	print createPrinterModels(ppdPath)
