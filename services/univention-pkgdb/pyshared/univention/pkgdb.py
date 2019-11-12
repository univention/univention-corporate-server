#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
'''Univention Package Database
python module for the package database'''
from __future__ import print_function
#
# Copyright 2004-2019 Univention GmbH
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

import DNS
import apt_pkg
import csv
import optparse
import os
import os.path
import pgdb
import sys
import time
import univention.config_registry
import univention.uldap

assert pgdb.paramstyle == 'pyformat'

# TODO use FQDN or DN as system identifier instead of hostname?
# TODO add <limit> parameter to sql_get* functions
# TODO add <order> parameter to sql_get* functions to change/disable sort
# TODO: pkgdbu should not be able to create roles, instead do it as postgres from listener script as root


def parse_options():
	'''
	parse options and return <options> with
		<options.debug>
		<options.action>
		<options.system>
		<options.db_server>
		set
	'''
	parser = optparse.OptionParser(add_help_option=False)
	actions = optparse.OptionGroup(parser, 'Actions', 'Select an action, default is --scan')
	parser.add_option_group(actions)
	parser.usage = '%prog [options]\nScan all packages in the local system and send this data to the database pkgdb.'
	actions.add_option(
		"--scan",
		help='Scan this systems packages and sent them to the package database',
		action='append_const', dest='action', const='scan', default=[])
	actions.add_option(
		"--remove-system", metavar='SYSTEM',
		help='Removes SYSTEM from the package database',
		action='store', dest='removesystem')
	actions.add_option(
		"--test-superuser",
		help='Test for ability to add or delete database users',
		action='append_const', dest='action', const='test-superuser')
	actions.add_option(
		'--dump-all',
		help='Dump entire content of the database',
		action='append_const', dest='action', const='dump-all')
	actions.add_option(
		'--dump-systems',
		help='Dump systems-table of the database',
		action='append_const', dest='action', const='dump-systems')
	actions.add_option(
		'--dump-packages',
		help='Dump packages-table (query) of the database',
		action='append_const', dest='action', const='dump-packages')
	actions.add_option(
		'--dump-systems-packages',
		help='Dump systems-packages-table of the database',
		action='append_const', dest='action', const='dump-systems-packages')
	actions.add_option(
		'--fill-testdb',
		help="Scan all packages of the local system and add them to the database using system name 'testsystemX', using 0001 to 1500 for X. For testing purposes only.",
		action='append_const', dest='action', const='fill-testdb')
	actions.add_option(
		'--version',
		help='Print version information and exit',
		action='append_const', dest='action', const='version')
	actions.add_option(
		"--add-system", metavar='SYSTEM',
		help='Add a SYSTEM as db-user-account. Normally this will be used by univention-listener',
		action='store', dest='addsystem')
	actions.add_option(
		"--del-system", metavar='SYSTEM',
		help='Delete a SYSTEM as db-user-account. Normally this will be used by univention-listener',
		action='store', dest='delsystem')
	parser.add_option("-?", "-h", "--help", action='help', help='show this help message and exit')
	parser.add_option('--debug', help='Print more output', action='count', dest='debug', default=0)
	parser.add_option(
		'--db-server', metavar='SERVER',
		help='The database server',
		action='store', dest='db_server')
	(options, args, ) = parser.parse_args()
	if args:
		parser.error('Additional arguments not supported!')
	if options.addsystem is not None:
		options.action.append('add-system')
		options.system = options.addsystem
	del options.addsystem
	if options.delsystem is not None:
		options.action.append('del-system')
		options.system = options.delsystem
	del options.delsystem
	if options.removesystem is not None:
		options.action.append('remove-system')
		options.system = options.removesystem
	del options.removesystem
	if len(options.action) > 1:
		parser.error('Only one action at a time supported!')
	if not options.action:
		options.action.append('scan')
	options.action = options.action[0]
	return options


def log(message):
	'''Log-Funktion'''
	try:
		logfile = open("/var/log/univention/pkgdb.log", "a")  # TODO: persistent handle?
		logfile.write(time.strftime('%G-%m-%d %H:%M:%S') + ' ' + message + '\n')
		logfile.close()
	except EnvironmentError:
		# no log, no real problem
		pass


def build_sysversion(config_registry):
	sysversion = '%s-%s' % (config_registry['version/version'], config_registry['version/patchlevel'], )
	if config_registry.get('version/security-patchlevel'):
		sysversion = "%s-%s" % (sysversion, config_registry['version/security-patchlevel'], )
	if config_registry.get('version/erratalevel'):
		sysversion = "%s errata%s" % (sysversion, config_registry['version/erratalevel'], )
	return sysversion


