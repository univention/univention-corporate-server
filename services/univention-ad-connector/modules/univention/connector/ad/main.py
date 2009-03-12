#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  the main start script
#
# Copyright (C) 2004-2009 Univention GmbH
#
# http://www.univention.de/
# 
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


import sys, string, os, time, signal, shutil

sys.path=['/etc/univention/connector/ad/']+sys.path

import ldap, traceback
import univention
import univention.connector
import univention.connector.ad

import univention_baseconfig

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
			pf=open('/var/run/univention-ad-connector', 'w+')
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

	f=open('/var/log/univention/connector-status.log', 'w+')
	sys.stdout=f
	print time.ctime()

	baseConfig=univention_baseconfig.baseConfig()
	baseConfig.load()

	if not baseConfig.has_key('connector/ad/ldap/host'):
		print 'connector/ad/ldap/host not set'
		f.close()
		sys.exit(1)
	if not baseConfig.has_key('connector/ad/ldap/port'):
		print 'connector/ad/ldap/port not set'
		f.close()
		sys.exit(1)
	if not baseConfig.has_key('connector/ad/ldap/base'):
		print 'connector/ad/ldap/base not set'
		f.close()
		sys.exit(1)
	if not baseConfig.has_key('connector/ad/ldap/binddn'):
		print 'connector/ad/ldap/binddn not set'
		f.close()
		sys.exit(1)
	if not baseConfig.has_key('connector/ad/ldap/bindpw'):
		print 'connector/ad/ldap/bindpw not set'
		f.close()
		sys.exit(1)
	if not baseConfig.has_key('connector/ad/ldap/certificate'):
		print 'connector/ad/ldap/certificate not set'
		f.close()
		sys.exit(1)

	if not baseConfig.has_key('connector/ad/listener/dir'):
		print 'connector/ad/listener/dir not set'
		f.close()
		sys.exit(1)

	if not baseConfig.has_key('connector/ad/retryrejected'):
		baseconfig_retry_rejected=10
	else:
		baseconfig_retry_rejected=baseConfig['connector/ad/retryrejected']

	ad_ldap_bindpw=open(baseConfig['connector/ad/ldap/bindpw']).read()
	if ad_ldap_bindpw[-1] == '\n':
		ad_ldap_bindpw=ad_ldap_bindpw[0:-1]
	
	poll_sleep=int(baseConfig['connector/ad/poll/sleep'])
	ad_init=None
	while not ad_init:
		try:
			ad=univention.connector.ad.ad(	mapping.ad_mapping, baseConfig, baseConfig['connector/ad/ldap/host'], baseConfig['connector/ad/ldap/port'],
											baseConfig['connector/ad/ldap/base'], baseConfig['connector/ad/ldap/binddn'],
											ad_ldap_bindpw, baseConfig['connector/ad/ldap/certificate'], baseConfig['connector/ad/listener/dir'])
			ad_init=True
		except ldap.SERVER_DOWN:
			print "Warning: Can't initialize LDAP-Connections, wait..."
			sys.stdout.flush()
			time.sleep(poll_sleep)
			pass


	# Initialisierung auf UCS und AD Seite durchfuehren
	ad_init=None
	ucs_init=None

	while not ucs_init:
		try:
			ad.initialize_ucs()
			ucs_init=True
		except ldap.SERVER_DOWN:
			time.sleep(poll_sleep)
			pass
	

	while not ad_init:
		try:
			ad.initialize()
			ad_init=True
		except ldap.SERVER_DOWN:
			time.sleep(poll_sleep)
			pass

	f.close()
	retry_rejected=0
	connected = True
	while connected:
		f=open('/var/log/univention/connector-status.log', 'w+')
		sys.stdout=f
		print time.ctime()
		# Aenderungen pollen
		change_counter=1
		while change_counter != 0:
			sys.stdout.flush()
			try:
				change_counter=ad.poll_ucs()			
			except ldap.SERVER_DOWN:
				print "Can't contact LDAP server during ucs-poll, sync not possible."
				connected = False
 				sys.stdout.flush()

			try:
				change_counter+=ad.poll()
			except ldap.SERVER_DOWN:
				print "Can't contact LDAP server during ad-poll, sync not possible."
				connected = False
 				sys.stdout.flush()

			if change_counter > 0:
				retry_rejected=0

		if str(retry_rejected) == baseconfig_retry_rejected:
			ad.resync_rejected_ucs()
			ad.resync_rejected()
			retry_rejected=0
		else:
			retry_rejected+=1

		print '- sleep %s seconds (%s/%s until resync) -'%(poll_sleep, retry_rejected, baseconfig_retry_rejected)
		sys.stdout.flush()
		time.sleep(poll_sleep)
		f.close()
	ad.close_debug()

def main():
	while True:
		try:
			connect()
		except SystemExit:
			raise
		except:
			f=open('/var/log/univention/connector-status.log', 'w+')
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

