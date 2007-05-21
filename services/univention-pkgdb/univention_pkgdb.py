#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-
#
# Univention Package Database
#  python module for the package database
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import sys, os, string, getopt, DNS, time, tempfile, os.path
import apt_pkg
import pgdb, commands
import univention_baseconfig

def usage():
	print 'univention-pkgdb-scan: Scan all packages in the lokal system and send this data to the database pkgdb.'
	print 'Copyright (c) 2005, 2006 Univention GmbH, Germany'
	print ''
	print 'Syntax:'
	print '  univention-pkg-scan [options]'
	print ''
	print 'options:'
	print '  -h | --help | -?'
	print '    Print this usage message and exit'
	print ''
	print '  --test-superuser'
	print '    Test for ability to add or del database users'
	print ''
	print '  --add-system=<name>'
	print '    Add a system as db-user-account.'
	print '    Normaly this will be used by univention-listener'
	print ''
	print '  --del-system=<name>'
	print '    Del a system as db-user-account.'
	print '    Normaly this will be used by univention-listener'
	print ''
	print '  --db-server=<name>'
	print '    The database server'
	print ''
	print '  --dump-all'
	print '    Dump entire content of the database'
	print ''
	print '  --dump-systems'
	print '    Dump systems-table of the database'
	print ''
	print '  --dump-packages'
	print '    Dump packages-table (query) of the database'
	print ''
	print '  --dump-systems-packages'
	print '    Dump systems-packages-table of the database'
	print ''
	print '  --fill-testdb'
	print '    Scan all packages of the local system and add them to the database'
	print '    using systemname \'testsystemX\', using 0001 to 1500 for X. For '
	print '    testing purposes only.'
	print ''
	print '  --debug'
	print '    Print more output'
	print ''
	print '  --clean'
	print '    Removes expired data from the database'
	print ''
	print '  --version'
	print '    Print version information and exit'
	print ''
	print 'Description:'
	print '  Scans all packages in the lokal system and sends this data to the database pkgdb.'
	print '  If any options are given, no scan is run.'
	print ''
	print 'Known-Bugs:'
	print '  -None-'
	print ''
	sys.exit(1)

# ------------------------------------------------------------------------------
# check if psql is in PATH
# ------------------------------------------------------------------------------
def has_psql_client():
	for dir in os.environ["PATH"].split(os.pathsep):
		if os.path.exists("%s/psql"%dir):
			return True
	return False

# ------------------------------------------------------------------------------
# Log-Funktion
# ------------------------------------------------------------------------------
def log( message ):
	try:
		fd=open( "/var/log/univention/pkgdb.log", "a" )
		fd.write( time.strftime('%G-%m-%d %H:%M:%S') + ' ' +  message + '\n')
		fd.close()
	except:
		# no log, no real problem
		pass

# ------------------------------------------------------------------------------
# translate sysrole names
# ------------------------------------------------------------------------------
def translate_sysrolename_from_baseconfig( old ):
	if not old:
		return 'basesystem'

	if old=='fatclient':
		return 'managedclient'

	return old

# ------------------------------------------------------------------------------
# DB-Privs testen (leerer Zugriff)
# ------------------------------------------------------------------------------
def sql_check_privileges( pkgdbcur ):

	log( 'check privileges ' )
	try:
		pkgdbcur.execute( 'select count(*) from systems where 1=0')
	except:
		log( 'not OK' )
		return 0
	log( 'OK' )
	return 1

# ------------------------------------------------------------------------------
# Datenbankserver ermitteln
# ------------------------------------------------------------------------------
def sql_get_dbservername( domainname ):
	log( 'get dbservername for ' + domainname )
	DNS.DiscoverNameServers()
	try:
		dbsrvname=map(lambda(x): x['data'], DNS.DnsRequest('_pkgdb._tcp.'+domainname, qtype='srv').req().answers)[0][3]
	except:
		log( 'Cannot find service-record of _pkgdb._tcp.' )
		print 'Cannot find service-record of _pkgdb._tcp.'
		dbsrvname = ''

	return dbsrvname

# ------------------------------------------------------------------------------
# Prüfe auf Superuser
# ------------------------------------------------------------------------------
def sql_test_superuser():
	log( 'test for pkgdbu' )
	try:
		# gibt es lokal das passwort von pkgdbu, dann nutze dieses
		pgdbpwfile = open('/etc/postgresql/pkgdb.secret','r')
		pgdbpw = pgdbpwfile.readline()[:-1]
		pgdbpwfile.close()
		pkgdb_connect_string = ':pkgdb:pkgdbu:'+pgdbpw
		if len(pkgdb_connect_string)==0:
			raise "no connectstring"
		dbhdl = pgdb.connect(pkgdb_connect_string)
		dbcur = dbhdl.cursor()
		if not sql_check_privileges( dbcur ):
			raise "no privileges"

		log( 'pkgdbu OK' )
		retcode = 0
	except:
		log( 'pkgdbu not OK' )
		retcode = 1

	return retcode

