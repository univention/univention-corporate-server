#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  main function for the installation interface
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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

# stop curses
def exit():
	stdscr.keypad(0)
	curses.nocbreak()
	curses.echo()
	curses.endwin()
	sys.exit(0)

# defaults
error_log = "/tmp/installation_error.log"
language_file = "/tmp/language"
y_length = 26
x_length = 76
border = 2

# geometry
text_length = y_length - (2 * border) - 4
text_width = x_length - (2 * border) - 2

# get and set language
if os.path.isfile(language_file):
	language = linecache.getline(language_file, 1)
	os.environ['LANGUAGE'] = language

# starting ncurses
stdscr = curses.initscr()
curses.noecho()
curses.curs_set(0)
stdscr.keypad(1)
curses.cbreak()

# colors
curses.start_color()
curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
curses.init_pair(3, curses.COLOR_RED, curses.COLOR_WHITE)

# main windows 
win = curses.newwin(y_length, x_length, border, border)
win.bkgd(curses.color_pair(1))
win.box()
win.addstr(y_length - border , x_length / 2 - 3,"[ OK ]", curses.color_pair(2))

# installation message
if os.path.isfile(error_log):
	win.addstr(2, 2, _("Installation failed!"), curses.color_pair(3))
	win.addstr(3, 2, _("Please restart the computer and try again."), curses.color_pair(3))
	win.addstr(5, 2, _("Installation Log:"))
	for i in xrange(1, text_length):
		line = linecache.getline(error_log, i)
		line = line[:text_width]
		line = line.replace("\n", " ")
		win.addstr(5 + i, 5, line)
else:
	win.addstr(2, 2, _("Installation succeded!"))
	win.addstr(3, 2, _("Please restart the computer."))
stdscr.refresh()
win.refresh()

# wait for user input
while 1:
	c = stdscr.getch()
	# exit if ENTER, F12 oer Space is pressed
	if c == 10 or c == 276 or c == 32: exit()


