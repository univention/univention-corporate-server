# -*- coding: utf-8 -*-
#
# Univention SAML
#  listener module: management of SAML service providers
#
# Copyright 2013-2021 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

from __future__ import absolute_import

import glob
import os
import os.path
import xml.etree.ElementTree
from subprocess import Popen, PIPE
from typing import IO, Dict, Iterable, List, Optional, Set, Text, Tuple, Union  # noqa F401

import listener
import univention.debug as ud
from univention.saml.php import php_array, php_bool, php_bytes, php_string

name = 'univention-saml-simplesamlphp-configuration'
description = 'Manage simpleSAMLphp service providers'
filter = '(objectClass=univentionSAMLServiceProvider)'

# based on /usr/share/simplesamlphp/www/admin/metadata-converter.php
raw_metadata_generator = '/usr/share/univention-saml/metadata-converter.php'
sp_config_dir = '/etc/simplesamlphp/metadata.d'
include_file = '/etc/simplesamlphp/metadata/metadata_include.php'


def ldap2bool(value):
	# type: (bytes) -> bool
	try:
		bool_ = value.decode('ASCII').lower()
		return {
			'true': True,
			'1': True,
			'false': False,
			'0': False,
		}[bool_]
	except LookupError:
		raise TypeError('Not a PHP bool: %s' % (bool_,))


@listener.SetUID(0)
def handler(dn, new, old):
	# type: (str, Optional[Dict[str, List[bytes]]], Optional[Dict[str, List[bytes]]]) -> None
	if old:
		delete_old(old)
	if new:
		build_new(dn, new)
	build_include()


def spi2filename(spi):
	# type: (bytes) -> str
	return os.path.join(sp_config_dir, '%s.php' % spi.decode('ASCII').replace('/', '_'))


def delete_old(old):
	# type: (Dict[str, List[bytes]]) -> None
	spi = old.get('SAMLServiceProviderIdentifier')
	if spi:
		old_filename = spi2filename(spi[0])
		if os.path.exists(old_filename):
			ud.debug(ud.LISTENER, ud.INFO, 'Deleting old SAML SP Configuration file %s' % old_filename)
			try:
				os.unlink(old_filename)
			except IOError as exc:
				ud.debug(ud.LISTENER, ud.ERROR, 'Deleting failed: %s' % (exc,))


def build_new(dn, new):
	# type: (str, Dict[str, List[bytes]]) -> None
	spi = new.get('SAMLServiceProviderIdentifier')
	spa = new.get('isServiceProviderActivated')
	if spi and spa and spa[0] == b"TRUE":
		filename = spi2filename(spi[0])
		ud.debug(ud.LISTENER, ud.INFO, 'Writing to SAML SP Configuration file %s' % filename)
		with open(filename, "w") as fd:
			write_configuration_file(dn, new, fd)
		validate_conf(filename)


def build_include():
	# type: () -> None
	with open(include_file, 'w') as fd:
		fd.write('<?php\n')
		for filename in glob.glob(os.path.join(sp_config_dir, '*.php')):
			fd.write("require_once(%s);\n" % (php_string(filename),))


def write_configuration_file(dn, new, fd):
	# type: (str, Dict[str, List[bytes]], IO[str]) -> None
	(metadata, entityid) = parse_metadata(new) or (b"", new['SAMLServiceProviderIdentifier'][0].decode('ASCII'))

	raw = new.get('rawsimplesamlSPconfig')
	if raw and raw[0]:
		fd.write(raw[0].decode('ASCII'))
	else:
		build_conf(dn, new, fd, metadata, entityid)


def parse_metadata(new):
	# type: (Dict[str, List[bytes]]) -> Optional[Tuple[bytes, str]]
	spm = new.get('serviceProviderMetadata')
	if spm and spm[0]:
		metadata = spm[0]
		try:
			root = xml.etree.ElementTree.fromstring(metadata.decode('ASCII'))
			entityid = root.get('entityID')
			if entityid:
				return (metadata, entityid)
		except xml.etree.ElementTree.ParseError as exc:
			ud.debug(ud.LISTENER, ud.ERROR, 'Parsing metadata failed: %s' % (exc,))

	return None


