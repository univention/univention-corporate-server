#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
@%@UCRWARNING=# @%@

import cracklib
import sys
import subprocess

@!@
for key in configRegistry.keys():
	if key.startswith('kerberos/password/quality/'):
		keyshort = key[26:]
		if keyshort in [ 'ascii_lowercase', 'ascii_uppercase' ]:
			print "cracklib.%s = '''%s'''" % (keyshort, configRegistry[key])
		elif keyshort in [ 'diff_ok', 'dig_credit', 'low_credit', 'min_length', 'oth_credit', 'up_credit' ]:
			try:
				val = int(configRegistry[key])
				print "cracklib.%s = %s" % (keyshort, configRegistry[key])
			except:
				pass
@!@

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
	userdn = None
	policies = {}

	p = subprocess.Popen( [ 'ldapsearch -LLLx krb5PrincipalName=%s dn' % params['principal'] ], shell=True, stdout=subprocess.PIPE, close_fds=True)
	chld_out, chld_err = p.communicate()
	for line in chld_out.splitlines():
		if line.startswith('dn: '):
			userdn = line[4:]

	if userdn:
		p = subprocess.Popen( [ 'univention-policy-result %s' % userdn ], shell=True, stdout=subprocess.PIPE, close_fds=True)
		chld_out, chld_err = p.communicate()
		key = None
		val = None
		for line in chld_out.splitlines():
			if line.startswith('Attribute: '):
				key = line[11:]
			elif line.startswith('Value: '):
				val = line[7:]
				if key:
					policies[key] = val

		pwlen = policies.get('univentionPWLength')
		if pwlen and pwlen.isdigit():
			cracklib.min_length = int(pwlen)

try:
	cracklib.FascistCheck( params['new-password'] )
	print 'APPROVED'
except ValueError, e:
	print str(e)