# ------------------------------------------------------------------------------
# DB-Connectstring für entfernte Datenbank ermitteln
# ------------------------------------------------------------------------------
def sql_create_connectstring( dbsrvname, sysname, pwdfile='/etc/machine.secret'  ):
	log( 'create connectstring for ' + sysname + ' on ' + dbsrvname )
	try:
		# versuche den machine-account zu nutzen
		pgdbpwfile = open(pwdfile,'r')
		pgdbpw = pgdbpwfile.readline()[:-1]
		pgdbpwfile.close()
		# 'host:database:user:password:opt:tty'
		pkgdb_connect_string = dbsrvname+':pkgdb:'+sysname+':'+pgdbpw
	except:
		log( 'Cannot read a db password file.' )
		print 'Cannot read a db password file.'
		pkgdb_connect_string = ''

	return pkgdb_connect_string

# ------------------------------------------------------------------------------
# DB-Connectstring für lokale Datenbank ermitteln
# ------------------------------------------------------------------------------
def sql_create_localconnectstring( sysname  ):
	log( 'create local connectstring for ' + sysname )
	try:
		# gibt es lokal das passwort von pkgdbu, dann nutze dieses
		pgdbpwfile = open('/etc/postgresql/pkgdb.secret','r')
		pgdbpw = pgdbpwfile.readline()[:-1]
		pgdbpwfile.close()
		# 'host:database:user:password:opt:tty'
		pkgdb_connect_string = ':pkgdb:pkgdbu:'+pgdbpw
	except:
		log( 'Cannot read a db password file.' )
		print 'Cannot read a db password file.'
		pkgdb_connect_string = ''

	return pkgdb_connect_string

# ------------------------------------------------------------------------------
# DB-Connectstring (allgemein) ermitteln
# ------------------------------------------------------------------------------
#def sql_create_psql_connectstring():
#
#	# ------------------------------------------------------------------------------
#	# Baseconfig auslesen
#	# ------------------------------------------------------------------------------
#	baseConfig=univention_baseconfig.baseConfig()
#	baseConfig.load()
#
#	# ------------------------------------------------------------------------------
#	# Datenbankserver ermitteln
#	# ------------------------------------------------------------------------------
#	dbsrvname = sql_get_dbservername( baseConfig['domainname'] )
#	if len(dbsrvname)==0:
#		print 'No DB-Server-Name found.'
#		sys.exit(1)
#
#	try:
#		# gibt es lokal das passwort von pkgdbu, dann nutze dieses
#		pgdbpwfile = open('/etc/postgresql/pkgdb.secret','r')
#		pgdbpw = pgdbpwfile.readline()[:-1]
#		pgdbpwfile.close()
#		pkgdb_connect_string = '-d pkgdb -U pkgdbu'
#		# pgdbpw
#	except:
#		try:
#			# versuche den machine-account zu nutzen
#			pgdbpwfile = open('/etc/machine.secret','r')
#			pgdbpw = pgdbpwfile.readline()[:-1]
#			pgdbpwfile.close()
#			pkgdb_connect_string = '-h '+dbsrvname+' -d pkgdb -U '+baseConfig['hostname']
#			# pgdbpw
#		except:
#			print 'Cannot read a db password file.'
#			sys.exit(1)
#
#	return (pkgdb_connect_string,pgdbpw)

# ------------------------------------------------------------------------------
# Befehl in der psql-Shell ausfuehren
# ------------------------------------------------------------------------------
def execute_psql_command(connect_string, cmd):

        # the connect string looks like this:
        # <fqdn of db-server>:<db-name>:<username>:<password>

        parts = connect_string.split(":")

        pw = ""
        host = ""
        user = ""

        try:
                host = parts[0]
                user = parts[2]
                pw = parts[3]
        except:
                log("Error parsing connect string in execute_psql_command")
                print("Error parsing connect string in execute_psql_command")
                sys.exit(1)

	# export pg-password (there seems to be no other way of passing it to pg)

	os.environ["PGPASSWORD"] = pw
	ret = ""
	try:
		foox = """psql -d "pkgdb" -c "%s" -q -h %s -U %s """%(cmd, host, user)
		ret = commands.getstatusoutput(foox)
	finally:
		# always unset password in environment
		os.environ["PGPASSWORD"] = ""
		return ret

# ------------------------------------------------------------------------------
# Datenbankbenutzer hinzufügen
# ------------------------------------------------------------------------------
def sql_grant_system( db_connect_string, sysname ):
	log( 'add (grant) user ' + sysname + ' to database' )
	try:
		dbhdl = pgdb.connect(db_connect_string)
		dbcur = dbhdl.cursor()
		if not sql_check_privileges( dbcur ):
			raise "No Privilege"
	except:
		log( 'Cannot connect to database' )
		print 'Cannot connect to database'
		sys.exit(1)

	sqlcmd = 'create user \"'+sysname+'\" in group pkgdbg'
	print 'SQL: %s\n' %(sqlcmd)
	try:
		dbcur.execute( sqlcmd )
		dbhdl.commit()
		log( 'create user OK' )
	except:
		dbhdl.rollback()
		log( 'not OK. Try to alter ' + sysname  )
		sqlcmd = 'alter group pkgdbg add user \"'+sysname+'\"'
		print 'SQL: %s\n' %(sqlcmd)
		try:
			dbcur.execute( sqlcmd )
			dbhdl.commit()
			log( 'alter user OK' )
		except:
			dbhdl.rollback()
			log( 'not OK. ignore it' )
			pass
	dbcur.close()
	dbhdl.close()
	return

