#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: partition configuration
#
# Copyright 2004-2012 Univention GmbH
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

#
# HINT:
#  - GUI code uses with factor 1024 for KB and MB ==> KiB and MiB
#  - Profile code uses (mostly) factor 1000 for KB and MB. Some parts (extent calculation for LVM) use factor 1024.
#  - imported and created profiles use factor 1000 for KB and MB !!!
# ==> look at MiB2MB and MB2MiB

from objects import *
from local import _
import os, re, string, curses
import inspect
import subprocess

# some autopartitioning config values
PARTSIZE_BOOT = 300          # size of /boot partition
PARTSIZE_SYSTEM_MIN = 4096   # minimum free space for system
PARTSIZE_SWAP_MIN = 192      # lower swap partition limit: 192MB
PARTSIZE_SWAP_MAX = 2048     # limit swap partition to 2048MB

# possible partition types
POSS_PARTTYPE_UNUSABLE = 0
POSS_PARTTYPE_PRIMARY = 1
POSS_PARTTYPE_LOGICAL = 2
POSS_PARTTYPE_BOTH = 3

# partition types
PARTTYPE_PRIMARY = 0
PARTTYPE_LOGICAL = 1
PARTTYPE_EXTENDED = 2
PARTTYPE_FREESPACE_PRIMARY = 4
PARTTYPE_FREESPACE_LOGICAL = 5
PARTTYPE_LVM_VG = 100
PARTTYPE_LVM_LV = 101
PARTTYPE_LVM_VG_FREE = 102

# file systems
EXPERIMENTAL_FSTYPES = ['btrfs']
ALLOWED_BOOT_FSTYPES = ['xfs','ext2','ext3','ext4']
ALLOWED_ROOT_FSTYPES = ['xfs','ext2','ext3','ext4','btrfs']

DISKLABEL_GPT = 'GPT'
DISKLABEL_UNKNOWN = 'UNKNOWN'


class object(content):
	def __init__(self,max_y,max_x,last=(1,1), file='/tmp/installer.log', cmdline={}):
		self.written=0
		content.__init__(self,max_y,max_x,last, file, cmdline)
		self.debug('init(): max_y=%s  max_x=%s' % (max_y, max_x))

	def MiB2MB(self, mb):
		return mb * 1024.0 * 1024.0 / 1000.0 / 1000.0

	def MB2MiB(self, mb):
		return mb * 1000.0 * 1000.0 / 1024.0 / 1024.0

	def MiB2CHSstr(self, disk, pos):
		return "%(cyls)d/%(heads)d/%(sectors)d" % self.MiB2CHS(pos, self.container['disk'][disk]['geometry'] )

	def MiB2CHS(self, pos, geometry):
		# pos: position as float in MiBytes
		# geometry: disk geometry as dict: { 'cyls': 123, 'heads': 255, 'sectors': 63 }
		# returns dict: { 'cyls': 123, 'heads': 255, 'sectors': 63, 'remainder': 0, 'valid': True }

		val = pos * 1024.0 * 1024.0  # convert MiB to Bytes
		result = {}
		size = {}

		size['sector'] = 512
		size['head'] = geometry['sectors'] * size['sector']
		size['cyl'] = geometry['heads'] * size['head']

		result['cyls'] = int(val / size['cyl'])
		val = val - (result['cyls'] * size['cyl'] )

		result['heads'] = int(val / size['head'] )
		val = val - (result['heads'] * size['head'] )

		result['sectors'] = int(val / size['sector'] )
		result['remainder'] = val - (result['sectors'] * size['sector'] )

		result['valid'] = (result['remainder'] == 0)

		return result

	def printPartitionsCHS(self):
		self.debug('PARTITIONS-CHS:')
		disk_list = self.container['disk'].keys()
		disk_list.sort()
		for diskitem in disk_list:
			disk = self.container['disk'][diskitem]
			part_list = disk['partitions'].keys()
			part_list.sort()
			for partitem in part_list:
				part = disk['partitions'][partitem]
				pos_start = self.getCHSandPosition( partitem, disk['geometry'], part['type'] )
				pos_end = self.getCHSandPosition( partitem + part['size'], disk['geometry'], part['type'] )
				self.debug('%s%s:  type=%d   start=%5d/%3d/%2d   end=%5d/%3d/%2d' % (diskitem, part['num'], part['type'],
																					 pos_start['cyls'], pos_start['heads'], pos_start['sectors'],
																					 pos_end['cyls'], pos_end['heads'], pos_end['sectors'] ) )

	def CHS2MiB(self, chs, geometry):
		size = {}
		size['sector'] = 512
		size['head'] = geometry['sectors'] * size['sector']
		size['cyl'] = geometry['heads'] * size['head']
		return (chs['cyls'] * size['cyl'] + chs['heads'] * size['head'] + chs['sectors'] * size['sector']) / 1024.0 / 1024.0

	def getCHSnextCyl(self, pos_end, geometry, parttype, correction = 'increase', force = True):
		pos = self.getCHSandPosition(pos_end, geometry, parttype, correction = correction, force = force)
		next_pos = (pos['position']*1024.0*1024.0 + 512) / 1024.0 / 1024.0
		next_pos = self.getCHSandPosition(next_pos, geometry, parttype, correction = 'decrease', force = True)
		return next_pos['position']

	def getCHSlastCyl(self, pos_end, geometry, parttype, correction = 'decrease', force = True):
		pos = self.getCHSandPosition(pos_end, geometry, parttype, correction = correction, force = force)
		next_pos = (pos['position']*1024.0*1024.0 - 512) / 1024.0 / 1024.0
		next_pos = self.getCHSandPosition(next_pos, geometry, parttype, correction = 'increase', force = True)
		return next_pos['position']

	def getCHSandPosition(self, pos, geometry, parttype, correction = False, force = False):
		# correction in [ 'increase', 'decrease' ]
		result = self.MiB2CHS(pos, geometry)
		result['position'] = pos

		# consistency check
		if result['cyls'] >= geometry['cyls']:
			self.debug('WARNING: CONSISTENCY CHECK FAILED: cyls is too large (%s) - setting to possible max (%s)' % (result['cyls'], geometry['cyls']-1))
			result['cyls'] = geometry['cyls'] - 1
		if result['heads'] >= geometry['heads']:
			self.debug('WARNING: CONSISTENCY CHECK FAILED: heads is too large (%s) - setting to possible max (%s)' % (result['heads'], geometry['heads']-1))
			result['heads'] = geometry['heads'] - 1
		if result['sectors'] >= geometry['sectors']:
			self.debug('WARNING: CONSISTENCY CHECK FAILED: sectors is too large (%s) - setting to possible max (%s)' % (result['sectors'], geometry['sectors']-1))
			result['sectors'] = geometry['sectors'] - 1

		# force increase/decrease
		if force:
			result['valid'] = False

		# correct chs values
		if not result['valid'] and correction:
			if correction == 'decrease':
				result['remainder'] = 0
				result['sectors'] = 0
				result['heads'] = 0
				# logical partitions always start at head +1, primary and extended partitions start at head 0
				if parttype == PARTTYPE_LOGICAL:
					result['heads'] += 1
				# first partition always starts at head 1 otherwise 0
				if result['cyls'] == 0:
					result['heads'] += 1
				# calculate new position
				result['position'] = self.CHS2MiB( result, geometry )
				result['valid'] = True
			elif correction == 'increase':
				result['remainder'] = 0
				result['sectors'] = geometry['sectors'] - 1
				result['heads'] = geometry['heads'] - 1
				# calculate new position
				result['position'] = self.CHS2MiB( result, geometry )
				result['valid'] = True
		return result

#geometry = {'cyls': 32635, 'heads': 255, 'sectors': 63 }
#print getCHSandPosition(0/1024.0/1024.0, geometry, PARTTYPE_PRIMARY, decrease = True, force = True)

	def checkname(self):
		return ['devices']

	def debug(self, txt):
		info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
		line = info[1]
		content.debug(self, 'PARTITION-MBR:%d: %s' % (line,txt))

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
		self.debug('checking free space for autopart...')
		disklist = {}
		disksizeall = 0.0
		for diskname, disk in self.container['disk'].items():
			disksize = 0.0
			for partname, part in self.container['disk'][diskname]['partitions'].items():
				disksize += part['size']
			disklist[diskname] = disksize
			disksizeall += disksize
		self.debug('disklist=%s' % disklist)
		if disksizeall < PARTSIZE_BOOT + PARTSIZE_SYSTEM_MIN + PARTSIZE_SWAP_MIN:
			result = _('Not enough space for autopartitioning: sum of disk sizes=%(disksizeall)s  required=%(required)s') % { 'disksizeall': disksizeall,
																															  'required': (PARTSIZE_BOOT + PARTSIZE_SYSTEM_MIN + PARTSIZE_SWAP_MIN) }
			self.debug( result)
			return result

		added_boot = False
		added_swap = False
		disklist_sorted = disklist.keys()
		disklist_sorted.sort()
		for diskname in disklist_sorted:
			disksize = disklist[diskname]
			if disksize > PARTSIZE_BOOT and not added_boot:
				disksize -= PARTSIZE_BOOT
				added_boot = True
			if disksize > PARTSIZE_SWAP_MIN and not added_swap:
				disksize -= PARTSIZE_SWAP_MIN
				added_swap = True
		if not added_swap or not added_boot:
			result = _('cannot autopart disk: /boot or swap does not fit on harddisk (required=%s)') % max(PARTSIZE_BOOT, PARTSIZE_SWAP_MIN)
			self.debug( result )
			self.debug('cannot autopart disk: bootsize=%s swapsize=%s disklist=%s' % (PARTSIZE_BOOT, PARTSIZE_SWAP_MIN, disklist))
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
		mpoint_list = []
		for key in self.container['profile']['create'].keys():
			for minor in self.container['profile']['create'][key].keys():
				fstype=self.container['profile']['create'][key][minor]['fstype'].strip()
				mpoint=self.container['profile']['create'][key][minor]['mpoint'].strip()
				self.debug('profile_complete: %s: mpoint=%s  fstype=%s' % (key, mpoint, fstype))
				if len(mpoint) and mpoint in mpoint_list:
					self.message="Double mountpoint '%s'" % mpoint
					return False
				mpoint_list.append(mpoint)

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
			if self.all_results['auto_part'] in [ 'full_disk', 'full_disk_usb' ]:
				result = self.check_space_for_autopart()
				if result:
					self.message = result
					return False
		return True

	def get_real_partition_device_name(self, device, number):
		match=0
		dev_match=0
		#/dev/cXdX
		regex = re.compile(".*c[0-9]d[0-9]*")
		match = re.search(regex,device)
		if match:
			regex = re.compile(".*c[0-9]*d[0-9]*")
			dev_match=re.search(regex,match.group())

		if dev_match:
			return '%sp%s' % (dev_match.group(),number)
		else:
			return '%s%d' % (device,number)

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
				parttype=self.container['profile']['create'][key][minor]['type']
				format=self.container['profile']['create'][key][minor]['format']
				fstype=self.container['profile']['create'][key][minor]['fstype']
				start=self.container['profile']['create'][key][minor]['start']
				end=self.container['profile']['create'][key][minor]['end']
				mpoint=self.container['profile']['create'][key][minor]['mpoint']
				flag=self.container['profile']['create'][key][minor]['flag']
				dev="%s"%self.get_real_partition_device_name(key,minor)

				tmpresult.append( ("PHY", dev, parttype, format, fstype, start, end, mpoint, flag) )

		for lvname,lv in self.container['profile']['lvmlv']['create'].items():
			device = '/dev/%s/%s' % (lv['vg'], lvname)
			tmpresult.append( ("LVM", device, 'LVMLV', lv['format'], lv['fstype'], lv['start'], lv['end'], lv['mpoint'], lv['flag']) )

		i = 0
		tmpresult.sort(lambda x,y: cmp(x[7], y[7]))  # sort by mountpoint
		self.debug('run_profiled: tmpresult=%s' % tmpresult)
		for (entrytype, device, parttype, format, fstype, start, end, mpoint, flag) in tmpresult:
			if type(start) == type(0) or type(start)==type(0.0):
				start = self.MiB2MB(start)
			if type(end) == type(0) or type(end)==type(0.0):
				end = self.MiB2MB(end)
			if mpoint == '':
				mpoint = 'None'
			if fstype == '':
				fstype = 'None'
			self.container['result'][ 'dev_%d' % i ] =  "%s %s %s %s %s %sM %sM %s %s" % (entrytype, device, parttype, format, fstype, start, end, mpoint, flag)

			i += 1

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

	def incomplete(self):
		self.debug('incomplete')
		root_device=0
		root_fs=0
		boot_fs=None
		root_fs_type=None
		boot_fs_type=None
		bootable_cnt=0
		mpoint_temp=[]
		for disk in self.container['disk'].keys():
			for part in self.container['disk'][disk]['partitions']:
				if self.container['disk'][disk]['partitions'][part]['num'] > 0 : # only valid partitions

					if 'boot' in self.container['disk'][disk]['partitions'][part]['flag']:
						bootable_cnt += 1

					if len(self.container['disk'][disk]['partitions'][part]['mpoint'].strip()):
						if self.container['disk'][disk]['partitions'][part]['mpoint'] in mpoint_temp:
							return _("Double mount point '%s'") % self.container['disk'][disk]['partitions'][part]['mpoint']
						mpoint_temp.append(self.container['disk'][disk]['partitions'][part]['mpoint'])

					if self.container['disk'][disk]['partitions'][part]['mpoint'] == '/':
						root_fs_type=self.container['disk'][disk]['partitions'][part]['fstype']
						if not self.container['disk'][disk]['partitions'][part]['fstype'] in ALLOWED_ROOT_FSTYPES:
							root_fs=self.container['disk'][disk]['partitions'][part]['fstype']
						root_device=1

					if self.container['disk'][disk]['partitions'][part]['mpoint'] == '/boot':
						boot_fs_type=self.container['disk'][disk]['partitions'][part]['fstype']
						if not self.container['disk'][disk]['partitions'][part]['fstype'] in ALLOWED_BOOT_FSTYPES:
							boot_fs=self.container['disk'][disk]['partitions'][part]['fstype']

		# check LVM Logical Volumes if LVM is enabled
		if self.container['lvm']['enabled'] and self.container['lvm']['vg'].has_key( self.container['lvm']['ucsvgname'] ):
			vg = self.container['lvm']['vg'][ self.container['lvm']['ucsvgname'] ]
			for lvname in vg['lv'].keys():
				lv = vg['lv'][lvname]
				mpoint = lv['mpoint'].strip()
				if len(mpoint):
					if mpoint in mpoint_temp:
						return _("Double mount point '%s'") % mpoint
				mpoint_temp.append(mpoint)
				if mpoint == '/':
					if not lv['fstype'] in ALLOWED_ROOT_FSTYPES:
						root_fs = lv['fstype']
					root_device=1

		if not bootable_cnt:
			return _('One partition must be flagged as bootable. This should usually be /boot.')

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

		if len(self.container['history']) or self.test_changes():
			self.sub.sub=self.sub.verify_exit(self.sub,self.sub.minY+(self.sub.maxHeight/3)+2,self.sub.minX+(self.sub.maxWidth/8),self.sub.maxWidth,self.sub.maxHeight-18)
			self.sub.sub.draw()
			return 1

		if root_fs_type == 'btrfs' and boot_fs_type in [ None, 'btrfs' ]:
			return _('Unbootable config! / on btrfs needs /boot-partition with other than btrfs!')

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

	def start(self):
		# self.container['problemdisk'][<devicename>] = set([DISKLABEL_GPT, DISKLABEL_UNKNOWN, ...])

		self.container={}
		self.container['min_size']=float(1)
		self.container['debug']=''
		self.container['module_disabled'] = False
		self.container['profile']={}
		disks, problemdisks = self.read_devices()
		self.container['disk']=disks
		self.container['problemdisk']=problemdisks
		self.container['history']=[]
		self.container['temp']={}
		self.container['selected']=1
		self.container['autopartition'] = None
		self.container['autopart_usbstorage'] = None
		self.container['lvm'] = {}
		self.container['lvm']['enabled'] = None
		self.container['lvm']['lvm1available'] = False
		self.container['lvm']['warnedlvm1'] = False
		self.container['lvm']['ucsvgname'] = None
		self.container['lvm']['lvmconfigread'] = False
		self.container['disk_checked'] = False
		self.container['partitiontable_checked'] = False

	def profile_autopart(self, disklist_blacklist = [], part_delete = 'all' ):
		self.debug('PROFILE BASED AUTOPARTITIONING: full_disk')

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
				sysmem = int(match.group(1)) / 1024
		self.debug('AUTOPART-PROFILE: sysmem=%s' % sysmem)

		# calc disk sizes
		disklist = {}
		disksizeall = 0.0
		for diskname, disk in self.container['disk'].items():
			if diskname in disklist_blacklist:
				self.debug('AUTOPART-PROFILE: disk %s is blacklisted' % diskname)
			else:
				disksize = 0.0
				for partname, part in self.container['disk'][diskname]['partitions'].items():
					disksize += part['size']
				disklist[diskname] = disksize
				disksizeall += disksize
		self.debug('AUTOPART-PROFILE: disklist=%s' % disklist)

		# place partitions
		dev_i = 0
		added_boot = False
		added_swap = False
		swapsize_result = 0
		disklist_sorted = disklist.keys()
		disklist_sorted.sort()
		for diskname in disklist_sorted:
			disksize = disklist[diskname]
			sizeused = 0.01
			partnum = 1
			# add /boot-partition
			if disksize > PARTSIZE_BOOT and not added_boot:
				start = sizeused
				end = sizeused + PARTSIZE_BOOT
				self.all_results['dev_%d' % dev_i] = 'PHY %s%d 0 1 ext4 %sM %sM /boot boot' % (diskname, partnum, start, end)
				dev_i += 1
				partnum += 1
				disksize -= PARTSIZE_BOOT
				sizeused += PARTSIZE_BOOT
				added_boot = True

			if disksize > PARTSIZE_SWAP_MIN and not added_swap:
				swapsize = 2 * sysmem
				if swapsize > PARTSIZE_SWAP_MAX:
					swapsize = PARTSIZE_SWAP_MAX
				while (disksize < swapsize) and (disksizeall < PARTSIZE_BOOT + PARTSIZE_SYSTEM_MIN + swapsize):
					swapsize -= 16
					if swapsize < PARTSIZE_SWAP_MIN:
						swapsize = PARTSIZE_SWAP_MIN

				start = sizeused + 0.01
				end = sizeused + swapsize
				self.all_results['dev_%d' % dev_i] = 'PHY %s%d 0 1 linux-swap %sM %sM None None' % (diskname, partnum, start, end)
				dev_i += 1
				partnum += 1
				disksize -= swapsize
				sizeused += swapsize
				swapsize_result = swapsize
				added_swap = True

			# use rest of disk als LVM PV
			self.all_results['dev_%d' % dev_i] = 'PHY %s%d 0 1 None %sM 0 None lvm' % (diskname, partnum, sizeused+0.01)
			dev_i += 1

		rootsize = (disksizeall - swapsize_result - PARTSIZE_BOOT) * 0.95
		self.all_results['dev_%d' % dev_i] = 'LVM /dev/vg_ucs/rootfs LVMLV 0 ext4 0 %sM / None' % rootsize
		dev_i += 1

