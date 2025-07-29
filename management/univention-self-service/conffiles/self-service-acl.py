#
# self-servic-acl
#  config registry module to update self-service ACLs
#
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
import subprocess
from datetime import datetime


ACL_TEMPLATE = '''
access to filter="univentionObjectType=users/user" attrs=%(ldap_attributes)s
    by self write
    by * +0 break

'''

ACL_FILE_PATH = os.path.join('/usr/share/univention-self-service/', '64selfservice_userattributes.acl')


def handler(configRegistry, changes):
    if configRegistry.get('server/role', None) != "domaincontroller_master":
        print('self-service-acl module can only run on role Primary Directory Node')
        return

    params = {}
    params['ldap_attributes'] = configRegistry.get('self-service/ldap_attributes', None)
    profiledata_enabled = configRegistry.is_true('umc/self-service/profiledata/enabled', False)

    # increment version with each change
    version_by_date = datetime.utcnow().strftime('%Y%m%d%H%M%S')

    if profiledata_enabled and params['ldap_attributes']:
        # remove whitespace (split at ',', map str.strip to list, join list with ','
        params['ldap_attributes'] = ','.join(x.strip() for x in params['ldap_attributes'].split(','))

        with open(ACL_FILE_PATH, 'w') as acl_file:
            try:
                acl_file.write(ACL_TEMPLATE % params)
                acl_file.flush()
            except OSError as exc:
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
