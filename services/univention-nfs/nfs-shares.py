# -*- coding: utf-8 -*-
#
# Univention NFS
#  listener module: update configuration of local NFS shares
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

from __future__ import absolute_import
import listener
import os
import re
import univention.debug
import univention.lib.listenerSharePath
import cPickle
from univention.config_registry.interfaces import Interfaces

hostname = listener.baseConfig['hostname']
domainname = listener.baseConfig['domainname']
interfaces = Interfaces(listener.configRegistry)
ip = interfaces.get_default_ip_address().ip

name = 'nfs-shares'
description = 'Create configuration for NFS shares'
filter = '(&(objectClass=univentionShare)(|(univentionShareHost=%s.%s)(univentionShareHost=%s)))' % (hostname, domainname, ip)
modrdn = '1'

__exports = '/etc/exports'
__comment_pattern = re.compile('^"*/.*#[ \t]*LDAP:[ \t]*(.*)')

tmpFile = '/var/cache/univention-directory-listener/nfs-shares.oldObject'


def handler(dn, new, old, command):
	# create tmp dir
	tmpDir = os.path.dirname(tmpFile)
	listener.setuid(0)
	try:
		if not os.path.exists(tmpDir):
			os.makedirs(tmpDir)
	except Exception as e:
		univention.debug.debug(
			univention.debug.LISTENER, univention.debug.ERROR,
			"%s: could not create tmp dir %s (%s)" % (name, tmpDir, str(e)))
		return
	finally:
		listener.unsetuid()

	# modrdn stuff
	# 'r'+'a' -> renamed
	# command='r' and "not new and old"
	# command='a' and "new and not old"

	# write old object to pickle file
	oldObject = {}
	listener.setuid(0)
	try:
		# object was renamed -> save old object
		if command == "r" and old:
			with open(tmpFile, "wb") as fp:
				os.chmod(tmpFile, 0o600)
				cPickle.dump({"dn": dn, "old": old}, fp)
		elif command == "a" and not old:
			if os.path.isfile(tmpFile):
				with open(tmpFile, "rb") as fp:
					p = cPickle.load(fp)
				oldObject = p.get("old", {})
				os.remove(tmpFile)
	except Exception as e:
		if os.path.isfile(tmpFile):
			os.remove(tmpFile)
		univention.debug.debug(
			univention.debug.LISTENER, univention.debug.ERROR,
			"%s: could not read/write tmp file %s (%s)" % (name, tmpFile, str(e)))
	finally:
		listener.unsetuid()

	# update exports file
	lines = _read(lambda match: not match or match.group(1) != _quote(dn))

	if new and 'objectClass' in new and 'univentionShareNFS' in new['objectClass']:
		path = new['univentionSharePath'][0]
		options = [
			'rw' if new.get('univentionShareWriteable', [''])[0] == 'yes' else 'ro',
			'root_squash' if new.get('univentionShareNFSRootSquash', [''])[0] == 'yes' else 'no_root_squash',
			'async' if new.get('univentionShareNFSSync', [''])[0] == 'async' else 'sync',
			'subtree_check' if new.get('univentionShareNFSSubTree', [''])[0] == 'yes' else 'no_subtree_check',
		] + new.get('univentionShareNFSCustomSetting', [])
		lines.append('%s -%s %s # LDAP:%s' % (
			_exports_escape(path),
			_quote(','.join(options)),
			_quote(' '.join(new.get('univentionShareNFSAllowed', ['*']))),
			_quote(dn)
		))

		_write(lines)

		listener.setuid(0)
		try:
			# object was renamed
			if not old and oldObject and command == "a":
				old = oldObject
			ret = univention.lib.listenerSharePath.createOrRename(old, new, listener.configRegistry)
			if ret:
				univention.debug.debug(
					univention.debug.LISTENER, univention.debug.ERROR,
					"%s: rename/create of sharePath for %s failed (%s)" % (name, dn, ret))
		finally:
			listener.unsetuid()
	else:
		_write(lines)


def clean():
	# clear exports file
	lines = _read(lambda match: not match)
	_write(lines)


def _read(keep=lambda match: True):
	with open(__exports) as fp:
		return [line.strip() for line in fp if keep(__comment_pattern.match(line))]


def _write(lines):
	listener.setuid(0)
	try:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, 'Writing /etc/exports with %d lines' % (len(lines),))
		with open(__exports, 'w') as fp:
			fp.write('\n'.join(lines) + '\n')
	finally:
		listener.unsetuid()


def _exports_escape(text):
	r"""
	Escape path for /etc/exports.

	According to nfs-utils/support/nfs/xio.c:82 xgettok().
	Bug in parser: r'\134042' double-unescaped '\'

	>>> _exports_escape('foo')
	'"foo"'
	>>> _exports_escape('a b')
	'"a b"'
	>>> _exports_escape('a"b')
	'"a\\042b"'
	"""
	return '"%s"' % (''.join(r'\%03o' % (ord(c),) if c < ' ' or c == '"' else c for c in text),)


def _quote(text):
	return _exports_escape(text)[1:-1]


def postrun():
	listener.run('/bin/systemctl', ['systemctl', 'reload-or-restart', 'nfs-kernel-server.service'], uid=0)
