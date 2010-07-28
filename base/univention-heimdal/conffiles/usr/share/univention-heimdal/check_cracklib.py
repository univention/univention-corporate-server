#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
@%@UCRWARNING=# @%@

import sys
import univention.password

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

if 'principal' in params:
	pwdCheck = univention.password.Check(None, params['principal'])
	try:
		pwdCheck.check(params['new-password'])
		print 'APPROVED'
	except ValueError, e:
		print str(e)

