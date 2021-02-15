#!/bin/bash
export TEXTDOMAINDIR=/usr/share/plymouth/themes/ucs/
export TEXTDOMAIN="univention-bootsplash"
i=0                                                                             
while ! plymouth --has-active-vt && [ $i -le 200 ]; do
	sleep "0.2"
	((i++))
done
[ "$1" = "boot" ] && plymouth update --status="univention-splash:status:$(gettext "Starting Univention Management Console Server")"
[ "$1" = "shutdown" ] && plymouth update --status="univention-splash:status:$(gettext "Stopping Univention Management Console Server")"
