#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Print Server
#  helper script: prints out a list of univention admin commands to create
#  settings/printermodel objects for all existing PPDs
#
# Copyright 2004-2012 Univention GmbH
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

import sys, os, gzip

def get_ppd_infos( filename ):
	nickname = manufacturer = None

	if filename.endswith( '.ppd.gz' ):
		file = gzip.open(filename)
	else:
		file = open(filename)
	for line in file:
		if line.startswith( '*NickName:' ):
			nickname = line.split( '"' )[ 1 ]		
		if line.startswith( '*Manufacturer:' ):
			manufacturer = line.split( '"' )[ 1 ]		
		if manufacturer and nickname:
			break
	return ( manufacturer, nickname )

def get_udm_command(manufacturer, models):
	first = 'univention-directory-manager settings/printermodel create $@ --ignore_exists --position "cn=cups,cn=univention,$ldap_base" --set name=%s' % manufacturer
	rest = [ r'--append printmodel="\"%s\" \"%s\""' % (path, name) for path, name in models ]
	rest.insert( 0, first )
	return '# Manufacturer: %s Printers: %d\n' % ( manufacturer, len( models ) ) + ' \\\n\t'.join(rest)

def __check_dir( commands, dirname, files ):
	for file in files:
		filename = os.path.join( dirname, file )
		if os.path.isfile( filename ) and ( filename.endswith( '.ppd' ) or filename.endswith( '.ppd.gz' ) ):
			rel_path = filename[ len( '/usr/share/ppd/' ) : ]
			manu, nick = get_ppd_infos( filename )
			if commands.has_key( manu ):
				commands[ manu ].append( ( rel_path, nick ) )
			else:
				commands[ manu ] = [ ( rel_path, nick ) ]
	return files

if __name__ == '__main__':
	printers = {}
	cmds = []
	os.path.walk( '/usr/share/ppd/', __check_dir, printers ) 
	for manu, models in printers.items():
		cmds.append( get_udm_command( manu, models ) )
	print '\n\n'.join(cmds)