# ------------------------------------------------------------------------------
# Datenbankbenutzer entfernen
# ------------------------------------------------------------------------------
def sql_revoke_system( db_connect_string, sysname ):
	log( 'del (revoke) user ' + sysname + ' from database' )
	try:
		dbhdl = pgdb.connect(db_connect_string)
		dbcur = dbhdl.cursor()
		if not sql_check_privileges( dbcur ):
			raise "No Privilege"
	except:
		print 'Cannot connect to database'
		sys.exit(1)

	sqlcmd = 'drop user \"'+sysname+'\"'
	print 'SQL: %s\n' %(sqlcmd)
	try:
		dbcur.execute( sqlcmd )
		dbhdl.commit()
	except:
		dbhdl.rollback()
		pass
	dbcur.close()
	dbhdl.close()
	return

# ------------------------------------------------------------------------------
# Datenbank aufraeumen (sollte regelmaessig erfolgen)
# ------------------------------------------------------------------------------
def sql_vacuum_analyse( db_connect_string ):
	sqlcmd = 'vacuum analyse'
	log( 'SQL: ' + sqlcmd )
	try:
		dbhdl = pgdb.connect(db_connect_string)
		dbcur = dbhdl.cursor()
		if not sql_check_privileges( dbcur ):
			raise "No Privilege"
	except:
		print 'Cannot connect to database'
		sys.exit(1)

	try:
		dbcur.execute( 'commit;'+sqlcmd+';begin' )
		dbhdl.commit()
	except Exception, e:
		log("Exception during sql_vacuum_analyse: %s"%str(e))

	dbcur.close()
	dbhdl.close()
	return


# ------------------------------------------------------------------------------
# insert a system name into the system-table (or update its data)
# ------------------------------------------------------------------------------
def sql_put_sys_in_systems( pkgdbhdl, pkgdbcur, sysname, sysversion, sysrole, ldaphostdn ):
	pkgdbcur.execute( 'select count(*) from systems where sysname=\''+sysname+'\'')
	if pkgdbcur.rowcount > 0:
		count = pkgdbcur.fetchone()[0]

		if count == 0:
			sqlcmd = 'insert into systems(sysname,sysversion,sysrole,ldaphostdn,scandate) values(\''+sysname+'\',\''+sysversion+'\',\''+sysrole+'\',\''+ldaphostdn+'\',current_timestamp)'
		else:
			sqlcmd = 'update systems set sysversion=\''+sysversion+'\',sysrole=\''+sysrole+'\',ldaphostdn=\''+ldaphostdn+'\',scandate=current_timestamp where sysname=\''+sysname+'\''
		try:
			pkgdbcur.execute( sqlcmd )
			pkgdbhdl.commit()
		except:
			log( 'DB-Error by sql_put_sys_on_systems:'+sqlcmd )
			pass
	else:
		print 'Fehler in put_sysname_in_systems'

# ------------------------------------------------------------------------------
# remove all package data for a given system
# ------------------------------------------------------------------------------
def sql_remove_all_packages_on_systems(pkgdbhdl, pkgdbcur, sysname):
	sqlcmd = 'delete from packages_on_systems where sysname=\'%s\''%sysname
	pkgdbcur.execute(sqlcmd)
	pkgdbhdl.commit()

def sql_put_inserted_packages_on_systems( pkgdbhdl, pkgdbcur, sysname, pkgname, vername, selectedstate, inststate, currentstate ):
	sqlcmd = 'insert into packages_on_systems(sysname,pkgname,vername,scandate,inststatus,selectedstate,inststate,currentstate) values(\''+sysname+'\',\''+pkgname+'\',\''+vername+'\',current_timestamp,\'i\',\''+str(selectedstate)+'\',\''+str(inststate)+'\',\''+str(currentstate)+'\')'
	try:
		pkgdbcur.execute( sqlcmd )
		pkgdbhdl.commit()
	except:
		log( 'DB-Error by sql_put_inserted_packages_on_systems:'+sqlcmd )

def sql_put_removed_packages_on_systems( pkgdbhdl, pkgdbcur, sysname, pkgname, selectedstate, inststate, currentstate ):
	sqlcmd = 'insert into packages_on_systems(sysname,pkgname,vername,scandate,inststatus,selectedstate,inststate,currentstate) values(\''+sysname+'\',\''+pkgname+'\',\'\',current_timestamp,\'n\',\''+str(selectedstate)+'\',\''+str(inststate)+'\',\''+str(currentstate)+'\')'
	try:
		pkgdbcur.execute( sqlcmd )
		pkgdbhdl.commit()
	except:
		log( 'DB-Error by sql_put_removed_packages_on_systems:'+sqlcmd )

