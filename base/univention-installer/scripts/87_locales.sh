#!/bin/sh
#
# Univention Installer
#  configure locales
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

. /tmp/installation_profile

cat >>/instmnt/locales.sh <<__EOT__

echo "Generating locales (this might take a while)"
locale-gen  >/dev/null 2>&1

__EOT__

chmod +x /instmnt/locales.sh
chroot /instmnt ./locales.sh


cat >>/instmnt/sources2.sh <<__EOT__

apt-get update  >/dev/null 2>&1

__EOT__

chmod +x /instmnt/sources2.sh
chroot /instmnt ./sources2.sh
