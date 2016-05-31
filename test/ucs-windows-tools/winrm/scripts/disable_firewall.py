args = dict(
	state = dict(
		choices=['on', 'off'],
		default='on',
		help='firewall state',
	)
)
name = 'disable_firewall'
description = 'disable/enable firewall for all profiles'
ps = '''
netsh advfirewall set allprofiles state %(state)s
'''
