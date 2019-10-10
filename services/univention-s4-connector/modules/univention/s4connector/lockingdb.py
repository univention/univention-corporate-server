#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  LockingDB
#
# Copyright 2014-2019 Univention GmbH
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

from __future__ import print_function
import univention.debug2 as ud
import sqlite3
import inspect


def func_name():
	return inspect.currentframe().f_back.f_code.co_name


class LockingDB:

	"""
			A local database which includes the list of objects
			which are currently locked. That means the
			synchronisation of these objects has not been finished.
			https://forge.univention.org/bugzilla/show_bug.cgi?id=35391
	"""

	def __init__(self, filename):
		_d = ud.function('LockingDB.%s' % func_name())  # noqa: F841
		self.filename = filename
		self._dbcon = sqlite3.connect(self.filename)
		self.s4cache = {}

		self.__create_tables()

	def lock_ucs(self, uuid):
		_d = ud.function('LockingDB.%s' % func_name())  # noqa: F841

		if not uuid:
			return None

		# The SQLite python module should do the escaping, that's
		# the reason why we use the tuple ? syntax.
		# I've chosen the str call because I want to make sure
		# that we use the same SQL value as before switching
		# to the tuple ? syntax
		sql_commands = [
			("INSERT INTO UCS_LOCK(uuid) VALUES(?);", (str(uuid),))
		]

		self.__execute_sql_commands(sql_commands, fetch_result=False)

	def unlock_ucs(self, uuid):
		_d = ud.function('LockingDB.%s' % func_name())  # noqa: F841

		if not uuid:
			return None

		sql_commands = [
			("DELETE FROM UCS_LOCK WHERE uuid = ?;", (str(uuid),))
		]

		self.__execute_sql_commands(sql_commands, fetch_result=False)

	def lock_s4(self, guid):
		_d = ud.function('LockingDB.%s' % func_name())  # noqa: F841

		if not guid:
			return None

		sql_commands = [
			("INSERT INTO S4_LOCK(guid) VALUES(?);", (str(guid),))
		]

		self.__execute_sql_commands(sql_commands, fetch_result=False)

	def unlock_s4(self, guid):
		_d = ud.function('LockingDB.%s' % func_name())  # noqa: F841

		if not guid:
			return None

		sql_commands = [
			("DELETE FROM S4_LOCK WHERE guid = ?;", (str(guid),))
		]

		self.__execute_sql_commands(sql_commands, fetch_result=False)

	def is_ucs_locked(self, uuid):
		_d = ud.function('LockingDB.%s' % func_name())  # noqa: F841

		if not uuid:
			return False

		sql_commands = [
			("SELECT id FROM UCS_LOCK WHERE uuid=?;", (str(uuid),))
		]

		rows = self.__execute_sql_commands(sql_commands, fetch_result=True)

		if rows:
			return True

		return False

	def is_s4_locked(self, guid):
		_d = ud.function('LockingDB.%s' % func_name())  # noqa: F841

		if not guid:
			return False

		sql_commands = [
			("SELECT id FROM S4_LOCK WHERE guid=?;", (str(guid),))
		]

		rows = self.__execute_sql_commands(sql_commands, fetch_result=True)

		if rows:
			return True

		return False

	def __create_tables(self):
		_d = ud.function('LockingDB.%s' % func_name())  # noqa: F841

		sql_commands = [
			"CREATE TABLE IF NOT EXISTS S4_LOCK (id INTEGER PRIMARY KEY, guid TEXT);",
			"CREATE TABLE IF NOT EXISTS UCS_LOCK (id INTEGER PRIMARY KEY, uuid TEXT);",
			"CREATE INDEX IF NOT EXISTS s4_lock_guid ON s4_lock(guid);",
			"CREATE INDEX IF NOT EXISTS ucs_lock_uuid ON ucs_lock(uuid);",
		]

		self.__execute_sql_commands(sql_commands, fetch_result=False)

	def __execute_sql_commands(self, sql_commands, fetch_result=False):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				for sql_command in sql_commands:
					if isinstance(sql_command, tuple):
						ud.debug(ud.LDAP, ud.INFO, "LockingDB: Execute SQL command: '%s', '%s'" % (sql_command[0], sql_command[1]))
						cur.execute(sql_command[0], sql_command[1])
					else:
						ud.debug(ud.LDAP, ud.INFO, "LockingDB: Execute SQL command: '%s'" % sql_command)
						cur.execute(sql_command)
				self._dbcon.commit()
				if fetch_result:
					rows = cur.fetchall()
				cur.close()
				if fetch_result:
					ud.debug(ud.LDAP, ud.INFO, "LockingDB: Return SQL result: '%s'" % rows)
					return rows
				return None
			except sqlite3.Error as exp:
				ud.debug(ud.LDAP, ud.WARN, "LockingDB: sqlite: %s. SQL command was: %s" % (exp, sql_commands))
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = sqlite3.connect(self.filename)


if __name__ == '__main__':

	import random

	print('Starting LockingDB test example ')

	l = LockingDB('lock.sqlite')

	uuid1 = random.random()

	guid1 = random.random()

	if l.is_s4_locked(guid1):
		print('E: guid1 is locked for S4')
	if l.is_s4_locked(uuid1):
		print('E: uuid1 is locked for S4')
	if l.is_ucs_locked(guid1):
		print('E: guid1 is locked for UCS')
	if l.is_ucs_locked(uuid1):
		print('E: uuid1 is locked for UCS')

	l.lock_s4(guid1)

	if not l.is_s4_locked(guid1):
		print('E: guid1 is not locked for S4')
	if l.is_s4_locked(uuid1):
		print('E: uuid1 is locked for S4')
	if l.is_ucs_locked(guid1):
		print('E: guid1 is locked for UCS')
	if l.is_ucs_locked(uuid1):
		print('E: uuid1 is locked for UCS')

	l.unlock_s4(guid1)

	if l.is_s4_locked(guid1):
		print('E: guid1 is locked for S4')
	if l.is_s4_locked(uuid1):
		print('E: uuid1 is locked for S4')
	if l.is_ucs_locked(guid1):
		print('E: guid1 is locked for UCS')
	if l.is_ucs_locked(uuid1):
		print('E: uuid1 is locked for UCS')

	l.lock_ucs(uuid1)
	l.lock_ucs(uuid1)
	l.lock_ucs(uuid1)
	l.lock_ucs(uuid1)
	l.lock_ucs(uuid1)

	if l.is_s4_locked(guid1):
		print('E: guid1 is locked for S4')
	if l.is_s4_locked(uuid1):
		print('E: uuid1 is locked for S4')
	if l.is_ucs_locked(guid1):
		print('E: guid1 is locked for UCS')
	if not l.is_ucs_locked(uuid1):
		print('E: uuid1 is not locked for UCS')

	l.unlock_ucs(uuid1)

	if l.is_s4_locked(guid1):
		print('E: guid1 is locked for S4')
	if l.is_s4_locked(uuid1):
		print('E: uuid1 is locked for S4')
	if l.is_ucs_locked(guid1):
		print('E: guid1 is locked for UCS')
	if l.is_ucs_locked(uuid1):
		print('E: uuid1 is locked for UCS')

	print('done')
