#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Node Common
#  script to restore virtual machines
#
# Copyright 2010-2019 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

from __future__ import print_function

from optparse import OptionParser
from xml.dom.minidom import parse

import fnmatch
import os
import subprocess
import sys

import univention.config_registry as ucr

configRegistry = ucr.ConfigRegistry()
configRegistry.load()


class Instance(object):

	def __init__(self, name, uuid, filename):
		self.name = name
		self.uuid = uuid
		self.filename = filename


def __get_value(doc, element):
	tag = doc.getElementsByTagName(element)
	if tag and tag[0].firstChild and tag[0].firstChild.nodeValue:
		return tag[0].firstChild.nodeValue

	return None


def _parse_xml_file(filename):
	doc = parse(filename)
	if not doc:
		print('error: failed to parse backup file %s' % filename, file=sys.stderr)
		return None
	name = __get_value(doc, 'name')
	uuid = __get_value(doc, 'uuid')

	return Instance(name, uuid, filename)


def read_backup_files():
	instances = []
	dir = configRegistry.get('uvmm/backup/directory', '/var/backups/univention-virtual-machine-manager-daemon')
	for filename in os.listdir(dir):
		if not os.path.isfile(os.path.join(dir, filename)) or not filename.endswith('.xml'):
			continue
		instance = _parse_xml_file(os.path.join(dir, filename))
		if instance:
			instances.append(instance)

	return instances


def list_instances(instances, pattern):
	if not instances:
		print('no backups available')
		return
	max_length = max([len(x.name) for x in instances])
	format_str = '%%-%ds (%%s)' % max_length
	for instance in instances:
		if fnmatch.fnmatch(instance.name, pattern):
			print(format_str % (instance.name, instance.uuid))


def instance_exists(instance):
	devnull = open(os.devnull, 'w')
	ret = subprocess.call(['virsh', 'domuuid', instance.name], stdout=devnull, stderr=devnull)
	devnull.close()
	return ret == 0


def restore_instance(instances, name, force):
	for instance in instances:
		if instance.name == name or instance.uuid == name:
			if instance_exists(instance):
				if not force:
					print('error: the virtual instance already exists. Use the option -f to overwrite it', file=sys.stderr)
					sys.exit(1)
				else:
					print('warning: overwriting existing virtual instance (forced)', file=sys.stderr)
			devnull = open(os.devnull, 'w')
			ret = subprocess.call(['virsh', 'define', instance.filename], stdout=devnull, stderr=devnull)
			devnull.close()
			if ret:
				print('error: failed to restore virtual instance %s' % instance.name, file=sys.stderr)
				return False
			break
	return True


if __name__ == '__main__':
	parser = OptionParser()
	parser.add_option('-l', '--list', action='store_true', dest='list', default=False, help='List all available backups.')
	parser.add_option('-p', '--pattern', action='store', dest='pattern', default='*', help='When listing backups the instance names must match this pattern.')
	parser.add_option('-r', '--restore', action='store', dest='restore', default=None, help='Restore a virtual instance. RESTORE can be the name or UUID.')
	parser.add_option('-f', '--force', action='store_true', dest='force', default=False, help='Force overwriting existing instances when restoring a virtual instance')

	(options, arguments) = parser.parse_args()

	# default action: list
	if len(sys.argv) < 2:
		options.list = True

	# whatever should be done the backup files need to be read
	instances = read_backup_files()

	if options.list:
		list_instances(instances, options.pattern)
	elif options.restore:
		restore_instance(instances, options.restore, options.force)
