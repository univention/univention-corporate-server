#!/usr/bin/python2.6
#
# Univention Dansguardian
#  Univention Configuration Registry Module to write filter group configuration
#
# Copyright 2009-2012 Univention GmbH
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

import os

import univention.config_registry as ucr

TEMPLATE_PATH = '/etc/univention/templates/files/etc/dansguardian/'
CONFIG_PATH = '/etc/dansguardian'

def handler( configRegistry, changes ):
	groups = configRegistry.get( 'dansguardian/groups', 'web-access' ).split( ';' )
	for i in range( len( groups ) ):
		ucr.handler_set( [ 'dansguardian/current/groupno=%d' % ( i + 1 ), 'dansguardian/current/group=%s' % groups[ i ] ] )

		# primary filter group configuration file
		src = os.path.join( TEMPLATE_PATH, 'dansguardianfX.conf' )
		src_fd = open( src )
		conf = os.path.join( CONFIG_PATH, 'dansguardianf%d.conf' % ( i + 1 ) )
		content = ucr.filter( src_fd.read(), configRegistry, srcfiles = [ src ] )
		src_fd.close()
		fd = open( conf, 'w' )
		fd.write( content )
		fd.close()

		# several lists for filter groups
		for entry in os.listdir( os.path.join( TEMPLATE_PATH, 'lists' ) ):
			abs_filename = os.path.join( TEMPLATE_PATH, 'lists', entry )
			if os.path.isfile( abs_filename ):
				template = open( abs_filename )
				conf = os.path.join( CONFIG_PATH, 'lists', '%s-%s' % (groups[ i ], entry ) )
				content = ucr.filter( template.read(), configRegistry, srcfiles = [ abs_filename ] )
				template.close()
				fd = open( conf, 'w' )
				fd.write( content )
				fd.close()

	ucr.handler_unset( [ 'dansguardian/current/groupno', 'dansguardian/current/group' ] )

# test
if __name__ == '__main__':
	configRegistry = ucr.ConfigRegistry()
	configRegistry.load()
	handler( configRegistry, [] )
