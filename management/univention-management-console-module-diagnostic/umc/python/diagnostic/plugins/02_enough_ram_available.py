#!/usr/bin/python2.7

import sys
import psutil

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Enough RAM available for running UCS')
description = _('Test whether the total amount of physical RAM is sufficient for running an UCS system')

def run():
	virtMem = psutil.total_virtmem()
	print _('Available physical memory: %i bytes (%i GB)') % (psutil.TOTAL_PHYMEM, psutil.TOTAL_PHYMEM / 1000 / 1000 / 1000)
	print _('Available virtual memory (swap): %i bytes (%i GB)') % (virtMem, virtMem / 1000 / 1000 / 1000)

	if psutil.TOTAL_PHYMEM < 2000000000:
		print _('\n\nIt is recommended to have at least 2GB of physical memory to run an UCS system')
		print _('summary: Available physical memory is less than the recommended minimum')
		return False, '', ''

	print _('\nThe recommended minimum of 2 GB physical memory to run an UCS system are available')
	return True, '', ''
