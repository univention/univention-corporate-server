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

	def _postgresql_add_with_cursor(entry, cur):
		if entry.event_name == 'COMMENT':
			entry_message = entry.message.get('en')
			event_id = None
		else:
			get_logger().debug('Searching for Event %s' % entry.event_name)
			entry_message = None
			cur.execute("INSERT INTO events (name) VALUES (%s) ON CONFLICT DO NOTHING", (entry.event_name,))
			cur.execute("SELECT id FROM events WHERE name = %s", (entry.event_name,))
			event_id = cur.fetchone()[0]
			get_logger().debug('Found Event ID %s' % event_id)
			if entry.message:
				for locale, message in entry.message.iteritems():
					get_logger().debug('Trying to insert message for %s' % locale)
					cur.execute("SELECT * FROM event_message_translations WHERE event_id = %s AND locale = %s", (event_id, locale))
					if not cur.fetchone():
						get_logger().debug('Found no existing one. Inserting %r' % message)
						cur.execute("INSERT INTO event_message_translations (event_id, locale, locked, message) VALUES (%s, %s, FALSE, %s)", (event_id, locale, message))
			else:
				get_logger().debug('No further message given, though')
		cur.execute("INSERT INTO entries (username, hostname, message, args, timestamp, tags, context_id, event_id, main_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, (SELECT MIN(id) FROM entries WHERE context_id = %s))", (entry.username, entry.hostname, entry_message, entry.args, entry.timestamp, entry.tags, entry.context_id, event_id, entry.context_id))
		get_logger().info('Successfully added %s to postgresql. (%s)' % (entry.context_id, entry.event_name))

	def _postgresql_add(entry):
		with cursor(psycopg2) as cur:
			_postgresql_add_with_cursor(entry, cur)

	def _postgresql_query():
		with cursor(psycopg2) as cur:
			args = ['id', 'username', 'hostname', 'message', 'args', 'timestamp', 'tags', 'context_id', 'event_name', 'amendments']
			cur.execute("SELECT %s, ev.name, (SELECT COUNT(e2.*) FROM entries e2 WHERE e2.main_id = e.id) as amendments FROM entries e INNER JOIN events ev ON ev.id = e.event_id WHERE e.main_id IS NULL" % ', '.join(['e.%s' % a for a in args[:-2]]))
			rows = cur.fetchall()
			res = [dict(zip(args, row)) for row in rows]
			for row in res:
				for k, v in row.items():
					if isinstance(v, datetime.datetime):
						row[k] = v.isoformat()
			return res

	def _postgresql_get(context_id):
		with cursor(psycopg2) as cur:
			args = ['id', 'username', 'hostname', 'message', 'args', 'timestamp', 'tags', 'context_id', 'event_name']
			cur.execute("SELECT %s, ev.name FROM entries e INNER JOIN events ev ON ev.id = e.event_id WHERE e.context_id = %%s" % ', '.join(['e.%s' % a for a in args[:-1]]), (context_id,))
			rows = cur.fetchall()
			res = [dict(zip(args, row)) for row in rows]
			for row in res:
				for k, v in row.items():
					if isinstance(v, datetime.datetime):
						row[k] = v.isoformat()
			return res

	def _postgresql_translate(event_name, locale):
		key = (event_name, locale)
		if key not in _postgresql_translate._cache:
			with cursor(psycopg2) as cur:
				cur.execute("SELECT et.message FROM event_message_translations et INNER JOIN events ev ON ev.id = et.event_id WHERE ev.name = %s AND et.locale = %s", (event_name, locale))
				translation = cur.fetchone()[0]
				_postgresql_translate._cache[key] = translation
		else:
			translation = _postgresql_translate._cache[key]
		return translation
	_postgresql_translate._cache = {}

	add = _postgresql_add
	query = _postgresql_query
	get = _postgresql_get
	translate = _postgresql_translate
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
	def _no_get():
		raise NotImplementedError()
	def _no_translate():
		raise NotImplementedError()

	add = _no_add
	query = _no_query
	get = _no_get
	translate = _no_translate
