#!/bin/sh
#
# Univention Thin Client Scanner Support
#  announce scanners to session host (via Univention Session)
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA

# read user info
. /tmp/.univention-thin-client-user-info

eval $(/usr/sbin/univention-baseconfig shell hostname domainname)

# set environment
univention-client-run -f /tmp/univention-client.sock.$USER -m "setenv SCANNER_ACTION $ACTION"
univention-client-run -f /tmp/univention-client.sock.$USER -m "setenv SCANNER_HOST $hostname.$domainname"
# show desktop link
univention-client-run -f /tmp/univention-client.sock.$USER -m "run /usr/sbin/univention-thin-client-scanner"
