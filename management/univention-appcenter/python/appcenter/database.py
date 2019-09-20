#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  Database integration
#
# Copyright 2016-2019 Univention GmbH
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
#

import os

import MySQLdb as mysql
from ipaddr import IPv4Network, AddressValueError

from univention.appcenter.utils import generate_password, call_process, call_process_as, container_mode
from univention.appcenter.packages import packages_are_installed, install_packages, update_packages, mark_packages_as_manually_installed, wait_for_dpkg_lock
from univention.appcenter.log import get_base_logger, LogCatcher
from univention.appcenter.ucr import ucr_get

database_logger = get_base_logger().getChild('database')


class DatabaseError(Exception):
	def exception_value(self):
		return str(self)


class DatabaseCreationFailed(DatabaseError):
	def __init__(self, msg, details=None):
		self.msg = msg
		self.details = details

	def __str__(self):
		return self.msg

	def exception_value(self):
		if self.details:
			return '%s: %s' % (self, self.details)
		else:
			return str(self)


class DatabaseConnectionFailed(DatabaseError):
	pass


class DatabaseInfoError(DatabaseError):
	pass


class DatabaseConnector(object):

	def __init__(self, app):
		self.app = app

	def _get_default_db_name(self):
		return self.app.id

	def get_db_port(self):
		return None

	def get_db_host(self):
		bip = ucr_get('docker/daemon/default/opts/bip', '172.17.42.1/16')
		try:
			docker0_net = IPv4Network(bip)
		except AddressValueError:
			raise DatabaseInfoError('Could not find DB host for %r' % bip)
		else:
			ip_address = docker0_net.ip
			return str(ip_address)

	def get_db_name(self):
		return self.app.database_name or self._get_default_db_name()

	def get_db_user(self):
		return self.app.database_user or self._get_default_db_name()

	def get_db_password(self):
		db_password_file = self.get_db_password_file()
		if not db_password_file:
			return None
		try:
			with open(db_password_file) as f:
				return f.read().rstrip('\n')
		except EnvironmentError:
			return None

	def get_db_password_file(self):
		if self.app.database_password_file:
			return self.app.database_password_file

	def get_autostart_variable(self):
		return None

	def _get_software_packages(self):
		return []

	def install(self):
		packages = self._get_software_packages()
		if packages:
			if packages_are_installed(packages, strict=False):
				mark_packages_as_manually_installed(packages)
			else:
				database_logger.info('Installing/upgrading %s' % ', '.join(packages))
				if wait_for_dpkg_lock():
					update_packages()
					if not install_packages(packages):
						raise DatabaseCreationFailed('Could not install software packages')
				else:
					raise DatabaseCreationFailed('Could not install software packages due to missing lock')

	@classmethod
	def get_connector(cls, app):
		value = app.database
		if value:
			if app.docker and container_mode():
				database_logger.warn('No database integration within container')
				return None
			if value.lower() == 'postgresql':
				database_logger.debug('%s uses PostgreSQL' % app)
				return PostgreSQL(app)
			elif value.lower() == 'mysql':
				database_logger.debug('%s uses MySQL' % app)
				return MySQL(app)
			else:
				raise DatabaseInfoError('%s wants %r as database. This is unsupported!' % (app, value))
		return None

	def _get_service_name(self):
		return self.__class__.__name__.lower()

	def start(self, attempts=2):
		service_name = self._get_service_name()
		if service_name:
			if call_process(['service', service_name, 'start'], database_logger).returncode:
				if attempts > 1:
					# try again. sometimes, under heavy load, mysql seems to fail to
					# start although it is just slow
					database_logger.info('Starting %s failed. Retrying...' % service_name)
					return self.start(attempts=attempts - 1)
				catcher = LogCatcher(database_logger)
				call_process(['service', service_name, 'status'], catcher)
				details = '\n'.join(catcher.stdstream())
				raise DatabaseCreationFailed('Could not start %s' % service_name, details=details)

	def _write_password(self, password):
		db_password_file = self.get_db_password_file()
		try:
			with open(db_password_file, 'wb') as f:
				os.chmod(f.name, 0o600)
				f.write(password)
		except EnvironmentError as exc:
			raise DatabaseCreationFailed(str(exc))
		else:
			database_logger.info('Password for %s database in %s' % (self.app.id, db_password_file))

	def _read_password(self):
		try:
			with open(self.get_db_password_file(), 'rb') as f:
				return f.read().rstrip('\n')
		except (EnvironmentError, TypeError):
			return None

	def db_exists(self):
		database_logger.info("DB Exists default implementation called...")
		return False

	def db_user_exists(self):
		return False

	def create_db_and_user(self, password):
		raise NotImplementedError()

	def setup(self):
		self.install()
		self.start()

	def create_database(self):
		self.setup()
		password = self._read_password()
		exists = False
		if password:
			database_logger.debug('Password already exists')
			if self.db_user_exists() and self.db_exists():
				database_logger.debug('Database and User already exist')
				exists = True
		if not exists:
			database_logger.info('Creating database for %s' % self.app)
			password = password or generate_password()
			self.create_db_and_user(password)
			self._write_password(password)
		else:
			database_logger.info('%s already has its database' % self.app)


