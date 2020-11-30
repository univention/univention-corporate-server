#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Samba
#  listener module: manage idmap
#
# Copyright 2001-2021 Univention GmbH
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

from __future__ import absolute_import

import listener
import os
import time
import univention.debug as ud

import ldb
from samba.ndr import ndr_pack
from samba.dcerpc import security
from samba.idmap import IDmapDB
from samba.auth import system_session
from samba.param import LoadParm
from samba.provision import setup_idmapdb

name = 'samba4-idmap'
description = 'Update local IDmap entries'
filter = '(&(|(objectClass=sambaSamAccount)(objectClass=sambaGroupMapping))(sambaSID=*))'
attributes = ['uid', 'cn', 'sambaSID', 'univentionSamba4SID', 'uidNumber', 'gidNumber']
modrdn = '1'

# Globals
lp = LoadParm()
listener.setuid(0)
lp.load('/etc/samba/smb.conf')
listener.unsetuid()

sidAttribute = 'sambaSID'
if listener.configRegistry.is_false('connector/s4/mapping/sid', False):
	sidAttribute = 'univentionSamba4SID'

__SPECIAL_ACCOUNT_SIDS = {
	"Null Authority": b"S-1-0",
	"World Authority": b"S-1-1",
	"Everyone": b"S-1-1-0",
	"Nobody": b"S-1-0-0",
	"Creator Group": b"S-1-3-1",
	"Creator Owner": b"S-1-3-0",
	"Owner Rights": b"S-1-3-4",
	"Dialup": b"S-1-5-1",
	"Network": b"S-1-5-2",
	"Batch": b"S-1-5-3",
	"Interactive": b"S-1-5-4",
	"Service": b"S-1-5-6",
	"Anonymous Logon": b"S-1-5-7",
	"Proxy": b"S-1-5-8",
	"Enterprise Domain Controllers": b"S-1-5-9",
	"Self": b"S-1-5-10",
	"Authenticated Users": b"S-1-5-11",
	"Restricted": b"S-1-5-12",
	"Terminal Server User": b"S-1-5-13",
	"Remote Interactive Logon": b"S-1-5-14",
	"This Organization": b"S-1-5-15",
	"IUSR": b"S-1-5-17",
	"System": b"S-1-5-18",
	"Local Service": b"S-1-5-19",
	"Network Service": b"S-1-5-20",
	"NTLM Authentication": b"S-1-5-64-10",
	"SChannel Authentication": b"S-1-5-64-14",
	"Digest Authentication": b"S-1-5-64-21",
	"Other Organization": b"S-1-5-1000",
}

__SPECIAL_SIDS = set(__SPECIAL_ACCOUNT_SIDS.values())


def open_idmap():
	# type: () -> IDmapDB
	global lp

	if open_idmap.instance:
		return open_idmap.instance

	idmap_ldb = '/var/lib/samba/private/idmap.ldb'
	listener.setuid(0)
	try:
		if not os.path.exists(idmap_ldb):
			setup_idmapdb(idmap_ldb, session_info=system_session(), lp=lp)
		open_idmap.instance = IDmapDB(idmap_ldb, session_info=system_session(), lp=lp)
	except ldb.LdbError:
		ud.debug(ud.LISTENER, ud.ERROR, "%s: /var/lib/samba/private/idmap.ldb could not be opened" % name)
		raise
	finally:
		listener.unsetuid()

	return open_idmap.instance


open_idmap.instance = None


def rename_or_modify_idmap_entry(old_sambaSID, new_sambaSID, xidNumber, type_string, idmap=None):
	if not idmap:
		# need to open idmap here in case it has been removed since the module  was loaded
		idmap = open_idmap()

	try:
		res = idmap.search('', ldb.SCOPE_SUBTREE, "(&(objectClass=sidMap)(cn=%s))" % old_sambaSID, attrs=["objectSid", "type"])
		if not res:
			ud.debug(ud.LISTENER, ud.INFO, "%s: rename_or_modify_idmap_entry: no mapping for objectSid %s, treating as add", (name, old_sambaSID))
			add_or_modify_idmap_entry(new_sambaSID, xidNumber, type_string, idmap)
		else:
			record = res.msgs[0]

			if record["type"][0].decode('ASCII') != type_string:
				ud.debug(ud.LISTENER, ud.ERROR, "%s: %s entry type %s does not match object type %s" % (name, old_sambaSID, record["type"][0], type_string))
				ud.debug(ud.LISTENER, ud.ERROR, "%s: skipping rename of %s to %s" % (name, old_sambaSID, new_sambaSID))
				return False

			ud.debug(ud.LISTENER, ud.PROCESS, "%s: renaming entry for %s to %s" % (name, old_sambaSID, new_sambaSID))

			# try a modrdn
			idmap.rename(str(record.dn), "CN=%s" % new_sambaSID)
			# and update related attributes
			msg = ldb.Message()
			msg.dn = ldb.Dn(idmap, "CN=%s" % new_sambaSID)
			msg["cn"] = ldb.MessageElement([new_sambaSID], ldb.FLAG_MOD_REPLACE, "cn")
			new_objectSid = ndr_pack(security.dom_sid(new_sambaSID))
			msg["objectSid"] = ldb.MessageElement([new_objectSid], ldb.FLAG_MOD_REPLACE, "objectSid")
			idmap.modify(msg)

	except ldb.LdbError as exc:
		(enum, estr) = exc.args
		ud.debug(ud.LISTENER, ud.WARN, estr)
		# ok, there is an entry for the target sambaSID, let's remove the old sambaSID and modify the target
		remove_idmap_entry(old_sambaSID, xidNumber, type_string, idmap)
		modify_idmap_entry(new_sambaSID, xidNumber, type_string, idmap)


