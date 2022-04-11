#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
# Univention Configuration Registry Module to rewrite OIDC configuration for UMC
#
# Copyright 2022 Univention GmbH
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

import requests
import sys

from six.moves.urllib_parse import quote

from univention.config_registry import handler_set

verify = False   # FIXME: deactivate


def handler(config_registry, changes):
	oidc_op = config_registry.get('umc/oidc/op-issuer')
	if not oidc_op:
		print('umc/oidc/op-issuer not set, nothing to do')
		return

	well_known_uri = '%s/.well-known/openid-configuration' % (oidc_op,)
	response = requests.get(well_known_uri, verify=verify)
	well_known = response.json()

	try:
		certs_uri = well_known['jwks_uri']
	except KeyError:
		print('OIDC IP: %r Well-Known: %r' % (oidc_op, well_known,), file=sys.stderr)
		raise

	cert_filename = '%s.jwks' % (quote(oidc_op, safe=''),)
	with open('/usr/share/univention-management-console/oidc/%s' % (cert_filename,), 'wb') as fd:
		cert_response = requests.get(certs_uri, verify=verify)
		cert_response.json()  # validate JSON!
		fd.write(cert_response.content)

	fqdn = '%(hostname)s.%(domainname)s' % config_registry

	handler_set([
		'umc/oidc/default-op=%s' % (fqdn,),
		'umc/oidc/%s/client-id=%s' % (fqdn, fqdn),
		'umc/oidc/%s/issuer=%s' % (fqdn, oidc_op),
		'umc/oidc/%s/client-secret-file=/etc/umc-oidc.secret' % (fqdn,),
		'umc/oidc/%s/extra-parameter=kc_idp_hint' % (fqdn,),  # TODO: required?
	])
