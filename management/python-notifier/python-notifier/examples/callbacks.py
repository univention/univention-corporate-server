#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: Andreas Büsching  <crunchy@bitkipper.net>
#
# callbacks test
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA

import notifier


notifier.init( notifier.GENERIC )

def cb( bla, fasel, fasel2 ):
    print bla
    print fasel
    print fasel2

b = notifier.Callback( cb )
c = notifier.Callback( cb, 'addional user data', 'more additional user data' )
c( 'mandatory arguments' )

print 'b == c', b == c
print 'b == cb', b == cb
