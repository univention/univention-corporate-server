#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMCP definitions like commands, error codes etc.
#
# Copyright 2006-2019 Univention GmbH
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

from univention.lib.i18n import NullTranslation
_ = NullTranslation('univention.management.console').translate

#: buffer size for reading commands from socket
RECV_BUFFER_SIZE = 65536

SUCCESS = 200
BAD_REQUEST = 400
BAD_REQUEST_UNAUTH = 401
BAD_REQUEST_AUTH_FAILED = 401
BAD_REQUEST_FORBIDDEN = 403
BAD_REQUEST_NOT_FOUND = 404
BAD_REQUEST_METHOD_NOT_ALLOWED = 405
BAD_REQUEST_INVALID_ARGS = 406
BAD_REQUEST_INVALID_OPTS = 407
SERVER_ERR = 500
SERVER_ERR_MODULE_DIED = 510
SERVER_ERR_MODULE_FAILED = 511
UMCP_ERR_UNPARSABLE_HEADER = 551
UMCP_ERR_UNPARSABLE_BODY = 554
MODULE_ERR = 590
MODULE_ERR_COMMAND_FAILED = 591
MODULE_ERR_INIT_FAILED = 592


def status_description(code):
	codes = {
		200: _('OK, operation successful'),
		400: _('Bad request'),
		401: _('Unauthorized'),
		403: _('Forbidden'),
		404: _('Not found'),
		405: _('Method not allowed'),
		406: _('Invalid command arguments'),  # FIXME: HTTP violation
		407: _('Invalid or missing command options'),  # FIXME: HTTP violation
		500: _('Internal error'),
		510: _('Module process died unexpectedly'),  # FIXME: HTTP violation
		511: _('Connection to module process failed'),  # FIXME: HTTP violation
		551: _('Unparsable message header'),  # FIXME: HTTP violation
		554: _('Unparsable message body'),  # FIXME: HTTP violation
		590: _('Error occurred during command processing'),  # FIXME: HTTP violation
		591: _('The execution of a command caused a fatal error'),  # FIXME: HTTP violation
		592: _('The initialization of the module caused a fatal error'),  # FIXME: HTTP violation
	}
	return codes.get(code, _('Unknown status code'))
