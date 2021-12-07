@!@
ROLES = {
	"domaincontroller_master": "Univention Primary Directory Node",
	"domaincontroller_slave": "Univention Replica Directory Node",
	"domaincontroller_backup": "Univention Backup Directory Node",
	"memberserver": "Univention Managed Node",
}

role = configRegistry.get('server/role')
menutitle = ROLES.get(role, "Univention Corporate Server")

if configRegistry.get('version/version'):
	print('%s %s-%s:' % (menutitle, configRegistry.get('version/version'), configRegistry.get('version/patchlevel')))
else:
	print('Univention Thin Client')

if role in ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver']:
	print('')
	startsite = ""
	host = configRegistry.get('hostname')
	domain = configRegistry.get('domainname')

	if host and domain:
		startsite = "%s.%s/" % (host, domain)

	from univention.config_registry.interfaces import Interfaces
	address = Interfaces(configRegistry).get_default_ip_address()
	if address:
		ip = str(address.ip)
		if ip:
			startsite = "%s (%s)" % (startsite, ip)

	if role == 'domaincontroller_master':
		print('The UCS management system is available at https://' + startsite)
	else:
		print('The UCS management system can be reached by following the link to the Primary Directory')
		print('Node at https://' + startsite + ' and selecting the')
		print('Univention Management Console.')

	print('')
	print('You can log into the Univention Management Console - the main tool to manage ')
	print('users, groups, etc. - using the "Administrator" account and the password selected ')
	print('for the root user on the Primary Directory Node.')
@!@

