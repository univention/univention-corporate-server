#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: Andreas Büsching  <crunchy@bitkipper.net>
#
# wxWindows test program
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA

import notifier

from wxPython.wx import *

class MyPanel( wxPanel ):
	def __init__( self, parent, ID ):
		self.parent = parent
		wxPanel.__init__( self, parent, ID )
		self.box = wxBoxSizer( wxVERTICAL )
		self.button_close = wxButton( self, 1, "Close" )
		self.button_send = wxButton( self, 2, "Hello" )
		EVT_BUTTON( self, 1, self.OnQuit )
		EVT_BUTTON( self, 2, self.OnSend )
		self.box.Add( self.button_send )
		self.box.Add( self.button_close )
		self.SetAutoLayout( true )
		self.SetSizer( self.box )
		self.box.Fit( self )

	def OnQuit( self, event ):
		self.parent.Close()

	def OnSend( self, event ):
		print 'Hello World!'

class MyFrame( wxFrame ):
	def __init__( self, parent ):
		wxFrame.__init__( self, parent, -1, "MyFrame" )
		self.box = wxBoxSizer( wxVERTICAL )
		self.panel = MyPanel( self, -1 )
		self.box.Add( self.panel )
		self.SetSizer( self.box )
		self.SetAutoLayout( true )
		self.box.Fit( self )

if __name__ == '__main__':
	notifier.init( notifier.WX )
	frame = MyFrame( None )
	frame.Show( true )

	notifier.loop()
