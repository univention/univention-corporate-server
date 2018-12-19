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

import psycopg2

password = open('/etc/admin-diary.secret').read().strip()

@contextmanager
def connection():
	conn = psycopg2.connect(dbname='diary', user='diary', host='localhost', password=password)
	yield conn
	conn.commit()
	conn.close()


@contextmanager
def cursor():
	with connection() as conn:
		cur = conn.cursor()
		yield cur


def add(entry):
	with cursor() as cur:
		cur.execute("INSERT INTO log_entries (username, hostname, message, args, issued, tags, log_id, event_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (entry.username, entry.hostname, entry.message, entry.args, entry.issued, entry.tags, entry.log_id, entry.event_name))

def query():
	with connection() as conn:
		conn.execute("SELECT username, hostname, message, args, issued, tags, log_id, event_name FROM log_entries")
		rows = conn.fetchall()
		res = [dict(row) for row in rows]
		for row in res:
			for k, v in row.items():
				if isinstance(v, datetime.datetime):
					row[k] = v.isoformat()
		return res