#def sql_del_old_packages_on_systems( pkgdbhdl, pkgdbcur, sysname, timestamp ):
#	sqlcmd = 'delete from packages_on_systems where sysname=\''+sysname+'\' and scandate<\''+timestamp+'\''
#	log( 'SQL: ' + sqlcmd )
#	try:
#		pkgdbcur.execute( sqlcmd )
#		pkgdbhdl.commit()
#	except:
#		log( 'DB-Error by sql_del_old_packages_on_systems:'+sqlcmd )
#		pass

def sql_del_unrefered_packages_on_systems( pkgdbhdl, pkgdbcur ):
	sqlcmd = 'delete from packages_on_systems where sysname not in(select distinct sysname from systems)'
	log( 'SQL: ' + sqlcmd )
	try:
		pkgdbcur.execute( sqlcmd )
		pkgdbhdl.commit()
	except:
		log( 'DB-Error by sql_del_unrefered_packages_on_systems:'+sqlcmd )
		pass

def sql_check_packages_in_systems( pkgdbhdl, pkgdbcur ):
	sqlcmd = 'delete from packages where(pkgname,vername)not in(select distinct pkgname,vername from packages_on_systems)'
	log( 'SQL: ' + sqlcmd )
	try:
		pkgdbcur.execute( sqlcmd )
		pkgdbhdl.commit()
	except:
		log( 'DB-Error by sql_check_packages_in_systems delete:'+ sqlcmd )
		pass

	sqlcmd = 'insert into packages(pkgname,vername,inststatus) select distinct on(pkgname,vername) pkgname,vername,inststatus from packages_on_systems where(pkgname,vername)not in(select pkgname,vername from packages)order by pkgname,vername,inststatus'
	log( 'SQL: ' + sqlcmd )
	try:
		pkgdbcur.execute( sqlcmd )
		pkgdbhdl.commit()
	except:
		log( 'DB-Error by sql_check_packages_in_systems insert:'+ sqlcmd )
		pass

	# todo update


# ------------------------------------------------------------------------------
# SQL Selects
# ------------------------------------------------------------------------------
def sql_select( db_connect_string, sqlcmd ):
	try:
		dbhdl = pgdb.connect(db_connect_string)
    	except:
		log( 'Cannot create a handle to the database.' )
		return []

	try:
		dbcur = dbhdl.cursor()
	except:
		log( 'Cannot create a cursor in the database.' )
		return []

	if not sql_check_privileges( dbcur ):
		log( 'No privileges to access the database.' )
		return []

	log( 'SQL: ' + sqlcmd )
	try:
		dbcur.execute( sqlcmd )
		p=dbcur.fetchall()
	except:
		log( 'Cannot read from the database:'+sqlcmd )
		return []
	dbcur.close()
	dbhdl.close()
	return p

def sql_get_current_timestamp( db_connect_string ):
	sqlcmd = 'select to_char(current_timestamp,\'YYYY-MM-DD HH24:MI:SS\')'
	if sqlcmd:
		return sql_select( db_connect_string, sqlcmd )[0][0]
	else:
		return None

def sql_getall_systems( db_connect_string ):
	sqlcmd = 'select sysname,sysversion,sysrole,to_char(scandate,\'YYYY-MM-DD HH24:MI:SS\'),ldaphostdn from systems order by sysname'
	return sql_select( db_connect_string, sqlcmd )

def sql_getall_systemroles( db_connect_string ):
	sqlcmd = 'select distinct sysrole from systems order by sysrole'
	return sql_select( db_connect_string, sqlcmd )

def sql_getall_systemversions( db_connect_string ):
	sqlcmd = 'select distinct sysversion from systems order by sysversion'
	return sql_select( db_connect_string, sqlcmd )

def sql_getall_packages( db_connect_string ):
	sqlcmd = 'select distinct on(pkgname,vername)pkgname,vername,inststatus from packages_on_systems order by pkgname,vername,inststatus'
	return sql_select( db_connect_string, sqlcmd )

def sql_getall_packages_in_systems( db_connect_string ):
	sqlcmd = 'select sysname,pkgname,vername,to_char(scandate,\'YYYY-MM-DD HH24:MI:SS\'),inststatus,selectedstate,inststate,currentstate from packages_on_systems order by sysname,pkgname,vername'
	return sql_select( db_connect_string, sqlcmd )

def sql_getall_inststati_from_packages_in_systems( db_connect_string ):
	sqlcmd = 'select distinct inststatus from packages_on_systems order by inststatus'
	return sql_select( db_connect_string, sqlcmd )

def sql_get_systems_by_query( db_connect_string, query ):
	if not query:
		return []
	sqlcmd = 'select sysname,sysversion,sysrole,to_char(scandate,\'YYYY-MM-DD HH24:MI:SS\'),ldaphostdn from systems where '+query+' order by sysname'
	return sql_select( db_connect_string, sqlcmd )

