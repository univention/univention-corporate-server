
@!@
if configRegistry.is_true('saml/idp/negotiate'):
	from univention.lib.misc import getLDAPURIs
	from univention.saml.php import php_array, php_string, split_attributes

	print('''
$config['univention-negotiate'] = array(
		'negotiate:Negotiate',
		'keytab' => '/etc/simplesamlphp.keytab',
		'fallback' => 'univention-ldap',
	''')
	config_attributes = split_attributes(configRegistry.get('saml/idp/ldap/get_attributes', 'uid'))
	print("	'attributes' => %s," % php_array(config_attributes))
	print("	'hostname' => %s," % php_string(getLDAPURIs()))
	print("	'base' => %s," % php_string(configRegistry["ldap/base"]))

	ldap_user = configRegistry.get('saml/idp/ldap/user') or 'uid=sys-idp-user,cn=users,%(ldap/base)s' % configRegistry
	print("	'adminUser' => %s," % php_string(ldap_user))

	try:
		password = open('/etc/idp-ldap-user.secret','r').read().strip()
		print("	'adminPassword' => %s," % php_string(password))
	except EnvironmentError:
		import sys
		sys.stderr.write('/etc/idp-ldap-user.secret could not be read!')

	subnets = [x.strip() for x in configRegistry.get('saml/idp/negotiate/filter-subnets', '').split(',') if x.strip()]
	if subnets:
		print("	'subnet' => %s" % php_array(subnets))
	print(');')
@!@