#dev_0="LVM /dev/vg_ucs/rootfs LVMLV 0 ext3 0M 7000M / None"
#dev_1="PHY /dev/sdb2 0 0 ext3 500.01M 596.01M /boot None"
#dev_2="PHY /dev/sda1 0 0 None 0.01M 0 None lvm,boot"
#dev_3="PHY /dev/sdb3 0 0 None 596.01M 0 None lvm,boot"
#dev_4="PHY /dev/sdb1 0 0 linux-swap 0.01M 500.01M None None"
#dev_5="LVM /dev/vg_ucs/homefs LVMLV 0 ext3 0M 2000M /home None"

	def read_profile(self):
		self.debug('read_profile')
		self.container['result']={}
		self.container['profile']['delete']={}
		self.container['profile']['create']={}
		self.container['profile']['lvmlv']={}
		self.container['profile']['lvmlv']['create']={}
		self.container['profile']['lvmlv']['delete']={}
		auto_part = False

		# disable module if partition table type in profile does not match 'MSDOS' or 'MBR'
		if self.all_results.get('partitiontable_type','msdos').lower() not in ('msdos','mbr'):
			self.container['module_disabled'] = True
			return

		# create disk list with usb storage devices
		disklist_usbstorage = self.get_usb_storage_device_list()

		if 'create_partitiontable' in self.all_results:
			diskchanged = False
			for dev in re.split('[\s,]+', self.all_results.get('create_partitiontable','')):
				dev = dev.strip()
				if dev:
					self.install_fresh_mbr(dev)
					diskchanged = True
			if diskchanged:
				# rereading partition tables
				self.debug('read_profile: rereading partition tables after altering some of them')
				disks, problemdisks = self.read_devices()
				self.container['disk'] = disks
				self.container['problemdisk'] = problemdisks

		if 'auto_part' in self.all_results.keys():
			self.debug('read_profile: auto_part key found: %s' % self.all_results['auto_part'])
			if self.all_results['auto_part'] in [ 'full_disk' ]:
				auto_part = True
				self.profile_autopart( disklist_blacklist = disklist_usbstorage, part_delete = 'all' )
			elif self.all_results['auto_part'] in [ 'full_disk_usb' ]:
				auto_part = True
				self.profile_autopart( disklist_blacklist = [], part_delete = 'all_usb' )
		else:
			self.debug('read_profile: no auto_part key found')

		for key in self.all_results.keys():
			self.debug('read_profile: key=%s' % key)
			delete_all_lvmlv = False
			if key == 'part_delete':
				delete=self.all_results['part_delete'].replace("'","").split(' ')
				self.debug('part_delete=%s' % str(delete))
				self.debug('disklist_usbstorage=%s' % str(disklist_usbstorage))
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
						flag = ''
						if len(parms) < 6 or parms[5] == 'None' or parms[5] == 'linux-swap':
							mpoint = ''
						else:
							mpoint = parms[5]
						if len(parms) >= 7:
							flag = parms[-1]
							if flag.lower() == 'none':
								flag = ''
						if parms[0] == 'only_mount':
							parms[1]=0

						temp={	'type':parms[0],
							'fstype':parms[2].lower(),
							'start': parms[3],
							'end': parms[4],
							'mpoint':mpoint,
							'format':parms[1],
							'flag': flag,
							}

						self.debug('Added to create physical container: %s' % temp)
						self.container['profile']['create'][disk][partnum]=temp
					else:
						self.debug('Syntax error for key[%s]' % key)
						pass
				elif parttype == 'LVM':
					if parms[0] == 'only_mount':
						parms[1]=0
					vgname, lvname = device.split('/')[-2:]         # /dev/VolumeGroup/LogicalVolume
					temp={	'vg': vgname,
							'type':parms[0],
							'format':parms[1],
							'fstype':parms[2].lower(),
							'start':parms[3],
							'end':parms[4],
							'mpoint':parms[5],
							'flag':parms[6],
							}
					self.debug('Added to create lvm volume: %s' % temp)
					self.container['profile']['lvmlv']['create'][lvname]=temp
				else:
					self.debug('%s devices in profile unsupported' % parttype)

	def get_device_name(self, partition):
		match=0
		dev_match=0
		self.debug('Try to get the device name for %s' % partition)
		# /dev/hdX
		regex = re.compile(".*hd[a-z]([0-9]*)$")
		match = re.search(regex,partition)
		if match:
			regex = re.compile(".*hd[a-z]*")
			dev_match=re.search(regex,match.group())
		#/dev/sdX
		regex = re.compile(".*sd[a-z]([0-9]*)$")
		match = re.search(regex,partition)
		if match:
			regex = re.compile(".*sd[a-z]*")
			dev_match=re.search(regex,match.group())
		#/dev/mdX
		regex = re.compile(".*md([0-9]*)$")
		match = re.search(regex,partition)
		if match:
			regex = re.compile(".*md*")
			dev_match=re.search(regex,match.group())
		#/dev/xdX
		regex = re.compile(".*xd[a-z]([0-9]*)$")
		match = re.search(regex,partition)
		if match:
			regex = re.compile(".*xd[a-z]*")
			dev_match=re.search(regex,match.group())
		#/dev/adX
		regex = re.compile(".*ad[a-z]([0-9]*)$")
		match = re.search(regex,partition)
		if match:
			regex = re.compile(".*ad[a-z]*")
			dev_match=re.search(regex,match.group())
		#/dev/edX
		regex = re.compile(".*ed[a-z]([0-9]*)$")
		match = re.search(regex,partition)
		if match:
			regex = re.compile(".*ed[a-z]*")
			dev_match=re.search(regex,match.group())
		#/dev/pdX
		regex = re.compile(".*pd[a-z]([0-9]*)$")
		match = re.search(regex,partition)
		if match:
			regex = re.compile(".*pd[a-z]*")
			dev_match=re.search(regex,match.group())
		#/dev/pfX
		regex = re.compile(".*pf[a-z]([0-9]*)$")
		match = re.search(regex,partition)
		if match:
			regex = re.compile(".*pf[a-z]*")
			dev_match=re.search(regex,match.group())
		#/dev/vdX
		regex = re.compile(".*vd[a-z]([0-9]*)$")
		match = re.search(regex,partition)
		if match:
			regex = re.compile(".*vd[a-z]*")
			dev_match=re.search(regex,match.group())
		#/dev/dasdX
		regex = re.compile(".*dasd[a-z]([0-9]*)$")
		match = re.search(regex,partition)
		if match:
			regex = re.compile(".*dasd[a-z]*")
			dev_match=re.search(regex,match.group())
		#/dev/dptiX
		regex = re.compile(".*dpti[a-z]([0-9]*)")
		match = re.search(regex,partition)
		if match:
			regex = re.compile(".*dpti[0-9]*")
			dev_match=re.search(regex,match.group())
		#/dev/cXdX
		regex = re.compile(".*c[0-9]d[0-9]*")
		match = re.search(regex,partition)
		if match:
			regex = re.compile(".*c[0-9]*d[0-9]*")
			dev_match=re.search(regex,match.group())
		#/dev/arX
		regex = re.compile(".*ar[0-9]*")
		match = re.search(regex,partition)
		if match:
			regex = re.compile(".*ar[0-9]*")
			dev_match=re.search(regex,match.group())

		if dev_match:
			return '%s' % dev_match.group()
		else:
			return partition

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

	def customsize2MiB(self, size):
		size = size.upper().strip()
		if size[-1] in [ 'K', 'M', 'G' ]:
			try:
				newsize = float(size.strip('KMG'))
			except:
				newsize = 0
			if size[-1] == 'K':
				result = newsize*1000.0/1024.0/1024.0
			elif size[-1] == 'M':
				result = newsize*1000.0*1000.0/1024.0/1024.0
			elif size[-1] == 'G':
				result = newsize*1000.0*1000.0*1000.0/1024.0/1024.0
		else:
			try:
				result = float(size)
			except:
				result = 0.0
		return result

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
			match=0
			dev_match=0
			#/dev/cXdX
			regex = re.compile(".*c[0-9]d[0-9]*")
			match = re.search(regex,device)
			if match:
				regex = re.compile(".*c[0-9]*d[0-9]*")
				dev_match=re.search(regex,match.group())

			if dev_match:
				return '%sp%s' % (dev_match.group(),number)
			else:
				return '%s%s' % (device,number)

		def run_cmd(self, command, debug=True):
			self.parent.debug('wait for udev to create device file')
			os.system("udevadm settle || true")
			self.parent.debug('(profile) run command: %s' % command)
			p=os.popen(command)
			output = p.read()
			p.close()
			if debug:
				self.parent.debug('\n=> %s' % output.replace('\n','\n=> '))
			return output

		def function(self):
			if self.action == 'prof_read_lvm':
				self.parent.debug('prof_read_lvm')
				self.parent.read_lvm()

			elif self.action == 'prof_delete_lvm':
				self.parent.debug('prof_delete_lvm')
				for dev,entry in self.parent.container['profile']['lvmlv']['delete'].items():
					device = entry['vg']
					if entry['lv']:
						device += '/%s' % entry['lv']
					self.run_cmd('/sbin/lvremove -f %s 2>&1' % device)

				# cleanup all known LVM volume groups
				for vgname, vg in self.parent.container['lvm']['vg'].items():
					self.run_cmd('/sbin/vgreduce -a --removemissing %s 2>&1' % vgname)
#				self.run_cmd('/sbin/vgscan 2>&1')

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
								testoutput = self.run_cmd( '/sbin/vgreduce -t %s %s 2>&1' % (pv['vg'], device) )
								if "Can't remove final physical volume" in testoutput:
									self.run_cmd( '/sbin/vgremove %s 2>&1' % pv['vg'] )
								else:
									self.run_cmd( '/sbin/vgreduce %s %s 2>&1' % (pv['vg'], device) )
								self.run_cmd( '/sbin/pvremove -ff %s 2>&1' % device )

						self.run_cmd('/sbin/parted --script %s p rm %s 2>&1'%(disk,num))

				# cleanup all known LVM volume groups
#				self.run_cmd('/sbin/pvscan 2>&1')
#				self.run_cmd('/sbin/vgscan 2>&1')
				for vgname, vg in self.parent.container['lvm']['vg'].items():
					self.run_cmd('/sbin/vgreduce -a --removemissing %s 2>&1' % vgname)

			elif self.action == 'prof_write':
				vgcreated = False
				self.parent.debug('prof_write')
				for disk in self.parent.container['profile']['create'].keys():
					num_list=self.parent.container['profile']['create'][disk].keys()
					num_list.sort()
					for num in num_list:
						type = self.parent.container['profile']['create'][disk][num]['type']
						flaglist = self.parent.container['profile']['create'][disk][num]['flag'].split(',')
						fstype = self.parent.container['profile']['create'][disk][num]['fstype']
						start = self.parent.container['profile']['create'][disk][num]['start']
						end = self.parent.container['profile']['create'][disk][num]['end']

						# do not create partitions if only_mount is set
						if type == "only_mount":
							self.parent.debug('will not create partition %s%s due type == %s' % (disk, num, type))
							continue

						if not fstype or fstype.lower() in [ 'none' ]:
							self.run_cmd('/sbin/PartedCreate -d %s -t %s -s %s -e %s 2>&1' % (disk, type, start, end))
						else:
							self.run_cmd('/sbin/PartedCreate -d %s -t %s -f %s -s %s -e %s 2>&1' % (disk, type, fstype, start, end))
						if 'boot' in flaglist:
							self.parent.debug('%s%s: boot flag' % (disk, num))
							self.run_cmd('/sbin/parted -s %s set %s boot on' % (disk, num))
						if 'lvm' in flaglist:
							device = self.get_real_partition_device_name(disk,num)
							self.parent.debug('%s: lvm flag' % device)
							ucsvgname = self.parent.container['lvm']['ucsvgname']
							self.run_cmd('/sbin/pvcreate %s 2>&1' % device)
							if not vgcreated:
								self.run_cmd('/sbin/vgcreate --physicalextentsize %sk %s %s 2>&1' % (self.parent.container['lvm']['vg'][ ucsvgname ]['PEsize'], ucsvgname, device))
#								self.run_cmd('/sbin/vgscan 2>&1')
								vgcreated = True
							self.run_cmd('/sbin/vgextend %s %s 2>&1' % (ucsvgname, device))
				# cleanup all known LVM volume groups
##				self.run_cmd('/sbin/pvscan 2>&1')
##				self.run_cmd('/sbin/vgscan 2>&1')

			elif self.action == 'prof_write_lvm':
				self.parent.debug('prof_write_lvm')
				for lvname, lv in self.parent.container['profile']['lvmlv']['create'].items():
					vg = self.parent.container['lvm']['vg'][ lv['vg'] ]
					size = self.parent.customsize2MiB( lv['end'] ) - self.parent.customsize2MiB( lv['start'] )
					self.parent.debug('creating LV: start=%s  end=%s  size=%s' % (lv['start'], lv['end'], size))
					currentLE = int(round(size * 1024.0 / vg['PEsize'] + 0.5))
					self.run_cmd('/sbin/lvcreate -l %d --name "%s" "%s" 2>&1' % (currentLE, lvname, lv['vg'] ))
