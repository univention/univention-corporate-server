#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
# Listener Module to rewrite SAML IDP configuration for UMC
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

__package__ = ''  # workaround for PEP 366
import listener

import os
import sys
import glob
import errno
import os.path
import xml.etree.ElementTree
from tempfile import NamedTemporaryFile
from subprocess import call, Popen, PIPE

name = description = 'univention-saml-umc'
filter = "(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))"
attribute = ['univentionSAMLServiceProvider']

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
	'NameIDFormat'  => 'urn:oasis:names:tc:SAML:2.0:nameid-format:basic',
	'simplesaml.nameidattribute' => 'uid',
	'simplesaml.attributes' => TRUE,
	'attributes' => array('uid'),
	'description' => 'Univention Management Console SAML2.0 Service Provider',
	'OrganizationName' => 'Univention Management Console SAML2.0 Service Provider',
));");
'''  # TODO: add dynamic description?
sp_config_dir = '/etc/simplesamlphp/metadata/umc'


def handler(dn, new, old):
	filename = os.path.join(sp_config_dir, '%s.php' % (dn.replace('/', '_'),))
	listener.setuid(0)
	try:
		try:
			os.makedirs(sp_config_dir)
		except OSError as exc:
			if exc.errno != errno.EEXIST or not os.path.isdir(sp_config_dir):
				raise

		if old and old.get('univentionSAMLServiceProvider'):
			remove_config(filename)
		if new and new.get('univentionSAMLServiceProvider'):
			try:
				write_metadata_configuration(filename, new['univentionSAMLServiceProvider'])
			except:
				remove_config(filename)
				raise
	finally:
		write_global_configuration()
		listener.unsetuid()


def remove_config(filename):
	if os.path.exists(filename):
		os.unlink(filename)


def write_global_configuration():
	with open('/etc/simplesamlphp/metadata/umc.php', 'w') as fd:
		fd.write('<?php\n')
		for path in glob.glob(os.path.join(sp_config_dir, '*.php')):
			fd.write('require_once("%s");\n' % (path,))


def write_metadata_configuration(filename, metadata):
	try:
		root = xml.etree.ElementTree.fromstring(metadata)
		entityid = root.get('entityID')
	except xml.etree.ElementTree.ParseError:
		return
	with NamedTemporaryFile() as temp:
		temp.write(php_code)
		temp.flush()

		fd = open(filename, 'w')
		process = Popen(['/usr/bin/php', temp.name, entityid], stdout=fd, stderr=PIPE, stdin=PIPE)
		stdout, stderr = process.communicate(metadata)
		if process.returncode != 0:
			print >> sys.stderr, stderr
			print >> sys.stderr, 'Failed to create %s' % (filename,)
		fd.close()
	if call(['/usr/bin/php', '-lf', filename]):
		raise SystemExit('/etc/simplesamlphp/metadata/umc.php seems to be broken.')
