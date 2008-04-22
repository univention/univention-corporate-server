#!/bin/sh
#
# Univention Check Printers
#  script monitoring local printers and re-activates stopped printers
#
# Copyright (C) 2006, 2007, 2008 Univention GmbH
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

disabled=''

eval `/usr/sbin/univention-config-registry shell cups/checkprinters/mail/subject cups/checkprinters/mail/address`

# search disabled printers
for printer in $(lpstat -a | sed 's/ .*//'); do
	if ! /usr/sbin/lpc status $printer | grep 'printing is enabled' &>/dev/null ; then
		disabled="$disabled $printer"
	fi
done

# send report mail for disabled printers
if [ -n "$disabled" ]; then
	(
		for printer in $disabled; do
			/usr/bin/lpq -P $printer
			echo
		done
	) | mail -s "$cups_checkprinters_mail_subject" "$cups_checkprinters_mail_address"
	# re-enable the printers
	for printer in $disabled; do
		/usr/bin/univention-cups-enable $printer &>/dev/null
	done
fi

exit 0