#				self.run_cmd('/sbin/lvscan 2>&1')

			elif self.action == 'prof_format':
				self.parent.debug('prof_format')
				for disk in self.parent.container['profile']['create'].keys():
					num_list=self.parent.container['profile']['create'][disk].keys()
					num_list.sort()
					for num in num_list:
						type = self.parent.container['profile']['create'][disk][num]['type']
						fstype = self.parent.container['profile']['create'][disk][num]['fstype']
						format = self.parent.container['profile']['create'][disk][num]['format']

						# do not create fs on partitions if format is 0
						if format in [ 0, "0" ] and not self.parent.all_results.get('part_delete', "") == "all":
							self.parent.debug('will not create fs on partition %s%s due format == %s' % (disk, num, format))
							continue

						mkfs_cmd = None
						fstype = fstype.lower()
						if fstype in ['ext2','ext3','vfat','msdos', 'ext4', 'btrfs']:
							mkfs_cmd='/sbin/mkfs.%s %s' % (fstype,self.get_real_partition_device_name(disk,num))
						elif fstype == 'xfs':
							mkfs_cmd='/sbin/mkfs.xfs -f %s' % self.get_real_partition_device_name(disk,num)
						elif fstype == 'linux-swap':
							mkfs_cmd='/bin/mkswap %s' % self.get_real_partition_device_name(disk,num)
						if mkfs_cmd:
							self.run_cmd('%s 2>&1' % mkfs_cmd)
						else:
							self.parent.debug('unknown fstype (%s) for %s' % (fstype, self.get_real_partition_device_name(disk,num)))

				for lvname, lv in self.parent.container['profile']['lvmlv']['create'].items():
					device = '/dev/%s/%s' % (lv['vg'], lvname)
					fstype = lv['fstype'].lower()
					format = lv['format']

					# do not create fs on partitions if format is 0
					if format in [ 0, "0" ] and not self.parent.all_results.get('part_delete', "") == "all":
						self.parent.debug('will not create fs on %s due format == %s' % (lvname, format))
						continue

					mkfs_cmd = None
					fstype = fstype.lower()
					if fstype in ['ext2','ext3','vfat','msdos', 'ext4', 'btrfs']:
						mkfs_cmd='/sbin/mkfs.%s %s' % (fstype, device)
					elif fstype == 'xfs':
						mkfs_cmd='/sbin/mkfs.xfs -f %s' % device
					elif fstype == 'linux-swap':
						mkfs_cmd='/bin/mkswap %s' % device
					if mkfs_cmd:
						self.run_cmd('%s 2>&1' % mkfs_cmd)
					else:
						self.parent.debug('unknown fstype (%s) for %s' % (fstype, device))

			self.stop()

	def read_lvm_pv(self):
#		p = os.popen('pvscan 2> /dev/null')
#		p.close()
		p = os.popen('pvdisplay -c 2> /dev/null')
		content=p.read()
		p.close()

		#  /dev/sdb4:vg_member50:3907584:-1:8:8:-1:4096:477:477:0:dEMYyK-EdEu-uXvk-OS39-IeBe-whg1-c8fTCF

		for line in content.splitlines():
			item = line.strip().split(':')

			self.container['lvm']['pv'][ item[0] ] = { 'touched': 0,
													   'vg': item[1],
													   'PEsize': int( item[7] ), # physical extent size in kilobytes
													   'totalPE': int( item[8] ),
													   'freePE': int( item[9] ),
													   'allocPE': int( item[10] ),
													   }

	def read_lvm_vg(self):
#		p = os.popen('vgscan 2> /dev/null')
#		p.close()

		p = os.popen('vgdisplay 2> /dev/null | grep " Format "')
		content=p.read()
		p.close()
		if 'lvm1' in content:
			self.container['lvm']['lvm1available'] = True

		p = os.popen('vgdisplay -c 2> /dev/null')
		content=p.read()
		p.close()

		#  vg_member50:r/w:772:-1:0:0:0:-1:0:2:2:2940928:4096:718:8:710:B2oHiE-D06t-g4eM-lblN-ELf2-KAYH-ef3CxX

		# get available VGs
		for line in content.splitlines():
			item = line.strip().split(':')
			self.container['lvm']['vg'][ item[0] ] = { 'touched': 0,
													   'PEsize': int(item[12]), # physical extent size in kilobytes
													   'totalPE': int(item[13]),
													   'allocPE': int(item[14]),
													   'freePE': int(item[15]),
													   'size': int(item[12])*int(item[13])/1024.0,
													   'created': 1,
													   'lv': {}
													   }

	def read_lvm_lv(self):
