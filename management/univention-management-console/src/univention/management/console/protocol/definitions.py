#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMCP definitions like commands, error codes etc.
#
# Copyright 2006-2016 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import sys

from univention.lib.i18n import NullTranslation

_ = NullTranslation('univention.management.console').translate

#: buffer size for reading commands from socket
RECV_BUFFER_SIZE = 65536


class Status(object):

	def __init__(self, name, code, description):
		self._name = name
		self._code = code
		self._description = description

	@property
	def name(self):
		return self._name

	@property
	def code(self):
		return self._code

	@property
	def description(self):
		return self._description

#: list of valid status names, codes, and human readable descriptions
STATUS = (
	# UMCP request success messages
	Status('SUCCESS', 200, _('OK, operation successful')),
	Status('SUCCESS_SHUTDOWN', 250, _('OK, operation successful ask for shutdown of connection')),

	# the UMCP request was parsable but within the context it is not valid
	Status('BAD_REQUEST', 400, _('Bad request')),
	Status('BAD_REQUEST_UNAUTH', 401, _('Unauthorized')),
	Status('BAD_REQUEST_FORBIDDEN', 403, _('Forbidden')),
	Status('BAD_REQUEST_NOT_FOUND', 404, _('Not found')),
	Status('BAD_REQUEST_INVALID_ARGS', 406, _('Invalid command arguments')),  # FIXME: HTTP violation
	Status('BAD_REQUEST_INVALID_OPTS', 407, _('Invalid or missing command options')),  # FIXME: HTTP violation
	Status('BAD_REQUEST_AUTH_FAILED', 401, _('The authentication has failed')),

	# UMCP server core errors
	Status('SERVER_ERR', 500, _('Internal error')),
	Status('SERVER_ERR_MODULE_DIED', 510, _('Module process died unexpectedly')),
	Status('SERVER_ERR_MODULE_FAILED', 511, _('Connection to module process failed')),

	# generic UMCP parser errors
	Status('UMCP_ERR_UNPARSABLE_HEADER', 551, _('Unparsable message header')),
	Status('UMCP_ERR_UNPARSABLE_BODY', 554, _('Unparsable message body')),

	# errors occuring during command process in module process
	Status('MODULE_ERR', 590, _('Error occurred during command processing')),
	Status('MODULE_ERR_COMMAND_FAILED', 591, _('The execution of a command caused a fatal error')),
	Status('MODULE_ERR_INIT_FAILED', 592, _('The initialization of the module caused a fatal error'))
)

# create symbols for status codes
for status in STATUS:
	setattr(sys.modules['univention.management.console.protocol.definitions'], status.name, status.code)


def status_description(code):
	for status in STATUS:
		if status.code == code:
			return status.description
	return _('Unknown status code')
