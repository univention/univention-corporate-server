#!/bin/sh
#
# Univention Installer
#  setup udev rules for network interface
#
# Copyright (C) 2008-2009 Univention GmbH
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

. /tmp/installation_profile

UDEVDIR="/instmnt/etc/udev/rules.d"
mkdir -p "$UDEVDIR"
export UDEVRULEFN="${UDEVDIR}/z25_persistent-net.rules"

# if dummy network interface is in use, delete mapping from existing rules file
if [ -f "/tmp/dummy-network-interface.txt" ] ; then
	MACADDR=$(/bin/ifconfig eth0 | grep " HWaddr " | awk "{ print $NF }")
	TMPFN=$(mktemp /tmp/temp.XXXXXXX)
	cat $UDEVRULEFN | grep -v "eth0" | grep -v "$MACADDR" > $TMPFN
	cat $TMPFN > $UDEVRULEFN
fi
