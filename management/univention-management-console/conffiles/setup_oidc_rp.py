#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
# Univention Configuration Registry Module to rewrite OIDC configuration for UMC
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
    oidc_op = config_registry.get('umc/oidc/issuer')
    if not oidc_op:
        print('umc/oidc/issuer not set, nothing to do')
        return

    well_known_uri = '%s/.well-known/openid-configuration' % (oidc_op,)
    response = requests.get(well_known_uri, verify=verify)

    try:
        well_known = response.json()
    except ValueError:
        print('OIDC OP: %r response: %r' % (oidc_op, response.content), file=sys.stderr)
        raise

    try:
        safe_filename = quote(well_known['issuer'], safe='')
        certs_uri = well_known['jwks_uri']
    except KeyError:
        print('OIDC OP: %r Well-Known: %r' % (oidc_op, well_known), file=sys.stderr)
        raise

    with open('/usr/share/univention-management-console/oidc/%s.json' % (safe_filename,), 'wb') as fd:
        fd.write(json.dumps(well_known, sort_keys=True, indent=4).encode('ASCII'))

    cert_response = requests.get(certs_uri, verify=verify)
    cert_response.json()  # validate JSON!
    with open('/usr/share/univention-management-console/oidc/%s.jwks' % (safe_filename,), 'wb') as fd:
        fd.write(cert_response.content)

    if oidc_op != well_known['issuer']:
        print('Warning: Issuer different: %r != %r' % (oidc_op, well_known['issuer']), file=sys.stderr)

    fqdn = '%(hostname)s.%(domainname)s' % config_registry

    handler_set([
        'umc/oidc/default-op=%s' % (fqdn,),
        'umc/oidc/%s/client-id=https://%s/univention/oidc/' % (fqdn, fqdn),
        'umc/oidc/%s/issuer=%s' % (fqdn, oidc_op),
        'umc/oidc/%s/client-secret-file=/etc/umc-oidc.secret' % (fqdn,),
        'umc/oidc/%s/op-file=/usr/share/univention-management-console/oidc/%s.json' % (fqdn, safe_filename),
        'umc/oidc/%s/jwks-file=/usr/share/univention-management-console/oidc/%s.jwks' % (fqdn, safe_filename),
        'umc/oidc/%s/extra-parameter=kc_idp_hint' % (fqdn,),
    ])
