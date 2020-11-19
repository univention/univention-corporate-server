# http://pysaml2.readthedocs.org/en/latest/howto/config.html
import glob
import os.path
from tempfile import NamedTemporaryFile
from cryptography import x509
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.backends import default_backend

from saml2 import SamlBase, BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from saml2.saml import NAME_FORMAT_URI, NAMEID_FORMAT_TRANSIENT, NAMEID_FORMAT_PERSISTENT
import saml2.attributemaps

from univention.config_registry.interfaces import Interfaces
from univention.config_registry import ConfigRegistry
ucr = ConfigRegistry()
ucr.load()


class CertDoesNotMatchPrivateKeyError(Exception):
	pass


def public_key_compare(key1, key2):
	pn1 = key1.public_numbers()
	pn2 = key2.public_numbers()
	return pn1.e == pn2.e and pn1.n == pn2.n


def get_cert():
	'''
	The cert file can contain multiple certs (e.g. with lets encrypt)
	saml expects only the one certificate that matches the private key
	'''
	with open(CONFIG['cert_file'], 'rb') as cert_file:
		cert = x509.load_pem_x509_certificate(cert_file.read(), default_backend())
		public_cert_key = cert.public_key()
	with open(CONFIG['key_file'], 'rb') as key_file:
		private_key = key_file.read()
		public_key = load_pem_private_key(private_key, password=None, backend=default_backend()).public_key()
	if public_key_compare(public_cert_key, public_key):
		return cert.public_bytes(Encoding.PEM)
	raise CertDoesNotMatchPrivateKeyError(
		'Cert: "{}" does not match private key: "{}"'.format(CONFIG['cert_file'], CONFIG['key_file'])
	)


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

bases = ['%s://%s/univention/saml' % (scheme, addr) for addr in addresses for scheme in ('https', 'http')]
CONFIG = {
	"entityid": "https://%s/univention/saml/metadata" % (fqdn,),
	"name_form": NAME_FORMAT_URI,
	"description": "Univention Management Console at %s" % (fqdn,),
	"service": {
		"sp": {
			"allow_unsolicited": True,
			"want_assertions_signed": True,
			"want_response_signed": True,
			"authn_requests_signed": True,
			"logout_requests_signed": True,
			"endpoints": {
				"assertion_consumer_service": [('%s/' % (url,), binding) for url in bases for binding in (BINDING_HTTP_POST,)],
				"single_logout_service": [('%s/slo/' % (url,), binding) for url in bases for binding in (BINDING_HTTP_POST, BINDING_HTTP_REDIRECT)],
			},
			"name_id_format": [NAMEID_FORMAT_TRANSIENT, NAMEID_FORMAT_PERSISTENT],
			"required_attributes": [x.strip() for x in ucr.get('umc/saml/required_attributes', 'uid').split(',') if x.strip()],
			"optional_attributes": [x.strip() for x in ucr.get('umc/saml/optional_attributes', '').split(',') if x.strip()]
		},
	},
	"attribute_map_dir": os.path.dirname(saml2.attributemaps.__file__),
	"key_file": "/etc/univention/ssl/%s/private.key" % (fqdn,),
	"cert_file": "/etc/univention/ssl/%s/cert.pem" % (fqdn,),
	"xmlsec_binary": "/usr/bin/xmlsec1",
	"metadata": {
		"local": glob.glob('/usr/share/univention-management-console/saml/idp/*.xml'),
	},
	"debug": ucr.is_true('umc/saml/debug', False),
	"contact_person": [
		{
			"givenname": ucr.get('umc/saml/contact_person/%s/givenname' % (type_,), ''),
			"surname": ucr.get('umc/saml/contact_person/%s/surname' % (type_,), ''),
			"company": ucr.get('umc/saml/contact_person/%s/company' % (type_,), ''),
			"mail": [x.strip() for x in ucr.get('umc/saml/contact_person/%s/mail' % (type_,), '').split(',') if x.strip()],
			"type": type_,
		} for type_ in ('technical', 'administrative') if ucr.get('umc/saml/contact_person/%s/mail' % (type_,))
	],
	"organization": {
		"name": [
			(ucr.get('umc/saml/organization/name', 'Univention Management Console %s' % (fqdn,)), "en"),
		],
		"display_name": [ucr.get('umc/saml/organization/display-name', 'Univention Management Console %s' % (fqdn,))],
		"url": [
			(ucr.get('umc/saml/organization/url', 'https://%s/univention/management/' % (fqdn,)), "en"),
		],
	},
}

tmpfile = NamedTemporaryFile()  # workaround for broken PEM parsing in pysaml2
tmpfile.write(get_cert())
tmpfile.flush()
CONFIG['cert_file'] = tmpfile.name

OASIS_DEFAULT_NS_PREFIXES = {
	'ds': 'http://www.w3.org/2000/09/xmldsig#',
	'md': 'urn:oasis:names:tc:SAML:2.0:metadata',
	'mdui': 'urn:oasis:names:tc:SAML:metadata:ui',
	'saml': 'urn:oasis:names:tc:SAML:2.0:assertion',
	'samlp': 'urn:oasis:names:tc:SAML:2.0:protocol',
	'xenc': 'http://www.w3.org/2001/04/xmlenc#',
	'xs': 'http://www.w3.org/2001/XMLSchema',
	'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
	'alg': "urn:oasis:names:tc:SAML:metadata:algsupport",
	'mdattr': "urn:oasis:names:tc:SAML:metadata:attribute"
}
SamlBase().register_prefix(OASIS_DEFAULT_NS_PREFIXES)
