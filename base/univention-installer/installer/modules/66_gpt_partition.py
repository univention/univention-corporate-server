#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: partition configuration
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

########################
# INLINE DOCUMENTATION #
########################
#
# - this partition module aligns the partitions at SI megabyte boundaries (MiB).
# - all sizes and start/end points are stored in bytes!

# TODO FIXME align MB ranges in grid
# TODO FIXME count GPT partitions ==> maximum is 127

from objects import *
from local import _
import os, re, curses
import inspect
import subprocess
import pprint
import struct
import textwrap

def B2KiB(value):
	return value / 1024.0

def KiB2B(value):
	return value * 1024

def B2MiB(value):
	return value / 1024.0 / 1024.0

def MiB2B(value):
	return value * 1024 * 1024

def MiB2MB(value):
	return value * 1024.0 * 1024.0 / 1000.0 / 1000.0


# some autopartitioning config values
PARTSIZE_EFI = MiB2B(260)           # size of EFI Partition 260 MiB
PARTSIZE_EFI_MIN = MiB2B(260)       # minimum size of EFI Partition 260 MiB (min. size is 260 MB due to limitation of FAT32 on 4k-sector-drives: see also http://technet.microsoft.com/en-us/library/hh824839.aspx)
PARTSIZE_BIOS_GRUB = MiB2B(8)       # size of BIOS Boot Partition 8 MiB
PARTSIZE_BOOT = MiB2B(512)          # size of /boot partition: 512 MiB
PARTSIZE_SYSTEM_MIN = MiB2B(4096)   # minimum free space for system: 4 GiB
PARTSIZE_SWAP_MIN = MiB2B(512)      # lower swap partition limit 512 MiB
PARTSIZE_SWAP_MAX = MiB2B(10240)    # limit swap partition to 10 GiB

# ATTENTION: value has to be megabyte aligned!
# minimum free space between partitions (otherwise ignored)
PARTSIZE_MINIMUM = MiB2B(4)			# minimum partition size

# ATTENTION: value has to be megabyte aligned!
# start of first partition ; first 16MiB have to be free to provide some spare space
EARLIEST_START_OF_FIRST_PARTITION = MiB2B(16)
RESERVED_SPACE_AT_END_OF_DISK = MiB2B(128)   # free space reserved for automatic partitions (incl. RESERVED_FOR_GPT)
RESERVED_FOR_GPT = MiB2B(4)                  # amount of space reserved for backup GPT at end of disk

# reduce size of each PV by at least this amount of megabytes for LVM overhead
LVM_OVERHEAD = MiB2B(15)

# mount points
MOUNTPOINT_EFI = '/boot/grub'

# filesystem definitions
FSTYPE_NONE = 'none'
FSTYPE_LVMPV = 'LVMPV'
FSTYPE_SWAP = 'linux-swap'
FSTYPE_VFAT = 'vfat'
FSTYPE_EFI = 'EFI'

# partition types
PARTTYPE_USED = 10
PARTTYPE_FREE = 11
PARTTYPE_RESERVED = 12
PARTTYPE_LVM_VG = 100
PARTTYPE_LVM_LV = 101
PARTTYPE_LVM_VG_FREE = 102

# partition flags
PARTFLAG_NONE = 'none'
PARTFLAG_SWAP = 'linux-swap'     # partition is a swap partition
PARTFLAG_LVM  = 'lvm'            # partition is a LVM PV
PARTFLAG_EFI = 'boot'           # partition is a EFI system partition
PARTFLAG_BIOS_GRUB = 'bios_grub' # partition is a BIOS boot partition
VALID_PARTED_FLAGS = [PARTFLAG_LVM, PARTFLAG_EFI, PARTFLAG_BIOS_GRUB] # flags that are known to parted

# partition index ("num")
# - indicating partition number if x > 0
# x == -1 → free space on disk
PARTNUMBER_FREE = -1
PARTNUMBER_MAXIMUM = 127

# file systems
EXPERIMENTAL_FSTYPES = ['btrfs']
ALLOWED_BOOT_FSTYPES = ['xfs','ext2','ext3','ext4']
ALLOWED_ROOT_FSTYPES = ['xfs','ext2','ext3','ext4','btrfs']
BLOCKED_FSTYPES_ON_LVM = [FSTYPE_SWAP]

# problems encountered with disks
DISKLABEL_GPT = 'gpt'
DISKLABEL_MSDOS = 'msdos'
DISKLABEL_UNKNOWN = 'unknown'
UNKNOWN_ERROR = 'unknown_error'
PARTITION_GPT_CONFLICT= 'partition_gpt_conflict'

def pretty_format(val):
	return pprint.PrettyPrinter(indent=4).pformat(val)

def align_partition_start(position):
	''' Align partition start (in bytes) to 1 MiB boundaries by increasing position '''
	if position % (1024*1024):
		return MiB2B(int(B2MiB(position))+1)  # cut off remainder after division and increase by one
	return position

def align_partition_end(position):
	''' Align partition end (in bytes) to 1 MiB boundaries by decreasing position.
		Please note: the partition end refers to the last byte of the partition. That means
					 that "position" is one byte below of an 1 MiB boundary.
	'''

	if (position+1) % (1024*1024):
		return MiB2B(int(B2MiB(position+1)))-1    # cut off remainder after division
	return position

def calc_part_size(start, end):
	''' start and end have to be integers referring to the first and the last byte of the partition.
		The method returns the size of the partition in bytes
	'''
	assert(end > start)
	return end - start + 1

def calc_part_end(start, size):
	''' start and size have to be integers referring to the first byte and the size of the partition.
		The method returns the last byte of the partition.
	'''
	assert(size > 0)
	assert(start > 0)
	return start + size - 1

def calc_next_partition_number(disk):
	known_numbers = [ x['num'] for x in disk['partitions'].values() ]
	for i in xrange(1, PARTNUMBER_MAXIMUM):
		if i not in known_numbers:
			return i
	raise Exception('too many partitions')

def get_sanitized_position(pos):
	"""
	This function converts values with given units to an integer value.
	All units are interpreted as binary units (factor of 1024):
	1K==1024, 1KB==1024, 1KiB=1024, and so on for M/G/T
	"""
	pos = pos.upper()
	factor = 1
	if 'T' in pos:
		factor = 1024 * 1024 * 1024 * 1024
	elif 'G' in pos:
		factor = 1024 * 1024 * 1024
	elif 'M' in pos:
		factor = 1024 * 1024
	elif 'K' in pos:
		factor = 1024
	value = pos.strip(' -+KMGTIB')
	try:
		if '.' in value:
			return int(float(value) * factor)
		else:
			return int(value, 10) * factor
	except ValueError:
		return None

def get_sanitized_label(label, flags, mpoint, fstype):
	"""
	This function automatically creates a sanitized label from given information:
	label, partition flags, mount point or filesystem type (values used in gived order)
	"""
	if not label:
		label = ''
		if PARTFLAG_LVM in flags:
			label = 'LVMPV'
		elif PARTFLAG_EFI in flags:
			label = 'EFI System'
		elif PARTFLAG_BIOS_GRUB in flags:
			label = 'BIOS Boot Partition'
		elif mpoint:
			for c in mpoint.lower():
				if c in 'abcdefghijklmnopqrstuvwxyz0123456789-_/':
					label += c
				else:
					label += '_'
		elif fstype:
			label = fstype
		else:
			label = 'unknown'
	# truncate label to 36 characters (all non ascii characters are filtered out above)
	return label[0:36]

def get_mkfs_cmd(device, fstype):
	fstype = fstype.lower()
	if fstype in ['ext2','ext3','vfat','msdos', 'ext4', 'btrfs']:
		mkfs_cmd = ['/sbin/mkfs.%s' % fstype, device]
	elif fstype == FSTYPE_EFI.lower():
		mkfs_cmd = ['/sbin/mkfs.vfat', '-F', '32', device]
	elif fstype == 'xfs':
		mkfs_cmd = ['/sbin/mkfs.xfs', '-f', device]
	elif fstype == 'linux-swap':
		mkfs_cmd = ['/bin/mkswap', device]
	else:
		mkfs_cmd = []
	return mkfs_cmd


class object(content):
	def __init__(self, max_y, max_x, last=(1,1), file='/tmp/installer.log', cmdline={}):
		self.written=0
		content.__init__(self,max_y,max_x,last, file, cmdline)
		self.debug('init(): max_y=%s  max_x=%s' % (max_y, max_x))

	def printPartitions(self):
		self.debug('PARTITION LIST:')
		disk_list = self.container['disk'].keys()
		disk_list.sort()
		for diskitem in disk_list:
			disk = self.container['disk'][diskitem]
			part_list = disk['partitions'].keys()
			part_list.sort()
			for partitem in part_list:
				part = disk['partitions'][partitem]
				start = partitem
				end = part['end']
				self.debug('%s%s:  type=%d	 start=%dB=%fMiB	 end=%dB=%fMiB' % (diskitem, part['num'], part['type'],
																				   start, B2MiB(start), end, B2MiB(end)))

	def checkname(self):
		return ['devices']

	def debug(self, txt):
		info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
		line = info[1]
		content.debug(self, 'PARTITION-GPT:%d: %s' % (line,txt))

	def fix_boot_flag_in_protective_mbr(self, device):
		"""
		This function reads the first 512 bytes of specified device and
		adds the bootable flag to all partitions with partition type 0xEE.
		The disk gets changed directly!
		returns True, if MBR has been modified, otherwise False.
		"""
		def parse_entry(mbr, partition_number):
			partition = struct.unpack('BBBBBBBB8x',mbr[446+partition_number*16:446+(partition_number+1)*16])
			return { 'flag': partition[0],
					 'type': partition[4],
					 'HSCstart': partition[1:4],
					 'HSCend': partition[5:8] }

		def get_modfied_entry_with_boot_flag(mbr, partition_number):
			"""
			Set bootable flag (bit 7) in flag byte in specified MBR partition entry.
			"""
			mbr = mbr[:446+partition_number*16] + \
				  chr(ord(mbr[446+partition_number*16]) | 0x80) + \
				  mbr[446+partition_number*16+1:]
			return mbr

		if not os.path.exists(device):
			self.debug('fix_boot_flag_in_protective_mbr: device %s does not exist' % device)
			return False
		# get MBR / 512 bytes of device
		try:
			data = open(device, 'r').read(512)
		except (IOError, OSError), e:
			self.debug('fix_boot_flag_in_protective_mbr: exception during read on device %s: %s' % (device, str(e)))
			return False

		# iterate over all partitions
		changed = False
		for i in xrange(0, 4):
			# if partition type is 0xEE...
			entry = parse_entry(data, i)
			self.debug('fix_boot_flag_in_protective_mbr: entry[%d]=%s' % (i, str(entry)))
			if entry['type'] == 0xEE:
				self.debug('fix_boot_flag_in_protective_mbr: found protective partition')
				# then set bootable flag
				data = get_modfied_entry_with_boot_flag(data, i)
				changed = True

		if changed:
			try:
				open(device, 'w').write(data)
			except (IOError, OSError), e:
				self.debug('fix_boot_flag_in_protective_mbr: exception during write on device %s: %s' % (device, str(e)))
				return False
		return changed


	def profile_prerun(self):
		self.debug('profile_prerun')
		self.start()
		self.container['profile']={}

		self.act = self.prof_active(self,_('Reading LVM config'),_('Please wait ...'),name='act')
		self.act.action='prof_read_lvm'
		self.act.draw()
