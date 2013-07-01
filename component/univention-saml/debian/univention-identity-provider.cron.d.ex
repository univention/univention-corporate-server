#
# Regular cron jobs for the univention-identity-provider package
#
0 4	* * *	root	[ -x /usr/bin/univention-identity-provider_maintenance ] && /usr/bin/univention-identity-provider_maintenance
