# http://pysaml2.readthedocs.org/en/latest/howto/config.html
import glob

from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from saml2.saml import NAME_FORMAT_URI

from univention.config_registry.interfaces import Interfaces
from univention.config_registry import ConfigRegistry
ucr = ConfigRegistry()
ucr.load()

i = Interfaces()
try:
	fqdn = '%s.%s' % (ucr['hostname'], ucr['domainname'])
except KeyError:
	fqdn = ''
addresses = [fqdn]
addresses.extend([y['address'] for x, y in i.all_interfaces])

bases = ['%s://%s/umcp/saml' % (scheme, addr) for addr in addresses for scheme in ('https', 'http')]
CONFIG = {
	"entityid": "https://%s/umcp/saml/metadata" % (fqdn,),
	"name_form": NAME_FORMAT_URI,
	"description": "Univention Management Console SAML2.0 Service Provider",
	"service": {
		"sp": {
			"want_assertions_signed": True,
			"authn_requests_signed": True,
			"logout_requests_signed": True,
			"endpoints": {
				"assertion_consumer_service": [('%s/' % (url,), binding) for url in bases for binding in (BINDING_HTTP_POST, BINDING_HTTP_REDIRECT)],
				"single_logout_service": [('%s/slo/' % (url,), binding) for url in bases for binding in (BINDING_HTTP_POST, BINDING_HTTP_REDIRECT)],
			},
#			"required_attributes": ["uid"], FIXME: pysaml2 exception, https://github.com/rohe/pysaml2/issues/246
		},
	},
	"attribute_map_dir": "/usr/share/univention-management-console/saml/attributes/",
	"key_file": "/usr/share/univention-management-console/saml/pki/mykey.pem",
	"cert_file": "/usr/share/univention-management-console/saml/pki/mycert.pem",
	"xmlsec_binary": "/usr/bin/xmlsec1",
	"metadata": {
		"local": glob.glob('/usr/share/univention-management-console/saml/idp/*.xml'),
#		"remote": [{"url": "https://%s/simplesamlphp/saml2/idp/metadata.php" % (host,), "cert":""} for host in addresses],
	},
	# TODO: add contact_person?
}