def sql_get_packages_in_systems_by_query( db_connect_string, query, join_systems ):
	if not query:
		return []
	if join_systems:
		sqlcmd = 'select sysname,pkgname,vername,to_char(packages_on_systems.scandate,\'YYYY-MM-DD HH24:MI:SS\'),inststatus,selectedstate,inststate,currentstate from packages_on_systems join systems using(sysname) where '+query+' order by sysname,pkgname,vername'
	else:
		sqlcmd = 'select sysname,pkgname,vername,to_char(packages_on_systems.scandate,\'YYYY-MM-DD HH24:MI:SS\'),inststatus,selectedstate,inststate,currentstate from packages_on_systems where '+query+' order by sysname,pkgname,vername'
	return sql_select( db_connect_string, sqlcmd )

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
def main(args):
	# ------------------------------------------------------------------------------
	# Argumente parsen
	# ------------------------------------------------------------------------------
	shortopts = '?h'
	longopts = [ 'help',
	             'test-superuser',
	             'add-system=',
		     'del-system=',
		     'db-server=',
		     'dump-all',
		     'dump-systems',
		     'dump-packages',
		     'dump-systems-packages',
		     'fill-testdb',
		     'clean',
		     'debug',
		     'version' ]

	try:
		opts, args = getopt.getopt(sys.argv[1:], shortopts, longopts)
	except getopt.error, msg:
		print msg
		sys.exit(1)

	to_debug       = 0
    	to_test_su     = 0
	add_system     = ''
	del_system     = ''
	dbsrvname = None
	to_dump_all    = 0
	to_dump_sys    = 0
	to_dump_pkg    = 0
	to_dump_syspkg = 0
	to_clean       = 0
	to_fill_testdb = 0
	need_su_privs  = 0
	for opt, val in opts:
		if opt == '-?':
			usage()
		elif opt == '-h':
			usage()
		elif opt == '--debug':
			to_debug = 1
		elif opt == '--test-superuser':
			to_test_su = 1
			need_su_privs = 1
		elif opt == '--add-system':
			add_system = val
			need_su_privs = 1
		elif opt == '--del-system':
			del_system = val
			need_su_privs = 1
		elif opt == '--db-server':
			dbsrvname = val
		elif opt == '--dump-all':
			to_dump_all = 1
		elif opt == '--dump-systems':
			to_dump_sys = 1
		elif opt == '--dump-packages':
			to_dump_pkg = 1
		elif opt == '--dump-systems-packages':
			to_dump_syspkg = 1
		elif opt == '--clean':
			to_clean = 1
			need_su_privs = 1
		elif opt == '--fill-testdb':
			to_fill_testdb = 1
			need_su_privs = 1
		elif opt == '--help':
			usage()
		elif opt == '--version':
			print '%s @%@package_version@%@'%sys.argv[0][sys.argv[0].rfind("/")+1:]
			sys.exit(1)

	# ------------------------------------------------------------------------------
	# Baseconfig auslesen
	# ------------------------------------------------------------------------------
	baseConfig=univention_baseconfig.baseConfig()
	baseConfig.load()

	# ------------------------------------------------------------------------------
	# Datenbankserver ermitteln
	# ------------------------------------------------------------------------------
	if not dbsrvname:
		dbsrvname = sql_get_dbservername( baseConfig['domainname'] )
		if len(dbsrvname)==0:
			print 'No DB-Server-Name found.'
			sys.exit(1)

	# ------------------------------------------------------------------------------
	# Datenbankzugriffsmethode ermitteln
	# ------------------------------------------------------------------------------
	if need_su_privs == 0:
		if baseConfig.has_key('pkgdb/user'):
			user=baseConfig['pkgdb/user']
		else:
			user='%s$' % baseConfig['hostname']
		if baseConfig.has_key('pkgdb/pwdfile'):
			pwdfile=baseConfig['pkgdb/pwdfile']
		else:
			pwdfile='/etc/machine.secret'
		pkgdb_connect_string = sql_create_connectstring( dbsrvname, user, pwdfile )
	else:
		pkgdb_connect_string = sql_create_localconnectstring( baseConfig['hostname']  )

	if len(pkgdb_connect_string)==0:
		print 'Connection to database not found or not configured.'
		sys.exit(1)

	if to_test_su > 0:
		# ------------------------------------------------------------------------------
		# Prüfe, ob dieser account ein Superuser ist
		# ------------------------------------------------------------------------------
    		sys.exit(sql_test_superuser())

	elif len(add_system) > 0:
		# ------------------------------------------------------------------------------
		# Systembenutzer zur Datenbank hinzufügen
		# ------------------------------------------------------------------------------
		sql_grant_system( pkgdb_connect_string, add_system )

	elif len(del_system) > 0:
		# ------------------------------------------------------------------------------
		# Systembenutzer aus Datenbank entfernen
		# ------------------------------------------------------------------------------
		sql_revoke_system( pkgdb_connect_string, del_system )

	elif to_dump_sys > 0:
		# ------------------------------------------------------------------------------
		# Dump
		# ------------------------------------------------------------------------------
		print 'dump systems'
		pkg = sql_getall_systems( pkgdb_connect_string )
		print 'sysname', 'sysversion', 'sysrole', 'scandate'
		for p in pkg:
			print p[0], p[1], p[2], p[3]

	elif to_dump_pkg > 0:
		# ------------------------------------------------------------------------------
		# Dump
		# ------------------------------------------------------------------------------
		print 'dump packages'
		pkg = sql_getall_packages( pkgdb_connect_string )
		print 'pkgname','vername','inststatus'
		for p in pkg:
			print p[0], p[1], p[2]

	elif to_dump_syspkg > 0:
		# ------------------------------------------------------------------------------
		# Dump
		# ------------------------------------------------------------------------------
		print 'dump packages_in_systems'
		pkg = sql_getall_packages_in_systems( pkgdb_connect_string )
		print 'sysname','pkgname','vername','scandate', 'inststatus', 'selectedstate', 'inststate', 'currentstate'
		for p in pkg:
			print p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]

	elif to_dump_all > 0:
		# ------------------------------------------------------------------------------
		# Dump
		# ------------------------------------------------------------------------------
		print 'dump all'

		print 'dump systems'
		pkg = sql_getall_systems( pkgdb_connect_string )
		print 'sysname', 'sysversion', 'sysrole', 'scandate'
		for p in pkg:
			print p[0], p[1], p[2], p[3]

		print 'dump packages'
		pkg = sql_getall_packages( pkgdb_connect_string )
		print 'pkgname','vername','inststatus'
		for p in pkg:
			print p[0], p[1], p[2]

		print 'dump packages_in_systems'
		pkg = sql_getall_packages_in_systems( pkgdb_connect_string )
		print 'sysname','pkgname','vername','scandate', 'inststatus', 'selectedstate', 'inststate', 'currentstate'
		for p in pkg:
			print p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]

	elif to_clean > 0:
		# --------------------------------------------------------------------------
		# nicht mehr referenzierte Pakete aus der Datenbank entfernen
		# --------------------------------------------------------------------------
		log("start cleaning of database")

		pkgdbhdl = pgdb.connect(pkgdb_connect_string)

		try:
			pkgdbcur = pkgdbhdl.cursor()
		except:
			print 'PKGDB: cannot create a cursor in the database'
			sys.exit(1)

		sql_del_unrefered_packages_on_systems( pkgdbhdl, pkgdbcur )
		sql_vacuum_analyse( pkgdb_connect_string )

		pkgdbcur.close()
		pkgdbhdl.close()

	elif to_fill_testdb > 0:
		# ------------------------------------------------------------------------------
		# Fülle Testdatenbank
		# ------------------------------------------------------------------------------
		log( 'start fill of testdb ' )
		sysversion = baseConfig['version/version'] + '-' + baseConfig['version/patchlevel']
		sysrole    = translate_sysrolename_from_baseconfig( baseConfig['server/role'] )
		ldaphostdn = baseConfig['ldap/hostdn']

		# ------------------------------------------------------------------------------
		# Datenbankverbindung öffnen
		# ------------------------------------------------------------------------------
    		if to_debug == 1:
			pkgdbhdl = pgdb.connect(pkgdb_connect_string)
		else:
			try:
				pkgdbhdl = pgdb.connect(pkgdb_connect_string)
			except:
				print 'PKGDB: cannot create a handle to the database pkgdb in %s' %(dbsrvname)
				sys.exit(1)

		try:
			pkgdbcur = pkgdbhdl.cursor()
		except:
			print 'PKGDB: cannot create a cursor in the database'
			sys.exit(1)

		try:
			if not sql_check_privileges( pkgdbcur ):
				raise "no priv"

			start_timestamp = sql_get_current_timestamp(pkgdb_connect_string)
		except:
			print 'PKGDB: no privileges to access the database'
			print 'You must first add this system with --add-system on the db-server (or join the system)'
			print 'This should be done automatically by the cronjob univention-pkg-check'
			sys.exit(1)

		# ------------------------------------------------------------------------------
		# Packages auslesen
		# ------------------------------------------------------------------------------
		apt_pkg.init()
		cache = apt_pkg.GetCache()
		packages = cache.Packages
		pkg_i_lst = []
		pkg_n_lst = []
		for package in packages:
			package_name = package.Name

			package_selectedstate = package.SelectedState
			# Definitions for Package::SelectedState
			# pkgSTATE_Unkown		0
			# pkgSTATE_Install		1
			# pkgSTATE_Hold			2
			# pkgSTATE_DeInstall		3
			# pkgSTATE_Purge		4

			package_inststate = package.InstState
			# Definitions for Package::InstState
			# pkgSTATE_Ok			0
			# pkgSTATE_ReInstReq		1
			# pkgSTATE_Hold			2
			# pkgSTATE_HoldReInstReq	3

			package_currentstate = package.CurrentState
			# Definitions for Package::CurrentState
			# pkgSTATE_NotInstalled		0
			# pkgSTATE_UnPacked		1
			# pkgSTATE_HalfConfigured	2
			# pkgSTATE_UnInstalled		3
			# pkgSTATE_HalfInstalled	4
			# pkgSTATE_ConfigFiles		5
			# pkgSTATE_Installed		6

			# Installed state:   Space - not installed;\n"
			#                     `*'  - installed;\n"
			#                     `-'  - not installed but config files remain;\n"
			#       packages in { `U'  - unpacked but not yet configured;\n"
			#      these states { `C'  - half-configured (an error happened);\n"
			#        are broken { `I'  - half-installed (an error happened).\n"

			if package.CurrentVer:
				package_verstr = package.CurrentVer.VerStr
				package_status = 'i'
				pkg_i_lst.append((package_name,package_verstr,package_selectedstate,package_inststate,package_currentstate))
			else:
				package_verstr =  ''
				package_status = 'n'
				pkg_n_lst.append((package_name,package_selectedstate,package_inststate,package_currentstate))

			if to_debug>0:
				print 'Package %s %s SelectedState=%d InstState=%d CurrentState=%d' %(package_name,package_status,package_selectedstate,package_inststate,package_currentstate)

		# ------------------------------------------------------------------------------
		# Schleife über 1500 testsysteme
		# ------------------------------------------------------------------------------
		for sysnr in range (1, 1500):
			sysname    = 'testsystem'+string.zfill( sysnr, 4)

			# ------------------------------------------------------------------------------
			# Datenbank füllen
			# ------------------------------------------------------------------------------

			# Systemname eintragen
			sql_put_sys_in_systems( pkgdbhdl, pkgdbcur, sysname, sysversion, sysrole, ldaphostdn )

			# alle bisherigen Eintraege loeschen
			sql_remove_all_packages_on_systems(pkgdbhdl, pkgdbcur, sysname)

			if has_psql_client():
				# Liste mit installierten und nicht installierten Paketen erzeugen
				tstamp = sql_get_current_timestamp(pkgdb_connect_string)
				fd, fname = tempfile.mkstemp(dir="/tmp", text=True)
				outfile = os.fdopen(fd, 'w')

				for pkgname, vername, package_selectedstate,package_inststate,package_currentstate in pkg_i_lst:
					outfile.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n"%(sysname, pkgname, vername, tstamp, "i", str(package_selectedstate), package_inststate, package_currentstate))
				for pkgname, package_selectedstate,package_inststate,package_currentstate in pkg_n_lst:
					outfile.write("%s\t%s\t\t%s\t%s\t%s\t%s\t%s\n"%(sysname, pkgname, tstamp, "n", str(package_selectedstate), package_inststate, package_currentstate))

				outfile.close()

				# Liste an sql-Server übertragen
				retval, rettxt = execute_psql_command(pkgdb_connect_string, """\\copy packages_on_systems from '%s'"""%fname)
				if not(rettxt==""):
					print("Error inserting package data: %s"%rettxt)

				os.unlink(fname)
			else:
				for pkgname, vername, package_selectedstate,package_inststate,package_currentstate in pkg_i_lst:
					sql_put_inserted_packages_on_systems( pkgdbhdl, pkgdbcur, sysname, pkgname, vername, package_selectedstate, package_inststate, package_currentstate )
				for pkgname,package_selectedstate,package_inststate,package_currentstate in pkg_n_lst:
					sql_put_removed_packages_on_systems( pkgdbhdl, pkgdbcur, sysname, pkgname, package_selectedstate, package_inststate, package_currentstate )

		# ------------------------------------------------------------------------------
		# Veraltete Einträge löschen
		# ------------------------------------------------------------------------------
		sql_del_unrefered_packages_on_systems( pkgdbhdl, pkgdbcur )

		# ------------------------------------------------------------------------------
		# Paketliste aktualisieren
		# ------------------------------------------------------------------------------
		sql_check_packages_in_systems( pkgdbhdl, pkgdbcur )

		# ------------------------------------------------------------------------------
		# Datenbankverbindung schliessen
		# ------------------------------------------------------------------------------
		pkgdbcur.close()
		pkgdbhdl.close()

		# ------------------------------------------------------------------------------
		# Datenbank intern aufräumen
		# ------------------------------------------------------------------------------
		sql_vacuum_analyse( pkgdb_connect_string )

		log( 'end of fill testdb' )
	else:
		# ------------------------------------------------------------------------------
		# Normales Verhalten: Scannen
		# ------------------------------------------------------------------------------
		sysname    = baseConfig['hostname']
		sysversion = baseConfig['version/version'] + '-' + baseConfig['version/patchlevel']
		if baseConfig.has_key('version/security-patchlevel') and baseConfig['version/security-patchlevel']:
			sysversion = "%s-%s" % (sysversion,baseConfig['version/security-patchlevel'])
		sysrole    = translate_sysrolename_from_baseconfig( baseConfig['server/role'] )
		ldaphostdn = baseConfig['ldap/hostdn']

		log( 'start scan of system ' + sysname )

		if baseConfig['pkgdb/scan'] != 'yes':
			log( 'univention-baseconfig pkgdb/scan != yes' )
			print 'In univention-baseconfig pkgdb/scan is not set to yes.'
			sys.exit(0)

		# ------------------------------------------------------------------------------
		# Datenbankverbindung öffnen
		# ------------------------------------------------------------------------------
    		if to_debug == 1:
			pkgdbhdl = pgdb.connect(pkgdb_connect_string)
		else:
			try:
				pkgdbhdl = pgdb.connect(pkgdb_connect_string)
			except:
				print 'PKGDB: cannot create a handle to the database pkgdb in %s' %(dbsrvname)
				sys.exit(1)

		try:
			pkgdbcur = pkgdbhdl.cursor()
		except:
			print 'PKGDB: cannot create a cursor in the database'
			sys.exit(1)

		try:
			if not sql_check_privileges( pkgdbcur ):
				raise "no priv"

			start_timestamp = sql_get_current_timestamp(pkgdb_connect_string)
		except:
			print 'PKGDB: no privileges to access the database'
			print 'You must first add this system with --add-system on the db-server (or join the system)'
			print 'This should be done automatically by the cronjob univention-pkg-check'
			sys.exit(1)

		# ------------------------------------------------------------------------------
		# Packages auslesen
		# ------------------------------------------------------------------------------
		apt_pkg.init()
		cache = apt_pkg.GetCache()
		packages = cache.Packages
		pkg_i_lst = []
		pkg_n_lst = []
		for package in packages:
			package_name = package.Name

			package_selectedstate = package.SelectedState
			# Definitions for Package::SelectedState
			# pkgSTATE_Unkown		0
			# pkgSTATE_Install		1
			# pkgSTATE_Hold			2
			# pkgSTATE_DeInstall		3
			# pkgSTATE_Purge		4

			package_inststate = package.InstState
			# Definitions for Package::InstState
			# pkgSTATE_Ok			0
			# pkgSTATE_ReInstReq		1
			# pkgSTATE_Hold			2
			# pkgSTATE_HoldReInstReq	3

			package_currentstate = package.CurrentState
			# Definitions for Package::CurrentState
			# pkgSTATE_NotInstalled		0
			# pkgSTATE_UnPacked		1
			# pkgSTATE_HalfConfigured	2
			# pkgSTATE_UnInstalled		3
			# pkgSTATE_HalfInstalled	4
			# pkgSTATE_ConfigFiles		5
			# pkgSTATE_Installed		6

			# Installed state:   Space - not installed;\n"
			#                     `*'  - installed;\n"
			#                     `-'  - not installed but config files remain;\n"
			#       packages in { `U'  - unpacked but not yet configured;\n"
			#      these states { `C'  - half-configured (an error happened);\n"
			#        are broken { `I'  - half-installed (an error happened).\n"

			if package.CurrentVer:
				package_verstr = package.CurrentVer.VerStr
				package_status = 'i'
				pkg_i_lst.append((package_name,package_verstr,package_selectedstate,package_inststate,package_currentstate))
			else:
				package_verstr =  ''
				package_status = 'n'
				pkg_n_lst.append((package_name,package_selectedstate,package_inststate,package_currentstate))

			if to_debug>0:
				print 'Package %s %s SelectedState=%d InstState=%d CurrentState=%d' %(package_name,package_status,package_selectedstate,package_inststate,package_currentstate)

		# ------------------------------------------------------------------------------
		# Datenbank füllen
		# ------------------------------------------------------------------------------

		# Systemname eintragen
		sql_put_sys_in_systems( pkgdbhdl, pkgdbcur, sysname, sysversion, sysrole, ldaphostdn )

		# alle bisherigen Eintraege loeschen
		sql_remove_all_packages_on_systems(pkgdbhdl, pkgdbcur, sysname)

		if has_psql_client():
			# Liste mit installierten und nicht installierten Paketen erzeugen
			tstamp = sql_get_current_timestamp(pkgdb_connect_string)
			fd, fname = tempfile.mkstemp(dir="/tmp", text=True)
			outfile = os.fdopen(fd, 'w')

			for pkgname, vername, package_selectedstate,package_inststate,package_currentstate in pkg_i_lst:
				outfile.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n"%(sysname, pkgname, vername, tstamp, "i", str(package_selectedstate), package_inststate, package_currentstate))
			for pkgname, package_selectedstate,package_inststate,package_currentstate in pkg_n_lst:
				outfile.write("%s\t%s\t\t%s\t%s\t%s\t%s\t%s\n"%(sysname, pkgname, tstamp, "n", str(package_selectedstate), package_inststate, package_currentstate))

			outfile.close()

			# Liste an sql-Server übertragen
			retval, rettxt = execute_psql_command(pkgdb_connect_string, """\\copy packages_on_systems from '%s'"""%fname)
			if not(rettxt==""):
				print("Error inserting package data: %s"%rettxt)

			os.unlink(fname)
		else:
			for pkgname, vername, package_selectedstate,package_inststate,package_currentstate in pkg_i_lst:
				sql_put_inserted_packages_on_systems( pkgdbhdl, pkgdbcur, sysname, pkgname, vername, package_selectedstate, package_inststate, package_currentstate )
			for pkgname,package_selectedstate,package_inststate,package_currentstate in pkg_n_lst:
				sql_put_removed_packages_on_systems( pkgdbhdl, pkgdbcur, sysname, pkgname, package_selectedstate, package_inststate, package_currentstate )

		# ------------------------------------------------------------------------------
		# Paketliste aktualisieren
		# ------------------------------------------------------------------------------
		sql_check_packages_in_systems( pkgdbhdl, pkgdbcur )

		# ------------------------------------------------------------------------------
		# Datenbankverbindung schliessen
		# ------------------------------------------------------------------------------
		pkgdbcur.close()
		pkgdbhdl.close()

		log( 'end of scan for system ' + sysname )

	return 0


if __name__ == '__main__':
	main(sys.argv[1:])
