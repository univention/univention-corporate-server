#!/usr/bin/python2.7

import psutil

from univention.management.console.modules.diagnostic import Conflict

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Not enough RAM available for running UCS')
umc_modules = [{
	'module': 'top'
}]


def run():
	virtual_memory = psutil.total_virtmem()

	if psutil.TOTAL_PHYMEM < 2000000000:
		description = _('The available physical memory is less than the recommended minimum.\n')
		description += _('It is recommended to have at least 2GB of physical memory to run an UCS system.\n')
		description += _('Available physical memory: %i bytes (%.2f GB)\n') % (psutil.TOTAL_PHYMEM, psutil.TOTAL_PHYMEM / 1000.0 / 1000.0 / 1000.0)
		description += _('Available virtual memory (swap): %i bytes (%.2f GB)\n') % (virtual_memory, virtual_memory / 1000.0 / 1000.0 / 1000.0)
		description += _('The {top} can give an overview of how much memory is currently in use by the current running processes.\n')
		raise Conflict(description)


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
