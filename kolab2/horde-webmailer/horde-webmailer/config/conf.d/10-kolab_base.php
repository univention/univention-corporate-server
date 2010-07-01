<?php

$conf['debug_level'] = E_ALL & ~E_DEPRECATED;

$conf['tmpdir'] = dirname(__FILE__) . '/../../../../webclient_data/tmp/';

$conf['sql']['database'] = dirname(__FILE__) . '/../../../../webclient_data/storage/horde.db';
$conf['sql']['mode'] = '0640';
$conf['sql']['charset'] = 'utf-8';
$conf['sql']['phptype'] = 'sqlite';

$conf['auth']['driver'] = 'kolab';
$conf['auth']['params']['login_block'] = false;

$conf['log']['priority'] = PEAR_LOG_WARNING;
$conf['log']['ident'] = 'HORDE';
$conf['log']['params'] = array();
$conf['log']['name'] = dirname(__FILE__) . '/../../../../webclient_data/log/horde.log';
$conf['log']['params']['append'] = true;
$conf['log']['type'] = 'file';
$conf['log']['enabled'] = true;

$conf['prefs']['params']['directory'] = dirname(__FILE__) . '/../../../../webclient_data/storage/';
$conf['prefs']['driver'] = 'file';

$conf['alarms']['params']['driverconfig'] = 'horde';
$conf['alarms']['params']['ttl'] = 300;
$conf['alarms']['driver'] = 'sql';

$conf['group']['driver'] = 'kolab';
$conf['group']['cache'] = true;

$conf['perms']['driverconfig'] = 'horde';
$conf['perms']['driver'] = 'sql';

$conf['share']['cache'] = true;
$conf['share']['driver'] = 'kolab';

$conf['cache']['default_lifetime'] = 1800;
$conf['cache']['params']['dir'] = $conf['tmpdir'];
$conf['cache']['params']['sub'] = 0;
$conf['cache']['driver'] = 'file';

$conf['mailer']['params']['host'] = 'localhost';
$conf['mailer']['params']['port'] = 587;
$conf['mailer']['params']['auth'] = true;
$conf['mailer']['type'] = 'smtp';

$conf['token']['params']['token_dir'] = dirname(__FILE__) . '/../../../../webclient_data/tmp';
$conf['token']['driver'] = 'file';

$conf['vfs']['params']['vfsroot'] = dirname(__FILE__) . '/../../../../webclient_data/storage';
$conf['vfs']['type'] = 'file';

$conf['accounts']['driver'] = 'kolab';
$conf['accounts']['params']['attr'] = 'mail';
$conf['accounts']['params']['strip'] = false;

$conf['kolab']['ldap']['server'] = 'localhost';
$conf['kolab']['ldap']['port'] = 389;
$conf['kolab']['imap']['port'] = 143;
$conf['kolab']['imap']['sieveport'] = 2000;
$conf['kolab']['imap']['cache_folders'] = true;
$conf['kolab']['smtp']['server'] = 'localhost';
$conf['kolab']['smtp']['port'] = 25;
$conf['kolab']['misc']['multidomain'] = false;
$conf['kolab']['cache_folders'] = true;
$conf['kolab']['enabled'] = true;
$conf['kolab']['freebusy']['server'] = 'https://localhost/freebusy';
