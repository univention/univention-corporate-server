<?php
// Warning: This file is auto-generated and might be overwritten by
//          univention-baseconfig.
//          Please edit the following file instead:
// Warnung: Diese Datei wurde automatisch generiert und kann durch
//          univention-baseconfig überschrieben werden.
//          Bitte bearbeiten Sie an Stelle dessen die folgende Datei:
//
// 	/etc/univention/templates/files/etc/horde/horde3/conf.php
//
$conf['debug_level'] = E_ALL;
$conf['max_exec_time'] = 0;
$conf['use_ssl'] = 2;
@!@
horde_auth=baseConfig.get('horde/auth', 'kolab')
if horde_auth.lower() == 'kolab':
	if baseConfig.has_key('horde/servername'):
		print "$conf['server']['name'] = '%s';" % baseConfig['horde/servername']
	else:
		print "$conf['server']['name'] = $_SERVER['SERVER_NAME'];"
@!@
$conf['server']['port'] = $_SERVER['SERVER_PORT'];
$conf['safe_ips'] = array();
$conf['compress_pages'] = true;
$conf['umask'] = 077;
$conf['session']['name'] = 'Horde';
$conf['session']['cache_limiter'] = 'nocache';
$conf['session']['timeout'] = 0;
@!@
if baseConfig.has_key('horde/servername'):
	print "$conf['cookie']['domain'] = '%s';" % baseConfig['horde/servername']
else:
	print "$conf['cookie']['domain'] = $_SERVER['SERVER_NAME'];"
@!@
$conf['cookie']['path'] = '/horde3';
$conf['sql']['persistent'] = true;
$conf['sql']['username'] = 'horde';
@!@
try:
	f = open( '/etc/horde.secret', 'r' )
	passwd = f.readlines()[ 0 ][ : -1 ]
	f.close()
	print "$conf['sql']['password'] = '%s';" % passwd
except:
	print "$conf['sql']['password'] = '';"
	
@!@
$conf['sql']['protocol'] = 'unix';
$conf['sql']['database'] = 'horde';
$conf['sql']['charset'] = 'iso-8859-1';
$conf['sql']['phptype'] = 'pgsql';
$conf['auth']['admins'] = array('Administrator');
$conf['auth']['checkip'] = false;
$conf['auth']['checkbrowser'] = false;
$conf['auth']['alternate_login'] = false;
$conf['auth']['redirect_on_logout'] = false;
@!@
horde_auth=baseConfig.get('horde/auth', 'kolab')
if horde_auth.lower() == 'kolab':
	if baseConfig.has_key("horde/imapserver"):
		print "$conf['auth']['params']['hostspec'] = '%s';"%baseConfig["horde/imapserver"]
	print "$conf['auth']['params']['login_block'] = false;"
	print "$conf['auth']['params']['login_block_count'] = 3;"
	print "$conf['auth']['params']['login_block_time'] = 5;"
	print "$conf['auth']['params']['port'] = 143;"
	print "$conf['auth']['params']['protocol'] = 'imap/notls';"
	print "$conf['auth']['params']['imapconfig'] = 'separate';"
	print "$conf['auth']['driver'] = 'kolab';"
else:
	print "$conf['auth']['params']['hostspec'] = '%s';" % baseConfig['ldap/server/name']
	print "$conf['auth']['params']['basedn'] = '%s';" % baseConfig['ldap/base']
	print "$conf['auth']['params']['version'] = '3';"
	print "$conf['auth']['params']['ad'] = false;"
	print "$conf['auth']['params']['uid'] = 'uid';"
	print "$conf['auth']['params']['encryption'] = 'md5-hex';"
	print "$conf['auth']['params']['newuser_objectclass'] = array('shadowAccount', 'inetOrgPerson');"
	print "$conf['auth']['params']['objectclass'] = array('shadowAccount');"
	print "$conf['auth']['params']['filter_type'] = 'objectclass';"
	print "$conf['auth']['params']['password_expiration'] = 'no';"
	print "$conf['auth']['driver'] = 'ldap';"
