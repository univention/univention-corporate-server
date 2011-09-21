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

# print variable if set
def setVar(phpName, ucrName):
	if baseConfig.get(ucrName):
		print phpName + " = %s;" % baseConfig[ucrName]

# db
setVar("$conf['sql']['persistent']", "horde/sql/persistent")
setVar("$conf['sql']['username']", "horde/sql/username")
setVar("$conf['sql']['hostspec']", "horde/sql/hostspec")
setVar("$conf['sql']['port']", "horde/sql/port")
setVar("$conf['sql']['protocol']", "horde/sql/protocol")
setVar("$conf['sql']['database']", "horde/sql/database")
setVar("$conf['sql']['charset']", "horde/sql/charset")
setVar("$conf['sql']['splitread']", "horde/sql/splitread")
setVar("$conf['sql']['phptype']", "horde/sql/phptype")
print "$conf['sql']['password'] = '%s';" % passwd

# mailer
setVar("$conf['mailer']['type']", "horde/mailer/type")
setVar("$conf['mailer']['params']['host']", "horde/mailer/params/host")
setVar("$conf['mailer']['params']['port']", "horde/mailer/params/port")
setVar("$conf['mailer']['params']['auth']", "horde/mailer/params/auth")

# auth
setVar("$conf['auth']['params']['app']", "horde/auth/params/app")
setVar("$conf['auth']['driver']", "horde/auth/driver")

# misc
setVar("$conf['auth']['admins']", "horde/auth/admins")
setVar("$conf['testdisable']", "horde/testdisable")

# logging
setVar("$conf['log']['enabled']", "horde/log/enabled")
setVar("$conf['log']['type']", "horde/log/type")
setVar("$conf['log']['priority']", "horde/log/priority")
setVar("$conf['log']['name']", "horde/log/name")
setVar("$conf['log']['params']['append']", "horde/log/params/append")
@!@