def modify_idmap_entry(sambaSID, xidNumber, type_string, idmap=None):
	if not idmap:
		# need to open idmap here in case it has been removed since the module  was loaded
		idmap = open_idmap()

	try:
		res = idmap.search('', ldb.SCOPE_SUBTREE, "(&(objectClass=sidMap)(cn=%s))" % sambaSID, attrs=["objectSid", "xidNumber", "type"])
		record = res.msgs[0]

		msg = ldb.Message()
		msg.dn = ldb.Dn(idmap, str(record.dn))
		if record["type"][0].decode('ASCII') != type_string:
			msg["type"] = ldb.MessageElement([type_string], ldb.FLAG_MOD_REPLACE, "type")
		if record["xidNumber"][0].decode('ASCII') != str(xidNumber):
			msg["xidNumber"] = ldb.MessageElement([str(xidNumber)], ldb.FLAG_MOD_REPLACE, "xidNumber")

		if len(msg) != 0:
			ud.debug(ud.LISTENER, ud.PROCESS, "%s: modifying entry for %s" % (name, sambaSID))
			if "xidNumber" in msg:
				ud.debug(ud.LISTENER, ud.INFO, "%s: changing xidNumber from %s to %s" % (name, record["xidNumber"][0], xidNumber))
			if "type" in msg:
				ud.debug(ud.LISTENER, ud.INFO, "%s: changing type from %s to %s" % (name, record["type"][0], type_string))

		idmap.modify(msg)

	except ldb.LdbError as exc:
		(enum, estr) = exc.args
		ud.debug(ud.LISTENER, ud.ERROR, estr)


def add_or_modify_idmap_entry(sambaSID, xidNumber, type_string, idmap=None):
	if not idmap:
		# need to open idmap here in case it has been removed since the module  was loaded
		idmap = open_idmap()

	try:
		idmap_type = {
			'ID_TYPE_UID': idmap.TYPE_UID,
			'ID_TYPE_GID': idmap.TYPE_GID,
			'ID_TYPE_BOTH': idmap.TYPE_BOTH
		}
		idmap.setup_name_mapping(sambaSID, idmap_type[type_string], xidNumber)
		#
		# or directly:
		#
		# idmap.add({"dn": "CN=%s" % sambaSID, "objectClass": "sidMap",
		# "cn": sambaSID, "objectSid": [ndr_pack(security.dom_sid(sambaSID))],
		# "xidNumber": [str(xidNumber)], "type": [type_string]})

		ud.debug(ud.LISTENER, ud.PROCESS, "%s: added entry for %s" % (name, sambaSID))

	except ldb.LdbError as exc:
		# ok, there is an entry for this sambaSID, let's replace it
		(enum, estr) = exc.args
		# ok, there is an entry for this sambaSID, let's replace it
		modify_idmap_entry(sambaSID, xidNumber, type_string, idmap)


def remove_idmap_entry(sambaSID, xidNumber, type_string, idmap=None):
	if not idmap:
		# need to open idmap here in case it has been removed since the module  was loaded
		idmap = open_idmap()

	try:
		res = idmap.search('', ldb.SCOPE_SUBTREE, "(&(objectClass=sidMap)(cn=%s))" % sambaSID, attrs=["objectSid", "xidNumber", "type"])
		if not res:
			ud.debug(ud.LISTENER, ud.INFO, "%s: remove_idmap_entry: no mapping for objectSid %s, skipping", (name, sambaSID))
		else:
			record = res.msgs[0]

			ud.debug(ud.LISTENER, ud.PROCESS, "%s: removing entry for %s" % (name, sambaSID))

			idmap.delete(ldb.Dn(idmap, str(record.dn)))

			if record["xidNumber"][0].decode('ASCII') != str(xidNumber):
				ud.debug(ud.LISTENER, ud.WARN, "%s: removed entry xidNumber %s did not match object xidNumber %s" % (name, record["xidNumber"][0], xidNumber))
			if record["type"][0].decode('ASCII') != type_string:
				ud.debug(ud.LISTENER, ud.WARN, "%s: removed entry type %s did not match object type %s" % (name, record["type"][0], type_string))

	except ldb.LdbError as exc:
		(enum, estr) = exc.args
		ud.debug(ud.LISTENER, ud.ERROR, estr)


