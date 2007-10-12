# -*- coding: utf-8 -*-
#
# Univention Configuration Registry
#  config registry module for the network interfaces
#
# Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
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

def interface(var):
	if var.startswith('interfaces/'):
		return var.split('/')[1].replace('_', ':')
	return None

def stop_iface(iface):
	if iface:
		os.system('ifdown %s >/dev/null 2>&1' % iface)

def start_iface(iface):
	if iface:
		os.system('ifup %s' % iface)

def restore_gateway(gateway):
	if gateway:
		os.system('route del default')
		os.system('route add default gw %s' % gateway)

def preinst(baseConfig, changes):
	for iface in set(changes):
		if baseConfig.has_key('interfaces/%s/address'%iface):
			stop_iface(interface(iface))

def postinst(baseConfig, changes):
	for iface in set(changes):
		if baseConfig.has_key('interfaces/%s/address'%iface):
			start_iface(interface(iface))
	restore_gateway(baseConfig.get('gateway'))
