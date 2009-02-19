# -*- coding: utf-8 -*-
#
# Univention Webui
#  waitdialog.py
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

import os
import sys
import time
import ldap
import string
import re

import unimodule
from uniparts import *
from localwebui import _

def create(a,b,c):
	return waitdialog(a,b,c)

def myrgroup():
	return ""

def mywgroup():
	return ""

class waitdialog(unimodule.unimodule):
	def mytype(self):
		return "waitdialog"

	def myinit(self):
		self.save=self.parent.save

		msg = ''
		if hasattr(self.pending_dialog, 'waitmessage'):
			msg = self.pending_dialog.waitmessage()
		if not msg:
			msg = _('The operation is in progress. Please wait.')

		self.subobjs.append(text('', {}, {'text': [msg]}))
		self.atts['refresh'] = '500'

class waitstatus(uniconf):
    def mytype(self):
        return "waitstatus"
    def myxmlrepr(self,xmlob,node):
        return xmlob

