#!/bin/sh
#
# Univention Installer
#  configure default locales
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

. /tmp/installation_profile

cat >>/instmnt/defaultlocales.sh <<__EOT__

if [ -n "$locale_default" ]; then
	short_form=`echo $locale_default | cut -c 1-2`

	univention-baseconfig set "locale/default"="$locale_default"

	univention-baseconfig set admin/web/language="\$short_form"
	univention-baseconfig set console/web/language="\$short_form"
	univention-baseconfig set gdm/language="\$locale_default"
fi

__EOT__

chmod +x /instmnt/defaultlocales.sh
chroot /instmnt ./defaultlocales.sh

