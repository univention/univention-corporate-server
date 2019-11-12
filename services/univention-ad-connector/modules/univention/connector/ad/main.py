#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  the main start script
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


from __future__ import print_function
import imp
import sys
import string
import fcntl
import os
import time
import signal
from optparse import OptionParser

import ldap
import traceback
import univention
import univention.connector
import univention.connector.ad

from univention.config_registry import ConfigRegistry

# parse commandline options

parser = OptionParser()
parser.add_option(
	"--configbasename", dest="configbasename",
	help="", metavar="CONFIGBASENAME", default="connector")
parser.add_option('-n', '--no-daemon', dest='daemonize', default=True, action='store_false', help='Start process in foreground')
(options, args) = parser.parse_args()

CONFIGBASENAME = "connector"
if options.configbasename:
	CONFIGBASENAME = options.configbasename
STATUSLOGFILE = "/var/log/univention/%s-status.log" % CONFIGBASENAME

mapping = imp.load_source('mapping', '/etc/univention/%s/ad/mapping.py' % CONFIGBASENAME)


def bind_stdout():
	if options.daemonize:
		sys.stdout = open(STATUSLOGFILE, 'w+')
	return sys.stdout


def daemon(lock_file):
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
			pf = open('/var/run/univention-ad-%s' % CONFIGBASENAME, 'w+')
			pf.write(str(pid))
			pf.close()
			os._exit(0)
	else:
		os._exit(0)

	try:
		maxfd = os.sysconf("SC_OPEN_MAX")
	except (AttributeError, ValueError):
		maxfd = 256       # default maximum

	for fd in range(0, maxfd):
		if fd == lock_file.fileno():
			continue
		try:
			os.close(fd)
		except OSError:   # ERROR (ignore)
			pass

	os.open("/dev/null", os.O_RDONLY)
	os.open("/dev/null", os.O_RDWR)
	os.open("/dev/null", os.O_RDWR)


