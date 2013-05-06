#!/usr/bin/env python
"""
Example for creating UCS packages.
"""
import time

now = time.localtime()
filename = '/tmp/testdeb-%s' % time.strftime('%y%m%d%H%M', now)
tmpfile = open(filename, 'a')
tmpfile.close()