#		self.read_lvm()
		self.set_lvm(True)
		self.debug('profile_prerun: self.container["disk"]=%s' % self.container['disk'])
		self.debug('profile_prerun: self.container["lvm"]=%s' % self.container['lvm'])
		self.read_profile()
		return {}

	def get_usb_storage_device_list(self):
		disklist_usbstorage = []
		self.debug('looking for usb storage devices')
		p = os.popen('/lib/univention-installer/usb-device.sh')
		data = p.read()
		p.close()
		for line in data.splitlines():
			items = line.split(' ')
			if len(items) >= 4:
				if '/' in items[-1]:
					disklist_usbstorage.append( items[-1] )
				else:
					disklist_usbstorage.append( '/dev/%s' % items[-1] )
		self.debug('found usb storage devices = %s' % disklist_usbstorage)
		return disklist_usbstorage

	def check_space_for_autopart(self):
		"""
		Returns error message (str) if not enough space is found for auto partitioning.
		Returns None if enough space is present.
		"""
		self.debug('checking free space for autopart...')
		first_disk_size = 0
		first_disk_name = 'UNKNOWN'
		if self.container['disk'].keys():
			first_disk_name = sorted(self.container['disk'].keys())[0]
			for part in self.container['disk'][first_disk_name]['partitions'].values():
				first_disk_size += part['size']
		self.debug('first_disk_name=%r' % first_disk_name)
		self.debug('first_disk_size=%0.2f KiB' % (first_disk_size / 1024.0))

		if first_disk_size < (PARTSIZE_BOOT + PARTSIZE_SYSTEM_MIN + PARTSIZE_SWAP_MIN):
			result = _('Not enough space for autopartitioning: sum of disk sizes=%(first_disk_size)d MiB  required=%(required)d MiB') % {
				'first_disk_size': B2MiB(first_disk_size),
				'required': B2MiB(PARTSIZE_BOOT + PARTSIZE_SYSTEM_MIN + PARTSIZE_SWAP_MIN),
				}
			self.debug( result)
			return result

		# everything ok - enough space for auto_part
		self.debug('found enough free space for autopart')
		return None

	def profile_complete(self):
		self.debug('profile_complete')

		if self.container['module_disabled']:
			self.debug('module has been disabled since profile requested following partition table type: %r' % self.all_results.get('partitiontable_type'))
			return True

		if self.check('partitions') | self.check('partition'):
			return False
		root_device=None
		boot_device=None
		root_fs=None
		boot_fs=None
		root_fs_type=None
		boot_fs_type=None
		partflag_cnt = {}
		mpoint_list = []
		self.debug('profile_complete: container_profile=\n%s' % pretty_format(self.container['profile']))
		for key in self.container['profile']['create'].keys():
			for minor in self.container['profile']['create'][key].keys():
				fstype = self.container['profile']['create'][key][minor]['fstype'].strip()
				mpoint = self.container['profile']['create'][key][minor]['mpoint'].strip()
				flags = self.container['profile']['create'][key][minor]['flag']
				self.debug('profile_complete: %s: mpoint=%s  fstype=%s  flags=%r' % (key, mpoint, fstype, flags))
				if len(mpoint) and mpoint in mpoint_list:
					self.message="Double mountpoint '%s'" % mpoint
					return False
				mpoint_list.append(mpoint)

				for flag in flags:
					partflag_cnt.setdefault(flag, 0)
					partflag_cnt[flag] += 1

				if mpoint == '/boot':
					boot_device = 'PHY'
					boot_fs_type=fstype
					if not fstype.lower() in ALLOWED_BOOT_FSTYPES:
						boot_fs = fstype

				if mpoint == '/':
					root_device = 'PHY'
					root_fs_type=fstype
					if not fstype.lower() in ALLOWED_ROOT_FSTYPES:
						root_fs = fstype

		for lvname, lv in self.container['profile']['lvmlv']['create'].items():
			mpoint = lv['mpoint']
			fstype = lv['fstype']
			self.debug('profile_complete: /dev/%s/%s: mpoint=%s  fstype=%s' % (lv['vg'], lvname, mpoint, fstype))

			if len(mpoint) and mpoint in mpoint_list:
				self.message="Double mountpoint '%s'" % mpoint
				return False
			mpoint_list.append(mpoint)

			if mpoint == '/boot':
				boot_device = 'LVM'
				boot_fs_type=fstype
				if not fstype.lower() in ALLOWED_BOOT_FSTYPES:
					boot_fs = fstype

			if mpoint == '/':
				root_device = 'LVM'
				root_fs_type=fstype
				if not fstype.lower() in ALLOWED_ROOT_FSTYPES:
					root_fs = fstype

		if self.container['use_efi'] and not partflag_cnt.get(PARTFLAG_EFI,0):
			self.message = 'The extensible firmware interface (EFI) has been detected but none of the configured partitions holds the flag "boot". Without this flag, the installed system is unbootable.'
			return False

		if not self.container['use_efi'] and not partflag_cnt.get(PARTFLAG_BIOS_GRUB,0):
			self.message = 'None of the configured partitions holds the flag "bios_grub". Without this flag, the installed system is unbootable.'
			return False

		if root_device == None:
			self.message = 'Missing / as mountpoint'
			return False

		if boot_device in ['LVM']:
			self.message = 'Unbootable config! /boot needs non LVM partition!'
			return False

		if root_device == 'LVM' and boot_device in [ None, 'LVM' ]:
			self.message = 'Unbootable config! / on LVM needs /boot-partition!'
			return False

		if root_fs:
			self.message='Wrong filesystem type \'%s\' for mount point \'/\'' % root_fs
			return False

		if boot_fs:
			self.message='Wrong filesystem type \'%s\' for mountpoint /boot' % boot_fs
			return False

		if root_fs_type == 'btrfs' and boot_fs_type in [ None, 'btrfs' ]:
			self.message='Unbootable config! / on btrfs needs /boot-partition with other than btrfs!'
			return False

		if 'auto_part' in self.all_results.keys():
			if self.all_results['auto_part'] in ['yes']:  # as of UCS 3.2-0 "yes" is the new standard;  in prior version 'full_disk' and 'full_disk_usb' have been valid
				result = self.check_space_for_autopart()
				if result:
					self.message = result
					return False
		return True

	def get_real_partition_device_name(self, device, number):
		dev_match=None
		#/dev/cXdX
		regex = re.compile(".*c[0-9]d[0-9]*")
		match = re.search(regex,device)
		if match:
			regex = re.compile(".*c[0-9]*d[0-9]*")
			dev_match=re.search(regex, match.group())

		if dev_match:
			return '%sp%s' % (dev_match.group(), number)
		return '%s%d' % (device, number)

	def run_profiled(self):
		self.debug('run_profiled')
		if self.container['module_disabled']:
			self.debug('module has been disabled since profile requested following partition table type: %r' % self.all_results.get('partitiontable_type'))
			return {}

		self.act_profile()

		self.debug('run_profiled: creating profile')
		tmpresult = []
		for key in self.container['profile']['create'].keys():
			for minor in self.container['profile']['create'][key].keys():
				parttype = self.container['profile']['create'][key][minor]['type']
				format = self.container['profile']['create'][key][minor]['format']
				fstype = self.container['profile']['create'][key][minor]['fstype']
				start = self.container['profile']['create'][key][minor]['start']
				end = self.container['profile']['create'][key][minor]['end']
				mpoint = self.container['profile']['create'][key][minor]['mpoint']
				flag = self.container['profile']['create'][key][minor]['flag']
				dev = "%s"%self.get_real_partition_device_name(key,minor)

				tmpresult.append( ("PHY", dev, parttype, format, fstype, start, end, mpoint, flag) )

		for lvname,lv in self.container['profile']['lvmlv']['create'].items():
			device = '/dev/%s/%s' % (lv['vg'], lvname)
			tmpresult.append( ("LVM", device, 'LVMLV', lv['format'], lv['fstype'], lv['start'], lv['end'], lv['mpoint'], lv['flag']) )

		i = 0
		tmpresult.sort(lambda x,y: cmp(x[7], y[7]))  # sort by mountpoint
		self.debug('run_profiled: tmpresult=%s' % tmpresult)
		for (entrytype, device, parttype, format, fstype, start, end, mpoint, flag) in tmpresult:
			start = int(B2MiB(start))
			end = int(B2MiB(end+1))
			if mpoint == '':
				mpoint = 'None'
			if fstype == '':
				fstype = 'None'
			if not flag:
				flag = [PARTFLAG_NONE]
			self.container['result'][ 'dev_%d' % i ] =  "%s %s %s %s %s %sMiB %sMiB %s %s" % (entrytype, device, parttype, format, fstype,
																							  start, end, mpoint, ','.join(flag))
			self.debug( 'dev_%d="%s"' % (i, self.container['result'][ 'dev_%d' % i ]))
			i += 1
		self.container['result']['partitiontable_type'] = 'GPT'
		self.container['result']['use_efi'] = { True: 'yes', False: 'no' }[self.container.get('use_efi',False)]


		self.debug('run_profiled: adding profile to results')
		return self.container['result']

	def layout(self):
		self.sub=self.partition(self,self.minY-12,self.minX,self.maxWidth+20,self.maxHeight+5)
		self.sub.draw()

	def input(self,key):
		return self.sub.input(key)

	def kill_subwin(self):
		#Defined to prevent subwin from killing (module == subwin)
		if hasattr(self.sub, 'sub'):
			self.sub.sub.exit()
		return ""

	def find_largest_free_space(self, requested_types, size, min_size):
		"""
		Arguments:
  		  requested_types: list of partition types to search for (e.g. [PARTTYPE_FREE, PARTTYPE_RESERVED])
		  size:	   requested partition size in bytes (has to be megabyte aligned)
		  min_size:  if free space of size <size> is not available then try to allocate partition with at least <min_size> bytes

		This function returns a 3-tuple consisting of <finalsize>, <diskname>, <part_start>
		  finalsize:  value between <min_size> and <size>
		  diskname:   name of disk on which this free space has been located
		  part_start: starting byte of located free space
		"""
		for type_of_free_space in requested_types:
			# try to find suitable free disk space
			for diskname, disk in self.container['disk'].items():
				for part_start, part in disk['partitions'].items():
					if part['type'] == type_of_free_space:
						if part['size'] >= size:
							return (size, diskname, part_start)
			# if min_size is equal to size, then do not try to find smaller region
			if min_size >= size:
				continue
			# no free partition found --> try to find largest one in range <min_size> to <size> bytes
			suitable_free_space = []
			for diskname, disk in self.container['disk'].items():
				for part_start, part in disk['partitions'].items():
					if part['type'] == type_of_free_space:
						if part['size'] < size and part['size'] >= min_size:
							suitable_free_space.append((size, diskname, part_start))
			if suitable_free_space:
				# at least one region is large enough
				suitable_free_space = sorted(suitable_free_space, lambda x,y: cmp(x[0], y[0]))
				size, diskname, part_start = suitable_free_space[-1]
				return suitable_free_space[-1]
		return None

	def ask_create_efi_part_callback(self, result):
		result = self.find_largest_free_space((PARTTYPE_FREE, PARTTYPE_RESERVED), PARTSIZE_EFI, PARTSIZE_EFI_MIN)
		self.debug('ask_create_efi_part_callback: result=%s' % pretty_format(result))
		if result:
			size, diskname, part_start = result
			self.sub.part_create_generic(diskname, part_start, MOUNTPOINT_EFI, size, FSTYPE_EFI, PARTTYPE_USED, [PARTFLAG_EFI], 1)


	def ask_create_biosboot_part_callback(self, result):
		result = self.find_largest_free_space((PARTTYPE_FREE, PARTTYPE_RESERVED), PARTSIZE_BIOS_GRUB, PARTSIZE_BIOS_GRUB)
		self.debug('ask_create_biosboot_part_callback: result=%s' % pretty_format(result))
		if result:
			size, diskname, part_start = result
			self.sub.part_create_generic(diskname, part_start, '', size, FSTYPE_NONE, PARTTYPE_USED, [PARTFLAG_BIOS_GRUB], 0)

	def ask_create_efi_or_biosgrub_part_callback(self, result):
		self.container['warned_missing_efi_or_biosgrub'] = True

	def incomplete(self):
		self.debug('incomplete')
		root_device=0
		root_fs=0
		boot_fs=None
		partflag_cnt = {}
		mpoint_temp = set()
		for disk in self.container['disk'].keys():
			for part in self.container['disk'][disk]['partitions']:
				if self.container['disk'][disk]['partitions'][part]['num'] > 0 : # only valid partitions
					mpoint = self.container['disk'][disk]['partitions'][part]['mpoint'].strip()

					for flag in self.container['disk'][disk]['partitions'][part]['flag']:
						partflag_cnt.setdefault(flag, 0)
						partflag_cnt[flag] += 1

					if mpoint and mpoint in mpoint_temp:
						return _("Double mount point '%s'") % mpoint
					mpoint_temp.add(mpoint)

					if mpoint == '/':
						if not self.container['disk'][disk]['partitions'][part]['fstype'] in ALLOWED_ROOT_FSTYPES:
							root_fs = self.container['disk'][disk]['partitions'][part]['fstype']
						root_device = 1

					if mpoint == '/boot':
						if not self.container['disk'][disk]['partitions'][part]['fstype'] in ALLOWED_BOOT_FSTYPES:
							boot_fs = self.container['disk'][disk]['partitions'][part]['fstype']

		# check LVM Logical Volumes if LVM is enabled
		if self.container['lvm']['enabled'] and self.container['lvm']['vg'].has_key( self.container['lvm']['ucsvgname'] ):
			vg = self.container['lvm']['vg'][ self.container['lvm']['ucsvgname'] ]
			for lvname in vg['lv'].keys():
				lv = vg['lv'][lvname]
				mpoint = lv['mpoint'].strip()
				if mpoint and mpoint in mpoint_temp:
					return _("Double mount point '%s'") % mpoint
				mpoint_temp.add(mpoint)
				if mpoint == '/':
					if not lv['fstype'] in ALLOWED_ROOT_FSTYPES:
						root_fs = lv['fstype']
					root_device = 1

		if self.container['use_efi'] and not partflag_cnt.get(PARTFLAG_EFI,0) and not self.container['warned_missing_efi_or_biosgrub']:
			result = self.find_largest_free_space((PARTTYPE_FREE, PARTTYPE_RESERVED), PARTSIZE_EFI, PARTSIZE_EFI_MIN)
			self.debug('incomplete: find_largest_free_space=%r' % pretty_format(result))
			if result:
				msglist = [ _('The extensible firmware interface (EFI) has been detected'),
							_('on your system but no EFI system partition has been'),
							_('defined. You may continue, but your installation may not'),
							_('be bootable.'),
							_('This message is shown only once.'),
							'',
							_('Create small EFI partition automatically?'),
							]
				self.sub.sub = yes_no_win(self, self.sub.minY, self.sub.minX, self.sub.maxWidth, len(msglist)+6, msglist, default='yes',
										  btn_name_yes=_('Create EFI partition'), btn_name_no=_('Ignore'),
										  callback_yes=self.ask_create_efi_part_callback, callback_no=self.ask_create_efi_or_biosgrub_part_callback)
				self.sub.sub.draw()
				return 1
			else:
				msglist = [ _('The extensible firmware interface (EFI) has been detected'),
							_('on your system but no EFI system partition has been'),
							_('defined (min. 32MiB). You may continue, but your installation'),
							_('may not be bootable.'),
							_('This message is shown only once.'),
							]
				self.sub.sub = msg_win(self, self.sub.minY, self.sub.minX+2, self.sub.maxWidth, len(msglist)+6, msglist)
				self.sub.sub.draw()
				self.container['warned_missing_efi_or_biosgrub'] = True
				return 1


		if not self.container['use_efi'] and not partflag_cnt.get(PARTFLAG_BIOS_GRUB,0) and not self.container['warned_missing_efi_or_biosgrub']:
			result = self.find_largest_free_space((PARTTYPE_FREE, PARTTYPE_RESERVED), PARTSIZE_BIOS_GRUB, PARTSIZE_BIOS_GRUB)
			self.debug('incomplete: find_largest_free_space=%r' % pretty_format(result))
			if result:
				msglist = [ _('A BIOS boot partition is missing in your selected'),
							_('partition setup. Your installation may not be bootable'),
							_('without further modifications.'),
							_('This message is shown only once.'),
							'',
							_('Create BIOS boot partition automatically?'),
							]
				self.sub.sub = yes_no_win(self, self.sub.minY, self.sub.minX, self.sub.maxWidth, len(msglist)+6, msglist, default='yes',
										  btn_name_yes=_('Create partition'), btn_name_no=_('Ignore'),
										  callback_yes=self.ask_create_biosboot_part_callback, callback_no=self.ask_create_efi_or_biosgrub_part_callback)
				self.sub.sub.draw()
				return 1
			else:
				msglist = [ _('A BIOS boot partition is missing in your selected'),
							_('partition setup (min. 4MiB). Your installation may'),
							_('not be bootable without further modifications.'),
							_('This message is shown only once.'),
							]
				self.sub.sub = msg_win(self, self.sub.minY, self.sub.minX, self.sub.maxWidth, len(msglist)+6, msglist)
				self.sub.sub.draw()
				self.container['warned_missing_efi_or_biosgrub'] = True
				return 1

		if not root_device:
			#self.move_focus( 1 )
			return _("Missing '/' as mount point")

		if root_fs:
			#self.move_focus( 1 )
			return _("Wrong file system type '%s' for mount point '/'") % root_fs

		if boot_fs:
			#self.move_focus( 1 )
			return _("Wrong file system type '%s' for mount point '/boot'") % boot_fs

		# check if LVM is enabled, /-partition is LVM LV and /boot is missing
		rootfs_is_lvm = False
		bootfs_is_lvm = None
		# check for /boot on regular partition
		for disk in self.container['disk'].keys():
			for part in self.container['disk'][disk]['partitions']:
				if self.container['disk'][disk]['partitions'][part]['num'] > 0 : # only valid partitions
					mpoint = self.container['disk'][disk]['partitions'][part]['mpoint'].strip()
					if mpoint == '/boot':
						bootfs_is_lvm = False
		if self.container['lvm']['enabled'] and self.container['lvm']['vg'].has_key( self.container['lvm']['ucsvgname'] ):
			vg = self.container['lvm']['vg'][ self.container['lvm']['ucsvgname'] ]
			for lvname in vg['lv'].keys():
				mpoint = vg['lv'][ lvname ]['mpoint'].strip()
				if mpoint == '/':
					rootfs_is_lvm = True
				if mpoint == '/boot':
					bootfs_is_lvm = True
		self.debug('bootfs_is_lvm=%s  rootfs_is_lvm=%s' % (bootfs_is_lvm, rootfs_is_lvm))
		if rootfs_is_lvm and bootfs_is_lvm in [ None, True ]:
			msglist= [ _('Unable to create bootable config!'),
					   _('/-partition is located on LVM and'),
					   _('/boot-partition is missing or located'),
					   _('on LVM too.') ]
			self.sub.sub=msg_win(self.sub, self.sub.minY+(self.sub.maxHeight/8)+2,self.sub.minX+(self.sub.maxWidth/8),1,1, msglist)
			self.sub.sub.draw()
			return 1

		if bootfs_is_lvm:
			return _('Unbootable config! /boot needs non LVM partition')

		if self.container['history'] or self.test_changes():
			self.sub.sub=self.sub.verify_exit(self.sub,self.sub.minY+(self.sub.maxHeight/3)+2,self.sub.minX+(self.sub.maxWidth/8),self.sub.maxWidth,self.sub.maxHeight-18)
			self.sub.sub.draw()
			return 1

	def profile_f12_run(self):
		self.debug('profile_f12_run')
		# send the F12 key event to the subwindow
		if hasattr(self.sub, 'sub'):
			self.sub.sub.input(276)
			if not hasattr(self.sub.sub, 'sub'):
				self.sub.sub.exit()
			return 1
		if len(self.container['history']) or self.test_changes():
			self.sub.sub=self.sub.verify_exit(self.sub,self.sub.minY+(self.sub.maxHeight/3)+2,self.sub.minX+(self.sub.maxWidth/8),self.sub.maxWidth,self.sub.maxHeight-18)
			self.sub.draw()
			return 1

	def test_changes(self):
		for disk in self.container['disk'].keys():
			for part in self.container['disk'][disk]['partitions']:
				if self.container['disk'][disk]['partitions'][part]['format']:
					return 1
		return 0

	def helptext(self):
		return ""

	def modheader(self):
		return _('Partitioning')

	def profileheader(self):
		return 'Partitioning'

	def detect_EFI_system(self):
		efi_found = os.path.isdir('/sys/firmware/efi')
		self.debug('detect_EFI_system: efi_found=%s' % efi_found)
		for arguments in (self.all_results, self.cmdline):
			if 'use_efi' in arguments:
				self.debug('detect_EFI_system: arguments use_efi=%s' % arguments['use_efi'])
				if arguments['use_efi'].lower() in ('no',):
					efi_found = False
				elif arguments['use_efi'].lower() in ('yes',):
					efi_found = True
		return efi_found

	def start(self):
		''' Initialize data structures, scan devices and read partition information from them '''
		# self.container['problemdisk'][<devicename>] = set([DISKLABEL_GPT, DISKLABEL_UNKNOWN, ...])

		self.debug('ALL RESULTS=%r' % self.all_results)
		self.debug('CMDLINE=%r' % self.cmdline)

		self.container={}
		self.container['debug'] = ''
		self.container['module_disabled'] = False
		self.container['profile'] = {}
		disks, problemdisks, problemmessages = self.read_devices()
		self.container['disk'] = disks
		self.container['problemdisk'] = problemdisks
		self.container['problemmessages'] = problemmessages
		self.container['history'] = []
		self.container['temp'] = {}
		self.container['selected'] = 1
		self.container['autopartition'] = None
		self.container['autopart_prunelvm'] = None
		self.container['warned_missing_efi_or_biosgrub'] = False
		self.container['lvm'] = {}
		self.container['lvm']['enabled'] = None
		self.container['lvm']['lvm1available'] = False
		self.container['lvm']['warnedlvm1'] = False
		self.container['lvm']['ucsvgname'] = None
		self.container['lvm']['lvmconfigread'] = False
		self.container['disk_checked'] = False
		self.container['partitiontable_checked'] = False
		self.container['use_efi'] = self.detect_EFI_system()

	def profile_autopart(self, disklist_blacklist = [], part_delete = 'all' ):
		self.debug('PROFILE BASED AUTOPARTITIONING:')

		# add all physical partitions for deletion
		self.all_results['part_delete'] = part_delete

		# add all logical volumes for deletion
		tmpstr = ''
		for vgname in self.container['lvm']['vg'].keys():
			tmpstr += ' /dev/%s' % vgname
		self.all_results['lvm_delete'] = tmpstr.strip()

		# remove all existing dev_N entries
		regex = re.compile('^dev_\d+$')
		for key in self.all_results.keys():
			if regex.match(key):
				self.debug('AUTOPART-PROFILE: deleting self.all_results[%s]' % key)
				del self.all_results[key]

		# get system memory
		p = os.popen('free')
		data = p.read()
		p.close()
		regex = re.compile('^\s+Mem:\s+(\d+)\s+.*$')
		sysmem = -1
		for line in data.splitlines():
			match = regex.match(line)
			if match:
				sysmem = int(match.group(1)) * 1024 # value read from "free" is given in KiB and has to be converted to bytes
		self.debug('AUTOPART-PROFILE: sysmem=%s' % sysmem)

		# calc disk sizes
		disklist = {}
		disksizeall = 0
		for diskname in self.container['disk'].keys():
			if diskname in disklist_blacklist:
				self.debug('AUTOPART-PROFILE: disk %s is blacklisted' % diskname)
			else:
				disksize = 0
				for part in self.container['disk'][diskname]['partitions'].values():
					disksize += part['size']
				disklist[diskname] = disksize
				disksizeall += disksize
		self.debug('AUTOPART-PROFILE: disklist=%s' % disklist)

		# define default partitions: add EFI partition if EFI system has been recognized
		required_partitions = []
		if self.container['use_efi']:
			required_partitions.append(('efi', PARTSIZE_EFI, FSTYPE_EFI, MOUNTPOINT_EFI, PARTFLAG_EFI))
		else:
			# otherwise add BIOS boot partition for GRUB
			required_partitions.append(('biosgrub', PARTSIZE_BIOS_GRUB, 'None', 'None', PARTFLAG_BIOS_GRUB))
		required_partitions.append(('/boot', PARTSIZE_BOOT, 'ext4', '/boot', PARTFLAG_NONE))

		# place partitions
		dev_i = 0
		added = set()
		rootsize = 0
		disklist_sorted = disklist.keys()
		disklist_sorted.sort()
		for diskname in disklist_sorted:
			disksize = disklist[diskname]
			sizeused = EARLIEST_START_OF_FIRST_PARTITION
			partnum = 1

			for name, size, fstype, mpoint, flag in required_partitions:
				if not name in added and size < disksize:
					start = sizeused
					end = sizeused + size
					self.all_results['dev_%d' % dev_i] = 'PHY %s%d 0 1 %s %dMiB %dMiB %s %s' % (diskname, partnum, fstype, B2MiB(start), B2MiB(end), mpoint, flag)
				dev_i += 1
				partnum += 1
				disksize -= size
				sizeused += size
				added.add(name)

			if not 'swap' in added and PARTSIZE_SWAP_MIN < disksize:
				swapsize = 2 * sysmem
				if swapsize > PARTSIZE_SWAP_MAX:
					swapsize = PARTSIZE_SWAP_MAX
				while (disksize < swapsize) and (disksizeall < PARTSIZE_BIOS_GRUB + PARTSIZE_EFI + PARTSIZE_BOOT + PARTSIZE_SYSTEM_MIN + swapsize):
					swapsize -= MiB2B(16)
					if swapsize < PARTSIZE_SWAP_MIN:
						swapsize = PARTSIZE_SWAP_MIN

				start = sizeused
				end = sizeused + swapsize
				self.all_results['dev_%d' % dev_i] = 'PHY %s%d 0 1 linux-swap %dMiB %dMiB None linux-swap' % (diskname, partnum, B2MiB(start), B2MiB(end))
				dev_i += 1
				partnum += 1
				disksize -= swapsize
				sizeused += swapsize
				added.add('swap')

			# accumulate size of LVM volumes to get final size of rootfs
			rootsize += disksize
			if (disksize + sizeused > RESERVED_SPACE_AT_END_OF_DISK):
				rootsize -= RESERVED_SPACE_AT_END_OF_DISK

			# use rest of disk als LVM PV
			self.all_results['dev_%d' % dev_i] = 'PHY %s%d 0 1 None %dMiB 0 None lvm' % (diskname, partnum, B2MiB(sizeused))
			dev_i += 1

		self.all_results['dev_%d' % dev_i] = 'LVM /dev/vg_ucs/rootfs LVMLV 0 ext4 0 %dMiB / None' % B2MiB(rootsize)
		dev_i += 1

		for key in [ x for x in self.all_results.keys() if x.startswith('dev_') ]:
			self.debug('AUTOPART-PROFILE: %s="%s"' % (key, self.all_results[key]))

