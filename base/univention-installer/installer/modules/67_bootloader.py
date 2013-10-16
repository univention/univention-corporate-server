#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: bootloader configuration and installation
#
# Copyright 2004-2013 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

#
# Results of previous modules are placed in self.all_results (dictionary)
# Results of this module need to be stored in the dictionary self.result (variablename:value[,value1,value2])
#

import re
import inspect
from objects import *
from local import _
import os

def human_readable(size, precision=2, base=1000.0):
	"""
	Convert number to human readable number.
	>>> human_readable(0)
	'0 B'
	>>> human_readable(1)
	'1 B'
	>>> human_readable(999)
	'999 B'
	>>> human_readable(1000)
	'1.00 KB'
	"""
	size, fac = reduce(lambda (val, suf), fac: (val, suf) if val < base else (val / base, fac), "KMGTPEZY", (size, ''))
	return "%.*f %sB" % (precision if fac else 0, size, fac)


class object(content):
	def __init__(self, max_y, max_x, last, file, cmdline):
		self.guessed = {}
		content.__init__(self, max_y, max_x, last, file, cmdline)
		self.auto_input_enabled = True
		self.max_length = 1
		self.devices = {}

	def debug(self, txt):
		info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
		line = info[1]
		content.debug(self, 'BOOTLOADER:%d: %s' % (line,txt))

	def checkname(self):
		return ['bootloader_record']

	def modvars(self):
		return ['bootloader_record']

	def run_profiled(self):
		self.debug('bootloader => run profiled')
		if len(self.devices) == 1:
			self.debug("  using found device %s" % self.devices.keys()[0])
			return {'bootloader_record' : self.devices.keys()[0]}
		return {}

	def profile_complete(self):
		self.debug("bootloader => profile complete")
		if self.check('bootloader_record'):
			self.debug("  check forced")
			return False
		if self.all_results.get("bootloader_record"):
			self.debug("  value %s from profile" % self.all_results["bootloader_record"])
			return True
		self.debug("  looking for devices ...")
		self.find_devices()
		if len(self.devices) == 1:
			self.debug("  found one device")
			return True
		return False

	def auto_input(self):
		# Return "next" (== F12) and disable auto_input() function.
		# This way, only one F12 keypress will be done automatically.
		self.auto_input_enabled = False
		return "next"

	def depends(self):
		# depends() is called every time the user enters this module - so we can update device list here
		# reset layout and selections
		return {'bootloader_record': ['boot_partition']}

	def find_devices(self):
		self.devices = {}
		# match on any device name that does not end on digit OR
		# any device name ending with cXdY where X and Y are one or more digits
		REpartitions = re.compile('^\d+\s+\d+\s+\d+\s+(.*)$')
		try:
			lines = [line.strip() for line in open('/proc/partitions', 'r')]
		except IOError, ex:
			self.debug('ERROR: cannot read /proc/partitions: %s' % (ex,))
			lines = []

		cdrom_device = self.all_results.get('cdrom_device')
		cdrom_device = os.path.basename(cdrom_device) if cdrom_device.startswith('/dev') else ''

		for line in lines:
			match = REpartitions.match(line)
			if not match:
				continue
			device = match.group(1)

			if device == cdrom_device:
				continue

			# is block device and no partition?
			prefix = "/sys/block/%s" % device.replace("/", "!")
			if not os.path.exists(prefix):
				continue

			# is readonly?
			try:
				content = open('%s/ro' % prefix, 'r').read()
			except IOError, ex:
				self.debug('WARNING: cannot read %s/ro: %s' % (prefix, ex))
				content = '0'
			if content.strip() != '0':
				continue

			# check if device is a CDROM
			try:
				content = open('%s/capability' % prefix, 'r').read()
			except IOError, ex:
				self.debug('WARNING: cannot read %s/capability: %s' % (prefix, ex))
				content = '0'
			try:
				value = int(content, 16)
			except ValueError:
				value = 0
			if value & 8:
				continue

			# ignore device mapper devices
			if os.path.isdir('%s/dm' % prefix):
				continue

			# valid device
			fullname = '/dev/%s' % device
			try:
				vendor = open('%s/device/vendor' % prefix, 'r').readline().strip()
			except IOError, ex:
				self.debug('WARNING: cannot read %s/device/vendor: %s' % (prefix, ex))
				vendor = 'Unknown'
			try:
				model = open('%s/device/model' % prefix, 'r').readline().strip()
			except IOError, ex:
				self.debug('WARNING: cannot read %s/device/model: %s' % (prefix, ex))
				model = 'Unknown'
			try:
				size = open('%s/size' % prefix, 'r').readline().strip()
				size = human_readable(long(size) * 512L)
			except IOError, ex:
				self.debug('WARNING: cannot read %s/size: %s' % (prefix, ex))
				size = '? B'
			label = '%s (%s: %s) - %s' % (fullname, vendor, model, size)
			self.devices[label] = (fullname, len(self.devices))
			self.max_length = max(self.max_length, len(label) + 3)

		self.debug('Possible bootloader devices: %s' % self.devices)

		if len(self.devices) > 1:
			self.debug('More than one possible bootloader device - disabling auto-f12')
			self.auto_input_enabled = False

		self.selected_device = self.all_results.get('bootloader_record')
		self.debug('User selected device: %s' % self.selected_device)
		if not self.selected_device:
			self.selected_device = self.all_results.get('boot_partition','')
			if 'cciss' in self.selected_device:
				# cut off partition number →
				# sub(pattern, repl, string, count=0) → if regular expression "pattern" matches then execute
				# callable "repl" which returns string without trailing "p\d+"
				self.selected_device = re.sub('^(.*?cciss/c\d+d\d+)p\d+$', lambda x: x.group(1), self.selected_device)
			else:
				self.selected_device = self.selected_device.rstrip('0123456789')
			self.debug('Guessing device: %s' % self.selected_device)
		devicelist = sorted(self.devices.values(), key=lambda entry: entry[1])
		if devicelist and not self.selected_device in [ entry[0] for entry in devicelist ]:
			self.selected_device = devicelist[0][0]
		self.debug('self.selected_device: %s' % self.selected_device)

	def layout(self):
		## clear layout
		self.reset_layout()
		# add default buttons
		self.std_button()

		self.find_devices()

		msg = _('This module is used to specifiy the device where to install the boot loader. The correct device depends on current BIOS settings and partitioning. If an incorrect device has been selected, the installed system may not boot. If unsure, continue without change.')
		self.add_elem('TA_desc', textarea(msg, self.minY-10, self.minX+5, 8, self.maxWidth+11))

		pos = self.minY - 10 + self.get_elem('TA_desc').get_number_of_lines()

		self.add_elem('TL_headline', textline(_('Select where to install the GRUB boot loader:'), pos + 1, self.minX+5))
		self.add_elem('DEVICE',select(self.devices, pos + 3, self.minX+5, self.max_length, 15, self.devices.get(self.selected_device,[0,0])[1]))
		self.move_focus(self.get_elem_id('DEVICE'))

	def input(self,key):
		if key in [ 10, 32 ] and self.btn_next():
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		else:
			return self.elements[self.current].key_event(key)

	def incomplete(self):
		return 0

	def helptext(self):
		return _('Boot loader \nSelect where you want the GRUB boot loader to be installed. \n ')

	def modheader(self):
		return _('Boot loader')

	def profileheader(self):
		return 'Boot loader'

	def result(self):
		result = { 'bootloader_record': '%s' % self.get_elem('DEVICE').result()[0] }
		return result

if __name__ == '__main__':
	import doctest
	doctest.testmod()
