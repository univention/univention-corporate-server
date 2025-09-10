#!/usr/bin/python3
#
# Univention S4 Connector
#  LockingDB
#
# SPDX-FileCopyrightText: 2014-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import sqlite3
from logging import getLogger


log = getLogger("LDAP").getChild(__name__)


class LockingDB:
    """
    A local database which includes the list of objects
    which are currently locked. That means the
    synchronisation of these objects has not been finished.
    https://forge.univention.org/bugzilla/show_bug.cgi?id=35391
    """

    def __init__(self, filename):
        self.filename = filename
        self._dbcon = sqlite3.connect(self.filename)
        self.s4cache = {}

        self.__create_tables()

    def lock_ucs(self, uuid):
        if not uuid:
            return

        # The SQLite Python module should do the escaping, that's
        # the reason why we use the tuple ? syntax.
        # I've chosen the str call because I want to make sure
        # that we use the same SQL value as before switching
        # to the tuple ? syntax
        sql_commands = [
            ("INSERT INTO UCS_LOCK(uuid) VALUES(?);", (str(uuid),)),
        ]

        self.__execute_sql_commands(sql_commands, fetch_result=False)

    def unlock_ucs(self, uuid):
        if not uuid:
            return

        sql_commands = [
            ("DELETE FROM UCS_LOCK WHERE uuid = ?;", (str(uuid),)),
        ]

        self.__execute_sql_commands(sql_commands, fetch_result=False)

    def lock_s4(self, guid):
        if not guid:
            return

        sql_commands = [
            ("INSERT INTO S4_LOCK(guid) VALUES(?);", (str(guid),)),
        ]

        self.__execute_sql_commands(sql_commands, fetch_result=False)

    def unlock_s4(self, guid):
        if not guid:
            return

        sql_commands = [
            ("DELETE FROM S4_LOCK WHERE guid = ?;", (str(guid),)),
        ]

        self.__execute_sql_commands(sql_commands, fetch_result=False)

    def is_ucs_locked(self, uuid):
        if not uuid:
            return False

        sql_commands = [
            ("SELECT id FROM UCS_LOCK WHERE uuid=?;", (str(uuid),)),
        ]

        rows = self.__execute_sql_commands(sql_commands, fetch_result=True)

        return bool(rows)

    def is_s4_locked(self, guid):
        if not guid:
            return False

        sql_commands = [
            ("SELECT id FROM S4_LOCK WHERE guid=?;", (str(guid),)),
        ]

        rows = self.__execute_sql_commands(sql_commands, fetch_result=True)

        return bool(rows)

    def __create_tables(self):
        sql_commands = [
            "CREATE TABLE IF NOT EXISTS S4_LOCK (id INTEGER PRIMARY KEY, guid TEXT);",
            "CREATE TABLE IF NOT EXISTS UCS_LOCK (id INTEGER PRIMARY KEY, uuid TEXT);",
            "CREATE INDEX IF NOT EXISTS s4_lock_guid ON s4_lock(guid);",
            "CREATE INDEX IF NOT EXISTS ucs_lock_uuid ON ucs_lock(uuid);",
        ]

        self.__execute_sql_commands(sql_commands, fetch_result=False)

    def __execute_sql_commands(self, sql_commands, fetch_result=False):
        for _i in [1, 2]:
            try:
                cur = self._dbcon.cursor()
                for sql_command in sql_commands:
                    if isinstance(sql_command, tuple):
                        log.trace(f"LockingDB: Execute SQL command: {sql_command[0]!r}, {sql_command[1]!r}")
                        cur.execute(sql_command[0], sql_command[1])
                    else:
                        log.trace(f"LockingDB: Execute SQL command: {sql_command!r}")
                        cur.execute(sql_command)
                self._dbcon.commit()
                if fetch_result:
                    rows = cur.fetchall()
                cur.close()
                if fetch_result:
                    log.trace(f"LockingDB: Return SQL result: {rows!r}")
                    return rows
                return None
            except sqlite3.Error as exp:
                log.warning(f"LockingDB: sqlite: {exp!r}. SQL command was: {sql_commands!r}")
                if self._dbcon:
                    self._dbcon.close()
                self._dbcon = sqlite3.connect(self.filename)


if __name__ == '__main__':
    import random

    print('Starting LockingDB test example ')

    lock = LockingDB('lock.sqlite')

    uuid1 = random.random()
    guid1 = random.random()

    if lock.is_s4_locked(guid1):
        print('E: guid1 is locked for S4')
    if lock.is_s4_locked(uuid1):
        print('E: uuid1 is locked for S4')
    if lock.is_ucs_locked(guid1):
        print('E: guid1 is locked for UCS')
    if lock.is_ucs_locked(uuid1):
        print('E: uuid1 is locked for UCS')

    lock.lock_s4(guid1)

    if not lock.is_s4_locked(guid1):
        print('E: guid1 is not locked for S4')
    if lock.is_s4_locked(uuid1):
        print('E: uuid1 is locked for S4')
    if lock.is_ucs_locked(guid1):
        print('E: guid1 is locked for UCS')
    if lock.is_ucs_locked(uuid1):
        print('E: uuid1 is locked for UCS')

    lock.unlock_s4(guid1)

    if lock.is_s4_locked(guid1):
        print('E: guid1 is locked for S4')
    if lock.is_s4_locked(uuid1):
        print('E: uuid1 is locked for S4')
    if lock.is_ucs_locked(guid1):
        print('E: guid1 is locked for UCS')
    if lock.is_ucs_locked(uuid1):
        print('E: uuid1 is locked for UCS')

    lock.lock_ucs(uuid1)
    lock.lock_ucs(uuid1)
    lock.lock_ucs(uuid1)
    lock.lock_ucs(uuid1)
    lock.lock_ucs(uuid1)

    if lock.is_s4_locked(guid1):
        print('E: guid1 is locked for S4')
    if lock.is_s4_locked(uuid1):
        print('E: uuid1 is locked for S4')
    if lock.is_ucs_locked(guid1):
        print('E: guid1 is locked for UCS')
    if not lock.is_ucs_locked(uuid1):
        print('E: uuid1 is not locked for UCS')

    lock.unlock_ucs(uuid1)

    if lock.is_s4_locked(guid1):
        print('E: guid1 is locked for S4')
    if lock.is_s4_locked(uuid1):
        print('E: uuid1 is locked for S4')
    if lock.is_ucs_locked(guid1):
        print('E: guid1 is locked for UCS')
    if lock.is_ucs_locked(uuid1):
        print('E: uuid1 is locked for UCS')

    print('done')
