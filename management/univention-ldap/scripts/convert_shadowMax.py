#!/usr/bin/python2.4 -OOO

import univention.uldap
import univention_baseconfig


lo = univention.uldap.getAdminConnection()

baseConfig = univention_baseconfig.baseConfig()
baseConfig.load()

searchResult = lo.search( base = baseConfig['ldap/base'], filter = '(&(objectClass=shadowAccount)(shadowLastChange=*)(shadowMax=*))', attr = ['shadowLastChange', 'shadowMax'] )

for dn,attributes in searchResult:
	ml = []
	if attributes.has_key('shadowLastChange') and attributes.has_key('shadowMax'):
		try:
			lastChange = int(attributes['shadowLastChange'][0])
			max = int(attributes['shadowMax'][0])
			if max >= lastChange:
				new_max = max - lastChange
				if new_max == 0:
					ml.append( ('shadowMax', attributes['shadowMax'], []) )
				else:
					ml.append( ('shadowMax', attributes['shadowMax'], [str(new_max)]) )
				lo.modify( dn, ml )
		except:
			pass
			
