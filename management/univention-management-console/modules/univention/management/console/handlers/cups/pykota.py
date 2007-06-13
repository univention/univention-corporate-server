#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages pykota
#
# Copyright (C) 2007 Univention GmbH
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
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import re, copy
import notifier.popen
import univention.debug as ud
import univention.management.console as umc

_ = umc.Translation( 'univention.management.console.handlers.cups' ).translate

class PrinterQuotaUser( object ):
	def __init__( self, data ):
		datacopy = copy.deepcopy(data)
		for key in [ 'user', 'overcharge', 'pagecounter', 'softlimit', 'hardlimit', 'balance', 'datelimit', 'lifetimepagecounter', 'lifetimepaid', 'warncounter' ]:
			if datacopy.has_key(key):
				self.__dict__[key] = datacopy[key]
			else:
				self.__dict__[key] = ''

class PrinterQuotaStatus( object ):
	def __init__( self, data ):
		datacopy = copy.deepcopy(data)
		for key in [ 'printername', 'gracetime', 'jobprice', 'pageprice', 'totalpages', 'totalpaid', 'realpages', 'userlist', 'grouplist' ]:
			if datacopy.has_key(key):
				self.__dict__[key] = datacopy[key]
			else:
				self.__dict__[key] = ''

#
# printernamelist ==> [ string, ... ]
# callback ==> callback( status, [ PrinterQuotaStatus, ... ] )
#
def _pykota_get_quota_users( printernamelist, callback ):
	cmd = 'LC_ALL="C" LANG="C" /usr/bin/repykota -P%s' % ','.join(printernamelist)

	ud.debug( ud.ADMIN, ud.INFO, 'CUPS.quota command: %s' % cmd )
	proc = notifier.popen.Shell( cmd, stdout = True )
	cb = notifier.Callback( _pykota_get_quota_users_return, callback )
	proc.signal_connect( 'finished', cb )
	proc.start()

def _pykota_get_quota_users_return( pid, status, buffer, callback ):
	result = []

	re_printername = re.compile( '.*?on printer (?P<printername>.*?) \(.*?\)' )
	re_gracetime = re.compile( '^Pages grace time: (?P<gracetime>[0-9]+ days)' )
	re_jobprice = re.compile( '^Price per job: (?P<jobprice>[.0-9]+)' )
	re_pageprice = re.compile( '^Price per page: (?P<pageprice>[.0-9]+)' )
	re_userquota = re.compile( '^(?P<user>[^ ]+) +[+-Q]+ +(?P<overcharge>[.0-9]+) +(?P<pagecounter>[0-9]+) +(?P<softlimit>([0-9]+|None)) +(?P<hardlimit>([0-9]+|None)) +(?P<balance>[.0-9]+) +(?P<datelimit>[\S]+)? +(?P<lifetimepagecounter>[0-9]+) +(?P<lifetimepaid>[.0-9]+) +(?P<warncount>[0-9]+)' )
	re_total = re.compile( '^ *Total : *(?P<totalpages>[0-9]+) *(?P<totalpaid>[.0-9]+) *' )
	re_real = re.compile( '^ *Real : *(?P<realpages>([0-9]+|unknown))' )

	usrinfo = []
	prninfo = { }

	for line in buffer:
		if len(line) == 0:
			if prninfo.has_key('printername'):
				prninfo['userlist'] = usrinfo
				result.append( PrinterQuotaStatus( prninfo ) )
				usrinfo = []
				prninfo = { }

		# match user quota regex
		matches = re_userquota.match(line)
		if matches:
			grps = matches.groupdict()
			usrinfo.append( PrinterQuotaUser(grps) )
			continue

		# match other regex
		for regex in [ re_printername, re_gracetime, re_jobprice, re_pageprice, re_total, re_real ]:
			matches = regex.match(line)
			if matches:
				for key in matches.groupdict().keys():
					prninfo[key] = matches.groupdict()[key]
					continue


	callback( status, result )

#
# printers: may be unset ==> all printers
# userlist: may be unset ==> all users
# softlimit: number of pages
# hardlimit: number of pages
# lifetimecounter: number of pages
# balance: <float>      set balance to <float>
#          +<float>     increase balance by <float>
#          -<float>     decrease balance by <float>
# userlist: [ user, ... ]
# overcharge: <float>   set overcharge to <float>
# reset: yes            resets pagecounter on all / specified printer
# hardreset: yes        resets pagecounter and lifetimecounter on all / specified printer
#
def _pykota_set_quota( callback, **kwargs ):
	cmd = '/usr/bin/edpykota '

	# check for boolean arguments
	for arg in [ 'add', 'delete', 'reset', 'hardreset' ]:
		if kwargs.has_key( arg ) and kwargs[ arg ] == True:
			cmd += '--%s ' % arg

	if kwargs.has_key('printers') and kwargs['printers']:
		cmd += '--printer %s ' % ','.join(kwargs['printers'])

	if kwargs.has_key('softlimit') and kwargs['softlimit']:
		cmd += '-S %s ' % kwargs['softlimit']

	if kwargs.has_key('hardlimit') and kwargs['hardlimit']:
		cmd += '-H %s ' % kwargs['hardlimit']

	if kwargs.has_key('lifetimecounter') and kwargs['lifetimecounter']:
		cmd += '--used %s ' % kwargs['lifetimecounter']

	if kwargs.has_key('balance') and kwargs['balance']:
		cmd += '--balance %s ' % str(kwargs['balance'])

	if kwargs.has_key('balance') and kwargs['balance']:
		cmd += '--overcharge %s ' % str(kwargs['balance'])

	if kwargs.has_key('userlist') and kwargs['userlist']:
		cmd += ' %s ' % ' '.join(kwargs['userlist'])

	ud.debug( ud.ADMIN, ud.PROCESS, 'run: %s' % cmd )
	proc = notifier.popen.RunIt( cmd )
	proc.signal_connect( 'finished', callback )
	proc.start()
