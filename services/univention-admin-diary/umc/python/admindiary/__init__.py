#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages system services
#
# Copyright 2011-2019 Univention GmbH
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

import time
from datetime import datetime, timedelta

from sqlalchemy.exc import OperationalError

from univention.config_registry import ConfigRegistry

from univention.management.console.base import Base
from univention.management.console.modules.decorators import simple_response
import univention.management.console.modules as umcm
import univention.management.console as umc
from univention.management.console.log import MODULE

from univention.admindiary.client import add_comment
from univention.admindiary.backend import get_client, get_engine
from univention.admindiary.events import DiaryEvent


_ = umc.Translation('univention-management-console-module-admindiary').translate


class Instance(Base):
	def _format_entry(self, entry, client):
		message = entry['message']
		if entry['event_name'] != 'COMMENT':
			message = client.translate(entry['event_name'], self.locale.language)
		try:
			message = message.format(**entry['args'])
		except (AttributeError, IndexError, KeyError):
			if entry['args']:
				message = '%s (%s)' % (message, ', '.join(['%s=%s' % (key, arg) for (key, arg) in entry['args'].items()]))
		icon = 'default'
		event = DiaryEvent.get(entry['event_name'])
		if event:
			icon = event.icon or icon
		if entry['event_name'] == 'COMMENT':
			icon = 'comment'
		try:
			date = datetime.strptime(entry['date'], '%Y-%m-%d %H:%M:%S').isoformat()
		except (TypeError, ValueError):
			date = entry['date']
		res_entry = {
			'id': entry['id'],
			'date': date,
			'event': entry['event_name'],
			'hostname': entry['hostname'],
			'username': entry['username'],
			'context_id': entry['context_id'],
			'message': message,
			'icon': icon,
		}
		if 'tags' in entry:
			res_entry['tags'] = entry['tags']
		if 'comments' in entry:
			res_entry['comments'] = entry['comments']
		return res_entry

	def error_handling(self, etype, exc, etraceback):
		ucr = ConfigRegistry()
		ucr.load()
		if isinstance(exc, OperationalError):
			MODULE.error(str(exc))
			db_url = get_engine().url
			hints = []
			hints.append(_('Error connecting to the Admin Diary Backend.'))
			hints.append(_('The database management system is "%s". Is the service running and does it respond to TCP/IP connections?') % (db_url.drivername))
			if db_url.host != 'localhost':
				hints.append(_('Make sure your firewall allows connections to %s.') % (db_url.host))
				hints.append(_('Check the password in /etc/admin-diary.secret. Is it the same on %s and on %s?') % (ucr.get('hostname'), db_url.host))
				hints.append(_('Is %s allowed to connect to the database service on %s?') % (ucr.get('hostname'), db_url.host))
			#hints.append(_('Did the system set up the database? If not, run /usr/share/univention-admin-diary/create-database'))
			raise umcm.UMC_Error('\n'.join(hints), status=500)
		return super(Instance, self).error_handling(exc, etype, etraceback)

	@simple_response
	def options(self):
		with get_client(version=1) as client:
			return client.options()

	@simple_response
	def get(self, context_id):
		with get_client(version=1) as client:
			entries = client.get(context_id)
			result = []
			for entry in entries:
				res_entry = self._format_entry(entry, client)
				result.append(res_entry)
			return sorted(result, key=lambda x: x['id'])

	@simple_response
	def query(self, time_from=None, time_until=None, tag=None, event=None, username=None, hostname=None, message=None):
		with get_client(version=1) as client:
			if time_until:
				time_until = datetime.strptime(time_until, '%Y-%m-%d')
				time_until = (time_until + timedelta(days=1)).strftime('%Y-%m-%d')
			entries = client.query(time_from=time_from, time_until=time_until, tag=tag, event=event, username=username, hostname=hostname, message=message, locale=self.locale.language)
			result = []
			for entry in entries:
				res_entry = self._format_entry(entry, client)
				result.append(res_entry)
			return sorted(result, key=lambda x: x['date'])

	@simple_response
	def add_comment(self, context_id, message):
		add_comment(message, context_id, self.username)
		time.sleep(1)  # give backend time to insert comment...
