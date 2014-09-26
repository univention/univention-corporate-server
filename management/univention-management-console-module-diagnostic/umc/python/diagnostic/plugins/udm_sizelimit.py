#!/usr/bin/python2.7

import univention.admin.uldap as uldap
import univention.admin.modules as modules
import univention.config_registry as configRegistry

from univention.management.console.modules.diagnostic import Warning

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('UMC configuration for large environments: Web-Sizelimit')


def run():
	ucr = configRegistry.ConfigRegistry()
	ucr.load()

	try:
		sizelimit = int(ucr.get('directory/manager/web/sizelimit', '2000'))
	except ValueError:
		sizelimit = 0

	exceeding_modules = {}
	modules.update()
	lo, po = uldap.getMachineConnection()

	for moduleID, module in modules.modules.iteritems():
		if not hasattr(module, 'lookup') or hasattr(module, 'superordinate'):
			continue
			
		try:
			objects = len(module.lookup(None, lo, ''))
		except:
			raise
	
		if objects > sizelimit:
			exceeding_modules[moduleID] = objects

	if True or exceeding_modules:
		umc_modules = [('ucr', '')]
		description = _('The currently configured UMC search limit is %i.\n') % sizelimit
		description += _('The following UDM modules exceed the configured UMC search limit:\n')
		for module, count in exceeding_modules.iteritems():
			umc_modules.append(('udm', module))
			description += '{udm:%s} having %i objects\n' % (module, count)
		description += _('To adjust this please change the UCR variable directory/manager/web/sizelimit to a higher value within the {ucr}.\n')
		raise Warning(description, umc_modules=umc_modules)


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
