#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Samba
#  listener module: manage idmap
#
# Copyright 2001-2019 Univention GmbH
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

__package__ = ''  # workaround for PEP 366
import listener
import os
import time
import univention.debug

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
	"Null Authority": "S-1-0",
	"World Authority": "S-1-1",
	"Everyone": "S-1-1-0",
	"Nobody": "S-1-0-0",
	"Creator Group": "S-1-3-1",
	"Creator Owner": "S-1-3-0",
	"Owner Rights": "S-1-3-4",
	"Dialup": "S-1-5-1",
	"Network": "S-1-5-2",
	"Batch": "S-1-5-3",
	"Interactive": "S-1-5-4",
	"Service": "S-1-5-6",
	"Anonymous Logon": "S-1-5-7",
	"Proxy": "S-1-5-8",
	"Enterprise Domain Controllers": "S-1-5-9",
	"Self": "S-1-5-10",
	"Authenticated Users": "S-1-5-11",
	"Restricted": "S-1-5-12",
	"Terminal Server User": "S-1-5-13",
	"Remote Interactive Logon": "S-1-5-14",
	"This Organization": "S-1-5-15",
	"IUSR": "S-1-5-17",
	"System": "S-1-5-18",
	"Local Service": "S-1-5-19",
	"Network Service": "S-1-5-20",
	"NTLM Authentication": "S-1-5-64-10",
	"SChannel Authentication": "S-1-5-64-14",
	"Digest Authentication": "S-1-5-64-21",
	"Other Organization": "S-1-5-1000",
}

__SPECIAL_SIDS = set(__SPECIAL_ACCOUNT_SIDS.values())


def open_idmap():
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
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, "%s: /var/lib/samba/private/idmap.ldb could not be opened" % name)
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
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "%s: rename_or_modify_idmap_entry: no mapping for objectSid %s, treating as add", (name, old_sambaSID))
			add_or_modify_idmap_entry(new_sambaSID, xidNumber, type_string, idmap)
		else:
			record = res.msgs[0]

			if record["type"][0] != type_string:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, "%s: %s entry type %s does not match object type %s" % (name, old_sambaSID, record["type"][0], type_string))
				univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, "%s: skipping rename of %s to %s" % (name, old_sambaSID, new_sambaSID))
				return False

			univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, "%s: renaming entry for %s to %s" % (name, old_sambaSID, new_sambaSID))

			# try a modrdn
			idmap.rename(str(record.dn), "CN=%s" % new_sambaSID)
			# and update related attributes
			msg = ldb.Message()
			msg.dn = ldb.Dn(idmap, "CN=%s" % new_sambaSID)
			msg["cn"] = ldb.MessageElement([new_sambaSID], ldb.FLAG_MOD_REPLACE, "cn")
			new_objectSid = ndr_pack(security.dom_sid(new_sambaSID))
			msg["objectSid"] = ldb.MessageElement([new_objectSid], ldb.FLAG_MOD_REPLACE, "objectSid")
			idmap.modify(msg)

	except ldb.LdbError as (enum, estr):
		univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, estr)
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
		if record["type"][0] != type_string:
			msg["type"] = ldb.MessageElement([type_string], ldb.FLAG_MOD_REPLACE, "type")
		if record["xidNumber"][0] != str(xidNumber):
			msg["xidNumber"] = ldb.MessageElement([str(xidNumber)], ldb.FLAG_MOD_REPLACE, "xidNumber")

		if len(msg) != 0:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, "%s: modifying entry for %s" % (name, sambaSID))
			if "xidNumber" in msg:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "%s: changing xidNumber from %s to %s" % (name, record["xidNumber"][0], xidNumber))
			if "type" in msg:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "%s: changing type from %s to %s" % (name, record["type"][0], type_string))

		idmap.modify(msg)

	except ldb.LdbError as (enum, estr):
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, estr)


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

		univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, "%s: added entry for %s" % (name, sambaSID))

	except ldb.LdbError as (enum, estr):
		# ok, there is an entry for this sambaSID, let's replace it
		modify_idmap_entry(sambaSID, xidNumber, type_string, idmap)


def remove_idmap_entry(sambaSID, xidNumber, type_string, idmap=None):
	if not idmap:
		# need to open idmap here in case it has been removed since the module  was loaded
		idmap = open_idmap()

	try:
		res = idmap.search('', ldb.SCOPE_SUBTREE, "(&(objectClass=sidMap)(cn=%s))" % sambaSID, attrs=["objectSid", "xidNumber", "type"])
		if not res:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "%s: remove_idmap_entry: no mapping for objectSid %s, skipping", (name, sambaSID))
		else:
			record = res.msgs[0]

			univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, "%s: removing entry for %s" % (name, sambaSID))

			idmap.delete(ldb.Dn(idmap, str(record.dn)))

			if record["xidNumber"][0] != str(xidNumber):
				univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, "%s: removed entry xidNumber %s did not match object xidNumber %s" % (name, record["xidNumber"][0], xidNumber))
			if record["type"][0] != type_string:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, "%s: removed entry type %s did not match object type %s" % (name, record["type"][0], type_string))

	except ldb.LdbError as (enum, estr):
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, estr)


