
@!@
if configRegistry.is_true('saml/idp/negotiate'):
	print('''
$config['univention-negotiate'] = array(
		'negotiate:Negotiate',
		'keytab' => '/etc/simplesamlphp.keytab',
		'fallback' => 'univention-ldap',
	''')
	print("	'attributes' => array(%s)," % configRegistry.get('saml/idp/ldap/get_attributes', 'uid'))
	from univention.lib.misc import getLDAPURIs
	hostname = getLDAPURIs()
	print("	'hostname' => '%s'," % (hostname,))
	print("	'base' => '%s'," % (configRegistry.get('ldap/base', 'null'),))
	ldap_user = 'uid=sys-idp-user,cn=users,%s' % configRegistry.get('ldap/base', 'null')
	if configRegistry.get('saml/idp/ldap/user'):
		ldap_user = configRegistry.get('saml/idp/ldap/user')
	print("	'adminUser' => '%s'," % (ldap_user,))
	password = ''
	try:
		password = open('/etc/idp-ldap-user.secret','r').read().strip()
	except (IOError, OSError):
		import sys
		print >> sys.stderr, '/etc/idp-ldap-user.secret could not be read!'
	print("	'adminPassword' => '%s'," % (password,))
	subnets = [x.strip() for x in configRegistry.get('saml/idp/negotiate/filter-subnets', '').split(',') if x.strip()]
	if subnets:
		print("	'subnet' => array('%s')" % ("', '".join(subnets),))
	print(');')
@!@
