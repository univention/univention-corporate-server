#!/usr/bin/python3
#
# Univention Management Console
#  self.logger: handle DB storage of tokens
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2015-2024 Univention GmbH
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

import datetime
import os
from functools import wraps

import psycopg2
import psycopg2.extras

from univention.management.console.config import ucr


DB_HOST = ucr.get("umc/self-service/postgresql/hostname", "localhost")
DB_PORT = ucr.get_int("umc/self-service/postgresql/port", 5432)
DB_USER = ucr.get("umc/self-service/postgresql/username", "selfservice")
DB_NAME = ucr.get("umc/self-service/postgresql/database", "selfservice")
DB_SECRETS_FILE = ucr.get("umc/self-service/postgresql/password-file", "/etc/self-service-db.secret")


class MultipleTokensInDB(Exception):
    pass


def auto_reopen_and_retry(func):
    """
    Close and reestablish connection to database only once in case an exception has been caught
    thrown by the wrapped method.
    """
    @wraps(func)
    def _decorator(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (psycopg2.InterfaceError, psycopg2.OperationalError, psycopg2.InternalError) as exc:
            self.logger.process("TokenDB: caught database error - reopening database and retrying transaction")
            self.logger.debug('TokenDB: database error was: %s', exc)
            # try to close database but ignore errors
            try:
                self.close_db()
            except psycopg2.Error:
                pass
            # reconnect and retry last action
            self.conn = self.open_db()
            return func(self, *args, **kwargs)
    return _decorator


class TokenDB:

    def __init__(self, logger):
        self.logger = logger
        self.conn = self.open_db()

    @auto_reopen_and_retry
    def insert_token(self, username, method, token):
        sql = "INSERT INTO tokens (username, method, timestamp, token) VALUES (%(username)s, %(method)s, %(ts)s, %(token)s);"
        data = {"username": username, "method": method, "ts": datetime.datetime.utcnow(), "token": token}
        cur = self.conn.cursor()
        cur.execute(sql, data)
        self.conn.commit()
        cur.close()

    @auto_reopen_and_retry
    def update_token(self, username, method, token):
        sql = "UPDATE tokens SET method=%(method)s, timestamp=%(ts)s, token=%(token)s WHERE username=%(username)s;"
        data = {"username": username, "method": method, "ts": datetime.datetime.utcnow(), "token": token}
        cur = self.conn.cursor()
        cur.execute(sql, data)
        self.conn.commit()
        cur.close()

    @auto_reopen_and_retry
    def delete_tokens(self, **kwargs):
        sql = "DELETE FROM tokens WHERE "
        sql += " AND ".join([f"{key}=%({key})s" for key in kwargs.keys()])
        cur = self.conn.cursor()
        cur.execute(sql, kwargs)
        self.conn.commit()
        cur.close()

    @auto_reopen_and_retry
    def get_all(self, **kwargs):
        sql = "SELECT * FROM tokens WHERE "
        sql += " AND ".join([f"{key}=%({key})s" for key in kwargs.keys()])
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(sql, kwargs)
        rows = cur.fetchall()
        cur.close()
        return rows

    @auto_reopen_and_retry
    def get_one(self, **kwargs):
        rows = self.get_all(**kwargs)
        if len(rows) == 1:
            return rows[0]
        elif len(rows) > 1:
            raise MultipleTokensInDB(f"Found {len(rows)} rows in DB for kwargs '{kwargs}'.")
        else:
            return None

    @auto_reopen_and_retry
    def create_table(self):
        self.logger.info("TokenDB: create_table(): Creating table 'tokens' and constraints...")
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
        password = os.getenv("SELF_SERVICE_DB_SECRET")
        if not password:
            try:
                with open(DB_SECRETS_FILE) as pw_file:
                    password = pw_file.readline().strip()
            except OSError as e:
                self.logger.error("TokenDB: open_db(): Could not read %s: %s", DB_SECRETS_FILE, e)
                raise
        try:
            self.logger.debug("TokenDB: open_db(): Connecting to database %r", DB_NAME)
            conn = psycopg2.connect(database=DB_NAME, user=DB_USER, password=password, host=DB_HOST, port=DB_PORT)
            self.logger.info("TokenDB: open_db(): Connected to database %r on server with version %r using protocol version %r", DB_NAME, conn.server_version, conn.protocol_version)
            return conn
        except Exception:
            self.logger.exception("TokenDB: open_db(): Error connecting to database %r:", DB_NAME)
            raise

    def close_db(self):
        self.conn.close()
        self.logger.info("TokenDB: close_db(): closed database connection.")

    @auto_reopen_and_retry
    def table_exists(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM pg_catalog.pg_tables WHERE tablename='tokens'")
        rows = cur.fetchall()
        cur.close()
        return len(rows) > 0
