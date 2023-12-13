#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Directory Manager
# Univention Configuration Registry Module to rewrite OAuth configuration for UDM-REST-API
#
# Copyright 2022-2024 Univention GmbH
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

from __future__ import print_function

import json
import sys

import requests
from six.moves.urllib_parse import quote

from univention.config_registry import handler_set


verify = True


def handler(config_registry, changes):
    oauth_op = config_registry.get('directory/manager/rest/oauth/issuer')
    if not oauth_op:
        print('directory/manager/rest/oauth/issuer not set, nothing to do')
        return

    well_known_uri = '%s/.well-known/openid-configuration' % (oauth_op,)
    response = requests.get(well_known_uri, verify=verify)

    try:
        well_known = response.json()
    except ValueError:
        print('OAuth OP: %r response: %r' % (oauth_op, response.content), file=sys.stderr)
        raise

    try:
        safe_filename = quote(well_known['issuer'], safe='')
        certs_uri = well_known['jwks_uri']
    except KeyError:
        print('OAuth OP: %r Well-Known: %r' % (oauth_op, well_known), file=sys.stderr)
        raise

    with open('/usr/share/univention-directory-manager-rest/oauth/%s.json' % (safe_filename,), 'wb') as fd:
        fd.write(json.dumps(well_known, sort_keys=True, indent=4).encode('ASCII'))

    cert_response = requests.get(certs_uri, verify=verify)
    cert_response.json()  # validate JSON!
    with open('/usr/share/univention-directory-manager-rest/oauth/%s.jwks' % (safe_filename,), 'wb') as fd:
        fd.write(cert_response.content)

    if oauth_op != well_known['issuer']:
        print('Warning: Issuer different: %r != %r' % (oauth_op, well_known['issuer']), file=sys.stderr)

    handler_set([
        'directory/manager/rest/oauth/client-id=https://%(hostname)s.%(domainname)s/univention/udm/' % config_registry,
        'directory/manager/rest/oauth/issuer=%s' % (oauth_op),
        'directory/manager/rest/oauth/client-secret-file=/etc/udm-rest-oauth.secret',
        'directory/manager/rest/oauth/op-file=/usr/share/univention-directory-manager-rest/oauth/%s.json' % (safe_filename),
        'directory/manager/rest/oauth/jwks-file=/usr/share/univention-directory-manager-rest/oauth/%s.jwks' % (safe_filename),
    ])
