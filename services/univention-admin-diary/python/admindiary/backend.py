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

import datetime
from contextlib import contextmanager
from functools import partial

from univention.config_registry import ConfigRegistry

from univention.admindiary import get_logger

ucr = ConfigRegistry()
ucr.load()

password = open('/etc/admin-diary.secret').read().strip()

dbms = ucr.get('admin/diary/dbms')
dbhost = ucr.get('admin/diary/dbhost', 'localhost')

get_logger = partial(get_logger, 'backend')

@contextmanager
def connection(module):
	if dbms == 'mysql':
		conn = module.connect(db='admindiary', user='admindiary', host=dbhost, passwd=password)
	elif dbms == 'postgresql':
		conn = module.connect(dbname='admindiary', user='admindiary', host=dbhost, password=password)
	yield conn
	conn.commit()
	conn.close()


@contextmanager
def cursor(module):
	with connection(module) as conn:
		cur = conn.cursor()
		yield cur


if ucr.get('admin/diary/dbms') == 'postgresql':
	import psycopg2

	def _postgresql_add(entry):
		with cursor(psycopg2) as cur:
			cur.execute("INSERT INTO entries (username, hostname, message, args, timestamp, tags, context_id, event_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (entry.username, entry.hostname, entry.message, entry.args, entry.timestamp, entry.tags, entry.context_id, entry.event_name))
		get_logger().info('Successfully added %s to postgresql. (%s)' % (entry.context_id, entry.event_name))

	def _postgresql_query():
		with cursor(psycopg2) as cur:
			args = ['id', 'username', 'hostname', 'message', 'args', 'timestamp', 'tags', 'context_id', 'event_name']
			cur.execute("SELECT %s FROM entries" % ', '.join(args))
			rows = cur.fetchall()
			res = [dict(zip(args, row)) for row in rows]
			for row in res:
				for k, v in row.items():
					if isinstance(v, datetime.datetime):
						row[k] = v.isoformat()
			return res

	add = _postgresql_add
	query = _postgresql_query
elif ucr.get('admin/diary/dbms') == 'mysql':
	import MySQLdb

	def _mysql_add(entry):
		with cursor(MySQLdb) as cur:
			cur.execute("INSERT INTO entries (username, hostname, message, timestamp, context_id, event_name) VALUES (%s, %s, %s, %s, %s, %s)", (entry.username, entry.hostname, entry.message, entry.timestamp, entry.context_id, entry.event_name))
			entry_id = cur.lastrowid
			for arg in entry.args:
				cur.execute("INSERT INTO arguments (log_entry_id, arg) VALUES (%s, %s)", (entry_id, arg))
			for tag in entry.tags:
				cur.execute("INSERT INTO tags (log_entry_id, tag) VALUES (%s, %s)", (entry_id, tag))
		get_logger().info('Successfully added %s to mysql. (%s)' % (entry.context_id, entry.event_name))

	def _mysql_query():
		with cursor(MySQLdb) as cur:
			args = ['id', 'username', 'hostname', 'message', 'timestamp', 'context_id', 'event_name']
			cur.execute("SELECT %s FROM entries" % ', '.join(args))
			rows = cur.fetchall()
			res = [dict(zip(args, row)) for row in rows]
			for row in res:
				entry_id = row.pop('id')
				rows = cur.execute("SELECT arg FROM arguments WHERE log_entry_id = %s", (entry_id,))
				row['args'] = [row['arg'] for row in rows]
				rows = cur.execute("SELECT tag FROM tags WHERE log_entry_id = %s", (entry_id,))
				row['tags'] = [row['tag'] for row in rows]
				for k, v in row.items():
					if isinstance(v, datetime.datetime):
						row[k] = v.isoformat()
			return res
	add = _mysql_add
	query = _mysql_query
else:
	def _no_add(entry):
		raise NotImplementedError()
	def _no_query():
		raise NotImplementedError()

	add = _no_add
	query = _no_query
