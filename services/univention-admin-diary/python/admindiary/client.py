#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2019 Univention GmbH
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

import logging
from logging.handlers import SysLogHandler
from univention.admindiary import LogEntry
import uuid
from getpass import getuser

class RsyslogEmitter(object):
	def __init__(self):
		self.logger = logging.getLogger('univention-admin-diary')
		self.logger.setLevel(logging.DEBUG)
		handler = SysLogHandler(address='/dev/log', facility='user')
		self.logger.addHandler(handler)

	def emit(self, entry):
		self.logger.info('ADMINDIARY: ' + str(entry))

emitter = RsyslogEmitter()

def log_event(event, args=None, username=None, log_id=None):
	args = args or []
	if not isinstance(args, (list, tuple)):
		raise TypeError('"args" must be a list')
	if len(args) != len(event.args):
		raise ValueError('Logging "%s" needs %d argument(s) (%s). %d given' % (event.message, len(event.args), ', '.join(event.args), len(args)))
	return log(event.message, args, None, event.tags, log_id, event.name)


def log(message, args=None, username=None, tags=None, log_id=None, event_name=None):
	if username is None:
		username = getuser()
	if args is None:
		args = []
	if tags is None:
		tags = []
	if log_id is None:
		log_id = str(uuid.uuid4())
	if event_name is None:
		event_name = 'CUSTOM'
	entry = LogEntry(username, message, args, tags, log_id, event_name)
	return log_entry(entry)


def log_entry(entry):
	body = entry.to_json()
	emitter.emit(body)
	return entry.log_id
