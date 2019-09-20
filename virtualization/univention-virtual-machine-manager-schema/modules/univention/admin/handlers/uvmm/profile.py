# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager
#  UDM Virtual Machine Manager Profiles
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

import univention.admin
import univention.admin.mapping as udm_mapping
from univention.admin.handlers import simpleLdap
import univention.admin.syntax as udm_syntax
from univention.admin.localization import translation
from univention.admin.layout import Tab, Group


_ = translation('univention.admin.handlers.uvmm').translate

module = 'uvmm/profile'
default_containers = ['cn=Profiles,cn=Virtual Machine Manager']

childs = False
short_description = _('UVMM: Profile')
object_name = _('Profile')
object_name_plural = _('Profiles')
long_description = ''
operations = ['search', 'edit', 'add', 'remove']

options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionVirtualMachineProfile']
	)
}


class BootDevice(udm_syntax.select):

	"""Boot device enumeration."""
	name = 'BootDevice'
	choices = [
		('hd', _('hard drive')),
		('cdrom', _('CDROM drive')),
		('network', _('Network')),
	]


class Architecture(udm_syntax.select):

	"""CPU architecture."""
	name = 'Architecture'
	choices = [
		('automatic', _('Automatic')),
		('i686', '32 Bit'),
		('x86_64', '64 Bit'),
	]


class VirtTech(udm_syntax.select):

	"""Virtualization technology."""
	name = 'VirtTech'
	choices = [
		('kvm-hvm', _('Full virtualization (KVM)')),
	]


class ClockOffset(udm_syntax.select):

	"""Setup for Real-Time-Clock. <http://libvirt.org/formatdomain.html#elementsTime>"""
	name = 'ClockOffset'
	choices = [
		('utc', _('Coordinated Universal Time')),
		('localtime', _('Local time zone')),
	]


class DriverCache(udm_syntax.select):

	"""Disk cache strategy. <http://libvirt.org/formatdomain.html#elementsDisks>"""
	name = 'DriverCache'
	choices = [
		('default', _('Hypervisor default')),
		('none', _('No host caching, no forced sync')),
		('writethrough', _('Read caching, forced sync')),
		('writeback', _('Read/write caching, no forced sync')),
		('directsync', _('No host caching, forced sync')),
		('unsafe', _('Read/write caching, sync filtered out')),
	]


# UDM properties
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description=_('Name'),
		syntax=udm_syntax.string,
		required=True,
		identifies=True
	),
	'name_prefix': univention.admin.property(
		short_description=_('Name prefix'),
		long_description=_('Prefix for the name of virtual machines'),
		syntax=udm_syntax.string,
	),
	'arch': univention.admin.property(
		short_description=_('Architecture'),
		long_description=_('Architecture of the virtual machine'),
		syntax=Architecture,
	),
	'virttech': univention.admin.property(
		short_description=_('Virtualisation Technology'),
		long_description=_('Virtualisation Technology'),
		syntax=VirtTech,
	),
	'cpus': univention.admin.property(
		short_description=_('CPUs'),
		long_description=_('Number of virtual CPUs'),
		syntax=udm_syntax.integer,
	),
	'cpu_model': univention.admin.property(
		short_description=_('CPU model'),
		long_description=_('CPU model name from e.g. `virsh cpu-models x86_64`'),
		syntax=udm_syntax.string,
	),
	'ram': univention.admin.property(
		short_description=_('Memory'),
		long_description=_('Amount of memory'),
		syntax=udm_syntax.UvmmCapacity,
	),
	'diskspace': univention.admin.property(
		short_description=_('Disk space'),
		long_description=_('Amount of disk space'),
		syntax=udm_syntax.UvmmCapacity,
	),
	'drivercache': univention.admin.property(
		short_description=_('Disk cache'),
		long_description=_('Disk cache handling on host'),
		syntax=DriverCache,
	),
	'interface': univention.admin.property(
		short_description=_('Network interface'),
		long_description=_('Bridging interface'),
		syntax=udm_syntax.string,
	),
	'vnc': univention.admin.property(
		short_description=_('Remote access'),
		long_description=_('Active VNC remote access'),
		syntax=udm_syntax.boolean,
	),
	'kblayout': univention.admin.property(
		short_description=_('Keyboard layout'),
		long_description=_('Keyboard layout'),
		syntax=udm_syntax.string,
	),
	'kernel': univention.admin.property(
		short_description=_('Kernel'),
		long_description=_('Kernel'),
		syntax=udm_syntax.string,
	),
	'kernel_parameter': univention.admin.property(
		short_description=_('Kernel parameter'),
		long_description=_('Kernel parameter'),
		syntax=udm_syntax.string,
	),
	'initramfs': univention.admin.property(
		short_description=_('Initramfs disk'),
		long_description=_('Initramfs disk'),
		syntax=udm_syntax.string,
	),
	'advkernelconf': univention.admin.property(
		short_description=_('Use advanced kernel configuration'),
		long_description=_('Manually specify the kernel configuration for paravirtualized machines or use pyGrub as bootloader'),
		syntax=udm_syntax.TrueFalseUp,
	),
	'bootdev': univention.admin.property(
		short_description=_('Boot devices'),
		long_description=_('Order of boot devices'),
		syntax=BootDevice,
		multivalue=True,
	),
	'os': univention.admin.property(
		short_description=_('Operating system'),
		long_description=_('Operating system'),
		syntax=udm_syntax.string,
	),
	'pvdisk': univention.admin.property(
		short_description=_('Use para-virtual driver for hard drives'),
		syntax=udm_syntax.boolean,
	),
	'pvinterface': univention.admin.property(
		short_description=_('Use para-virtual driver for network interface'),
		syntax=udm_syntax.boolean,
	),
	'pvcdrom': univention.admin.property(
		short_description=_('Use para-virtual driver for CDROM drives'),
		syntax=udm_syntax.boolean,
	),
	'rtcoffset': univention.admin.property(
		short_description=_('Real Time Clock offset'),
		long_description=_('Offset of instances Real Time Clock to host computers clock'),
		syntax=ClockOffset,
	),
}


