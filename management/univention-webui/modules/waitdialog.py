# -*- coding: utf-8 -*-
#
# Univention Webui
#  waitdialog.py
#
# Copyright 2004-2010 Univention GmbH
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