def initialize():
	idmap_ldb = '/var/lib/samba/private/idmap.ldb'
	listener.setuid(0)
	try:
		if os.path.exists(idmap_ldb):
			idmap_ldb_backup = '%s_%d' % (idmap_ldb, time.time())
			univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, 'Move %s to %s' % (idmap_ldb, idmap_ldb_backup))
			os.rename(idmap_ldb, idmap_ldb_backup)
		setup_idmapdb(idmap_ldb, session_info=system_session(), lp=lp)
	finally:
		listener.unsetuid()


def handler(dn, new, old, operation):

	idmap = open_idmap()
	if new:
		try:
			if 'sambaSamAccount' in new['objectClass']:
				xid_attr = 'uidNumber'
				xid_type = 'ID_TYPE_UID'
				samaccountname = new.get('uid', [None])[0]
			elif 'sambaGroupMapping' in new['objectClass']:
				xid_attr = 'gidNumber'
				xid_type = 'ID_TYPE_GID'
				samaccountname = new.get('cn', [None])[0]

			new_xid = new.get(xid_attr, [''])[0]
			if new_xid:
				new_sambaSID = new.get(sidAttribute, [''])[0]
				if xid_type == 'ID_TYPE_GID' and new_sambaSID in __SPECIAL_SIDS:
					xid_type = 'ID_TYPE_BOTH'
				old_sambaSID = old.get(sidAttribute, [''])[0]
				if old and old_sambaSID:
					if not new_sambaSID:
						univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, "Samba account '%s' has no attribute '%s', cannot update" % (samaccountname, sidAttribute))
						return
					if new_sambaSID != old_sambaSID:
						rename_or_modify_idmap_entry(old_sambaSID, new_sambaSID, new_xid, xid_type, idmap)
					old_xid = old.get(xid_attr, [''])[0]
					if new_xid != old_xid:
						add_or_modify_idmap_entry(new_sambaSID, new_xid, xid_type, idmap)
				else:
					if not new_sambaSID:
						univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, "Samba account '%s' has no attribute '%s', cannot add" % (samaccountname, sidAttribute))
						return
					add_or_modify_idmap_entry(new_sambaSID, new_xid, xid_type, idmap)
		except ldb.LdbError as (enum, estr):
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, "%s: entry for %s could not be updated" % (name, new['sambaSID'][0]))
	elif old:
		if operation == 'r':  # modrdn
			return

		try:
			if 'sambaSamAccount' in old['objectClass']:
				xid_attr = 'uidNumber'
				xid_type = 'ID_TYPE_UID'
				samaccountname = old.get('uid', [None])[0]
			elif 'sambaGroupMapping' in old['objectClass']:
				xid_attr = 'gidNumber'
				xid_type = 'ID_TYPE_GID'
				samaccountname = old.get('cn', [None])[0]

			old_xid = old.get(xid_attr, [''])[0]
			if old_xid:
				old_sambaSID = old.get(sidAttribute, [''])[0]
				if not old_sambaSID:
					univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, "Samba account '%s' has no attribute '%s', cannot remove" % (samaccountname, sidAttribute))
					return
				if xid_type == 'ID_TYPE_GID' and old_sambaSID in __SPECIAL_SIDS:
					xid_type = 'ID_TYPE_BOTH'
				remove_idmap_entry(old_sambaSID, old_xid, xid_type, idmap)
		except ldb.LdbError as (enum, estr):
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, "%s: entry for %s could not be updated" % (name, old[sidAttribute][0]))


if __name__ == '__main__':
	from optparse import OptionParser
	import sys
	from univention.config_registry import ConfigRegistry
	import subprocess
	from ldif import LDIFParser
	import StringIO

	parser = OptionParser(usage="%prog [-h|--help] [--direct-resync]")
	parser.add_option(
		"--direct-resync", action="store_true", dest="direct_resync", default=False,
		help="Filter the output of univention-ldapsearch through the this module"
	)
	(options, args) = parser.parse_args()

	if not options.direct_resync:
		parser.error("The option --direct-resync is required to run this module directly")
		sys.exit(1)

	univention.debug.init("stderr", univention.debug.NO_FLUSH, univention.debug.NO_FUNCTION)
	ucr = ConfigRegistry()
	ucr.load()
	univention.debug.set_level(univention.debug.LISTENER, int(ucr.get('listener/debug/level', 2)))

	cmd = ['/usr/bin/univention-ldapsearch', '-LLL', filter, 'objectClass']
	cmd.extend(attributes)
	p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	(stdout, stderr) = p1.communicate()

	class ListenerHandler(LDIFParser):

		def __init__(self, input):
			LDIFParser.__init__(self, input)

		def handle(self, dn, entry):
			handler(dn, entry, {}, 'a')

	parser = ListenerHandler(StringIO.StringIO(stdout))
	parser.parse()

	subprocess.call(['net', 'cache', 'flush'])
