#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages a CUPS server
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

from fnmatch import *

import re
import univention.management.console.locales as locales

_ = locales.Translation( 'univention.management.console.handlers.cups' ).translate

def parse_lpstat_v( buffer, printers ):
	regex = re.compile( '^device for (?P<printer>.+?)\: (?P<device>.+)$' )

	for line in buffer:
		matches = regex.match(line)
		if matches:
			items = matches.groupdict()
			if printers.has_key( items['printer'] ):
				if items['device'].startswith('cupspykota:'):
					printers[ items['printer'] ][ 'quotastate' ] = True
				else:
					printers[ items['printer'] ][ 'quotastate' ] = False

	for key in printers.keys():
		if not printers[key].has_key('quotastate'):
			printers[key]['quotastate'] = _( 'inactive' )

	return printers

def parse_lpstat_l( buffer, filter = '*', key = 'printer' ):
	printers = {}
	current = None
	for prt in buffer:
		if not prt:
			continue
		if prt.startswith( 'printer ' ):
			dummy, printer, status = prt.split( ' ', 2 )
			printers[ printer ] = {}
			current = printer
			if not status.startswith( 'disabled' ):
				printers[ printer ][ 'state' ] = _( 'active' )
			else:
				printers[ printer ][ 'state' ] = _( 'inactive' )
			continue

		if not current:
			continue
		prt = prt.strip()
		for attribute in ( 'Description', 'Location' ):
			pattern = '%s:' % attribute
			if prt.startswith( pattern ):
				value = prt[ prt.find( pattern ) + len( pattern )  + 1 : ]
				printers[ printer ][ attribute.lower() ] = unicode( value, 'utf8' )

	filtered = {}
	for printer, attrs in printers.items():
		if key == 'printer' and not fnmatch( printer, filter ):
			continue
		elif attrs.has_key( key ) and not fnmatch( attrs[ key ], filter ):
			continue
		filtered[ printer ] = attrs
	return filtered

def parse_lpstat_o( buffer ):
	jobs = []
	for line in buffer:
		if not line: continue
		job, owner, size, date = line.split( None, 3 )
		job_id = job.split( '-' )[ 1 ]
		jobs.append( ( job_id, owner, size, date ) )

	return jobs
