#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2017 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import glob
import shutil
import socket
import tempfile
import subprocess
import contextlib

import requests
from ldap.filter import filter_format
from defusedxml.ElementTree import fromstring

import univention.uldap
import univention.config_registry
from univention.management.console.modules.diagnostic import Critical, ProblemFixed
from univention.management.console.config import ucr

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate


@contextlib.contextmanager
def download_tempfile(url, headers=None):
	with tempfile.NamedTemporaryFile() as fob:
		response = requests.get(url, headers=headers, stream=True)
		shutil.copyfileobj(response.raw, fob)
		fob.flush()
		yield fob.name


def find_node(node, element):
	elem = node.find(element)
	if elem is not None:
		return elem
	for child in node:
		x = find_node(child, element)
		if x is not None:
			return x


def run(_umc_instance):
	test_identity_provider_certificate()
	test_service_provider_certificate()


def test_identity_provider_certificate():
	# download from all ip addresses of ucs-sso. the IDP certificate (/etc/simplesamlphp/*-idp-certificate.crt)
	# compare this with /usr/share/univention-management-console/saml/idp/*.xml
	# If it fails: univention-run-joinscripts --force --run-scripts 92univention-management-console-web-server
	for host in socket.gethostbyname_ex(ucr['ucs/server/sso/fqdn'])[2]:
		try:
			with download_tempfile('https://%s/simplesamlphp/saml2/idp/certificate' % (host,), {'host': ucr['ucs/server/sso/fqdn']}) as certificate:
				certificate = certificate.read()
				for idp in glob.glob('/usr/share/univention-management-console/saml/idp/*.xml'):
					with open(idp) as fd:
						cert = find_node(fromstring(fd.read()), '{http://www.w3.org/2000/09/xmldsig#}X509Certificate')
						if cert.text.strip() not in certificate:
							raise Critical(_('The certificate of the SAML identity provider does not match.'), buttons=[{
								'action': 'fix_identity_provider_certificate',
								'label': _('Repair identity provider certificate')
							}])

		except requests.exceptions.ConnectionError:
			print 'error, connecting'
			pass


def fix_identity_provider_certificate(_umc_instance):
	# FIXME: DC Slave needs credentials
	subprocess.call(['univention-run-joinscripts', '--force', '--run-scripts', '92univention-management-console-web-server'])
	test_identity_provider_certificate()
	raise ProblemFixed()


def test_service_provider_certificate():
	# compare /etc/univention/ssl/$(hostname -f)/cert.pem with
	# univention-ldapsearch -LLL "(&(serviceProviderMetadata=*)(univentionObjectType=saml/serviceprovider)(SAMLServiceProviderIdentifier=https://$(hostname -f)/univention/saml/metadata))" serviceProviderMetadata  | ldapsearch-wrapper | ldapsearch-decode64
	# If it fails: /usr/share/univention-management-console/saml/update_metadata
	#
	# fails because https://help.univention.com/t/renewing-the-ssl-certificates/37 was not used. https://help.univention.com/t/renewing-the-complete-ssl-certificate-chain/36
	lo = univention.uldap.getMachineConnection()
	certs = lo.search(filter_format('(&(serviceProviderMetadata=*)(univentionObjectType=saml/serviceprovider)(SAMLServiceProviderIdentifier=https://%s/univention/saml/metadata))', ['%s.%s' % (ucr.get('hostname'), ucr.get('domainname'))]), attr=['serviceProviderMetadata'])
	with open('/etc/univention/ssl/%s.%s/cert.pem' % (ucr.get('hostname'), ucr.get('domainname'))) as fd:
		for cert in certs:
			cert = find_node(fromstring(cert[1]['serviceProviderMetadata'][0]), '{http://www.w3.org/2000/09/xmldsig#}X509Certificate')
			if cert.text.strip() not in fd.read():
				raise Critical(_('The certificate of the SAML service provider does not match.'), buttons=[{
					'action': 'fix_service_provider_certificate',
					'label': _('Repair service provider certificate')
				}])


def fix_service_provider_certificate(_umc_instance):
	# FIXME: DC Slave needs credentials
	subprocess.call(['univention-run-joinscripts', '--force', '--run-scripts', '92univention-management-console-web-server'])
	test_identity_provider_certificate()
	raise ProblemFixed()


actions = {
	'fix_service_provider_certificate': fix_service_provider_certificate,
	'fix_identity_provider_certificate': fix_identity_provider_certificate,
}


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	run(0)
	main()
