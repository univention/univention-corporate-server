SHELL=/bin/sh
PATH=/sbin:/bin:/usr/sbin:/usr/bin

55 5 * * * root (ucr commit /etc/freeradius/modules/ldap && /etc/init.d/freeradius restart) > /var/log/univention/univention-freeradius-sync.log

