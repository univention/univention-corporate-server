#!/usr/bin/python3
#
# Univention Directory Manager
#  OpenID Connect implementation for UDM REST API
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

import json

import jwt
from jwt.algorithms import RSAAlgorithm
from tornado.auth import OAuth2Mixin

from univention.config_registry import ucr
from univention.lib.i18n import Translation
from univention.management.console.log import CORE


#from tornado.httpclient import HTTPClientError, HTTPRequest


_ = Translation('univention-directory-manager-rest').translate


class OAuthException(Exception):
    pass


class OAuthResource(OAuth2Mixin):
    """Base class for all OAuth resources."""

    def oauth_prepare(self):
        settings = self.application.settings['oauth']
        self.client_id = settings['client_id']
        self.issuer = settings['issuer']

        openid_configuration = {}
        if settings['op_file']:
            with open(settings['op_file']) as fd:  # noqa: ASYNC101
                openid_configuration = json.loads(fd.read())

        if settings['jwks_file']:
            with open(settings['jwks_file']) as fd:  # noqa: ASYNC101
                settings["jwks"] = json.loads(fd.read())
                self.JWKS = settings["jwks"]
        else:
            self.JWKS = {}

        # if settings['client_secret_file']:
        #     with open(settings['client_secret_file']) as fd:  # noqa: ASYNC101
        #         self.client_secret = fd.read().strip()
        # else:
        #     self.client_secret = ''

        self._OAUTH_AUTHORIZE_URL = openid_configuration.get("authorization_endpoint")
        self._OAUTH_ACCESS_TOKEN_URL = openid_configuration.get("token_endpoint")
        self._OAUTH_LOGOUT_URL = openid_configuration.get("end_session_endpoint")
        self._OAUTH_USERINFO_URL = openid_configuration.get("userinfo_endpoint")
        self._OAUTH_CERT_URL = openid_configuration.get("jwks_uri")
        self.id_token_signing_alg_values_supported = openid_configuration.get("id_token_signing_alg_values_supported")

    def bearer_authorization(self, bearer_token):
        claims = self.verify_jwt(bearer_token)
        return claims['uid'], bearer_token

    def verify_jwt(self, access_token):
        # pre-verification and username receiving
        try:
            public_key = RSAAlgorithm.from_jwk(json.dumps(self.JWKS['keys'][0]))
            claims = jwt.decode(
                access_token,
                public_key,
                algorithms=self.id_token_signing_alg_values_supported,
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_nbf': True,
                    'verify_iat': True,
                    'verify_aud': False,  # only relevant for ID Token
                    'verify_iss': True,

                },
                issuer=self.issuer,
                audience=None,
                leeway=ucr.get_int('directory/manager/rest/oauth/grace-time', 600),  # seconds
            )
        except jwt.ExpiredSignatureError:
            CORE.warn("Signature expired")
            raise OAuthException(_("The OAuth response signature is expired."))
        except jwt.InvalidSignatureError as exc:
            CORE.error("Invalid signature: %s" % (exc,))
            raise OAuthException(_('The OAuth response contained an invalid signature: %s') % (exc,))
        except jwt.InvalidIssuerError as exc:
            CORE.warn("Invalid issuer: %s" % (exc,))
            raise OAuthException(_('The OAuth response contained an invalid issuer: %s') % (exc,))
        except jwt.InvalidAudienceError as exc:
            CORE.warn("Invalid signature: %s" % (exc,))
            raise OAuthException(_('The OAuth response contained an invalid audience: %s') % (exc,))
        except jwt.MissingRequiredClaimError as exc:
            CORE.warn("Missing claim: %s" % (exc,))
            raise OAuthException(_('The OAuth response is missing a required claim: %s') % (exc,))
        except jwt.ImmatureSignatureError as exc:
            CORE.warn("Immature signature: %s" % (exc,))
            raise OAuthException(_('The OAuth response contained an immature signature: %s') % (exc,))

        CORE.debug('OAuth JWK-Payload: %r' % (claims,))
        return claims

#    async def get_user_information(self, bearer_token):
#        user_info_req = HTTPRequest(
#            self._OAUTH_USERINFO_URL,
#            method="GET",
#            headers={
#                "Accept": "application/json",
#                "Authorization": "Bearer %s" % (bearer_token,),
#            },
#        )
#        http_client = self.get_auth_http_client()
#        try:
#            user_info_res = await http_client.fetch(user_info_req)
#        except HTTPClientError as exc:
#            CORE.warn("Fetching user info failed: %s %s" % (user_info_req.url, exc))
#            raise ServerError(_("Could not receive user information from OP."))
#
#        user_info = json.loads(user_info_res.body.decode('utf-8'))
#        CORE.debug('OAuth User-Info: %r' % (user_info,))
#        return user_info
