# -*- coding: utf-8 -*-
#
# self-servic-acl
#  config registry module to update self-service ACLs
#
# Copyright 2019 Univention GmbH
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

import os
from datetime import datetime
import subprocess

ACL_TEMPLATE = '''
access to filter="univentionObjectType=users/user" attrs=%(ldap_attributes)s
	by self write
	by * +0 break

'''

ACL_FILE_PATH = os.path.join('/usr/share/univention-self-service/', '64selfservice_userattributes.acl')


def handler(configRegistry, changes):
	if configRegistry.get('server/role', None) != "domaincontroller_master":
		print('self-service-acl module can only run on role DC Master')
		return

	params = {}
	params['ldap_attributes'] = configRegistry.get('self-service/ldap_attributes', None)
	profiledata_enabled = configRegistry.is_true('umc/self-service/profiledata/enabled', False)

	# increment version with each change
	version_by_date = datetime.now().strftime('%Y%m%d%H%M%S')

	if profiledata_enabled and params['ldap_attributes']:
		# remove whitespace (split at ',', map str.strip to list, join list with ','
		params['ldap_attributes'] = ','.join(map(str.strip, params['ldap_attributes'].split(',')))

		with open(ACL_FILE_PATH, 'w') as acl_file:
			try:
				acl_file.write(ACL_TEMPLATE % params)
				acl_file.flush()
			except IOError as exc:
				print('Error writing updated LDAP ACL!\n %s' % exc)
				return
		try:
			cmd = ["/usr/sbin/univention-self-service-register-acl", "register", "%s" % ACL_FILE_PATH, "%s" % version_by_date]
			print('Registering ACL in LDAP')
			subprocess.call(cmd, shell=False)
		except subprocess.CalledProcessError as e:
				print('Error registering updated LDAP ACL!\n %s' % e.output)

	else:
		try:
			cmd = ["/usr/sbin/univention-self-service-register-acl", "unregister", "%s" % ACL_FILE_PATH, "%s" % version_by_date]
			subprocess.call(cmd, shell=False)
		except subprocess.CalledProcessError as e:
				print('Error unregistering updated LDAP ACL!\n %s' % e.output)
