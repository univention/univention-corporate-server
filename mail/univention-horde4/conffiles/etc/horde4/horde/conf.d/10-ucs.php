<?php

@%@BCWARNING=// @%@

@!@
passwd = ""
try:
	f = open( '/etc/horde.secret', 'r' )
	passwd = f.readlines()[ 0 ][ : -1 ]
	f.close()
except:
	pass

# db
print "$conf['sql']['persistent'] =   %s;" % baseConfig.get("horde/sql/persistent", "true")
print "$conf['sql']['username']   = '%s';" % baseConfig.get("horde/sql/username", "horde")
print "$conf['sql']['hostspec']   = '%s';" % baseConfig.get("horde/sql/hostspec", "localhost")
print "$conf['sql']['port']       =   %s;" % baseConfig.get("horde/sql/port", "5432")
print "$conf['sql']['protocol']   = '%s';" % baseConfig.get("horde/sql/protocol", "tcp")
print "$conf['sql']['database']   = '%s';" % baseConfig.get("horde/sql/database", "hordedb")
print "$conf['sql']['charset']    = '%s';" % baseConfig.get("horde/sql/charset", "utf-8")
print "$conf['sql']['splitread']  =   %s;" % baseConfig.get("horde/sql/splitread", "false")
print "$conf['sql']['phptype']    = '%s';" % baseConfig.get("horde/sql/phptype", "pgsql")
print "$conf['sql']['password']   = '%s';" % passwd

# mailer
print "$conf['mailer']['type']           = '%s';" % baseConfig.get("horde/mailer/type", "smtp")
print "$conf['mailer']['params']['host'] = '%s';" % baseConfig.get("horde/mailer/params/host", "localhost")
print "$conf['mailer']['params']['port'] =   %s;" % baseConfig.get("horde/mailer/params/port", "25")
print "$conf['mailer']['params']['auth'] =   %s;" % baseConfig.get("horde/mailer/params/auth", "true")

# auth
admins = baseConfig.get("horde/auth/admins", "")
admins = "', '".join(admins.split(","))
if admins:
	admins = "'" + admins + "'"
else:
	admins = ""
print "$conf['auth']['admins'] = array(%s);" % admins
print "$conf['auth']['params']['app'] = '%s';" % baseConfig.get("horde/auth/params/app", "imp")
print "$conf['auth']['driver'] = '%s';" % baseConfig.get("horde/auth/driver", "application")

# misc
print "$conf['problems']['email'] = '%s';" % baseConfig.get("horde/problems/mail", "")
print "$conf['testdisable'] = %s;" % baseConfig.get("horde/testdisable", "true")

# logging
print "$conf['log']['enabled']          =   %s;" % baseConfig.get("horde/log/enabled", "true")
print "$conf['log']['type']             = '%s';" % baseConfig.get("horde/log/type", "file")
print "$conf['log']['priority']         =   %s;" % baseConfig.get("horde/log/priority", "LOG_ERR")
print "$conf['log']['name']             = '%s';" % baseConfig.get("horde/log/name", "/var/log/horde/horde.log")
print "$conf['log']['params']['append'] =   %s;" % baseConfig.get("horde/log/params/append", "true")

# driver
print "$conf['group']['driver'] = '%s';" % baseConfig.get("horde/group/driver", "Sql")
print "$conf['share']['driver'] = '%s';" % baseConfig.get("horde/share/driver", "Sqlng")
@!@

