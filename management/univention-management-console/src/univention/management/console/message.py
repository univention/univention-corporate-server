#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2006-2023 Univention GmbH
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

"""
A backwards compatible layer to wrap HTTP request and response messages.
The API of the Python objects representing the messages are based on the class :class:`.Message`.
"""
from __future__ import absolute_import, print_function

import mimetypes
import sys
import time

import ldap
import ldap.sasl
import six

import univention.admin.uexceptions as udm_errors
from univention.management.console.error import PasswordRequired
from univention.management.console.ldap import get_user_connection
from univention.management.console.log import CORE, PARSER, PROTOCOL


try:
    from typing import Any, Dict, List, Optional, Union  # noqa: F401
    RequestType = int
    UmcpBody = Union[dict, str, bytes]
except ImportError:
    pass

MIMETYPE_JSON = 'application/json'

__all__ = ('Request', 'Response')


class Message(object):
    """
    Represents a wrapper for a HTTP message.

    :param type: message type (RESPONSE or REQUEST)
    :param str command: type of request (UPLOAD or COMMAND)
    :param str mime_type: defines the MIME type of the message body
    :param data: binary data that should contain a message
    :param arguments: the URL path which is requested.
    :param options: options passed to the command handler. This works for request messages with MIME type application/json only.
    """

    RESPONSE, REQUEST = range(2)
    __counter = 0

    def __init__(self, type=REQUEST, command=u'', mime_type=MIMETYPE_JSON, data=None, arguments=None, options=None):
        # type: (RequestType, str, str, bytes, List[str], Dict[str, Any]) -> None
        self.id = None  # type: Optional[str]
        if mime_type == MIMETYPE_JSON:
            self.body = {}  # type: UmcpBody
        else:
            self.body = b''
        self.command = command
        self.arguments = arguments if arguments is not None else []
        self.mimetype = mime_type
        if mime_type == MIMETYPE_JSON:
            self.options = options if options is not None else {}
        self.cookies = {}
        self.headers = {}
        self.http_method = None

    @classmethod
    def generate_id(cls):
        # type: () -> str
        # cut off 'L' for long
        generated_id = u'%lu-%d' % (int(time.time() * 100000), Message.__counter)
        Message.__counter += 1
        return generated_id

    def _create_id(self):
        # type: () -> None
        self.id = self.generate_id()

    def recreate_id(self):
        # type: () -> None
        """Creates a new unique ID for the message"""
        self._create_id()

    # JSON body properties
    def _set_key(self, key, value, cast=None):
        if self.mimetype == MIMETYPE_JSON:
            if cast is not None:
                self.body[key] = cast(value)
            else:
                self.body[key] = value
        else:
            PARSER.warn('Attribute %s just available for MIME type %s' % (key, MIMETYPE_JSON))

    def _get_key(self, key, default=None):
        if isinstance(default, dict):
            default = default.copy()
        if self.mimetype == MIMETYPE_JSON:
            if isinstance(default, dict):
                self.body.setdefault(key, default)
            return self.body.get(key, default)
        else:
            PARSER.info('Attribute %s just available for MIME type %s' % (key, MIMETYPE_JSON))
            return default

    #: contains a human readable error message
    message = property(lambda self: self._get_key('message'), lambda self, value: self._set_key('message', value))

    #: contains error information
    error = property(lambda self: self._get_key('error'), lambda self, value: self._set_key('error', value))

    #: contains the data that represents the result of the request
    result = property(lambda self: self._get_key('result'), lambda self, value: self._set_key('result', value))

    #: contains the HTTP status code defining the success or failure of a request
    status = property(lambda self: self._get_key('status'), lambda self, value: self._set_key('status', value, int))

    #: contains the reason phrase for the status code
    reason = property(lambda self: self._get_key('reason'), lambda self, value: self._set_key('reason', value))

    #: defines options to pass on to the module command
    options = property(lambda self: self._get_key('options'), lambda self, value: self._set_key('options', value))

    #: flavor of the request
    flavor = property(lambda self: self._get_key('flavor'), lambda self, value: self._set_key('flavor', value))


