#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
# Univention Configuration Registry Module to rewrite SAML IDP configuration for UMC
#
# Copyright 2015 Univention GmbH
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

from subprocess import call, Popen, PIPE
from tempfile import NamedTemporaryFile
import sys

import univention.uldap

php_code = '''<?php

set_error_handler(function($errno, $errstr, $errfile, $errline) {
    throw new ErrorException($errstr, 0, $errno, $errfile, $errline);
});

$entityid = $argv[1];
$_SERVER['REQUEST_URI'] = $entityid;
$_SERVER['REQUEST_METHOD'] = 'POST';
$_POST['xmldata'] = file_get_contents("php://stdin");
chdir('/usr/share/simplesamlphp/www/admin');
ob_start();
require_once('./metadata-converter.php');
ob_end_clean();
print($output["saml20-sp-remote"]);
print("array_merge(\$metadata['$entityid'], array(
	'simplesaml.nameidattribute' => 'uid',
	'simplesaml.attributes' => TRUE,
	'attributes' => array('uid'),
	'description' => 'Univention Management Console SAML2.0 Service Provider',  # TODO:
	'OrganizationName' => 'Univention Management Console SAML2.0 Service Provider',
));");
'''


def handler(config_registry, changes):
	with open('/etc/simplesamlphp/metadata/umc.php', 'w') as fd:
		failed = []
		fd.write('<?php\n')
		with NamedTemporaryFile() as temp:
			temp.write(php_code)
			temp.flush()
			for server in get_saml_idp_servers():
				try:
					entityid, metadata = get_saml_metadata(server)
				except ValueError:
					failed.append(server)
					continue

				process = Popen(['/usr/bin/php', temp.name, entityid], stdout=PIPE, stderr=PIPE, stdin=PIPE)
				stdout, stderr = process.communicate(metadata)
				if process.returncode != 0:
					sys.stderr.write(stderr)
					failed.append(server)
					continue
				fd.write(stdout)
				fd.write('\n\n')
		if failed:
			raise SystemExit('Failed to create entries for %s' % (', '.join(failed)))
	if call(['/usr/bin/php', '-lf', '/etc/simplesamlphp/metadata/umc.php']):
		raise SystemExit('/etc/simplesamlphp/metadata/umc.php seems to be broken.')


def get_saml_idp_servers():
	lo = univention.uldap.getMachineConnection()
	for dn, attrs in lo.search(filter="(&(objectClass=univentionDomainController)(|(univentionServerRole=master)(univentionServerRole=backup)))", attr=['cn', 'associatedDomain']):
		yield '%s.%s' % (attrs['cn'][0], attrs['associatedDomain'][0])
	lo.lo.unbind()


def get_saml_metadata(server):
	metadata = 'https://%s/umcp/saml/metadata' % (server,),
	process = Popen([
		'/usr/bin/wget',
		'--ca-certificate', '/etc/univention/ssl/ucsCA/CAcert.pem',
		'-O', '-', '-q',
		metadata
	], stdout=PIPE)
	stdout, _ = process.communicate()
	if process.returncode != 0:
		return
	return metadata, stdout
