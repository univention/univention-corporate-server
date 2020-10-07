#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  the main start script
#
# Copyright 2004-2020 Univention GmbH
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


from __future__ import print_function
import os
import signal
import six
import sys
import time
from argparse import ArgumentParser
import fcntl
import traceback
import contextlib

import ldap

import univention
import univention.s4connector
import univention.s4connector.s4

from univention.config_registry import ConfigRegistry


@contextlib.contextmanager
def bind_stdout(options, statuslogfile):
	if options.daemonize:
		with open(statuslogfile, 'w+') as sys.stdout:
			yield
	else:
		yield


def daemon(lock_file, options):
	try:
		pid = os.fork()
	except OSError as e:
		print('Daemon Mode Error: %s' % e.strerror)

	if (pid == 0):
		os.setsid()
		signal.signal(signal.SIGHUP, signal.SIG_IGN)
		try:
			pid = os.fork()
		except OSError as e:
			print('Daemon Mode Error: %s' % e.strerror)
		if (pid == 0):
			os.chdir("/")
			os.umask(0)
		else:
			pf = open('/var/run/univention-s4-%s' % options.configbasename, 'w+')
			pf.write(str(pid))
			pf.close()
			os._exit(0)
	else:
		os._exit(0)

	try:
		maxfd = os.sysconf("SC_OPEN_MAX")
	except (AttributeError, ValueError):
		maxfd = 256  # default maximum

	for fd in range(0, maxfd):
		if fd == lock_file.fileno():
			continue
		try:
			os.close(fd)
		except OSError:  # ERROR (ignore)
			pass

	os.open("/dev/null", os.O_RDONLY)
	os.open("/dev/null", os.O_RDWR)
	os.open("/dev/null", os.O_RDWR)


