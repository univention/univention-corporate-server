<?php

$params = array();
require '/kolab/etc/resmgr/fbview.conf';

/* CONFIG START. DO NOT CHANGE ANYTHING IN OR AFTER THIS LINE. */
// $Horde: horde/config/conf.xml,v 1.40 2004/05/17 08:52:32 jan Exp $
$conf['debug_level'] = E_ALL;
$conf['max_exec_time'] = 0;
$conf['use_ssl'] = 2;
$conf['server']['name'] = $_SERVER['SERVER_NAME'];
$conf['server']['port'] = $_SERVER['SERVER_PORT'];
$conf['compress_pages'] = true;
$conf['umask'] = 077;
$conf['session']['name'] = 'Horde';
$conf['session']['cache_limiter'] = 'nocache';
$conf['session']['timeout'] = 0;
$conf['cookie']['domain'] = $_SERVER['SERVER_NAME'];
$conf['cookie']['path'] = '/fbview';
$conf['kolab']['server'] = $params['server'];
$conf['kolab']['maildomain'] = $params['email_domain'];
$conf['kolab']['basedn'] = $params['base_dn'];
$conf['kolab']['binddn'] = $params['bind_dn'];
$conf['kolab']['bindpw'] = $params['bind_pw'];
/*$conf['kolab']['cyrusadmin'] = 'manager';
$conf['kolab']['cyruspw'] = 'password';*/
$conf['kolab']['virtual_domains'] = $params['virtual_domains'];
$conf['sql']['phptype'] = 'mysql';
$conf['sql']['persistent'] = false;
$conf['sql']['protocol'] = 'unix';
$conf['sql']['hostspec'] = 'localhost';
$conf['sql']['username'] = 'horde';
$conf['sql']['password'] = 'horde';
$conf['sql']['database'] = 'horde';
$conf['sql']['charset'] = 'iso-8859-1';
$conf['auth']['admins'] = array('hordeadmin@oberon.co.za');
$conf['auth']['checkip'] = true;
$conf['auth']['params']['hostspec'] = 'localhost';
$conf['auth']['params']['port'] = 143;
$conf['auth']['params']['protocol'] = 'imap/notls';
$conf['auth']['params']['imapconfig'] = 'separate';
$conf['auth']['driver'] = 'imap';
$conf['signup']['allow'] = false;
$conf['signup']['approve'] = true;
$conf['signup']['preprocess'] = true;
$conf['signup']['queue'] = true;
$conf['log']['priority'] = PEAR_LOG_NOTICE;
$conf['log']['ident'] = 'HORDE';
$conf['log']['params'] = array();
$conf['log']['name'] = '/kolab/var/resmgr/fbview.log';
$conf['log']['params']['append'] = true;
$conf['log']['type'] = 'file';
$conf['log']['enabled'] = true;
$conf['log_accesskeys'] = false;
$conf['prefs']['driver'] = 'session';
$conf['datatree']['params']['driverconfig'] = 'horde';
$conf['datatree']['driver'] = 'null';
$conf['group']['driver'] = 'datatree';
$conf['cache']['default_lifetime'] = 1800;
$conf['cache']['params']['dir'] = Horde::getTempDir();
$conf['cache']['driver'] = 'file';
$conf['token']['driver'] = 'none';
$conf['mailer']['params']['auth'] = false;
$conf['mailer']['type'] = 'smtp';
$conf['vfs']['params']['vfsroot'] = '/tmp';
$conf['vfs']['type'] = 'file';
$conf['sessionhandler']['type'] = 'none';
$conf['problems']['email'] = 'webmaster@example.com';
$conf['user']['online_help'] = true;
$conf['css']['cached'] = true;
$conf['menu']['display'] = false;
$conf['menu']['always'] = false;
$conf['hooks']['username'] = false;
$conf['hooks']['preauthenticate'] = false;
$conf['hooks']['postauthenticate'] = false;
$conf['hooks']['authldap'] = false;
/* CONFIG END. DO NOT CHANGE ANYTHING IN OR BEFORE THIS LINE. */