# UDM web layout
layout = [
	Tab(_('General'), _('Virtual machine profile'), layout=[
		Group(_('General'), layout=[
			"name",
			"virttech",
			"os",
			"name_prefix",
		]),
		Group(_('Virtual hardware'), layout=[
			"arch",
			"cpus",
			"cpu_model",
			"ram",
			"diskspace",
			"drivercache",
			"interface",
			'rtcoffset',
			"pvdisk",
			"pvinterface",
			"pvcdrom",
		]),
		Group(_('Remote access'), layout=[
			"vnc",
			"kblayout",
		]),
		Group(_('Boot configuration'), layout=[
			"bootdev",
			"advkernelconf",
			"kernel",
			"kernel_parameter",
			"initramfs",
		])
	])
]


def list2str(lst):
	"""Convert list to comma separated string."""
	return ','.join(lst)


def str2list(value):
	"""Split comma separated string into list."""
	if value:
		return value[0].split(',')
	return []


# Mapping between UDM properties and LDAP attributes
mapping = udm_mapping.mapping()
mapping.register('name', 'cn', None, udm_mapping.ListToString)
mapping.register('name_prefix', 'univentionVirtualMachineProfileNamePrefix', None, udm_mapping.ListToString)
mapping.register('arch', 'univentionVirtualMachineProfileArch', None, udm_mapping.ListToString)
mapping.register('cpus', 'univentionVirtualMachineProfileCPUs', None, udm_mapping.ListToString)
mapping.register('cpu_model', 'univentionVirtualMachineProfileCPUModel', None, udm_mapping.ListToString)
mapping.register('virttech', 'univentionVirtualMachineProfileVirtTech', None, udm_mapping.ListToString)
mapping.register('ram', 'univentionVirtualMachineProfileRAM', None, udm_mapping.ListToString)
mapping.register('diskspace', 'univentionVirtualMachineProfileDiskspace', None, udm_mapping.ListToString)
mapping.register('drivercache', 'univentionVirtualMachineProfileDriverCache', None, udm_mapping.ListToString)
mapping.register('vnc', 'univentionVirtualMachineProfileVNC', None, udm_mapping.ListToString)
mapping.register('interface', 'univentionVirtualMachineProfileInterface', None, udm_mapping.ListToString)
mapping.register('kblayout', 'univentionVirtualMachineProfileKBLayout', None, udm_mapping.ListToString)
mapping.register('kernel', 'univentionVirtualMachineProfileKernel', None, udm_mapping.ListToString)
mapping.register('kernel_parameter', 'univentionVirtualMachineProfileKernelParameter', None, udm_mapping.ListToString)
mapping.register('initramfs', 'univentionVirtualMachineProfileInitRAMfs', None, udm_mapping.ListToString)
mapping.register('advkernelconf', 'univentionVirtualMachineAdvancedKernelConfig', None, udm_mapping.ListToString)
mapping.register('bootdev', 'univentionVirtualMachineProfileBootDevices', list2str, str2list)
mapping.register('os', 'univentionVirtualMachineProfileOS', None, udm_mapping.ListToString)
mapping.register('pvdisk', 'univentionVirtualMachineProfilePVDisk', None, udm_mapping.ListToString)
mapping.register('pvinterface', 'univentionVirtualMachineProfilePVInterface', None, udm_mapping.ListToString)
mapping.register('pvcdrom', 'univentionVirtualMachineProfilePVCDROM', None, udm_mapping.ListToString)
mapping.register('rtcoffset', 'univentionVirtualMachineProfileRTCOffset', None, udm_mapping.ListToString)


class object(simpleLdap):
	"""UVMM Profile."""
	module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
