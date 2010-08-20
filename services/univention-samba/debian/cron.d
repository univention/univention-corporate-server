SHELL=/bin/sh
PATH=/sbin:/bin:/usr/sbin:/usr/bin

30 * * * * root /usr/sbin/jitter 600 /usr/share/univention-samba/slave-sync >>/var/log/univention/samba-sync.log 2>&1

