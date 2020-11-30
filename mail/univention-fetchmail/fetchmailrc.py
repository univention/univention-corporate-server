#
# Copyright 2004-2021 Univention GmbH
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
# you and Univention.
#
# This program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
#
from __future__ import absolute_import

import listener
import univention.debug as ud
import re
import univention.config_registry
import univention.uldap
import os
from six.moves import cPickle as pickle
try:
	from typing import Dict, Iterable, List, Optional  # noqa F401
except ImportError:
	pass

name = 'fetchmailrc'
description = 'write user-configuration to fetchmailrc'
filter = '(objectClass=univentionFetchmail)'
attributes = []  # type: List[str]

modrdn = "1"

fn_fetchmailrc = '/etc/fetchmailrc'
__initscript = '/etc/init.d/fetchmail'
FETCHMAIL_OLD_PICKLE = "/var/spool/univention-fetchmail/fetchmail_old_dn"


REpassword = re.compile("^poll .*? there with password '(.*?)' is '[^']+' here")


def load_rc(ofile):
	# type: () -> Optional[int]
	"""open an textfile with setuid(0) for root-action"""
	rc = None
	listener.setuid(0)
	try:
		with open(ofile, "r") as fd:
			rc = fd.readlines()
	except EnvironmentError as exc:
		ud.debug(ud.LISTENER, ud.ERROR, 'Failed to open "%s": %s' % (ofile, exc))
	listener.unsetuid()
	return rc


def write_rc(flist, wfile):
	# type: (Iterable[str], str) -> None
	"""write to an textfile with setuid(0) for root-action"""
	listener.setuid(0)
	try:
		with open(wfile, "w") as fd:
			fd.writelines(flist)
	except EnvironmentError as exc:
		ud.debug(ud.LISTENER, ud.ERROR, 'Failed to write to file "%s": %s' % (wfile, exc))
	listener.unsetuid()


def get_pw_from_rc(lines, uid):
	# type: (Iterable[str], int) -> Optional[str]
	"""get current password of a user from fetchmailrc"""
	if not uid:
		return None
	for line in lines:
		line = line.rstrip()
		if line.endswith("#UID='%s'" % uid):
			match = REpassword.match(line)
			if match:
				return match.group(1)
	return None


def objdelete(dlist, old):
	# type: (Iterable[str], Dict[str, List[bytes]]) -> List[str]
	"""delete an object in filerepresenting-list if old settings are found"""
	if old.get('uid'):
		return [line for line in dlist if not re.search("#UID='%s'[ \t]*$" % re.escape(old['uid'][0].decode('UTF-8')), line)]
	else:
		ud.debug(ud.LISTENER, ud.INFO, 'Removal of user in fetchmailrc failed: %r' % old.get('uid'))


def objappend(flist, new, password=None):
	# type: (List[str], Dict[str, List[bytes]], Optional[str]) -> None
	"""add new entry"""
	passwd = password
	if details_complete(new):
		passwd = new.get('univentionFetchmailPasswd', [passwd.encode('UTF-8')])[0].decode('UTF-8')
		flag_ssl = 'ssl' if new.get('univentionFetchmailUseSSL', [b''])[0] == b'1' else ''
		flag_keep = 'keep' if new.get('univentionFetchmailKeepMailOnServer', [b''])[0] == b'1' else 'nokeep'

		flist.append("poll %s with proto %s auth password user '%s' there with password '%s' is '%s' here %s %s #UID='%s'\n" % (
			new['univentionFetchmailServer'][0].decode('UTF-8'),
			new['univentionFetchmailProtocol'][0].decode('UTF-8'),
			new['univentionFetchmailAddress'][0].decode('ASCII'),
			passwd,
			new['mailPrimaryAddress'][0].decode('UTF-8'),
			flag_keep,
			flag_ssl,
			new['uid'][0].decode('UTF-8'),
		))
	else:
		ud.debug(ud.LISTENER, ud.INFO, 'Adding user to "fetchmailrc" failed')


def details_complete(obj, incl_password=False):
	# type: (Optional[Dict[str, List[bytes]]], bool) -> bool
	if not obj:
		return False
	attrlist = ['mailPrimaryAddress', 'univentionFetchmailServer', 'univentionFetchmailProtocol', 'univentionFetchmailAddress']
	if incl_password:
		attrlist.append('univentionFetchmailPasswd')
	return all(obj.get(attr, [b''])[0] for attr in attrlist)


