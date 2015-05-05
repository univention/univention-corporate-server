#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: Andreas Büsching	<crunchy@bitkipper.net>
#
# signal - implementation of asynchron events
#
# Copyright (C) 2005, 2006
#		Andreas Büsching <crunchy@bitkipper.net>
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

import notifier
import notifier.signals as signals

def _wait_for_click():
	print "clicked"

def _wait_for_movement( optional = None ):
	print "optional:", optional

def _emitting():
	signals.emit( "clicked" )
	# return True

if __name__ == '__main__':
	notifier.init( notifier.GENERIC )

	signals.new( "clicked" )
	try:
		signals.connect( "clicked2", _wait_for_click )
	except signals.UnknownSignalError, e:
		print 'Exception:', e
	if not signals.exists( 'clicked3' ):
		print "signal 'clicked3' does not exist"
	signals.connect( 'clicked', _wait_for_click )
	signals.connect( 'clicked', notifier.Callback( _wait_for_movement,
												 'optional something' ) )
	notifier.timer_add( 3000, _emitting )

	notifier.loop()
