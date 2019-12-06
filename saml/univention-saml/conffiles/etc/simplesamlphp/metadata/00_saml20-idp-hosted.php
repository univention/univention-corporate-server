<?php
@%@UCRWARNING=# @%@
/**
 * SAML 2.0 IdP configuration for simpleSAMLphp.
 *
 * See: https://rnd.feide.no/content/idp-hosted-metadata-reference
 */

$idp_config = array(
	/*
	 * The hostname of the server (VHOST) that will use this SAML entity.
	 *
	 * Can be '__DEFAULT__', to use this entry by default.
	 */
	'host' => '__DEFAULT__',

	/* X.509 key and certificate. Relative to the cert directory. */
@!@
print("	'privatekey'	=> '%s'," % configRegistry.get('saml/idp/certificate/privatekey', configRegistry.get('apache2/ssl/key', '/etc/univention/ssl/%s.%s/private.key' % (configRegistry.get('hostname'), configRegistry.get('domainname')) )))
print("	'certificate'	=> '%s'," % configRegistry.get('saml/idp/certificate/certificate', configRegistry.get('apache2/ssl/certificate', '/etc/univention/ssl/%s.%s/cert.pem' % (configRegistry.get('hostname'), configRegistry.get('domainname')) )))
@!@
	/*
	 * Authentication source to use. Must be one that is configured in
	 * 'config/authsources.php'.
	 */
	//'auth' => 'example-userpass',
@!@
print("	'auth'	=> '%s'," % configRegistry.get('saml/idp/authsource', 'univention-negotiate'))
@!@

	/* Uncomment the following to use the uri NameFormat on attributes. */
	/*
	'attributes.NameFormat' => 'urn:oasis:names:tc:SAML:2.0:attrname-format:uri',
	'authproc' => array(
		// Convert LDAP names to oids.
		100 => array('class' => 'core:AttributeMap', 'name2oid'),
	),
	*/

);
@!@
from univention.saml.lib import get_idps
idps = get_idps(configRegistry)
for idp in idps:
	print("$metadata['{}'] = array_replace($idp_config, array('host' => '{}'));".format(
		idp['entityID'],
		idp['baseurl']
	))
@!@