@!@
$conf['signup']['allow'] = false;
$conf['log']['priority'] = PEAR_LOG_ERR;
$conf['log']['ident'] = 'HORDE';
$conf['log']['params'] = array();
$conf['log']['name'] = '/var/log/horde/horde3.log';
$conf['log']['params']['append'] = true;
$conf['log']['type'] = 'file';
$conf['log']['enabled'] = true;
$conf['log_accesskeys'] = false;
$conf['prefs']['params']['driverconfig'] = 'horde';
$conf['prefs']['driver'] = 'sql';
$conf['datatree']['params']['driverconfig'] = 'horde';
$conf['datatree']['driver'] = 'sql';
$conf['history']['driver'] = 'sql';
$conf['group']['params']['hostspec'] = '@%@ldap/server/name@%@';
$conf['group']['params']['basedn'] = '@%@ldap/base@%@';
$conf['group']['params']['version'] = '3';
$conf['group']['params']['gid'] = 'cn';
$conf['group']['params']['memberuid'] = 'memberUid';
$conf['group']['params']['isdnattr'] = false;
$conf['group']['params']['newgroup_objectclass'] = array('posixGroup', 'univentionGroup');
$conf['group']['params']['objectclass'] = array('posixGroup');
$conf['group']['params']['filter_type'] = 'objectclass';
$conf['group']['driver'] = 'ldap';
$conf['cache']['default_lifetime'] = 1800;
$conf['cache']['params']['dir'] = Horde::getTempDir();
$conf['cache']['params']['gc'] = 86400;
$conf['cache']['driver'] = 'file';
$conf['token']['driver'] = 'none';
@!@
mailer_is_sendmail = False
if baseConfig.has_key('horde/mailer/type') and baseConfig['horde/mailer/type'].lower() in ['sendmail', 'smtp' ]:
	print "$conf['mailer']['type'] = '%s';" % baseConfig['horde/mailer/type'].lower()
	mailer_is_sendmail = ( baseConfig['horde/mailer/type'].lower() == 'sendmail' )
else:
	print "$conf['mailer']['type'] = 'sendmail';"
	mailer_is_sendmail = True

if mailer_is_sendmail:
	print "$conf['mailer']['params']['sendmail_path'] = '/usr/sbin/sendmail';"
	print "$conf['mailer']['params']['sendmail_args'] = '-oi';"

if not mailer_is_sendmail:
	if baseConfig.has_key('horde/mailer/smtp/host'):
		print "$conf['mailer']['params']['host'] = '%s';" % baseConfig['horde/mailer/smtp/host']
	else:
		print "$conf['mailer']['params']['host'] = 'localhost';"

	if baseConfig.has_key('horde/mailer/smtp/port'):
		print "$conf['mailer']['params']['port'] = %s;" % baseConfig['horde/mailer/smtp/port']
	else:
		print "$conf['mailer']['params']['port'] = 25;"

	if baseConfig.has_key('horde/mailer/smtp/name'):
		print "$conf['mailer']['params']['name'] = '%s';" % baseConfig['horde/mailer/smtp/name']
	else:
		print "$conf['mailer']['params']['name'] = 'localhost';"

	if baseConfig.has_key('horde/mailer/smtp/auth'):
		if baseConfig['horde/mailer/smtp/auth'].lower() in [ 'false', 'no', '0' ]:
			print "$conf['mailer']['params']['auth'] = '0';"
		elif baseConfig['horde/mailer/smtp/auth'].lower() in [ 'true', 'yes', '1' ]:
			print "$conf['mailer']['params']['auth'] = '1';"
		elif baseConfig['horde/mailer/smtp/auth'].upper() in [ 'DIGEST-MD5', 'CRAM-MD5', 'LOGIN', 'PLAIN' ]:
			print "$conf['mailer']['params']['auth'] = '%s';" % baseConfig['horde/mailer/smtp/auth'].upper()
		else:
			print "$conf['mailer']['params']['auth'] = '1';"
	else:
		print "$conf['mailer']['params']['auth'] = '0';"
