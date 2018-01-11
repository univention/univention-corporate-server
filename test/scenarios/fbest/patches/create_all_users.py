#!/usr/bin/python
import itertools
import subprocess
import pipes
options = ['posix', 'samba', 'kerberos', 'mail', 'pki', 'person', 'ldap_pwd']

length = range(1, 1 + len(options))
combinations = tuple(itertools.chain(*(itertools.combinations(options, i) for i in length)))
#print length, len(combinations)
#print '\n'.join([', '.join(x) for x in sorted(combinations)])

for options in combinations:
	cmd = ['udm', 'users/user', 'create', '--ignore_exists']
	for i in options:
		cmd.extend(['--option', i])
	cmd.extend(['--set', 'username=x.%s' % ('.'.join(sorted(options)))])
	cmd.extend(['--set', 'lastname=%s' % ('.'.join(sorted(options)))])
	if 'posix' in options or 'samba' in options or 'kerberos' in options or 'ldap_pwd' in options:
		cmd.extend(['--set', 'password=univention'])
	if 'samba' in options and 'posix' not in options:
		cmd.extend(['--set', 'primaryGroup=cn=Domain Users,cn=groups,dc=school,dc=local'])
	if 'posix' not in options and 'samba' not in options and 'person' not in options and 'ldap_pwd' not in options:
		continue

	print '#', ' '.join(pipes.quote(x) for x in cmd)
	if subprocess.call(cmd):
		print 'FAILED !!!'
