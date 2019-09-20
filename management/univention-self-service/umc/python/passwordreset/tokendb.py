#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  self.logger: handle DB storage of tokens
#
# Copyright 2015-2019 Univention GmbH
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

import traceback
import datetime

import psycopg2
import psycopg2.extras

DB_USER = "selfservice"
DB_NAME = "selfservice"
DB_SECRETS_FILE = "/etc/self-service-db.secret"


class MultipleTokensInDB(Exception):
	pass


class TokenDB(object):

	def __init__(self, logger):
		self.logger = logger
		self.conn = self.open_db()

	def insert_token(self, username, method, token):
		sql = "INSERT INTO tokens (username, method, timestamp, token) VALUES (%(username)s, %(method)s, %(ts)s, %(token)s);"
		data = {"username": username, "method": method, "ts": datetime.datetime.now(), "token": token}
		cur = self.conn.cursor()
		cur.execute(sql, data)
		self.conn.commit()
		cur.close()

	def update_token(self, username, method, token):
		sql = "UPDATE tokens SET method=%(method)s, timestamp=%(ts)s, token=%(token)s WHERE username=%(username)s;"
		data = {"username": username, "method": method, "ts": datetime.datetime.now(), "token": token}
		cur = self.conn.cursor()
		cur.execute(sql, data)
		self.conn.commit()
		cur.close()

	def delete_tokens(self, **kwargs):
		sql = "DELETE FROM tokens WHERE "
		sql += " AND ".join(["{0}=%({0})s".format(key) for key in kwargs.keys()])
		cur = self.conn.cursor()
		cur.execute(sql, kwargs)
		self.conn.commit()
		cur.close()

	def get_all(self, **kwargs):
		sql = "SELECT * FROM tokens WHERE "
		sql += " AND ".join(["{0}=%({0})s".format(key) for key in kwargs.keys()])
		cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute(sql, kwargs)
		rows = cur.fetchall()
		cur.close()
		return rows

	def get_one(self, **kwargs):
		rows = self.get_all(**kwargs)
		if len(rows) == 1:
			return rows[0]
		elif len(rows) > 1:
			raise MultipleTokensInDB("Found {} rows in DB for kwargs '{}'.".format(len(rows), kwargs))
		else:
			return None

	def create_table(self):
		self.logger.info("db_create_table(): Creating table 'tokens' and constraints...")
		cur = self.conn.cursor()
		cur.execute("""CREATE TABLE tokens
(id SERIAL PRIMARY KEY NOT NULL,
username VARCHAR(255) NOT NULL,
method VARCHAR(255) NOT NULL,
timestamp TIMESTAMP NOT NULL,
token VARCHAR(255) NOT NULL);""")
		cur.execute("ALTER TABLE tokens ADD CONSTRAINT unique_id UNIQUE (id);")
		cur.execute("ALTER TABLE tokens ADD CONSTRAINT unique_username UNIQUE (username);")
		self.conn.commit()
		cur.close()

	def open_db(self):
		try:
			with open(DB_SECRETS_FILE) as pw_file:
				password = pw_file.readline().strip()
		except (OSError, IOError) as e:
			self.logger.error("db_open(): Could not read {}: {}".format(DB_SECRETS_FILE, e))
			raise
		try:
			conn = psycopg2.connect("dbname={db_name} user={db_user} host='localhost' password='{db_pw}'".format(
				db_name=DB_NAME, db_user=DB_USER, db_pw=password))
			self.logger.info("db_open(): Connected to database '{}' on server with version {} using protocol version {}.".format(
				DB_NAME, conn.server_version, conn.protocol_version))
			return conn
		except:
			self.logger.error("db_open(): Error connecting to database '{}': {}".format(DB_NAME, traceback.format_exc()))
			raise

	def close_db(self):
		self.conn.close()
		self.logger.info("close_database(): closed database connection.")

	def table_exists(self):
		cur = self.conn.cursor()
		cur.execute("SELECT * FROM pg_catalog.pg_tables WHERE tablename='tokens'")
		rows = cur.fetchall()
		cur.close()
		return len(rows) > 0
