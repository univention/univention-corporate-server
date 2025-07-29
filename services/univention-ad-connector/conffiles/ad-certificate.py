#
# Univention AD Connector
#  this baseconfig script automatically generates the SSL certificate for the AD host
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
from shlex import quote


ad_var = 'connector/ad/ldap/host'
ssl_path = '/etc/univention/ssl'

cert_cmd = '/usr/sbin/univention-certificate'
cert_log = '/var/log/univention/ad-connector-certificate.log'


def handler(configRegistry, changes):
    new = configRegistry.get(ad_var, '')
    path = os.path.join(ssl_path, new)
    if new and not os.path.exists(path):
        os.system('%s new -name %s >> %s 2>&1' % (cert_cmd, quote(new), cert_log))  # noqa: S605
