<?php
@%@UCRWARNING=# @%@

$config = array(


	// This is a authentication source which handles admin authentication.
	'admin' => array(
		// The default is to use core:AdminPassword, but it can be replaced with
		// any authentication source.

		'core:AdminPassword',
	),

	// An authentication source which can authenticate against both SAML 2.0
	// and Shibboleth 1.3 IdPs.
	'default-sp' => array(
		'saml:SP',

		// The entity ID of this SP.
		// Can be NULL/unset, in which case an entity ID is generated based on the metadata URL.
		'entityID' => NULL,

		// The entity ID of the IdP this should SP should contact.
		// Can be NULL/unset, in which case the user will be shown a list of available IdPs.
		'idp' => NULL,

		// The URL to the discovery service.
		// Can be NULL/unset, in which case a builtin discovery service will be used.
		'discoURL' => NULL,
	),

	// LDAP authentication source.
	'univention-ldap' => array(
		'uldap:uLDAP',

		// Give the user an option to save their username for future login attempts
		// And when enabled, what should the default be, to save the username or not
		//'remember.username.enabled' => FALSE,
		//'remember.username.checked' => FALSE,

		// The hostname of the LDAP server.
		//'hostname' => '127.0.0.1',
		// Whether SSL/TLS should be used when contacting the LDAP server.
		//'enable_tls' => FALSE,


@!@
from univention.lib.misc import getLDAPURIs
hostname = getLDAPURIs()

expiry_attributes = "'shadowExpire', 'sambaPwdLastSet', 'shadowLastChange', 'shadowMax', 'sambaKickoffTime', 'krb5ValidEnd', 'krb5PasswordEnd', 'sambaAcctFlags'"

config_attributes = configRegistry.get('saml/idp/ldap/get_attributes', '\'uid\'')

attributes = "%s, %s" % (config_attributes, expiry_attributes)

print("	'hostname'		=> '%s'," % hostname)
print("	'enable_tls'		=> %s," % configRegistry.get('saml/idp/ldap/enable_tls', 'true'))
print("	'debug' 		=> %s," % configRegistry.get('saml/idp/ldap/debug', 'FALSE'))
print("	'attributes'		=> array(%s)," % attributes)
print("	'search.base'		=> '%s'," % configRegistry.get('ldap/base', 'null'))
print("	'search.attributes' 	=> array(%s)," % configRegistry.get('saml/idp/ldap/search_attributes', '\'uid\''))

ldap_user = 'uid=sys-idp-user,cn=users,%s' % configRegistry.get('ldap/base', 'null')
if configRegistry.get('saml/idp/ldap/user'):
	ldap_user = configRegistry.get('saml/idp/ldap/user')

print("	'search.username'	=> '%s'," % ldap_user)

password = ''
try:
	password = open('/etc/idp-ldap-user.secret','r').read().strip()
except (IOError, OSError):
	import sys
	print >> sys.stderr, '/etc/idp-ldap-user.secret could not be read!'

print("	'search.password'	=> '%s'," % password)
@!@


		// Whether debug output from the LDAP library should be enabled.
		// Default is FALSE.
		// 'debug' => FALSE
		// The timeout for accessing the LDAP server, in seconds.
		// The default is 0, which means no timeout.
		'timeout' => 0,

		// Set whether to follow referrals. AD Controllers may require FALSE to function.
		'referrals' => TRUE,

		// Which attributes should be retrieved from the LDAP server.
		// This can be an array of attribute names, or NULL, in which case
		// all attributes are fetched.
		//'attributes' => NULL,

		// The pattern which should be used to create the users DN given the username.
		// %username% in this pattern will be replaced with the users username.
		//
		// This option is not used if the search.enable option is set to TRUE.
		//'dnpattern' => 'uid=%username%,ou=people,dc=example,dc=org',
		//'dnpattern' => 'uid=%username%,cn=users,dc=intra,dc=local',
		// As an alternative to specifying a pattern for the users DN, it is possible to
		// search for the username in a set of attributes. This is enabled by this option.
		'search.enable' => TRUE,

		// The DN which will be used as a base for the search.
		// This can be a single string, in which case only that DN is searched, or an
		// array of strings, in which case they will be searched in the order given.
		//'search.base' => 'cn=users,dc=intra,dc=local',
		// The attribute(s) the username should match against.
		//
		// This is an array with one or more attribute names. Any of the attributes in
		// the array may match the value the username.

		// The username & password the simpleSAMLphp should bind to before searching. If
		// this is left as NULL, no bind will be performed before searching.

		// If the directory uses privilege separation,
		// the authenticated user may not be able to retrieve
		// all required attributes, a privileged entity is required
		// to get them. This is enabled with this option.
		'priv.read' => FALSE,

		// The DN & password the simpleSAMLphp should bind to before
		// retrieving attributes. These options are required if
		// 'priv.read' is set to TRUE.
		'priv.username' => NULL,
		'priv.password' => NULL,

	),

);