def connect():
	print(time.ctime())

	baseConfig = ConfigRegistry()
	baseConfig.load()

	if '%s/ad/ldap/host' % CONFIGBASENAME not in baseConfig:
		print('%s/ad/ldap/host not set' % CONFIGBASENAME)
		sys.exit(1)
	if '%s/ad/ldap/port' % CONFIGBASENAME not in baseConfig:
		print('%s/ad/ldap/port not set' % CONFIGBASENAME)
		sys.exit(1)
	if '%s/ad/ldap/base' % CONFIGBASENAME not in baseConfig:
		print('%s/ad/ldap/base not set' % CONFIGBASENAME)
		sys.exit(1)
	if '%s/ad/ldap/binddn' % CONFIGBASENAME not in baseConfig:
		print('%s/ad/ldap/binddn not set' % CONFIGBASENAME)
		sys.exit(1)
	if '%s/ad/ldap/bindpw' % CONFIGBASENAME not in baseConfig:
		print('%s/ad/ldap/bindpw not set' % CONFIGBASENAME)
		sys.exit(1)

	ca_file = baseConfig.get('%s/ad/ldap/certificate' % CONFIGBASENAME)
	if baseConfig.is_true('%s/ad/ldap/ssl' % CONFIGBASENAME, True) or baseConfig.is_true('%s/ad/ldap/ldaps' % CONFIGBASENAME, False):
		if ca_file:
			# create a new CAcert file, which contains the UCS CA and the AD CA,
			# see Bug #17768 for details
			#  https://forge.univention.org/bugzilla/show_bug.cgi?id=17768
			new_ca_filename = '/var/cache/univention-ad-connector/CAcert-%s.pem' % CONFIGBASENAME
			new_ca = open(new_ca_filename, 'w')

			ca = open('/etc/univention/ssl/ucsCA/CAcert.pem', 'r')
			new_ca.write(string.join(ca.readlines(), ''))
			ca.close()

			ca = open(baseConfig['%s/ad/ldap/certificate' % CONFIGBASENAME])
			new_ca.write(string.join(ca.readlines(), ''))
			ca.close()

			new_ca.close()

			ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, new_ca_filename)
		else:
			ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

	if '%s/ad/listener/dir' % CONFIGBASENAME not in baseConfig:
		print('%s/ad/listener/dir not set' % CONFIGBASENAME)
		sys.exit(1)

	if '%s/ad/retryrejected' % CONFIGBASENAME not in baseConfig:
		baseconfig_retry_rejected = 10
	else:
		baseconfig_retry_rejected = baseConfig['%s/ad/retryrejected' % CONFIGBASENAME]

	ad_ldap_bindpw = open(baseConfig['%s/ad/ldap/bindpw' % CONFIGBASENAME]).read()
	if ad_ldap_bindpw[-1] == '\n':
		ad_ldap_bindpw = ad_ldap_bindpw[0:-1]

	poll_sleep = int(baseConfig['%s/ad/poll/sleep' % CONFIGBASENAME])
	ad_init = None
	while not ad_init:
		try:
			ad = univention.connector.ad.ad(
				CONFIGBASENAME,
				mapping.ad_mapping,
				baseConfig,
				baseConfig['%s/ad/ldap/host' % CONFIGBASENAME],
				baseConfig['%s/ad/ldap/port' % CONFIGBASENAME],
				baseConfig['%s/ad/ldap/base' % CONFIGBASENAME],
				baseConfig['%s/ad/ldap/binddn' % CONFIGBASENAME],
				ad_ldap_bindpw,
				baseConfig['%s/ad/ldap/certificate' % CONFIGBASENAME],
				baseConfig['%s/ad/listener/dir' % CONFIGBASENAME]
			)
			ad_init = True
		except ldap.SERVER_DOWN:
			print("Warning: Can't initialize LDAP-Connections, wait...")
			sys.stdout.flush()
			time.sleep(poll_sleep)

	# Initialisierung auf UCS und AD Seite durchfuehren
	ad_init = None
	ucs_init = None

	while not ucs_init:
		try:
			ad.initialize_ucs()
			ucs_init = True
		except ldap.SERVER_DOWN:
			print("Can't contact LDAP server during ucs-poll, sync not possible.")
			sys.stdout.flush()
			time.sleep(poll_sleep)
			ad.open_ad()
			ad.open_ucs()

	while not ad_init:
		try:
			ad.initialize()
			ad_init = True
		except ldap.SERVER_DOWN:
			print("Can't contact LDAP server during ucs-poll, sync not possible.")
			sys.stdout.flush()
			time.sleep(poll_sleep)
			ad.open_ad()
			ad.open_ucs()

	retry_rejected = 0
	connected = True
	while connected:
		print(time.ctime())
		# Aenderungen pollen
		sys.stdout.flush()
		while True:
			# Read changes from OpenLDAP
			try:
				change_counter = ad.poll_ucs()
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
				change_counter = ad.poll()
				if change_counter > 0:
					# AD changes, read again from AD
					retry_rejected = 0
					time.sleep(1)
					continue
				else:
					break
			except ldap.SERVER_DOWN:
				print("Can't contact LDAP server during ad-poll, sync not possible.")
				connected = False
				sys.stdout.flush()
				break

		try:
			if str(retry_rejected) == baseconfig_retry_rejected:
				ad.resync_rejected_ucs()
				ad.resync_rejected()
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
	ad.close_debug()


def lock(filename):
	lock_file = open(filename, "a+")
	fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
	return lock_file


def main():
	try:
		lock_file = lock('/var/lock/univention-ad-%s' % CONFIGBASENAME)
	except IOError:
		print('Error: Another AD connector process is already running.', file=sys.stderr)
		sys.exit(1)

	if options.daemonize:
		daemon(lock_file)
	f = bind_stdout()

	while True:
		try:
			connect()
		except SystemExit:
			lock_file.close()
			raise
		except:
			print(time.ctime())
			print(" --- connect failed, failure was: ---")
			print(traceback.format_exc())
			print(" ---     retry in 30 seconds      ---")
			sys.stdout.flush()
			time.sleep(30)
	lock_file.close()
	f.close()


if __name__ == "__main__":
	main()
