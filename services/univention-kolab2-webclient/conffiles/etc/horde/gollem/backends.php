<?php

@%@BCWARNING=// @%@

@!@
import string

shares = []
for key in baseConfig.keys():
	if key.startswith('horde/webaccess/share/'):
		name = string.join(key.split('/')[0:4], '/')
		if name not in shares:
			shares.append( name )

shares.sort()
for share in shares:
	conf = {}
	conf[ 'port' ]  = 139
	conf[ 'smbclient' ]  = '/usr/bin/smbclient'
	conf[ 'clipboard' ]  = 'false'
	conf[ 'driver' ]  = 'smb'
	for key in baseConfig.keys():
		if key.startswith(share):
			val = key.split( "%s/" % share )[1]
			conf[ val ] = baseConfig[ key ]

	print '$backends["%s"] = array(' % share.split('/')[3]
	if conf.has_key( 'name' ):
		print "'name' => '%s'," % conf[ 'name' ]
	elif conf.has_key( 'ldapdn' ):
		print "'name' => '%s'," % conf[ 'ldapdn' ]
	else:
		print "'name' => '%s'," % key.split('/')[3]
	print "'driver' => '%s'," % conf[ 'driver' ]
	print "'preferred' => '',"
	if conf.has_key('hordeauth'):
		print "'hordeauth' => '%s'," % conf[ 'hordeauth' ]
	elif baseConfig.get('horde/auth', 'kolab') == 'kolab':
		print "'hordeauth' => 'mappedUser',"
	else:
		print "'hordeauth' => 'true',"
	print "'params' => array("
 	print "'hostspec' => '%s'," % conf[ 'hostspec' ]
 	print "'port' => %s," % conf[ 'port' ]
	if conf.has_key( 'share' ):
 		print "'share' => '%s'," % conf[ 'share']
 	print "'smbclient' => '%s'," % conf[ 'smbclient' ]
	if conf.has_key( 'ipaddress' ):
 		print "'ipaddress' => '%s'," % conf[ 'ipaddress' ]
	print "),"

	print "'loginparams' => array(),"
	print "'clipboard' => false,"
	print "'attributes' => array('type', 'name', 'download', 'modified', 'size')"
	print ');'

if len(shares) < 1:
	print '$backends = array();'
@!@
	