#dev_0="LVM /dev/vg_ucs/rootfs LVMLV 0 ext3 0M 7000M / None"
#dev_1="PHY /dev/sdb2 0 0 ext3 500.01M 596.01M /boot None"
#dev_2="PHY /dev/sda1 0 0 None 0.01M 0 None lvm,boot"
#dev_3="PHY /dev/sdb3 0 0 None 596.01M 0 None lvm,boot"
#dev_4="PHY /dev/sdb1 0 0 linux-swap 0.01M 500.01M None None"
#dev_5="LVM /dev/vg_ucs/homefs LVMLV 0 ext3 0M 2000M /home None"

	def read_profile(self):
		self.debug('read_profile')
		self.container['result'] = {}
		self.container['profile']['delete'] = {}
		self.container['profile']['create'] = {}
		self.container['profile']['lvmlv'] = {}
		self.container['profile']['lvmlv']['create'] = {}
		self.container['profile']['lvmlv']['delete'] = {}

		# disable module if partition table type in profile does not match 'GPT'
		if self.all_results.get('partitiontable_type','').lower() not in ('gpt',):
			self.container['module_disabled'] = True
			return

		# create disk list with usb storage devices
		disklist_usbstorage = self.get_usb_storage_device_list()

		if 'create_partitiontable' in self.all_results:
			diskchanged = False
			for dev in re.split('[\s,]+', self.all_results.get('create_partitiontable','')):
				dev = dev.strip()
				if dev:
					self.debug('read_profile: installing new partition table on device %r' % dev)
					self.install_fresh_gpt(dev)
					diskchanged = True
			if diskchanged:
				# rereading partition tables
				self.debug('read_profile: rereading partition tables after altering some of them')
				disks, problemdisks, problemmessages = self.read_devices()
				self.container['disk'] = disks
				self.container['problemdisk'] = problemdisks
				self.container['problemmessages'] = problemmessages

		if self.all_results.get('auto_part') in ['yes']: # as of UCS 3.2-0 "yes" is the new standard;  in prior version 'full_disk' and 'full_disk_usb' have been valid
			self.debug('read_profile: auto_part key found: %r' % self.all_results.get('auto_part'))
			disklist = sorted(self.container['disk'].keys())
			if disklist:
				first_disk = disklist[0]
				other_disks = disklist[1:]
				self.debug('read_profile: performing auto partitioning on disk %r  (blacklist=%r)' % (first_disk, other_disks))
				self.profile_autopart( disklist_blacklist = other_disks, part_delete = 'all' )
		else:
			self.debug('read_profile: no auto_part key found or not activated (%r)' % (self.all_results.get('auto_part'),))

		for key in self.all_results.keys():
			self.debug('read_profile: key=%s' % key)
			delete_all_lvmlv = False
			if key == 'part_delete':
				delete=self.all_results['part_delete'].replace("'","").split(' ')
				self.debug('part_delete=%r' % (delete,))
				self.debug('disklist_usbstorage=%r' % (disklist_usbstorage,))
				for entry in delete:
					if entry in [ 'all', 'all_usb' ]: # delete all existing partitions (all_usb) or all existing partitions exclusive usb storage devices (all)
						# PLEASE NOTE:
						# part_delete=all does also delete ALL logical volumes and ALL volume groups on any LVMPV.
						# Even if LVMPV is located on a usb storage device LVMLV and LVMVG will be deleted!

						self.debug('Deleting all partitions')

						# if all partitions shall be deleted all volumegroups prior have to be deleted
						if not self.all_results.has_key('lvmlv_delete'):
							delete_all_lvmlv = True
							s = ''
							for vg in self.container['lvm']['vg'].keys():
								s += ' ' + vg
							self.all_results['lvmlv_delete'] = s.strip()
							self.debug('lvmlv_delete not found; adding it automagically: lvmlv_delete=%s' % self.all_results['lvmlv_delete'])

						for disk in self.container['disk'].keys():
							# continue if usb storage devices shall also be deleted or
							# disk is not in usb storage device list
							if entry == 'all' and disk in disklist_usbstorage:
								self.debug('read_profile: new syntax: disk %s is usb storage device and blacklisted' % disk)
							if entry == 'all_usb' or disk not in disklist_usbstorage:
								if len(self.container['disk'][disk]['partitions'].keys()):
									self.container['profile']['delete'][disk]=[]
								for part in self.container['disk'][disk]['partitions'].keys():
									if self.container['disk'][disk]['partitions'][part]['num'] > 0:
										self.container['profile']['delete'][disk].append(self.container['disk'][disk]['partitions'][part]['num'])

					elif self.test_old_device_syntax(entry):
						disk, partnum = self.test_old_device_syntax(entry)

						# continue if usb storage devices shall also be deleted or
						# disk is not in usb storage device list
						if entry == 'all' and disk in disklist_usbstorage:
							self.debug('read_profile: old syntax: disk %s is usb storage device and blacklisted' % disk)
						if entry == 'all_usb' or disk not in disklist_usbstorage:
							if not self.container['profile']['delete'].has_key(disk):
								self.container['profile']['delete'][disk]=[]

							if not partnum and self.container['disk'].has_key(disk) and len(self.container['disk'][disk]['partitions'].keys()):
								# case delete complete /dev/sda
								for part in self.container['disk'][disk]['partitions'].keys():
									self.container['profile']['delete'][disk].append(self.container['disk'][disk]['partitions'][part]['num'])
							else:
								self.container['profile']['delete'][disk].append(partnum)

			if key == 'lvmlv_delete' or delete_all_lvmlv:
				lvmdelete=self.all_results['lvmlv_delete'].replace("'","").split(' ')
				for entry in lvmdelete:
					# /dev/vgname         ==> delete all LVs in VG
					# /dev/vgname/        ==> delete all LVs in VG
					# /dev/vgname/*       ==> delete all LVs in VG
					# /dev/vgname/lvname  ==> delete specific LV in VG
					# vgname              ==> delete all LVs in VG
					# vgname/lvname       ==> delete specific LV in VG
					dev = entry.rstrip(' /*')
					if dev.startswith('/dev/'):
						dev = dev[5:]
					if dev.count('/'):
						vgname, lvname = dev.split('/',1)
						self.debug('deleting LV %s of VG %s' % (lvname, vgname))
						if self.container['lvm']['vg'].has_key(vgname):
							if self.container['lvm']['vg'][vgname]['lv'].has_key(lvname):
								self.container['profile']['lvmlv']['delete'][ entry ] = { 'lv': lvname,
																						  'vg': vgname }
							else:
								self.debug('WARNING: LVM LV %s not found in VG %s! Ignoring it' % (lvname, vgname))
						else:
							self.debug('WARNING: LVM VG %s not found! Ignoring it' % vgname)
					else:
						vgname = dev
						self.debug('deleting whole VG %s' % vgname)
						if self.container['lvm']['vg'].has_key(vgname):
							self.container['profile']['lvmlv']['delete'][ entry ] = { 'lv': '',
																					  'vg': vgname }
						else:
							self.debug('WARNING: LVM VG %s not found! Ignoring it' % vgname)

			elif self.get_device_entry(key): # test for matching syntax (dev_sda2, /dev/sda2, dev_2 etc)
				self.debug('profread: key=%s  val=%s' % (key, self.all_results[key]))
				parttype, device, parms = self.get_device_entry(key)
				parms=parms.replace("'","").split()

				self.container['result'][key] = ''

				if parttype == 'PHY':
					disk, partnum = self.test_old_device_syntax(device)
					if not self.container['profile']['create'].has_key(disk):
						self.container['profile']['create'][disk]={}
					if len(parms) >= 5:
						flags = []
						if len(parms) < 6 or parms[5] == 'None' or parms[5] == FSTYPE_SWAP:
							mpoint = ''
						else:
							mpoint = parms[5]
						if len(parms) >= 7:
							flags = parms[-1].lower().split(',')
							if 'none' in flags or flags == ['']:
								flags = []
							elif PARTFLAG_BIOS_GRUB in flags:
								mpoint = ''
								parms[1] = '0'
							elif PARTFLAG_EFI in flags:
								mpoint = MOUNTPOINT_EFI
								parms[2] = FSTYPE_EFI
						if parms[0] == 'only_mount':
							parms[1]=0

						# parms[0] → partition type (with MSDOS valid values are 0 (primary), 1 (logical) and 2 (extended))
						# GPT does not support logical/extended partitions → these lines will be ignored
						if parms[0].lower() not in ('0', 'only_mount',):
							self.debug('Ignoring line: partition types other than "0" or "only_mount" are invalid with GPT: %r=%r' % (key, parms,))
							continue

						label = get_sanitized_label('', flags, mpoint, parms[2].lower())

						start = get_sanitized_position(parms[3])
						end = get_sanitized_position(parms[4])
						if start is None:
							self.debug('Ignoring line: partition start cannot be parsed correctly: %r' % parms[3])
							continue
						if end is None:
							self.debug('Ignoring line: partition start cannot be parsed correctly: %r' % parms[4])
							continue
						max_end = align_partition_end(self.container['disk'][disk]['max_part_end'])

						start = align_partition_start(start)
						if end == 0:
							end = max_end
						end = align_partition_end(end)
						if end > max_end:
							end = max_end

						temp={
							'type':parms[0],
							'fstype':parms[2].lower(),
							'start': start,
							'end': end,
							'mpoint':mpoint,
							'format':parms[1],
							'flag': flags,
							'label': label,
							}

						self.debug('Added to create physical container: %s' % temp)
						self.container['profile']['create'][disk][partnum]=temp
					else:
						self.debug('Syntax error for key[%s]' % key)

				elif parttype == 'LVM':
					if parms[0] == 'only_mount':
						parms[1]=0
					vgname, lvname = device.split('/')[-2:]         # /dev/VolumeGroup/LogicalVolume

					start = get_sanitized_position(parms[3])
					end = get_sanitized_position(parms[4])
					if start is None:
						self.debug('Ignoring line: LVM partition start cannot be parsed correctly: %r' % parms[3])
						continue
					if end is None:
						self.debug('Ignoring line: LVM partition start cannot be parsed correctly: %r' % parms[4])
						continue

					temp={	'vg': vgname,
							'type':parms[0],
							'format':parms[1],
							'fstype':parms[2].lower(),
							'start': start,
							'end': align_partition_end(end)+1, # align end of partition to megabyte boundaries
							'mpoint':parms[5],
							'flag': parms[6].lower().split(',')
							}
					self.debug('Added to create lvm volume: %s' % temp)
					self.container['profile']['lvmlv']['create'][lvname]=temp
				else:
					self.debug('%s devices in profile unsupported' % parttype)

	def test_old_device_syntax(self, entry):
		result = [ None, 0 ]
		regex = re.compile('(/dev/([a-zA-Z]+)(-?(\d+))?|dev_([a-zA-Z]+)(\d+)?)')  # match /dev/sda, /dev/sda2, /dev/sda-2, dev_sda2
		match = regex.match(entry)
		if match:
			grp = match.groups()
			if grp[1]:
				result[0] = '/dev/%s' % grp[1]
				if grp[3]:
					result[1] = int(grp[3])
			elif grp[4]:
				result[0] = '/dev/%s' % grp[4]
				if grp[5]:
					result[1] = int(grp[5])
		if result[0]:
			self.debug("test_old_device_syntax: result=%s" % result)
			return result
		# cciss
		regex = re.compile('/dev/([^/]+)/([a-zA-Z0-9]+)p(\d+)')
		match = regex.match(entry)
		if match:
			grp = match.groups()
			result[0] = '/dev/%s/%s' % (grp[0], grp[1])
			result[1] = grp[2]
		if result[0]:
			self.debug("test_old_device_syntax: result=%s" % result)
			return result
		return None

	def get_device_entry(self, key):
		value = self.all_results[key]
		result = self.test_old_device_syntax(key)
		if result:
			if result[0] != None:
				return [ 'PHY', '%s%s' % (result[0], result[1]), value ]   # [ PHY, /dev/sda2, LINE ]

		regex = re.compile('^dev_\d+$')
		if regex.match(key):
			if value.startswith('PHY ') or value.startswith('LVM '): # [ PHY|LVM, /dev/sda2, LINE ]
				items = value.split(' ',2)
				return items
		return []

	def parse_syntax(self,entry): # need to test different types of profile
		num=0
		if len(entry.split('/')) > 2 and entry.split('/')[1] == 'dev' and len(entry.split('-')) > 1 and entry.split('-')[1].isdigit(): # got something like /dev/sda-2
			devices=entry.split('-')
			dev=devices[0]
			num=devices[1]
		elif len(entry.split('/')) > 2 and entry.split('/')[1] == 'dev': # got /dev/sda1 /dev/sda
			devices=entry.split('/')[-1]
			i=-1
			while devices[i].isdigit(): # need to find part_num in string
				i-=1
			if i < -1:
				num=int(devices[i+1:])
				dev=entry[:i+1]
			else:
				dev=entry

		elif len(entry.split('_')) > 1 and entry.split('_')[0] == "dev": # got dev_sda1
			devices=entry.split('_')[-1]
			i=-1
			while devices[i].isdigit():
				i-=1
			if i < -1:
				num=int(devices[i+1:])
				dev="/%s" % entry[:i+1].replace('_','/')
			else:
				dev="/%s" % entry.replace('_','/')

		else:
			return  0
		return ["%s" % dev.strip(), num]


	def act_profile(self):
		if not self.written:
			self.act = self.prof_active(self,_('Deleting LVM volumes'),_('Please wait ...'),name='act')
			self.act.action='prof_delete_lvm'
			self.act.draw()
			self.act = self.prof_active(self,_('Deleting partitions'),_('Please wait ...'),name='act')
			self.act.action='prof_delete'
			self.act.draw()
			self.act = self.prof_active(self,_('Creating partitions'),_('Please wait ...'),name='act')
			self.act.action='prof_write'
			self.act.draw()
			self.act = self.prof_active(self,_('Creating LVM volumes'),_('Please wait ...'),name='act')
			self.act.action='prof_write_lvm'
			self.act.draw()
			self.act = self.prof_active(self,_('Formatting partitions'),_('Please wait ...'),name='act')
			self.act.action='prof_format'
			self.act.draw()
			self.written=1

	class prof_active(act_win):
		def get_real_partition_device_name(self, device, number):
			dev_match = None
			#/dev/cXdX
			regex = re.compile(".*c[0-9]d[0-9]*")
			match = re.search(regex,device)
			if match:
				regex = re.compile(".*c[0-9]*d[0-9]*")
				dev_match=re.search(regex,match.group())

			if dev_match:
				return '%sp%s' % (dev_match.group(), number)
			return '%s%s' % (device, number)

		def run_cmd(self, cmd, log_stdout=True, log_stderr=True):
			self.parent.debug('(profile) run_cmd(%r)' % (cmd,))
			proc = subprocess.Popen(cmd, bufsize=0, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			(stdout, stderr) = proc.communicate()
			self.parent.debug('===(exitcode=%d)====' % proc.returncode)
			if stdout and log_stdout:
				self.parent.debug('stdout of %r:\n=> %s' % (cmd, '\n=> '.join(stdout.split('\n'))))
			if stderr and log_stderr:
				self.parent.debug('stderr of %r:\n=> %s' % (cmd, '\n=> '.join(stderr.split('\n'))))
			return '%s\n%s' % (stdout, stderr)

		def function(self):
			if self.action == 'prof_read_lvm':
				self.parent.debug('prof_read_lvm')
				self.parent.read_lvm()

			elif self.action == 'prof_delete_lvm':
				self.parent.debug('prof_delete_lvm')
				for entry in self.parent.container['profile']['lvmlv']['delete'].values():
					device = entry['vg']
					if entry['lv']:
						device += '/%s' % entry['lv']
					self.run_cmd(['/sbin/lvremove', '-f', device])

				# cleanup all known LVM volume groups
				for vgname, vg in self.parent.container['lvm']['vg'].items():
					self.run_cmd(['/sbin/vgreduce', '-a', '--removemissing', vgname])

			elif self.action == 'prof_delete':
				self.parent.debug('prof_delete')
				for disk in self.parent.container['profile']['delete'].keys():
					num_list=self.parent.container['profile']['delete'][disk]
					num_list.reverse()
					for num in num_list:
						# remove LVM PV signature if LVM partition
						device = self.get_real_partition_device_name(disk,num)
						if device in self.parent.container['lvm']['pv'].keys():
							self.parent.debug('%s in LVM PV' % device)
							pv = self.parent.container['lvm']['pv'][device]
							if pv['vg']:
								testoutput = self.run_cmd(['/sbin/vgreduce', '-t', pv['vg'], device])
								if "Can't remove final physical volume" in testoutput:
									self.run_cmd(['/sbin/vgremove', pv['vg']])
								else:
									self.run_cmd(['/sbin/vgreduce', pv['vg'], device])
								self.run_cmd(['/sbin/wrapper-yes-pvremove', '-ff', device])

						self.run_cmd(['/sbin/parted', '--script', str(disk), 'p', 'rm', str(num)])

				# cleanup all known LVM volume groups
				for vgname, vg in self.parent.container['lvm']['vg'].items():
					self.run_cmd(['/sbin/vgreduce', '-a', '--removemissing', vgname])

			elif self.action == 'prof_write':
				vgcreated = False
				self.parent.debug('prof_write')
				for disk in self.parent.container['profile']['create'].keys():
					bootable = False
					num_list=self.parent.container['profile']['create'][disk].keys()
					num_list.sort()
					for num in num_list:
						parttype = self.parent.container['profile']['create'][disk][num]['type']
						flaglist = self.parent.container['profile']['create'][disk][num]['flag']
						fstype = self.parent.container['profile']['create'][disk][num]['fstype']
						start = self.parent.container['profile']['create'][disk][num]['start']
						end = self.parent.container['profile']['create'][disk][num]['end']
						label = self.parent.container['profile']['create'][disk][num]['label']
						device = self.get_real_partition_device_name(disk,num)

						if PARTFLAG_BIOS_GRUB in flaglist:
							bootable = True

						# do not create partitions if only_mount is set
						if parttype == "only_mount":
							self.parent.debug('will not create partition %s%s due type == %s' % (disk, num, parttype))
							continue

						# WARNING: parted is kind of broken and requires a quoted label as argument → i.e. the value is double quoted
						self.run_cmd(['/sbin/parted', '--script', disk, 'unit', 'B', 'mkpart', '"%s"' % label, str(start), str(end)])
						if fstype and not fstype.lower() in ('none',):
							mkfs_cmd = get_mkfs_cmd(device, fstype)
							self.parent.debug('mkfs_cmd=%r   (%r, %r)' % (mkfs_cmd, device, fstype))
							if mkfs_cmd:
								self.run_cmd(mkfs_cmd)
							else:
								self.parent.debug('ERROR: unknown filesystem for %r specified: %r' % (device, fstype))
						for flag in flaglist:
							if flag not in VALID_PARTED_FLAGS:
								continue
							self.parent.debug('%s%s: setting flag %s' % (disk, num, flag))
							self.run_cmd(['/sbin/parted', '-s', str(disk), 'set', str(num), flag, 'on'])
						if PARTFLAG_LVM in flaglist:
							self.parent.debug('%s: lvm flag' % device)
							ucsvgname = self.parent.container['lvm']['ucsvgname']
							self.run_cmd(['/sbin/pvcreate', device])
							if not vgcreated:
								self.run_cmd(['/sbin/vgcreate', '--physicalextentsize',
											  '%sk' % B2KiB(self.parent.container['lvm']['vg'][ ucsvgname ]['PEsize']),
											  ucsvgname, device])
								vgcreated = True
							self.run_cmd(['/sbin/vgextend', ucsvgname, device])
					if bootable:
						self.parent.fix_boot_flag_in_protective_mbr(disk)


			elif self.action == 'prof_write_lvm':
				self.parent.debug('prof_write_lvm')
				for lvname, lv in self.parent.container['profile']['lvmlv']['create'].items():
					vg = self.parent.container['lvm']['vg'][ lv['vg'] ]
					size = lv['end'] - lv['start']
					self.parent.debug('creating LV: start=%s  end=%s  size=%s' % (lv['start'], lv['end'], size))

					currentLE = int(size / vg['PEsize'])
					if size % vg['PEsize']: # number of logical extents has to cover at least "size" bytes
						currentLE += 1

					self.run_cmd(['/sbin/lvcreate', '-l', str(currentLE), '--name', lvname, lv['vg']])

			elif self.action == 'prof_format':
				self.parent.debug('prof_format')
				for disk in self.parent.container['profile']['create'].keys():
					num_list=self.parent.container['profile']['create'][disk].keys()
					num_list.sort()
					for num in num_list:
						fstype = self.parent.container['profile']['create'][disk][num]['fstype']
						format = self.parent.container['profile']['create'][disk][num]['format']

						# do not create fs on partitions if format is 0
						if format in [ 0, "0" ] and not self.parent.all_results.get('part_delete', "") == "all":
							self.parent.debug('will not create fs on partition %s%s due format == %s' % (disk, num, format))
							continue

						device = self.get_real_partition_device_name(disk,num)
						mkfs_cmd = get_mkfs_cmd(device, fstype)
						self.parent.debug('mkfs_cmd=%r   (%r, %r)' % (mkfs_cmd, device, fstype))
						if mkfs_cmd:
							self.run_cmd(mkfs_cmd)
						else:
							self.parent.debug('ERROR: unknown fstype (%s) for %s' % (fstype, self.get_real_partition_device_name(disk,num)))

				for lvname, lv in self.parent.container['profile']['lvmlv']['create'].items():
					device = '/dev/%s/%s' % (lv['vg'], lvname)
					fstype = lv['fstype'].lower()
					format = lv['format']

					# do not create fs on partitions if format is 0
					if format in [ 0, "0" ] and not self.parent.all_results.get('part_delete', "") == "all":
						self.parent.debug('will not create fs on %s due format == %s' % (lvname, format))
						continue

					mkfs_cmd = get_mkfs_cmd(device, fstype)
					self.parent.debug('mkfs_cmd=%r   (%r, %r)' % (mkfs_cmd, device, fstype))
					if mkfs_cmd:
						self.run_cmd(mkfs_cmd)
					else:
						self.parent.debug('ERROR: unknown fstype (%s) for %s' % (fstype, device))

			self.stop()

	def run_cmd(self, cmd, log_stdout=True, log_stderr=True):
		self.debug('run_cmd(%r)' % (cmd,))
		proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdout, stderr) = proc.communicate()
		self.debug('===(exitcode=%d)====' % proc.returncode)
		if stdout and log_stdout:
			self.debug('stdout of %r:\n=> %s' % (cmd, '\n=> '.join(stdout.split('\n'))))
		if stderr and log_stderr:
			self.debug('stderr of %r:\n=> %s' % (cmd, '\n=> '.join(stderr.split('\n'))))

		return (stdout, stderr)

	def detect_filesystem(self, device):
		data = self.run_cmd(['/bin/file', '-Ls', device])[0]
		fstype=''
		if 'SGI XFS filesystem data' in data:
			fstype = 'xfs'
		elif 'ext2 filesystem data' in data:
			fstype = 'ext2'
		elif 'ext3 filesystem data' in data:
			fstype = 'ext3'
		elif 'ext4 filesystem data' in data:
			fstype = 'ext4'
		elif 'swap file' in data and 'Linux' in data:
			fstype = FSTYPE_SWAP
		elif 'BTRFS Filesystem' in data:
			fstype = 'btrfs'
		elif 'FAT (16 bit)' in data:
			fstype = 'fat16'
		elif 'FAT (32 bit)' in data:
			fstype = 'fat32'
		return fstype

	def read_lvm_pv(self):
		self.debug('read_lvm_pv()')
		content = self.run_cmd(['/sbin/pvdisplay', '-c'])[0]
		#  /dev/sdb4:vg_member50:3907584:-1:8:8:-1:4096:477:477:0:dEMYyK-EdEu-uXvk-OS39-IeBe-whg1-c8fTCF

		for line in content.splitlines():
			# ignore invalid lines
			if line.strip().count(':') < 10:
				continue

			item = line.strip().split(':')

			self.container['lvm']['pv'][ item[0] ] = { 'touched': 0,
													   'vg': item[1],
													   'PEsize': KiB2B(int(item[7])), # physical extent size is returned in KiB but stored in bytes
													   'totalPE': int(item[8]),
													   'freePE': int(item[9]),
													   'allocPE': int(item[10]),
													   }

	def read_lvm_vg(self):
		self.debug('read_lvm_vg()')
		content = self.run_cmd(['/sbin/vgdisplay'])[0]
		for line in content.splitlines():
			if ' Format ' in line and 'lvm1' in line:
				self.container['lvm']['lvm1available'] = True

		content = self.run_cmd(['/sbin/vgdisplay', '-c'])[0]
		#  vg_member50:r/w:772:-1:0:0:0:-1:0:2:2:2940928:4096:718:8:710:B2oHiE-D06t-g4eM-lblN-ELf2-KAYH-ef3CxX

		# get available VGs
		for line in content.splitlines():
			# ignore invalid lines
			if line.strip().count(':') < 10:
				continue

			item = line.strip().split(':')
			self.container['lvm']['vg'][ item[0] ] = { 'touched': 0,
													   'PEsize': KiB2B(int(item[12])), # physical extent size is returned in KiB but stored in bytes
													   'totalPE': int(item[13]),
													   'allocPE': int(item[14]),
													   'freePE': int(item[15]),
													   'size': KiB2B(int(item[12]))*int(item[13]), # size of VG in bytes
													   'created': 1,
													   'lv': {}
													   }

	def read_lvm_lv(self):
		self.debug('read_lvm_lv()')
		content = self.run_cmd(['/sbin/lvdisplay', '-c'])[0]
		#  /dev/ucsvg/ucsvg-vol1:ucsvg:3:1:-1:0:819200:100:-1:0:0:254:0
		#  /dev/ucsvg/ucsvg-vol2:ucsvg:3:1:-1:0:311296:38:-1:0:0:254:1
		#  /dev/ucsvg/ucsvg_vol3:ucsvg:3:1:-1:0:204800:25:-1:0:0:254:2

		# get available LVs
		for line in content.splitlines():
			# ignore invalid lines
			if line.strip().count(':') < 10:
				continue

			item = line.strip().split(':')
			vg = item[1]
			pesize = self.container['lvm']['vg'][ vg ]['PEsize']
			lvname = item[0].split('/')[-1]

			# determine filesystem on device item[0]
			fstype = self.detect_filesystem(item[0])

			self.container['lvm']['vg'][ item[1] ]['lv'][ lvname ] = {  'dev': item[0],
																		'vg': item[1],
																		'touched': 0,
																		'PEsize': pesize, # physical extent size in bytes
																		'currentLE': int(item[7]),
																		'format': 0,
																		'size': int(item[7]) * pesize, # size of LV in bytes
																		'fstype': fstype,
																		'flag': '',
																		'mpoint': '',
																		}

	def enable_all_vg(self):
		self.run_cmd(['/sbin/vgchange', '-ay'], True, True)

	def disable_all_vg(self):
		self.run_cmd(['/sbin/vgchange', '-an'], True, True)

	def read_lvm(self):
		# read initial LVM status
		self.container['lvm']['pv'] = {}
		self.container['lvm']['vg'] = {}
		self.read_lvm_pv()
		self.read_lvm_vg()
		self.read_lvm_lv()
		self.enable_all_vg()
		if len(self.container['lvm']['vg'].keys()) > 0:
			self.container['lvm']['enabled'] = True
		self.container['lvm']['lvmconfigread'] = True

	def set_lvm(self, flag, vgname = None):
		self.container['lvm']['enabled'] = flag
		if flag:
			if vgname:
				self.container['lvm']['ucsvgname'] = vgname
			else:
				self.container['lvm']['ucsvgname'] = 'vg_ucs'
			self.debug( 'LVM enabled: lvm1available=%s  ucsvgname="%s"' %
						(self.container['lvm']['lvm1available'], self.container['lvm']['ucsvgname']))
			if not self.container['lvm']['vg'].has_key( self.container['lvm']['ucsvgname'] ):
				self.container['lvm']['vg'][ self.container['lvm']['ucsvgname'] ] = { 'touched': 1,
																					  'PEsize': KiB2B(4096), # physical extent size in bytes (4096 KiB)
																					  'totalPE': 0,
																					  'allocPE': 0,
																					  'freePE': 0,
																					  'size': 0,
																					  'created': 0,
																					  'lv': {}
																					  }

	def read_devices(self):
		self.debug('entering read_devices')
		if os.path.exists('/lib/univention-installer/partitions'):
			fd = open('/lib/univention-installer/partitions')
			self.debug('Reading from /lib/univention-installer/partitions')
		else:
			fd = open('/proc/partitions')
			self.debug('Reading from /proc/partitions')
		proc_partitions = fd.readlines()
		devices=[]
		for line in proc_partitions[2:]:
			cols=line.split()
			if len(cols) >= 4  and cols[0] != 'major':
				dev_match = None
				self.debug('Testing Entry /dev/%s ' % cols[3])
				# /dev/hdX
				regex = re.compile(".*hd[a-z]([0-9]*)$")
				match = re.search(regex,cols[3])
				if match:
					regex = re.compile(".*hd[a-z]*")
					dev_match=re.search(regex,match.group())
				#/dev/sdX
				regex = re.compile(".*sd[a-z]([0-9]*)$")
				match = re.search(regex,cols[3])
				if match:
					regex = re.compile(".*sd[a-z]*")
					dev_match=re.search(regex,match.group())
				#/dev/mdX
				regex = re.compile(".*md([0-9]*)$")
				match = re.search(regex,cols[3])
				if match:
					regex = re.compile(".*md*")
					dev_match=re.search(regex,match.group())
				#/dev/xdX
				regex = re.compile(".*xd[a-z]([0-9]*)$")
				match = re.search(regex,cols[3])
				if match:
					regex = re.compile(".*xd[a-z]*")
					dev_match=re.search(regex,match.group())
				#/dev/adX
				regex = re.compile(".*ad[a-z]([0-9]*)$")
				match = re.search(regex,cols[3])
				if match:
					regex = re.compile(".*ad[a-z]*")
					dev_match=re.search(regex,match.group())
				#/dev/edX
				regex = re.compile(".*ed[a-z]([0-9]*)$")
				match = re.search(regex,cols[3])
				if match:
					regex = re.compile(".*ed[a-z]*")
					dev_match=re.search(regex,match.group())
				#/dev/pdX
				regex = re.compile(".*pd[a-z]([0-9]*)$")
				match = re.search(regex,cols[3])
				if match:
					regex = re.compile(".*pd[a-z]*")
					dev_match=re.search(regex,match.group())
				#/dev/pfX
				regex = re.compile(".*pf[a-z]([0-9]*)$")
				match = re.search(regex,cols[3])
				if match:
					regex = re.compile(".*pf[a-z]*")
					dev_match=re.search(regex,match.group())
				#/dev/vdX
				regex = re.compile(".*vd[a-z]([0-9]*)$")
				match = re.search(regex,cols[3])
				if match:
					regex = re.compile(".*vd[a-z]*")
					dev_match=re.search(regex,match.group())
				#/dev/dasdX
				regex = re.compile(".*dasd[a-z]([0-9]*)$")
				match = re.search(regex,cols[3])
				if match:
					regex = re.compile(".*dasd[a-z]*")
					dev_match=re.search(regex,match.group())
				#/dev/dptiX
				regex = re.compile(".*dpti[a-z]([0-9]*)")
				match = re.search(regex,cols[3])
				if match:
					regex = re.compile(".*dpti[0-9]*")
					dev_match=re.search(regex,match.group())
				#/dev/cXdX
				regex = re.compile(".*c[0-9]d[0-9]*")
				match = re.search(regex,cols[3])
				if match:
					regex = re.compile(".*c[0-9]*d[0-9]*")
					dev_match=re.search(regex,match.group())
				#/dev/arX
				regex = re.compile(".*ar[0-9]*")
				match = re.search(regex,cols[3])
				if match:
					regex = re.compile(".*ar[0-9]*")
					dev_match=re.search(regex,match.group())

				if dev_match:
					devices.append('/dev/%s' % dev_match.group())
					self.debug('Extracting /dev/%s ' % cols[3])
		fd.close()

		uniqlist = []
		for dev in devices:
			if not dev in uniqlist:
				uniqlist.append(dev)
		devices = uniqlist
		devices.sort()
		self.debug('devices=%s' % devices)

		diskList={}
		diskProblemList={}       # device ==> set()
		diskProblemMessages={}   # device ==> str
		devices_remove={}

		_re_error_unknown_label = re.compile('^Error: .* unrecognised disk label')
		_re_warning_or_error = re.compile('^(?:Warning|Error): (.*)$')

		for dev in devices:
			dev=dev.strip()
			bn = os.path.basename(dev)
			# ignore CD-ROM devices
			try:
				fn = '/sys/block/%s/capability' % (bn,)
				f = open(fn, 'r')
				try:
					d = f.read()
				finally:
					f.close()
				d = d.rstrip()
				cap = int(d, 16) # hex
				if cap & 8: # include/linux/genhd.h: GENHD_FL_CD
					self.debug('Skipping CD-device %s' % (dev,))
					continue
			except IOError, e:
				self.debug('Error querying %s/capability: %s' % (bn, e))

			# ignore read-only devices
			try:
				fn = '/sys/block/%s/ro' % (bn,)
				f = open(fn, 'r')
				try:
					d = f.read()
				finally:
					f.close()
				d = d.rstrip()
				ro = bool(int(d))
				if ro: # include/linux/genhd.h: GENHD_FL_CD
					self.debug('Skipping read-only device %s' % (dev,))
					continue
			except IOError, e:
				self.debug('Error querying %s/ro: %s' % (bn, e))

			p = os.popen('/sbin/parted -m -s %s unit B print 2>&1'% dev)
			# parted output:
			# BYT;
			# /dev/vda:53687091200B:virtblk:512:512:gpt:Virtio Block Device;
			# 1:32256B:213857279B:213825024B:ext3:BOOT:;
			# 2:213857280B:2319528959B:2105671680B:linux-swap(v1):myswap:;
			# 3:2319528960B:53686402559B:51366873600B::DESCRIPTION:lvm;

			first_line=p.readline().strip()
			self.debug('first line: [%s]' % first_line)
			if _re_error_unknown_label.match(first_line):
				self.debug('Firstline starts with error')
				self.debug('Device %s contains unknown disk label' % dev)
				self.debug('Removing device %s' % dev)
				diskProblemList[dev] = diskProblemList.get(dev, set()) | set([DISKLABEL_UNKNOWN]) # add new problem to list
				devices_remove[dev] = 1
				continue
			elif _re_warning_or_error.match(first_line):
				self.debug('Firstline starts with warning or error')
				self.debug('Removing device: %s' % dev)
				diskProblemList[dev] = diskProblemList.get(dev, set()) | set([UNKNOWN_ERROR]) # add new problem to list
				diskProblemMessages[dev] = first_line
				devices_remove[dev] = 1
				continue
			elif not first_line == 'BYT;':
				self.debug('First line of parted output does not start with "BYT;"!')
				self.debug('Removing device: %s' % dev)
				devices_remove[dev] = 1
				continue

			disk_size = 0       # size of device in bytes
			partList = {}
			last_part_end = 0   # position of last byte of last partition
			_re_int=re.compile('^[0-9].*')
			for line in [ first_line ] + p.readlines():
				self.debug('DEBUG: parted: %s' % line)
				line=line.rstrip(';\n\r')

				# parse disk size
				if line.startswith('/'):
					data = line.split(':')
					disk_size = int(data[1].strip('B'))
					if disk_size > RESERVED_SPACE_AT_END_OF_DISK:
						max_part_end = disk_size - RESERVED_SPACE_AT_END_OF_DISK
					else:
						max_part_end = disk_size
					parttabletype = data[5]
					self.debug('DEBUG: disk size = %dB = %fMiB    max_part_end = %fMiB' % (disk_size, B2MiB(disk_size), B2MiB(max_part_end)))

					if parttabletype in 'msdos':
						self.debug('Device %s uses MSDOS partition table' % dev)
						self.debug('Removing device %s' % dev)
						diskProblemList[dev] = diskProblemList.get(dev, set()) | set([DISKLABEL_MSDOS]) # add new problem to list
						devices_remove[dev] = 1
						continue

					if parttabletype not in ['gpt', 'msdos']:
						self.debug('Device %s uses unknown partition table: %s' % (dev, parttabletype))
						self.debug('Removing device %s' % dev)
						diskProblemList[dev] = diskProblemList.get(dev, set()) | set([DISKLABEL_UNKNOWN]) # add new problem to list
						devices_remove[dev] = 1
						continue

				if not _re_int.match(line):
					if _re_warning_or_error.match(line):
						self.debug('Line starts with Error: [%s]' % line)
						self.debug('Removing device %s' % dev)
						devices_remove[dev] = 1
					continue

				if line and line[0].isdigit():
					cols = line.split(':')
					self.debug('cols = %r' % (cols,))
					num = int(cols[0])
					start = int(cols[1].strip('B'))				# partition start
					end = int(cols[2].strip('B'))				# partition end
					size = calc_part_size(start, end)			# get partition size
					fstype = self.detect_filesystem(self.get_device(dev, '', num))	# filesystem type
					label = cols[5]								# partition label
					flag = []
					if cols[6]:
						flag = re.split(',[ \t]+', cols[6])     # flags are separated by comma

					# check if disk uses a MBR and an existing partition blocks disk space required by GPT
					# GPT uses at least 34 sectors
					if (start < 34*512) or (end > disk_size-34*512) and DISKLABEL_MSDOS in diskProblemList.get(dev, set()):
						self.debug('ERROR: Partition size conflicts with GPT if MBR shall get converted!')
						self.debug('line=%r' % line)
						self.debug('Removing device %s' % dev)
						diskProblemList[dev].remove(DISKLABEL_MSDOS)     # remove old problem from list
						diskProblemList[dev].add(PARTITION_GPT_CONFLICT) # add new problem to list
						devices_remove[dev] = 1

					# fix fstypes
					if fstype == 'linux-swap':
						flag.append(PARTFLAG_SWAP)

					# add free space between partitions
					if (start - last_part_end) >= PARTSIZE_MINIMUM and start > EARLIEST_START_OF_FIRST_PARTITION:
						if last_part_end == 0:
							# free space in front of first partition and enough to use it
							free_start = align_partition_start(EARLIEST_START_OF_FIRST_PARTITION)
						else:
							# first free byte starts one after last used byte
							free_start = align_partition_start(last_part_end + 1)
						free_end = align_partition_end(start - 1)
						if free_end - free_start >= PARTSIZE_MINIMUM:
							self.debug('Adding free space: start=%d   last_part_end=%d   free_start=%d   free_end=%d' % (start, last_part_end, free_start, free_end))
							partList[free_start] = self.generate_freespace(free_start, free_end)

					partList[start] = {
						'type': PARTTYPE_USED,
						'touched': 0,
						'fstype': fstype,
						'size': size,
						'end': end,
						'num': num,
						'label': label,
						'mpoint': '',
						'flag': flag,
						'format': 0,
						'preexist': 1
						}

					self.debug('partList[%d] = %r' % (start, partList[start],))
					last_part_end = end

				if devices_remove.get(dev):
					continue

			# check if there is empty space behind last partition entry
			if ( max_part_end - last_part_end) >= PARTSIZE_MINIMUM:
				if last_part_end == 0:
					# whole disk is empty
					free_start = align_partition_start(EARLIEST_START_OF_FIRST_PARTITION)
				else:
					# free space after last partition
					free_start = align_partition_start(last_part_end + 1)
				free_end = align_partition_end(max_part_end - 1)
				partList[free_start] = self.generate_freespace(free_start, free_end)

			# add reserved free space to list of partitions if not used by other partitions
			reserved_start = max_part_end
			if last_part_end > max_part_end:
				reserved_start = last_part_end
			if (disk_size - reserved_start - RESERVED_FOR_GPT) >= PARTSIZE_MINIMUM:
				reserved_start = align_partition_start(reserved_start)
				reserved_end = (disk_size - 1 - RESERVED_FOR_GPT)
				partList[reserved_start] = self.generate_freespace(reserved_start, reserved_end, parttype=PARTTYPE_RESERVED)

			diskList[dev]={ 'partitions': partList,
							'size': disk_size,
							'min_part_start': EARLIEST_START_OF_FIRST_PARTITION,
							'max_part_end': max_part_end,
							}
			p.close()

		if devices_remove:
			self.debug('devices=%s' % devices)
			self.debug('diskList=%s' % diskList)
		for d in devices_remove:
			devices.remove(d)
			if d in diskList:
				del diskList[d]
		self.debug('devices=%s' % devices)
		self.debug('diskList=%s' % diskList)
		self.debug('diskProblemList=%s' % diskProblemList)
		return diskList, diskProblemList, diskProblemMessages


	def generate_freespace(self, start, end, touched=0, parttype=PARTTYPE_FREE):
		return {
			'type': parttype,
			'touched': touched,
			'fstype': '---',
			'size': calc_part_size(start, end),
			'end': end,
			'num': PARTNUMBER_FREE,
			'mpoint': '',
			'flag': [],
			'format': 0
			}

	def get_device(self, disk, part, num=None):
		device="/dev/%s" % disk.replace('/dev/', '').replace('//', '/')
		regex = re.compile(".*c[0-9]d[0-9]*")
		match = re.search(regex,disk)
		if match: # got /dev/cciss/cXdXpX
			device += "p"
		if num is None:
			device += "%s" % self.container['disk'][disk]['partitions'][part]['num']
		else:
			device += '%d' % num
		return device

	def result(self):
		if self.container['module_disabled']:
			self.debug('module has been disabled since profile requested following partition table type: %r' % self.all_results.get('partitiontable_type'))
			return {}

		result={
			'partitiontable_type': 'GPT',
			'use_efi': { True: 'yes', False: 'no' }[self.container.get('use_efi',False)]
			}
		tmpresult = []
		partitions = []
		for disk in self.container['disk']:
			partitions.append( disk )
			for part in self.container['disk'][disk]['partitions']:
				if self.container['disk'][disk]['partitions'][part]['num'] > 0 : # only valid partitions
					if self.container['disk'][disk]['partitions'][part]['fstype'][0:3] != 'LVM':
						mpoint=self.container['disk'][disk]['partitions'][part]['mpoint']
						if mpoint == '':
							mpoint = 'None'
						fstype=self.container['disk'][disk]['partitions'][part]['fstype']
						if fstype == '':
							fstype = 'None'
						device = self.get_device(disk, part)

						if mpoint == '/boot':
							result[ 'boot_partition' ] = device
						if mpoint == '/':
							if not result.has_key( 'boot_partition' ):
								result[ 'boot_partition' ] = device

						format=self.container['disk'][disk]['partitions'][part]['format']
						start=part
						end=part+self.container['disk'][disk]['partitions'][part]['size']
						flag=','.join(self.container['disk'][disk]['partitions'][part]['flag'])
						if not flag:
							flag = 'None'
						parttype='only_mount'
						if self.container['disk'][disk]['partitions'][part]['touched']:
							parttype = '0' # GPT contains only "primary" partitions / kept this value to make format similar to old MBR profiles
						tmpresult.append( ("PHY", device, parttype, format, fstype, start, end, mpoint, flag) )
		result[ 'disks' ] = ' '.join(partitions)

		# append LVM if enabled
		if self.container['lvm']['enabled'] and self.container['lvm']['vg'].has_key( self.container['lvm']['ucsvgname'] ):
			vg = self.container['lvm']['vg'][ self.container['lvm']['ucsvgname'] ]
			for lvname in vg['lv'].keys():
				lv = vg['lv'][lvname]
				mpoint = lv['mpoint']
				if not mpoint:
					mpoint = 'None'
				fstype = lv['fstype']
				if not fstype:
					fstype = 'None'

				if mpoint == '/boot':
					result[ 'boot_partition' ] = lv['dev']
				if mpoint == '/':
					if not result.has_key( 'boot_partition' ):
						result[ 'boot_partition' ] = lv['dev']

				format = lv['format']
				start = 0
				end = lv['size']
				parttype='only_mount'
				if lv['touched']:
					parttype = 'LVMLV'
				flag='None'
				tmpresult.append( ("LVM", lv['dev'], parttype, format, fstype, start, end, mpoint, flag) )
		# sort partitions by mountpoint
		i = 0
		tmpresult.sort(lambda x,y: cmp(x[7], y[7]))  # sort by mountpoint
		for (devtype, device, parttype, format, fstype, start, end, mpoint, flag) in tmpresult:
			result[ 'dev_%d' % i ] =  "%s %s %s %s %s %sMiB %sMiB %s %s" % (devtype, device, parttype, format, fstype, int(B2MiB(start)), int(B2MiB(end)), mpoint, flag)
			i += 1
		return result

	def install_fresh_gpt(self, device=None):
		self.debug('Trying to install fresh partition table on device %s' % device)
		if not os.path.exists(device):
			self.debug('ERROR: device %s does not exist!' % device)
		else:
			self.disable_all_vg()
			self.run_cmd(['/sbin/parted', '-s', device, 'mklabel', 'gpt'])
			self.fix_boot_flag_in_protective_mbr(device)
			self.enable_all_vg()

	def convert_to_gpt(self, device=None):
		self.debug('Trying to convert MBR to GPT on device %s' % device)
		if not os.path.exists(device):
			self.debug('ERROR: device %s does not exist!' % device)
		else:
			self.run_cmd(['/sbin/sgdisk', '-g', device])
			self.fix_boot_flag_in_protective_mbr(device)

	def print_history(self):
		self.debug("HISTORY")
		for entry in self.container['history']:
			self.debug('==> %s' % entry)

	class partition(subwin):
		def __init__(self,parent,pos_y,pos_x,width,height):
			self.part_objects = {}
			subwin.__init__(self,parent,pos_y,pos_x,width,height,show_border=False,show_shadow=False)
			self.check_partition_table_msg()
			self.no_devices_msg()
			self.check_lvm_msg()
			self.ERROR = False

		def auto_partitioning_get_freespacelist(self, disklist):
			""" determines sizes of free space regions on given disks.
				return values:
					freespacelist → [ (<size:int>, <disk:string>, <part:string>), ... ]
					freespacemax  → size of largest region
					freespacesum  → sum of all free space regions
			"""
			freespacelist = []
			freespacemax = 0.0
			freespacesum = 0.0
			for disk in disklist:
				for part in self.container['disk'][disk]['partitions'].keys():
					if self.container['disk'][disk]['partitions'][part]['type'] in [ PARTTYPE_FREE ]:
						freespacelist.append( ( int(self.container['disk'][disk]['partitions'][part]['size']), disk, part ) )
						freespacesum += int(self.container['disk'][disk]['partitions'][part]['size'])
						if int(self.container['disk'][disk]['partitions'][part]['size']) > freespacemax:
							freespacemax = int(self.container['disk'][disk]['partitions'][part]['size'])
			freespacelist.sort(lambda x,y: int(x[0]) < int(y[0]))
			self.parent.debug('AUTOPART: freespacelist=%s' % freespacelist)
			self.parent.debug('AUTOPART: freespacesum=%s' % freespacesum)
			self.parent.debug('AUTOPART: freespacemax=%s' % freespacemax)
			return (freespacelist, freespacemax, freespacesum)

		def auto_partitioning_question_prunelvm_callback(self, result):
			self.container['autopart'] = True
			self.container['autopart_prunelvm'] = True
			self.parent.debug('Purge LVM devices during autopart')
			self.auto_partitioning(result)

		def auto_partitioning(self, result):
			# create disk list with usb storage devices
			disk_blacklist = self.parent.get_usb_storage_device_list()

			if self.container['lvm']['vg'] and self.container.get('autopart_prunelvm') is None:
				self.parent.debug('requesting user input: prune all disks for auto partitioning due to found LVM devices?')
				msglist=[ _('At least one LVM volume group has been found. To use the'),
						  _('auto partitioning, all attached disks have to be erased!'),
						  '',
						  _('Continue with auto partitioning?'),
						  '',
						  _('WARNING: Choosing "yes" prepares for deletion of all'),
						  _('partitions on all disks! If auto-partition result is'),
						  _('unsuitable, press F5 afterwards to restart partitioning.')
						  ]
				self.container['autopart_prunelvm'] = False
				self.container['autopartition'] = False
				self.sub = yes_no_win(self, self.pos_y+8, self.pos_x+2, self.width-4, self.height-20, msglist, default='no',
									  callback_yes=self.auto_partitioning_question_prunelvm_callback)
				self.draw()
				return

			self.container['autopartition'] = True
			self.parent.debug('INTERACTIVE AUTO PARTITIONING')

			# remove all LVM LVs
			for vgname,vg in self.container['lvm']['vg'].items():
				for lvname, lv in vg['lv'].items():
					self.parent.debug('deleting LVM LV: %s' % lvname)
					self.part_delete_generic( 'lvm_lv', vgname, lvname )

			# reduce all LVM VGs
			for vgname,vg in self.container['lvm']['vg'].items():
				self.parent.debug('reducing LVM VG: %s' % vgname)
				if self.container['lvm']['vg'][ vgname ]['created']:
					self.container['history'].append(['/sbin/vgreduce', '-a', '--removemissing', vgname])
					self.container['history'].append(['/sbin/vgremove', vgname])
					self.container['lvm']['vg'][ vgname ]['created'] = 0

			# remove all partitions on all disks
			for diskname, disk in self.container['disk'].items():
				# do not use blacklisted devices
				if diskname in disk_blacklist:
					self.parent.debug('disk %s is blacklisted (used)' % (diskname,))
				else:
					for partname, part in disk['partitions'].items():
						if part['type'] == PARTTYPE_USED:
							self.parent.debug('deleting part: %s on %s (%s)' % (partname, diskname, self.parent.get_device(diskname, partname)))
							self.part_delete_generic( 'part', diskname, partname, force=True )

			# remove internal data about LVM VGs and LVM PGs
			for vgname,vg in self.container['lvm']['vg'].items():
				self.parent.debug('removing LVM VG: %s' % vgname)
				del self.container['lvm']['vg'][vgname]
			self.container['lvm']['pv'] = {}

			self.parent.print_history()

			# reactivate LVM
			self.parent.set_lvm(True)

			# get disk list
			disklist = self.container['disk'].keys()
			disklist.sort()
			self.parent.debug('original disklist = %s' % disklist)
			self.parent.debug('disk_blacklist = %s' % disk_blacklist)
			# remove blacklisted devices from disklist
			for disk in disk_blacklist:
				if disk in disklist:
					disklist.remove(disk)
			# WARNING: auto partitioning uses only first disk since UCS 3.2
			disklist = disklist[0:1]
			self.parent.debug('final disklist = %s' % disklist)

			# get system memory
			p = os.popen('free')
			data = p.read()
			p.close()
			regex = re.compile('^\s+Mem:\s+(\d+)\s+.*$')
			sysmem = -1
			for line in data.splitlines():
				match = regex.match(line)
				if match:
					sysmem = int(match.group(1)) * 1024 # value read from "free" is given in KiB and has to be converted to bytes
			self.parent.debug('AUTOPART: sysmem=%s' % sysmem)


			# create EFI system partition if EFI has been detected
			if self.container['use_efi']:
				GRUBPART = { 'size': PARTSIZE_EFI,
							 'flags': [PARTFLAG_EFI],
							 'format': 1,
							 'mpoint': MOUNTPOINT_EFI,
							 'fstype': FSTYPE_EFI,
							 'msg': _('Not enough disk space found for EFI system partition!'),
							 }
			else:
				# create BIOS boot partition for GRUB otherwise
				GRUBPART = { 'size': PARTSIZE_BIOS_GRUB,
							 'flags': [PARTFLAG_BIOS_GRUB],
							 'format': 0,
							 'mpoint': '',
							 'fstype': '',
							 'msg': _('Not enough disk space found for BIOS boot partition!'),
							 }

			# create partition on first harddisk for BIOS_BOOT
			targetdisk = None
			targetpart = None
			for disk in disklist:
				for part in self.container['disk'][disk]['partitions'].keys():
					if self.container['disk'][disk]['partitions'][part]['type'] in [ PARTTYPE_FREE ]:
						if int(self.container['disk'][disk]['partitions'][part]['size']) > GRUBPART['size']:
							targetdisk = disk
							targetpart = part
							break
				if targetdisk:
					break

			if targetdisk:
				# part_create_generic(self,arg_disk,arg_part,mpoint,size,fstype,type,flag,format,label):
				self.part_create_generic(targetdisk, targetpart, GRUBPART['mpoint'], GRUBPART['size'], GRUBPART['fstype'], PARTTYPE_USED, GRUBPART['flags'], GRUBPART['format'], '')
			else:
				msglist = [ GRUBPART['msg'],
							_('Auto partitioning aborted.') ]
				self.sub = msg_win(self,self.pos_y+8,self.pos_x+5,self.maxWidth,6, msglist)
				self.draw()
				return

			# get free space on target disk (first disk)
			freespacelist, freespacemax, freespacesum = self.auto_partitioning_get_freespacelist([targetdisk])

			# create partition on first harddisk for /boot
			if freespacemax >= PARTSIZE_BOOT:
				# part_create_generic(self,arg_disk,arg_part,mpoint,size,fstype,type,flag,format,label):
				self.part_create_generic(freespacelist[0][1], freespacelist[0][2], '/boot', PARTSIZE_BOOT, 'ext4', PARTTYPE_USED, [PARTFLAG_NONE], 1, '/boot')
			else:
				msglist = [ _('Not enough disk space found for /boot!'),
							_('Auto partitioning aborted.') ]
				self.sub = msg_win(self,self.pos_y+8,self.pos_x+5,self.maxWidth,6, msglist)
				self.draw()
				return

			# get free space on all disks
			freespacelist, freespacemax, freespacesum = self.auto_partitioning_get_freespacelist(disklist)

			# create primary partition on first harddisk for /swap
			swapsize = 2 * sysmem  # default for swap partition
			if swapsize > PARTSIZE_SWAP_MAX:    # limit swap partition to 2GB
				swapsize = PARTSIZE_SWAP_MAX
			if swapsize < PARTSIZE_SWAP_MIN:
				swapsize = PARTSIZE_SWAP_MIN
			if (freespacesum - PARTSIZE_SWAP_MIN < PARTSIZE_SYSTEM_MIN) or (freespacemax < PARTSIZE_SWAP_MIN):
				self.parent.debug('AUTOPART: not enough disk space for swap (freespacesum=%s  freespacemax=%s  PARTSIZE_SWAP_MIN=%s  PARTSIZE_SYSTEM_MIN=%s' %
								  (freespacesum, freespacemax, PARTSIZE_SWAP_MIN, PARTSIZE_SYSTEM_MIN))
				msglist = [ _('Not enough disk space found!'),
							_('Auto partitioning aborted.') ]
				self.sub = msg_win(self,self.pos_y+2,self.pos_x+5,self.maxWidth,6, msglist)
				self.draw()
				return
			while freespacesum - swapsize < PARTSIZE_SYSTEM_MIN:
				swapsize -= MiB2B(8)
				if swapsize < PARTSIZE_SWAP_MIN:
					swapsize = PARTSIZE_SWAP_MIN

			targetdisk = None
			targetpart = None
			for disk in disklist:
				for part in self.container['disk'][disk]['partitions'].keys():
					if self.container['disk'][disk]['partitions'][part]['type'] in [ PARTTYPE_FREE ]:
						if int(self.container['disk'][disk]['partitions'][part]['size']) > swapsize:
							targetdisk = disk
							targetpart = part
							break
				if targetdisk:
					break
			if targetdisk:
				# part_create_generic(self,arg_disk,arg_part,mpoint,size,fstype,type,flag,format,label):
				self.parent.debug('AUTOPART: create swap: disk=%s  part=%s  swapsize=%s' % (targetdisk, targetpart, swapsize))
				self.part_create_generic(targetdisk, targetpart, '', swapsize, FSTYPE_SWAP, PARTTYPE_USED, [PARTFLAG_SWAP], 1, 'SWAP')
			else:
				self.parent.debug('AUTOPART: no disk space for swap found')
				self.parent.debug('AUTOPART: DISK=%s' % self.container['disk'])
				msglist = [ _('Not enough disk space found for /boot!'),
							_('Auto partitioning aborted.') ]
				self.sub = msg_win(self,self.pos_y+8,self.pos_x+5,self.maxWidth,6, msglist)
				self.draw()
				return

			# create one LVM PV per free space range
			for disk in disklist:
				for part in self.container['disk'][disk]['partitions'].keys():
					if self.container['disk'][disk]['partitions'][part]['type'] in [ PARTTYPE_FREE ]:
						# part_create_generic(self,arg_disk,arg_part,mpoint,size,fstype,type,flag,format,end=0):
						size = self.container['disk'][disk]['partitions'][part]['size']
						parttype = PARTTYPE_USED
						self.part_create_generic(disk, part, '', size, '', parttype, ['lvm'], 'LVMPV')

			# create one LVM LV for /-filesystem
			vgname = self.parent.container['lvm']['ucsvgname']
			vg = self.parent.container['lvm']['vg'][ vgname ]
			lvname = 'rootfs'
			format = 1
			fstype = 'ext4'
			mpoint = '/'
			flag = []
			currentLE = vg['freePE']
			self.lv_create(vgname, lvname, currentLE, format, fstype, flag, mpoint)

			self.parent.debug('AUTOPART FINISHED - INTERNAL STATUS:')
			for pvname, pv in self.container['lvm']['pv'].items():
				self.parent.debug('PV[%s]=%s' % (pvname, pretty_format(pv)))
			for vgname, vg in self.container['lvm']['vg'].items():
				self.parent.debug('VG[%s]=%s' % (vgname, pretty_format(vg)))

		def ask_lvm_enable_callback(self, result):
			self.parent.set_lvm( (result == 'BT_YES') )

		def no_devices_msg(self):
			if not self.container["disk"] and not self.container['disk_checked']:
				if not hasattr(self,'sub'):
					self.container['disk_checked'] = True
					self.parent.set_lvm( False )
					msglist = [		_('WARNING: No devices or valid partitions found!'),
							_('Please check your harddrive or partitioning.'),
							_('Further information can be found in the'),
							_('Support & Knowledge Base: http://sdb.univention.de.')
							]
					self.sub = msg_win(self,self.pos_y+11,self.pos_x+5,self.maxWidth,6, msglist)
					self.draw()

		def install_fresh_gpt_interactive(self, result, device=None):
			self.parent.install_fresh_gpt(device)
			self.container['problemdisk'][device].discard(UNKNOWN_ERROR)
			self.container['problemdisk'][device].discard(DISKLABEL_UNKNOWN)
			self.container['problemdisk'][device].discard(DISKLABEL_MSDOS)
			self.parent.debug('performing restart of module')
			self.parent.start()
			#self.parent.layout()
			self.parent.debug('module restart done')
			self.container['lvm']['lvmconfigread'] = False
			self.container['autopartition'] = None

		def convert_to_gpt_interactive(self, result, device=None):
			self.parent.convert_to_gpt(device)
			self.container['problemdisk'][device].discard(DISKLABEL_UNKNOWN)
			self.container['problemdisk'][device].discard(DISKLABEL_MSDOS)
			self.parent.debug('performing restart of module')
			self.parent.start()
			#self.parent.layout()
			self.parent.debug('module restart done')
			self.container['lvm']['lvmconfigread'] = False
			self.container['autopartition'] = None

		def check_partition_table_msg(self):
			if self.container['partitiontable_checked']:
				# already checked and approved by user
				return

			if hasattr(self, 'sub') and self.sub:
				# there's another subwindow active ==> stop here
				return

			self.parent.debug('check_partition_table_msg()')
			for dev in self.container['problemdisk']:
				self.parent.debug('Checking problems for device %s ==> %s' % (dev, self.container['problemdisk'][dev]))

				if UNKNOWN_ERROR in self.container['problemdisk'][dev]:  # search for specific problem in set() of errors
					self.parent.debug('requesting user input: unknown error ==> write new GPT?')
					msglist=[ _('An error occurred while reading device %s:') % dev,
							  '',
							  '',
							  _('Install now an empty GPT to device %s ?') % dev,
							  '',
							  _('WARNING: By choosing "Write GPT" existing data'),
							  _('on device %s will be lost.') % dev,
							  ]
					# insert message from parted
					msglist[2:2] = textwrap.wrap(self.container['problemmessages'][dev], 68, drop_whitespace=True)
					self.sub = yes_no_win(self, self.pos_y+9, self.pos_x+2, self.width-4, self.height-25, msglist, default='no',
										  btn_name_yes=_('Write GPT'), btn_name_no=_('Ignore Device'),
										  callback_yes=self.install_fresh_gpt_interactive, device=dev)
					self.draw()
					self.container['problemdisk'][dev].discard(UNKNOWN_ERROR)
					break

				if DISKLABEL_UNKNOWN in self.container['problemdisk'][dev]:  # search for specific problem in set() of errors
					self.parent.debug('requesting user input: unknown disklabel ==> write new GPT?')
					msglist=[ _('No valid partition table found on device %s.') % dev,
							  _('Install now an empty GPT to device %s ?') % dev,
							  '',
							  _('WARNING: By choosing "Write GPT" existing data'),
							  _('on device %s will be lost.') % dev,
							  ]
					self.sub = yes_no_win(self, self.pos_y+9, self.pos_x+2, self.width-4, self.height-25, msglist, default='no',
										  btn_name_yes=_('Write GPT'), btn_name_no=_('Ignore Device'),
										  callback_yes=self.install_fresh_gpt_interactive, device=dev)
					self.draw()
					self.container['problemdisk'][dev].discard(DISKLABEL_UNKNOWN)
					break

				if PARTITION_GPT_CONFLICT in self.container['problemdisk'][dev]:  # search for specific problem in set() of errors
					self.parent.debug('show warning to user: disk uses MBR and at least one partition is too large and is conflicting with GPT sectors ==> automatic conversion impossible')
					msglist = [ _('A MBR has been found on device %s.') % dev,
								_('Devices with MBR are not supported by the interactive installation.'),
								_('An automatic conversion of the existing MBR to a GPT is not possible.'),
								_('At least one partition occupies sectors that shall be used by GPT.'),
								_('Until this conflict is resolved manually, this device will be ignored.'),
								'',
								_('HINT: Further information for an installation'),
								_('on a device with problematic MBR can be found in the'),
								_('Support & Knowledge Base: http://sdb.univention.de.'),
								]
					self.sub = msg_win(self, self.pos_y+4, self.pos_x, self.width-1, len(msglist)+6, msglist)
					self.draw()
					self.container['problemdisk'][dev].discard(PARTITION_GPT_CONFLICT)
					break

				if DISKLABEL_MSDOS in self.container['problemdisk'][dev]:  # search for specific problem in set() of errors
					self.parent.debug('requesting user input: MSDOS parttable found ==> ignore or convert to GPT?')
					msglist=[ _('A MBR has been found on device %s.') % dev,
							  _('Devices with MBR are unsupported in interactive installation.'),
							  _('You can proceed by ignoring this device or by converting'),
							  _('the existing MBR to GPT immediately.'),
							  '',
							  _('WARNING: By choosing "Convert to GPT" existing partition'),
							  _('order may change and affect other operationg systems!'),
							  '',
							  _('HINT: Further information for an installation'),
							  _('on a device with MBR can be found in the'),
							  _('Support & Knowledge Base: http://sdb.univention.de.'),
							  '',
							  '',
							  _('Convert MBR of device %s to GPT now?') % dev,
							  ]
					self.sub = yes_no_win(self, self.pos_y+4, self.pos_x+2, self.width-4, self.height-25, msglist, default='no',
										  btn_name_yes=_('Convert to GPT'), btn_name_no=_('Ignore Device'),
										  callback_yes=self.convert_to_gpt_interactive, device=dev)
					self.draw()
					self.container['problemdisk'][dev].discard(DISKLABEL_MSDOS)
					break
			else:
				# only set check==True if all checks have been made
				self.container['partitiontable_checked'] = True

		def check_lvm_msg(self):
			# check if LVM config has to be read
			if not self.container['lvm']['lvmconfigread']:
				self.draw()
				self.act = self.active(self,_('Detecting LVM devices'),_('Please wait ...'),name='act',action='read_lvm')
				self.act.draw()
				self.draw()

			# check for free space for auto partitioning
			if self.container['lvm']['lvmconfigread'] and self.container['autopartition'] == None and not hasattr(self,'sub'):
				result = self.parent.check_space_for_autopart()
				if result:
					self.container['autopartition'] = False
					msglist = [ _('WARNING: not enough free space for auto partitioning!'),
								_('Auto partitioning has been disabled!')
								]
					self.sub = msg_win(self,self.pos_y+11,self.pos_x+5,self.maxWidth,6, msglist)
					self.draw()

			# ask for auto partitioning
			if self.container['lvm']['lvmconfigread'] and self.container['autopartition'] == None and not hasattr(self,'sub'):
				self.parent.debug('requesting user input: use autopart?')
				msglist=[ _('Do you want to use auto-partitioning?'),
						  '',
						  _('WARNING: Choosing "yes" prepares for deletion of all'),
						  _('partitions on all disks! If auto-partition result is'),
						  _('unsuitable, press F5 afterwards to restart partitioning.')
						  ]
				self.container['autopartition'] = False
				self.sub = yes_no_win(self, self.pos_y+9, self.pos_x+2, self.width-4, self.height-25, msglist, default='yes', callback_yes=self.auto_partitioning)
				self.draw()

			# show warning if LVM1 volumes are detected
			if self.container['lvm']['lvm1available'] and not self.container['lvm']['warnedlvm1'] and not hasattr(self,'sub'):
				self.container['lvm']['warnedlvm1'] = True
				msglist = [ _('LVM1 volumes detected. To use LVM1 volumes all'),
							_('existing LVM1 snapshots have to be removed!'),
							_('Otherwise kernel is unable to mount them!') ]
				self.sub = msg_win(self,self.pos_y+11,self.pos_x+5,self.maxWidth,6, msglist)
				self.draw()

			# if more than one volume group is present, ask which one to use
			if not self.container['lvm']['ucsvgname'] and len(self.container['lvm']['vg'].keys()) > 1 and not hasattr(self,'sub'):
				self.parent.debug('requesting user input: more that one LVMVG found')
				self.sub = self.ask_lvm_vg(self,self.minY+5,self.minX+5,self.maxWidth,self.maxHeight-3)
				self.draw()

			# if only one volume group os present, use it
			if not self.container['lvm']['ucsvgname'] and len(self.container['lvm']['vg'].keys()) == 1:
				self.parent.debug('Enabling LVM - only one VG found - %s' % self.container['lvm']['vg'].keys() )
				self.container['lvm']['ucsvgname'] = self.container['lvm']['vg'].keys()[0]
				self.layout()
				self.draw()

			# if LVM is not automagically enabled then ask user if it should be enabled
			if self.container['lvm']['enabled'] == None and not hasattr(self,'sub'):
				msglist=[ _('No LVM volume group found on current system.'),
						  _('Do you want to use LVM2?') ]
				self.sub = yes_no_win(self, self.pos_y+11, self.pos_x+4, self.width-8, self.height-25, msglist, default='yes',
									  callback_yes=self.ask_lvm_enable_callback, callback_no=self.ask_lvm_enable_callback)
				self.draw()

		def draw(self):
			if self.show_shadow:
				self.shadow.refresh(0,0,self.pos_y+1,self.pos_x+1,self.pos_y+self.height+1,self.pos_x+self.width+1)
			self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+self.height,self.pos_x+self.width)
			self.header.draw()
			for element in self.elements:
				element.draw()
			if self.startIt:
				self.startIt=0
				self.start()
			if hasattr(self,"sub"):
				self.sub.draw()

		def modheader(self):
			return ''
			return _(' Partitioning dialog ')

		def profileheader(self):
			return ' Partitioning dialog '

		def layout(self):
			self.reset_layout()
			self.container=self.parent.container
			self.minY=self.parent.minY-11
			self.minX=self.parent.minX+4
			self.maxWidth=self.parent.maxWidth
			self.maxHeight=self.parent.maxHeight

			col1=10
			col2=13
			col3=8
			col4=6
			col5=13
			col6=10

			head1=self.get_col(_('Device'),col1,'l')
			head2=self.get_col(_('Region(MiB)'),col2)
			head3=self.get_col(_('Type'),col3)
			head4=self.get_col(_('Form.'),col4)
			head5=self.get_col(_('Mount point'),col5,'l')
			head6=self.get_col(_('Size(MiB)'),col6)
			text = '%s %s %s %s %s %s'%(head1,head2,head3,head4,head5,head6)
			self.add_elem('TXT_0', textline(text,self.minY+11,self.minX+2)) #0

			device=self.container['disk'].keys()
			device.sort()

			self.parent.debug('LAYOUT')
			self.parent.printPartitions()

			dict=[]
			for dev in device:
				disk = self.container['disk'][dev]
				self.rebuild_table(disk,dev)
				txt = '%s  (%s) %s' % (dev.split('/',2)[-1], _('diskdrive'), '-'*(col1+col2+col3+col4+col5+10))
				path = self.get_col(txt,col1+col2+col3+col4+col5+4,'l')

				size = self.get_col('%d' % int(B2MiB(disk['max_part_end'])),col6)
				# save for later use (evaluating inputs)
				self.part_objects[ len(dict) ] = [ 'disk', dev ]
				dict.append('%s %s' % (path,size))

				part_list=self.container['disk'][dev]['partitions'].keys()
				part_list.sort()
				for i in range(len(part_list)):
					part = self.container['disk'][dev]['partitions'][part_list[i]]
					path = self.get_col(' %s' % self.dev_to_part(part, dev),col1,'l')

					if part['type'] == PARTTYPE_RESERVED:
						continue

					format=self.get_col('',col4,'m')
					if part['format']:
						format=self.get_col('X',col4,'m')
					if PARTFLAG_LVM in part['flag']:
						type = self.get_col('LVMPV',col3)

						device = self.parent.get_device(dev, part_list[i])
						# display corresponding vg of pv if available
						if self.container['lvm'].has_key('pv') and self.container['lvm']['pv'].has_key( device ):
							if self.container['lvm']['pv'][device]['vg']:
								mount = self.get_col( self.container['lvm']['pv'][device]['vg'], col5, 'l')
							else:
								mount = self.get_col( _('(unassigned)'), col5, 'l')
						else:
							mount = self.get_col('', col5, 'l')
					else:
						type = self.get_col(part['fstype'], col3)
						if part['fstype']== FSTYPE_SWAP:
							type = self.get_col('swap', col3)
						if PARTFLAG_BIOS_GRUB in part['flag']:
							type = self.get_col('BIOS', col3)
						if PARTFLAG_EFI in part['flag']:
							type = self.get_col('EFI', col3)
						mount = self.get_col(part['mpoint'], col5, 'l')

					size = self.get_col('%d' % B2MiB(part['size']), col6)

					if part['type'] == PARTTYPE_USED: # DATA
						path = self.get_col(' %s' % self.dev_to_part(part, dev), col1,'l')
						start = int(B2MiB(part_list[i]))
						end = int(B2MiB(part['end']))
						region = self.get_col('%d-%d' % (start, end), col2)
					elif part['type'] == PARTTYPE_FREE: # FREE SPACE
						region = self.get_col('', col2)
						mount = self.get_col('', col5, 'l')
						path = self.get_col(' ---', col1, 'l')
						type = self.get_col(_('free'), col3)
					else:
						region=self.get_col('', col2)
						type=self.get_col(_('unknown'), col3)
						path=self.get_col('---', col1)

					self.part_objects[ len(dict) ] = [ 'part', dev, part_list[i], i ]
					dict.append('%s %s %s %s %s %s' % (path, region, type, format, mount, size))
					self.parent.debug('==> DEV = %s   PART(%s) = %s' % (dev, part_list[i], pretty_format(part)))

			# display LVM items if enabled
			if self.container['lvm']['enabled'] and self.container['lvm'].has_key('vg'):
				for vgname in self.container['lvm']['vg'].keys():
					# remove following line to display all VGs!
					# but check other code parts for compliance first
					if vgname == self.container['lvm']['ucsvgname']:
						vg = self.container['lvm']['vg'][ vgname ]
						self.parent.debug('==> VG = %s' % vg)
						lvlist = vg['lv'].keys() # equal to   self.container['lvm']['vg'][ vgname ]['lv'].keys()
						lvlist.sort()

						txt = '%s  (%s) %s' % (vgname, _('LVM volume group'), '-'*(col1+col2+col3+col4+col5+10))
						path = self.get_col(txt,col1+col2+col3+col4+col5+4,'l')
						size = self.get_col('%d' % B2MiB(vg['PEsize'] * vg['totalPE']), col6)

						self.part_objects[ len(dict) ] = [ 'lvm_vg', vgname, None ]
						dict.append('%s %s' % (path,size))

						for lvname in lvlist:
							lv = vg['lv'][ lvname ]
							self.parent.debug('==> LV = %s' % lv)
							path = self.get_col(' %s' % lvname,col1,'l')
							format = self.get_col('',col4,'m')
							if lv['format']:
								format = self.get_col('X',col4,'m')
							size = self.get_col('%d' % B2MiB(lv['size']),col6)
							type = self.get_col(lv['fstype'],col3)
							if lv['fstype'] == FSTYPE_SWAP:
								type = self.get_col('swap',col3)
							mount = self.get_col(lv['mpoint'],col5,'l')
							region = self.get_col('',col2)

							self.part_objects[ len(dict) ] = [ 'lvm_lv', vgname, lvname ]
							dict.append('%s %s %s %s %s %s' % (path, region, type, format, mount, size))

						# show free space in volume group  ( don't show less than 3 physical extents )
						if vg['freePE'] > 2:
							path = self.get_col(' ---',col1,'l')
							format = self.get_col('',col4,'m')
							vgfree = vg['PEsize'] * vg['freePE']
							size = self.get_col('%d' % B2MiB(vgfree), col6)
							type = self.get_col('free', col3)
							mount = self.get_col('', col5, 'l')
							region = self.get_col('', col2)
							self.parent.debug('==> FREE %f MiB' % B2MiB(vgfree))

							self.part_objects[ len(dict) ] = [ 'lvm_vg_free', vgname, None ]
							dict.append('%s %s %s %s %s %s' % (path, region, type, format, mount, size))

			self.container['dict']=dict

			msg = _('This module is used for partitioning the existing hard drives. It is recommended to use at least three partitions - one BIOS boot or EFI partition, one for the root file system, and one for the swap area.\n\nPlease note:\nIf automatic partitioning has been selected, all the data stored on these hard drives will be lost during this process! Should the proposed partitioning be undesirable, it can be rejected by pressing the F5 function key.')

			self.add_elem('TA_desc', textarea(msg, self.minY, self.minX, 10, self.maxWidth+11))
			self.add_elem('SEL_part', select(dict,self.minY+12,self.minX,self.maxWidth+11,14,self.container['selected'])) #1
			self.add_elem('BT_create', button(_('F2-Create'),self.minY+28,self.minX,18)) #2
			self.add_elem('BT_edit', button(_('F3-Edit'),self.minY+28,self.minX+(self.width/2)-4,align="middle")) #3
			self.add_elem('BT_delete', button(_('F4-Delete'),self.minY+28,self.minX+(self.width)-7,align="right")) #4
			self.add_elem('BT_reset', button(_('F5-Reset changes'),self.minY+29,self.minX,30)) #5
			self.add_elem('BT_write', button(_('F6-Write partitions'),self.minY+29,self.minX+(self.width)-37,30)) #6
			self.add_elem('BT_back', button(_('F11-Back'),self.minY+30,self.minX,30)) #7
			self.add_elem('BT_next', button(_('F12-Next'),self.minY+30,self.minX+(self.width)-37,30)) #8

		def get_col(self, word, width, align='r'):
			# convert utf-8 input to unicode → len works also with umlauts
			word = word.decode('utf-8')
			wspace = u' '*width
			if align is 'l':
				result = word[:width] + wspace[len(word):]
			elif align is 'm':
				space = (width-len(word))/2
				result = u"%s%s%s" % (wspace[:space], word[:width], wspace[space+len(word):width])
			else:
				result = wspace[len(word):] + word[:width]
			# encode aligned unicode string back to utf-8
			return result.encode('utf-8')

		def dev_to_part(self, part, dev, type="part"):
			#/dev/hdX /dev/sdX /dev/mdX /dev/xdX /dev/adX /dev/edX /dev/pdX /dev/pfX /dev/vdX /dev/dasdX /dev/dptiX /dev/arX
			for ex in [".*hd[a-z]([0-9]*)$",".*sd[a-z]([0-9]*)$",".*md([0-9]*)$",".*xd[a-z]([0-9]*)$",".*ad[a-z]([0-9]*)$", ".*ed[a-z]([0-9]*)$",".*pd[a-z]([0-9]*)$",".*pf[a-z]([0-9]*)$",".*vd[a-z]([0-9]*)$",".*dasd[a-z]([0-9]*)$",".*dpti[a-z]([0-9]*)",".*ar[0-9]*"]:
				regex = re.compile(ex)
				match = re.search(regex,dev)
				if match:
					if type == "part":
						return "%s%s" %(dev.split('/')[-1], part['num'])
					elif type == "full":
						return "%s%s" %(dev, part['num'])
			#/dev/cciss/cXdX
			regex = re.compile(".*c[0-9]d[0-9]*")
			match = re.search(regex,dev)
			if match:
				if type == "part":
					return "%sp%s" % (dev.split('/')[-1],part['num'])
				elif type == "full":
					return "%sp%s" % (dev,part['num'])

		def helptext(self):
			return _('UCS-Partition-Tool \n \n This tool is designed for creating, editing and deleting partitions during the installation. \n \n Use \"F2-Create\" to add a new partition. \n \n Use \"F3-Edit\" to configure an already existing partition. \n \n Use \"F4-Delete\" to remove a partition. \n \n Use the \"Reset changes\" button to discard changes to the partition table. \n \n Use the \"Write Partitions\" button to create and/or format your partitions.')

		def input(self,key):
			self.parent.debug('partition.input: key=%d' % key)
			self.check_partition_table_msg()
			self.no_devices_msg()
			self.check_lvm_msg()
			if hasattr(self,"sub"):
				rtest=self.sub.input(key)
				if not rtest:
					if not self.sub.incomplete():
						self.subresult=self.sub.get_result()
						self.sub.exit()
						self.parent.layout()
				elif rtest=='next':
					self.subresult=self.sub.get_result()
					self.sub.exit()
					return 'next'
				elif rtest == 'tab':
					self.sub.tab()

			elif key == 269 or self.get_elem('BT_reset').get_status(): # F5 - reset changes
				self.parent.start()
				self.parent.layout()
				self.get_elem_by_id(self.current).set_on()
				self.get_elem('SEL_part').set_off()
				if hasattr(self,"sub"):
					self.sub.draw()
				return 1

			elif self.get_elem('BT_back').get_status():#back
				return 'prev'

			elif self.get_elem('BT_next').get_status() or key == 276: # F12 - next
				if len(self.container['history']) or self.parent.test_changes():
					self.sub=self.verify_exit(self,self.minY+(self.maxHeight/3),self.minX+(self.maxWidth/8),self.maxWidth,self.maxHeight-18)
					self.sub.draw()
				else:
					return 'next'

			elif key == 260:
				#move left
				active=0
				for elemid in ['BT_edit', 'BT_delete', 'BT_reset', 'BT_write', 'BT_back', 'BT_next']:
					if self.get_elem(elemid).active:
						active=self.get_elem_id(elemid)
				if active:
					self.get_elem_by_id(active).set_off()
					self.get_elem_by_id(active-1).set_on()
					self.current=active-1
					self.draw()

			elif key == 261:
				#move right
				active=0
				for elemid in ['BT_create', 'BT_edit', 'BT_delete', 'BT_reset', 'BT_write', 'BT_back']:
					if self.get_elem(elemid).active:
						active=self.get_elem_id(elemid)
				if active:
					self.get_elem_by_id(active).set_off()
					self.get_elem_by_id(active+1).set_on()
					self.current=active+1
					self.draw()

			elif len(self.get_elem('SEL_part').result()) > 0:
				selected = self.part_objects[ self.get_elem('SEL_part').result()[0] ]
				self.parent.debug('self.part_objects=%s' % self.part_objects)
				self.parent.debug('cur_elem=%s' % self.get_elem('SEL_part').result()[0])
				self.parent.debug('selected=[%s]' % selected)
				self.container['selected']=self.get_elem('SEL_part').result()[0]
				disk=selected[1]
				part=''
				type=''
				if selected[0] == 'part':
					part=selected[2]
					type = self.container['disk'][disk]['partitions'][part]['type']
				elif selected[0] == 'lvm_lv':
					type = PARTTYPE_LVM_LV

				if key == 266:# F2 - Create
					self.parent.debug('create')
					if type == PARTTYPE_FREE:
						self.parent.debug('create (%s)' % type)
						self.sub=self.edit(self,self.minY+5,self.minX+4,self.maxWidth,self.maxHeight-8)
						self.sub.draw()
					elif selected[0] == 'lvm_vg_free':
						self.parent.debug('create lvm!')
						self.sub=self.edit_lvm_lv(self,self.minY+5,self.minX+4,self.maxWidth,self.maxHeight-8)
						self.sub.draw()

				elif key == 267:# F3 - Edit
					self.parent.debug('edit')
					if type == PARTTYPE_USED:
						item = self.part_objects[ self.get_elem('SEL_part').result()[0] ]
						if 'lvm' in self.parent.container['disk'][item[1]]['partitions'][item[2]]['flag']:
							self.parent.debug('edit lvm pv not allowed')
							msglist=[ _('LVM physical volumes cannot be modified!'), _('If necessary delete this partition.') ]
							self.sub = msg_win(self, self.pos_y+11, self.pos_x+4, self.width-8, self.height-25, msglist)
							self.sub.draw()
						else:
							self.parent.debug('edit! (%s)' % type)
							self.sub=self.edit(self,self.minY+5,self.minX+4,self.maxWidth,self.maxHeight-8)
							self.sub.draw()
					elif selected[0] == 'lvm_lv':
						self.parent.debug('edit lvm!')
						self.sub=self.edit_lvm_lv(self,self.minY+5,self.minX+4,self.maxWidth,self.maxHeight-8)
						self.sub.draw()
				elif key == 268:# F4 - Delete
					self.parent.debug('delete (%s)' % type)
					if type == PARTTYPE_USED or type == PARTTYPE_LVM_LV:
						self.parent.debug('delete!')
						self.part_delete(self.get_elem('SEL_part').result()[0])

				elif key == 270 or self.get_elem('BT_write').get_status(): # F6 - Write Partitions
					self.sub=self.verify(self,self.minY+(self.maxHeight/3),self.minX+(self.maxWidth/8),self.maxWidth,self.maxHeight-18)
					self.sub.draw()

				elif key in [ 10, 32 ]:
					if self.get_elem('SEL_part').get_status():
						if disk or part: #select
							if type == PARTTYPE_USED:
								item = self.part_objects[ self.get_elem('SEL_part').result()[0] ]
								if 'lvm' in self.parent.container['disk'][item[1]]['partitions'][item[2]]['flag']:
									self.parent.debug('edit lvm pv not allowed')
									msglist=[ _('LVM physical volumes cannot be modified!'), _('If necessary delete this partition.') ]
									self.sub = msg_win(self, self.pos_y+11, self.pos_x+4, self.width-8, self.height-25, msglist)
									self.sub.draw()
								else:
									self.parent.debug('edit!')
									self.sub=self.edit(self,self.minY+6,self.minX+4,self.maxWidth,self.maxHeight-8)
									self.sub.draw()
							if type == PARTTYPE_LVM_LV:
								self.parent.debug('edit lvm!')
								self.sub=self.edit_lvm_lv(self,self.minY+6,self.minX+4,self.maxWidth,self.maxHeight-8)
								self.sub.draw()

					elif self.get_elem('BT_create').get_status():#create
						if type == PARTTYPE_FREE:
							self.sub=self.edit(self,self.minY+6,self.minX+4,self.maxWidth,self.maxHeight-8)
							self.sub.draw()

					elif self.get_elem('BT_edit').get_status():#edit
						if type == PARTTYPE_USED:
							item = self.part_objects[ self.get_elem('SEL_part').result()[0] ]
							if 'lvm' in self.parent.container['disk'][item[1]]['partitions'][item[2]]['flag']:
								self.parent.debug('edit lvm pv not allowed')
								msglist=[ _('LVM physical volumes cannot be modified!'), _('If necessary delete this partition.') ]
								self.sub = msg_win(self, self.pos_y+11, self.pos_x+4, self.width-8, self.height-25, msglist)
								self.sub.draw()
							else:
								self.sub=self.edit(self,self.minY+6,self.minX+4,self.maxWidth,self.maxHeight-8)
								self.sub.draw()
						elif selected[0] == 'lvm_lv':
							self.parent.debug('edit lvm!')
							self.sub=self.edit_lvm_lv(self,self.minY+6,self.minX+4,self.maxWidth,self.maxHeight-8)
							self.sub.draw()

					elif self.get_elem('BT_delete').get_status():#delete
						if type == PARTTYPE_USED or type == PARTTYPE_LVM_LV:
							self.part_delete(self.get_elem('SEL_part').result()[0])

					elif key == 10 and self.get_elem_by_id(self.current).usable():
						return self.get_elem_by_id(self.current).key_event(key)

				elif key == curses.KEY_DOWN or key == curses.KEY_UP:
					self.get_elem('SEL_part').key_event(key)
				else:
					self.get_elem_by_id(self.current).key_event(key)
				return 1

		def resolve_part(self,index):
			i=0
			device = self.container['disk'].keys()
			device.sort()
			for disk in device:
				if index is i:
					return ['disk',disk]
				partitions=self.container['disk'][disk]['partitions'].keys()
				partitions.sort()
				j=0
				for part in partitions:
					i+=1
					if index is i:
						return ['part',disk ,part,j]
					j+=1
				i+=1

		def pv_delete(self, parttype, disk, part, force=False):
			# returns False if pv has been deleted
			# return True if pv cannot be deleted

			if 'lvm' in parttype:
				return False

			if self.container['lvm']['enabled'] and 'lvm' in self.container['disk'][disk]['partitions'][part]['flag']:
				device = '%s%d' % (disk,self.container['disk'][disk]['partitions'][part]['num'])
				if self.container['lvm']['pv'].has_key(device):
					pv = self.container['lvm']['pv'][ device ]
					vgname = pv['vg']

					# check if enough free space in VG is present
					if vgname and self.container['lvm']['vg'][ vgname ]['freePE'] < pv['totalPE'] and not force:
						self.parent.debug('Unable to remove physical volume from VG %s - vg[freePE]=%s  pv[totalPE]=%s' %
										  (vgname, self.container['lvm']['vg'][ vgname ]['freePE'], pv['totalPE']))
						msglist = [ _('Unable to remove physical volume from'),
									_('volume group "%s"!') % pv['vg'],
									_('Physical volume contains physical extents in use!') ]
						self.sub = msg_win(self, self.pos_y+11, self.pos_x+4, self.width-8, self.height-24, msglist)
						self.draw()
						return True

					# check if PV is empty
					self.parent.debug( 'pv_delete: remaining LV: %s' % self.container['lvm']['vg'][ vgname ]['lv'].keys() )
					self.parent.debug( 'pv_delete: allocPE: %s' % pv['allocPE'] )
					if len(self.container['lvm']['vg'][ vgname ]['lv']) > 0 and pv['allocPE'] > 0 and not force:
						msglist = [ _('Unable to remove physical volume from'),
									_('volume group "%s"!') % pv['vg'],
									_('Physical volume contains physical extents in use!'),
									_('Please use "pvmove" to move data to other'),
									_('physical volumes.') ]
						self.sub = msg_win(self, self.pos_y+11, self.pos_x+4, self.width-8, self.height-24, msglist)
						self.draw()
						return True
					else:
						# PV is empty
						if vgname:
							# PV is assigned to VG --> update VG data
							vg = self.container['lvm']['vg'][ vgname ]
							vg['freePE'] -= pv['totalPE']
							vg['totalPE'] -= pv['totalPE']
							vg['size'] = vg['PEsize'] * vg['totalPE']
							if vg['freePE'] + vg['allocPE'] != vg['totalPE']:
								self.parent.debug('ASSERTION FAILED: vg[freePE] + vg[allocPE] != vg[totalPE]: %d + %d != %d' % (vg['freePE'], vg['allocPE'], vg['totalPE']))
							if vg['freePE'] < 0 or vg['allocPE'] < 0 or vg['totalPE'] < 0:
								self.parent.debug('ASSERTION FAILED: vg[freePE]=%d  vg[allocPE]=%d  vg[totalPE]=%d' % (vg['freePE'], vg['allocPE'], vg['totalPE']))
							# reduce or remove VG if VG is still present:
							#   then check if PV is last PV in VG ==> if yes, then call vgremove ==> else call vgreduce
							if self.container['lvm']['vg'][ vgname ]['created']:
								vg_cnt = 0
								for tmppv in self.container['lvm']['pv'].values():
									if tmppv['vg'] == vgname:
										vg_cnt += 1
								self.parent.debug('pv_delete: vgname=%s	 vg_cnt=%s' % (vgname, vg_cnt))
								if vg_cnt > 1:
									self.container['history'].append(['/sbin/vgreduce', vgname, device])
								elif vg_cnt == 1:
									self.container['history'].append(['/sbin/vgreduce', '-a', '--removemissing', vgname])
									self.container['history'].append(['/sbin/vgremove', vgname])
									self.container['lvm']['vg'][ vgname ]['created'] = 0
								else:
									self.parent.debug('pv_delete: installer is confused: vg_cnt is 0: doing nothing')
							pv['vg'] = ''

						# removing LVM PV signature from partition
						cmd = ['/sbin/pvremove', device]
						if force:
							cmd = ['/sbin/wrapper-yes-pvremove', '-ff', device]
						self.container['history'].append(cmd)

			return False

		def part_delete(self,index):
			result=self.part_objects[index]
			arg_parttype = result[0]
			arg_disk = result[1]
			arg_part = None
			if len(result) > 2:
				arg_part = result[2]

			self.part_delete_generic(arg_parttype, arg_disk, arg_part)

			self.layout()
			self.draw()

		def part_delete_generic(self, arg_parttype, arg_disk, arg_part, force=False):
			if self.pv_delete(arg_parttype, arg_disk, arg_part, force):
				return

			if arg_parttype == 'lvm_lv':
				parttype = PARTTYPE_LVM_LV
			else:
				parttype = self.container['disk'][arg_disk]['partitions'][arg_part]['type']

			if parttype == PARTTYPE_USED:
				self.container['history'].append(['/sbin/parted', '--script', arg_disk, 'rm', str(self.container['disk'][arg_disk]['partitions'][arg_part]['num'])])
				free_start = align_partition_start(max(EARLIEST_START_OF_FIRST_PARTITION, arg_part)) # first partition should not start earlier than EARLIEST_START_OF_FIRST_PARTITION
				free_end = align_partition_end(self.container['disk'][arg_disk]['partitions'][arg_part]['end'])

				del self.container['disk'][arg_disk]['partitions'][arg_part]
				if free_end - free_start >= PARTSIZE_MINIMUM:
					self.container['disk'][arg_disk]['partitions'][free_start] = self.parent.generate_freespace(free_start, free_end)

			elif parttype == PARTTYPE_LVM_LV:
				lv = self.container['lvm']['vg'][ arg_disk ]['lv'][ arg_part ]

				self.parent.debug('removing LVM LV %s' % lv['dev'])
				self.container['history'].append(['/sbin/lvremove', '-f', lv['dev']])

				# update used/free space on volume group
				currentLE = lv['currentLE']
				self.parent.container['lvm']['vg'][ lv['vg'] ]['freePE'] += currentLE
				self.parent.container['lvm']['vg'][ lv['vg'] ]['allocPE'] -= currentLE

				del self.container['lvm']['vg'][ arg_disk ]['lv'][ arg_part ]

			if parttype != PARTTYPE_LVM_LV:
				self.container['disk'][arg_disk] = self.rebuild_table(self.container['disk'][arg_disk],arg_disk)

		def part_create(self,index,mpoint,size,fstype,parttype,flags,format,label=None):
			result = self.part_objects[index]
			self.part_create_generic(result[1], result[2], mpoint, size, fstype, parttype, flags, format, label)

		def part_create_generic(self, arg_disk, arg_part, mpoint, size, fstype, parttype, flags, format, label=None):
			"""
			arg_disk:  defines disk on which a new partition shall be created
			arg_part:  byte position of free space where the new partition shall be created (has to be megabyte aligned)
			mpoint:    mount point (e.g. '/boot')
			size:      requested partition size in bytes (has to be megabyte aligned)
			type: 	   only valid value is PARTTYPE_USED
			flags:	   array of flags
			format:    format new partition?
			label:     partition label
			"""

			# consistency checks
			if parttype != PARTTYPE_USED:
				self.parent.debug('CONSISTENCY CHECK ERROR: requested type is %s but assumed %s' % (type, PARTTYPE_USED))
			assert(parttype == PARTTYPE_USED)

			# get start and end point of free space
			free_part_start = arg_part
			free_part_end = self.container['disk'][arg_disk]['partitions'][arg_part]['end']
			free_part_size = self.container['disk'][arg_disk]['partitions'][arg_part]['size']
			free_part_type = self.container['disk'][arg_disk]['partitions'][arg_part]['type']
			self.parent.debug("free_part_start = %15d B" % free_part_start)
			self.parent.debug("free_part_end   = %15d B" % free_part_end)
			self.parent.debug("free_part_size  = %15d B" % free_part_size)

			if size > free_part_size:
				self.parent.debug('CONSISTENCY CHECK ERROR: requested size is too large: free_part_size=%s B    requested size=%s B' % (free_part_size, size))
				self.parent.debug('CONSISTENCY CHECK ERROR: shrinking requested partition size')
				size = free_part_size

			# sanitize mpoint → add leading '/' if missing
			if mpoint:
				mpoint = '/%s' % mpoint.lstrip('/')

			label = get_sanitized_label(label, flags, mpoint, fstype)

			# create new partition
			new_part_start = free_part_start
			new_part_end = calc_part_end(free_part_start, size)
			self.container['disk'][arg_disk]['partitions'][arg_part]['touched'] = 1
			self.container['disk'][arg_disk]['partitions'][arg_part]['mpoint'] = mpoint
			self.container['disk'][arg_disk]['partitions'][arg_part]['fstype'] = fstype
			self.container['disk'][arg_disk]['partitions'][arg_part]['flag'] = flags
			self.container['disk'][arg_disk]['partitions'][arg_part]['format'] = format
			self.container['disk'][arg_disk]['partitions'][arg_part]['type'] = parttype
			self.container['disk'][arg_disk]['partitions'][arg_part]['num'] = calc_next_partition_number(self.container['disk'][arg_disk])
			self.container['disk'][arg_disk]['partitions'][arg_part]['size'] = size
			self.container['disk'][arg_disk]['partitions'][arg_part]['end'] = new_part_end
			self.container['disk'][arg_disk]['partitions'][arg_part]['label'] = label
			# WARNING: parted is kind of broken and requires a quoted label as argument → i.e. the value is double quoted
			self.container['history'].append(['/sbin/parted', '--script', arg_disk, 'unit', 'B',
												'mkpart', '"%s"' % label, str(new_part_start), str(new_part_end)])

			# if "size" is smaller than free space and remaining free space is larger than PARTSIZE_MINIMUM then
			# create new entry for free space
			if (free_part_size - size) >= PARTSIZE_MINIMUM:
				new_free_part_start = align_partition_start(new_part_start + size)
				# no need to align free_part_end - it should be aligned by initial import of partition table or by removing a partition
				self.container['disk'][arg_disk]['partitions'][new_free_part_start] = self.parent.generate_freespace(new_free_part_start, free_part_end, touched=1, parttype=free_part_type)
			self.rebuild_table( self.container['disk'][arg_disk], arg_disk)

			for flag in flags:
				if flag not in VALID_PARTED_FLAGS:
					continue
				# parted --script <device> set <partitionnumber> <flagname> on
				self.container['history'].append(['/sbin/parted', '--script', arg_disk, 'set',
													str(self.container['disk'][arg_disk]['partitions'][arg_part]['num']), flag, 'on'])

			if 'lvm' in flags:
				self.pv_create(arg_disk, arg_part)

			self.parent.print_history()
			self.parent.printPartitions()


		def pv_create(self, disk, part):
			device = '%s%d' % (disk,self.container['disk'][disk]['partitions'][part]['num'])
			ucsvgname = self.container['lvm']['ucsvgname']

			# create new PV entry
			pesize = self.container['lvm']['vg'][ ucsvgname ]['PEsize']
			# number of physical extents
			pecnt = int(self.container['disk'][disk]['partitions'][part]['size'] / pesize)
			# calculate overhead for LVM metadata
			peoverhead = int(LVM_OVERHEAD / pesize) + 1
			# reduce total amount of available physical extents by spare physical extents for LVM overhead
			totalpe = max(0, pecnt - peoverhead)

			self.parent.debug('pv_create: pesize=%sk   partsize=%sMiB=%sk  pecnt=%sPE  totalpe=%sPE  peoverhead=%sPE' %
							  (pesize,
							   B2MiB(self.container['disk'][disk]['partitions'][part]['size']),
							   B2KiB(self.container['disk'][disk]['partitions'][part]['size']),
							   pecnt, totalpe, peoverhead))

			self.container['lvm']['pv'][ device ] = { 'touched': 1,
													  'vg': ucsvgname,
													  'PEsize': pesize,
													  'totalPE': totalpe,
													  'freePE': totalpe,
													  'allocPE': 0,
													  }

			# update VG entry
			self.container['lvm']['vg'][ ucsvgname ]['touched'] = 1
			self.container['lvm']['vg'][ ucsvgname ]['totalPE'] += totalpe
			self.container['lvm']['vg'][ ucsvgname ]['freePE'] += totalpe
			self.container['lvm']['vg'][ ucsvgname ]['size'] = (self.container['lvm']['vg'][ ucsvgname ]['totalPE'] *
																self.container['lvm']['vg'][ ucsvgname ]['PEsize'])

			device = self.parent.get_device(disk, part)
			# remove LVMPV signature before creating a new one
			self.container['history'].append(['/sbin/wrapper-yes-pvremove', '-ff', device])
