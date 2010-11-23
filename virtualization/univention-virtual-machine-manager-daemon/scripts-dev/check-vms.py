#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Check if VMs are still valid
# 1. all referenced disks exist
#
import sys
import os
import libvirt
from optparse import OptionParser
try:
	import xml.etree.ElementTree as ET
except ImportError:
	import elementtree.ElementTree as ET

verbosity = 0
def log(level, message):
	"""Print message."""
	global verbosity
	if verbosity >= level:
		print message

def check_vm(dom, dom_name, paths):
	"""Check libvirt-domain object for missing disks."""
	valid = True
	xml = dom.XMLDesc(0)
	domain = ET.fromstring(xml)
	devices = domain.find('devices')
	disks = devices.findall('disk')
	for disk in disks:
		type = disk.attrib['type']
		source = disk.find('source')
		if type == 'file':
			path = source.attrib['file']
		elif type == 'block':
			path = source.attrib['dev']
		else:
			log(1, '%s: SKIP type="%s"' % (dom_name, type))
			continue

		vms = paths.setdefault(path, [])
		if os.path.exists(path):
			log(1, '%s: OK "%s" [%s]' % (dom_name, path, ' '.join(vms)))
		else:
			log(1, '%s: MISSING "%s" [%s]' % (dom_name, path, ' '.join(vms)))
			valid = False
		vms.append(dom_name)
	if valid:
		log(0, '%s: OK' % (dom_name,))
	else:
		log(0, '%s: MISSING' % (dom_name,))
	return valid

def check_paths(paths):
	"""Check for unreferenced images."""
	ref_dirs = set((os.path.dirname(path) for path in paths))
	for dir in ref_dirs:
		for root, dirs, files in os.walk(dir):
			for file in files:
				path = os.path.join(root, file)
				if path in paths:
					log(0, 'USED "%s" [%s]' % (path, ' '.join(paths[path])))
				else:
					log(0, 'UNUSED "%s"' % (path,))
			del dirs[:]

if __name__ == '__main__':
	parser = OptionParser(usage='Usage: %%prog [options] [uri]')
	parser.add_option('-v', '--verbose',
			action='count', dest='verbose', default=0,
			help='Increase verbosity')

	options, arguments = parser.parse_args()

	verbosity = options.verbose
	try:
		url = arguments[0]
	except IndexError:
		url = 'xen:///'

	paths = {}
	c = libvirt.open(url)
	dom_ids = c.listDomainsID()
	for dom_id in dom_ids:
		dom = c.lookupByID(dom_id)
		dom_name = dom.name()
		check_vm(dom, dom_name, paths)
	dom_names = c.listDefinedDomains()
	for dom_name in dom_names:
		dom = c.lookupByName(dom_name)
		check_vm(dom, dom_name, paths)

	check_paths(paths)

# vim:set ts=4 sw=4 noet:
# :!scp % xen4:/usr/local/bin/
