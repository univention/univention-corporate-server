#!/usr/share/ucs-test/runner python3
## desc: Move an UDM computers object to a position which already exists local as container
## tags:
##  - replication
## roles:
##  - domaincontroller_backup
##  - domaincontroller_slave
## packages:
##  - univention-config
##  - univention-directory-manager-tools
##  - ldap-utils
## bugs:
##  - 33495
## exposure: dangerous

import os
import re
import sys

import ldap

import univention.testing.udm as udm_test
import univention.uldap
from univention.config_registry import ConfigRegistry
from univention.testing.strings import random_name
from univention.testing.utils import wait_for_replication


success = True

ucr = ConfigRegistry()
ucr.load()

UDM_MODULE = 'computers/linux'

name = random_name()
dn = f'cn={name},cn=memberserver,cn=computers,{ucr.get("ldap/base")}'
addlist = [
    ('cn', [name.encode('UTF-8')]),
    ('objectClass', [b'top', b'organizationalRole', b'univentionObject']),
    ('univentionObjectType', [b'container/cn']),
]

name_subobject = random_name()
dn_subobject = f'cn={name_subobject},cn={name},cn=memberserver,cn=computers,{ucr.get("ldap/base")}'
addlist_subobject = [
    ('cn', [name_subobject.encode('UTF-8')]),
    ('objectClass', [b'top', b'organizationalRole', b'univentionObject']),
    ('univentionObjectType', [b'container/cn']),
]


def get_entryUUID(lo, dn):
    result = lo.search_s(base=dn, scope=ldap.SCOPE_BASE, attrlist=['entryUUID'])
    print(f'DN: {dn}\n{result}')
    return result[0][1].get('entryUUID')[0].decode('ASCII')

# create computer


udm = udm_test.UCSTestUDM()
computer = udm.create_object(UDM_MODULE, name=name, position=ucr.get('ldap/base'), wait_for_replication=True)

lo = univention.uldap.getRootDnConnection().lo

# read computer uuid
computer_UUID = get_entryUUID(lo, computer)

# create container
lo.add_s(dn, addlist)
lo.add_s(dn_subobject, addlist_subobject)

container_UUID = get_entryUUID(lo, dn)
subcontainer_UUID = get_entryUUID(lo, dn_subobject)

# move container to the same position of the new container
udm.move_object(UDM_MODULE, dn=computer, position=f'cn=memberserver,cn=computers,{ucr.get("ldap/base")}', wait_for_replication=True)

new_computer_UUID = get_entryUUID(lo, dn)

# The container should have be replaced by the computer object
if computer_UUID != new_computer_UUID:
    print('ERROR: entryUUID of moved object do not match')
    print(f'  new_computer_UUID: {computer_UUID}')
    print(f'      computer_UUID: {new_computer_UUID}')
    print(f'     container_UUID: {container_UUID}')
    success = False

found_backup_container = False
found_backup_subcontainer = False

BACKUP_DIR = '/var/univention-backup/replication'
if os.path.exists(BACKUP_DIR):
    for f in os.listdir(BACKUP_DIR):
        fd = open(os.path.join(BACKUP_DIR, f))
        for line in fd.readlines():
            if re.match(f'entryUUID: {container_UUID}', line):
                found_backup_container = True
            elif re.match(f'entryUUID: {subcontainer_UUID}', line):
                found_backup_subcontainer = True
        fd.close()

if not found_backup_container:
    print(f'ERROR: Backup of container with UUID {container_UUID} was not found')
    success = False
if not found_backup_subcontainer:
    print(f'ERROR: Backup of subcontainer with UUID {subcontainer_UUID} was not found')
    success = False


udm.cleanup()
wait_for_replication()

if not success:
    sys.exit(1)

# vim: set ft=python :