class Request(Message):
    """Wraps a HTTP request message in a backwards compatible Python API format"""

    _user_connections = set()  # prevent garbage collection

    def __init__(self, command, arguments=None, options=None, mime_type=MIMETYPE_JSON):
        # type: (str, Any, Any, str) -> None
        Message.__init__(self, Message.REQUEST, command, arguments=arguments, options=options, mime_type=mime_type)
        self._create_id()
        self.username = None
        self.password = None
        self.user_dn = None
        self.auth_type = None
        self.locale = None
        self._request_handler = None

    def require_password(self):
        if self.auth_type is not None:
            raise PasswordRequired()

    def get_user_ldap_connection(self, no_cache=False, **kwargs):
        if not self.user_dn:
            return  # local user (probably root)
        try:
            lo, po = get_user_connection(bind=self.bind_user_connection, write=kwargs.pop('write', False), follow_referral=True, no_cache=no_cache, **kwargs)
            if not no_cache:
                self._user_connections.add(lo)
            return lo
        except (ldap.LDAPError, udm_errors.base) as exc:
            CORE.warn('Failed to open LDAP connection for user %s: %s' % (self.user_dn, exc))

    def bind_user_connection(self, lo):
        CORE.process('LDAP bind for user %r.' % (self.user_dn,))
        try:
            if self.auth_type == 'SAML':
                lo.lo.bind_saml(self.password)
                if not lo.lo.compare_dn(lo.binddn, self.user_dn):
                    CORE.warn('SAML binddn does not match: %r != %r' % (lo.binddn, self.user_dn))
                    self.user_dn = lo.binddn
            else:
                try:
                    lo.lo.bind(self.user_dn, self.password)
                except ldap.INVALID_CREDENTIALS:  # workaround for Bug #44382: the password might be a SAML message, try to authenticate via SAML
                    etype, exc, etraceback = sys.exc_info()
                    CORE.error('LDAP authentication for %r failed: %s' % (self.user_dn, exc))
                    if len(self.password) < 25:
                        raise
                    CORE.warn('Trying to authenticate via SAML.')
                    try:
                        lo.lo.bind_saml(self.password)
                    except ldap.OTHER:
                        CORE.error('SAML authentication failed.')
                        six.reraise(etype, exc, etraceback)
                    CORE.error('Wrong authentication type. Resetting.')
                    self.auth_type = 'SAML'
        except ldap.INVALID_CREDENTIALS:
            etype, exc, etraceback = sys.exc_info()
            exc = etype('An error during LDAP authentication happened. Auth type: %s; SAML message length: %s; DN length: %s; Original Error: %s' % (self.auth_type, len(self.password or '') if len(self.password or '') > 25 else False, len(self.user_dn or ''), exc))
            six.reraise(etype, exc, etraceback)


class Response(Message):
    """
    This class describes a response to a request from the console
    frontend to the console daemon
    """

    def __init__(self, request=None, data=None, mime_type=MIMETYPE_JSON):
        # type: (Request, Any, str) -> None
        Message.__init__(self, Message.RESPONSE, mime_type=mime_type)
        if request:
            self.id = request.id
            self.command = request.command
            self.arguments = request.arguments
            if request.mimetype == MIMETYPE_JSON:
                self.options = request.options
        elif data:
            self.parse(data)

    recreate_id = None

    def set_body(self, filename, mimetype=None):
        # type: (str, Optional[str]) -> None
        """
        Set body of response by guessing the mime type of the given
        file if not specified and adding the content of the file to the body. The mime
        type is guessed using the extension of the filename.
        """
        if mimetype is None:
            self.mimetype, encoding = mimetypes.guess_type(filename)
        else:
            self.mimetype = mimetype

        if self.mimetype is None:
            PROTOCOL.process('Failed to guess MIME type of %s' % filename)
            raise TypeError('Unknown mime type')

        with open(filename, 'rb') as fd:
            # FIXME: should check size first
            self.body = fd.read()
