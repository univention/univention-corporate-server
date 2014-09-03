#!/usr/bin/python2.7
## title: Enough RAM available for running UCS
## description: Test whether the total amount of physical RAM is sufficient for running an UCS system


import sys
import psutil

virtMem = psutil.total_virtmem()
print 'Available physical memory: %i bytes (%i GB)' % (psutil.TOTAL_PHYMEM, psutil.TOTAL_PHYMEM / 1000 / 1000 / 1000)
print 'Available virtual memory (swap): %i bytes (%i GB)' % (virtMem, virtMem / 1000 / 1000 / 1000)

if psutil.TOTAL_PHYMEM < 2000000000:
	print '\n\nIt is recommended to have at least 2GB of physical memory to run an UCS system'
	print 'summary: Available physical memory is less than the recommended minimum'
	sys.exit(1)

print '\nThe recommended minimum of 2 GB physical memory to run an UCS system are available'
