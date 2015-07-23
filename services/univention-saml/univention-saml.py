# -*- coding: utf-8 -*-
#
# Univention SAML
#  listener module: management of SAML service providers
#
# Copyright 2013-2014 Univention GmbH
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
import os.path
import univention.debug as ud

name='univention-saml'
description='Manage simpleSAMLphp service providers'
filter='(objectClass=univentionSAMLServiceProvider)'

sp_config_dir = '/etc/simplesamlphp/metadata.d'
include_file = '/etc/simplesamlphp/metadata/metadata_include.php'

def remove_sp_config(old_filename):
	listener.setuid(0)
	try:
		# delete file
		if os.path.exists(old_filename):
			os.unlink(old_filename)

		# delete file reference from include file
		if not os.path.isfile(include_file):
			return

		with open(include_file, 'r') as f:
			lines = f.readlines()

		with open(include_file, 'w') as f:
			for line in lines:
				if not old_filename in line:
					f.write(line)
	except IOError as e:
		print 'Error: Could not open %s: %s' % (include_file, str(e))

	finally:
		listener.unsetuid()
	
def add_sp_config(new_filename):
	try:
		with open(include_file, 'a') as f:
			f.write('<?php require_once("%s"); ?>\n' % new_filename)

	except IOError as e:
		print 'Error: Could not open %s: %s' % (new_filename, str(e))

def handler(dn, new, old):
	if old:
		if old.get('SAMLServiceProviderIdentifier'):
			# delete old service provider config file
			old_filename = os.path.join(sp_config_dir, '%s.php' % old.get('SAMLServiceProviderIdentifier')[0].replace('/', '_'))
			ud.debug(ud.LISTENER, ud.INFO, 'Deleting old SAML SP Configuration file %s' % old_filename)
			remove_sp_config(old_filename)

	if new:
		if new.get('SAMLServiceProviderIdentifier') and new.get('isServiceProviderActivated')[0] == "TRUE":
			# write new service provider config file
			new_filename = os.path.join(sp_config_dir, '%s.php' % new.get('SAMLServiceProviderIdentifier')[0].replace('/', '_'))
			ud.debug(ud.LISTENER, ud.INFO, 'Writing to SAML SP Configuration file %s' % new_filename)

			listener.setuid(0)
			with open(new_filename, 'w') as f:
				f.write("<?php\n")
				f.write("$metadata[\'%s\'] = array(\n" % new.get('SAMLServiceProviderIdentifier')[0])
				f.write("	'AssertionConsumerService'	=> array('%s'),\n" % "', '".join(new.get('AssertionConsumerService')))
				if new.get('NameIDFormat'):
					f.write("	'NameIDFormat'	=> '%s',\n" % new.get('NameIDFormat')[0])
				if new.get('simplesamlNameIDAttribute'):
					f.write("	'simplesaml.nameidattribute'	=> '%s',\n" % new.get('simplesamlNameIDAttribute')[0])
				if new.get('simplesamlAttributes'):
					f.write("	'simplesaml.attributes'	=> %s,\n" % new.get('simplesamlAttributes')[0])
				simplesamlLDAPattributes = list(new.get('simplesamlLDAPattributes', [])) + ['enabledServiceProviderIdentifier']
				f.write("	'attributes'	=> array('%s'),\n" % "', '".join(simplesamlLDAPattributes))
				if new.get('serviceproviderdescription'):
					f.write("	'description'	=> '%s',\n" % new.get('serviceproviderdescription')[0])
				if new.get('serviceProviderOrganizationName'):
					f.write("	'OrganizationName'	=> '%s',\n" % new.get('serviceProviderOrganizationName')[0])
				if new.get('privacypolicyURL'):
					f.write("	'privacypolicy'	=> '%s',\n" % new.get('privacypolicyURL')[0])
				if new.get('attributesNameFormat'):
					f.write("	'attributes.NameFormat'	=> '%s',\n" % new.get('attributesNameFormat')[0])
				if new.get('singleLogoutService'):
					f.write("	'SingleLogoutService'	=> '%s',\n" % new.get('singleLogoutService')[0])

				# make sure that only users that are enabled to use this service provider are allowed
				f.write("	'authproc' => array(\n")
				f.write("		60 => array(\n")
				f.write("		'class' => 'authorize:Authorize',\n")
				f.write("		'regex' => FALSE,\n")
				f.write("		'enabledServiceProviderIdentifier' =>  array('%s'),\n" % dn )
				f.write("	)),\n")
				f.write(");\n")
					
			add_sp_config(new_filename)
			listener.unsetuid()

	script = '/etc/init.d/apache2'
	if os.path.exists(script):
		ud.debug(ud.LISTENER, ud.INFO, "%s reload" % script )
		listener.run(script, ['apache2', 'reload'], uid=0)
	else:
		ud.debug(ud.LISTENER, ud.INFO, "Apache Webserver not reloaded: %s does not exist" % (script,))
