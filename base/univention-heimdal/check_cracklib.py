#!/usr/bin/python

import cracklib
import sys

params = {}

end = False
while not end:
	line = sys.stdin.readline()
	line = line[:-1]
	if line == 'end':
		end = True
		continue

	try:
		key, val = line.split(': ',1)
	except:
		print 'key value pair is not correct: %s' % line
		sys.exit(1)
	params[key] = val

if not 'new-password' in params:
	print 'missing password'
	sys.exit(1)

try:
	cracklib.FascistCheck( params['new-password'] )
	print 'APPROVED'
except ValueError, e:
	print str(e)
