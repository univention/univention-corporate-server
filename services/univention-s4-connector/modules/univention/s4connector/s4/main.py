#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  the main start script
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


import sys, string, os, time, signal, shutil
from optparse import OptionParser

import ldap, traceback
import univention
import univention.s4connector
import univention.s4connector.s4

import univention_baseconfig

# parse commandline options

parser = OptionParser()
parser.add_option("--configbasename", dest="configbasename",
                  help="", metavar="CONFIGBASENAME", default="connector")
(options, args) = parser.parse_args()

CONFIGBASENAME = "connector"
if options.configbasename:
	CONFIGBASENAME = options.configbasename
STATUSLOGFILE = "/var/log/univention/%s-s4-status.log" % CONFIGBASENAME

sys.path=['/etc/univention/%s/s4/' % CONFIGBASENAME]+sys.path


import mapping


def daemon():
	try:
		pid = os.fork()
	except OSError, e:
		print 'Daemon Mode Error: %s' % e.strerror

	if (pid == 0):
		os.setsid()
		signal.signal(signal.SIGHUP, signal.SIG_IGN)
		try:
			pid = os.fork()
		except OSError, e:
			print 'Daemon Mode Error: %s' % e.strerror
		if (pid == 0):
			os.chdir("/")
			os.umask(0)
		else:
			pf=open('/var/run/univention-s4-%s' % CONFIGBASENAME, 'w+')
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
		try:
			os.close(fd)
		except OSError:   # ERROR (ignore)
			pass

	os.open("/dev/null", os.O_RDONLY)
	os.open("/dev/null", os.O_RDWR)
	os.open("/dev/null", os.O_RDWR)