#		p = os.popen('lvscan 2> /dev/null')
#		p.close()

		p = os.popen('lvdisplay -c 2> /dev/null')
		content=p.read()
		p.close()

		#  /dev/ucsvg/ucsvg-vol1:ucsvg:3:1:-1:0:819200:100:-1:0:0:254:0
		#  /dev/ucsvg/ucsvg-vol2:ucsvg:3:1:-1:0:311296:38:-1:0:0:254:1
		#  /dev/ucsvg/ucsvg_vol3:ucsvg:3:1:-1:0:204800:25:-1:0:0:254:2

		# get available LVs
		for line in content.splitlines():
			item = line.strip().split(':')

			vg = item[1]
			pesize = self.container['lvm']['vg'][ vg ]['PEsize']
			lvname = item[0].split('/')[-1]

			p = os.popen('/bin/file -Ls %s' % item[0])
			data = p.read()
			p.close()
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
				fstype = 'linux-swap'
			elif 'BTRFS Filesystem' in data:
				fstype = 'btrfs'
			elif 'FAT (16 bit)' in data:
				fstype = 'fat16'
			elif 'FAT (32 bit)' in data:
				fstype = 'fat32'

			self.container['lvm']['vg'][ item[1] ]['lv'][ lvname ] = {  'dev': item[0],
																		'vg': item[1],
																		'touched': 0,
																		'PEsize': int(pesize), # physical extent size in kilobytes
																		'currentLE': int(item[7]),
																		'format': 0,
																		'size': int(item[7])*int(pesize)/1024.0,
																		'fstype': fstype,
																		'flag': '',
																		'mpoint': '',
																		}

	def enable_all_vg(self):
		command = '/sbin/vgchange -ay 2>&1'
		self.debug('run command: %s' % command)
		p=os.popen(command)
		output = p.read()
		p.close()
		self.debug('\n=> %s' % output.replace('\n','\n=> '))

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
																					  'PEsize': 4096, # physical extent size in kilobytes
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
			file=open('/lib/univention-installer/partitions')
			self.debug('Reading from /lib/univention-installer/partitions')
		else:
			file=open('/proc/partitions')
			self.debug('Reading from /proc/partitions')
		proc_partitions=file.readlines()
		devices=[]
		for line in proc_partitions[2:]:
			cols=line.split()
			if len(cols) >= 4  and cols[0] != 'major':
				match=0
				dev_match=0
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

		uniqlist = []
		for dev in devices:
			if not dev in uniqlist:
				uniqlist.append(dev)
		devices = uniqlist
		devices.sort()
		self.debug('devices=%s' % devices)

		diskList={}
		diskProblemList={}
		devices_remove={}

		_re_warning=re.compile('^Warning: Unable to open .*')
		_re_error=re.compile('^Error: .* unrecognised disk label')
		_re_disklabel=re.compile('^Partition Table: (.*)$', re.I | re.M)  # case insensitive & ^ matches on \n

		for dev in devices:
			dev=dev.strip()
			bn = os.path.basename(dev)
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

			p = os.popen('/sbin/parted -s %s unit B print 2>&1 | grep [a-z]'% dev)

			first_line=p.readline().strip()
			self.debug('first line: [%s]' % first_line)
			if _re_warning.match(first_line):
				self.debug('Firstline starts with warning')
				self.debug('Remove device: %s' % dev)
				devices_remove[dev] = 1
				continue
			elif _re_error.match(first_line):
				self.debug('Firstline starts with error')
				self.debug('Device %s contains unknown disk label' % dev)
				self.debug('Removing device %s' % dev)
				diskProblemList[dev] = diskProblemList.get(dev, set()) | set([DISKLABEL_UNKNOWN]) # add new problem to list
				devices_remove[dev] = 1
				continue

			# get CHS geometry
			geometry = None
			pchs = os.popen('/sbin/parted -s %s unit chs print 2>&1'% dev)
			for line in pchs.readlines():
				if line.startswith('BIOS cylinder,head,sector geometry: '):
					line = line[36:]
					chs = line.split('. ')[0]
					chs = chs.split(',')
					if len(chs) != 3:
						self.debug('ERROR: cannot get drive geometry: bad line: %s' % line)
						self.debug('ERROR: removing drive %s' % dev)
						del diskList[dev]
					else:
						geometry = { 'cyls': int(chs[0]), 'heads': int(chs[1]), 'sectors': int(chs[2]) }
						self.debug('INFO: %s: BIOS CHS geometry = %s/%s/%s' % (dev, chs[0], chs[1], chs[2]))
			pchs.close()

			mb_size = 0
			extended=0
			primary=0
			logical=0
			partList={}
			last_end=float(0)
			_re_int=re.compile('^[0-9].*')
			for line in [ first_line ] + p.readlines():
				line=line.strip()

				# parse disk size
				if line.startswith('Disk '):
					mb_size = int(line.split(' ')[-1].split('B')[0].split(',')[0]) / 1024.0 / 1024.0
					tmpsize = self.getCHSandPosition(mb_size, geometry, PARTTYPE_PRIMARY, correction = 'increase', force = True)
					self.debug('DEBUG: mb_size = %f  tmpsize = %f  chs=%s/%s/%s' % (mb_size, tmpsize['position'],
																					tmpsize['cyls'], tmpsize['heads'], tmpsize['sectors']))
					mb_size = tmpsize['position']
					continue

				# check for GPT partition table
				match = _re_disklabel.match(line)
				if match and match.group(1).lower().strip() in 'gpt':
					self.debug('Device %s uses GPT' % dev)
					self.debug('Removing device %s' % dev)
					diskProblemList[dev] = diskProblemList.get(dev, set()) | set([DISKLABEL_GPT]) # add new problem to list
					devices_remove[dev] = 1
					continue

				if not _re_int.match(line):
					if _re_error.match(line):
						self.debug('Line starts with Error: [%s]' % line)
						self.debug('Removing device %s' % dev)
						devices_remove[dev] = 1
					continue

				if devices_remove.get(dev):
					continue

				cols=line.split()
				num=cols[0]
				part=dev+cols[0]
				start=float( int(cols[1].split('B')[0].replace(',','.')) / 1024.0 / 1024.0 )
				#
				end=float( int(cols[2].split('B')[0].replace(',','.')) / 1024.0 / 1024.0 )
				# EVIL EVIL EVIL START ==> FIXME TODO
				# start is used as identifier but extended and logical partition can have same start point
				while start in partList.keys():
					start += 0.00000001
				# EVIL EVIL EVIL END

				size=end-start
				type=cols[4]
				if type == 'extended':
					ptype=PARTTYPE_EXTENDED
					extended=1
					primary+=1
				elif type == 'primary':
					ptype=PARTTYPE_PRIMARY
					primary+=1
				elif type == 'logical':
					ptype=PARTTYPE_LOGICAL
					logical+=1
				else:
					self.debug('ERROR: parted returned no valid partition type')
					self.debug('ERROR: line = "%s"' % line)
					self.debug('Removing device %s' % dev)
					devices_remove[dev] = 1
					continue

				fstype=''
				flag=[]

				if len(cols) > 5:
					fstype=cols[5]
					#FIXME
					if fstype in ['boot','hidden','raid','lvm','lba','palo','prep','boot,','hidden,','raid,','lvm,','lba,','palo,','prep']:
						flag.append(fstype.strip(','))
						fstype=''


				for i in range(6,10):
					if len(cols) > i:
						flag.append(cols[i].strip(','))

				# add free space between partitions
				if ( start - last_end) > self.container['min_size']:
					if last_end == 0:
						free_start = self.getCHSandPosition( 0.5, geometry, PARTTYPE_FREESPACE_PRIMARY, correction = 'decrease', force = True )['position']
					else:
						free_start = self.getCHSnextCyl(last_end, geometry, PARTTYPE_FREESPACE_PRIMARY)
					free_end = self.getCHSlastCyl(start, geometry, PARTTYPE_FREESPACE_PRIMARY)
					if free_end - free_start > self.container['min_size']:
						partList[free_start] = self.generate_freespace(free_start,free_end)


				partList[start]={'type':ptype,
						'touched':0,
						'fstype':fstype,
						'size':size,
						'end':end,
						'num':int(num),
						'mpoint':'',
						'flag':flag,
						'format':0,
						'preexist': 1
						}
				if type == 'extended':
					last_end=start
				else:
					last_end=end
			#
			if ( mb_size - last_end) > self.container['min_size']:
				if last_end == 0:
					free_start = self.getCHSandPosition( 0.5, geometry, PARTTYPE_FREESPACE_PRIMARY, correction = 'decrease', force = True )['position']
				else:
					free_start = self.getCHSnextCyl(last_end, geometry, PARTTYPE_FREESPACE_PRIMARY)
				free_end = float(mb_size)
				partList[free_start]=self.generate_freespace(free_start,free_end)

			diskList[dev]={'partitions':partList,
					'primary':primary,
					'extended':extended,
					'logical':logical,
					'size':mb_size,
					'geometry': geometry,
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
		return diskList, diskProblemList

	def scan_extended_size(self):
		for disk in self.container['disk'].keys():
			part_list = self.container['disk'][disk]['partitions'].keys()
			part_list.sort()
			start=float(-1)
			end=float(-1)
			found=0
			found_extended=0
			for part in part_list:
				if self.container['disk'][disk]['partitions'][part]['type'] == PARTTYPE_LOGICAL:
					found=1
					if start < 0:
						start = part
					elif part < start:
						start = part
					if end < part+self.container['disk'][disk]['partitions'][part]['size']:
						end = part+self.container['disk'][disk]['partitions'][part]['size']
				elif self.container['disk'][disk]['partitions'][part]['type'] == PARTTYPE_EXTENDED:
					found_extended=1
					extended_start = part
					extended_end = part+self.container['disk'][disk]['partitions'][part]['size']
			if found and found_extended:
				self.debug('scan_extended_size: extended_start=%s  start=%s  diff=%s' % (extended_start,start,start - extended_start))
				self.debug('scan_extended_size: extended_end=%s  end=%s  diff=%s' % (extended_end,end, extended_end - end))
				if extended_start < start-float(0.1):
					self.container['temp'][disk]=[extended_start,start-float(0.1),end]
				elif extended_end > end+float(0.1):
					self.container['temp'][disk]=[extended_start,start+float(0.01),end]

	def generate_freespace(self,start,end):
		return {'type':PARTTYPE_FREESPACE_PRIMARY,
			'touched':0,
			'fstype':'---',
			'size':end-start,
			'end':end,
			'num':-1,
			'mpoint':'',
			'flag':[],
			'format':0
			}

	def use_mpoint(self,mpoint):
		for disk in self.container['disk']:
			for part in self.container['disk'][disk]['partitions']:
				if self.container['disk'][disk]['partitions'][part]['mpoint'] == mpoint:
					return 1
		return 0

	def get_device(self, disk, part):
		device="/dev/%s" % disk.replace('/dev/', '').replace('//', '/')
		regex = re.compile(".*c[0-9]d[0-9]*")
		match = re.search(regex,disk)
		if match: # got /dev/cciss/cXdXpX
			device += "p"
		device += "%s"%self.container['disk'][disk]['partitions'][part]['num']
		return device

	def result(self):
		if self.container['module_disabled']:
			self.debug('module has been disabled since profile requested following partition table type: %r' % self.all_results.get('partitiontable_type'))
			return {}

		result={}
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
						type='only_mount'
						if self.container['disk'][disk]['partitions'][part]['touched']:
							type=self.container['disk'][disk]['partitions'][part]['type']
						tmpresult.append( ("PHY", device, type, format, fstype, start, end, mpoint, flag) )
		result[ 'disks' ] = string.join( partitions, ' ')

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
				type='only_mount'
				if lv['touched']:
					type = 'LVMLV'
				flag='None'
				tmpresult.append( ("LVM", lv['dev'], type, format, fstype, start, end, mpoint, flag) )
		# sort partitions by mountpoint
		i = 0
		tmpresult.sort(lambda x,y: cmp(x[7], y[7]))  # sort by mountpoint
		for (parttype, device, type, format, fstype, start, end, mpoint, flag) in tmpresult:
			result[ 'dev_%d' % i ] =  "%s %s %s %s %s %sM %sM %s %s" % (parttype, device, type, format, fstype, self.MiB2MB(start), self.MiB2MB(end), mpoint, flag)
			i += 1
		return result

	def install_fresh_mbr(self, device=None):
		self.debug('Trying to install fresh partition table on device %s' % device)
		if not os.path.exists(device):
			self.debug('ERROR: device %s does not exist!' % device)
		else:
			command = ['/sbin/parted', '-s', device, 'mklabel', 'msdos']
			self.debug('Calling %s' % command)
			proc = subprocess.Popen(command, bufsize=0, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			(stdout, stderr) = proc.communicate()
			self.debug('===(exitcode=%d)====> %s\nSTDERR:\n=> %s\nSTDOUT:\n=> %s' %
							  (proc.returncode, command, stderr.replace('\n','\n=> '), stdout.replace('\n','\n=> ')))

	class partition(subwin):
		def __init__(self,parent,pos_y,pos_x,width,height):
			self.part_objects = {}
			subwin.__init__(self,parent,pos_y,pos_x,width,height)
			self.check_partition_table_msg()
			self.no_devices_msg()
			self.check_lvm_msg()
			self.ERROR = False

		def auto_partitioning_question_usbstorage_callback(self, result):
			self.container['autopart_usbstorage'] = True
			self.parent.debug('INCLUDE USB STORAGE DEVICES WITHIN AUTOPART')
			self.auto_partitioning(result)

		def auto_partitioning(self, result):
			# create disk list with usb storage devices
			disk_blacklist = self.parent.get_usb_storage_device_list()
			if len(disk_blacklist) > 0 and self.container['autopart_usbstorage'] == None:
				self.parent.debug('requesting user input: use usb storage devices?')
				msglist=[ _('Include USB storage devices while auto partitioning?'),
						  '',
						  _('WARNING: Choosing "yes" prepares for deletion of all'),
						  _('partitions on all disks! This includes USB harddisks'),
						  _('and USB sticks. In any case *ALL* LVM LV and LVM VG'),
						  _('will be deleted!'),
						  ]
				self.container['autopart_usbstorage'] = False
				self.sub = yes_no_win(self, self.pos_y+4, self.pos_x+2, self.width-4, self.height-14, msglist, default='no',
									  callback_yes=self.auto_partitioning_question_usbstorage_callback, callback_no=self.auto_partitioning)
				self.draw()
				return

			self.container['autopartition'] = True
			self.parent.debug('INTERACTIVE AUTO PARTITIONING')

			# if usb storage devices shall be included in autopart then delete blacklist
			if self.container['autopart_usbstorage']:
				disk_blacklist = []

			# remove all LVM LVs
			for vgname,vg in self.container['lvm']['vg'].items():
				for lvname, lv in vg['lv'].items():
					self.parent.debug('deleting LVM LV: %s' % lvname)
					self.part_delete_generic( 'lvm_lv', vgname, lvname )

			# reduce all LVM VGs
			for vgname,vg in self.container['lvm']['vg'].items():
				self.parent.debug('reducing LVM VG: %s' % vgname)
				if self.container['lvm']['vg'][ vgname ]['created']:
					self.container['history'].append('/sbin/vgreduce -a --removemissing %s' % vgname)
					self.container['history'].append('/sbin/vgremove %s' % vgname)
					self.container['lvm']['vg'][ vgname ]['created'] = 0

			# remove all logical partitions, next all extended partitions and finally all primary partitions
			for parttype in [ PARTTYPE_LOGICAL, PARTTYPE_EXTENDED, PARTTYPE_PRIMARY ]:
				for diskname, disk in self.container['disk'].items():
					# do not use blacklisted devices
					if diskname in disk_blacklist:
						self.parent.debug('disk %s is blacklisted (parttype=%s)' % (diskname, parttype))
					else:
						for partname, part in disk['partitions'].items():
							if part['type'] == parttype:
								self.parent.debug('deleting part: %s on %s (%s)' % (partname, diskname, self.parent.get_device(diskname, partname)))
								self.part_delete_generic( 'part', diskname, partname, force=True )

			# remove internal data avout LVM VGs and LVM PGs
			for vgname,vg in self.container['lvm']['vg'].items():
				self.parent.debug('removing LVM VG: %s' % vgname)
				del self.container['lvm']['vg'][vgname]
			self.container['lvm']['pv'] = {}

			self.parent.debug("HISTORY")
			for h in self.container['history']:
				self.parent.debug('==> %s' % h)

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
					sysmem = int(match.group(1)) / 1024
			self.parent.debug('AUTOPART: sysmem=%s' % sysmem)

			# create primary partition on first harddisk for /boot
			targetdisk = None
			targetpart = None
			for disk in disklist:
				for part in self.container['disk'][disk]['partitions'].keys():
					if self.container['disk'][disk]['partitions'][part]['type'] in [ PARTTYPE_FREESPACE_PRIMARY ]:
						if int(self.container['disk'][disk]['partitions'][part]['size']) > PARTSIZE_BOOT:
							targetdisk = disk
							targetpart = part
					if targetdisk:
						break
				if targetdisk:
					break
			if targetdisk:
				# part_create_generic(self,arg_disk,arg_part,mpoint,size,fstype,type,flag,format,end=0):
				self.part_create_generic(targetdisk, targetpart, '/boot', PARTSIZE_BOOT, 'ext4', PARTTYPE_PRIMARY, ['boot'], 1)
			else:
				msglist = [ _('Not enough disk space found for /boot!'),
							_('Auto partitioning aborted.') ]
				self.sub = msg_win(self,self.pos_y+8,self.pos_x+5,self.maxWidth,6, msglist)
				self.draw()
				return

			# determine size of free space areas
			freespacelist = []
			freespacemax = 0.0
			freespacesum = 0.0
			for disk in disklist:
				for part in self.container['disk'][disk]['partitions'].keys():
					if self.container['disk'][disk]['partitions'][part]['type'] in [ PARTTYPE_FREESPACE_PRIMARY ]:
						freespacelist.append( ( int(self.container['disk'][disk]['partitions'][part]['size']), disk, part ) )
						freespacesum += int(self.container['disk'][disk]['partitions'][part]['size'])
						if int(self.container['disk'][disk]['partitions'][part]['size']) > freespacemax:
							freespacemax = int(self.container['disk'][disk]['partitions'][part]['size'])
			freespacelist.sort(lambda x,y: int(x[0]) < int(y[0]))
			self.parent.debug('AUTOPART: freespacelist=%s' % freespacelist)
			self.parent.debug('AUTOPART: freespacesum=%s' % freespacesum)
			self.parent.debug('AUTOPART: freespacemax=%s' % freespacemax)

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
				swapsize -= 16
				if swapsize < PARTSIZE_SWAP_MIN:
					swapsize = PARTSIZE_SWAP_MIN

			targetdisk = None
			targetpart = None
			for disk in disklist:
				for part in self.container['disk'][disk]['partitions'].keys():
					if self.container['disk'][disk]['partitions'][part]['type'] in [ PARTTYPE_FREESPACE_PRIMARY ]:
						if int(self.container['disk'][disk]['partitions'][part]['size']) > swapsize:
							targetdisk = disk
							targetpart = part
					if targetdisk:
						break
				if targetdisk:
					break
			if targetdisk:
				# part_create_generic(self,arg_disk,arg_part,mpoint,size,fstype,type,flag,format,end=0):
				self.parent.debug('AUTOPART: create swap: disk=%s  part=%s  swapsize=%s' % (targetdisk, targetpart, swapsize))
				self.part_create_generic(targetdisk, targetpart, '', swapsize, 'linux-swap', PARTTYPE_PRIMARY, [], 1)
			else:
				self.parent.debug('AUTOPART: no disk space for swap found')
				self.parent.debug('AUTOPART: DISK=%s' % self.container['disk'])
				msglist = [ _('Not enough disk space found for /boot!'),
							_('Auto partitioning aborted.') ]
				self.sub = msg_win(self,self.pos_y+8,self.pos_x+5,self.maxWidth,6, msglist)
				self.draw()
				return

			# create one LVM PV per free space range
			parttype_mapping = { PARTTYPE_FREESPACE_PRIMARY: PARTTYPE_PRIMARY,
								 PARTTYPE_FREESPACE_LOGICAL: PARTTYPE_LOGICAL }
			for disk in disklist:
				for part in self.container['disk'][disk]['partitions'].keys():
					if self.container['disk'][disk]['partitions'][part]['type'] in [ PARTTYPE_FREESPACE_PRIMARY, PARTTYPE_FREESPACE_LOGICAL ]:
						# part_create_generic(self,arg_disk,arg_part,mpoint,size,fstype,type,flag,format,end=0):
						size = self.container['disk'][disk]['partitions'][part]['size']
						parttype = parttype_mapping[ self.container['disk'][disk]['partitions'][part]['type'] ]
						self.part_create_generic(disk, part, '', size, '', parttype, ['lvm'], 0)

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
				self.parent.debug('PV[%s]=%s' % (pvname, pv))
			for vgname, vg in self.container['lvm']['vg'].items():
				self.parent.debug('VG[%s]=%s' % (vgname, vg))

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

		def install_fresh_mbr_interactive(self, result, device=None):
			self.parent.install_fresh_mbr(device)
			self.container['problemdisk'][device].discard(DISKLABEL_UNKNOWN)
			self.container['problemdisk'][device].discard(DISKLABEL_GPT)
			self.parent.debug('performing restart of module')
			self.parent.start()
			#self.parent.layout()
			self.parent.debug('module restart done')
			self.container['lvm']['lvmconfigread'] = False
			self.container['autopartition'] == None


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

				if DISKLABEL_UNKNOWN in self.container['problemdisk'][dev]:  # search for specific problem in set() of errors
					self.parent.debug('requesting user input: unknown disklabel ==> write new MBR?')
					msglist=[ _('No valid partition table found on device %s.') % dev,
							  _('Install empty MBR to device %s ?') % dev,
							  '',
							  _('WARNING: By choosing "Write MBR" existing data'),
							  _('on device %s will be lost.') % dev,
							  ]
					self.sub = yes_no_win(self, self.pos_y+9, self.pos_x+2, self.width-4, self.height-25, msglist, default='no',
										  btn_name_yes=_('Write MBR'), btn_name_no=_('Ignore Device'),
										  callback_yes=self.install_fresh_mbr_interactive, device=dev)
					self.draw()
					self.container['problemdisk'][dev].discard(DISKLABEL_UNKNOWN)
					break

				if DISKLABEL_GPT in self.container['problemdisk'][dev]:  # search for specific problem in set() of errors
					self.parent.debug('requesting user input: GPT found ==> ignore or install empty MBR?')
					msglist=[ _('A GUID partition table (GPT) has been found on device %s.') % dev,
							  _('GPT devices are not supported by the interactive installation.'),
							  _('You can proceed by ignoring this device or by removing'),
							  _('the existing GPT and writing an empty MBR.'),
							  '',
							  _('WARNING: By choosing "Write MBR" existing data'),
							  _('on device %s will be lost.') % dev,
							  '',
							  _('HINT: Further information for an installation'),
							  _('on a device with GPT can be found in the'),
							  _('Support & Knowledge Base: http://sdb.univention.de.'),
							  '',
							  '',
							  _('Write an empty MBR to device %s ?') % dev,
							  ]
					self.sub = yes_no_win(self, self.pos_y+4, self.pos_x+2, self.width-4, self.height-25, msglist, default='no',
										  btn_name_yes=_('Write MBR'), btn_name_no=_('Ignore Device'),
										  callback_yes=self.install_fresh_mbr_interactive, device=dev)
					self.draw()
					self.container['problemdisk'][dev].discard(DISKLABEL_GPT)
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
						  _('unsuitable press F5 to restart partitioning.')
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
			col5=14
			col6=9

			head1=self.get_col(_('Device'),col1,'l')
			head2=self.get_col(_('Area(MB)'),col2)
			head3=self.get_col(_('Type'),col3)
			head4=self.get_col(_('Form.'),col4)
			head5=self.get_col(_('Mount point'),col5,'l')
			head6=self.get_col(_('Size(MB)'),col6)
			text = '%s %s %s %s %s %s'%(head1,head2,head3,head4,head5,head6)
			self.add_elem('TXT_0', textline(text,self.minY+11,self.minX+2)) #0

			device=self.container['disk'].keys()
			device.sort()

			self.parent.debug('LAYOUT')
			self.parent.printPartitionsCHS()

			dict=[]
			for dev in device:
				disk = self.container['disk'][dev]
				self.rebuild_table(disk,dev)
				txt = '%s  (%s) %s' % (dev.split('/',2)[-1], _('diskdrive'), '-'*(col1+col2+col3+col4+col5+10))
				path = self.get_col(txt,col1+col2+col3+col4+col5+4,'l')

				size = self.get_col('%s'%int(disk['size']),col6)
				# save for later use (evaluating inputs)
				self.part_objects[ len(dict) ] = [ 'disk', dev ]
				dict.append('%s %s' % (path,size))

				part_list=self.container['disk'][dev]['partitions'].keys()
				part_list.sort()
				for i in range(len(part_list)):
					part = self.container['disk'][dev]['partitions'][part_list[i]]
					path = self.get_col(' %s' % self.dev_to_part(part, dev),col1,'l')

					format=self.get_col('',col4,'m')
					if part['format']:
						format=self.get_col('X',col4,'m')
					if 'lvm' in part['flag']:
						type=self.get_col('LVMPV',col3)

						device = self.parent.get_device(dev, part_list[i])
						# display corresponding vg of pv if available
						if self.container['lvm'].has_key('pv') and self.container['lvm']['pv'].has_key( device ):
							if self.container['lvm']['pv'][device]['vg']:
								mount=self.get_col( self.container['lvm']['pv'][device]['vg'], col5, 'l')
							else:
								mount=self.get_col( _('(unassigned)'), col5, 'l')
						else:
							mount=self.get_col('',col5,'l')
					else:
						type=self.get_col(part['fstype'],col3)
						if part['fstype']== 'linux-swap':
							type=self.get_col('swap',col3)
						mount=self.get_col(part['mpoint'],col5,'l')
					size=self.get_col('%s'%int(part['size']),col6)
					if part['type'] in [0,1,2]:
						start=('%s' % part_list[i]).split('.')[0]
						end=('%s' % (part_list[i]+part['size'])).split('.')[0]
						area=self.get_col('%s-%s' % (start,end),col2)

					if part['type'] == PARTTYPE_PRIMARY: # PRIMARY
						path = self.get_col(' %s' % self.dev_to_part(part, dev),col1,'l')
					elif part['type'] == PARTTYPE_LOGICAL: # LOGICAL
						path = self.get_col('  %s' % self.dev_to_part(part, dev),col1,'l')
					elif part['type'] == PARTTYPE_EXTENDED: # EXTENDED
						path = self.get_col(' %s' % self.dev_to_part(part, dev),col1,'l')
						type = self.get_col('extended',col3)
					elif part['type'] == PARTTYPE_FREESPACE_PRIMARY or part['type'] == PARTTYPE_FREESPACE_LOGICAL: # FREESPACE
						area=self.get_col('',col2)
						mount=self.get_col('',col5,'l')
						if not self.possible_type(self.container['disk'][dev],part_list[i]):
							path = self.get_col(' !!!',col1,'l')
							type = self.get_col(_('unusable'),col3)
						elif self.possible_type(self.container['disk'][dev],part_list[i]) == POSS_PARTTYPE_LOGICAL:
							path = self.get_col('  ---',col1,'l')
							type = self.get_col(_('free'),col3)
						elif self.possible_type(self.container['disk'][dev],part_list[i]) == POSS_PARTTYPE_BOTH or \
								 self.possible_type(self.container['disk'][dev],part_list[i]) == POSS_PARTTYPE_PRIMARY:
							path = self.get_col(' ---',col1,'l')
							type = self.get_col(_('free'),col3)
					else:
						area=self.get_col('',col2)
						type=self.get_col(_('unknown'),col3)
						path=self.get_col('---',col1)

					self.part_objects[ len(dict) ] = [ 'part', dev, part_list[i], i ]
					dict.append('%s %s %s %s %s %s'%(path,area,type,format,mount,size))
					self.parent.debug('==> DEV = %s   PART(%s) = %s' % (dev,part_list[i],part))

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
						vgsize = vg['PEsize'] * vg['totalPE'] / 1024
						size = self.get_col('%s' % vgsize,col6)

						self.part_objects[ len(dict) ] = [ 'lvm_vg', vgname, None ]
						dict.append('%s %s' % (path,size))

						for lvname in lvlist:
							lv = vg['lv'][ lvname ]
							self.parent.debug('==> LV = %s' % lv)
							path = self.get_col(' %s' % lvname,col1,'l')
							format = self.get_col('',col4,'m')
							if lv['format']:
								format=self.get_col('X',col4,'m')
							size=self.get_col('%s' % int(lv['size']),col6)
							type=self.get_col(lv['fstype'],col3)
							if lv['fstype']== 'linux-swap':
								type=self.get_col('swap',col3)
							mount=self.get_col(lv['mpoint'],col5,'l')
							area=self.get_col('',col2)

							self.part_objects[ len(dict) ] = [ 'lvm_lv', vgname, lvname ]
							dict.append('%s %s %s %s %s %s'%(path,area,type,format,mount,size))

						# show free space in volume group  ( don't show less than 3 physical extents )
						if vg['freePE'] > 2:
							path = self.get_col(' ---',col1,'l')
							format = self.get_col('',col4,'m')
							vgfree = vg['PEsize'] * vg['freePE'] / 1024
							size=self.get_col('%s' % int(vgfree),col6)
							type=self.get_col('free',col3)
							mount=self.get_col('',col5,'l')
							area=self.get_col('',col2)
							self.parent.debug('==> FREE %s MB' % vgfree)

							self.part_objects[ len(dict) ] = [ 'lvm_vg_free', vgname, None ]
							dict.append('%s %s %s %s %s %s'%(path,area,type,format,mount,size))

			self.container['dict']=dict

			msg = _('This module is used for partitioning the existing hard drives. It is recommended to use at least two partitions - one for the root file system, and one for the swap area.\n\nPlease note:\nIf automatic partitioning has been selected, all the data stored on these hard drives will be lost during this process! Should the proposed partitioning be undesirable, it can be rejected by pressing the F5 function key.')

			self.add_elem('TA_desc', textarea(msg, self.minY, self.minX, 10, self.maxWidth+11))
			self.add_elem('SEL_part', select(dict,self.minY+12,self.minX,self.maxWidth+11,14,self.container['selected'])) #1
			self.add_elem('BT_create', button(_('F2-Create'),self.minY+28,self.minX,18)) #2
			self.add_elem('BT_edit', button(_('F3-Edit'),self.minY+28,self.minX+(self.width/2)-4,align="middle")) #3
			self.add_elem('BT_delete', button(_('F4-Delete'),self.minY+28,self.minX+(self.width)-7,align="right")) #4
			self.add_elem('BT_reset', button(_('F5-Reset changes'),self.minY+29,self.minX,30)) #5
			self.add_elem('BT_write', button(_('F6-Write partitions'),self.minY+29,self.minX+(self.width)-37,30)) #6
			self.add_elem('BT_back', button(_('F11-Back'),self.minY+30,self.minX,30)) #7
			self.add_elem('BT_next', button(_('F12-Next'),self.minY+30,self.minX+(self.width)-37,30)) #8
			if self.startIt:
				self.parent.scan_extended_size()
				self.parent.debug('SCAN_EXT: %s' % self.container['temp'])
				if len(self.container['temp'].keys()):
					self.sub=self.resize_extended(self,self.minY+4,self.minX-2,self.maxWidth+16,self.maxHeight-19)
					self.sub.draw()

		def get_col(self, word, width, align='r'):
			wspace=' '*width
			if align is 'l':
				return word[:width]+wspace[len(word):]
			elif align is 'm':
				space=(width-len(word))/2
				return "%s%s%s" % (wspace[:space],word[:width],wspace[space+len(word):width])
			return wspace[len(word):]+word[:width]

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
					if self.resolve_type(type) == 'free' and self.possible_type(self.container['disk'][disk],part):
						self.parent.debug('create (%s)' % type)
						self.sub=self.edit(self,self.minY+5,self.minX+4,self.maxWidth,self.maxHeight-8)
						self.sub.draw()
					elif selected[0] == 'lvm_vg_free':
						self.parent.debug('create lvm!')
						self.sub=self.edit_lvm_lv(self,self.minY+5,self.minX+4,self.maxWidth,self.maxHeight-8)
						self.sub.draw()

				elif key == 267:# F3 - Edit
					self.parent.debug('edit')
					if self.resolve_type(type) == 'primary' or self.resolve_type(type) == 'logical':
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
					if type == PARTTYPE_PRIMARY or type == PARTTYPE_LOGICAL or type == PARTTYPE_LVM_LV:
						self.parent.debug('delete!')
						self.part_delete(self.get_elem('SEL_part').result()[0])
					elif type == PARTTYPE_EXTENDED:
						self.parent.debug('delete ext!')
						self.sub=self.del_extended(self,self.minY+9,self.minX-2,self.maxWidth+16,self.maxHeight-17)
						self.sub.draw()

				elif key == 270 or self.get_elem('BT_write').get_status(): # F6 - Write Partitions
					self.sub=self.verify(self,self.minY+(self.maxHeight/3),self.minX+(self.maxWidth/8),self.maxWidth,self.maxHeight-18)
					self.sub.draw()

				elif key in [ 10, 32 ]:
					if self.get_elem('SEL_part').get_status():
						if self.resolve_type(type) == 'extended':
							pass
						elif disk or part and self.possible_type(self.container['disk'][disk],part): #select
							if self.resolve_type(type) in ['primary', 'logical']:
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
							if self.resolve_type(type) in ['lvm_lv']:
								self.parent.debug('edit lvm!')
								self.sub=self.edit_lvm_lv(self,self.minY+6,self.minX+4,self.maxWidth,self.maxHeight-8)
								self.sub.draw()

					elif self.get_elem('BT_create').get_status():#create
						if self.resolve_type(type) is 'free' and self.possible_type(self.container['disk'][disk],part):
							self.sub=self.edit(self,self.minY+6,self.minX+4,self.maxWidth,self.maxHeight-8)
							self.sub.draw()

					elif self.get_elem('BT_edit').get_status():#edit
						if self.resolve_type(type) == 'primary' or self.resolve_type(type) == 'logical':
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
						if type == PARTTYPE_PRIMARY or type == PARTTYPE_LOGICAL or type == PARTTYPE_LVM_LV:
							self.part_delete(self.get_elem('SEL_part').result()[0])
						elif type == PARTTYPE_EXTENDED:
							self.sub=self.del_extended(self,self.minY+9,self.minX-2,self.maxWidth+16,self.maxHeight-17)
							self.sub.draw()

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
			forceflag=''
			if force:
				forceflag='-ff'

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
							vg['size'] = vg['PEsize'] * vg['totalPE'] / 1024.0
							if vg['freePE'] + vg['allocPE'] != vg['totalPE']:
								self.parent.debug('ASSERTION FAILED: vg[freePE] + vg[allocPE] != vg[totalPE]: %d + %d != %d' % (vg['freePE'], vg['allocPE'], vg['totalPE']))
							if vg['freePE'] < 0 or vg['allocPE'] < 0 or vg['totalPE'] < 0:
								self.parent.debug('ASSERTION FAILED: vg[freePE]=%d  vg[allocPE]=%d  vg[totalPE]=%d' % (vg['freePE'], vg['allocPE'], vg['totalPE']))
							# reduce or remove VG if VG is still present:
							#   then check if PV is last PV in VG ==> if yes, then call vgremove ==> else call vgreduce
							if self.container['lvm']['vg'][ vgname ]['created']:
								vg_cnt = 0
								for tmppvname, tmppv in self.container['lvm']['pv'].items():
									if tmppv['vg'] == vgname:
										vg_cnt += 1
								self.parent.debug('pv_delete: vgname=%s	 vg_cnt=%s' % (vgname, vg_cnt))
								if vg_cnt > 1:
									self.container['history'].append('/sbin/vgreduce %s %s' % (vgname, device))
								elif vg_cnt == 1:
									self.container['history'].append('/sbin/vgreduce -a --removemissing %s' % vgname)
									self.container['history'].append('/sbin/vgremove %s ' % vgname)
									self.container['lvm']['vg'][ vgname ]['created'] = 0
								else:
									self.parent.debug('pv_delete: installer is confused: vg_cnt is 0: doing nothing')
							pv['vg'] = ''

						# removing LVM PV signature from partition
						self.container['history'].append('/sbin/pvremove %s %s' % (forceflag, device))

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
				type = PARTTYPE_LVM_LV
			else:
				type=self.container['disk'][arg_disk]['partitions'][arg_part]['type']

			if type == PARTTYPE_PRIMARY:
				self.container['history'].append('/sbin/parted --script %s rm %s' % (arg_disk,self.container['disk'][arg_disk]['partitions'][arg_part]['num']))
				self.container['disk'][arg_disk]['partitions'][arg_part]['type']=PARTTYPE_FREESPACE_PRIMARY
				self.container['disk'][arg_disk]['partitions'][arg_part]['touched']=1
				self.container['disk'][arg_disk]['partitions'][arg_part]['format']=0
				self.container['disk'][arg_disk]['partitions'][arg_part]['mpoint']=''
				self.container['disk'][arg_disk]['partitions'][arg_part]['num']=-1
				self.container['disk'][arg_disk]['primary']-=1

			elif type == PARTTYPE_LOGICAL:
				deleted=self.container['disk'][arg_disk]['partitions'][arg_part]['num']
				self.container['history'].append('/sbin/parted --script %s rm %s' % (arg_disk,self.container['disk'][arg_disk]['partitions'][arg_part]['num']))
				self.container['disk'][arg_disk]['partitions'][arg_part]['type']=PARTTYPE_FREESPACE_LOGICAL
				self.container['disk'][arg_disk]['partitions'][arg_part]['touched']=1
				self.container['disk'][arg_disk]['partitions'][arg_part]['format']=0
				self.container['disk'][arg_disk]['partitions'][arg_part]['mpoint']=''
				self.container['disk'][arg_disk]['partitions'][arg_part]['num']=-1
				count=0
				for part in self.container['disk'][arg_disk]['partitions'].keys():
					if self.container['disk'][arg_disk]['partitions'][part]['type'] == PARTTYPE_LOGICAL:
						count += 1
					if self.container['disk'][arg_disk]['partitions'][part]['type'] is PARTTYPE_EXTENDED:
						extended=part
				if not count and extended: # empty extended
					self.container['history'].append('/sbin/parted --script %s rm %s' % (arg_disk,self.container['disk'][arg_disk]['partitions'][extended]['num']))
					self.container['disk'][arg_disk]['extended']=0
					self.container['disk'][arg_disk]['primary']-=1
					self.container['disk'][arg_disk]['partitions'][extended]['type']=PARTTYPE_FREESPACE_PRIMARY
					self.container['disk'][arg_disk]['partitions'][extended]['touched']=1
					self.container['disk'][arg_disk]['partitions'][arg_part]['num']=-1
				self.container['disk'][arg_disk]['logical']-=1
				self.container['disk'][arg_disk] = self.renum_logical(self.container['disk'][arg_disk],deleted)

			elif type == PARTTYPE_EXTENDED:
				self.container['disk'][arg_disk]['extended']=0
				self.container['disk'][arg_disk]['primary']-=1
				self.container['disk'][arg_disk]['partitions'][arg_part]['type']=PARTTYPE_FREESPACE_PRIMARY
				self.container['disk'][arg_disk]['partitions'][arg_part]['touched']=1
				for part in self.container['disk'][arg_disk]['partitions'].keys():
					if self.container['disk'][arg_disk]['partitions'][part]['type'] == PARTTYPE_LOGICAL:
						self.container['history'].append('/sbin/parted --script %s rm %s' % (arg_disk,self.container['disk'][arg_disk]['partitions'][part]['num']))
						self.container['disk'][arg_disk]['partitions'][part]['type']=PARTTYPE_FREESPACE_LOGICAL
						self.container['disk'][arg_disk]['partitions'][part]['touched']=1
						self.container['disk'][arg_disk]['logical']-=1
				self.container['history'].append('/sbin/parted --script %s rm %s' % (arg_disk,self.container['disk'][arg_disk]['partitions'][arg_part]['num']))
				self.container['disk'][arg_disk]['partitions'][arg_part]['num']=-1

			elif type == PARTTYPE_LVM_LV:
				lv = self.container['lvm']['vg'][ arg_disk ]['lv'][ arg_part ]

				self.parent.debug('removing LVM LV %s' % lv['dev'])
				self.container['history'].append('/sbin/lvremove -f %s' % lv['dev'])

				# update used/free space on volume group
				currentLE = lv['currentLE']
				self.parent.container['lvm']['vg'][ lv['vg'] ]['freePE'] += currentLE
				self.parent.container['lvm']['vg'][ lv['vg'] ]['allocPE'] -= currentLE

				del self.container['lvm']['vg'][ arg_disk ]['lv'][ arg_part ]

			if type == PARTTYPE_LOGICAL:
				self.minimize_extended(arg_disk)
			if type != PARTTYPE_LVM_LV:
				self.container['disk'][arg_disk]=self.rebuild_table(self.container['disk'][arg_disk],arg_disk)

		def part_create(self,index,mpoint,size,fstype,type,flag,format,end=0):
			result=self.part_objects[index]
			self.part_create_generic(result[1], result[2], mpoint, size, fstype, type, flag, format, end)

		def part_create_generic(self,arg_disk,arg_part,mpoint,size,fstype,type,flag,format,end=0):
			part_list = self.container['disk'][arg_disk]['partitions'].keys()
			part_list.sort()
			old_size=self.container['disk'][arg_disk]['partitions'][arg_part]['size']
			old_type=self.container['disk'][arg_disk]['partitions'][arg_part]['type']
			old_sectors=self.container['disk'][arg_disk]['partitions'][arg_part]['size']

			# getCHSandPosition( positionOnDisk, geometry, parttype )
			# get start of partition and correct it if neccessary
			free_part_start = self.parent.getCHSandPosition(arg_part, self.container['disk'][arg_disk]['geometry'], type)
			self.parent.debug("free_part_start_orig=%s" % str(free_part_start))
			free_part_start = self.parent.getCHSandPosition(arg_part, self.container['disk'][arg_disk]['geometry'], type, correction = 'decrease', force = True)
			self.parent.debug("free_part_start_corr=%s" % str(free_part_start))

			# move startpoint of current disk if needed
			if arg_part != free_part_start['position']:
				self.container['disk'][arg_disk]['partitions'][ free_part_start['position'] ] = self.container['disk'][arg_disk]['partitions'][arg_part]
				del self.container['disk'][arg_disk]['partitions'][arg_part]
				arg_part = free_part_start['position']

			# get end of partition and correct it if neccessary
			free_part_end = self.parent.getCHSandPosition(arg_part + self.container['disk'][arg_disk]['partitions'][arg_part]['size'],
													 self.container['disk'][arg_disk]['geometry'], type, correction = 'increase', force = True)
			self.parent.debug("free_part_end_corr=%s" % str(free_part_end))
			# calculate size of free partition space
			free_part_size = free_part_end['position'] - free_part_start['position']
			self.parent.debug("free_part_size=%s" % str(free_part_size))


			new_part_start = free_part_start
			new_part_size = free_part_size
			# consistency checks
			if new_part_size > size:
				new_part_size = size
			if new_part_size < size:
				self.parent.debug('CONSISTENCY CHECK ERROR: requested size is too large: new_part_size=%s   requested size=%s' % (new_part_size, size))
			new_part_end = self.parent.getCHSandPosition(arg_part + new_part_size, self.container['disk'][arg_disk]['geometry'], type, correction = 'increase', force = True)

			new_part_size = new_part_end['position'] - new_part_start['position']
			self.parent.debug("new_part_start_corr=%s" % str(new_part_start))
			self.parent.debug("new_part_end_corr=%s" % str(new_part_end))
			self.parent.debug("new_part_size=%s" % str(new_part_size))

			if type == PARTTYPE_PRIMARY or type == PARTTYPE_LOGICAL: #create new primary/logical disk
				current = arg_part
				if type == PARTTYPE_LOGICAL: # need to modify/create extended
					if not self.container['disk'][arg_disk]['extended']: #create extended
						ext_part_start = self.parent.getCHSandPosition( current, self.container['disk'][arg_disk]['geometry'], PARTTYPE_EXTENDED, correction = 'decrease', force = True)
						ext_part_end = new_part_end
						ext_part_size = ext_part_end['position'] - ext_part_start['position']
						ext_part = ext_part_start['position']
						self.parent.debug("ext_part_start_corr=%s" % str(ext_part_start))
						self.parent.debug("ext_part_end_corr=%s" % str(ext_part_end))
						self.parent.debug("ext_part_size=%s" % str(ext_part_size))

						self.container['disk'][arg_disk]['partitions'][ext_part] = {}
						self.container['disk'][arg_disk]['partitions'][ext_part]['size'] = ext_part_size
						self.container['disk'][arg_disk]['partitions'][ext_part]['touched']=1
						self.container['disk'][arg_disk]['partitions'][ext_part]['mpoint']=''
						self.container['disk'][arg_disk]['partitions'][ext_part]['fstype']=''
						self.container['disk'][arg_disk]['partitions'][ext_part]['flag']=[]
						self.container['disk'][arg_disk]['partitions'][ext_part]['format']=0
						self.container['disk'][arg_disk]['partitions'][ext_part]['type']=PARTTYPE_EXTENDED
						self.container['disk'][arg_disk]['partitions'][ext_part]['num']=0
						self.container['disk'][arg_disk]['primary']+=1
						self.container['disk'][arg_disk]['extended']=1
						self.container['history'].append('/sbin/parted --script %s unit chs mkpart %s %s %s' %
														 (arg_disk,
														  self.resolve_type(PARTTYPE_EXTENDED),
														  self.parent.MiB2CHSstr(arg_disk, ext_part),
														  self.parent.MiB2CHSstr(arg_disk, ext_part+ext_part_size)))

					else: # resize extended
						for part in self.container['disk'][arg_disk]['partitions'].keys():
							if self.container['disk'][arg_disk]['partitions'][part]['type'] == PARTTYPE_EXTENDED:
								break #found extended leaving loop
						if (part + self.container['disk'][arg_disk]['partitions'][part]['size']) < arg_part:
							# starting point of extended partition is smaller than starting point of new logical partition
							# extended partition is getting larger at the end
							self.container['disk'][arg_disk]['partitions'][part]['size'] = new_part_end['position'] - part
							self.container['disk'][arg_disk]['partitions'][part]['touched']=1
							self.container['history'].append('/sbin/parted --script %s unit chs resize %s %s %s' %
															 (arg_disk,
															  self.container['disk'][arg_disk]['partitions'][part]['num'],
															  self.parent.MiB2CHSstr(arg_disk, part),
															  self.parent.MiB2CHSstr(arg_disk, part + self.container['disk'][arg_disk]['partitions'][part]['size'])))
						elif part > arg_part:
							# starting point of extended partition is larger than starting point of new logical partition
							# extended partition grows at the beginning
							extendpos = part + self.container['disk'][arg_disk]['partitions'][part]['size']
							ext_part_start = self.parent.getCHSandPosition( current, self.container['disk'][arg_disk]['geometry'], PARTTYPE_EXTENDED, correction = 'decrease', force = True)
							ext_part_end = self.parent.getCHSandPosition( extendpos, self.container['disk'][arg_disk]['geometry'], PARTTYPE_EXTENDED, correction = 'increase', force = True)
							ext_part_size = ext_part_end['position'] - ext_part_start['position']
							ext_part = ext_part_start['position']
							self.parent.debug("ext_part_start_corr=%s" % str(ext_part_start))
							self.parent.debug("ext_part_end_corr=%s" % str(ext_part_end))
							self.parent.debug("ext_part_size=%s" % str(ext_part_size))

							self.container['disk'][arg_disk]['partitions'][ ext_part ] = self.container['disk'][arg_disk]['partitions'][part]
							del self.container['disk'][arg_disk]['partitions'][part]

							self.container['disk'][arg_disk]['partitions'][ext_part]['size'] = ext_part_size
							self.container['disk'][arg_disk]['partitions'][ext_part]['touched']=1
							self.container['history'].append('/sbin/parted --script %s unit chs resize %s %s %s' %
															 (arg_disk,
															  self.container['disk'][arg_disk]['partitions'][arg_part]['num'],
															  self.parent.MiB2CHSstr(arg_disk, arg_part),
															  self.parent.MiB2CHSstr(arg_disk, arg_part + self.container['disk'][arg_disk]['partitions'][arg_part]['size'])))

				if not self.container['disk'][arg_disk]['partitions'].has_key(current):
					self.container['disk'][arg_disk]['partitions'][current]={}
				self.container['disk'][arg_disk]['partitions'][current]['touched']=1
				if len(mpoint) > 0 and not mpoint.startswith('/'):
					mpoint='/%s' % mpoint
				self.container['disk'][arg_disk]['partitions'][current]['mpoint']=mpoint
				self.container['disk'][arg_disk]['partitions'][current]['fstype']=fstype
				self.container['disk'][arg_disk]['partitions'][current]['flag']=flag
				self.container['disk'][arg_disk]['partitions'][current]['format']=format
				self.container['disk'][arg_disk]['partitions'][current]['type']=type
				self.container['disk'][arg_disk]['partitions'][current]['num']=0
				self.container['disk'][arg_disk]['partitions'][current]['size']=new_part_size
				self.container['history'].append('/sbin/parted --script %s unit chs mkpart %s %s %s' %
												 (arg_disk,
												  self.resolve_type(type),
												  self.parent.MiB2CHSstr(arg_disk, current),
												  self.parent.MiB2CHSstr(arg_disk, current + new_part_size)))
				if type == PARTTYPE_PRIMARY:
					self.container['disk'][arg_disk]['primary']+=1
				# if partition is greater/equal than min_size then create free space entry
				if (old_size - size) >= self.container['min_size']:
					self.container['disk'][arg_disk]['partitions'][current]['size'] = new_part_size
					if not end: #start at first sector of freespace
						# calculate start position of next cyl
						self.parent.debug('current=%s' % current)
						self.parent.debug('new_part_size=%s' % new_part_size)
						new_free_start = self.parent.getCHSnextCyl(current + new_part_size, self.container['disk'][arg_disk]['geometry'], PARTTYPE_FREESPACE_PRIMARY)
						self.parent.debug('new_free_start=%s' % new_free_start)
						new_free_size = free_part_end['position'] - new_free_start
						self.parent.debug('new_free_size=%s' % new_free_size)
					else: # new partition at the end of freespace
						newpos = self.parent.getCHSandPosition( free_part_end['position'] - new_part_size, self.container['disk'][arg_disk]['geometry'], type, correction = 'decrease', force = True )
						self.container['disk'][arg_disk]['partitions'][ newpos['position'] ] = self.container['disk'][arg_disk]['partitions'][current]

						new_free_end = self.parent.getCHSlastCyl( newpos['position'], self.container['disk'][arg_disk]['geometry'], PARTTYPE_FREESPACE_PRIMARY)
						new_free_start = current
						new_free_size = new_free_end - new_free_start
					self.container['disk'][arg_disk]['partitions'][new_free_start]={}
					self.container['disk'][arg_disk]['partitions'][new_free_start]['touched']=1
					self.container['disk'][arg_disk]['partitions'][new_free_start]['size'] = new_free_size
					self.container['disk'][arg_disk]['partitions'][new_free_start]['mpoint']=''
					self.container['disk'][arg_disk]['partitions'][new_free_start]['fstype']=''
					self.container['disk'][arg_disk]['partitions'][new_free_start]['flag']=[]
					self.container['disk'][arg_disk]['partitions'][new_free_start]['format']=0
					self.container['disk'][arg_disk]['partitions'][new_free_start]['type']=PARTTYPE_FREESPACE_PRIMARY
					self.container['disk'][arg_disk]['partitions'][new_free_start]['num']=-1 #temporary wrong num
				if type == PARTTYPE_LOGICAL:
					self.minimize_extended(arg_disk)
				self.rebuild_table( self.container['disk'][arg_disk],arg_disk)

				for f in flag:
					self.container['history'].append('/sbin/parted --script %s set %d %s on' % (arg_disk,self.container['disk'][arg_disk]['partitions'][current]['num'],f))

				if 'lvm' in flag:
					self.pv_create(arg_disk, current)

				self.parent.debug("HISTORY")
				for h in self.container['history']:
					self.parent.debug('==> %s' % h)

			self.parent.printPartitionsCHS()

		def pv_create(self, disk, part):
			device = '%s%d' % (disk,self.container['disk'][disk]['partitions'][part]['num'])
			ucsvgname = self.container['lvm']['ucsvgname']

			# create new PV entry
			pesize = self.container['lvm']['vg'][ ucsvgname ]['PEsize']
			# number of physical extents
			pecnt = int(self.container['disk'][disk]['partitions'][part]['size'] * 1024 / pesize)
			# LVM uses about 2% of percent for metadata overhead
			totalpe = int(pecnt * 0.978)

			self.parent.debug('pv_create: pesize=%sk   partsize=%sM=%sk  pecnt=%sPE  totalpe=%sPE' %
							  (pesize, self.container['disk'][disk]['partitions'][part]['size'],
							   self.container['disk'][disk]['partitions'][part]['size'] * 1024, pecnt, totalpe))

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
																self.container['lvm']['vg'][ ucsvgname ]['PEsize'] / 1024.0)

			device = self.parent.get_device(disk, part)
			# remove LVMPV signature before creating a new one
			self.container['history'].append('/sbin/pvremove -ff %s' % device)
#			self.container['history'].append('/sbin/pvscan')
			self.container['history'].append('/sbin/pvcreate %s' % device)
			if not self.container['lvm']['vg'][ ucsvgname ]['created']:
				self.container['history'].append('/sbin/vgcreate --physicalextentsize %sk %s %s' %
														 (self.container['lvm']['vg'][ ucsvgname ]['PEsize'], ucsvgname, device))
				self.container['lvm']['vg'][ ucsvgname ]['created'] = 1
#				self.container['history'].append('/sbin/vgscan')
			else:
				self.container['history'].append('/sbin/vgextend %s %s' % (ucsvgname, device))

		def minimize_extended_old(self, disk):
			self.parent.debug('### minimize: %s'%disk)
			new_start=float(-1)
			start=new_start
			new_end=float(-1)
			end=new_end
			part_list=self.container['disk'][disk]['partitions'].keys()
			part_list.sort()
			for part in part_list:
				# check all logical parts and find minimum size for extended
				if self.container['disk'][disk]['partitions'][part]['type'] == PARTTYPE_LOGICAL:
					if new_end > 0:
						new_end=part+self.container['disk'][disk]['partitions'][part]['size']
					if new_start < 0 or part < new_start:
						new_start = part
					if new_end < 0 or new_end < part+self.container['disk'][disk]['partitions'][part]['size']:
						new_end = part+self.container['disk'][disk]['partitions'][part]['size']
				elif self.container['disk'][disk]['partitions'][part]['type'] == PARTTYPE_EXTENDED:
					start = part
					end=start+self.container['disk'][disk]['partitions'][part]['size']
			new_start -= float(0.01)
			if self.container['disk'][disk]['partitions'].has_key(start):
				if new_start > start:
					self.parent.debug('### minimize at start: %s'%[new_start,start])
					self.container['disk'][disk]['partitions'][start]['size']=end-new_start
					self.container['disk'][disk]['partitions'][new_start]=self.container['disk'][disk]['partitions'][start]
					self.container['history'].append('/sbin/parted --script %s unit chs resize %s %s %s; #1' %
													 (disk,
													  self.container['disk'][disk]['partitions'][start]['num'],
													  self.parent.MiB2CHSstr(disk, new_start),
													  self.parent.MiB2CHSstr(disk, new_end)))
					self.container['disk'][disk]['partitions'].pop(start)
				elif new_end > end:
					self.parent.debug('### minimize at end: %s'%[new_end,end])
					self.container['disk'][disk]['partitions'][part_list[-1]]['type']=PARTTYPE_FREESPACE_LOGICAL
					self.container['disk'][disk]['partitions'][part_list[-1]]['num']=-1
					self.container['history'].append('/sbin/parted --script %s unit chs resize %s %s %s' %
													 (disk,
													  self.container['disk'][disk]['partitions'][start]['num'],
													  self.parent.MiB2CHSstr(disk, start),
													  self.parent.MiB2CHSstr(disk, new_end)))

			self.layout()
			self.draw()

		def minimize_extended(self, disk):
			self.parent.debug('minimize_extended: %s' % disk)
			ext_start = float(-1)
			ext_end = float(-1)
			new_start = float(-1)
			new_end = float(-1)

			part_list=self.container['disk'][disk]['partitions'].keys()
			# sort part_list to make sure to get all partitions in ascending order
			part_list.sort()
			for part in part_list:
				# check all logical parts and find minimum size for extended
				if self.container['disk'][disk]['partitions'][part]['type'] == PARTTYPE_LOGICAL:
					# if new_end is not set (-1) or is smaller than the end position of current logical partition then save end pos to new_end
					if new_end < 0 or new_end < part+self.container['disk'][disk]['partitions'][part]['size']:
						new_end = part+self.container['disk'][disk]['partitions'][part]['size']
					if new_start < 0 or part < new_start:
						new_start = part
				elif self.container['disk'][disk]['partitions'][part]['type'] == PARTTYPE_EXTENDED:
					ext_start = part
					ext_end = part + self.container['disk'][disk]['partitions'][part]['size']
			if new_start >= 0 and new_end >= 0:
				newpos = self.parent.getCHSandPosition( new_start, self.container['disk'][disk]['geometry'], PARTTYPE_EXTENDED, correction = 'decrease', force = True )
				new_start = newpos['position']
				newpos = self.parent.getCHSandPosition( new_end, self.container['disk'][disk]['geometry'], PARTTYPE_EXTENDED, correction = 'increase', force = True )
				new_end = newpos['position']

			if ext_start >= 0:
				if new_start > ext_start:
					self.parent.debug('minimize_extended: minimize at start: old_start=%s  new_start=%s' % (ext_start, new_start))
					# correct size if current ext partition
					self.container['disk'][disk]['partitions'][ext_start]['size'] = ext_end - new_start
					self.container['disk'][disk]['partitions'][new_start] = self.container['disk'][disk]['partitions'][ext_start]
					# create primary free space after ext partition
					free_start = ext_start
					free_end = self.parent.getCHSlastCyl( new_start, self.container['disk'][disk]['geometry'], PARTTYPE_FREESPACE_PRIMARY )
					self.container['disk'][disk]['partitions'][ free_start ] = self.parent.generate_freespace( free_start, free_end )
					# run parted
					self.container['history'].append('/sbin/parted --script %s unit chs resize %s %s %s; #1' %
													 (disk,
													  self.container['disk'][disk]['partitions'][ext_start]['num'],
													  self.parent.MiB2CHSstr(disk, new_start),
													  self.parent.MiB2CHSstr(disk, ext_end)))
				elif new_end < ext_end:
					self.parent.debug('minimize_extended: minimize at end: old_end=%s  new_end=%s' % (ext_end, new_end))
					# correct size of current ext partition
					self.container['disk'][disk]['partitions'][ext_start]['size'] = new_end - ext_start
					# create primary free space after ext partition
					free_end = ext_end
					free_start = self.parent.getCHSnextCyl( new_end, self.container['disk'][disk]['geometry'], PARTTYPE_FREESPACE_PRIMARY )
					self.container['disk'][disk]['partitions'][ free_start ] = self.parent.generate_freespace( free_start, free_end )
					# run parted
					self.container['history'].append('/sbin/parted --script %s unit chs resize %s %s %s' %
													 (disk,
													  self.container['disk'][disk]['partitions'][ext_start]['num'],
													  self.parent.MiB2CHSstr(disk, ext_start),
													  self.parent.MiB2CHSstr(disk, new_end)))

				self.layout()
				self.draw()

		def rebuild_table(self, disc, device):
			part=disc['partitions'].keys()
			part.sort()
			old=disc['partitions']
			new={}
			extended=-1
			last_new=-1
			previous_type=-1
			next_type=-1
			primary=[1,2,3,4]
			new_primary=-1
			redo=0
			for i in range(len(part)):
				current_type=old[part[i]]['type']
				if current_type == PARTTYPE_PRIMARY or current_type == PARTTYPE_EXTENDED: # Copy primary
					#need to find next number for primary
					if old[part[i]]['num'] == 0:
						new_primary=part[i]
					else:
						primary.remove(int(old[part[i]]['num']))
					if current_type == PARTTYPE_EXTENDED:
						extended=part[i]
				if i > 0:
					previous_type=new[last_new]['type']
					if (previous_type == PARTTYPE_FREESPACE_PRIMARY and current_type == PARTTYPE_FREESPACE_PRIMARY) or \
					   (previous_type == PARTTYPE_FREESPACE_LOGICAL and current_type == PARTTYPE_FREESPACE_LOGICAL) or \
					   (previous_type == PARTTYPE_FREESPACE_PRIMARY and current_type == PARTTYPE_FREESPACE_LOGICAL): # found freespace next to freespace -> merge
						new[last_new]['size']= (part[i] + old[part[i]]['size']) - last_new
					elif previous_type == PARTTYPE_FREESPACE_LOGICAL and current_type == PARTTYPE_FREESPACE_PRIMARY:
						if extended < 0:
							old[part[i]]['size']+=new[last_new]['size']
							new[last_new]=old[part[i]]
							new[last_new]['touched']
						else:
							new[extended]['size']-=old[part[i-1]]['size']
							new[extended]['touched']=1
							old[part[i]]['size']+=new[last_new]['size']
							new[last_new]=old[part[i]]
							new[last_new]['touched']
						redo=1
					elif previous_type == PARTTYPE_EXTENDED and current_type == PARTTYPE_FREESPACE_LOGICAL and \
						 not i == 1 and disc['partitions'][part[i-2]]['type'] == PARTTYPE_FREESPACE_PRIMARY:
						# freespace next to extended part
						# a logical part has been remove
						# the extended have to be resized
						# frespaces have to be merged
						old[part[i-2]]['size']=( part[i] + old[part[i]]['size']) - part[i-2]
						new[part[i-2]]=old[part[i-2]] # resize primary freespace
						new[part[i-2]]['touched']=1
						new[last_new]['size']-=old[part[i]]['size']
						new[part[i]+old[part[i]]['size']]=new[last_new]
						new[part[i]+old[part[i]]['size']]['touched']=1
						new.pop(last_new)
						last_new=part[i]+old[part[i]]['size']

					elif previous_type == PARTTYPE_EXTENDED and current_type == PARTTYPE_FREESPACE_LOGICAL:
						old[part[i-1]]['size']-=old[part[i]]['size']
						new_start=part[i]
						new_end=new_start+old[part[i-1]]['size']
						new[new_start]=old[part[i-1]]
						self.container['history'].append('/sbin/parted --script %s unit chs resize %s %s %s' %
														 (device,
														  old[part[i-1]]['num'],
														  self.parent.MiB2CHSstr(device, new_start),
														  self.parent.MiB2CHSstr(device, new_end)))
						new[part[i-1]]=old[part[i]]
						redo=1

					elif current_type == PARTTYPE_EXTENDED and previous_type == PARTTYPE_LOGICAL:
						# new logical in front of extend found - need to resize extended
						old[part[i]]['size']+=old[part[i-1]]['size']
						new[last_new]=old[part[i]]
						new[last_new]['touched']=1
						old[part[i-1]]['size']-=1
						new[last_new+1]=old[part[i-1]]
						new[last_new+1]['touched']=1
						last_new+=1

					elif current_type == PARTTYPE_LOGICAL:
						# Copy logical and correct number
						if not old[part[i]]['num']:
							disc['logical']+=1
							old[part[i]]['num']=4+disc['logical']
						new[part[i]]=old[part[i]]
						last_new=part[i]

					elif current_type == PARTTYPE_PRIMARY:
						# Copy primary
						new[part[i]]=old[part[i]]
						last_new=part[i]

					elif current_type == PARTTYPE_FREESPACE_PRIMARY or current_type == PARTTYPE_FREESPACE_LOGICAL:
						# Copy Freespace
						new[part[i]]=old[part[i]]
						last_new=part[i]

					elif current_type == PARTTYPE_EXTENDED:
						new[part[i]]=old[part[i]]
						extended = part[i]
						last_new=part[i]

				else:
					new[part[i]]=old[part[i]]
					last_new=part[i]

			if new_primary > -1: # new primary needs free number
				new[new_primary]['num'] = primary[0]

			disc['partitions']=new

			if redo:
				return self.rebuild_table(disc,device)
			else:
				return disc

		def renum_logical(self,disk,deleted): # got to renum partitions Example: Got 5 logical on hda and remove hda7
			parts = disk['partitions'].keys()
			parts.sort()
			for part in parts:
				if disk['partitions'][part]['type'] == PARTTYPE_LOGICAL and disk['partitions'][part]['num'] > deleted:
					disk['partitions'][part]['num'] -= 1
			return disk

		def possible_type(self, disk, p_index):
			# 1 -> primary only
			# 2 -> logical only
			# 3 -> both
			# 0 -> unusable
			parts=disk['partitions'].keys()
			parts.sort()
			current=parts.index(p_index)
			if len(disk['partitions'])>1:
				if disk['extended']:
					if len(parts)-1 > current and disk['partitions'][parts[current-1]]['type'] == PARTTYPE_LOGICAL and \
						   disk['partitions'][parts[current+1]]['type'] == PARTTYPE_LOGICAL:
						return 2
					primary=0
					if disk['primary'] < 4:
						primary = 1
					if len(parts)-1 > current and disk['partitions'][parts[current+1]]['type'] == PARTTYPE_EXTENDED:
						return 2+primary
					elif disk['partitions'][parts[current-1]]['type'] == PARTTYPE_LOGICAL:
						return 2+primary
					else:
						return 0+primary

				elif disk['primary'] < 4:
					return 3
				else:
					return 0
			else:
				return 3

		def lv_create(self, vgname, lvname, currentLE, format, fstype, flag, mpoint):
			vg = self.parent.container['lvm']['vg'][ vgname ]
			size = int(vg['PEsize'] * currentLE / 1024.0)
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

			self.parent.container['history'].append('/sbin/lvcreate -l %d --name "%s" "%s"' % (currentLE, lvname, vgname) )
#			self.parent.container['history'].append('/sbin/lvscan 2> /dev/null')

			self.parent.debug("HISTORY")
			for h in self.parent.container['history']:
				self.parent.debug('==> %s' % h)

			# update used/free space on volume group
			self.parent.container['lvm']['vg'][ vgname ]['freePE'] -= currentLE
			self.parent.container['lvm']['vg'][ vgname ]['allocPE'] += currentLE

		def resolve_type(self,type):
			mapping = { PARTTYPE_PRIMARY: 'primary',
						PARTTYPE_LOGICAL: 'logical',
						PARTTYPE_EXTENDED: 'extended',
						PARTTYPE_FREESPACE_PRIMARY: 'free',
						PARTTYPE_FREESPACE_LOGICAL: 'free',
						8: 'meta',
						9: 'meta',
						PARTTYPE_LVM_VG: 'lvm_vg',
						PARTTYPE_LVM_LV: 'lvm_lv',
						PARTTYPE_LVM_VG_FREE: 'lvm_lv_free',
						}
			if mapping.has_key(type):
				return mapping[type]
			self.parent.debug('ERROR: resolve_type(%s)=unknown' % type)
			return 'unknown'

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
				self.sub = msg_win(self,self.pos_y+6,self.pos_x+1,self.width-1,2,msg)
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
			def __init__(self,parent,header,text,name='act',action=None):
				if action=='read_lvm':
					self.pos_x=parent.minX+(parent.maxWidth/2)-18
					self.pos_y=parent.minY+11
				else:
					self.pos_x=parent.minX+(parent.maxWidth/2)-13
					self.pos_y=parent.minY+11
				self.action = action
				act_win.__init__(self,parent,header,text,name)

			def run_command(self, command):
				self.parent.parent.debug('running "%s"' % command)
				proc = subprocess.Popen(command,bufsize=0,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
				(stdout, stderr) = proc.communicate()
				self.parent.parent.debug('===(exitcode=%d)====> %s\nSTDERR:\n=> %s\nSTDOUT:\n=> %s' %
										 (proc.returncode, command, stderr.replace('\n','\n=> '), stdout.replace('\n','\n=> ')))
				self.parent.parent.debug('waiting for udev to settle down')
				os.system("udevadm settle || true")

				if proc.returncode:
					self.parent.container['history']=[]
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
					self.parent.container['history']=[]
					self.parent.parent.written=1
				elif self.action == 'make_filesystem':
					self.parent.parent.debug('Create Filesystem')
					# create filesystems on physical partitions
					for disk in self.parent.container['disk'].keys():
						for part in self.parent.container['disk'][disk]['partitions'].keys():
							if self.parent.container['disk'][disk]['partitions'][part]['format']:
								device = self.parent.parent.get_device(disk, part)
								fstype=self.parent.container['disk'][disk]['partitions'][part]['fstype']
								if fstype in ['ext2','ext3','vfat','msdos', 'ext4', 'btrfs']:
									mkfs_cmd='/sbin/mkfs.%s %s' % (fstype,device)
								elif fstype == 'xfs':
									mkfs_cmd='/sbin/mkfs.xfs -f %s' % device
								elif fstype == 'linux-swap':
									mkfs_cmd='/bin/mkswap %s' % device
								else:
									mkfs_cmd='/bin/true %s' % device
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
								if fstype in ['ext2','ext3','vfat','msdos', 'ext4', 'btrfs']:
									mkfs_cmd='/sbin/mkfs.%s %s' % (fstype,device)
								elif fstype == 'xfs':
									mkfs_cmd='/sbin/mkfs.xfs -f %s' % device
								elif fstype == 'linux-swap':
									mkfs_cmd='/bin/mkswap %s' % device
								else:
									mkfs_cmd='/bin/true %s' % device
								retval = self.run_command(mkfs_cmd)
								if retval:
									return
								vg['lv'][lvname]['format'] = 0

				self.parent.layout()
				self.stop()

		class edit(subwin):
			def __init__(self,parent,pos_x,pos_y,width,heigth):
				self.close_on_subwin_exit = False
				subwin.__init__(self,parent,pos_x,pos_y,width,heigth)

			def helptext(self):
				return self.parent.helptext()

			def no_format_callback_part_create(self, result):
				selected=self.parent.container['temp']['selected']
				mpoint=self.parent.container['temp']['mpoint']
				size=self.parent.container['temp']['size']
				fstype=self.parent.container['temp']['fstype']
				type=self.parent.container['temp']['type']
				flag=self.parent.container['temp']['flag']
				self.parent.container['temp']={}
				if result == 'BT_YES':
					format=1
					self.parent.part_create(selected,mpoint,size,fstype,type,flag,format)
				elif result == 'BT_NO':
					format=0
					self.parent.part_create(selected,mpoint,size,fstype,type,flag,format)
				return 0

			def no_format_callback_part_edit(self, result, path, part):
				fstype=self.parent.container['temp']['fstype']
				self.parent.container['temp']={}
				if result == 'BT_YES':
					format=1
				else:
					format=0
				self.parent.container['disk'][path]['partitions'][part]['format']=format
				self.parent.container['disk'][path]['partitions'][part]['fstype']=fstype
				return 0

			def ignore_experimental_fstype(self):
				self.expFStype = True
				return 0

			def input(self, key):
				dev = self.parent.part_objects[self.parent.get_elem('SEL_part').result()[0]]
				type = dev[0]
				path = dev[1]
				disk=self.parent.container['disk'][path]

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
						if self.operation is 'create': # Speichern
							part=dev[2]
							mpoint=self.get_elem('INP_mpoint').result().strip()
							if self.get_elem('INP_size').result().isdigit():
								size=float(self.get_elem('INP_size').result())
							else:
								return 1
							format=self.get_elem('CB_format').result()
							fstype=self.get_elem('SEL_fstype').result()[0]
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

							type=int(self.get_elem('RB_pri_log').result())
							if float(disk['partitions'][part]['size']) < size:
								size=float(disk['partitions'][part]['size'])
							flag=[]
							if self.get_elem('CB_bootable').result():
								flag.append('boot')
							if self.elem_exists('CB_ppcprep') and self.get_elem('CB_ppcprep').result():
								flag.append('prep')
								flag.append('boot')
							if self.elem_exists('CB_lvmpv') and self.get_elem('CB_lvmpv').result():
								flag.append('lvm')
								mpoint=''
								format=1
								fstype='LVMPV'

							if fstype == 'linux-swap':
								mpoint=''
							if len(mpoint) > 0 and not mpoint.startswith('/'):
								mpoint='/%s' % mpoint
							self.parent.container['temp']={'selected':self.parent.get_elem('SEL_part').result()[0],
										'mpoint':mpoint,
										'size':size,
										'fstype':fstype,
										'type':type,
										'flag':flag,
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
								self.parent.container['temp']={}
								format=1

							num=0 # temporary zero
							self.parent.part_create(self.parent.get_elem('SEL_part').result()[0],mpoint,size,fstype,type,flag,format)
						elif self.operation is 'edit': # Speichern
							part=dev[2]
							mpoint=self.get_elem('INP_mpoint').result().strip()
							fstype=self.get_elem('SEL_fstype').result()[0]
							flag=[]
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

							if self.get_elem('CB_bootable').result():
								flag.append('boot')
							if self.elem_exists('CB_ppcprep') and self.get_elem('CB_ppcprep').result():
								flag.append('prep')
								flag.append('boot')

							self.parent.container['temp']={'fstype':fstype}
							if fstype == 'linux-swap':
								mpoint=''
							if len(mpoint) > 0 and not mpoint.startswith('/'):
								mpoint='/%s' % mpoint
							self.parent.container['disk'][path]['partitions'][part]['mpoint']=mpoint
							#if self.get_elem('CB_bootable').result():
							old_flags=self.parent.container['disk'][path]['partitions'][part]['flag']

							for f in old_flags:
								if f not in flag:
									self.parent.container['history'].append('/sbin/parted --script %s set %d %s off' % (path,self.parent.container['disk'][path]['partitions'][part]['num'],f))
							for f in flag:
								if f not in old_flags:
									self.parent.container['history'].append('/sbin/parted --script %s set %d %s on' % (path,self.parent.container['disk'][path]['partitions'][part]['num'],f))

							self.parent.container['disk'][path]['partitions'][part]['flag']=flag

							rootfs = (mpoint == '/')
							# if format is not set and mpoint == '/' OR
							#    format is not set and fstype changed
							if ( self.parent.container['disk'][path]['partitions'][part]['fstype'] != fstype or rootfs) and not self.get_elem('CB_format').result():
								if rootfs:
									msglist = [ _('This partition is designated as root file system,'),
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
													  msglist=msglist, callback_yes=self.no_format_callback_part_edit,
													  callback_no=self.no_format_callback_part_edit, default='no', path=path, part=part )
								self.sub.draw()
								return 1
							else:
								self.parent.container['temp']={}
								if self.get_elem('CB_format').result():
									self.parent.container['disk'][path]['partitions'][part]['format']=1
								else:
									self.parent.container['disk'][path]['partitions'][part]['format']=0
								self.parent.container['disk'][path]['partitions'][part]['fstype']=fstype
						self.parent.container['disk'][path]=self.parent.rebuild_table(disk,path)

						self.parent.layout()
						self.parent.draw()
						return 0
					elif key == 10 and self.get_elem_by_id(self.current).usable():
						return self.get_elem_by_id(self.current).key_event(key)
				if self.get_elem_by_id(self.current).usable():
					self.get_elem_by_id(self.current).key_event(key)
				if self.operation == 'edit':
					# if partition is LVM PV
					if not self.elem_exists('CB_lvmpv'):
						self.get_elem('INP_mpoint').enable()
						self.get_elem('SEL_fstype').enable()
						self.get_elem('CB_format').enable()
						self.get_elem('CB_bootable').enable()
						if self.elem_exists('CB_ppcprep'):
							self.get_elem('CB_ppcprep').enable()

						if 'linux-swap' in self.get_elem('SEL_fstype').result():
							self.get_elem('INP_mpoint').disable()
						else:
							self.get_elem('INP_mpoint').enable()
						if self.current == self.get_elem_id('INP_mpoint'):
							self.get_elem('INP_mpoint').set_on()
							self.get_elem('INP_mpoint').draw()

				elif self.operation == 'create':
					if self.elem_exists('CB_lvmpv') and self.get_elem('CB_lvmpv').result():
						# partition is LVM PV
						self.get_elem('INP_mpoint').disable()
						self.get_elem('SEL_fstype').disable()
						self.get_elem('CB_format').disable()
						self.get_elem('CB_bootable').disable()
						if self.elem_exists('CB_ppcprep'):
							self.get_elem('CB_ppcprep').disable()
					else:
						# partition is no LVM PV
						self.get_elem('INP_mpoint').enable()
						self.get_elem('SEL_fstype').enable()
						self.get_elem('CB_format').enable()
						self.get_elem('CB_bootable').enable()
						if self.elem_exists('CB_ppcprep'):
							self.get_elem('CB_ppcprep').enable()

						if 'linux-swap' in self.get_elem('SEL_fstype').result():
							self.get_elem('INP_mpoint').disable()
						else:
							self.get_elem('INP_mpoint').enable()
					if self.current == self.get_elem_id('INP_mpoint'):
						self.get_elem('INP_mpoint').set_on()
						self.get_elem('INP_mpoint').draw()
				return 1

			def get_result(self):
				pass

			def layout(self):
				dev = self.parent.part_objects[self.parent.get_elem('SEL_part').result()[0]]
				type = dev[0]
				path = dev[1]
				disk=self.parent.container['disk'][path]
				self.operation=''

				if type is 'disk': # got a diskdrive
					self.operation='diskinfo'
					self.add_elem('TXT_1',textline(_('Physical Diskdrive'),self.pos_y+2,self.pos_x+2))#0
					self.add_elem('TXT_2',textline(_('Device: %s') % path,self.pos_y+4,self.pos_x+2))#1
					self.add_elem('TXT_3',textline(_('Size: %s') % disk['size'],self.pos_y+6,self.pos_x+2))#2
					self.add_elem('D1',dummy())#3
					self.add_elem('TXT_4',textline(_('Primary Partitions: %s') % disk[(_('primary'))],self.pos_y+10,self.pos_x+2))#4
					self.add_elem('TXT_5',textline(_('Logical Partitions: %s') % disk[(_('logical'))],self.pos_y+12,self.pos_x+2))#5
					self.add_elem('D2',dummy())#6
					self.add_elem('D3',dummy())#7
					self.add_elem('D4',dummy())#8
					self.add_elem('D5',dummy())#9
					self.add_elem('BT_next',button(_("Next"),self.pos_y+17,self.pos_x+20,15)) #10
					self.add_elem('D6',dummy())#11
					self.current=self.get_elem_id('BT_next')
					self.get_elem_by_id(self.current).set_on()

				elif type is 'part':
					start = dev[2]
					partition=disk['partitions'][start]
					part_type=self.parent.resolve_type(partition['type'])
					if partition['type'] is PARTTYPE_FREESPACE_PRIMARY or partition['type'] is PARTTYPE_FREESPACE_LOGICAL: # got freespace
						self.operation='create'
						self.add_elem('TXT_1', textline(_('New Partition:'),self.pos_y+2,self.pos_x+5)) #0

						self.add_elem('TXT_2', textline(_('Mount point:'),self.pos_y+4,self.pos_x+5)) #1
						self.add_elem('INP_mpoint', input(partition['mpoint'],self.pos_y+4,self.pos_x+6+len(_('Mount point:')),20)) #2
						self.add_elem('TXT_3', textline(_('Size (MB):'),self.pos_y+6,self.pos_x+5)) #3
						self.add_elem('INP_size', input('%s' % int(partition['size']),self.pos_y+6,self.pos_x+6+len(_('Mount point:')),20)) #4
						self.add_elem('TXT_4', textline(_('File system'),self.pos_y+8,self.pos_x+5)) #5

						try:
							file=open('modules/filesystem')
						except:
							file=open('/lib/univention-installer/modules/filesystem')
						dict={}
						filesystem_num=0
						filesystem=file.readlines()
						for line in range(len(filesystem)):
							fs=filesystem[line].split(' ')
							if len(fs) > 1:
								entry = fs[1][:-1]
								dict[entry]=[entry,line]
						file.close()
						self.add_elem('SEL_fstype', select(dict,self.pos_y+9,self.pos_x+4,15,6)) #6
						self.get_elem('SEL_fstype').set_off()
						dict={}
						if self.parent.possible_type(disk, start) is 1:
							dict[_('primary')]=[0, 0]
						elif self.parent.possible_type(disk, start) is 2:
							dict[_('logical')]=[1, 1]
						elif self.parent.possible_type(disk, start) is 3:
							dict[_('primary')]=[0, 0]
							dict[_('logical')]=[1, 1]
						self.add_elem('RB_pri_log', radiobutton(dict,self.pos_y+9,self.pos_x+33,10,2,[0])) #7

						self.add_elem('CB_bootable', checkbox({_('bootable'):'1'},self.pos_y+12,self.pos_x+33,11,1,[])) #8
						if self.parent.parent.cmdline.has_key('architecture') and self.parent.parent.cmdline['architecture'] == 'powerpc':
							self.add_elem('CB_ppcprep', checkbox({_('PPC PreP'):'1'},self.pos_y+13,self.pos_x+33,11,1,[])) #9
						if self.operation == 'create':
							self.add_elem('CB_format', checkbox({_('format'):'1'},self.pos_y+14,self.pos_x+33,14,1,[0])) #10
						else:
							self.add_elem('CB_format', checkbox({_('format'):'1'},self.pos_y+14,self.pos_x+33,14,1,[])) #10
						if self.parent.container['lvm']['enabled']:
							self.add_elem('CB_lvmpv', checkbox({_('LVM PV'):'1'},self.pos_y+15,self.pos_x+33,14,1,[])) #13
						self.add_elem('BT_save', button("F12-"+_("Save"),self.pos_y+17,self.pos_x+(self.width)-4,align="right")) #11
						self.add_elem('BT_cancel', button("ESC-"+_("Cancel"),self.pos_y+17,self.pos_x+4,align="left")) #12

						self.current=self.get_elem_id('INP_mpoint')
						self.get_elem('INP_mpoint').set_on()
					else:  #got a valid partition
						self.operation='edit'
						self.add_elem('TXT_1', textline(_('Partition: %s') % self.parent.dev_to_part(partition,path,type="full"),self.pos_y+2,self.pos_x+5))#0
						if part_type== "primary":
							self.add_elem('TXT_2', textline(_('Typ: primary'),self.pos_y+4,self.pos_x+5))#1
						else:
							self.add_elem('TXT_2', textline(_('Typ: logical'),self.pos_y+4,self.pos_x+5))#1
						self.add_elem('TXT_3', textline(_('Size: %s MB') % int(partition['size']),self.pos_y+4,self.pos_x+33))#2
						self.add_elem('TXT_4', textline(_('File system'),self.pos_y+7,self.pos_x+5)) #3

						try:
							file=open('modules/filesystem')
						except:
							file=open('/lib/univention-installer/modules/filesystem')
						dict={}
						filesystem_num=0
						filesystem=file.readlines()
						for line in range(0, len(filesystem)):
							fs=filesystem[line].split(' ')
							if len(fs) > 1:
								entry = fs[1][:-1]
								dict[entry]=[entry,line]
								if entry == partition['fstype']:
									filesystem_num=line
						file.close()
						self.add_elem('SEL_fstype', select(dict,self.pos_y+8,self.pos_x+4,15,6, filesystem_num)) #4
						self.add_elem('TXT_5', textline(_('Mount point'),self.pos_y+7,self.pos_x+33)) #5
						self.add_elem('INP_mpoint', input(partition['mpoint'],self.pos_y+8,self.pos_x+33,20)) #6
						if 'boot' in partition['flag']:
							self.add_elem('CB_bootable', checkbox({_('bootable'):'1'},self.pos_y+10,self.pos_x+33,11,1,[0])) #7
						else:
							self.add_elem('CB_bootable', checkbox({_('bootable'):'1'},self.pos_y+10,self.pos_x+33,11,1,[])) #7
						if self.parent.parent.cmdline.has_key('architecture') and self.parent.parent.cmdline['architecture'] == 'powerpc':
							if 'prep' in partition['flag']:
								self.add_elem('CB_ppcprep', checkbox({_('PPC PreP'):'1'},self.pos_y+11,self.pos_x+33,11,1,[0])) #9
							else:
								self.add_elem('CB_ppcprep', checkbox({_('PPC PreP'):'1'},self.pos_y+11,self.pos_x+33,11,1,[])) #9
						if partition['format']:
							self.add_elem('CB_format', checkbox({_('format'):'1'},self.pos_y+12,self.pos_x+33,14,1,[0])) #10
						else:
							self.add_elem('CB_format', checkbox({_('format'):'1'},self.pos_y+12,self.pos_x+33,14,1,[])) #10

						self.add_elem('BT_save', button("F12-"+_("Save"),self.pos_y+17,self.pos_x+(self.width)-4,align="right")) #11
						self.add_elem('BT_cancel', button("ESC-"+_("Cancel"),self.pos_y+17,self.pos_x+4,align='left')) #12
						if filesystem_num == 3:
							self.get_elem('INP_mpoint').disable()

		class edit_lvm_lv(subwin):
			def __init__(self,parent,pos_x,pos_y,width,heigth):
				self.close_on_subwin_exit = False
				subwin.__init__(self,parent,pos_x,pos_y,width,heigth)

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
							if self.get_elem('INP_size').result().isdigit():
								size = float(self.get_elem('INP_size').result())
							else:
								size = None
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

							if size == None:
								self.get_elem_by_id(self.current).set_off()
								self.current=self.get_elem_id('INP_size')
								self.get_elem_by_id(self.current).set_on()

								msglist = [ _('Size contains non-digit characters!') ]
								self.sub = msg_win(self,self.pos_y+4,self.pos_x+1,self.width-2,7, msglist)
								self.draw()
								return 1

							currentLE = int(round(size * 1024.0 / vg['PEsize'] + 0.5))
							if currentLE > vg['freePE']:  # decrease logical volume by one physical extent - maybe it fits then
								currentLE -= 1
							if currentLE > vg['freePE']:
								self.get_elem_by_id(self.current).set_off()
								self.current=self.get_elem_id('INP_size')
								self.get_elem_by_id(self.current).set_on()

								msglist = [ _('Not enough free space on volume group!') ]
								self.sub = msg_win(self,self.pos_y+4,self.pos_x+1,self.width-2,7, msglist)
								self.draw()
								return 1
							size = int(vg['PEsize'] * currentLE / 1024.0)

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
				self.operation=''

				if parttype is 'lvm_vg_free':  # FREE SPACE ON VOLUME GROUP
					vg = self.parent.container['lvm']['vg'][ vgname ]
					maxsize = (vg['PEsize'] * vg['freePE'] / 1024)

					lvname_proposal = ''
					for i in range(1,255):
						if not vg['lv'].has_key('vol%d' % i):
							lvname_proposal = 'vol%d' % i
							break

					self.operation='create'
					self.add_elem('TXT_0', textline(_('New logical volume:'),self.pos_y+2,self.pos_x+5)) #0
					self.add_elem('INP_name', input(lvname_proposal,self.pos_y+2,self.pos_x+5+len(_('New logical volume:'))+1,20)) #2
					self.add_elem('TXT_1', textline(_('Mount point:'),self.pos_y+4,self.pos_x+5)) #1
					self.add_elem('INP_mpoint', input('',self.pos_y+4,self.pos_x+5+len(_('Mount point:'))+1,20)) #2
					self.add_elem('TXT_3', textline(_('Size (MB):'),self.pos_y+6,self.pos_x+5)) #3
					self.add_elem('INP_size', input('%s' % int(maxsize),self.pos_y+6,self.pos_x+5+len(_('Mount point:'))+1,20)) #4
					self.add_elem('TXT_5', textline(_('File system'),self.pos_y+8,self.pos_x+5)) #5

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
							if entry != 'linux-swap':   # disable swap on LVM
								dict[entry]=[entry,i]
								i += 1
					file.close()
					self.add_elem('SEL_fstype', select(dict,self.pos_y+9,self.pos_x+4,15,6)) #6
					self.get_elem('SEL_fstype').set_off()

					self.add_elem('CB_format', checkbox({_('format'):'1'},self.pos_y+14,self.pos_x+33,14,1,[0])) #7

					self.add_elem('BT_save', button("F12-"+_("Save"),self.pos_y+17,self.pos_x+(self.width)-4,align="right")) #8
					self.add_elem('BT_cancel', button("ESC-"+_("Cancel"),self.pos_y+17,self.pos_x+4,align="left")) #9

					self.current=self.get_elem_id('INP_name')
					self.get_elem_by_id(self.current).set_on()
				elif parttype is 'lvm_lv':  # EXISTING LOGICAL VOLUME
					lv = self.parent.container['lvm']['vg'][ vgname ]['lv'][ lvname ]
					self.operation='edit'
					self.add_elem('TXT_0', textline(_('LVM Logical Volume: %s') % lvname,self.pos_y+2,self.pos_x+5))#0
					self.add_elem('TXT_2', textline(_('Size: %s MB') % int(lv['size']),self.pos_y+4,self.pos_x+5))#2
					self.add_elem('TXT_3', textline(_('File system'),self.pos_y+7,self.pos_x+5)) #3

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
							if entry != 'linux-swap':   # disable swap on LVM
								dict[entry]=[entry,i]
								if entry == lv['fstype']:
									filesystem_num=i
								i += 1
					file.close()
					self.add_elem('SEL_fstype', select(dict,self.pos_y+8,self.pos_x+4,15,6, filesystem_num)) #4
					self.add_elem('TXT_5', textline(_('Mount point'),self.pos_y+7,self.pos_x+33)) #5
					self.add_elem('INP_mpoint', input(lv['mpoint'],self.pos_y+8,self.pos_x+33,20)) #6

					if lv['format']:
						self.add_elem('CB_format', checkbox({_('format'):'1'},self.pos_y+12,self.pos_x+33,14,1,[0])) #7
					else:
						self.add_elem('CB_format', checkbox({_('format'):'1'},self.pos_y+12,self.pos_x+33,14,1,[])) #7

					self.add_elem('BT_save', button("F12-"+_("Save"),self.pos_y+17,self.pos_x+(self.width)-4,align="right")) #8
					self.add_elem('BT_cancel', button("ESC-"+_("Cancel"),self.pos_y+17,self.pos_x+4,align='left')) #9

		class del_extended(subwin):
			def input(self, key):
				if key in [ 10, 32 ]:
					if self.elements[3].get_status():
						self.parent.part_delete(self.parent.get_elem('SEL_part').result()[0])
						self.parent.layout()
						return 0
					elif self.elements[4].get_status():
						return 0
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
				return 1

			def layout(self):
				message=_('The selected partition is the extended partition of this disc.')
				self.elements.append(textline(message,self.pos_y+2,self.pos_x+2)) #0
				message=_('The extended partition contains all logical partitions.')
				self.elements.append(textline(message,self.pos_y+3,self.pos_x+2)) #1
				message=_('Do you really want to delete all logical partitions?')
				self.elements.append(textline(message,self.pos_y+5,self.pos_x+2)) #2

				self.elements.append(button(_("Yes"),self.pos_y+8,self.pos_x+10,15)) #3
				self.elements.append(button(_("No"),self.pos_y+8,self.pos_x+40,15)) #4
				self.current=4
				self.elements[4].set_on()

			def get_result(self):
				pass

		class resize_extended(subwin):
			def input(self, key):
				if key in [ 10, 32 ]:
					if self.elements[2].get_status():
						if self.elements[2].get_status():
							for disk in self.parent.container['temp'].keys():
								self.parent.parent.debug('resize_extended: disk=%s   temp=%s' % (disk, self.parent.container['temp']))
								part=self.parent.container['temp'][disk][0]
								start=self.parent.container['temp'][disk][1]
								end=self.parent.container['temp'][disk][2]
								self.parent.parent.debug('resize_extended: end=%s  start=%s' % (end, start))
								self.parent.container['disk'][disk]['partitions'][part]['size']=end-start
								self.parent.container['disk'][disk]['partitions'][start]=self.parent.container['disk'][disk]['partitions'][part]
								self.parent.container['history'].append('/sbin/parted --script %s unit chs resize %s %s %s' %
																		(disk,
																		 self.parent.container['disk'][disk]['partitions'][part]['num'],
																		 self.parent.parent.MiB2CHSstr(disk, start),
																		 self.parent.parent.MiB2CHSstr(disk, end)))
								self.parent.parent.debug('COMMAND: /sbin/parted --script %s unit chs resize %s %s %s' %
														 (disk,
														  self.parent.container['disk'][disk]['partitions'][part]['num'],
														  self.parent.parent.MiB2CHSstr(disk, start),
														  self.parent.parent.MiB2CHSstr(disk, end)))
								self.parent.container['disk'][disk]['partitions'].pop(part)
						self.parent.container['temp']={}
						self.parent.rebuild_table(self.parent.container['disk'][disk],disk)
						self.parent.layout()
						return 0
				return 1

			def layout(self):
				message=_('Found over-sized extended partition.')
				self.elements.append(textline(message,self.pos_y+2,self.pos_x+2)) #0
				message=_('This program will resize them to free unused space')
				self.elements.append(textline(message,self.pos_y+3,self.pos_x+2)) #1

				self.elements.append(button(_("OK"),self.pos_y+6,self.pos_x+30,15)) #2
				self.current=2
				self.elements[2].set_on()
			def get_result(self):
				pass

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
