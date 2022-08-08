#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  ad cache
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2014-2022 Univention GmbH
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
import base64


def _encode_base64(val):
	return base64.b64encode(val).decode('ASCII')


class EntryDiff(object):

	def __init__(self, old, new):
		self.old = old
		self.new = new
		if not old:
			old = {}
		if not new:
			new = {}
		self.set_old = set(old.keys())
		self.set_new = set(new.keys())
		self.intersect = self.set_new.intersection(self.set_old)

	def added(self):
		return self.set_new - self.intersect

	def removed(self):
		return self.set_old - self.intersect

	def changed(self):
		return set(o for o in self.intersect if set(self.old[o]) != set(self.new[o]))


class ADCache(object):

	"""
			Local cache for the current AD state of the adconnector.
			With this cache the connector has the possibility to create
			a diff between the new AD object and the old one from
			cache.
	"""

	def __init__(self, filename):
		self.filename = filename
		self._dbcon = sqlite3.connect(self.filename)
		self.adcache = {}

		self.__create_tables()

	def add_entry(self, guid, entry):
		if not self._guid_exists(guid):
			self._add_entry(guid, entry)
		else:
			self._update_entry(guid, entry)
		self.adcache[guid] = entry

	def diff_entry(self, old_entry, new_entry):
		result = {'added': None, 'removed': None, 'changed': None}

		diff = EntryDiff(old_entry, new_entry)

		result['added'] = diff.added()
		result['removed'] = diff.removed()
		result['changed'] = diff.changed()

		return result

	def get_entry(self, guid):
		entry = {}

		guid_id = self._get_guid_id(guid)

		if not guid_id:
			return None

		# The SQLite python module should do the escaping, that's
		# the reason why we use the tuple ? syntax.
		# I've chosen the str call because I want to make sure
		# that we use the same SQL value as before switching
		# to the tuple ? syntax
		sql_commands = [
			("SELECT ATTRIBUTES.attribute,data.value from data \
				inner join ATTRIBUTES ON data.attribute_id=attributes.id where guid_id = ?;", (str(guid_id),))
		]

		rows = self.__execute_sql_commands(sql_commands, fetch_result=True)

		if not rows:
			return None

		for line in rows:
			if not entry.get(line[0]):
				entry[str(line[0])] = []
			entry[line[0]].append(base64.b64decode(line[1]))

		return entry

	def remove_entry(self, guid):
		guid_id = self._get_guid_id(guid)

		if not guid_id:
			return None

		sql_commands = [
			("DELETE FROM data WHERE guid_id=?;", (str(guid_id),)),
			("DELETE FROM guids WHERE id=?;", (str(guid_id),))
		]

		self.__execute_sql_commands(sql_commands, fetch_result=False)

	def __execute_sql_commands(self, sql_commands, fetch_result=False):
		for i in [1, 2]:
			try:
				cur = self._dbcon.cursor()
				for sql_command in sql_commands:
					if isinstance(sql_command, tuple):
						ud.debug(ud.LDAP, ud.ALL, "ADCache: Execute SQL command: '%s', '%s'" % (sql_command[0], sql_command[1]))
						cur.execute(sql_command[0], sql_command[1])
					else:
						ud.debug(ud.LDAP, ud.ALL, "ADCache: Execute SQL command: '%s'" % sql_command)
						cur.execute(sql_command)
				self._dbcon.commit()
				if fetch_result:
					rows = cur.fetchall()
				cur.close()
				if fetch_result:
					ud.debug(ud.LDAP, ud.ALL, "ADCache: Return SQL result: '%s'" % rows)
					return rows
				return None
			except sqlite3.Error as exp:
				ud.debug(ud.LDAP, ud.WARN, "ADCache: sqlite: %s. SQL command was: %s" % (exp, sql_commands))
				if self._dbcon:
					self._dbcon.close()
				self._dbcon = sqlite3.connect(self.filename)

	def __create_tables(self):
		sql_commands = [
			"CREATE TABLE IF NOT EXISTS GUIDS (id INTEGER PRIMARY KEY, guid TEXT);",
			"CREATE TABLE IF NOT EXISTS ATTRIBUTES (id INTEGER PRIMARY KEY, attribute TEXT);",
			"CREATE TABLE IF NOT EXISTS DATA (id INTEGER PRIMARY KEY, guid_id INTEGER, attribute_id INTEGER, value TEXT);",
			"CREATE INDEX IF NOT EXISTS data_foreign_keys ON data(guid_id, attribute_id);",
			"CREATE INDEX IF NOT EXISTS attributes_attribute ON attributes(attribute);",
			"CREATE INDEX IF NOT EXISTS guids_guid ON guids(guid);",
		]

		self.__execute_sql_commands(sql_commands, fetch_result=False)

	def _guid_exists(self, guid):
		return self._get_guid_id(guid.strip()) is not None

	def _get_guid_id(self, guid):
		sql_commands = [
			("SELECT id FROM GUIDS WHERE guid=?;", (str(guid),))
		]

		rows = self.__execute_sql_commands(sql_commands, fetch_result=True)

		if rows:
			return rows[0][0]

		return None

	def _append_guid(self, guid):
		sql_commands = [
			("INSERT INTO GUIDS(guid) VALUES(?);", (str(guid),))
		]

		self.__execute_sql_commands(sql_commands, fetch_result=False)

	def _get_attr_id(self, attr):
		sql_commands = [
			("SELECT id FROM ATTRIBUTES WHERE attribute=?;", (str(attr),))
		]

		rows = self.__execute_sql_commands(sql_commands, fetch_result=True)

		if rows:
			return rows[0][0]

		return None

	def _attr_exists(self, guid):
		return self._get_attr_id(guid) is not None

	def _create_attr(self, attr):
		sql_commands = [
			("INSERT INTO ATTRIBUTES(attribute) VALUES(?);", (str(attr),))
		]

		self.__execute_sql_commands(sql_commands, fetch_result=False)

	def _get_attr_id_and_create_if_not_exists(self, attr):
		attr_id = self._get_attr_id(attr)
		if not attr_id:
			self._create_attr(attr)
			attr_id = self._get_attr_id(attr)

		return attr_id

	def _add_entry(self, guid, entry):
		guid = guid.strip()

		self._append_guid(guid)
		guid_id = self._get_guid_id(guid)

		sql_commands = []
		for attr in entry.keys():
			attr_id = self._get_attr_id_and_create_if_not_exists(attr)
			for value in entry[attr]:
				sql_commands.append(
					(
						"INSERT INTO DATA(guid_id,attribute_id,value) VALUES(?,?,?);", (str(guid_id), str(attr_id), _encode_base64(value))
					)
				)

		if sql_commands:
			self.__execute_sql_commands(sql_commands, fetch_result=False)

	def _update_entry(self, guid, entry):
		guid = guid.strip()
		guid_id = self._get_guid_id(guid)
		old_entry = self.get_entry(guid)
		diff = self.diff_entry(old_entry, entry)

		sql_commands = []
		for attribute in diff['removed']:
			sql_commands.append(
				(
					"DELETE FROM data WHERE data.id IN (\
				SELECT data.id FROM DATA INNER JOIN ATTRIBUTES ON data.attribute_id=attributes.id \
					where attributes.attribute=? and guid_id=? \
				);", (str(attribute), str(guid_id))
				)
			)
		for attribute in diff['added']:
			attr_id = self._get_attr_id_and_create_if_not_exists(attribute)
			for value in entry[attribute]:
				sql_commands.append(
					(
						"INSERT INTO DATA(guid_id,attribute_id,value) VALUES(?,?,?);", (str(guid_id), str(attr_id), _encode_base64(value))
					)
				)
		for attribute in diff['changed']:
			attr_id = self._get_attr_id_and_create_if_not_exists(attribute)
			for value in set(old_entry.get(attribute)) - set(entry.get(attribute)):
				sql_commands.append(
					(
						"DELETE FROM data WHERE data.id IN (\
							SELECT data.id FROM DATA INNER JOIN ATTRIBUTES ON data.attribute_id=attributes.id \
							where attributes.id=? and guid_id = ? and value = ? \
						);", (str(attr_id), str(guid_id), _encode_base64(value))
					)
				)
			for value in set(entry.get(attribute)) - set(old_entry.get(attribute)):
				sql_commands.append(
					(
						"INSERT INTO DATA(guid_id,attribute_id,value) VALUES(?,?,?);", (str(guid_id), str(attr_id), _encode_base64(value))
					)
				)

		if sql_commands:
			self.__execute_sql_commands(sql_commands, fetch_result=False)


