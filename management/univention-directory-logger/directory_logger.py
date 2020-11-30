# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#  listener script for directory transaction logging
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
import time
import syslog
import re
import hashlib
import base64
import grp
import subprocess
import os

import univention.debug

name = 'directory_logger'
description = 'Log directory transactions'
filter = '(objectClass=*)'  # log all objects by default
attributes = []

logname = '/var/log/univention/directory-logger.log'
excludeKeyPattern = re.compile('ldap/logging/exclude\d+')
cachename = '/var/lib/univention-directory-logger/cache'
notifier_id = '/var/lib/univention-directory-listener/notifier_id'

headerfmt = '''START\nOld Hash: %s\nDN: %s\nID: %s\nModifier: %s\nTimestamp: %s\nAction: %s\n'''
newtag = '\nNew values:\n'
oldtag = '\nOld values:\n'
endtag = 'END\n'
logmsgfmt = '''DN=%s\nID=%s\nModifier=%s\nTimestamp=%s\nNew Hash=%s\n'''
timestampfmt = '''%d.%m.%Y %H:%M:%S'''
uidNumber = 0
preferedGroup = "adm"
gidNumber = 0  # fallback
filemode = '0640'
cleanupDellog = True  # remove missed dellog entries (after reporting about them)
digest = listener.configRegistry.get('ldap/logging/hash', 'md5')

SAFE_STRING_RE = re.compile(r'^(?:\000|\n|\r| |:|<)|[\000\n\r\200-\377]+|[ ]+$')


def ldapEntry2string(entry):
	# type: (dict) -> str
	return ''.join(
		'%s:: %s\n' % (key, base64.standard_b64encode(value))
		if SAFE_STRING_RE.search(value) else
		'%s: %s\n' % (key, value)
		for key, values in entry.iteritems()
		for value in values
	)


def ldapTime2string(timestamp):
	# type: (str) -> str
	try:
		timestruct = time.strptime(timestamp, "%Y%m%d%H%M%SZ")
	except ValueError:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, '%s: could not parse timestamp %s, expected LDAP format' % (name, timestamp))
		return timestamp  # return it as it was
	return time.strftime(timestampfmt, timestruct)


def filterOutUnchangedAttributes(old_copy, new_copy):
	keylist = old_copy.keys()
	for key in keylist:
		if key not in new_copy:
			continue
		if new_copy[key] == old_copy[key]:
			del old_copy[key]
			del new_copy[key]
			continue
		removelist = []
		for value in old_copy[key]:
			for value2 in new_copy[key]:
				if value == value2:
					removelist.append(value)
					continue
		for value in removelist:
			old_copy[key].remove(value)
			new_copy[key].remove(value)


def process_dellog(dn):
	dellog = listener.configRegistry['ldap/logging/dellogdir']

	dellist = sorted(os.listdir(dellog))
	for filename in dellist:
		pathname = os.path.join(dellog, filename)
		try:
			with open(pathname, 'r') as f:
				(dellog_stamp, dellog_id, dellog_dn, modifier, action) = [line.rstrip() for line in f]

			if cleanupDellog:
				os.unlink(pathname)
		except EnvironmentError:
			continue

		if dellog_dn == dn:
			timestamp = ldapTime2string(dellog_stamp)
			break
	else:
		timestamp = time.strftime(timestampfmt, time.gmtime())
		dellog_id = '<NoID>'
		modifier = '<unknown>'
		action = '<unknown>'

	return (timestamp, dellog_id, modifier, action)


def prefix_record(record, identifier):
	if not listener.configRegistry.is_true('ldap/logging/id-prefix', False):
		return record
	return '\n'.join('ID %s: %s' % (identifier, line) for line in record.splitlines()) + '\n'


