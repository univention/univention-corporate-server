SHELL=/bin/sh
PATH=/sbin:/bin:/usr/sbin:/usr/bin

*/20 * * * * root /usr/share/univention-ssl/ssl-sync >>/var/log/univention/ssl-sync.log 2>&1
