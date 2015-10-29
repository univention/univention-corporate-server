# http://pysaml2.readthedocs.org/en/latest/howto/config.html
import glob
import re
from tempfile import NamedTemporaryFile

from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from saml2.saml import NAME_FORMAT_URI

from univention.config_registry.interfaces import Interfaces
from univention.config_registry import ConfigRegistry
ucr = ConfigRegistry()
ucr.load()

if ucr.get('umc/saml/sp-server'):
	fqdn = ucr.get('umc/saml/sp-server')
	addresses = [fqdn]
else:
	i = Interfaces()
	try:
		fqdn = '%s.%s' % (ucr['hostname'], ucr['domainname'])
	except KeyError:
		fqdn = ''
	addresses = [fqdn]
	addresses.extend([y['address'] for x, y in i.all_interfaces if y and y.get('address')])

bases = ['%s://%s/univention-management-console/saml' % (scheme, addr) for addr in addresses for scheme in ('https', 'http')]
CONFIG = {
	"entityid": "https://%s/univention-management-console/saml/metadata" % (fqdn,),
	"name_form": NAME_FORMAT_URI,
	"description": "Univention Management Console SAML2.0 Service Provider",
	"service": {
		"sp": {
			"allow_unsolicited": True,
			"want_assertions_signed": True,
			"authn_requests_signed": True,
			"logout_requests_signed": True,
			"endpoints": {
				"assertion_consumer_service": [('%s/' % (url,), binding) for url in bases for binding in (BINDING_HTTP_POST,)],
				"single_logout_service": [('%s/slo/' % (url,), binding) for url in bases for binding in (BINDING_HTTP_POST, BINDING_HTTP_REDIRECT)],
			},
			"required_attributes": ["uid"],
		},
	},
	"attribute_map_dir": "/usr/lib/python2.7/dist-packages/saml2/attributemaps/",
	"key_file": "/etc/univention/ssl/%s/private.key" % (fqdn,),
	"cert_file": "/etc/univention/ssl/%s/cert.pem" % (fqdn,),
	"xmlsec_binary": "/usr/bin/xmlsec1",
	"metadata": {
		"local": glob.glob('/usr/share/univention-management-console/saml/idp/*.xml'),
	},
	# TODO: add contact_person?
}

tmpfile = NamedTemporaryFile()  # workaround for broken PEM parsing in pysaml2
with open(CONFIG['cert_file'], 'rb') as fd:
	tmpfile.write(re.split('\n(?=-----BEGIN CERTIFICATE-----)', fd.read(), re.M)[-1])
	tmpfile.flush()
CONFIG['cert_file'] = tmpfile.name
