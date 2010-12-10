<?php

@%@BCWARNING=// @%@

@!@
if baseConfig.get('horde/debug/level') == 'PEAR_LOG_DEBUG':
	print 'ini_set("display_errors", 1);'
@!@
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
// overrride setting defined in /usr/share/horde3/lib/core.php
session_save_path('/var/cache/horde');
@!@
if baseConfig.has_key('horde/servername'):
	print "$conf['cookie']['domain'] = '%s';" % baseConfig['horde/servername']
else:
	print "$conf['cookie']['domain'] = $_SERVER['SERVER_NAME'];"
@!@
$conf['sql']['persistent'] = true;
$conf['sql']['username'] = 'horde';
@!@
if baseConfig.has_key('horde/webroot'):
      print "$conf['cookie']['path'] = '%s';" % baseConfig['horde/webroot']
else:
      print "$conf['cookie']['path'] = '/horde3';"
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
	print "$conf['auth']['params']['port'] = %s;" % baseConfig.get('horde/imapport', '143')
	print "$conf['auth']['params']['protocol'] = '%s';" % baseConfig.get('horde/imapprotocol', 'imap/tls/novalidate-cert')
	print "$conf['auth']['params']['imapconfig'] = 'separate';"
	print "$conf['auth']['params']['app'] = 'imp';"
	print "$conf['auth']['driver'] = 'application';"
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
$conf['kolab']['ldap']['phpdn'] = '';
$conf['kolab']['ldap']['phppw'] = '';
$conf['signup']['allow'] = false;
$conf['log']['priority'] = @%@horde/debug/level@%@;
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
$conf['group']['params']['attrisdn'] = false;
$conf['group']['params']['newgroup_objectclass'] = array('posixGroup', 'univentionGroup');
$conf['group']['params']['objectclass'] = array('posixGroup');
$conf['group']['params']['filter_type'] = 'objectclass';
$conf['group']['driver'] = 'ldap';
$conf['cache']['default_lifetime'] = 1800;
$conf['cache']['params']['dir'] = '/var/cache/horde';
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
	mailer_port = baseConfig.get('horde/mailer/smtp/port', '25')
	if baseConfig.get("horde/imapserver"):
		mailer_host = baseConfig.get('horde/mailer/smtp/host', baseConfig.get("horde/imapserver"))
	else:
		mailer_host = baseConfig.get('horde/mailer/smtp/host', '%s.%s' %(baseConfig['hostname'], baseConfig['domainname']))
	mailer_name = baseConfig.get('horde/mailer/smtp/name', '%s.%s' %(baseConfig['hostname'], baseConfig['domainname']))
	if mailer_port == '465':
		print "$conf['mailer']['params']['host'] = 'ssl://%s';" % mailer_host
	else:
		print "$conf['mailer']['params']['host'] = '%s';" % mailer_host

	print "$conf['mailer']['params']['port'] = '%s';" % mailer_port
	print "$conf['mailer']['params']['name'] = '%s';" % mailer_name

	mailer_auth = baseConfig.get('horde/mailer/smtp/auth', 'PLAIN') # [ 'DIGEST-MD5', 'CRAM-MD5', 'LOGIN', 'PLAIN' ]:
	if mailer_auth.lower() in [ 'false', 'no', '0' ]:
		print "$conf['mailer']['params']['auth'] = '0';"
	elif mailer_auth.lower() in [ 'true', 'yes', '1' ]:
		print "$conf['mailer']['params']['auth'] = 'PLAIN';"
	else:
		print "$conf['mailer']['params']['auth'] = '%s';" % mailer_auth.upper()

@!@
$conf['mailformat']['brokenrfc2231'] = false;
$conf['tmpdir'] = '/var/cache/horde';
$conf['vfs']['params']['vfsroot'] = '/var/cache/horde';
$conf['vfs']['type'] = 'file';
$conf['sessionhandler']['type'] = 'none';
$conf['image']['convert'] = '/usr/bin/convert';
$conf['mime']['magic_db'] = '/etc/magic';
$conf['problems']['email'] = '@%@mail/alias/webmaster@%@';
$conf['problems']['tickets'] = false;
$conf['menu']['apps'] = array();
$conf['menu']['always'] = false;
$conf['menu']['options_in_sidebar'] = true;
$conf['menu']['links']['help'] = 'all';
$conf['menu']['links']['help_about'] = true;
$conf['menu']['links']['options'] = 'authenticated';
@!@
if baseConfig.has_key('horde/menu/options') and baseConfig['horde/menu/options'] in ['0', 'false', 'no' ]:
	print "$conf['menu']['options'] = false;"

if baseConfig.get('horde/menu/options_in_sidebar','true').lower() in ['0', 'false', 'no' ]:
	print "$conf['menu']['options_in_sidebar'] = false;"

if baseConfig.has_key('horde/menu/save_state') and baseConfig['horde/menu/save_state'] in ['0', 'false', 'no' ]:
	print "$conf['menu']['save_state'] = false;"
else:
	print "$conf['menu']['save_state'] = true;"
@!@
$conf['menu']['links']['problem'] = 'all';
$conf['menu']['links']['login'] = 'all';
$conf['menu']['links']['logout'] = 'authenticated';
$conf['hooks']['permsdenied'] = true;
$conf['hooks']['username'] = true;
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
	print "$conf['kolab']['imap']['port'] = %s;" % baseConfig.get('horde/imapport', '143')
	print "$conf['kolab']['imap']['protocol'] = '%s';" % baseConfig.get('horde/imapprotocol', 'imap/tls/novalidate-cert')
	print "$conf['kolab']['imap']['sieveport'] = 2000;"
	print "$conf['kolab']['imap']['maildomain'] = '%s';" % res;
	print "$conf['problems']['maildomain'] = '%s';" % res;
	print "$conf['share']['driver'] = 'kolab';"
	print "$conf['share']['no_sharing'] = false;"
	print "$conf['share']['cache'] = true;"
	print "$conf['share']['any_group'] = true;"   
	print "$conf['kolab']['imap']['virtdomains'] = false;"
	print "$conf['kolab']['smtp']['port'] = 25;"
	print "$conf['kolab']['enabled'] = true;"
	print "unset($conf['kolab']['freebusy']['server']);	/* this would override kolabHomeServer */"

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

print "$conf['sync']['notemsg'] = '%s';" % baseConfig.get('horde/sync/notemsg','<DONT CHANGE>')
print "$conf['sync']['notesize'] = %s;" % baseConfig.get('horde/sync/notesize','4000')
print "$conf['sync']['debug'] = %s;" % baseConfig.get('horde/sync/debug','false')
print "$conf['sync']['debugdir'] = '%s';" % baseConfig.get('horde/sync/debugdir','/var/log/horde/sync')

@!@
$conf['urls']['token_lifetime'] = 30;
$conf['urls']['hmac_lifetime'] = 30;
?>