#			self.container['history'].append('/sbin/pvscan')
			self.container['history'].append(['/sbin/pvcreate', device])
			if not self.container['lvm']['vg'][ ucsvgname ]['created']:
				self.container['history'].append(['/sbin/vgcreate', '--physicalextentsize',
													'%sk' % B2KiB(self.container['lvm']['vg'][ ucsvgname ]['PEsize']),
													ucsvgname, device])
				self.container['lvm']['vg'][ ucsvgname ]['created'] = 1
			else:
				self.container['history'].append(['/sbin/vgextend', ucsvgname, device])


		def add_changed_flags_to_history(self, path, part, old_flags, flags):
			self.parent.debug('add_changed_flags_to_history: old_flags = %s     flags = %s' % (old_flags, flags))
			for f in old_flags:
				if f not in flags and f in VALID_PARTED_FLAGS:
					self.container['history'].append(['/sbin/parted', '--script', path, 'set', str(self.container['disk'][path]['partitions'][part]['num']), f, 'off'])
			for f in flags:
				if f not in old_flags and f in VALID_PARTED_FLAGS:
					self.container['history'].append(['/sbin/parted', '--script', path, 'set', str(self.container['disk'][path]['partitions'][part]['num']), f, 'on'])
			self.parent.debug('add_changed_flags_to_history: history updated')
			self.parent.print_history()

		def part_edit_determine_settings(self, disk, part, mpoint, fstype, flags, format, label=None):
			partition = copy.deepcopy(self.parent.container['disk'][disk]['partitions'][part])

			self.parent.debug('part_edit_determine_settings: format = %r' % format)
			self.parent.debug('part_edit_determine_settings: fstype = %r' % fstype)
			self.parent.debug('part_edit_determine_settings: flags = %r' % flags)
			self.parent.debug('part_edit_determine_settings: mpoint = %r' % mpoint)

			partition['flag'] = flags
			partition['fstype'] = fstype
			partition['mpoint'] = mpoint

			# EFI partition will be mounted at /boot/efi with vfat as file system
			if PARTFLAG_EFI in flags:
				partition['mpoint'] = MOUNTPOINT_EFI
				partition['fstype'] = FSTYPE_EFI

			# LVM PV has no mount point
			if PARTFLAG_LVM in flags:
				partition['mpoint'] = ''
				partition['fstype'] = FSTYPE_LVMPV

			# BIOS boot partitions do not need to be formatted
			if PARTFLAG_BIOS_GRUB in flags:
				partition['mpoint'] = ''
				partition['format'] = 0

			# SWAP has no mount point
			if PARTFLAG_SWAP in flags:
				partition['mpoint'] = ''
				partition['fstype'] = FSTYPE_SWAP

			# sanitize mpoint → add leading '/' if missing
			if partition['mpoint'] and PARTFLAG_BIOS_GRUB not in flags:
				partition['mpoint'] = '/%s' % partition['mpoint'].lstrip('/')

			# create label if not given
			if label:
				partition['label'] = label
			else:
				partition['label'] = get_sanitized_label('', partition['flag'], partition['mpoint'], partition['fstype'])

			return partition

		def part_edit_set_settings(self, disk, part, temp_part):
			self.parent.debug('part_edit_set_settings: temp_part = %s' % pretty_format(temp_part))
			old_flags = self.parent.container['disk'][disk]['partitions'][part]['flag']
			if temp_part['format']:
				self.parent.debug('part_edit_set_settings: calling add_changed_flags_to_history')
				self.add_changed_flags_to_history(disk, part, old_flags, temp_part['flag'])
			self.parent.container['disk'][disk]['partitions'][part] = temp_part
			if PARTFLAG_LVM in temp_part['flag']:
				self.pv_create(disk, part)

		def rebuild_table(self, disk, device):
			# get ordered list of start positions of all partitions on given disk
			partitions = copy.copy(disk['partitions'])
			partlist = partitions.keys()
			partlist.sort()

			self.parent.debug('rebuild_table(%s): OLD VALUES\n%s' % (device, pretty_format(partitions)))

			i = 0
			# iterate over partlist items with index 0...(len-2)
			while i < len(partlist)-1:
				start_current = partlist[i]
				start_next = partlist[i+1]
				# compare current and next partition's type
				# ==> if both entries define free space then merge those entries
				if partitions[start_current]['type'] == PARTTYPE_FREE and \
						partitions[start_current]['type'] == partitions[start_next]['type']:
					partitions[start_current]['size'] += partitions[start_next]['size']
					partitions[start_current]['end'] += partitions[start_next]['size']
					# remove "next" partition from list
					partlist.remove(start_next)
					del partitions[start_next]
				else:
					# if not free space and not merged then jump to next entry
					i += 1

			self.parent.debug('rebuild_table(%s): NEW VALUES\n%s' % (device, pretty_format(partitions)))

			disk['partitions'] = partitions
			return disk

		def lv_create(self, vgname, lvname, currentLE, format, fstype, flag, mpoint):
			vg = self.parent.container['lvm']['vg'][ vgname ]
			size = int(vg['PEsize'] * currentLE)
			self.container['lvm']['vg'][vgname]['lv'][lvname] = { 'dev': '/dev/%s/%s' % (vgname, lvname),
																  'vg': vgname,
																  'touched': 1,
																  'PEsize': vg['PEsize'],
																  'currentLE': currentLE,
																  'format': format,
																  'size': size,
																  'fstype': fstype,
																  'flag': '',
																  'mpoint': mpoint,
																  }

			self.parent.container['history'].append(['/sbin/lvcreate', '-l', str(currentLE), '--name', lvname, vgname])