class PostgreSQL(DatabaseConnector):

	def _get_software_packages(self):
		return ['univention-postgresql']

	def get_db_port(self):
		return 5432

	def get_db_password_file(self):
		if self.app.database_password_file:
			return self.app.database_password_file
		return '/etc/postgres-%s.secret' % self.app.id

	def get_autostart_variable(self):
		return 'postgres8/autostart'

	def execute(self, query):
		logger = LogCatcher()
		process = call_process_as('postgres', ['/usr/bin/psql', '-tc', query], logger=logger)
		if process.returncode:
			for level, msg in logger.logs:
				if level == 'OUT':
					database_logger.info(msg)
				elif level == 'ERR':
					database_logger.warn(msg)
			raise DatabaseError('Returncode %s for query' % process.returncode)
		return list(logger.stdout())

	def db_exists(self):
		database_logger.info('Checking if database %s exists (postgresql implementation)' % self.get_db_name())
		stdout = self.execute('SELECT COUNT(*) FROM pg_database WHERE datname = \'%s\'' % self.get_db_name())
		if stdout and stdout[0].strip() == '1':
			database_logger.info('Database %s already exists' % self.get_db_name())
			return True
		else:
			database_logger.info('Database %s does not exist' % self.get_db_name())
			return False

	def db_user_exists(self):
		stdout = self.execute('SELECT COUNT(*) FROM pg_user WHERE usename = \'%s\'' % self.get_db_user())
		if stdout and stdout[0].strip() == '1':
			return True

	def create_db_and_user(self, password):
		call_process_as('postgres', ['/usr/bin/createuser', '-DRS', '--login', self.get_db_user()], logger=database_logger)
		call_process_as('postgres', ['/usr/bin/createdb', '-O', self.get_db_user(), '-T', 'template0', '-E', 'UTF8', self.get_db_name()], logger=database_logger)
		self.execute('ALTER ROLE "%s" WITH ENCRYPTED PASSWORD \'%s\'' % (self.get_db_user(), password))


class MySQL(DatabaseConnector):

	def __init__(self, app):
		super(MySQL, self).__init__(app)
		self._connection = None
		self._cursor = None

	def _get_software_packages(self):
		return ['univention-mysql']

	def get_db_port(self):
		try:
			return int(ucr_get('mysql/config/mysqld/port'))
		except (TypeError, ValueError):
			return 3306

	def get_db_password_file(self):
		if self.app.database_password_file:
			return self.app.database_password_file
		return '/etc/mysql-%s.secret' % self.app.id

	def get_autostart_variable(self):
		return 'mysql/autostart'

	def get_root_connection(self):
		if self._connection is None:
			with open('/etc/mysql.secret') as f:
				passwd = f.read().rstrip('\n')
			try:
				self._connection = mysql.connect(host='localhost', user='root', passwd=passwd)
			except mysql.OperationalError:
				raise DatabaseConnectionFailed('Could not connect to the MySQL server. Please verify that MySQL is running. The password for MySQL\'s root user should be in /etc/mysql.secret. You can test the connection via\n  mysql --password="$(cat /etc/mysql.secret)"')
		return self._connection

	def get_cursor(self):
		if self._cursor is None:
			self._cursor = self.get_root_connection().cursor()
		return self._cursor

	def execute(self, query):
		try:
			cursor = self.get_cursor()
			cursor.execute(query)
		except mysql.Error as exc:
			raise DatabaseError(str(exc))
		else:
			return cursor

	def db_exists(self):
		database_logger.info('Checking if database %s exists (mysql implementation)' % self.get_db_name())
		cursor = self.execute("SELECT EXISTS (SELECT schema_name FROM information_schema.schemata WHERE schema_name = '%s')" % self.escape(self.get_db_name()))
		return cursor.fetchone()[0]

	def db_user_exists(self):
		cursor = self.execute("SELECT EXISTS (SELECT DISTINCT user FROM mysql.user WHERE user = '%s')" % self.escape(self.get_db_user()))
		return cursor.fetchone()[0]

	def escape(self, value):
		return self.get_root_connection().escape(unicode(value))

	def create_db_and_user(self, password):
		self.execute('CREATE DATABASE IF NOT EXISTS `%s`' % self.escape(self.get_db_name()))
		self.execute("GRANT ALL ON `%s`.* TO '%s'@'%%' IDENTIFIED BY '%s'" % (self.escape(self.get_db_name()), self.escape(self.get_db_user()), password))

	def __del__(self):
		if self._connection:
			self._connection.close()
