#!/usr/bin/python2.4
#

import univention.debug2 as ud

ud.init( '/tmp/univention.debug2.log', 0, 0, 1)
ud.set_level( ud.ADMIN, ud.ALL )
ud.set_level( ud.PROCESS, ud.ERROR )
ud.set_level( ud.LISTENER, ud.WARN )
ud.set_level( ud.NETWORK, ud.PROCESS )
ud.set_level( ud.LDAP, ud.INFO )

for lvl in [ ud.ALL, ud.ERROR, ud.WARN, ud.PROCESS, ud.INFO ]:
	for mod in [ ud.ADMIN, ud.PROCESS, ud.LISTENER, ud.NETWORK, ud.LDAP ]:
		ud.debug( mod, lvl, '==> send msg to %s with level %s' % (mod, lvl) )


ud.set_level( ud.ADMIN, ud.ERROR )
ud.debug( ud.ADMIN, ud.ALL, '==> admin all' )
ud.debug( ud.ADMIN, ud.ERROR, '==> admin error' )
ud.debug( ud.ADMIN, ud.WARN, '==> admin warn' )
ud.debug( ud.ADMIN, ud.PROCESS, '==> admin process' )
ud.debug( ud.ADMIN, ud.INFO, '==> admin info' )

ud.set_level( ud.LDAP, ud.INFO )
ud.debug( ud.LDAP, ud.ALL, '==> ldap all' )
ud.debug( ud.LDAP, ud.ERROR, '==> ldap error' )
ud.debug( ud.LDAP, ud.WARN, '==> ldap warn' )
ud.debug( ud.LDAP, ud.PROCESS, '==> ldap process' )
ud.debug( ud.LDAP, ud.INFO, '==> ldap info' )

ud.debug( ud.ADMIN, ud.ALL, '==> adding function' )
_d = ud.function(' my new function ')
ud.debug( ud.ADMIN, ud.ALL, '==> trying to delete function' )
del _d
ud.debug( ud.ADMIN, ud.ALL, '==> function deleted' )

ud.reopen()

ud.set_level( ud.ADMIN, ud.ERROR )
ud.debug( ud.ADMIN, ud.ALL, '==> admin all' )
ud.debug( ud.ADMIN, ud.ERROR, '==> admin error' )
ud.debug( ud.ADMIN, ud.WARN, '==> admin warn' )
ud.debug( ud.ADMIN, ud.PROCESS, '==> admin process' )
ud.debug( ud.ADMIN, ud.INFO, '==> admin info' )

ud.set_level( ud.LDAP, ud.INFO )
ud.debug( ud.LDAP, ud.ALL, '==> ldap all' )
ud.debug( ud.LDAP, ud.ERROR, '==> ldap error' )
ud.debug( ud.LDAP, ud.WARN, '==> ldap warn' )
ud.debug( ud.LDAP, ud.PROCESS, '==> ldap process' )
ud.debug( ud.LDAP, ud.INFO, '==> ldap info' )

ud.debug( ud.ADMIN, ud.ALL, '==> adding function' )
_d = ud.function(' my new function ')
ud.debug( ud.ADMIN, ud.ALL, '==> trying to delete function' )
del _d
ud.debug( ud.ADMIN, ud.ALL, '==> function deleted' )
