set doc off

/**

Oracle Table Creation Scripts.

$Horde: horde/scripts/db/oracle_create.sql,v 1.4 2004/03/18 20:25:11 jan Exp $

@author Miguel Ward <mward@aluar.com.ar>

This sql creates the Horde SQL tables in an Oracle 8.x
database. Should work with Oracle 9.x (and Oracle7 using varchar2).

Once the tables are created you have to complete following steps:

1) Edit /usr/local/horde/config/horde.php and modify/include:

// Preference System Settings

// What preferences driver should we use? Valid values are 'none'
// (meaning use system defaults and don't save any user preferences),
// 'session' (preferences only persist during the login), 'ldap',
// and 'sql'.

$conf['prefs']['driver'] = 'sql';

// Any parameters that the preferences driver needs. This includes
// database or ldap server, username/password to connect with, etc.
$conf['prefs']['params']['phptype'] = 'oci8';
$conf['prefs']['params']['hostspec'] = 'database_name';
$conf['prefs']['params']['username'] = 'horde';
$conf['prefs']['params']['password'] = '*******';
$conf['prefs']['params']['database'] = '';
$conf['prefs']['params']['table'] = 'horde_prefs';

Where 'database_name' is the database name as defined in tnsnames.ora
that you wish to connect to.

2) Make similar changes in the configuration file belonging to turba
(IF you wish to save 'My Addressbook' in Oracle):

vi /usr/local/horde/turba/config/sources.php

(see above).

3) Make sure that the user that starts up Apache (usually nobody or
www-data) has the following environment variables defined:

ORACLE_HOME=/home/oracle/OraHome1                      ; export ORACLE_HOME
ORA_NLS=/home/oracle/OraHome1/ocommon/nls/admin/data   ; export ORA_NLS
ORA_NLS33=/home/oracle/OraHome1/ocommon/nls/admin/data ; export ORA_NLS33
LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH      ; export LD_LIBRARY_PATH

YOU MUST CUSTOMIZE THESE VALUES TO BE APPROPRIATE TO YOUR INSTALLATION

You can include these variables in the user's local .profile or in
/etc/profile, etc. 
Obviously you must have Oracle installed on this machine AND you must
have compiled Apache/PHP with Oracle (you included --with-oci8 in the
build arguments for PHP, or uncommented the oci8 extension in
php.ini).

4) Make sure you have latest PEAR instalation inside your PHP library.
Specifically the file /usr/local/lib/php/DB.php and the directory
associated with it must be dated after April 2002 (PHP 4.2.1 is ok).

If you have an older version of PHP OR you overwrote the PHP
installation with the PEAR version 4.1.0 found at the IMP website
everything will seem to work ok but the 'Options' you save in IMP will
not appear next time you connect.

5) No grants are necessary since we connect as the owner of the
tables. If you wish you can adapt the creation of tables to include
tablespace and storage information. Since we include none it will use
the default tablespace values for the user creating these tables. Same
with the indexes (in theory these should use a different tablespace).

There is no need to shut down and start up the database!

6) It is important to note that no column can have more than 4000
bytes (whilst in MySQL there is no such limit), this could cause
problems when saving long 'signatures' or many identities (which are
all stored in only one record). You will see an 'ORA-01704: string
literal too long' in /tmp/horde.log and a 'DB Error: unknown error' at
line 297 on the screen.

This is an Oracle limitation. PHP/PEAR could in theory circumvent this
limitation with a fair amount of work. The PEAR distribution of April
2002 does not include this workaround thus the limitation.

*/

rem conn horde/&horde_password@database


/**

This is the Horde users table, needed only if you are using SQL
authentication. Note that passowrds in this table need to be
md5-encoded.

*/

CREATE TABLE horde_users (
    user_uid    VARCHAR2(255) NOT NULL,
    user_pass   VARCHAR2(32) NOT NULL,

    PRIMARY KEY (user_uid)
);


/**

This is the Horde preferences table, holding all of the user-specific
options for every Horde user.

pref_uid   is the username (appended with @realm if specified in servers.php)
pref_scope is either IMP, Horde or turba
pref_name  is the name of the variable to save
pref_value is the value saved (can be very long)

In MySQL 'pref_value' is defined as a TEXT column which is equivalent
to a CLOB in Oracle. Unfortunately one still gets an 'ORA-01704:
string literal too long' and Oracle's solution is to split message in
pieces (which IMP/Horde/PEAR/PHP do not do at the present time).

We use a CLOB column so that longer columns can be supported when
Oracle fixes the limitation or PHP/PEAR include a workaround.

If still using Oracle 7 this should work but you have to use
VARCHAR2(2000) which is the limit imposed by said version.

*/

CREATE TABLE horde_prefs (
    pref_uid        CHAR(255) NOT NULL,
    pref_scope      CHAR(16) NOT NULL,
    pref_name       CHAR(32) NOT NULL,
--  See above notes on CLOBs.
    pref_value      CLOB,

    PRIMARY KEY (pref_uid, pref_scope, pref_name)
);


/*

The DataTree tables are used for holding hierarchical data such as
Groups, Permissions, and data for some Horde applications.

*/

CREATE TABLE horde_datatree (
    datatree_id NUMBER(16) NOT NULL,
    group_uid VARCHAR2(255) NOT NULL,
    user_uid VARCHAR2(255) NOT NULL,
    datatree_name VARCHAR2(255) NOT NULL,
    datatree_parents VARCHAR2(255) NOT NULL,
    datatree_order NUMBER(16),
--  See above notes on CLOBs.
    datatree_data CLOB,
    datatree_serialized NUMBER(8) DEFAULT 0 NOT NULL,
    datatree_updated DATE,

    PRIMARY KEY (datatree_id)
);

CREATE INDEX datatree_datatree_name_idx ON horde_datatree (datatree_name);
CREATE INDEX datatree_group_idx ON horde_datatree (group_uid);
CREATE INDEX datatree_user_idx ON horde_datatree (user_uid);
CREATE INDEX datatree_order_idx ON horde_datatree (datatree_order);
CREATE INDEX datatree_serialized_idx ON horde_datatree (datatree_serialized);


/**

Turba table as defined in /usr/local/horde/turba/scripts/drivers/turba.sql

Required for local SQL-based address books.

*/

CREATE TABLE turba_objects (
    object_id VARCHAR2(32) NOT NULL,
    owner_id VARCHAR2(255) NOT NULL,
    object_name VARCHAR2(255),
    object_alias VARCHAR2(32),
    object_email VARCHAR2(255),
    object_homeAddress VARCHAR2(255),
    object_workAddress VARCHAR2(255),
    object_homePhone VARCHAR2(25),
    object_workPhone VARCHAR2(25),
    object_cellPhone VARCHAR2(25),
    object_fax VARCHAR2(25),
    object_title VARCHAR2(32),
    object_company VARCHAR2(32),
    object_notes VARCHAR2(4000),

    PRIMARY KEY (object_id)
);

exit