def build_conf(dn, new, fd, metadata, entityid):
	# type: (str, Dict[str, List[bytes]], IO[str], bytes, str) -> None
	fd.write("<?php\n")
	fd.write('$memberof = "False";\n')
	fd.write("if(file_exists('/etc/simplesamlphp/serviceprovider_enabled_groups.json')){\n")
	fd.write("	$samlenabledgroups = json_decode(file_get_contents('/etc/simplesamlphp/serviceprovider_enabled_groups.json'), true);\n")
	fd.write("	if(array_key_exists(%s, $samlenabledgroups) and isset($samlenabledgroups[%s])){\n" % (php_string(dn), php_string(dn)))
	fd.write("		$memberof = $samlenabledgroups[%s];\n" % (php_string(dn)))
	fd.write("	}\n")
	fd.write("}\n")

	if metadata:
		fd.flush()
		process = Popen(['php', raw_metadata_generator, entityid], stdout=fd, stderr=PIPE, stdin=PIPE)
		stdout, stderr = process.communicate(metadata)
		if process.returncode:
			ud.debug(ud.LISTENER, ud.ERROR, 'Failed to create %s: %s' % (fd.name, stderr.decode('UTF-8', 'replace'),))
		fd.write("$further = array(\n")
	else:
		fd.write('$metadata[%s] = array(\n' % php_string(entityid))
		fd.write("	'AssertionConsumerService' => %s,\n" % php_array(new.get('AssertionConsumerService')))
		if new.get('singleLogoutService'):
			fd.write("	'SingleLogoutService' => %s,\n" % php_array(new.get('singleLogoutService')))

	if new.get('signLogouts') and new['signLogouts'][0] == b"TRUE":
		fd.write("	'sign.logout' => TRUE,\n")
	if new.get('NameIDFormat'):
		fd.write("	'NameIDFormat' => %s,\n" % php_bytes(new['NameIDFormat'][0]))
	name_id_attrs = new.get('simplesamlNameIDAttribute')
	if name_id_attrs:
		fd.write("	'simplesaml.nameidattribute' => %s,\n" % php_bytes(name_id_attrs[0]))
	if new.get('simplesamlAttributes'):
		fd.write("	'simplesaml.attributes' => %s,\n" % php_bool(ldap2bool(new['simplesamlAttributes'][0])))

	attributes, mapping = parse_mapping(new.get('simplesamlLDAPattributes', []))
	if new.get('simplesamlAttributes') and new['simplesamlAttributes'][0] == b"TRUE":
		if name_id_attrs:
			attributes.add(name_id_attrs[0])
		fd.write("	'attributes' => %s,\n" % php_array(attributes))

	if new.get('attributesNameFormat'):
		fd.write("	'attributes.NameFormat' => %s,\n" % php_bytes(new['attributesNameFormat'][0]))
	if new.get('serviceproviderdescription'):
		fd.write("	'description' => %s,\n" % php_bytes(new['serviceproviderdescription'][0]))
	if new.get('serviceProviderOrganizationName'):
		fd.write("	'OrganizationName' => %s,\n" % php_bytes(new['serviceProviderOrganizationName'][0]))
	if new.get('privacypolicyURL'):
		fd.write("	'privacypolicy' => %s,\n" % php_bytes(new['privacypolicyURL'][0]))

	fd.write("	'assertion.lifetime' => %d,\n" % (int(new.get('assertionLifetime', [b'300'])[0].decode('ASCII')),))
	fd.write("	'authproc' => array(\n")
	if not metadata:  # TODO: make it configurable
		# make sure that only users that are enabled to use this service provider are allowed
		fd.write("		10 => array(\n")
		fd.write("			'class' => 'authorize:Authorize',\n")
		fd.write("			'regex' => FALSE,\n")
		fd.write("			'enabledServiceProviderIdentifier' => %s,\n" % php_array([dn]))
		fd.write("			'memberOf' => $memberof,\n")
		fd.write("		),\n")
		if mapping:
			fd.write("		50 => array(\n			'class' => 'core:AttributeMap',\n")
			for key, attrs in mapping.items():
				fd.write("			%s => %s,\n" % (php_bytes(key), php_bytes(attrs[0]) if len(attrs) == 1 else php_array(attrs)))
			fd.write("		),\n")
	else:
		fd.write("		100 => array('class' => 'core:AttributeMap', 'name2oid'),\n")

	fd.write("	),\n")

	fd.write(");\n")
	if metadata:
		fd.write("$metadata[%s] = array_merge($metadata[%s], $further);\n" % (php_string(entityid), php_string(entityid)))


def parse_mapping(attrs):
	# type: (List[bytes]) -> Tuple[Set[bytes], Dict[bytes, List[bytes]]]
	attributes = set()  # type: Set[bytes]
	mapping = {}  # type: Dict[bytes, List[bytes]]

	for attr in attrs:
		line = [val.strip() for val in attr.split(b"=", 1)]
		try:
			src, dst = line
		except ValueError:
			src, = dst, = line
		if src:
			attributes.add(src)
			if src != dst:
				mapping.setdefault(src, []).append(dst)

	return (attributes, mapping)


def validate_conf(filename):
	# type: (str) -> None
	process = Popen(['php', '-lf', filename], stderr=PIPE, stdout=PIPE)
	stdout, stderr = process.communicate()
	if process.returncode:
		ud.debug(ud.LISTENER, ud.ERROR, 'broken PHP syntax(%d) in %s: %s%s' % (process.returncode, filename, stderr.decode('UTF-8', 'replace'), stdout.decode('UTF-8', 'replace')))
		try:
			with open(filename) as fd:
				ud.debug(ud.LISTENER, ud.ERROR, 'repr(%r)' % (fd.read(),))
			os.unlink(filename)
		except IOError:
			pass