def handler(dn, new_copy, old_copy):
	# type: (str, dict, dict) -> None
	if not listener.configRegistry.is_true('ldap/logging'):
		return

	listener.setuid(0)
	try:
		# check for exclusion
		if any(
			value in dn
			for key, value in listener.configRegistry.items()
			if excludeKeyPattern.match(key)
		):
			if not new_copy:  # there should be a dellog entry to remove
				process_dellog(dn)
			# important: don't return a thing, otherwise this dn
			# seems to get excluded from future processing by this module
			return

		# Start processing
		# 1. read previous hash
		if not os.path.exists(cachename):
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, '%s: %s vanished mid-run, stop.' % (name, cachename))
			return  # really bad, stop it.
		cachefile = open(cachename, 'r+')
		previoushash = cachefile.read()

		# get ID
		with open(notifier_id, 'r') as f:
			id = int(f.read()) + 1
		# matches notifier transaction id. Tested for UCS 1.3-2 and 2.0.
		# Note about 1.3-2:
		# For user removal this matches with ++last_id as seen by the dellog overlay,
		# but for user create dellog sees id-1, i.e. last_id has already been incremented before
		# we see it here

		# 2. generate log record
		if new_copy:
			try:
				modifier = new_copy['modifiersName'][0]
			except LookupError:
				modifier = '<unknown>'
			try:
				timestamp = ldapTime2string(new_copy['modifyTimestamp'][0])
			except LookupError:
				timestamp = '<unknown>'

			if not old_copy:  # create branch
				record = headerfmt % (previoushash, dn, id, modifier, timestamp, 'add')
				record += newtag
				record += ldapEntry2string(new_copy)
			else:  # modify branch
				# filter out unchanged attributes
				filterOutUnchangedAttributes(old_copy, new_copy)
				record = headerfmt % (previoushash, dn, id, modifier, timestamp, 'modify')
				record += oldtag
				record += ldapEntry2string(old_copy)
				record += newtag
				record += ldapEntry2string(new_copy)
		else:  # delete branch
			(timestamp, dellog_id, modifier, action) = process_dellog(dn)

			record = headerfmt % (previoushash, dn, id, modifier, timestamp, 'delete')
			record += oldtag
			record += ldapEntry2string(old_copy)
		record += endtag

		# 3. write log file record
		with open(logname, 'a') as logfile:  # append
			logfile.write(prefix_record(record, id))
		# 4. calculate nexthash, omitting the final line break to make validation of the
		#    record more intituive
		nexthash = hashlib.new(digest, record[:-1]).hexdigest()
		# 5. cache nexthash (the actual logfile might be logrotated away..)
		cachefile.seek(0)
		cachefile.write(nexthash)
		cachefile.close()
		# 6. send log message including nexthash
		syslog.openlog(name, 0, syslog.LOG_DAEMON)
		syslog.syslog(syslog.LOG_INFO, logmsgfmt % (dn, id, modifier, timestamp, nexthash))
		syslog.closelog()
	finally:
		listener.unsetuid()


def createFile(filename):
	# type: (str) -> int
	global gidNumber

	if gidNumber == 0:
		try:
			gidNumber = int(grp.getgrnam(preferedGroup)[2])
		except:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, '%s: Failed to get groupID for "%s"' % (name, preferedGroup))
			gidNumber = 0

	basedir = os.path.dirname(filename)
	if not os.path.exists(basedir):
		os.makedirs(basedir)

	if subprocess.call(["/bin/touch", filename]) or not os.path.exists(filename):
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, '%s: %s could not be created.' % (name, filename))
		return 1
	os.chown(filename, uidNumber, gidNumber)
	os.chmod(filename, int(filemode, 0))
	return 0


def initialize():
	# type: () -> None
	timestamp = time.strftime(timestampfmt, time.gmtime())
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'init %s' % name)

	listener.setuid(0)
	try:
		if not os.path.exists(logname):
			createFile(logname)

		if not os.path.exists(cachename):
			createFile(cachename)
		size = os.path.getsize(cachename)
		cachefile = open(cachename, 'r+')

		# generate log record
		if size == 0:
			action = 'Initialize'
			record = 'START\nTimestamp: %s\nAction: %s %s\n' % (timestamp, action, name)
		else:
			# read previous hash
			previoushash = cachefile.read()
			action = 'Reinitialize'
			record = 'START\nOld Hash: %s\nTimestamp: %s\nAction: %s %s\n' % (previoushash, timestamp, action, name)
		record += endtag

		# 3. write log file record
		with open(logname, 'a') as logfile:  # append
			logfile.write(prefix_record(record, 0))
		# 4. calculate initial hash
		nexthash = hashlib.new(digest, record).hexdigest()
		# 5. cache nexthash (the actual logfile might be logrotated away..)
		cachefile.seek(0)
		cachefile.write(nexthash)
		cachefile.close()
		# 6. send log message including nexthash
		syslog.openlog(name, 0, syslog.LOG_DAEMON)
		syslog.syslog(syslog.LOG_INFO, '%s\nTimestamp=%s\nNew Hash=%s' % (action, timestamp, nexthash))
		syslog.closelog()
	finally:
		listener.unsetuid()


# --- initialize on load:
listener.setuid(0)
try:
	if not os.path.exists(logname):
		createFile(logname)
	if not os.path.exists(cachename):
		univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, '%s: %s vanished, creating it' % (name, cachename))
		createFile(cachename)
finally:
	listener.unsetuid()
