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

from socket import getfqdn
from datetime import datetime
import json

class LogEntry(object):
	def __init__(self, username, message, args, tags, log_id, event_name):
		self.username = username
		self.hostname = getfqdn()
		self.message = message
		self.args = [str(arg) for arg in args]
		self.issued = datetime.now()
		self.tags = tags
		self.log_id = log_id
		self.event_name = event_name

	def to_json(self):
		attrs = {
			'username': self.username,
			'hostname': self.hostname,
			'message': self.message,
			'args': self.args,
			'issued': self.issued.strftime('%Y-%m-%d %H:%M:%S%z'),
			'tags': self.tags,
			'log_id': self.log_id,
			'event': self.event_name,
			}
		return json.dumps(attrs)

	@classmethod
	def from_json(cls, body):
		json_body = json.loads(body)
		entry = cls(json_body['username'], json_body['message'], json_body['args'], json_body['tags'], json_body['log_id'], json_body['event'])
		entry.issued = json_body['issued']
		entry.hostname = json_body['hostname']
		return entry