#			self.parent.container['history'].append('/sbin/lvscan 2> /dev/null')

			self.parent.print_history()

			# update used/free space on volume group
			self.parent.container['lvm']['vg'][ vgname ]['freePE'] -= currentLE
			self.parent.container['lvm']['vg'][ vgname ]['allocPE'] += currentLE

		def get_result(self):
			pass

		# returns False if one or more device files cannot be found - otherwise True
		def write_devices_check(self):
			self.parent.debug('WRITE_DEVICES')
			error = self.write_devices()
			if error:
				self.ERROR = False
				msg = []
				for err in error.split('\n'):
					msg.append(err[:60])
				self.sub = msg_win(self, self.pos_y+6, self.pos_x+1, self.width-1, 2, msg)
				self.parent.start()
				self.draw()
				return False
			return True

		def write_devices(self):
			self.draw()
			self.act = self.active(self, _('Writing partitions'), _('Please wait ...'), name='act', action='create_partitions')
			self.act.draw()
			if self.ERROR:
				return _("Error while writing partitions:") + "\n" + self.ERROR
			if self.container['lvm']['enabled']:
				self.act = self.active(self, _('Creating LVM Volumes'), _('Please wait ...'), name='act', action='make_filesystem')
				self.act.draw()
				if self.ERROR:
					return _("Error while creating LVM volumes:") +"\n" + self.ERROR
			self.act = self.active(self, _('Creating file systems'), _('Please wait ...'), name='act', action='make_filesystem')
			self.act.draw()
			if self.ERROR:
				return _("Error while creating file systems:") + "\n" + self.ERROR
			self.draw()

		class active(act_win):
			def __init__(self, parent, header, text, name='act', action=None):
				if action == 'read_lvm':
					self.pos_x = parent.minX+(parent.maxWidth/2)-18
					self.pos_y = parent.minY+11
				else:
					self.pos_x = parent.minX+(parent.maxWidth/2)-13
					self.pos_y = parent.minY+11
				self.action = action
				act_win.__init__(self, parent, header, text, name)

			def run_command(self, command):
				self.parent.parent.debug('running %s' % command)
				proc = subprocess.Popen(command, bufsize=0, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				(stdout, stderr) = proc.communicate()
				self.parent.parent.debug('===(exitcode=%d)====> %s\nSTDERR:\n=> %s\nSTDOUT:\n=> %s' %
										 (proc.returncode, command, stderr.replace('\n','\n=> '), stdout.replace('\n','\n=> ')))
				self.parent.parent.debug('waiting for udev to settle down')
				os.system("udevadm settle || true")

				if proc.returncode:
					self.parent.container['history'] = []
					self.parent.ERROR = "%s (%s)\n%s " % (command, proc.returncode, stderr)

				return proc.returncode

			def function(self):
				if self.action == 'read_lvm':
					self.parent.parent.debug('Reading LVM config')
					self.parent.parent.read_lvm()
				elif self.action == 'create_partitions':
					self.parent.parent.debug('Create Partitions')
					for command in self.parent.container['history']:
						retval = self.run_command(command)
						if retval:
							return
					self.parent.container['history'] = []

					# fix boot flag in protective MBR that has been mistakenly removed by parted 2.3
					for diskname, disk in self.parent.container['disk'].items():
						for partname, part in disk['partitions'].items():
							device = self.parent.parent.get_device(diskname, partname)
							self.parent.parent.debug('fix_boot_flag test: device=%s  flag=%r' % (device, part['flag']))
							if PARTFLAG_BIOS_GRUB in part['flag']:
								self.parent.parent.fix_boot_flag_in_protective_mbr(diskname)

					self.parent.parent.written = 1
				elif self.action == 'make_filesystem':
					self.parent.parent.debug('Create Filesystem')
					# create filesystems on physical partitions
					for disk in self.parent.container['disk'].keys():
						for part in self.parent.container['disk'][disk]['partitions'].keys():
							if self.parent.container['disk'][disk]['partitions'][part]['format']:
								device = self.parent.parent.get_device(disk, part)
								fstype=self.parent.container['disk'][disk]['partitions'][part]['fstype']
								mkfs_cmd = get_mkfs_cmd(device, fstype)
								self.parent.parent.debug('mkfs_cmd=%r   (%r, %r)' % (mkfs_cmd, device, fstype))
								if mkfs_cmd:
									retval = self.run_command(mkfs_cmd)
									if retval:
										return
								self.parent.container['disk'][disk]['partitions'][part]['format']=0
					# create filesystems on logical volumes
					for vgname in self.parent.container['lvm']['vg'].keys():
						vg = self.parent.container['lvm']['vg'][ vgname ]
						for lvname in vg['lv'].keys():
							if vg['lv'][lvname]['format']:
								device = vg['lv'][lvname]['dev']
								fstype = vg['lv'][lvname]['fstype']
								mkfs_cmd = get_mkfs_cmd(device, fstype)
								self.parent.parent.debug('mkfs_cmd=%r   (%r, %r)' % (mkfs_cmd, device, fstype))
								if mkfs_cmd:
									retval = self.run_command(mkfs_cmd)
									if retval:
										return
								vg['lv'][lvname]['format'] = 0

				self.parent.layout()
				self.stop()

		class edit(subwin):
			OPERATION_EDIT = 'edit'
			OPERATION_CREATE = 'create'

			def __init__(self,parent,pos_x,pos_y,width,height):
				self.close_on_subwin_exit = False
				self.title = 'unknown'
				self.parent = parent
				self.load_filesystems()

				deviceentry = self.parent.part_objects[self.parent.get_elem('SEL_part').result()[0]]
				partition = self.parent.container['disk'][deviceentry[1]]['partitions'][deviceentry[2]]
				if partition['type'] == PARTTYPE_FREE:
					self.operation = self.OPERATION_CREATE
					height -= 2
				else:
					self.operation = self.OPERATION_EDIT

				subwin.__init__(self,parent,pos_x,pos_y,width,height)

			def load_filesystems(self):
				""" load available filesystems """
				try:
					file = open('modules/filesystem')
				except:
					file = open('/lib/univention-installer/modules/filesystem')
				self.fsdict={}
				filesystem = file.readlines()
				i = 0
				for line in filesystem:
					fs = line.split(' ')
					if len(fs) > 1:
						entry = fs[1].strip()
						if not entry == FSTYPE_SWAP:
							self.fsdict[entry] = [entry, i]
							i += 1
				file.close()
				self.parent.parent.debug('self.fsdict = %s' % pretty_format(self.fsdict))

				if self.parent.container['lvm']['enabled']:
					self.partflags = { _('Data'): [PARTFLAG_NONE, 0],
									   _('Swap'): [PARTFLAG_SWAP, 1],
									   _('LVM PV'): [PARTFLAG_LVM, 2],
									   _('BIOS Boot'): [PARTFLAG_BIOS_GRUB, 3],
									   _('EFI System'): [PARTFLAG_EFI, 4],
									   }
				else:
					self.partflags = { _('Data'): [PARTFLAG_NONE, 0],
									   _('Swap'): [PARTFLAG_SWAP, 1],
									   _('BIOS Boot'): [PARTFLAG_BIOS_GRUB, 2],
									   _('EFI System'): [PARTFLAG_EFI, 3],
									   }


			def helptext(self):
				return self.parent.helptext()

			def no_format_callback_part_create(self, result):
				selected = self.parent.container['temp']['selected']
				mpoint = self.parent.container['temp']['mpoint']
				size = self.parent.container['temp']['size']
				fstype = self.parent.container['temp']['fstype']
				parttype = self.parent.container['temp']['type']
				flag = self.parent.container['temp']['flag']
				self.parent.container['temp'] = {}
				if result == 'BT_YES':
					format=1
				elif result == 'BT_NO':
					format=0
				self.parent.part_create(selected, mpoint, size, fstype, parttype, flag, format)
				return 0

			def no_format_callback_part_edit(self, result, path, part):
				temp_part = self.parent.container['temp']
				self.parent.container['temp'] = {}
				if result == 'BT_YES':
					temp_part['format'] = 1
				else:
					# user declined format / partition type change gets also reverted
					temp_part['format'] = 0
					temp_part['flag'] = self.parent.container['disk'][path]['partitions'][part]['flag']
				self.parent.part_edit_set_settings(path, part, temp_part)
				return 0

			def ignore_experimental_fstype(self):
				self.expFStype = True
				return 0

			def set_title(self, title):
				""" set new title/header for subwin """
				self.title = title
				self.update_header()

			def modheader(self):
				return self.title

			def input(self, key):
				dev = self.parent.part_objects[self.parent.get_elem('SEL_part').result()[0]]
				parttype = dev[0]
				path = dev[1]
				disk = self.parent.container['disk'][path]

				if hasattr(self,"sub"):
					if not self.sub.input(key):
						self.parent.layout()
						self.sub.exit()
						self.draw()
						if self.close_on_subwin_exit:
							return 0
					return 1
				if key == 260 and self.get_elem('BT_save').active:
					#move left
					self.get_elem('BT_save').set_off()
					self.get_elem('BT_cancel').set_on()
					self.current = self.get_elem_id('BT_cancel')
					self.draw()
				elif key == 261 and self.get_elem('BT_cancel').active:
					#move right
					self.get_elem('BT_cancel').set_off()
					self.get_elem('BT_save').set_on()
					self.current = self.get_elem_id('BT_save')
					self.draw()
				elif key in [ 10, 32, 276 ]:
					if self.get_elem('BT_cancel').usable() and self.get_elem('BT_cancel').get_status():
						return 0
					elif ( self.get_elem('BT_save').usable() and self.get_elem('BT_save').get_status() ) or key == 276:
						if self.operation == self.OPERATION_CREATE: # Speichern
							part = dev[2]
							mpoint = self.get_elem('INP_mpoint').result().strip()
							if self.get_elem('INP_size').result().isdigit():
								size = MiB2B(int(self.get_elem('INP_size').result()))
							else:
								return 1
							format = self.get_elem('CB_format').result()
							fstype = self.get_elem('SEL_fstype').result()[0]
							# check experimental filesystems
							msg = [_("Filesystem %s:") % fstype]
							EXPERIMENTAL_FSTYPES_MSG = [_('This is a highly experimental filesystem'), _('and should not be used in productive'), _('environments.')]
							for i in EXPERIMENTAL_FSTYPES_MSG:
								msg.append(i)
							if fstype in EXPERIMENTAL_FSTYPES and not hasattr(self,"expFStype"):
								self.sub = msg_win(self, self.pos_y+4, self.pos_x+1, self.width-2, 0, callback=self.ignore_experimental_fstype, msglist=msg)
								self.sub.draw()
								return 1

							parttype = PARTTYPE_USED
							if disk['partitions'][part]['size'] < size:
								self.parent.debug('edit:input: size given by user is too large. Falling back to size of free space: %d < %d' % (disk['partitions'][part]['size'], size))
								size = disk['partitions'][part]['size']

							flag = [self.get_elem('SEL_partflags').result()[0]]
							if PARTFLAG_LVM in flag:
								mpoint = ''
								format = 1
								fstype = FSTYPE_LVMPV

							if PARTFLAG_EFI in flag:
								mpoint = MOUNTPOINT_EFI
								format = 1
								fstype = FSTYPE_EFI

							if PARTFLAG_SWAP in flag:
								mpoint = ''
								fstype = FSTYPE_SWAP

							# sanitize mpoint → add leading '/' if missing
							if mpoint:
								mpoint = '/%s' % mpoint.lstrip('/')

							self.parent.container['temp'] = {'selected': self.parent.get_elem('SEL_part').result()[0],
										'mpoint': mpoint,
										'size': size,
										'fstype': fstype,
										'type': parttype,
										'flag': flag,
										}

							msglist = [ _('The selected file system takes no'),
										_('effect, if format is not selected.'),
										'',
										_('Do you want to format this partition?') ]

							if not format:
								self.close_on_subwin_exit = True
								self.sub = yes_no_win(self, self.pos_y+4, self.pos_x+1, self.width-2, 0,
													  msglist=msglist, callback_yes=self.no_format_callback_part_create,
													  callback_no=self.no_format_callback_part_create, default='no' )
								self.sub.draw()
								return 1
							else:
								self.parent.container['temp'] = {}
								format=1

							self.parent.part_create(self.parent.get_elem('SEL_part').result()[0],mpoint,size,fstype,parttype,flag,format)

						elif self.operation == self.OPERATION_EDIT: # Speichern
							part = dev[2]
							old_flags = self.parent.container['disk'][path]['partitions'][part]['flag']
							old_fstype = self.parent.container['disk'][path]['partitions'][part]['fstype']
							if not old_flags:
								old_flags = [PARTFLAG_NONE]

							mpoint = self.get_elem('INP_mpoint').result().strip()
							fstype = self.get_elem('SEL_fstype').result()[0]
							flags = [self.get_elem('SEL_partflags').result()[0]]
							format = 0
							if self.get_elem('CB_format').result():
								format = 1

							# check experimental filesystems
							msg = [_("Filesystem %s:") % fstype]
							EXPERIMENTAL_FSTYPES_MSG = [_('This is a highly experimental filesystem'), _('and should not be used in productive'), _('environments.')]
							for i in EXPERIMENTAL_FSTYPES_MSG:
								msg.append(i)
							if fstype in EXPERIMENTAL_FSTYPES and not hasattr(self,"expFStype"):
								self.sub = msg_win(self, self.pos_y+4, self.pos_x+1, self.width-2, 0, callback=self.ignore_experimental_fstype, msglist=msg)
								self.sub.draw()
								return 1

							# determine new partition settings depending user input
							temp_part = self.parent.part_edit_determine_settings(path, part, mpoint, fstype, flags, format)
							temp_part['format'] = format

							# save values in temporary object → will be used if format question is shown (see below)
							self.parent.container['temp'] = temp_part

							rootfs = (mpoint == '/')
							# if format == 0, check if user shall be asked to format partition:
							# FROM \ TO | none | swap | lvm | bios_grub | boot |
							#		\------------------------------------------|
							#	   none | FSCG |  Y	  |	 Y	|	 N		|  Y   |
							#	   swap |  Y   |  N	  |	 Y	|	 N		|  Y   |
							#		lvm |  Y   |  Y	  |	 N	|	 N		|  Y   |
							# bios_grub |  Y   |  Y	  |	 Y	|	 N		|  Y   |
							#	   boot |  Y   |  Y	  |	 Y	|	 N		|  N   |
							#
							# ==> LVM PV partitions may not be edited at the moment ==> irrelevant
							# ==> bios_grub partitions to not have to be formatted ==> irrelevant
							# ==> "FSCG" ==> if filesystem changes on that partition, it has to be formatted or mpoint is '/'
							#
							if ((format == 0) and ((old_flags != flags and not PARTFLAG_BIOS_GRUB in flags) or
												   (PARTFLAG_NONE in flags and (old_fstype != fstype or rootfs)))):
								if rootfs:
									msglist = [ _('This partition is designated as root file system,'),
												_('but "format" is not selected. This can cause'),
												_('problems with preexisting data on disk!'),
												'',
												_('Do you want to format this partition?')
												]
								else:
									msglist = [ _('The selected file system and partition type'),
												_('take no effect, if "format" is not selected.'),
												'',
												_('Do you want to format this partition?')
												]

								self.close_on_subwin_exit = True
								self.sub = yes_no_win(self, self.pos_y+4, self.pos_x+1, self.width-2, 0,
													  msglist=msglist, callback_yes=self.no_format_callback_part_edit,
													  callback_no=self.no_format_callback_part_edit, default='no', path=path, part=part )
								self.sub.draw()
								return 1
							else:
								self.parent.part_edit_set_settings(path, part, temp_part)
								self.parent.container['temp'] = {}

						self.parent.container['disk'][path] = self.parent.rebuild_table(disk, path)

						self.parent.layout()
						self.parent.draw()
						return 0
					elif key == 10 and self.get_elem_by_id(self.current).usable():
						return self.get_elem_by_id(self.current).key_event(key)
				if self.get_elem_by_id(self.current).usable():
					self.get_elem_by_id(self.current).key_event(key)

				self.update_widget_states()
				return 1

			def get_result(self):
				pass

			def update_widget_states(self):
				if PARTFLAG_NONE in self.get_elem('SEL_partflags').result():
					self.get_elem('INP_mpoint').enable()
					self.get_elem('SEL_fstype').enable()
				else:
					self.get_elem('INP_mpoint').disable()
					self.get_elem('SEL_fstype').disable()

				if self.get_elem('SEL_partflags').result()[0] in (PARTFLAG_NONE, PARTFLAG_SWAP, PARTFLAG_EFI, PARTFLAG_LVM):
					self.get_elem('CB_format').enable()
				else:
					self.get_elem('CB_format').disable()

			def layout(self):
				dev = self.parent.part_objects[self.parent.get_elem('SEL_part').result()[0]]
				parttype = dev[0]
				path = dev[1]
				disk = self.parent.container['disk'][path]

				if parttype is 'part':
					start = dev[2]
					partition = disk['partitions'][start]
					if self.operation == self.OPERATION_CREATE:
						self.set_title(_('Create new partition'))
						self.add_elem('TXT_3', textline(_('Size (MiB):'), self.pos_y+2, self.pos_x+5)) #3
						self.add_elem('INP_size', input(str(int(B2MiB(partition['size']))), self.pos_y+2, self.pos_x+6+len(_('Mount point:')), 12)) #4
						self.add_elem('TXT_2', textline(_('Mount point:'), self.pos_y+4, self.pos_x+5)) #1
						self.add_elem('INP_mpoint', input(partition['mpoint'], self.pos_y+4, self.pos_x+6+len(_('Mount point:')), 35)) #2

						self.add_elem('TXT_5', textline(_('Partition type:'), self.pos_y+6, self.pos_x+5))
						self.add_elem('SEL_partflags', select(self.partflags, self.pos_y+7, self.pos_x+4, 17, 5))
						self.get_elem('SEL_partflags').set_off()

						self.parent.parent.debug('self.fsdict = %s' % pretty_format(self.fsdict))
						self.add_elem('TXT_4', textline(_('File system:'), self.pos_y+6, self.pos_x+33))
						self.add_elem('SEL_fstype', select(self.fsdict, self.pos_y+7, self.pos_x+33, 17, 8))
						self.get_elem('SEL_fstype').set_off()

						self.add_elem('CB_format', checkbox({_('format'):'1'}, self.pos_y+13, self.pos_x+5, 14, 1, [0]))

						self.add_elem('BT_save', button("F12-"+_("Save"), self.pos_y+15, self.pos_x+(self.width)-4, align="right")) #11
						self.add_elem('BT_cancel', button("ESC-"+_("Cancel"), self.pos_y+15, self.pos_x+4, align="left")) #12

						self.current = self.get_elem_id('INP_size')
						self.get_elem_by_id(self.current).set_on()

					else:  #got a valid partition
						self.set_title(_('Edit partition'))
						self.add_elem('TXT_1', textline(_('Partition: %s') % self.parent.dev_to_part(partition, path, type="full"), self.pos_y+2, self.pos_x+5)) #0
						self.add_elem('TXT_3', textline(_('Size: %d MiB') % B2MiB(partition['size']), self.pos_y+4, self.pos_x+5)) #2
						self.add_elem('TXT_5', textline(_('Mount point:'), self.pos_y+6, self.pos_x+5)) #5
						self.add_elem('INP_mpoint', input(partition['mpoint'], self.pos_y+6, self.pos_x+6+len(_('Mount point:')), 35)) #2

						# get currently selected entry
						partflags_num = 0
						for flag in partition['flag']:
							for name, value in self.partflags.items():
								if flag == value[0]:
									partflags_num = value[1]
									break
						self.add_elem('TXT_5', textline(_('Partition type:'), self.pos_y+8, self.pos_x+5))
						self.add_elem('SEL_partflags', select(self.partflags, self.pos_y+9, self.pos_x+4, 17, 5, partflags_num))
						self.get_elem('SEL_partflags').set_off()

						# get currently selected entry
						filesystem_num = self.fsdict.get(partition['fstype'], [0,0])[1]
						self.add_elem('TXT_4', textline(_('File system:'), self.pos_y+8, self.pos_x+33))
						self.add_elem('SEL_fstype', select(self.fsdict, self.pos_y+9, self.pos_x+33, 17, 7, filesystem_num)) #4
						self.get_elem('SEL_fstype').set_off()

						if partition['format']:
							self.add_elem('CB_format', checkbox({_('format'):'1'}, self.pos_y+15, self.pos_x+5, 14, 1, [0])) #10
						else:
							self.add_elem('CB_format', checkbox({_('format'):'1'}, self.pos_y+15, self.pos_x+5, 14, 1, [])) #10

						self.add_elem('BT_save', button("F12-"+_("Save"), self.pos_y+17, self.pos_x+(self.width)-4, align="right")) #11
						self.add_elem('BT_cancel', button("ESC-"+_("Cancel"), self.pos_y+17, self.pos_x+4, align='left')) #12
						self.update_widget_states()
						if self.get_elem('INP_mpoint').usable():
							self.current = self.get_elem_id('INP_mpoint')
						else:
							self.current = self.get_elem_id('SEL_partflags')
						self.get_elem_by_id(self.current).set_on()

		class edit_lvm_lv(subwin):
			def __init__(self,parent,pos_x,pos_y,width,height):
				self.close_on_subwin_exit = False
				self.title = 'unknown'
				subwin.__init__(self,parent,pos_x,pos_y,width,height)

			def helptext(self):
				return self.parent.helptext()

			def no_format_callback(self, result, lv):
				if result == 'BT_YES':
					format=1
				else:
					format=0
				lv['format'] = format
				return result

			def ignore_experimental_fstype(self):
				self.expFStype = True

			def set_title(self, title):
				""" set new title/header for subwin """
				self.title = title
				self.update_header()

			def modheader(self):
				return self.title

			def input(self, key):
				parttype, vgname, lvname = self.parent.part_objects[self.parent.get_elem('SEL_part').result()[0]]

				if hasattr(self,"sub"):
					res = self.sub.input(key)
					if not res:
						if not self.sub.incomplete():
							self.sub.exit()
							self.draw()
							if self.close_on_subwin_exit:
								return 0
					return 1
				elif key == 260 and self.get_elem('BT_save').active:
					#move left
					self.get_elem('BT_save').set_off()
					self.get_elem('BT_cancel').set_on()
					self.current = self.get_elem_id('BT_cancel')
					self.draw()
				elif key == 261 and self.get_elem('BT_cancel').active:
					#move right
					self.get_elem('BT_cancel').set_off()
					self.get_elem('BT_save').set_on()
					self.current = self.get_elem_id('BT_save')
					self.draw()
				elif key in [ 10, 32, 276 ]:
					if self.get_elem('BT_cancel').usable() and self.get_elem('BT_cancel').get_status():
						return 0
					elif ( self.get_elem('BT_save').usable() and self.get_elem('BT_save').get_status() ) or key == 276:

						if self.operation is 'create': # save new logical volume

							vg = self.parent.container['lvm']['vg'][ vgname ]

							# get values

							lvname = self.get_elem('INP_name').result()
							mpoint = self.get_elem('INP_mpoint').result().strip()
							size = None
							if self.get_elem('INP_size').result().isdigit():
								size = MiB2B(int(self.get_elem('INP_size').result()))
							format = self.get_elem('CB_format').result()
							fstype = self.get_elem('SEL_fstype').result()[0]

							# do some consistency checks
							lvname_ok = True
							for c in lvname:
								if not(c.isalnum() or c == '_'):
									lvname_ok = False

							if not lvname or lvname in vg['lv'].keys() or not lvname_ok:
								if not lvname:
									msglist = [ _('Please enter volume name!') ]
								elif not lvname_ok:
									msglist = [ _('Logical volume name contains illegal characters!') ]
								else:
									msglist = [ _('Logical volume name is already in use!') ]

								self.get_elem_by_id(self.current).set_off()
								self.current=self.get_elem_id('INP_name')
								self.get_elem_by_id(self.current).set_on()

								self.sub = msg_win(self,self.pos_y+4,self.pos_x+1,self.width-2,7, msglist)
								self.draw()
								return 1

							if size is None:
								self.get_elem_by_id(self.current).set_off()
								self.current = self.get_elem_id('INP_size')
								self.get_elem_by_id(self.current).set_on()

								msglist = [ _('Size contains non-digit characters!') ]
								self.sub = msg_win(self,self.pos_y+4,self.pos_x+1,self.width-2,7, msglist)
								self.draw()
								return 1

							currentLE = size / vg['PEsize']
							if size % vg['PEsize']: # number of logical extents has to cover at least "size" bytes
								currentLE += 1

							if currentLE > vg['freePE']:  # decrease logical volume by one physical extent - maybe it fits then
								currentLE -= 1

							if currentLE > vg['freePE']:
								self.get_elem_by_id(self.current).set_off()
								self.current = self.get_elem_id('INP_size')
								self.get_elem_by_id(self.current).set_on()

								msglist = [ _('Not enough free space on volume group!') ]
								self.sub = msg_win(self, self.pos_y+4, self.pos_x+1, self.width-2, 7, msglist)
								self.draw()
								return 1

							# check experimental filesystems
							msg = [_("Filesystem %s:") % fstype]
							EXPERIMENTAL_FSTYPES_MSG = [_('This is a highly experimental filesystem'),_('and should not be used in productive'),_('environments.')]
							for i in EXPERIMENTAL_FSTYPES_MSG:
								msg.append(i)
							if fstype in EXPERIMENTAL_FSTYPES and not hasattr(self,"expFStype"):
								self.sub = msg_win(self, self.pos_y+4, self.pos_x+1, self.width-2, 0, callback = self.ignore_experimental_fstype, msglist=msg)
								self.sub.draw()
								return 1

							# data seems to be ok ==> create LVM LV
							self.parent.lv_create(vgname, lvname, currentLE, format, fstype, '', mpoint)

							msglist = [ _('The selected file system takes no'),
										_('effect, if format is not selected.'),
										'',
										_('Do you want to format this partition?') ]

							if not format:
								self.close_on_subwin_exit = True
								self.sub = yes_no_win(self, self.pos_y+4, self.pos_x+1, self.width-2, 0,
													  msglist=msglist, callback_yes=self.no_format_callback,
													  callback_no=self.no_format_callback, default='no', lv=vg['lv'][lvname] )
								self.sub.draw()
								return 1

						elif self.operation is 'edit': # Speichern
							# get and save values
							oldfstype = self.parent.container['lvm']['vg'][vgname]['lv'][lvname]['fstype']
							fstype = self.get_elem('SEL_fstype').result()[0]
							self.parent.container['lvm']['vg'][vgname]['lv'][lvname]['touched'] = 1
							self.parent.container['lvm']['vg'][vgname]['lv'][lvname]['mpoint'] = self.get_elem('INP_mpoint').result().strip()
							self.parent.container['lvm']['vg'][vgname]['lv'][lvname]['format'] = self.get_elem('CB_format').result()
							self.parent.container['lvm']['vg'][vgname]['lv'][lvname]['fstype'] = fstype

							rootfs = (self.parent.container['lvm']['vg'][vgname]['lv'][lvname]['mpoint'] == '/')

							# check experimental filesystems
							msg = [_("Filesystem %s:") % fstype]
							EXPERIMENTAL_FSTYPES_MSG = [_('This is a highly experimental filesystem'),_('and should not be used in productive'),_('environments.')]
							for i in EXPERIMENTAL_FSTYPES_MSG:
								msg.append(i)
							if fstype in EXPERIMENTAL_FSTYPES and not hasattr(self,"expFStype"):
								self.sub = msg_win(self, self.pos_y+4, self.pos_x+1, self.width-2, 0,
									callback=self.ignore_experimental_fstype, msglist=msg)
								self.sub.draw()
								return 1

							# if format is not set and mpoint == '/' OR
							#    format is not set and fstype changed
							if ( oldfstype != fstype or rootfs) and not self.get_elem('CB_format').result():
								if rootfs:
									msglist = [ _('This volume is designated as root filesystem,'),
												_('but "format" is not selected. This can cause'),
												_('problems with preexisting data on disk!'),
												'',
												_('Do you want to format this partition?')
												]
								else:
									msglist = [ _('The selected file system takes no'),
												_('effect, if "format" is not selected.'),
												'',
												_('Do you want to format this partition?')
												]

								self.close_on_subwin_exit = True
								self.sub = yes_no_win(self, self.pos_y+4, self.pos_x+1, self.width-2, 0,
													  msglist=msglist, callback_yes=self.no_format_callback,
													  callback_no=self.no_format_callback, default='no',
													  lv=self.parent.container['lvm']['vg'][vgname]['lv'][lvname] )
								self.sub.draw()
								return 1

						self.parent.layout()
						self.parent.draw()

						return 0

					elif key == 10 and self.get_elem_by_id(self.current).usable():
						return self.get_elem_by_id(self.current).key_event(key)

				if self.get_elem_by_id(self.current).usable():
					self.get_elem_by_id(self.current).key_event(key)

				return 1

			def get_result(self):
				pass

			def layout(self):
				parttype, vgname, lvname = self.parent.part_objects[self.parent.get_elem('SEL_part').result()[0]]
				self.operation = ''

				if parttype is 'lvm_vg_free':  # FREE SPACE ON VOLUME GROUP
					vg = self.parent.container['lvm']['vg'][ vgname ]
					maxsize = int(vg['PEsize'] * vg['freePE']) # calculate maximum size in bytes

					lvname_proposal = ''
					for i in xrange(1, 9999):
						if not vg['lv'].has_key('vol%d' % i):
							lvname_proposal = 'vol%d' % i
							break

					self.operation = 'create'
					self.set_title(_('Create new LVM logical volume'))
					self.add_elem('TXT_0', textline(_('Volume name:'), self.pos_y+2, self.pos_x+5)) #0
					self.add_elem('INP_name', input(lvname_proposal, self.pos_y+2, self.pos_x+5+len(_('Volume name:'))+1, 20)) #2
					self.add_elem('TXT_3', textline(_('Size (MiB):'), self.pos_y+4, self.pos_x+5)) #3
					self.add_elem('INP_size', input(str(int(B2MiB(maxsize))), self.pos_y+4, self.pos_x+5+len(_('Mount point:'))+1, 12)) #4
					self.add_elem('TXT_1', textline(_('Mount point:'), self.pos_y+6, self.pos_x+5)) #1
					self.add_elem('INP_mpoint', input('', self.pos_y+6, self.pos_x+5+len(_('Mount point:'))+1,35)) #2
					self.add_elem('TXT_5', textline(_('File system:'), self.pos_y+8, self.pos_x+5)) #5

					try:
						file=open('modules/filesystem')
					except:
						file=open('/lib/univention-installer/modules/filesystem')
					dict={}
					filesystem_num=0
					filesystem=file.readlines()
					i=0
					for line in filesystem:
						fs=line.split(' ')
						if len(fs) > 1:
							entry = fs[1][:-1]
							if entry not in BLOCKED_FSTYPES_ON_LVM:   # disable e.g. swap on LVM
								dict[entry]=[entry,i]
								i += 1
					file.close()
					self.add_elem('SEL_fstype', select(dict, self.pos_y+9, self.pos_x+4, 15, 6)) #6
					self.get_elem('SEL_fstype').set_off()

					self.add_elem('CB_format', checkbox({_('format'):'1'}, self.pos_y+14, self.pos_x+33, 14, 1, [0])) #7

					self.add_elem('BT_save', button("F12-"+_("Save"), self.pos_y+17, self.pos_x+(self.width)-4, align="right")) #8
					self.add_elem('BT_cancel', button("ESC-"+_("Cancel"), self.pos_y+17, self.pos_x+4, align="left")) #9

					self.current = self.get_elem_id('INP_name')
					self.get_elem_by_id(self.current).set_on()
				elif parttype is 'lvm_lv':  # EXISTING LOGICAL VOLUME
					lv = self.parent.container['lvm']['vg'][ vgname ]['lv'][ lvname ]
					self.operation = 'edit'
					self.set_title(_('Edit LVM logical volume'))
					self.add_elem('TXT_0', textline(_('Volume name: %s') % lvname, self.pos_y+2, self.pos_x+5))
					self.add_elem('TXT_2', textline(_('Size: %d MiB') % B2MiB(lv['size']), self.pos_y+4, self.pos_x+5))
					self.add_elem('TXT_5', textline(_('Mount point:'), self.pos_y+6, self.pos_x+5))
					self.add_elem('INP_mpoint', input(lv['mpoint'], self.pos_y+6, self.pos_x+6+len(_('Mount point:')), 35))
					self.add_elem('TXT_3', textline(_('File system:'), self.pos_y+8, self.pos_x+5))

					try:
						file=open('modules/filesystem')
					except:
						file=open('/lib/univention-installer/modules/filesystem')
					dict={}
					filesystem_num=0
					filesystem=file.readlines()
					i=0
					for line in filesystem:
						fs=line.split(' ')
						if len(fs) > 1:
							entry = fs[1][:-1]
							if entry not in BLOCKED_FSTYPES_ON_LVM:   # disable e.g. swap on LVM
								dict[entry]=[entry,i]
								if entry == lv['fstype']:
									filesystem_num = i
								i += 1
					file.close()
					self.add_elem('SEL_fstype', select(dict, self.pos_y+9, self.pos_x+4, 15, 6, filesystem_num)) #4

					if lv['format']:
						self.add_elem('CB_format', checkbox({_('format'):'1'}, self.pos_y+14, self.pos_x+33, 14, 1, [0])) #7
					else:
						self.add_elem('CB_format', checkbox({_('format'):'1'}, self.pos_y+14, self.pos_x+33, 14, 1, [])) #7

					self.add_elem('BT_save', button("F12-"+_("Save"), self.pos_y+17, self.pos_x+(self.width)-4, align="right")) #8
					self.add_elem('BT_cancel', button("ESC-"+_("Cancel"), self.pos_y+17, self.pos_x+4, align='left')) #9
					self.current = self.get_elem_id('INP_mpoint')
					self.get_elem_by_id(self.current).set_on()

		class ask_lvm_vg(subwin):
			def input(self, key):
				if key in [ 10, 32 ]:
					if self.elements[4].get_status(): #Ok
						return self._ok()
				elif key == 260 and self.elements[4].active:
					#move left
					self.elements[4].set_off()
					self.elements[3].set_on()
					self.current=3
					self.draw()
				elif key == 261 and self.elements[3].active:
					#move right
					self.elements[3].set_off()
					self.elements[4].set_on()
					self.current=4
					self.draw()
				if self.elements[self.current].usable():
					self.elements[self.current].key_event(key)
				return 1

			def layout(self):
				message=_('UCS Installer supports only one LVM volume group.')
				self.elements.append(textline(message,self.pos_y+2,self.pos_x+(self.width/2),align="middle")) #0
				message=_('Please select volume group to use for installation.')
				self.elements.append(textline(message,self.pos_y+3,self.pos_x+(self.width/2),align="middle")) #1
				message=_('Volume Group:')
				self.elements.append(textline(message,self.pos_y+5,self.pos_x+2)) #2

				dict = {}
				line = 0
				for vg in self.parent.container['lvm']['vg'].keys():
					dict[ vg ] = [ vg, line ]
					line += 1
				default_line = 0
				self.elements.append(select(dict,self.pos_y+6,self.pos_x+3,self.width-6,4, default_line)) #3

				self.elements.append(button(_("OK"),self.pos_y+11,self.pos_x+(self.width/2)-7,15)) #4
				self.current=3
				self.elements[3].set_on()
			def _ok(self):
				self.parent.parent.set_lvm(True, vgname = self.elements[3].result()[0] )
				return 0

		class verify(subwin):
			def input(self, key):
				if key in [ 10, 32 ]:
					if self.elements[2].get_status(): #Yes
						return self._ok()
					elif self.elements[3].get_status(): #No
						return self._false()
				elif key == 260 and self.elements[3].active:
					#move left
					self.elements[3].set_off()
					self.elements[2].set_on()
					self.current=2
					self.draw()
				elif key == 261 and self.elements[2].active:
					#move right
					self.elements[2].set_off()
					self.elements[3].set_on()
					self.current=3
					self.draw()
				return 1
			def layout(self):
				self.parent.parent.print_history()
				message=_('Do you really want to write all changes?')
				self.elements.append(textline(message,self.pos_y+2,self.pos_x+(self.width/2),align="middle")) #0
				message=_('This may destroy all data on modified discs!')
				self.elements.append(textline(message,self.pos_y+4,self.pos_x+(self.width/2),align="middle")) #1

				self.elements.append(button(_("Yes"),self.pos_y+7,self.pos_x+5,15)) #2
				self.elements.append(button(_("No"),self.pos_y+7,self.pos_x+35,15)) #3
				self.current=3
				self.elements[3].set_on()
			def _ok(self):
				if not self.parent.write_devices_check():
					return 1  # do not return 0 ==> will close self.sub, but write_devices_check replaced self.sub with new msg win
				return 0
			def _false(self):
				return 0

		class verify_exit(verify):
			def _ok(self):
				if self.parent.write_devices_check():
					return 'next'
				return 1  # do not return 0 ==> will close self.sub, but write_devices_check replaced self.sub with new msg win

			def _false(self):
				return 0

		class no_disk(subwin):
			def input(self, key):
				if key in [ 10, 32 ]:
					if self.elements[2].get_status(): #Yes
						return self._ok()
				return 1
			def layout(self):
				message=_('No disk detected!')
				self.elements.append(textline(message,self.pos_y+2,self.pos_x+(self.width/2),align="middle")) #0
				message=_('Please try to load the suitable module and rescan!')
				self.elements.append(textline(message,self.pos_y+4,self.pos_x+(self.width/2),align="middle")) #1

				self.elements.append(button(_("Ok"),self.pos_y+7,self.pos_x+(self.width/2),15,align="middle")) #2
				self.current=3
				self.elements[3].set_on()
			def _ok(self):
				if not self.parent.write_devices_check():
					return 1  # do not return 0 ==> will close self.sub, but write_devices_check replaced self.sub with new msg win
				return 0

		class wrong_rootfs(subwin):
			def layout(self):
				message=_('Wrong file system type for mount point "/" !')
				self.elements.append(textline(message,self.pos_y+2,self.pos_x+(self.width/2),align="middle")) #0
				message=_('Please select another file system.')
				self.elements.append(textline(message,self.pos_y+4,self.pos_x+(self.width/2),align="middle")) #1

				self.elements.append(button(_("Ok"),self.pos_y+7,self.pos_x+(self.width/2),15,align="middle")) #2
				self.current=3
				self.elements[3].set_on()

			def _ok(self):
				return 0
