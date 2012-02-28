#!/usr/bin/python2.6
#
# Univention Management Console
#  MODULEDESC
#
# Copyright 2012 Univention GmbH
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

import notifier
import smtplib

from univention.management.console.modules import Base
from univention.management.console.log import MODULE
from univention.management.console.config import ucr

from univention.lib.i18n import Translation

_ = Translation( 'PACKAGENAME' ).translate

class Instance( Base ):
	def init( self ):
		# this initialization method is called when the
		# module process is started and the configuration from the
		# UMC server is completed
		pass

	def configuration( self, request ):
		"""Returns a directionary of initial values for the form."""
		self.finished( request.id, {
			'sender' : self._username + '@example.com',
			'subject' : 'Test mail from PACKAGENAME',
			'recipient' : 'test@exaple.com' } )


	def send( self, request ):
		def _send_thread( sender, recipient, subject, message ):
			MODULE.info( 'sending mail: thread running' )

			msg = u'From: ' + sender + u'\r\n'
			msg += u'To: ' + recipient + u'\r\n'
			msg += u'Subject: %s\r\n' % subject
			msg += u'\r\n'
			msg += message + u'\r\n'
			msg += u'\r\n'

			msg = msg.encode('latin1')

			server = smtplib.SMTP('localhost')
			server.set_debuglevel(0)
			server.sendmail(sender, recipient, msg)
			server.quit()

		def _send_return( thread, result, request ):
			import traceback

			if not isinstance( result, BaseException ):
				MODULE.info( 'sending mail: completed successfully' )
				self.finished( request.id, True )
			else:
				msg = '%s\n%s: %s\n' % ( ''.join( traceback.format_tb( thread.exc_info[ 2 ] ) ), thread.exc_info[ 0 ].__name__, str( thread.exc_info[ 1 ] ) )
				MODULE.process( 'sending mail:An internal error occurred: %s' % msg )
				self.finished( request.id, False, msg, False )


		keys = [ 'sender', 'recipient', 'subject', 'message' ]
		self.required_options( request, *keys )
		for key in keys:
			if request.options[ key ]:
				MODULE.info( 'send ' + key + '=' + request.options[ key ].replace('%','_') )

		func = notifier.Callback( _send_thread,
								  request.options[ 'sender' ],
								  request.options[ 'recipient' ],
								  request.options[ 'subject' ],
								  request.options[ 'message' ] )
		MODULE.info( 'sending mail: starting thread' )
		cb = notifier.Callback( _send_return, request )
		thread = notifier.threads.Simple( 'mailing', func, cb )
		thread.run()