def sql_check_privileges(cursor):
	'''DB-Privs testen (leerer Zugriff)'''
	log('check privileges ')
	try:
		cursor.execute('SELECT COUNT(*) FROM systems WHERE 1=0')
	except pgdb.Error:
		log('not OK')
		return 0
	log('OK')
	return 1


def get_dbservername(domainname):
	'''Datenbankserver ermitteln'''
	log('get dbservername for ' + domainname)
	DNS.DiscoverNameServers()
	dbsrvname = None
	try:
		dbsrvname = map(lambda x: x['data'], DNS.DnsRequest('_pkgdb._tcp.' + domainname, qtype='srv').req().answers)[0][3]
	except:
		log('Cannot find service-record of _pkgdb._tcp.')
		print('Cannot find service-record of _pkgdb._tcp.')
	return dbsrvname


def sql_test_superuser(cursor):
	'Prüfe auf Superuser'
	log('test for pkgdbu')
	if not sql_check_privileges(cursor):
		log('pkgdbu not OK')
		return 1
	log('pkgdbu OK')
	return 0


def sql_grant_system(connection, cursor, sysname):
	'''Datenbankbenutzer hinzufügen'''
	log('add (grant) user ' + sysname + ' to database')
	# manual "quoted identifier" (no pgdb support)
	sqlcmd = 'CREATE USER "%s" IN GROUP pkgdbg' % (sysname.replace('"', '""'), )
	print('SQL: %s\n' % (sqlcmd, ))
	try:
		cursor.execute(sqlcmd)
		connection.commit()
		log('create user OK')
	except pgdb.Error:
		connection.rollback()
		log('not OK. Try to alter ' + sysname)
		# manual "quoted identifier" (no pgdb support)
		sqlcmd = 'ALTER GROUP pkgdbg ADD USER "%s"' % (sysname.replace('"', '""'), )
		print('SQL: %s\n' % (sqlcmd, ))
		try:
			cursor.execute(sqlcmd)
			connection.commit()
			log('alter user OK')
		except pgdb.Error:
			connection.rollback()
			log('not OK. ignore it')
	return 0


def sql_revoke_system(connection, cursor, sysname):
	'''Datenbankbenutzer entfernen'''
	log('del (revoke) user ' + sysname + ' from database')
	# manual "quoted identifier" (no pgdb support)
	sql_command = 'DROP USER IF EXISTS "%s"' % (sysname.replace('"', '""'), )
	cursor.execute(sql_command)
	connection.commit()
	return 0


def sql_put_sys_in_systems(cursor, sysname, sysversion, sysrole, ldaphostdn, architecture):
	'''insert a system name into the system-table (or update its data)'''
	parameters = {
		'sysname': sysname,
		'sysversion': sysversion,
		'sysrole': sysrole,
		'ldaphostdn': ldaphostdn,
		'architecture': architecture,
	}
	cursor.execute('SELECT true FROM systems WHERE sysname = %(sysname)s', parameters)
	if cursor.rowcount == 0:
		sql_command = '''
		INSERT INTO systems (sysname,
                             sysversion,
                             sysrole,
                             ldaphostdn,
                             architecture,
                             scandate)
               VALUES(%(sysname)s,
                      %(sysversion)s,
                      %(sysrole)s,
                      %(ldaphostdn)s,
                      %(architecture)s,
                      CURRENT_TIMESTAMP)
		'''  # noqa: E101
	else:
		sql_command = '''
		UPDATE systems SET sysversion   = %(sysversion)s,
                           sysrole      = %(sysrole)s,
                           ldaphostdn   = %(ldaphostdn)s,
                           architecture = %(architecture)s,
                           scandate     = CURRENT_TIMESTAMP
                       WHERE sysname = %(sysname)s
		'''  # noqa: E101
	try:
		cursor.execute(sql_command, parameters)
	except pgdb.Error as error:
		log('DB-Error in sql_put_sys_on_systems: %r %r %r' % (error, sql_command, parameters, ))
		raise


