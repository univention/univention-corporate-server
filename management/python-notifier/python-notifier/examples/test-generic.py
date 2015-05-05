#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: Andreas Büsching  <crunchy@bitkipper.net>
#
# test programm for generic notifier implementation
#
# Copyright (C) 2004, 2005, 2006, 2007
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

import time

def timeout( data ):
    print 'timeout', time.time()
    print '  data    :', data

    return True

def zero( data ):
    print 'timeout', time.time()
    print '  data    :', data

    return True

def dispatch( data ):
    #print 'dispatch', data
    return True

# when no argument is given to init default is GENERIC
notifier.init( notifier.GENERIC, recursive_depth = 5 )
notifier.timer_add( 1000, notifier.Callback( timeout, 'hello' ) )
#notifier.timer_add( 0, notifier.Callback( zero, 'hello' ) )
notifier.dispatcher_add( notifier.Callback( dispatch, 'hello' ) )
#notifier.dispatcher_add( notifier.Callback( dispatch, 'hello' ), False )

notifier.loop()
