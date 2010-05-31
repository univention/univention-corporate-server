#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager Daemon
#  python module
#
# Copyright (C) 2010 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA

__all__ = ['_', 'TranslatableException']

import gettext
N_ = lambda msg: msg
_ = gettext.translation('univention-virtual-machine-manager', fallback=True).ugettext

class TranslatableException(Exception):
	"""Translatable exception (translatable_text, dict, key=value)."""

	def __init__(self, translatable_text, dict={}, **args):
		if isinstance(translatable_text, TranslatableException):
			translatable_text, dict2 = translatable_text.args
			dict2.update(dict)
			dict = dict2
		dict.update(args)
		Exception.__init__(self, translatable_text, dict)

	def __str__(self):
		translatable_text, dict = self.args
		return translatable_text % dict

	@property
	def translatable_text(self):
		return self.args[0]

	@property
	def dict(self):
		return self.args[1]
