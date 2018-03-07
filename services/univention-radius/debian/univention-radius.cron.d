SHELL=/bin/sh
PATH=/sbin:/bin:/usr/sbin:/usr/bin

55 5 * * * root (ucr commit /etc/freeradius/3.0/mods-available/ldap && systemctl restart freeradius) > /var/log/univention/univention-freeradius-sync.log