def only_password_reset(old, new):
	# type: (Optional[Dict[str, List[bytes]]], Optional[Dict[str, List[bytes]]]) -> bool
	# if one or both objects are missing ==> false
	if (old and not new) or (not old and new) or (not old and not new):
		return False
	else:
		# if one of the following attributes changed ==> false
		attrlist = ['mailPrimaryAddress', 'univentionFetchmailServer', 'univentionFetchmailProtocol', 'univentionFetchmailAddress']
		for attr in attrlist:
			if old.get(attr) != new.get(attr):
				return False

		# if password hasn't been reset (reset == "old.pw and not new.pw") ==> false
		if not old.get('univentionFetchmailPasswd') or new.get('univentionFetchmailPasswd'):
			return False

	return True


def handler(dn, new, old, command):
	# type: (str, Optional[Dict[str, List[bytes]]], Optional[Dict[str, List[bytes]]], str) -> None
	if os.path.exists(FETCHMAIL_OLD_PICKLE):
		with open(FETCHMAIL_OLD_PICKLE, 'r') as fd:
			p = pickle.Unpickler(fd)
			old = p.load()
		os.unlink(FETCHMAIL_OLD_PICKLE)
	if command == 'r':
		with open(FETCHMAIL_OLD_PICKLE, 'w+') as fd:
			os.chmod(FETCHMAIL_OLD_PICKLE, 0o600)
			p = pickle.Pickler(fd)
			old = p.dump(old)
			p.clear_memo()

	flist = load_rc(fn_fetchmailrc)
	if old and not new and not command == 'r':
		# object has been deleted ==> remove entry from rc file
		flist = objdelete(flist, old)
		write_rc(flist, fn_fetchmailrc)

	elif old and new and details_complete(old) and not details_complete(new):
		# data is now incomplete ==> remove entry from rc file
		flist = objdelete(flist, old)
		write_rc(flist, fn_fetchmailrc)

	elif new and details_complete(new):
		# obj has been created or modified
		passwd = None
		if old:
			# old exists ==> object has been modified ==> get old password and remove object entry from rc file
			passwd = get_pw_from_rc(flist, old['uid'][0].decode('UTF-8'))
			flist = objdelete(flist, old)

		if not details_complete(new, incl_password=True):
			if only_password_reset(old, new):
				ud.debug(ud.LISTENER, ud.INFO, 'fetchmail: password has been reset - nothing to do')
				# only password has been reset ==> nothing to do
				return

			# new obj does not contain password
			if passwd:
				# passwd has been set in old ==> use old password
				ud.debug(ud.LISTENER, ud.INFO, 'fetchmail: using old password')
				objappend(flist, new, passwd)
				write_rc(flist, fn_fetchmailrc)
			else:
				ud.debug(ud.LISTENER, ud.ERROR, 'fetchmail: user "%s": no password set in old and new' % new['uid'][0])
		else:
			# new obj contains password ==> use new password
			objappend(flist, new)
			write_rc(flist, fn_fetchmailrc)

			ud.debug(ud.LISTENER, ud.INFO, 'fetchmail: using new password')

			configRegistry = univention.config_registry.ConfigRegistry()
			configRegistry.load()

			listener.setuid(0)
			try:
				lo = univention.uldap.getMachineConnection()
				modlist = [('univentionFetchmailPasswd', new['univentionFetchmailPasswd'][0], b"")]
				lo.modify(dn, modlist)
				ud.debug(ud.LISTENER, ud.INFO, 'fetchmail: reset password successfully')
			except Exception as exc:
				ud.debug(ud.LISTENER, ud.ERROR, 'fetchmail: cannot reset password in LDAP (%s): %s' % (dn, exc))
			finally:
				listener.unsetuid()


def postrun():
	# type: () -> None
	global __initscript
	initscript = __initscript
	ud.debug(ud.LISTENER, ud.INFO, 'Restarting fetchmail-daemon')
	listener.setuid(0)
	try:
		listener.run(initscript, ['fetchmail', 'restart'], uid=0)
	finally:
		listener.unsetuid()
