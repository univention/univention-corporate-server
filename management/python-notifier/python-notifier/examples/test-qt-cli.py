#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: Andreas Büsching <crunchy@bitkipper.net>
#
# test programm for the QT3 and QT4 notifier
#
# Copyright (C) 2004, 2005, 2006, 2007
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

import PyQt4.Qt as qt
import notifier

import sys

class QTestApp( qt.QCoreApplication ):
	def __init__( self ):
		qt.QCoreApplication.__init__( self, sys.argv )

		self.timer_id = notifier.timer_add( 1000, self.timerTest )
		self.dispatch_it = 10

	def recvQuit( self, mmsg, data = None ):
		if version == 4:
			self.quit()
		else:
			self.exit_loop()

	def timerTest( self ):
		print 'tick'
		return True

	def _dispatch( self ):
		print 'dispatch'
		self.dispatch_it -= 1
		return self.dispatch_it > 0

class MyThread( qt.QThread ):
	def run( self ):
		self._timer = notifier.timer_add( 2000, self.tick )

		notifier.loop()
		# import time
		# while True:
		# 	print 'going to sleep'
		# 	time.sleep( 1 )
		# 	# in order to process events in this thread
		# 	qt.QCoreApplication.processEvents()
		# 	print 'wake up'

	def tick( self ):
		print 'tick my thread'
		return True

if __name__ == '__main__':
	notifier.init( notifier.QT )
	app = QTestApp()

	mt = MyThread()
	mt.start()

	#notifier.dispatcher_add( app._dispatch )
	print 'exit code: %d' % notifier.loop()
