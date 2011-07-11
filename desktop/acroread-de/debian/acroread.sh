#!/bin/sh

# ensure that firefox finds the GTK+ printer backends on amd64
if dpkg-architecture -eamd64; then
	export GTK_PATH=/usr/lib32/gtk-2.0
fi

exec /opt/Adobe/Reader9/bin/acroread "$@"