def connect(options, mapping):
	print(time.ctime())

	ucr = ConfigRegistry()
	ucr.load()

	if '%s/s4/ldap/host' % options.configbasename not in ucr:
		print('%s/s4/ldap/host not set' % options.configbasename)
		sys.exit(1)
	if '%s/s4/ldap/port' % options.configbasename not in ucr:
		print('%s/s4/ldap/port not set' % options.configbasename)
		sys.exit(1)
	if '%s/s4/ldap/base' % options.configbasename not in ucr:
		print('%s/s4/ldap/base not set' % options.configbasename)
		sys.exit(1)

	if '%s/s4/ldap/certificate' % options.configbasename not in ucr and not ('%s/s4/ldap/ssl' % options.configbasename in ucr and ucr['%s/s4/ldap/ssl' % options.configbasename] == 'no'):
		print('%s/s4/ldap/certificate not set' % options.configbasename)
		sys.exit(1)

	if '%s/s4/listener/dir' % options.configbasename not in ucr:
		print('%s/s4/listener/dir not set' % options.configbasename)
		sys.exit(1)

	if '%s/s4/retryrejected' % options.configbasename not in ucr:
		baseconfig_retry_rejected = 10
	else:
		baseconfig_retry_rejected = ucr['%s/s4/retryrejected' % options.configbasename]

	if ucr.get('%s/s4/ldap/bindpw' % options.configbasename) and os.path.exists(ucr['%s/s4/ldap/bindpw' % options.configbasename]):
		s4_ldap_bindpw = open(ucr['%s/s4/ldap/bindpw' % options.configbasename]).read()
		if s4_ldap_bindpw[-1] == '\n':
			s4_ldap_bindpw = s4_ldap_bindpw[0:-1]
	else:
		s4_ldap_bindpw = None

	poll_sleep = int(ucr['%s/s4/poll/sleep' % options.configbasename])
	s4_init = None
	while not s4_init:
		try:
			s4 = univention.s4connector.s4.s4(
				options.configbasename,
				mapping.s4_mapping,
				ucr,
				ucr['%s/s4/ldap/host' % options.configbasename],
				ucr['%s/s4/ldap/port' % options.configbasename],
				ucr['%s/s4/ldap/base' % options.configbasename],
				ucr.get('%s/s4/ldap/binddn' % options.configbasename, None),
				s4_ldap_bindpw,
				ucr['%s/s4/ldap/certificate' % options.configbasename],
				ucr['%s/s4/listener/dir' % options.configbasename]
			)
			s4_init = True
		except ldap.SERVER_DOWN:
			print("Warning: Can't initialize LDAP-Connections, wait...")
			sys.stdout.flush()
			time.sleep(poll_sleep)

	# Initialisierung auf UCS und S4 Seite durchfuehren
	s4_init = None
	ucs_init = None

	while not ucs_init:
		try:
			s4.initialize_ucs()
			ucs_init = True
		except ldap.SERVER_DOWN:
			print("Can't contact LDAP server during ucs-poll, sync not possible.")
			sys.stdout.flush()
			time.sleep(poll_sleep)
			s4.open_s4()
			s4.open_ucs()

	while not s4_init:
		try:
			s4.initialize()
			s4_init = True
		except ldap.SERVER_DOWN:
			print("Can't contact LDAP server during ucs-poll, sync not possible.")
			sys.stdout.flush()
			time.sleep(poll_sleep)
			s4.open_s4()
			s4.open_ucs()

	retry_rejected = 0
	connected = True
	while connected:
		print(time.ctime())
		# Aenderungen pollen
		sys.stdout.flush()
		while True:
			# Read changes from OpenLDAP
			try:
				change_counter = s4.poll_ucs()
				if change_counter > 0:
					# UCS changes, read again from UCS
					retry_rejected = 0
					time.sleep(1)
					continue
				else:
					break
			except ldap.SERVER_DOWN:
				print("Can't contact LDAP server during ucs-poll, sync not possible.")
				connected = False
				sys.stdout.flush()
				break

		while True:
			try:
				change_counter = s4.poll()
				if change_counter > 0:
					# S4 changes, read again from S4
					retry_rejected = 0
					time.sleep(1)
					continue
				else:
					break
			except ldap.SERVER_DOWN:
				print("Can't contact LDAP server during s4-poll, sync not possible.")
				connected = False
				sys.stdout.flush()
				break

		try:
			if str(retry_rejected) == baseconfig_retry_rejected:
				s4.resync_rejected_ucs()
				s4.resync_rejected()
				retry_rejected = 0
			else:
				retry_rejected += 1
		except ldap.SERVER_DOWN:
			print("Can't contact LDAP server during resync rejected, sync not possible.")
			connected = False
			sys.stdout.flush()
			change_counter = 0
			retry_rejected += 1

		print('- sleep %s seconds (%s/%s until resync) -' % (poll_sleep, retry_rejected, baseconfig_retry_rejected))
		sys.stdout.flush()
		time.sleep(poll_sleep)
	s4.close_debug()


@contextlib.contextmanager
def lock(filename):
	try:
		lock_file = open(filename, "a+")
		fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
	except IOError:
		print('Error: Another S4 connector process is already running.', file=sys.stderr)
		sys.exit(1)
	with lock_file as lock_file:
		yield lock_file


def main():
	parser = ArgumentParser()
	parser.add_argument("--configbasename", help="", metavar="CONFIGBASENAME", default="connector")
	parser.add_argument('-n', '--no-daemon', dest='daemonize', default=True, action='store_false', help='Start process in foreground')
	options = parser.parse_args()

	MAPPING_FILENAME = '/etc/univention/%s/s4/mapping.py' % options.configbasename
	if six.PY2:
		import imp
		mapping = imp.load_source('mapping', MAPPING_FILENAME)
	else:
		import importlib.util
		spec = importlib.util.spec_from_file_location(os.path.basename(MAPPING_FILENAME).rsplit('.', 1)[0], MAPPING_FILENAME)
		mapping = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(mapping)

	with lock('/var/lock/univention-s4-%s' % options.configbasename) as lock_file:
		if options.daemonize:
			daemon(lock_file, options)

		with bind_stdout(options, "/var/log/univention/%s-s4-status.log" % options.configbasename):
			while True:
				try:
					connect(options, mapping)
				except Exception:
					print(time.ctime())

					print(" --- connect failed, failure was: ---")
					print(traceback.format_exc())
					print(" ---     retry in 30 seconds      ---")
					sys.stdout.flush()
					time.sleep(30)


if __name__ == "__main__":
	main()
