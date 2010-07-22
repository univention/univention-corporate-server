#!/bin/sh

# Add Xen console
if test -d /proc/xen
then
        cat <<EOF >>/instmnt/etc/inittab
hvc0:2345:respawn:/sbin/getty 38400 hvc0
EOF

echo hvc0 >>/instmnt/etc/securetty
fi 