@!@
$conf['mailformat']['brokenrfc2231'] = false;
$conf['tmpdir'] = '/tmp/';
$conf['vfs']['params']['vfsroot'] = '/tmp';
$conf['vfs']['type'] = 'file';
$conf['sessionhandler']['type'] = 'none';
$conf['image']['convert'] = '/usr/bin/convert';
$conf['mime']['magic_db'] = '/etc/magic';
$conf['problems']['email'] = '@%@mail/alias/webmaster@%@';
$conf['problems']['tickets'] = false;
$conf['menu']['apps'] = array();
$conf['menu']['always'] = false;
$conf['menu']['links']['help'] = 'all';
$conf['menu']['links']['help_about'] = true;
$conf['menu']['links']['options'] = 'authenticated';
@!@
if baseConfig.has_key('horde/menu/options') and baseConfig['horde/menu/options'] in ['0', 'false', 'no' ]:
	print "$conf['menu']['options'] = false;"

if baseConfig.has_key('horde/menu/save_state') and baseConfig['horde/menu/save_state'] in ['0', 'false', 'no' ]:
	print "$conf['menu']['save_state'] = false;"
else:
	print "$conf['menu']['save_state'] = true;"
@!@
$conf['menu']['links']['problem'] = 'all';
$conf['menu']['links']['login'] = 'all';
$conf['menu']['links']['logout'] = 'authenticated';
$conf['hooks']['permsdenied'] = true;
$conf['hooks']['username'] = false;
$conf['hooks']['preauthenticate'] = false;
$conf['hooks']['postauthenticate'] = false;
$conf['hooks']['authldap'] = false;
$conf['portal']['fixed_blocks'] = array();
$conf['accounts']['driver'] = 'null';
$conf['imsp']['enabled'] = false;
$conf['memcache']['enabled'] = false;
@!@
horde_auth=baseConfig.get('horde/auth', 'kolab')
if horde_auth.lower() == 'kolab':
	if baseConfig.has_key("horde/hosteddomain"):
		domains = baseConfig["horde/hosteddomain"]
	elif baseConfig.has_key("mail/hosteddomains"):
		domains = baseConfig["mail/hosteddomains"]
	else:
		domains=baseConfig['domainname']

	if domains.find( ' ' ) != -1:
		res = domains[ : domains.find( ' ' ) ]
	else:
		res = domains

	print "$conf['kolab']['ldap']['server'] = '%s';" % baseConfig['ldap/server/name']
	print "$conf['kolab']['ldap']['port'] = 389;"
	print "$conf['kolab']['ldap']['basedn'] = '%s';" % baseConfig['ldap/base']
	print "$conf['kolab']['ldap']['binddn'] = '';"
	print "$conf['kolab']['ldap']['bindpw'] = '';"
	print "$conf['kolab']['imap']['port'] = 143;"
	print "$conf['kolab']['imap']['sieveport'] = 2000;"
	print "$conf['kolab']['imap']['maildomain'] = '%s';" % res;
	print "$conf['problems']['maildomain'] = '%s';" % res;
	print "$conf['share']['driver'] = 'kolab';"
	print "$conf['share']['no_sharing'] = false;"
	print "$conf['share']['cache'] = true;"
	print "$conf['kolab']['imap']['virtdomains'] = false;"
	print "$conf['kolab']['smtp']['port'] = 25;"
	print "$conf['kolab']['enabled'] = true;"

	fqdn = "%s.%s" % ( baseConfig[ 'hostname' ], baseConfig[ 'domainname' ] )
	print "$conf['sql']['hostspec'] = '%s';" % fqdn

	if baseConfig.has_key("horde/imapserver"):
		print "$conf['kolab']['smtp']['server'] = '%s';" % baseConfig["horde/imapserver"]
		print "$conf['kolab']['imap']['server'] = '%s';" % baseConfig["horde/imapserver"]
		print "$conf['kolab']['server']['fqdn'] = '%s';" % baseConfig["horde/imapserver"]
	else:
		print "$conf['kolab']['smtp']['server'] = '%s';" % fqdn
		print "$conf['kolab']['imap']['server'] = '%s';" % fqdn
		print "$conf['kolab']['server']['fqdn'] = '%s';" % fqdn

if baseConfig.get('horde/menu/hide_groupware','false') in ['1','yes','true']:
	print "$conf['menu']['hide_groupware'] = true;"

@!@
/* CONFIG END. DO NOT CHANGE ANYTHING IN OR BEFORE THIS LINE. */
