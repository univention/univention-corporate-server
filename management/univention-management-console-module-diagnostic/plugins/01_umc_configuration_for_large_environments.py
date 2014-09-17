#!/usr/bin/python2.7
## title: UMC configuration for large environments
## description: Checks if the number of objects for any UDM module is beyound the configured maximum for UMC search


import sys
import univention.admin.uldap as uldap
import univention.admin.modules as modules
import univention.config_registry as configRegistry


ucr = configRegistry.ConfigRegistry()
ucr.load()

sizelimit = int(ucr.get('directory/manager/web/sizelimit', '2000'))
exceedingModules = {}

modules.update()

lo = uldap.getMachineConnection()[0]


for moduleID, module in modules.modules.iteritems():
	if not hasattr(module, 'lookup') or hasattr(module, 'superordinate'):
		continue
		
	objectCount = len(module.lookup(None, lo, ''))
	if objectCount > sizelimit:
		exceedingModules[moduleID] = objectCount

print 'Configured UMC search limit: %i\n' % sizelimit

if exceedingModules:
	print 'The following UDM modules exceed the configured UMC search limit:\n' % sizelimit
	for moduleID, count in exceedingModules.iteritems():
		print '%s: %i' % (moduleID, count)
	print 'summary: The number of objects for some UDM modules is higher than the search size limit'
	sys.exit(1)

print 'No UDM modul exceeds the configured UMC search limit'

