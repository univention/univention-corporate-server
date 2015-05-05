#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: Andreas Büsching <crunchy@bitkipper.net>
#
# package's setup.py
#
# Copyright (C) 2004, 2005, 2006
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

"""A generic notifier/event scheduler abstraction

pyNotifier provides an implementation of a notifier/event scheduler and is
capable of wrapping other notifier implementations of GTK+, Qt and wxWindows.
This enables library developers to write code that may be used in applications
with """

from distutils.core import setup

execfile( 'notifier/version.py' )

classifiers = """\
Development Status :: 5 - Production/Stable
Environment :: Console
Environment :: X11 Applications :: GTK
Environment :: X11 Applications :: Qt
Intended Audience :: Developers
License :: OSI Approved :: GNU General Public License (GPL)
Programming Language :: Python
Topic :: Software Development :: Libraries :: Python Modules
Operating System :: Unix
"""

doclines = __doc__.split( '\n' )
setup( name	= 'python-notifier',
       version	= VERSION,
       license  = 'LGPLv2',
       description = doclines[ 0 ],
       long_description = '\n'.join( doclines[ 2 : ] ),
       author	= 'Andreas Büsching',
       author_email = 'crunchy@bitkipper.net',
       url	= 'http://blog.bitkipper.net/?page_id=51',
       download_url = 'http://blog.bitkipper.net/?page_id=51',
       platforms = [ 'any', ],
       classifiers = filter( None, classifiers.split( '\n' ) ),
       packages = [ 'notifier', ],
     )
