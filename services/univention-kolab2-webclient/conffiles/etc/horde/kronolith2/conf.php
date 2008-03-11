<?php
// Warning: This file is auto-generated and might be overwritten by
//          univention-baseconfig.
//          Please edit the following file instead:
// Warnung: Diese Datei wurde automatisch generiert und kann durch
//          univention-baseconfig überschrieben werden.
//          Bitte bearbeiten Sie an Stelle dessen die folgende Datei:
//
// 	/etc/univention/templates/files/etc/horde/kronolith2/conf.php
//
$conf['calendar']['driver'] = 'kolab';
$conf['storage']['default_domain'] = '@%@doaminname@%@';
$conf['storage']['freebusy']['protocol'] = 'http';
$conf['storage']['freebusy']['port'] = 80;
$conf['storage']['driver'] = 'kolab';
$conf['metadata']['keywords'] = false;
$conf['reminder']['server_name'] = 'localhost';
$conf['reminder']['from_addr'] = 'systemmail@@%@domainname@%@';
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

if baseConfig.get('horde/calendar/workweek/display', 'false') in ['1', 'yes', 'true']:
	print "$conf['calendar']['workweek']['display'] = true;"
else:
	print "$conf['calendar']['workweek']['display'] = false;"

if baseConfig.get('horde/calendar/edit/save_as_new', 'false') in ['1', 'yes', 'true']:
	print "$conf['calendar']['edit']['save_as_new'] = true;"
else:
	print "$conf['calendar']['edit']['save_as_new'] = false;"

if baseConfig.get('horde/calendar/invitation/send', 'false') in ['1', 'yes', 'true']:
	print "$conf['calendar']['invitation']['send'] = true;"
else:
	print "$conf['calendar']['invitation']['send'] = false;"
@!@