def sql_put_sys_in_systems_no_architecture(cursor, sysname, sysversion, sysrole, ldaphostdn):
	'''insert a system name into the old system-table (or update its data)'''
	parameters = {
		'sysname': sysname,
		'sysversion': sysversion,
		'sysrole': sysrole,
		'ldaphostdn': ldaphostdn,
	}
	cursor.execute('SELECT true FROM systems WHERE sysname = %(sysname)s', parameters)
	if cursor.rowcount == 0:
		sql_command = '''
		INSERT INTO systems (sysname,
                             sysversion,
                             sysrole,
                             ldaphostdn,
                             scandate)
               VALUES(%(sysname)s,
                      %(sysversion)s,
                      %(sysrole)s,
                      %(ldaphostdn)s,
                      CURRENT_TIMESTAMP)
		'''  # noqa: E101
	else:
		sql_command = '''
		UPDATE systems SET sysversion   = %(sysversion)s,
                           sysrole      = %(sysrole)s,
                           ldaphostdn   = %(ldaphostdn)s,
                           scandate     = CURRENT_TIMESTAMP
                       WHERE sysname = %(sysname)s
		'''  # noqa: E101
	try:
		cursor.execute(sql_command, parameters)
	except pgdb.Error as error:
		log('DB-Error in sql_put_sys_on_systems: %r %r %r' % (error, sql_command, parameters, ))
		raise


def sql_select(cursor, sqlcmd):
	'''SQL Selects'''
	log('SQL: ' + sqlcmd)  # TODO: why?
	try:
		cursor.execute(sqlcmd)
		result = cursor.fetchall()
		return result
	except pgdb.Error:
		log('Cannot read from the database:' + sqlcmd)
		return []


def sql_getall_systems(cursor):
	sqlcmd = "SELECT sysname, sysversion, sysrole, to_char(scandate,'YYYY-MM-DD HH24:MI:SS'), ldaphostdn FROM systems ORDER BY sysname"
	return sql_select(cursor, sqlcmd)


def sql_getall_systemroles(cursor):
	query = "SELECT DISTINCT sysrole FROM systems ORDER BY sysrole"
	return sql_select(cursor, query)


def sql_getall_systemversions(cursor):
	sqlcmd = "SELECT DISTINCT sysversion FROM systems ORDER BY sysversion"
	return sql_select(cursor, sqlcmd)


def sql_getall_packages_in_systems(cursor):
	sqlcmd = "SELECT sysname, pkgname, vername, to_char(scandate,'YYYY-MM-DD HH24:MI:SS'), inststatus, selectedstate, inststate, currentstate FROM packages_on_systems ORDER BY sysname, pkgname, vername"
	return sql_select(cursor, sqlcmd)


def sql_get_systems_by_query(cursor, query):
	if not query:
		return []
	sqlcmd = "SELECT sysname, sysversion, sysrole, to_char(scandate,'YYYY-MM-DD HH24:MI:SS'), ldaphostdn FROM systems WHERE " + query + " ORDER BY sysname"  # FIXME
	return sql_select(cursor, sqlcmd)


def sql_get_packages_in_systems_by_query(cursor, query, join_systems, limit=None, orderby='sysname, pkgname, vername'):
	if not query:
		return []
	if join_systems:
		sqlcmd = "SELECT sysname, pkgname, vername, to_char(packages_on_systems.scandate, 'YYYY-MM-DD HH24:MI:SS'), inststatus, selectedstate, inststate, currentstate FROM packages_on_systems JOIN systems USING(sysname) WHERE " + query  # FIXME
	else:
		sqlcmd = "SELECT sysname, pkgname, vername, to_char(packages_on_systems.scandate, 'YYYY-MM-DD HH24:MI:SS'), inststatus, selectedstate, inststate, currentstate FROM packages_on_systems WHERE " + query  # FIXME

	if orderby:
		sqlcmd += " ORDER BY %s" % (orderby)

	if limit is not None:
		sqlcmd += " LIMIT %d" % (limit)
	return sql_select(cursor, sqlcmd)


def dump_systems(cursor):
	'''writes CSV with all systems and their system-specific information to stdout'''
	cursor.execute("SET datestyle = 'ISO'")
	query = '''
	SELECT sysname, sysversion, sysrole, scandate, ldaphostdn
           FROM systems
           ORDER BY sysname
	'''  # noqa: E101
	cursor.execute(query)
	writer = csv.writer(sys.stdout, delimiter=' ')
	writer.writerow(('hostname', 'UCS version', 'server role', 'last scan', 'LDAP host DN', ))
	for row in cursor:
		writer.writerow(row)
	return 0


def dump_packages(cursor):
	# TODO: What use is this functionality?
	query = "SELECT DISTINCT ON (pkgname, vername) pkgname, vername, inststatus FROM packages_on_systems ORDER BY pkgname, vername, inststatus"
	cursor.execute(query)
	writer = csv.writer(sys.stdout, delimiter=' ')
	writer.writerow(('package', 'version', 'installed', ))
	for row in cursor:
		writer.writerow(row)
	return 0


