# Univention SAML
# Listener module to configure selfservice userattribute list
# This module creates LDAP ACLs on the DC Master
#
# Copyright 2019 Univention GmbH
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
import subprocess
import os.path
from datetime import datetime
import univention.admin.modules
import univention.debug as ud
from univention.config_registry import ConfigRegistry

name = 'selfservice-userattributes-master'
description = 'Setup LDAP ACLs for selfservice userattributes'
filter = '(objectClass=univentionPolicyRegistry)'

ACL_TEMPLATE = '''
access to filter="univentionObjectType=users/user" attrs=%(ldap_attributes)s
	by self write
	by * none break

'''
ACL_FILE_PATH = os.path.join('/usr/share/univention-self-service/', '67selfservice_userattributes.acl')

univention.admin.modules.update()
udm_users_user = univention.admin.modules.get("users/user")

ucr = ConfigRegistry()
ucr.load()


def handler(dn, new, old):
	if ucr.get('server/role', None) != "domaincontroller_master":
		ud.debug(ud.LISTENER, ud.WARN, '%s module can only run on role DC Master' % name)
		return

	userattr_policy_objectdn = ucr.get('umc/self-service/configpolicy', 'cn=self-service-userattributes,cn=univention,%s' % ucr.get('ldap/base'))

	params = {}
	params['base'] = ucr.get('ldap/base')

	listener.setuid(0)
	try:
		if userattr_policy_objectdn == new['entryDN'][0]:
			# get (and sort) all udm attribute values from policy
			selfservice_userattrs = []
			for key, value in new.items():
				# all ucr policy values are encoded
				if key.startswith('univentionRegistry;entry-hex-'):
					key_name = key.split('univentionRegistry;entry-hex-', 1)[1].decode('hex').strip()
					udm_attr_name = value[0].strip()
					# todo: get mapping
					# get LDAP Attribute mapping for each attribute
					ldap_attr_name = udm_users_user.mapping.mapName(udm_attr_name)
					if ldap_attr_name:
						selfservice_userattrs.append((key_name, udm_attr_name, ldap_attr_name))
					else:
						ud.debug(ud.LISTENER, ud.WARN, 'error with UDM attribute %s mapping, ignoring.' % udm_attr_name)

			# sort attr list by ucr policy keys
			selfservice_userattrs.sort(key=lambda attr_tuple: attr_tuple[0])
			params['ldap_attributes'] = ",".join([x for _, _, x in selfservice_userattrs])

			# TODO: Frontend can get all required information for UDM attributes e.g. required syntax
			# here and store them globally in LDAP

			# register ACLs
			with open(ACL_FILE_PATH, 'w') as acl_file:
				try:
					acl_file.write(ACL_TEMPLATE % params)
					acl_file.flush()
				except IOError as e:
					ud.debug(ud.LISTENER, ud.ERROR, 'Error writing updated LDAP ACL!\n %s' % e.output)
					return

			try:
				# increment version with each change to ensure LDAP update
				version_by_date = datetime.now().strftime('%Y%m%d%H%M%S.%f')

				cmd = ["/usr/sbin/univention-self-service-register-acl", "%s" % ACL_FILE_PATH, "%s" % version_by_date]
				subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)

			except subprocess.CalledProcessError as e:
				ud.debug(ud.LISTENER, ud.ERROR, 'Error registering updated LDAP ACL!\n %s' % e.output)

		else:
			ud.debug(ud.LISTENER, ud.INFO, 'An ucr policy object was modified, but it is not the object the listener is configured for (%s). Ignoring changes. DN of modified object: %s' % (userattr_policy_objectdn, new['entryDN']))

	finally:
		listener.unsetuid()
