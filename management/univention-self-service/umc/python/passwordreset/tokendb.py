#!/usr/bin/python3
#
# Univention Management Console
#  self.logger: handle DB storage of tokens
#
# SPDX-FileCopyrightText: 2015-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import datetime
import os
from contextlib import contextmanager

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


class TokenDB:

    def __init__(self, logger):
        self.logger = logger.getChild(type(self).__name__)
        self.conn = self.open_db()

    @contextmanager
    def cursor(self, *args, **kwargs):
        try:
            cur = self.conn.cursor(*args, **kwargs)
            cur.execute('SELECT 1')
        except psycopg2.Error as exc:
            try:
                self.close_db()
            except psycopg2.Error:
                pass

            self.logger.warning('Connection to database lost: %s', exc)
            self.conn = self.open_db()
            cur = self.conn.cursor(*args, **kwargs)

        yield cur
        self.conn.commit()
        cur.close()

    def insert_token(self, username, method, token):
        sql = "INSERT INTO tokens (username, method, timestamp, token) VALUES (%(username)s, %(method)s, %(ts)s, %(token)s);"
        data = {"username": username, "method": method, "ts": datetime.datetime.utcnow(), "token": token}
        with self.cursor() as cur:
            cur.execute(sql, data)

    def update_token(self, username, method, token):
        sql = "UPDATE tokens SET method=%(method)s, timestamp=%(ts)s, token=%(token)s WHERE username=%(username)s;"
        data = {"username": username, "method": method, "ts": datetime.datetime.utcnow(), "token": token}
        with self.cursor() as cur:
            cur.execute(sql, data)

    def delete_tokens(self, **kwargs):
        sql = "DELETE FROM tokens WHERE "
        sql += " AND ".join([f"{key}=%({key})s" for key in kwargs.keys()])
        with self.cursor() as cur:
            cur.execute(sql, kwargs)

    def get_all(self, **kwargs):
        sql = "SELECT * FROM tokens WHERE "
        sql += " AND ".join([f"{key}=%({key})s" for key in kwargs.keys()])
        with self.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, kwargs)
            rows = cur.fetchall()
        return rows

    def get_one(self, **kwargs):
        rows = self.get_all(**kwargs)
        if len(rows) == 1:
            return rows[0]
        elif len(rows) > 1:
            raise MultipleTokensInDB(f"Found {len(rows)} rows in DB for kwargs '{kwargs}'.")
        else:
            return None

    def create_table(self):
        self.logger.info("db_create_table(): Creating table 'tokens' and constraints...")
        with self.cursor() as cur:
            cur.execute("""CREATE TABLE tokens
(id SERIAL PRIMARY KEY NOT NULL,
username VARCHAR(255) NOT NULL,
method VARCHAR(255) NOT NULL,
timestamp TIMESTAMP NOT NULL,
token VARCHAR(255) NOT NULL);""")
            cur.execute("ALTER TABLE tokens ADD CONSTRAINT unique_id UNIQUE (id);")
            cur.execute("ALTER TABLE tokens ADD CONSTRAINT unique_username UNIQUE (username);")

    def open_db(self):
        password = os.getenv("SELF_SERVICE_DB_SECRET")
        if not password:
            try:
                with open(DB_SECRETS_FILE) as pw_file:
                    password = pw_file.readline().strip()
            except OSError as e:
                self.logger.error("db_open(): Could not read %s: %s", DB_SECRETS_FILE, e)
                raise
        try:
            conn = psycopg2.connect(database=DB_NAME, user=DB_USER, password=password, host=DB_HOST, port=DB_PORT)
            self.logger.info("open_db(): Connected to database %r on server with version %r using protocol version %r.", DB_NAME, conn.server_version, conn.protocol_version)
            return conn
        except Exception:
            self.logger.exception("open_db(): Error connecting to database %r:", DB_NAME)
            raise

    def close_db(self):
        self.conn.close()
        self.logger.info("close_db(): closed database connection.")

    def table_exists(self):
        with self.cursor() as cur:
            cur.execute("SELECT * FROM pg_catalog.pg_tables WHERE tablename='tokens'")
            rows = cur.fetchall()
        return len(rows) > 0