def dump_systems_packages(cursor):
	cursor.execute("SET datestyle = 'ISO'")
	query = '''
	SELECT sysname, pkgname, vername, scandate, inststatus, selectedstate, inststate, currentstate
           FROM packages_on_systems
           ORDER BY sysname, pkgname, vername
	'''  # noqa: E101
	cursor.execute(query)
	writer = csv.writer(sys.stdout, delimiter=' ')
	writer.writerow(('system', 'package', 'version', 'last scan', 'installed', 'selected state', 'installation state', 'current state'))
	for row in cursor:
		writer.writerow(row)
	return 0


def action_remove_system(connection, cursor, sysname):
	'''removes system <sysname> from the database'''
	connection.rollback()
	delete_packages = '''
	DELETE FROM packages_on_systems
           WHERE sysname = %(sysname)s
	'''  # noqa: E101
	delete_system = '''
	DELETE FROM systems
           WHERE sysname = %(sysname)s
	'''  # noqa: E101
	cursor.execute(delete_packages, {'sysname': sysname, })
	cursor.execute(delete_system, {'sysname': sysname, })
	connection.commit()


def scan_and_store_packages(cursor, sysname, fake_null=False, architecture=None):
	'''updates the system <sysname> with the current package state
	if <fake_null> is True put '' instead of None in the vername field'''
	delete_packages = '''
	DELETE FROM packages_on_systems
           WHERE sysname = %(sysname)s
	'''  # noqa: E101
	insert_statement = '''
	INSERT INTO packages_on_systems (scandate,
                                     sysname,
                                     currentstate,
                                     inststate,
                                     inststatus,
                                     pkgname,
                                     selectedstate,
                                     vername)
           VALUES
	'''  # noqa: E101
	insert_value = '''(
	CURRENT_TIMESTAMP,
	%(sysname)s,
	%(currentstate)s,
	%(inststate)s,
	%(inststatus)s,
	%(pkgname)s,
	%(selectedstate)s,
	%(vername)s)
	'''
	if scan_and_store_packages.cache is None:
		apt_pkg.init()
		scan_and_store_packages.cache = apt_pkg.Cache()
	cursor.execute(delete_packages, {'sysname': sysname, })
	insert_values = []
	for package in scan_and_store_packages.cache.packages:
		if not package.has_versions:
			continue
		if architecture is not None and architecture != package.architecture:
			continue
		parameters = {
			'sysname': sysname,
			'currentstate': package.current_state,
			'inststate': package.inst_state,
			'inststatus': 'n',
			'pkgname': package.name,
			'selectedstate': package.selected_state,
			'vername': None,
		}
		if fake_null:
			parameters['vername'] = ''
		if package.current_ver:
			parameters['inststatus'] = 'i'
			parameters['vername'] = package.current_ver.ver_str
		insert_values.append(cursor._quoteparams(insert_value, parameters))
	if insert_values:
		insert_statement += ','.join(insert_values)
		cursor.execute(insert_statement)


scan_and_store_packages.cache = None


def action_fill_testdb(connection, cursor, config_registry):
	'''Fülle Testdatenbank'''
	connection.rollback()
	sysversion = build_sysversion(config_registry)
	sysrole = config_registry['server/role']
	ldaphostdn = config_registry['ldap/hostdn']
	apt_pkg.init()
	architecture = apt_pkg.config.find("APT::Architecture")
	log('start fill of testdb ')
	for sysname in ['testsystem%04d' % (i, ) for i in range(1, 1500)]:
		try:
			sql_put_sys_in_systems(cursor, sysname, sysversion, sysrole, ldaphostdn, architecture)
			fake_null = False
		except pgdb.DatabaseError:
			# assume we are connected to a univention-pkgdb < 6.0.7-1 (old schema)
			connection.rollback()
			# retry for old schema
			sql_put_sys_in_systems_no_architecture(cursor, sysname, sysversion, sysrole, ldaphostdn)
			fake_null = True  # old schema has NOT NULL, thus we have to use '' instead of None
		scan_and_store_packages(cursor, sysname, fake_null, architecture)
		connection.commit()
	log('end of fill testdb')
	return 0


