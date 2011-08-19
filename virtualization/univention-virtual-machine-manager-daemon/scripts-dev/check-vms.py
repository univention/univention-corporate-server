#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Check if VMs are still valid
# 1. all referenced disks exist
#
import sys
import os
import re
import libvirt
import subprocess
from optparse import OptionParser
try:
	import xml.etree.ElementTree as ET
except ImportError:
	import elementtree.ElementTree as ET

try:
	import curses
	curses.setupterm()
	NORMAL = curses.tigetstr('sgr0')
	set_af = curses.tigetstr('setaf')
	BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = [curses.tparm(set_af, i) for i in range(8)]
except Exception, e:
	NORMAL = BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = ''

verbosity = 0
def log(level, message):
	"""Print message."""
	global verbosity
	if verbosity >= level:
		print message

def key2dot(key, RE_KEY=re.compile('[^0-9A-Za-z]')):
	"""Convert key to dot compatible format."""
	return '_' + RE_KEY.sub('_', key)

def dot(code):
	"""Print dot code."""
	print >>sys.stderr, code # FIXME

def check_vm(dom, dom_name, paths):
	"""Check libvirt-domain object for missing disks."""
	key = key2dot(dom_name)
	valid = True
	xml = dom.XMLDesc(0)
	domain = ET.fromstring(xml)
	devices = domain.find('devices')
	disks = devices.findall('disk')
	for disk in disks:
		type = disk.attrib['type']
		source = disk.find('source')
		if disk.attrib['device'] in ('cdrom', 'floppy') and source is None:
			continue
		if type == 'file':
			path = source.attrib['file']
		elif type == 'block':
			path = source.attrib['dev']
		else:
			log(1, "'%s': %sSKIP type='%s'%s" % (dom_name, BLUE, type, NORMAL))
			continue

		vms = paths.setdefault(path, [])
		if os.path.exists(path):
			log(1, "'%s': %sOK '%s' [%s]%s" % (dom_name, GREEN, path, ' '.join(vms), NORMAL))
			dot('%s -> %s [color=green];' % (key, key2dot(path),))
		else:
			log(1, "'%s': %sMISSING '%s' [%s]%s" % (dom_name, RED, path, ' '.join(vms), NORMAL))
			dot('%s -> %s [color=red];' % (key, key2dot(path),))
			dot('%s [shape=egg, style=filled, color=red, label="%s"];' % (key2dot(path), path))
			valid = False
		vms.append(dom_name)
	if valid:
		log(0, "'%s': %sOK%s" % (dom_name, GREEN, NORMAL))
		dot('%s [shape=rectangle, style=filled, color=green, label="%s"];' % (key, dom_name))
	else:
		log(0, "'%s': %sMISSING%s" % (dom_name, RED, NORMAL))
		dot('%s [shape=rectangle, style=filled, color=red, label="%s"];' % (key, dom_name))
	return valid

def check_paths(paths):
	"""Check for unreferenced images."""
	ref_dirs = set((os.path.dirname(path) for path in paths))
	for dir in ref_dirs:
		dot('subgraph cluster%s {' % key2dot(dir))
		# dot('%s [shape=diamond, label="%s"];' % (key2dot(dir), dir))
		for root, dirs, files in os.walk(dir):
			del dirs[:] # not recursive
			for file in files:
				path = os.path.join(root, file)
				# dot('%s -> %s;' % (key2dot(dir), key2dot(path)))
				if path in paths:
					log(0, "'%s': %sUSED%s [%s]" % (path, GREEN, NORMAL, ' '.join(paths[path])))
					dot('%s [shape=egg, color=green, label="%s"];' % (key2dot(path), file))
				else:
					log(0, "'%s': %sUNUSED%s" % (path, BLUE, NORMAL))
					dot('%s [shape=egg, color=blue, label="%s"];' % (key2dot(path), file))
				if file.endswith('.xml'):
					continue
				if file.endswith('.raw'):
					continue
				if file.endswith('.iso'):
					continue
				p = subprocess.Popen(('qemu-img', 'info', path), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				stdout, stderr = p.communicate()
				if p.returncode != 0:
					log(2, "'%s': FORMAT %s" % (path, stderr))
					continue
				for l in stdout.splitlines():
					PREFIX = 'backing file: '
					SUFFIX = ' (actual path: '
					if not l.startswith(PREFIX):
						continue
					l = l[len(PREFIX):]
					i = l.index(SUFFIX)
					if i < 0:
						continue
					base = l[:i]
					if not os.path.isabs(base):
						base = os.path.join(root, base)
					log(0, "'%s': %sBASE%s '%s'" % (path, YELLOW, NORMAL, base))
					dot('%s -> %s;' % (key2dot(path), key2dot(base)))
		dot('label="%s";' % (dir,))
		dot('color=blue;')
		dot('}')

if __name__ == '__main__':
	parser = OptionParser(usage='Usage: %%prog [options] [uri]')
	parser.add_option('-v', '--verbose',
			action='count', dest='verbose', default=0,
			help='Increase verbosity')
	parser.add_option('-g', '--dot',
			action='store_true', dest='dot', default=False,
			help='Generate dot graph')

	options, arguments = parser.parse_args()

	verbosity = options.verbose
	try:
		url = arguments[0]
	except IndexError:
		if os.path.exists('/dev/kvm'):
			url = 'qemu:///system'
		elif os.path.exists('/proc/xen/capabilities'):
			url = 'xen:///'
		else:
			parser.print_usage(sys.stderr)
			sys.exit(2)
	
	if options.dot:
		dot('digraph G')
		dot('{')
		dot('rankdir=TB;')
		dot('rotate=90;')
		dot('nodesep=.05;')
		#dot('node [shape=record, fontsize=5, height=.05];')

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

	if options.dot:
		dot('}')

# vim:set ts=4 sw=4 noet:
# :!scp % xen4:/usr/local/bin/
