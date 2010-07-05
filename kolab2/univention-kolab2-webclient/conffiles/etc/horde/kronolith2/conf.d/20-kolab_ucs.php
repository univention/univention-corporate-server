<?php

@%@BCWARNING=// @%@

// from templates/kronolith-2.3.3/webclient-kronolith-kolab-conf.template
$conf['storage']['default_domain'] = '@%@doaminname@%@';
$conf['reminder']['server_name'] = '@%@hostname@%@.@%@doaminname@%@';
$conf['reminder']['from_addr'] = 'systemmail@@%@domainname@%@';
// The Holidays driver is broken in Kolab Server 2.2.2 and 2.2.3. It needs
// some more work and has been fixed for 2.3 for that reason.
$conf['holidays']['enable'] = false;

// ucs settings
$conf['calendar']['driver'] = 'kolab';
$conf['storage']['freebusy']['protocol'] = 'https';
$conf['storage']['freebusy']['port'] = 443;
$conf['storage']['driver'] = 'kolab';
$conf['metadata']['keywords'] = false;
$conf['autoshare']['shareperms'] = 'none';
$conf['menu']['print'] = true;
$conf['menu']['import_export'] = true;
$conf['menu']['apps'] = array();
@!@
if baseConfig.get('horde/calendar/day/inline_time', 'false') in ['1', 'yes', 'true']:
	print "$conf['calendar']['day']['inline_time'] = true;"
else:
	print "$conf['calendar']['day']['inline_time'] = false;"

if baseConfig.get('horde/calendar/week/inline_time', 'false') in ['1', 'yes', 'true']:
	print "$conf['calendar']['week']['inline_time'] = true;"
else:
	print "$conf['calendar']['week']['inline_time'] = false;"

if baseConfig.get('horde/calendar/edit/save_as_new', 'false') in ['1', 'yes', 'true']:
	print "$conf['calendar']['edit']['save_as_new'] = true;"
else:
	print "$conf['calendar']['edit']['save_as_new'] = false;"

if baseConfig.get('horde/calendar/invitation/send', 'false') in ['1', 'yes', 'true']:
	print "$conf['calendar']['edit']['invitation_send'] = true;"
else:
	print "$conf['calendar']['edit']['invitation_send'] = false;"
@!@

?>