if __name__ == '__main__':
	print('Starting ADcache test example ', end=' ')

	adcache = ADCache('cache.sqlite')

	guid = '1234'

	entry = {
		'attr1': [b'foobar'],
		'attr2': [b'val1', b'val2', b'val3']
	}

	adcache.add_entry(guid, entry)
	entry_old = adcache.get_entry(guid)
	diff_entry = adcache.diff_entry(entry_old, entry)
	if diff_entry.get('changed') or diff_entry.get('removed') or diff_entry.get('added'):
		raise Exception('Test 1 failed: %s' % diff_entry)
	print('.', end=' ')

	entry['attr3'] = [b'val2']
	entry['attr2'] = [b'val1', b'val3']

	diff_entry = adcache.diff_entry(entry_old, entry)
	if diff_entry.get('changed') != set(['attr2']) or diff_entry.get('removed') or diff_entry.get('added') != set(['attr3']):
		raise Exception('Test 2 failed: %s' % diff_entry)
	print('.', end=' ')

	adcache.add_entry(guid, entry)
	entry_old = adcache.get_entry(guid)
	diff_entry = adcache.diff_entry(entry_old, entry)
	if diff_entry.get('changed') or diff_entry.get('removed') or diff_entry.get('added'):
		raise Exception('Test 3 failed: %s' % diff_entry)
	print('.', end=' ')

	print(' done')
