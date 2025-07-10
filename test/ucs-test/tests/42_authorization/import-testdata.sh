#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_ldif_file>"
    exit 1
fi

LDIF_FILE="$1"

echo "Stopping slapd service ..."
systemctl stop slapd

DATA_MDB="/var/lib/univention-ldap/ldap/data.mdb"
DATA_MDB_BACKUP="/var/lib/univention-ldap/ldap/data.mdb.backup"

if [ ! -f "$DATA_MDB_BACKUP" ]; then
    echo "Backup file does not exist. Creating a backup..."
    cp "$DATA_MDB" "$DATA_MDB_BACKUP"
else
    echo "Backup file exists. Restoring from backup..."
    cp "$DATA_MDB_BACKUP" "$DATA_MDB"
fi
echo "Importing LDIF file..."
slapadd -l "$LDIF_FILE"
echo "Starting slapd service..."
systemctl start slapd
