#!/usr/bin/python3
#
# Univention Management Console
# Univention Configuration Registry Module to rewrite OIDC configuration for UMC
#
# SPDX-FileCopyrightText: 2022-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import json
import sys
from urllib.parse import quote

import requests

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

    # some customers want to use a non-UCS keycloak with their own OIDC clients
    # we don't want to change the client configuration for UMC in this case
    if config_registry.is_false('umc/oidc/autoconfiguration'):
        return

    fqdn = config_registry['umc/oidc/rp/server'] if config_registry.get('umc/oidc/rp/server') else '%(hostname)s.%(domainname)s' % config_registry

    handler_set([
        'umc/oidc/default-op=%s' % (fqdn,),
        'umc/oidc/%s/client-id=https://%s/univention/oidc/' % (fqdn, fqdn),
        'umc/oidc/%s/issuer=%s' % (fqdn, oidc_op),
        'umc/oidc/%s/client-secret-file=/etc/umc-oidc.secret' % (fqdn,),
        'umc/oidc/%s/openid-configuration=/usr/share/univention-management-console/oidc/%s.json' % (fqdn, safe_filename),
        'umc/oidc/%s/openid-certs=/usr/share/univention-management-console/oidc/%s.jwks' % (fqdn, safe_filename),
        'umc/oidc/%s/extra-parameter=kc_idp_hint' % (fqdn,),
    ])
