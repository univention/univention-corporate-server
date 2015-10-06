# -*- coding: utf-8 -*-
#
# Univention SAML
#  listener module: management of SAML service providers
#
# Copyright 2013-2015 Univention GmbH
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

__package__=''  # workaround for PEP 366
import listener

import os
import glob
import os.path
import xml.etree.ElementTree
from tempfile import NamedTemporaryFile
from subprocess import call, Popen, PIPE

import univention.debug as ud

name = 'univention-saml-simplesamlphp-configuration'
description = 'Manage simpleSAMLphp service providers'
filter = '(objectClass=univentionSAMLServiceProvider)'

raw_metadata_generator = '''<?php
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
'''
sp_config_dir = '/etc/simplesamlphp/metadata.d'
include_file = '/etc/simplesamlphp/metadata/metadata_include.php'


def escape_php_string(string):
	return string.replace('\x00', '').replace("\\", "\\\\").replace("'", r"\'")


def php_string(string):
	return "'%s'" % (escape_php_string(string),)


def php_array(list_):
	if not list_:
		return 'array()'
	return "array('%s')" % "', '".join(escape_php_string(x) for x in list_)


def php_bool(bool_):
	mapped = {
		'true': True,
		'1': True,
		'false': False,
		'0': False,
	}.get(bool_.lower())
	if mapped is None:
		raise TypeError('Not a PHP bool: %s' % (bool_,))
	return 'true' if mapped else 'false'


def handler(dn, new, old):
	listener.setuid(0)
	try:
		if old:
			if old.get('SAMLServiceProviderIdentifier'):
				# delete old service provider config file
				old_filename = os.path.join(sp_config_dir, '%s.php' % old.get('SAMLServiceProviderIdentifier')[0].replace('/', '_'))
				if os.path.exists(old_filename):
					ud.debug(ud.LISTENER, ud.INFO, 'Deleting old SAML SP Configuration file %s' % old_filename)
					try:
						os.unlink(old_filename)
					except IOError as exc:
						ud.debug(ud.LISTENER, ud.ERROR, 'Deleting failed: %s' % (exc,))

		if new and new.get('SAMLServiceProviderIdentifier') and new.get('isServiceProviderActivated')[0] == "TRUE":
			# write new service provider config file
			filename = os.path.join(sp_config_dir, '%s.php' % new.get('SAMLServiceProviderIdentifier')[0].replace('/', '_'))
			ud.debug(ud.LISTENER, ud.INFO, 'Writing to SAML SP Configuration file %s' % filename)
			write_configuration_file(dn, new, filename)

		with open(include_file, 'w') as fd:
			fd.write('<?php\n')
			for filename in glob.glob(os.path.join(sp_config_dir, '*.php')):
				fd.write("require_once(%s);\n" % (php_string(filename),))
	finally:
		listener.unsetuid()


def write_configuration_file(dn, new, filename):
	if new.get('serviceProviderMetadata') and new['serviceProviderMetadata'][0]:
		metadata = new['serviceProviderMetadata'][0]
		try:
			root = xml.etree.ElementTree.fromstring(metadata)
			entityid = root.get('entityID')
		except xml.etree.ElementTree.ParseError as exc:
			ud.debug(ud.LISTENER, ud.ERROR, 'Parsing metadata failed: %s' % (exc,))
			return False
	else:
		metadata = None
		entityid = new.get('SAMLServiceProviderIdentifier')[0]

	fd = open(filename, 'w')
	fd.write("<?php\n")
	fd.flush()

	if metadata:
		with NamedTemporaryFile() as temp:
			temp.write(raw_metadata_generator)
			temp.flush()

			process = Popen(['/usr/bin/php', temp.name, entityid], stdout=fd, stderr=PIPE, stdin=PIPE)
			stdout, stderr = process.communicate(metadata)
			if process.returncode != 0:
				ud.debug(ud.LISTENER, ud.ERROR, 'Failed to create %s: %s' % (filename, stderr,))
		fd.write("$further = array(\n")
	else:
		fd.write('$metadata[%s] = array(\n' % php_string(entityid))
		fd.write("	'AssertionConsumerService'	=> %s,\n" % php_array(new.get('AssertionConsumerService')))
		if new.get('singleLogoutService'):
			fd.write("	'SingleLogoutService'	=> %s,\n" % php_array(new.get('singleLogoutService')))

	if new.get('NameIDFormat'):
		fd.write("	'NameIDFormat'	=> %s,\n" % php_string(new.get('NameIDFormat')[0]))
	if new.get('simplesamlNameIDAttribute'):
		fd.write("	'simplesaml.nameidattribute'	=> %s,\n" % php_string(new.get('simplesamlNameIDAttribute')[0]))

	simplesamlLDAPattributes = list(new.get('simplesamlLDAPattributes', [])) + ['enabledServiceProviderIdentifier']
	if new.get('simplesamlAttributes'):
		fd.write("	'simplesaml.attributes'	=> %s,\n" % php_bool(new.get('simplesamlAttributes')[0]))
	if new.get('attributesNameFormat'):
		fd.write("	'attributes.NameFormat'	=> %s,\n" % php_string(new.get('attributesNameFormat')[0]))
	fd.write("	'attributes'	=> %s,\n" % php_array(simplesamlLDAPattributes))

	if new.get('serviceproviderdescription'):
		fd.write("	'description'	=> %s,\n" % php_string(new.get('serviceproviderdescription')[0]))
	if new.get('serviceProviderOrganizationName'):
		fd.write("	'OrganizationName'	=> %s,\n" % php_string(new.get('serviceProviderOrganizationName')[0]))
	if new.get('privacypolicyURL'):
		fd.write("	'privacypolicy'	=> %s,\n" % php_string(new.get('privacypolicyURL')[0]))

	fd.write("	'authproc' => array(\n")
	if not metadata:  # TODO: make it configurable
		# make sure that only users that are enabled to use this service provider are allowed
		fd.write("		60 => array(\n")
		fd.write("		'class' => 'authorize:Authorize',\n")
		fd.write("		'regex' => FALSE,\n")
		fd.write("		'enabledServiceProviderIdentifier' => %s,\n" % php_array([dn]))
		fd.write("		)\n")
	else:
		fd.write("		100 => array('class' => 'core:AttributeMap', 'name2oid'),\n")
	fd.write("	),\n")

	fd.write(");\n")
	if metadata:
		fd.write("$metadata[%s] = array_merge($metadata[%s], $further);" % (php_string(entityid), php_string(entityid)))

	fd.close()
	process = Popen(['/usr/bin/php', '-lf', filename], stderr=PIPE, stdout=PIPE)
	stdout, stderr = process.communicate()
	if process.returncode:
		ud.debug(ud.LISTENER, ud.ERROR, 'broken PHP syntax(%d) in %s: %s%s' % (process.returncode, filename, stderr, stdout))
		try:
			os.unlink(filename)
		except IOError:
			pass
