#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: Andreas Büsching	<crunchy@bitkipper.net>
#
# signal
#
# Copyright (C) 2005, 2006
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

import notifier
import notifier.signals as signals

class TestSignal( signals.Provider ):
	def __init__( self ):
		signals.Provider.__init__( self )
		self.signal_new( 'test-signal' )

test = TestSignal()

def timer_cb( a ):
	print 'timer argument', a
	signals.emit( 'test-signal' )
	test.signal_emit( 'test-signal' )
	print '-------------------------'
	return True

def signal_cb( signal, a, b ):
	print 'signal arguments', signal, a, b
	# disconnect global signal
	signals.disconnect( 'test-signal', signal_cb )

notifier.init( notifier.GENERIC )

signals.new( 'test-signal' )
signals.connect( 'test-signal', notifier.Callback( signal_cb, 1, 2, 'global signal' ) )
test.signal_connect( 'test-signal',notifier.Callback( signal_cb, 1, 2, 'TestSignal signal' ) )
notifier.timer_add( 2000, notifier.Callback( timer_cb, 7 ) )

notifier.loop()
