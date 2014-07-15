# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager
#  UDM Virtual Machine Manager Profiles
#
# Copyright 2010-2014 Univention GmbH
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

import univention.admin
import univention.admin.filter as udm_filter
import univention.admin.mapping as udm_mapping
from univention.admin.handlers import simpleLdap
import univention.admin.syntax as udm_syntax
from univention.admin.localization import translation
from univention.admin.layout import Tab, Group


_ = translation('univention.admin.handlers.uvmm').translate

module = 'uvmm/profile'
default_containers = ['cn=Profiles,cn=Virtual Machine Manager']

childs = 0
short_description = _('UVMM: Profile')
long_description = ''
operations = ['search', 'edit', 'add', 'remove']


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
		('xen-hvm', _('Full virtualization (XEN)')),
		('xen-xen', _('Paravirtualization (XEN)')),
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
		('none', _('No host cacheing, no forced sync')),
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
			multivalue=False,
			options=[],
			required=True,
			may_change=True,
			identifies=True
		),
	'name_prefix': univention.admin.property(
			short_description=_('Name prefix'),
			long_description=_('Prefix for the name of virtual machines'),
			syntax=udm_syntax.string,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'arch': univention.admin.property(
			short_description=_('Architecture'),
			long_description=_('Architecture of the virtual machine'),
			syntax = Architecture,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'virttech': univention.admin.property(
			short_description=_('Virtualisation Technology'),
			long_description=_('Virtualisation Technology'),
			syntax=VirtTech,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'cpus': univention.admin.property(
			short_description=_('CPUs'),
			long_description=_('Number of virtual CPUs'),
			syntax=udm_syntax.integer,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'ram': univention.admin.property(
			short_description=_('Memory'),
			long_description=_('Amount of memory'),
			syntax=udm_syntax.UvmmCapacity,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'diskspace': univention.admin.property(
			short_description=_('Disk space'),
			long_description=_('Amount of disk space'),
			syntax=udm_syntax.UvmmCapacity,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'drivercache': univention.admin.property(
			short_description=_('Disk cache'),
			long_description=_('Disk cache handling on host'),
			syntax=DriverCache,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'interface': univention.admin.property(
			short_description=_('Network interface'),
			long_description=_('Bridging interface'),
			syntax=udm_syntax.string,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'vnc': univention.admin.property(
			short_description=_('Remote access'),
			long_description=_('Active VNC remote acess'),
			syntax=udm_syntax.boolean,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'kblayout': univention.admin.property(
			short_description=_('Keyboard layout'),
			long_description=_('Keyboard layout'),
			syntax=udm_syntax.string,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'kernel': univention.admin.property(
			short_description=_('Kernel'),
			long_description=_('Kernel'),
			syntax=udm_syntax.string,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'kernel_parameter': univention.admin.property(
			short_description=_('Kernel parameter'),
			long_description=_('Kernel parameter'),
			syntax=udm_syntax.string,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'initramfs': univention.admin.property(
			short_description=_('Initramfs disk'),
			long_description=_('Initramfs disk'),
			syntax=udm_syntax.string,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'advkernelconf': univention.admin.property(
			short_description=_('Use advanced kernel configuarion'),
			long_description=_('Manually specify the kernel configuration for paravirtualized machines or use pyGrub as bootloader'),
			syntax=udm_syntax.TrueFalseUp,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'bootdev': univention.admin.property(
			short_description=_('Boot devices'),
			long_description=_('Order of boot devices'),
			syntax=BootDevice,
			multivalue=True,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'os': univention.admin.property(
			short_description=_('Operating system'),
			long_description=_('Operating system'),
			syntax=udm_syntax.string,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'pvdisk': univention.admin.property(
			short_description=_('Use para-virtual driver for hard drives'),
			syntax=udm_syntax.boolean,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'pvinterface': univention.admin.property(
			short_description=_('Use para-virtual driver for network interface'),
			syntax=udm_syntax.boolean,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'pvcdrom': univention.admin.property(
			short_description=_( 'Use para-virtual driver for CDROM drives' ),
			syntax=udm_syntax.boolean,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
		),
	'rtcoffset': univention.admin.property(
			short_description=_('Real Time Clock offset'),
			long_description=_('Offset of instances Real Time Clock to host computers clock'),
			syntax=ClockOffset,
			multivalue=False,
			options=[],
			required=False,
			may_change=True,
			identifies=False
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


# Maping between UDM properties and LDAP attributes
mapping = udm_mapping.mapping()
mapping.register('name', 'cn', None, udm_mapping.ListToString)
mapping.register('name_prefix', 'univentionVirtualMachineProfileNamePrefix', None, udm_mapping.ListToString)
mapping.register('arch', 'univentionVirtualMachineProfileArch', None, udm_mapping.ListToString)
mapping.register('cpus', 'univentionVirtualMachineProfileCPUs', None, udm_mapping.ListToString)
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
mapping.register('bootdev', 'univentionVirtualMachineProfileBootDevices', list2str, str2list )
mapping.register('os', 'univentionVirtualMachineProfileOS', None, udm_mapping.ListToString)
mapping.register('pvdisk', 'univentionVirtualMachineProfilePVDisk', None, udm_mapping.ListToString)
mapping.register('pvinterface', 'univentionVirtualMachineProfilePVInterface', None, udm_mapping.ListToString)
mapping.register('pvcdrom', 'univentionVirtualMachineProfilePVCDROM', None, udm_mapping.ListToString)
mapping.register('rtcoffset', 'univentionVirtualMachineProfileRTCOffset', None, udm_mapping.ListToString)


class object(simpleLdap):
	"""UVMM Profile."""
	module = module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[]):
		global mapping
		global property_descriptions

		self.mapping = mapping
		self.descriptions = property_descriptions

		simpleLdap.__init__(self, co, lo, position, dn, superordinate)

	def _ldap_pre_create(self):
		"""Create DN for new UVMM Profile."""
		self.dn = '%s=%s,%s' % (
				mapping.mapName('name'),
				mapping.mapValue('name', self.info['name']),
				self.position.getDn()
				)

	def _ldap_addlist(self):
		"""Add LDAP objectClass for UVMM Profile."""
		return [
				('objectClass', ['univentionVirtualMachineProfile'])
				]


def lookup_filter(filter_s=None, lo=None):
	"""
	Return LDAP search filter for UVMM VM profile entries.
	"""
	ldap_filter = udm_filter.conjunction('&', [
				udm_filter.expression('objectClass', 'univentionVirtualMachineProfile'),
				])
	ldap_filter.append_unmapped_filter_string(filter_s, udm_mapping.mapRewrite, mapping)
	return unicode(ldap_filter)


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):
	"""Search for UVMM profile objects."""
	ldap_filter = lookup_filter(filter_s)
	return [object(co, lo, None, dn)
			for dn in lo.searchDn(ldap_filter, base, scope, unique, required, timeout, sizelimit)]


def identify(dn, attr, canonical=0):
	"""Return True if LDAP object is a UVMM profile."""
	return 'univentionVirtualMachineProfile' in attr.get('objectClass', [])
