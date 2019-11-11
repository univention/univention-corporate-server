#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2019 Univention GmbH
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

import os
import logging
from logging.handlers import SysLogHandler
import uuid
from getpass import getuser
from functools import partial, wraps

from univention.admindiary import DiaryEntry, get_logger, get_events_to_reject
from univention.admindiary.events import DiaryEvent

get_logger = partial(get_logger, 'client')


def exceptionlogging(f):
	@wraps(f)
	def wrapper(*args, **kwds):
		try:
			return f(*args, **kwds)
		except Exception as exc:
			get_logger().error('%s failed! %s' % (f.__name__, exc))
			import traceback
			get_logger().error(traceback.format_exc())
			return ''
	return wrapper


class RsyslogEmitter(object):
	def __init__(self):
		self.handler = None

	def emit(self, entry):
		if self.handler is None:
			if os.path.exists('/dev/log'):
				self.handler = SysLogHandler(address='/dev/log', facility='user')
			else:
				get_logger().error('RsyslogEmitter().emit() failed: /dev/log does not exist, cannot emit entry (%s)' % (entry,))
				return
		record = logging.LogRecord('diary-rsyslogger', logging.INFO, None, None, 'ADMINDIARY: ' + str(entry), (), None, None)
		self.handler.emit(record)


emitter = RsyslogEmitter()


@exceptionlogging
def add_comment(message, context_id, username=None):
	event = DiaryEvent('COMMENT', {'en': message})
	return write_event(event, username=username, context_id=context_id)


@exceptionlogging
def write_event(event, args=None, username=None, context_id=None):
	args = args or {}
	return write(event.message, args, username, event.tags, context_id, event.name)


@exceptionlogging
def write(message, args=None, username=None, tags=None, context_id=None, event_name=None):
	if username is None:
		username = getuser()
	if args is None:
		args = {}
	if tags is None:
		tags = []
	if context_id is None:
		context_id = os.environ.get('ADMINDIARY_CONTEXT') or str(uuid.uuid4())
	if event_name is None:
		event_name = 'CUSTOM'
	entry = DiaryEntry(username, message, args, tags, context_id, event_name)
	return write_entry(entry)


@exceptionlogging
def write_entry(entry):
	entry.assert_types()
	blocked_events = get_events_to_reject()
	if entry.event_name in blocked_events:
		get_logger().info('Rejecting %s' % entry.event_name)
		return
	body = entry.to_json()
	emitter.emit(body)
	get_logger().debug('Successfully wrote %s. (%s)' % (entry.context_id, entry.event_name))
	return entry.context_id