def action_scan(connection, cursor, config_registry):
	'''put systems <sysname> in the database and updates it with the current package state'''
	connection.rollback()
	sysname = config_registry['hostname']
	sysversion = build_sysversion(config_registry)
	sysrole = config_registry['server/role']
	ldaphostdn = config_registry['ldap/hostdn']
	apt_pkg.init()
	architecture = apt_pkg.config.find("APT::Architecture")
	log('Starting scan of system %r' % (sysname, ))
	try:
		sql_put_sys_in_systems(cursor, sysname, sysversion, sysrole, ldaphostdn, architecture)
		fake_null = False
	except pgdb.DatabaseError:
		# assume we are connected to a univention-pkgdb < 6.0.7-1 (old schema)
		connection.rollback()
		# retry for old schema
		sql_put_sys_in_systems_no_architecture(cursor, sysname, sysversion, sysrole, ldaphostdn)
		fake_null = True  # old schema has NOT NULL, thus we have to use '' instead of None
	scan_and_store_packages(cursor, sysname, fake_null, architecture)
	connection.commit()
	log('end of scan for system %r' % (sysname, ))
	return 0


PRIVILEGED_OPERATIONS = frozenset(('add-system', 'del-system', 'fill-testdb', 'test-superuser',))


def open_database_connection(config_registry, pkgdbu=False, db_server=None):
	connection_info = {  # see <http://www.postgresql.org/docs/8.4/static/libpq-connect.html>
		'dbname': 'pkgdb',
	}
	if config_registry.is_true('pkgdb/requiressl'):
		connection_info['sslmode'] = 'require'
	if pkgdbu:
		# 'host' not specified -> localhost over Unix-domain socket (connection type "local")
		connection_info['user'] = 'pkgdbu'
		password_file = '/etc/postgresql/pkgdb.secret'
	else:
		if db_server is None:
			db_server = get_dbservername(config_registry['domainname'])
			if db_server is None:
				return None
		connection_info['host'] = db_server
		connection_info['user'] = config_registry.get('pkgdb/user', '%s$' % (config_registry['hostname'], ))
		password_file = config_registry.get('pkgdb/pwdfile', '/etc/machine.secret')
	connection_info['password'] = open(password_file, 'rb').read().rstrip('\n')
	connectstring = ' '.join([
		"%s='%s'" % (key, value.replace('\\', '\\\\').replace("'", "\\'"),)
		for (key, value, )
		in connection_info.items()
	])
	connection = pgdb.connect(database=connectstring)
	return connection


def main():
	'''main function for univention-pkgdb-scan'''
	options = parse_options()
	if options.action == 'version':
		print('%s %s' % (os.path.basename(sys.argv[0]), '@%@package_version@%@', ))
		return 0

	config_registry = univention.config_registry.ConfigRegistry()
	config_registry.load()

	# Datenbankzugriffsmethode ermitteln
	if options.action in PRIVILEGED_OPERATIONS:
		connection = open_database_connection(config_registry, pkgdbu=True)
	else:
		connection = open_database_connection(config_registry, pkgdbu=False)
		if connection is None:
			print('No DB-Server-Name found.')
			return 1
	cursor = connection.cursor()

	if options.action == 'test-superuser':
		return sql_test_superuser(cursor)
	elif options.action == 'dump-systems':
		return dump_systems(cursor)
	elif options.action == 'dump-packages':
		return dump_packages(cursor)
	elif options.action == 'dump-systems-packages':
		return dump_systems_packages(cursor)
	elif options.action == 'dump-all':
		return dump_systems(cursor) or \
			dump_packages(cursor) or \
			dump_systems_packages(cursor)
	elif not sql_check_privileges(cursor):
		print('PKGDB: no privileges to access the database')
		print('You must first add this system with --add-system on the db-server (or join the system)')
		print('This should be done automatically by the cronjob univention-pkgdb-check')
		return 1
	elif options.action == 'add-system':
		# Systembenutzer zur Datenbank hinzufügen
		return sql_grant_system(connection, cursor, options.system)
	elif options.action == 'del-system':
		# Systembenutzer aus Datenbank entfernen
		return sql_revoke_system(connection, cursor, options.system)
	elif options.action == 'fill-testdb':
		return action_fill_testdb(connection, cursor, config_registry)
	elif options.action == 'remove-system':
		return action_remove_system(connection, cursor, options.system)
	elif not config_registry.is_true('pkgdb/scan'):
		log('univention-config-registry pkgdb/scan is not true')
		print('The Univention Configuration Registry variable pkgdb/scan is not true.')
		return 0
	elif options.action == 'scan':
		return action_scan(connection, cursor, config_registry)