def connect():

	daemon()

	f=open(STATUSLOGFILE, 'w+')
	sys.stdout=f
	print time.ctime()

	baseConfig=univention_baseconfig.baseConfig()
	baseConfig.load()

	if not baseConfig.has_key('%s/s4/ldap/host' % CONFIGBASENAME):
		print '%s/s4/ldap/host not set' % CONFIGBASENAME
		f.close()
		sys.exit(1)
	if not baseConfig.has_key('%s/s4/ldap/port' % CONFIGBASENAME):
		print '%s/s4/ldap/port not set' % CONFIGBASENAME
		f.close()
		sys.exit(1)
	if not baseConfig.has_key('%s/s4/ldap/base' % CONFIGBASENAME):
		print '%s/s4/ldap/base not set' % CONFIGBASENAME
		f.close()
		sys.exit(1)

	if not baseConfig.has_key('%s/s4/ldap/certificate' % CONFIGBASENAME) and not (baseConfig.has_key('%s/s4/ldap/ssl' % CONFIGBASENAME) and baseConfig['%s/s4/ldap/ssl' % CONFIGBASENAME] == 'no') :
		print '%s/s4/ldap/certificate not set' % CONFIGBASENAME
		f.close()
		sys.exit(1)

	if not baseConfig.has_key('%s/s4/listener/dir' % CONFIGBASENAME):
		print '%s/s4/listener/dir not set' % CONFIGBASENAME
		f.close()
		sys.exit(1)

	if not baseConfig.has_key('%s/s4/retryrejected' % CONFIGBASENAME):
		baseconfig_retry_rejected=10
	else:
		baseconfig_retry_rejected=baseConfig['%s/s4/retryrejected' % CONFIGBASENAME]

	if baseConfig.get('%s/s4/ldap/bindpw' % CONFIGBASENAME) and os.path.exists(baseConfig['%s/s4/ldap/bindpw' % CONFIGBASENAME]):
		s4_ldap_bindpw=open(baseConfig['%s/s4/ldap/bindpw' % CONFIGBASENAME]).read()
		if s4_ldap_bindpw[-1] == '\n':
			s4_ldap_bindpw=s4_ldap_bindpw[0:-1]
	else:
		s4_ldap_bindpw=None
	
	poll_sleep=int(baseConfig['%s/s4/poll/sleep' % CONFIGBASENAME])
	s4_init=None
	while not s4_init:
		try:
			s4=univention.s4connector.s4.s4(	CONFIGBASENAME,
							mapping.s4_mapping,
							baseConfig,
							baseConfig['%s/s4/ldap/host' % CONFIGBASENAME],
							baseConfig['%s/s4/ldap/port' % CONFIGBASENAME],
							baseConfig['%s/s4/ldap/base' % CONFIGBASENAME],
							baseConfig.get('%s/s4/ldap/binddn' % CONFIGBASENAME, None),
							s4_ldap_bindpw,
							baseConfig['%s/s4/ldap/certificate' % CONFIGBASENAME],
							baseConfig['%s/s4/listener/dir' % CONFIGBASENAME])
			s4_init=True
		except ldap.SERVER_DOWN:
			print "Warning: Can't initialize LDAP-Connections, wait..."
			sys.stdout.flush()
			time.sleep(poll_sleep)
			pass


	# Initialisierung auf UCS und S4 Seite durchfuehren
	s4_init=None
	ucs_init=None

	while not ucs_init:
		try:
			s4.initialize_ucs()
			ucs_init=True
		except ldap.SERVER_DOWN:
			print "Can't contact LDAP server during ucs-poll, sync not possible."
 			sys.stdout.flush()
			time.sleep(poll_sleep)
			s4.open_s4()
			s4.open_ucs()
			pass
	

	while not s4_init:
		try:
			s4.initialize()
			s4_init=True
		except ldap.SERVER_DOWN:
			print "Can't contact LDAP server during ucs-poll, sync not possible."
 			sys.stdout.flush()
			time.sleep(poll_sleep)
			s4.open_s4()
			s4.open_ucs()
			pass

	f.close()
	retry_rejected=0
	connected = True
	while connected:
		f=open(STATUSLOGFILE, 'w+')
		sys.stdout=f
		print time.ctime()
		# Aenderungen pollen
		change_counter=1
		while change_counter != 0:
			sys.stdout.flush()
			try:
				change_counter=s4.poll_ucs()			
			except ldap.SERVER_DOWN:
				print "Can't contact LDAP server during ucs-poll, sync not possible."
				connected = False
 				sys.stdout.flush()
				change_counter=0

			try:
				change_counter+=s4.poll()
			except ldap.SERVER_DOWN:
				print "Can't contact LDAP server during s4-poll, sync not possible."
				connected = False
 				sys.stdout.flush()
				change_counter=0

			if change_counter > 0:
				retry_rejected=0

		try:
			if str(retry_rejected) == baseconfig_retry_rejected:
				s4.resync_rejected_ucs()
				s4.resync_rejected()
				retry_rejected=0
			else:
				retry_rejected+=1
		except ldap.SERVER_DOWN:
			print "Can't contact LDAP server during resync rejected, sync not possible."
			connected = False
 			sys.stdout.flush()
			change_counter=0
			retry_rejected+=1

		print '- sleep %s seconds (%s/%s until resync) -'%(poll_sleep, retry_rejected, baseconfig_retry_rejected)
		sys.stdout.flush()
		time.sleep(poll_sleep)
		f.close()
	s4.close_debug()

def main():
	while True:
		try:
			connect()
		except SystemExit:
			raise
		except:
			f=open(STATUSLOGFILE, 'w+')
			sys.stdout=f
			print time.ctime()
			
			text = ''
			exc_info = sys.exc_info()
			lines = apply(traceback.format_exception, exc_info)
			text = text + '\n'
			for line in lines:
				text += line
			print " --- connect failed, failure was: ---"
			print text
			print " ---     retry in 30 seconds      ---"
			sys.stdout.flush()
			time.sleep(30)

			f.close()


if __name__ == "__main__":
	main()

