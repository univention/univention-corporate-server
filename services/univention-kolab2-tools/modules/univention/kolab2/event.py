#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Kolab2 Tools
#
# Copyright (C) 2008-2009 Univention GmbH
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

from object import Kolab2Object

class Kolab2Event( Kolab2Object ):
	def __init__( self ):
		Kolab2Object.__init__( self, Kolab2Object.EVENT )

	def parse( self, data ):
		Kolab2Object.parse( self, data )

		self._define_element( 'summary' )
		self._define_element( 'location' )
		self._define_element( 'start-date', 'start_date' )
		self._define_element( 'alarm' )

		organizer = self._doc.getElementsByTagName( 'organizer' )
		if organizer:
			self._define_element( 'display-name', prefix = 'organizer', parent = organizer[ 0 ] )
			self._define_element( 'smtp-address', prefix = 'organizer', parent = organizer[ 0 ] )

		attendees = self._doc.getElementsByTagName( 'attendee' )
		self.n_attendees = 1
		for attendee in attendees:
			self._define_element( 'display-name', prefix = 'attendee%d' % self.n_attendees,
								  parent = attendee )
			self._define_element( 'smtp-address', prefix = 'attendee%d' % self.n_attendees,
								  parent = attendee )
			self._define_element( 'status', prefix = 'attendee%d' % self.n_attendees,
								  parent = attendee )
			self._define_element( 'request-response', prefix = 'attendee%d' % self.n_attendees,
								  parent = attendee )
			self._define_element( 'role', prefix = 'attendee%d' % self.n_attendees,
								  parent = attendee )

			self.n_attendees += 1

	def get_attendee_email( self, n ):
		return getattr( self, 'attendee%d_smtp_address' % n )

	def set_attendee_email( self, n, value ):
		return setattr( self, 'attendee%d_smtp_address' % n, value )

	def create( self ):
		Kolab2Object.create( self )
		# TODO: to be implemented