def initialize():
	# type: () -> None
	idmap_ldb = '/var/lib/samba/private/idmap.ldb'
	listener.setuid(0)
	try:
		if os.path.exists(idmap_ldb):
			idmap_ldb_backup = '%s_%d' % (idmap_ldb, time.time())
			ud.debug(ud.LISTENER, ud.PROCESS, 'Move %s to %s' % (idmap_ldb, idmap_ldb_backup))
			os.rename(idmap_ldb, idmap_ldb_backup)
		setup_idmapdb(idmap_ldb, session_info=system_session(), lp=lp)
	finally:
		listener.unsetuid()


def handler(dn, new, old, operation):
	# type: (str, dict, dict, str) -> None

	idmap = open_idmap()
	if new:
		try:
			if b'sambaSamAccount' in new['objectClass']:
				xid_attr = 'uidNumber'
				xid_type = 'ID_TYPE_UID'
				samaccountname = new.get('uid', [None])[0]
			elif b'sambaGroupMapping' in new['objectClass']:
				xid_attr = 'gidNumber'
				xid_type = 'ID_TYPE_GID'
				samaccountname = new.get('cn', [None])[0]

			new_xid = new.get(xid_attr, [b''])[0]
			if new_xid:
				new_sambaSID = new.get(sidAttribute, [b''])[0]
				if xid_type == 'ID_TYPE_GID' and new_sambaSID in __SPECIAL_SIDS:
					xid_type = 'ID_TYPE_BOTH'
				old_sambaSID = old.get(sidAttribute, [b''])[0]
				if old and old_sambaSID:
					if not new_sambaSID:
						ud.debug(ud.LISTENER, ud.WARN, "Samba account %r has no attribute '%s', cannot update" % (samaccountname, sidAttribute))
						return
					if new_sambaSID != old_sambaSID:
						rename_or_modify_idmap_entry(old_sambaSID.decode('ASCII'), new_sambaSID.decode('ASCII'), new_xid, xid_type, idmap)
					old_xid = old.get(xid_attr, [b''])[0]
					if new_xid != old_xid:
						add_or_modify_idmap_entry(new_sambaSID.decode('ASCII'), new_xid.decode('ASCII'), xid_type, idmap)
				else:
					if not new_sambaSID:
						ud.debug(ud.LISTENER, ud.WARN, "Samba account %r has no attribute '%s', cannot add" % (samaccountname, sidAttribute))
						return
					add_or_modify_idmap_entry(new_sambaSID.decode('ASCII'), new_xid.decode('ASCII'), xid_type, idmap)
		except ldb.LdbError as exc:
			(enum, estr) = exc.args
			ud.debug(ud.LISTENER, ud.ERROR, "%s: entry for %r could not be updated" % (name, new[sidAttribute][0]))
	elif old:
		if operation == 'r':  # modrdn
			return

		try:
			if b'sambaSamAccount' in old['objectClass']:
				xid_attr = 'uidNumber'
				xid_type = 'ID_TYPE_UID'
				samaccountname = old.get('uid', [None])[0]
			elif b'sambaGroupMapping' in old['objectClass']:
				xid_attr = 'gidNumber'
				xid_type = 'ID_TYPE_GID'
				samaccountname = old.get('cn', [None])[0]

			old_xid = old.get(xid_attr, [b''])[0]
			if old_xid:
				old_sambaSID = old.get(sidAttribute, [b''])[0]
				if not old_sambaSID:
					ud.debug(ud.LISTENER, ud.WARN, "Samba account '%s' has no attribute '%s', cannot remove" % (samaccountname, sidAttribute))
					return
				if xid_type == 'ID_TYPE_GID' and old_sambaSID in __SPECIAL_SIDS:
					xid_type = 'ID_TYPE_BOTH'
				remove_idmap_entry(old_sambaSID.decode('ASCII'), old_xid.decode('ASCII'), xid_type, idmap)
		except ldb.LdbError as exc:
			(enum, estr) = exc.args
			ud.debug(ud.LISTENER, ud.ERROR, "%s: entry for %r could not be updated" % (name, old[sidAttribute][0]))


if __name__ == '__main__':
	from argparse import ArgumentParser
	import sys
	from univention.config_registry import ConfigRegistry
	import subprocess
	from ldif import LDIFParser
	import io

	parser = ArgumentParser()
	parser.add_argument(
		"--direct-resync", action="store_true", dest="direct_resync", default=False,
		help="Filter the output of univention-ldapsearch through this module"
	)
	options = parser.parse_args()

	if not options.direct_resync:
		parser.error("The option --direct-resync is required to run this module directly")
		sys.exit(1)

	ud.init("stderr", ud.NO_FLUSH, ud.NO_FUNCTION)
	ucr = ConfigRegistry()
	ucr.load()
	ud.set_level(ud.LISTENER, int(ucr.get('listener/debug/level', 2)))

	cmd = ['/usr/bin/univention-ldapsearch', '-LLL', filter, 'objectClass']
	cmd.extend(attributes)
	p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	(stdout, stderr) = p1.communicate()

	class ListenerHandler(LDIFParser):

		def __init__(self, input):
			LDIFParser.__init__(self, input)

		def handle(self, dn, entry):
			handler(dn, entry, {}, 'a')

	parser = ListenerHandler(io.BytesIO(stdout))
	parser.parse()

	subprocess.call(['net', 'cache', 'flush'])
