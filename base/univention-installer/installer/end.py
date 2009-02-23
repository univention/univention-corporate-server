#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  main function for the installation interface
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
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# Module
import sys
import os
import curses
import curses.ascii
import linecache
from local import _

MAX_HEIGHT = 24
MAX_WIDTH = 78
fn_error_msg = "/tmp/installation_error.log"
fn_success_msg = "/tmp/installation_success.log"
language_file = "/tmp/language"

class MsgWindow(object):
	def __init__(self, msg = [], x = -1, y = -1, border = 2, title = '[ Univention Corporate Server ]'):
		global MAX_HEIGHT, MAX_WIDTH
		# get screen dimension
		self.stdscr = curses.initscr()
		MAX_HEIGHT, MAX_WIDTH = self.stdscr.getmaxyx()

		# determine width and height
		print y
		if y < 0:
			y = len(msg) + 5
		print y

		if x < 0:
			maxx = 0
			for line in msg:
				if len(line) > maxx:
					maxx = len(line)
			x = maxx + (2 * border ) + 4

		# limit width and height
		if y > MAX_HEIGHT:
			y = MAX_HEIGHT
		print y
		print msg
#		sys.exit(0)

		if x < len(title):
			x = len(title) + (2 * border ) + 2
		if x > MAX_WIDTH:
			x = MAX_WIDTH

		self.width = x
		self.height = y
		self.border = border
		self.textwidth = x - (2 * self.border) - 4
		self.textheight = y - 4
		self.msg = msg[:self.textheight]
		self.title = title

		curses.noecho()
		curses.curs_set(0)
		self.stdscr.keypad(1)
		curses.cbreak()

		# colors
		curses.start_color()
		curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
		curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
		curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED)

		# main windows 
		self.win = curses.newwin(y, x, int((MAX_HEIGHT-y)/2), int((MAX_WIDTH-x)/2))
		self.win.bkgd(curses.color_pair(1))
		self.win.box()
		self.win.addstr(0, self.width / 2 - (len(self.title) / 2), self.title, curses.color_pair(1))
		self.win.addstr(self.height - self.border , self.width / 2 - 3,"[ OK ]", curses.color_pair(3))

		i = 2
		for line in self.msg:
			if len(line) > self.textwidth:
				line = line[:self.textwidth]
			try:
				self.win.addstr( i, self.border + 2, line.decode('utf-8').encode('latin-1') )
			except:
				pass
			i += 1

	def run(self):
		self.stdscr.refresh()
		self.win.refresh()

		# wait for user input
		while 1:
			c = self.stdscr.getch()
			# exit if ENTER, F12 or Space is pressed
			if c == 10 or c == 276 or c == 32:
				break

		# stop curses
		self.stdscr.keypad(0)
		curses.nocbreak()
		curses.echo()
		curses.endwin()


def createSuccessMsg():
	profile = {}
	try:
		lines = open('/tmp/installation_profile', 'r').readlines()
		for line in lines:
			try:
				key, val = line.split('=',1)
				val = val.rstrip('\n\r ')[1:-1]
				profile[key] = val
			except:
				pass
	except:
		pass

	msg = []
	msg.append( _('The installation has been finished successfully!') )
	msg.append( '' )

	if profile.get('eth0_ip'):
		msg.append( _('This system has been configured to IP address %s and') % profile.get('eth0_ip') )
	else:
		msg.append( _('This system has been configured for DHCP usage and') )

	if profile.get('auto_join') == 'false':
		msg.append( _('has not been joined to UCS domain yet.') )
	else:
		msg.append( _('has been joined to UCS domain.') )

	msg.append( _('Please remove installation media from drive and' ) )
	msg.append( _('press ok to reboot this system.') )
	msg.append( '' )
	msg.append( _('Administrative frontends:') )

	fqdn = '%s.%s' % (profile.get('hostname'), profile.get('domainname'))
	postfix_udm = 'univention-directory-manager'
	postfix_umc = 'univention-management-console'
	if len(fqdn) > 31:
		postfix_udm = 'udm'
		postfix_umc = 'umc'

	if profile.get('system_role') in [ 'domaincontroller_master', 'domaincontroller_backup' ]:
		msg.append( _(' Univention Directory Manager') )
		msg.append( _('  https://%s/%s/') % (fqdn, postfix_udm) )
		if profile.get('eth0_ip'):
			msg.append( _('  https://%s/%s/') % (profile.get('eth0_ip'), postfix_udm) )
		msg.append( _('  Administrative account name: Administrator') )
		msg.append( '' )
	msg.append( _(' Univention Management Console') )
	msg.append( _('  https://%s/%s/') % (fqdn, postfix_umc) )
	if profile.get('eth0_ip'):
		msg.append( _('  https://%s/%s/') % (profile.get('eth0_ip'), postfix_umc ) )
	msg.append( _('  Administrative account name: Administrator') )
	msg.append( '' )
	msg.append( _('Additional information: http://www.univention.de/dokumentation.html') )

	return msg


def main():
	# get and set language
	if os.path.isfile(language_file):
		language = linecache.getline(language_file, 1).strip('\n')
		os.environ['LANGUAGE'] = language

	msg = []
	# does error message exist?
	if os.path.isfile( fn_error_msg ):
		msg.append( _('Some problems occurred during installation!') )
		msg.append( _('Please read the following error messages carefully.') )
		msg.append( _('In case of doubt a reinstallation might be reasonable.') )
		msg.append( '' )
		try:
			lines = open(fn_error_msg,'r').readlines()
			for line in lines:
				msg.append( line.rstrip('\r\n\t ') )
		except:
			pass

	# does success msg exist?
	elif os.path.isfile( fn_success_msg ):
		msg.append( _('The installation has been finished successfully!') )
		msg.append( '' )
		try:
			lines = open(fn_success_msg,'r').readlines()
			for line in lines:
				msg.append( line.rstrip('\r\n\t ') )
		except:
			pass

	else:
		msg = createSuccessMsg()

	win = MsgWindow( msg )
	win.run()


if __name__ == '__main__':
	main()
	sys.exit(0)
