#!/bin/bash
#
# Univention Package Database
#  Univention Console module
#
# Copyright 2004-2011 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

# We need Root-Privileges
if [ $UID != 0 ] ;then
  echo "Only root ca do this" >&2
  exit 1
fi

# We need the DB-Superuser
if [ ! "`getent passwd postgres`" ] ;then
  echo "User postgres does not exist. Is really postgresql-server installed?" >&2
  exit 1
fi


#
# Create the local DB-Superuser pkgdbu for pkgdb with password in /etc/postgresql/pkgdb.secret
#
if [ -e /etc/postgresql/pkgdb.secret ] ;then
  # always create a new password
  rm /etc/postgresql/pkgdb.secret
fi
makepasswd --char 16 | tr -d '\n' >/etc/postgresql/pkgdb.secret
chmod ug=r,o= /etc/postgresql/pkgdb.secret
chown postgres:www-data /etc/postgresql/pkgdb.secret
pkgdbu=`su - postgres -c "psql template1 -c \"select * from pg_user where usename='pkgdbu'\""|awk '/ pkgdbu /{print $1}'`
if [ ! "$pkgdbu" ] ;then
  # only, if pkgdbu not exists
  su - postgres -c "createuser --adduser --no-createdb pkgdbu"
fi
su - postgres -c "psql -c \"ALTER USER pkgdbu WITH PASSWORD '`cat /etc/postgresql/pkgdb.secret`';\" template1"


#
# Create Database pkgdb and Tables
#
pkgdb=`su - postgres -c "psql --list"|awk '/ pkgdb /{print $1}'`
if [ ! "$pkgdb" ] ;then
  # only, if database not exists
  su - postgres -c "createdb -T template0 --encoding UNICODE --owner pkgdbu pkgdb"
  su - postgres -c "psql -d pkgdb -f /var/lib/postgres/pkgdb.sql"
fi
