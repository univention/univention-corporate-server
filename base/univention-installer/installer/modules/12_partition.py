#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: partition configuration
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

#
# Results of previous modules are placed in self.all_results (dictionary)
# Results of this module need to be stored in the dictionary self.result (variablename:value[,value1,value2])
#

import objects
from objects import *
from local import _
import os, re, string, curses

class object(content):
	def __init__(self,max_y,max_x,last=(1,1), file='/tmp/installer.log', cmdline={}):
		self.written=0
		content.__init__(self,max_y,max_x,last, file, cmdline)

	def checkname(self):
		return ['devices']

	def profile_prerun(self):
		self.start()
		self.container['profile']={}
		self.read_profile()
		return {}

	def profile_complete(self):
		if self.check('partitions') | self.check('partition'):
			return False
		root_device=0
		root_fs=0
		for key in self.container['profile']['create'].keys():
			for minor in self.container['profile']['create'][key].keys():
				fstype=self.container['profile']['create'][key][minor]['fstype']
				mpoint=self.container['profile']['create'][key][minor]['mpoint']
				if mpoint == '/':
					root_device=1
					if fstype in ['xfs','ext2','ext3']:
						root_fs=1
		if not root_device:
			#Missing / as mountpoint
			self.message='Missing / as mountpoint'
			return False
		if not root_fs:
			#Wrong filesystemtype for mountpoint /
			self.message='Wrong filesystemtype for mountpoint /'
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
			return '%sp%d' % (dev_match.group(),number)
		else:
			return '%s%d' % (device,number)
	def run_profiled(self):
		self.act_profile()
		for key in self.container['profile']['create'].keys():
			device=key.lstrip('/').replace('/','_')
			for minor in self.container['profile']['create'][key].keys():
				type=self.container['profile']['create'][key][minor]['type']
				format=self.container['profile']['create'][key][minor]['format']
				fstype=self.container['profile']['create'][key][minor]['fstype']
				start=self.container['profile']['create'][key][minor]['start']
				end=self.container['profile']['create'][key][minor]['end']
				mpoint=self.container['profile']['create'][key][minor]['mpoint']
				dev="%s"%self.get_real_partition_device_name(device,minor)
				self.container['result'][dev]="%s %s %s %s %s %s"%(type,format,fstype,start,end,mpoint)
		return self.container['result']

	def layout(self):
		self.sub=self.partition(self,self.minY-2,self.minX-20,self.maxWidth+20,self.maxHeight+5)
		self.sub.draw()

	def input(self,key):
		return self.sub.input(key)

	def kill_subwin(self):
		#Defined to prevend subwin from killing (module == subwin)
		if hasattr(self.sub, 'sub'):
			self.sub.sub.exit()
		return ""

	def incomplete(self):
		root_device=0
		root_fs=0
		mpoint_temp=[]
		for disk in self.container['disk'].keys():
			for part in self.container['disk'][disk]['partitions']:
				if self.container['disk'][disk]['partitions'][part]['num'] > 0 : # only valid partitions
					if len(self.container['disk'][disk]['partitions'][part]['mpoint'].strip()):
						if self.container['disk'][disk]['partitions'][part]['mpoint'] in mpoint_temp:
							return _('Double Mount-Point \'%s\'') % self.container['disk'][disk]['partitions'][part]['mpoint']
						mpoint_temp.append(self.container['disk'][disk]['partitions'][part]['mpoint'])
					if self.container['disk'][disk]['partitions'][part]['mpoint'] == '/':
						if not self.container['disk'][disk]['partitions'][part]['fstype'] in ['xfs','ext2','ext3']:
							root_fs=self.container['disk'][disk]['partitions'][part]['fstype']
						root_device=1
		if not root_device:
			self.move_focus( 1 )
			return _('Missing \'/\' as mountpoint')

		if root_fs:
			self.move_focus( 1 )
			return _('Wrong filesystemtype \'%s\' for mountpoint \'/\'' % root_fs)

		if len(self.container['history']) or self.test_changes():
			self.sub.sub=self.sub.verify_exit(self.sub,self.sub.minY+(self.sub.maxHeight/8)+2,self.sub.minX+(self.sub.maxWidth/8),self.sub.maxWidth,self.sub.maxHeight-7)
			self.sub.sub.draw()
			return 1

	def profile_f12_run(self):
		# send the F12 key event to the subwindow
		if hasattr(self.sub, 'sub'):
			self.sub.sub.input(276)
			self.sub.sub.exit()
			return 1
		if len(self.container['history']) or self.test_changes():
			self.sub.sub=self.sub.verify_exit(self.sub,self.sub.minY+(self.sub.maxHeight/8)+2,self.sub.minX+(self.sub.maxWidth/8),self.sub.maxWidth,self.sub.maxHeight-7)
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
		return _('Partition')

	def start(self):
		self.container={}
		self.container['min_size']=float(1)
		self.container['debug']=''
		self.container['profile']={}
		self.container['disk']=self.read_devices()
		self.container['history']=[]
		self.container['temp']={}
		self.container['selected']=1

	def read_profile(self):
		self.container['result']={}
		self.container['profile']['empty']=[]
		self.container['profile']['delete']={}
		self.container['profile']['create']={}
		for key in self.all_results.keys():
			if key == 'part_delete':
				delete=self.all_results['part_delete'].replace("'","").split(' ')
				for entry in delete:
					if entry == 'all': # delete all existing partitions
						for disk in self.container['disk'].keys():
							if len(self.container['disk'][disk]['partitions'].keys()):
								self.container['profile']['delete'][disk]=[]
							for part in self.container['disk'][disk]['partitions'].keys():
								if self.container['disk'][disk]['partitions'][part]['num'] > 0:
									self.container['profile']['delete'][disk].append(self.container['disk'][disk]['partitions'][part]['num'])
						self.container['profile']['empty'].append('all')
					elif self.parse_syntax(entry):
						result=self.parse_syntax(entry)
						result[0]=self.get_device_name(result[0])
						if not self.container['profile']['delete'].has_key(result[0]):
							self.container['profile']['delete'][result[0]]=[]
						if not result[1] and self.container['disk'].has_key(result[0]) and len(self.container['disk'][result[0]]['partitions'].keys()): # case delete complete /dev/sda
							for part in self.container['disk'][result[0]]['partitions'].keys():
								self.container['profile']['delete'][result[0]].append(self.container['disk'][result[0]]['partitions'][part]['num'])
							self.container['profile']['empty'].append(result[0])
						else:
							self.container['profile']['delete'][result[0]].append(result[1])

			elif self.parse_syntax(key): # test for matching syntax (dev_sda2, /dev/sda2, etc)
				result=self.parse_syntax(key)
				result[0]=self.get_device_name(result[0])
				if not self.container['profile']['create'].has_key(result[0]):
					self.container['profile']['create'][result[0]]={}
				parms=self.all_results[key].replace("'","").split()
				self.container['result'][key]=''
				if len(parms) >= 5:
					if len(parms) < 6 or parms[5] == 'None' or parms[5] == 'linux-swap':
						mpoint = ''
					else:
						mpoint = parms[5]
					if parms[0] == 'only_mount':
						parms[1]=0
					if result[1] < 5 and result[1] > 0:
						type = 0

					temp={	'type':parms[0],
						'fstype':parms[2],
						'start':parms[3],
						'end':parms[4],
						'mpoint':mpoint,
						'format':parms[1]
						}

					self.debug('Added to create container: [%s]' % temp)
					self.container['profile']['create'][result[0]][result[1]]=temp
				else:
					self.debug('Syntax error for key=[%s]' % key)
					pass


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
		return ["%s"%dev.strip(),num]

	def act_profile(self):
		if not self.written:
			self.act = self.prof_active(self,_('Deleting partitions'),_('Please wait ...'),name='act')
			self.act.action='prof_delete'
			self.act.draw()
			self.act = self.prof_active(self,_('Write partitions'),_('Please wait ...'),name='act')
			self.act.action='prof_write'
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
				return '%sp%d' % (dev_match.group(),number)
			else:
				return '%s%d' % (device,number)

		def function(self):
			if self.action == 'prof_delete':
				for disk in self.parent.container['profile']['delete'].keys():
					num_list=self.parent.container['profile']['delete'][disk]
					num_list.reverse()
					for num in num_list:
						command='/sbin/parted --script %s p rm %s'%(disk,num)
						p=os.popen('%s >>/tmp/installer.log 2>&1'%command)
						p.close()
			elif self.action == 'prof_write':
				for disk in self.parent.container['profile']['create'].keys():
					num_list=self.parent.container['profile']['create'][disk].keys()
					num_list.sort()
					for num in num_list:
						type = self.parent.container['profile']['create'][disk][num]['type']
						fstype = self.parent.container['profile']['create'][disk][num]['fstype']
						start = self.parent.container['profile']['create'][disk][num]['start']
						end = self.parent.container['profile']['create'][disk][num]['end']
						if not fstype or fstype in [ 'None', 'none' ]:
							command='/sbin/PartedCreate -d %s -t %s -s %s -e %s'%(disk,type,start,end)
						else:
							command='/sbin/PartedCreate -d %s -t %s -f %s -s %s -e %s'%(disk,type,fstype,start,end)
						self.parent.debug('run command: %s' % command)
						p=os.popen('%s >>/tmp/installer.log 2>&1'%command)
						p.close()
						if fstype in ['ext2','ext3','vfat','msdos']:
							mkfs_cmd='/sbin/mkfs.%s %s' % (fstype,self.get_real_partition_device_name(disk,num))
						elif fstype == 'xfs':
							mkfs_cmd='/sbin/mkfs.xfs -f %s' % self.get_real_partition_device_name(disk,num)
						elif fstype == 'linux-swap':
							mkfs_cmd='/bin/mkswap %s' % self.get_real_partition_device_name(disk,num)
						self.parent.debug('PARTITION: %s' % mkfs_cmd)
						p=os.popen('%s 2>&1'%mkfs_cmd)
						p.close()

			self.stop()


	def read_devices(self):
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

		devices.sort()

		diskList={}
		_re_warning=re.compile('^Warning: Unable to open .*')
		_re_error=re.compile('^Error: Unable to open .*')
		_re_disk_geometry=re.compile('^Disk geometry for .*')
		devices_remove=[]
		for dev in devices:
			dev=dev.strip()
			p = os.popen('/sbin/parted -s %s unit MB p 2>&1 | grep [a-z]'% dev)

			first_line=p.readline().strip()
			self.debug('fist line: [%s]' % first_line)
			if _re_warning.match(first_line):
				self.debug('Firstline starts with warning')
				self.debug('Remove device: %s' % dev)
				devices_remove.append(dev)
				continue
			elif _re_error.match(first_line):
				os.system('/sbin/install-mbr -f %s' % dev)
				p = os.popen('/sbin/parted %s unit MB p'% dev)
				first_line=p.readline()
				if _re_error.match(first_line):
					self.debug('Firstline starts with error')
					self.debug('Remove device %s' % dev)
					devices_remove.append(dev)
					continue
			if first_line.startswith('Disk '):
				mb_size = int(first_lise.split(' ')[-1].split('MB')[0].split(',')[0])
			else:
				mb_size=1000
			extended=0
			primary=0
			logical=0
			partList={}
			last_end=float(0)
			_re_int=re.compile('^[0-9].*')
			for line in p.readlines():
				line=line.strip()
				if not _re_int.match(line):
					if _re_error.match(line):
						self.debug('Line starts wirh Error: [%s]' % line)
						self.debug('Remove device %s' % dev)
						devices_remove.append(dev)
					continue
				line=line.strip()
				cols=line.split()
				num=cols[0]
				part=dev+cols[0]
				start=float(cols[1].split('MB')[0].replace(',','.'))
				end=float(cols[2].split('MB')[0].replace(',','.'))
				size=end-start
				type=cols[4]
				if type == 'extended':
					ptype=2
					extended=1
					primary+=1
				if type == 'primary':
					ptype=0
					primary+=1
				if type == 'logical':
					ptype=1
					logical+=1

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
				if ( start - last_end) > self.container['min_size']:
					free_start=last_end+float(0.01)
					free_end = start-float(0.01)
					partList[free_start]=self.generate_freespace(free_start,free_end)


				partList[start]={'type':ptype,
						'touched':0,
						'fstype':fstype,
						'size':size,
						'end':end,
						'num':int(num),
						'mpoint':'',
						'flag':flag,
						'format':0
						}
				if type == 'extended':
					last_end=start
				else:
					last_end=end
			if ( mb_size -last_end) > self.container['min_size']:
				free_start=last_end+float(0.01)
				free_end = float(mb_size)
				partList[free_start]=self.generate_freespace(free_start,free_end)
			diskList[dev]={'partitions':partList,
					'primary':primary,
					'extended':extended,
					'logical':logical,
					'size':mb_size
					}

			p.close()
		for d in devices_remove:
			devices.remove(d)
		return diskList


	def scan_extended_size(self):
		for disk in self.container['disk'].keys():
			part_list = self.container['disk'][disk]['partitions'].keys()
			part_list.sort()
			start=float(-1)
			end=float(-1)
			found=0
			found_extended=0
			for part in part_list:
				if self.container['disk'][disk]['partitions'][part]['type'] == 1:
					found=1
					if start < 0:
						start = part
					elif part < start:
						start = part
					if end < part+self.container['disk'][disk]['partitions'][part]['size']:
						end = part+self.container['disk'][disk]['partitions'][part]['size']
				elif self.container['disk'][disk]['partitions'][part]['type'] == 2:
					found_extended=1
					extended_start = part
					extended_end = part+self.container['disk'][disk]['partitions'][part]['size']
			if found and found_extended:
				if extended_start < start-float(0.1):
					self.container['temp'][disk]=[extended_start,start-float(0.1),end]
				elif extended_end > end+float(0.1):
					self.container['temp'][disk]=[extended_start,start+float(0.01),end]



	def generate_freespace(self,start,end):
		return {'type':4,
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
		device="dev_%s"%(disk.replace('/dev/', '').replace('/','_'))
		regex = re.compile(".*c[0-9]d[0-9]*")
		match = re.search(regex,disk)
		if match: # got /dev/cciss/cXdXpX
			device += "p"
		device += "%s"%self.container['disk'][disk]['partitions'][part]['num']
		return device

	def result(self):
		result={}
		device_list=[]
		partitions = []
		for disk in self.container['disk']:
			partitions.append( disk )
			for part in self.container['disk'][disk]['partitions']:
				if self.container['disk'][disk]['partitions'][part]['num'] > 0 : # only valid partitions
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

					device_list.append(device)
					format=self.container['disk'][disk]['partitions'][part]['format']
					start=part
					end=part+self.container['disk'][disk]['partitions'][part]['size']
					type='only_mount'
					if self.container['disk'][disk]['partitions'][part]['touched']:
						type=self.container['disk'][disk]['partitions'][part]['type']
					result[device] = "%s %s %s %sM %sM %s" % (type,format,fstype,start,end,mpoint)
		result[ 'disks' ] = string.join( partitions, ' ')
		return result

	class partition(subwin):

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
			return _(' Partition dialog ')

		def layout(self):
			self.elements=[]
			self.container=self.parent.container
			self.minY=self.parent.minY
			self.minX=self.parent.minX-16
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
			head3=self.get_col(_('Typ'),col3)
			head4=self.get_col(_('Form.'),col4)
			head5=self.get_col(_('Mount-Point'),col5,'l')
			head6=self.get_col(_('Size(MB)'),col6)
			text = '%s %s %s %s %s %s'%(head1,head2,head3,head4,head5,head6)
			self.elements.append(textline(text,self.minY,self.minX+2)) #0

			device=self.container['disk'].keys()
			device.sort()

			dict=[]
			for dev in device:
				disk = self.container['disk'][dev]
				self.rebuild_table(disk,dev)
				path = self.get_col(dev.split('/',2)[-1],col1,'l')
				model = self.get_col('-'*(col2+col3+col4+col5+10),col2+col3+col4+col5+3)
				size = self.get_col('%s'%disk['size'],col6)
				dict.append('%s %s %s' % (path,model,size))

				part_list=self.container['disk'][dev]['partitions'].keys()
				part_list.sort()
				for i in range(len(part_list)):
					part = self.container['disk'][dev]['partitions'][part_list[i]]
					path = self.get_col(' %s' % self.dev_to_part(part, dev),col1,'l')
					format=self.get_col('',col4,'m')
					if part['format']:
						format=self.get_col('X',col4,'m')
					size=self.get_col('%s'%int(part['size']),col6)
					type=self.get_col(part['fstype'],col3)
					if part['fstype']== 'linux-swap':
						type=self.get_col('swap',col3)
					mount=self.get_col(part['mpoint'],col5,'l')
					if part['type'] in [0,1,2]:
						start=('%s' % part_list[i]).split('.')[0]
						end=('%s' % (part_list[i]+part['size'])).split('.')[0]
						area=self.get_col('%s-%s' % (start,end),col2)

					if part['type'] == 0: # PRIMARY
						path = self.get_col(' %s' % self.dev_to_part(part, dev),col1,'l')
					elif part['type'] == 1: # LOGICAL
						path = self.get_col('  %s' % self.dev_to_part(part, dev),col1,'l')
					elif part['type'] == 2: # EXTENDED
						path = self.get_col(' %s' % self.dev_to_part(part, dev),col1,'l')
						type = self.get_col('extended',col3)
					elif part['type'] == 4 or part['type'] == 5: # FREESPACE
						area=self.get_col('',col2)
						mount=self.get_col('',col5,'l')
						if not self.possible_type(self.container['disk'][dev],part_list[i]):
							path = self.get_col(' !!!',col1,'l')
							type = self.get_col(_('unusable'),col3)
						elif self.possible_type(self.container['disk'][dev],part_list[i]) == 2:
							path = self.get_col('  ---',col1,'l')
							type = self.get_col(_('free'),col3)
						elif self.possible_type(self.container['disk'][dev],part_list[i]) == 3 or self.possible_type(self.container['disk'][dev],part_list[i]) == 1:
							path = self.get_col(' ---',col1,'l')
							type = self.get_col(_('free'),col3)
					else:
						area=self.get_col('',col2)
						type=self.get_col(_('unknown'),col3)
						path=self.get_col('---',col1)
					dict.append('%s %s %s %s %s %s'%(path,area,type,format,mount,size))
			self.container['dict']=dict

			self.elements.append(select(dict,self.minY+1,self.minX,self.maxWidth+11,12,self.container['selected'])) #1
			self.elements.append(button(_('F2-Create'),self.minY+14,self.minX,18)) #2
			self.elements.append(button(_('F3-Edit'),self.minY+14,self.minX+(self.width/2)-4,align="middle")) #3
			self.elements.append(button(_('F4-Delete'),self.minY+14,self.minX+(self.width)-7,align="right")) #4

			self.elements.append(button(_('F5-Reset changes'),self.minY+16,self.minX,30)) #5
			self.elements.append(button(_('F6-Write partitions'),self.minY+16,self.minX+(self.width)-37,30)) #6
			self.elements.append(button(_('F11-Back'),self.minY+18,self.minX,30)) #7
			self.elements.append(button(_('F12-Next'),self.minY+18,self.minX+(self.width)-37,30)) #8
			if self.startIt:
				self.parent.scan_extended_size()
				self.parent.debug('SCAN_EXT: %s' % self.container['temp'])
				if len(self.container['temp'].keys()):
					self.sub=self.resize_extended(self,self.minY+4,self.minX-2,self.maxWidth+16,self.maxHeight-8)
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
			return _('UCS-Partition-Tool \n \n This tool is designed for creating, editing and deleting partitions during the installation. \n \n Use \"F2-Create\" to add a new partition. \n \n Use \"F3-Edit\" to configure an already existing partition. \n \n Use \"F4-Delete\" to remove a partition. \n \n Use the \"Reset changes\" button to cancel your changes to the partition table. \n \n Use the \"Write Partitions\" button to create and/or format your partitions.')

		def input(self,key):
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
			elif not len(self.elements[1].list) and key in [ 10, 32, 276 ]:
				if self.elements[5].get_status():#reset changes
					self.parent.start()
					self.parent.layout()
					self.elements[self.current].set_on()
					self.elements[1].set_off()
					if hasattr(self,"sub"):
						self.sub.draw()
				elif self.elements[7].get_status():#back
					return 'prev'
				elif self.elements[8].get_status() or key == 276:#next
					if len(self.container['history']) or self.parent.test_changes():
						self.sub=self.verify_exit(self,self.minY+(self.maxHeight/8)+2,self.minX+(self.maxWidth/8),self.maxWidth,self.maxHeight-7)
						self.sub.draw()
					else:
						return 'next'

			elif key == 260:
				#move left
				active=0
				if  self.elements[3].active:
					active=3
				elif  self.elements[4].active:
					active=4
				elif  self.elements[5].active:
					active=5
				elif  self.elements[6].active:
					active=6
				elif  self.elements[7].active:
					active=7
				elif  self.elements[8].active:
					active=8
				if active:
					self.elements[active].set_off()
					self.elements[active-1].set_on()
					self.current=active-1
					self.draw()
			elif key == 261:
				#move right
				active=0
				if  self.elements[2].active:
					active=2
				elif  self.elements[3].active:
					active=3
				elif  self.elements[4].active:
					active=4
				elif  self.elements[5].active:
					active=5
				elif  self.elements[6].active:
					active=6
				elif  self.elements[7].active:
					active=7
				if active:
					self.elements[active].set_off()
					self.elements[active+1].set_on()
					self.current=active+1
					self.draw()

			elif len(self.elements[1].result()) > 0:
				selected = self.resolve_part(self.elements[1].result()[0])
				self.parent.debug('partition: selected=[%s]' % selected)
				self.container['selected']=self.elements[1].result()[0]
				disk=selected[1]
				part=''
				type=''
				if selected[0] == 'part':
					part=selected[2]
					type = self.container['disk'][disk]['partitions'][part]['type']

				if key == 266:# F2 - Create
					self.parent.debug('partition: create')
					if self.resolve_type(type) is 'free' and self.possible_type(self.container['disk'][disk],part):
						self.parent.debug('partition: create!')
						self.sub=self.edit(self,self.minY-1,self.minX+4,self.maxWidth,self.maxHeight+3)
						self.sub.draw()
				elif key == 267:# F3 - Edit
					self.parent.debug('partition: edit')
					if self.resolve_type(type) == 'primary' or self.resolve_type(type) == 'logical':
						self.parent.debug('partition: edit!')
						self.sub=self.edit(self,self.minY-1,self.minX+4,self.maxWidth,self.maxHeight+3)
						self.sub.draw()
				elif key == 268:# F4 - Delete
					self.parent.debug('partition: delete')
					if type == 0 or type == 1:
						self.parent.debug('partition: delete!')
						self.part_delete(self.elements[1].result()[0])
					elif type == 2:
						self.sub=self.del_extended(self,self.minY+4,self.minX-2,self.maxWidth+16,self.maxHeight-5)
						self.sub.draw()

				elif key == 269:# F5 - Reset changes
					self.parent.start()
					self.parent.layout()
					self.elements[self.current].set_on()
					self.elements[1].set_off()
					if hasattr(self,"sub"):
						self.sub.draw()
				elif key == 270:# F6 - Write Partitions
					self.sub=self.verify(self,self.minY+(self.maxHeight/8),self.minX+(self.maxWidth/8),self.maxWidth,self.maxHeight-7)
					self.sub.draw()

				elif key == 276:
					if len(self.container['history']) or self.parent.test_changes():
						self.sub=self.verify_exit(self,self.minY+(self.maxHeight/8)+2,self.minX+(self.maxWidth/8),self.maxWidth,self.maxHeight-7)
						self.sub.draw()
					else:
						return 'next'
				elif key in [ 10, 32 ]:
					if self.elements[1].get_status():
						if self.resolve_type(type) == 'extended':
							pass
						elif disk or part and self.possible_type(self.container['disk'][disk],part): #select
							if self.resolve_type(type) in ['primary', 'logical']:
								self.sub=self.edit(self,self.minY-1,self.minX+4,self.maxWidth,self.maxHeight+3)
								self.sub.draw()
					elif self.elements[2].get_status():#create
						if self.resolve_type(type) is 'free' and self.possible_type(self.container['disk'][disk],part):
							self.sub=self.edit(self,self.minY-1,self.minX+4,self.maxWidth,self.maxHeight+3)
							self.sub.draw()
					elif self.elements[3].get_status():#edit
						if self.resolve_type(type) == 'primary' or self.resolve_type(type) == 'logical':
							self.sub=self.edit(self,self.minY-1,self.minX+4,self.maxWidth,self.maxHeight+3)
							self.sub.draw()
					elif self.elements[4].get_status():#delete
						if type == 0 or type == 1:
							self.part_delete(self.elements[1].result()[0])
						elif type == 2:
							self.sub=self.del_extended(self,self.minY+4,self.minX-2,self.maxWidth+16,self.maxHeight-5)
							self.sub.draw()
					elif self.elements[5].get_status():#reset changes
						self.parent.start()
						self.parent.layout()
						self.elements[self.current].set_on()
						self.elements[1].set_off()
						if hasattr(self,"sub"):
							self.sub.draw()
					elif self.elements[6].get_status():#write changes
						self.sub=self.verify(self,self.minY+(self.maxHeight/8),self.minX+(self.maxWidth/8),self.maxWidth,self.maxHeight-7)
						self.sub.draw()
					elif self.elements[7].get_status():#back
						return 'prev'
					elif self.elements[8].get_status():#next
						if len(self.container['history']) or self.parent.test_changes():
							self.sub=self.verify_exit(self,self.minY+(self.maxHeight/8)+2,self.minX+(self.maxWidth/8),self.maxWidth,self.maxHeight-7)
							self.sub.draw()
						else:
							return 'next'
					elif key == 10 and self.elements[self.current].usable():
						return self.elements[self.current].key_event(key)
				elif key == curses.KEY_DOWN or key == curses.KEY_UP:
					self.elements[1].key_event(key)
				else:
					self.elements[self.current].key_event(key)
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
		def part_delete(self,index):
			result=self.resolve_part(index)
			disk = result[1]
			part_list = self.container['disk'][disk]['partitions'].keys()
			part_list.sort()
			type=self.container['disk'][disk]['partitions'][result[2]]['type']
			if type is 0:#primary
				self.container['history'].append('/sbin/parted --script %s rm %s' % (disk,self.container['disk'][disk]['partitions'][result[2]]['num']))
				self.container['disk'][disk]['partitions'][result[2]]['type']=4
				self.container['disk'][disk]['partitions'][result[2]]['touched']=1
				self.container['disk'][disk]['partitions'][result[2]]['format']=0
				self.container['disk'][disk]['partitions'][result[2]]['mpoint']=''
				self.container['disk'][disk]['partitions'][result[2]]['num']=-1
				self.container['disk'][disk]['primary']-=1
			elif type is 1:#logical
				deleted=self.container['disk'][disk]['partitions'][result[2]]['num']
				self.container['history'].append('/sbin/parted --script %s rm %s' % (disk,self.container['disk'][disk]['partitions'][result[2]]['num']))
				self.container['disk'][disk]['partitions'][result[2]]['type']=5
				self.container['disk'][disk]['partitions'][result[2]]['touched']=1
				self.container['disk'][disk]['partitions'][result[2]]['format']=0
				self.container['disk'][disk]['partitions'][result[2]]['mpoint']=''
				self.container['disk'][disk]['partitions'][result[2]]['num']=-1
				count=0
				for part in self.container['disk'][disk]['partitions'].keys():
					if self.container['disk'][disk]['partitions'][part]['type'] is 1:
						count += 1
					if self.container['disk'][disk]['partitions'][part]['type'] is 2:
						extended=part
				if not count and extended: # empty extended
					self.container['history'].append('/sbin/parted --script %s rm %s' % (disk,self.container['disk'][disk]['partitions'][extended]['num']))
					self.container['disk'][disk]['extended']=0
					self.container['disk'][disk]['primary']-=1
					self.container['disk'][disk]['partitions'][extended]['type']=4
					self.container['disk'][disk]['partitions'][extended]['touched']=1
					self.container['disk'][disk]['partitions'][result[2]]['num']=-1
				self.container['disk'][disk]['logical']-=1
				self.container['disk'][disk] = self.renum_logical(self.container['disk'][disk],deleted)


			elif type is 2:#extended
				self.container['disk'][disk]['extended']=0
				self.container['disk'][disk]['primary']-=1
				self.container['disk'][disk]['partitions'][result[2]]['type']=4
				self.container['disk'][disk]['partitions'][result[2]]['touched']=1
				for part in self.container['disk'][disk]['partitions'].keys():
					if self.container['disk'][disk]['partitions'][part]['type'] is 1:
						self.container['history'].append('/sbin/parted --script %s rm %s' % (disk,self.container['disk'][disk]['partitions'][part]['num']))
						self.container['disk'][disk]['partitions'][part]['type']=5
						self.container['disk'][disk]['partitions'][part]['touched']=1
						self.container['disk'][disk]['logical']-=1
				self.container['history'].append('/sbin/parted --script %s rm %s' % (disk,self.container['disk'][disk]['partitions'][result[2]]['num']))
				self.container['disk'][disk]['partitions'][result[2]]['num']=-1

			if type is 1:
				self.minimize_extended(disk)
			self.container['disk'][disk]=self.rebuild_table(self.container['disk'][disk],disk)
			self.layout()
			self.draw()

		def part_create(self,index,mpoint,size,fstype,type,flag,format,end=0):
			result=self.resolve_part(index)
			disk = result[1]
			part_list = self.container['disk'][disk]['partitions'].keys()
			part_list.sort()
			old_size=self.container['disk'][disk]['partitions'][result[2]]['size']
			old_type=self.container['disk'][disk]['partitions'][result[2]]['type']
			old_sectors=self.container['disk'][disk]['partitions'][result[2]]['size']
			new_sectors=size
			if type is 0 or type is 1: #create new primary/logical disk
				current=result[2]
				if type is 1: # need to modify/create extended
					if not self.container['disk'][disk]['extended']: #create extended
						size=new_sectors+float(0.01)
						self.container['disk'][disk]['partitions'][result[2]]['size']=size
						self.container['disk'][disk]['partitions'][result[2]]['touched']=1
						self.container['disk'][disk]['partitions'][result[2]]['mpoint']=''
						self.container['disk'][disk]['partitions'][result[2]]['fstype']=''
						self.container['disk'][disk]['partitions'][result[2]]['flag']=[]
						self.container['disk'][disk]['partitions'][result[2]]['format']=0
						self.container['disk'][disk]['partitions'][result[2]]['type']=2
						self.container['disk'][disk]['partitions'][result[2]]['num']=0
						self.container['disk'][disk]['primary']+=1
						self.container['disk'][disk]['extended']=1
						self.container['history'].append('/sbin/parted --script %s mkpart %s %s %s' % (disk,self.resolve_type(2),result[2],result[2]+size))
						current += float(0.01)
						size -= float(0.01)

					else: # resize extended
						for part in self.container['disk'][disk]['partitions'].keys():
							if self.container['disk'][disk]['partitions'][part]['type'] == 2:
								break #found extended leaving loop
						if (part + self.container['disk'][disk]['partitions'][part]['size']) < result[2]+1:
							self.container['disk'][disk]['partitions'][part]['size']+=new_sectors
							self.container['disk'][disk]['partitions'][part]['touched']=1
							self.container['history'].append('/sbin/parted --script %s resize %s %s %s' % (disk,self.container['disk'][disk]['partitions'][part]['num'],part,part+self.container['disk'][disk]['partitions'][part]['size']))
							size -= float(0.01)
						elif part > result[2]:
							self.container['disk'][disk]['partitions'][part]['size']+=(part-result[2])
							self.container['disk'][disk]['partitions'][result[2]]=self.container['disk'][disk]['partitions'][part]
							self.container['disk'][disk]['partitions'][result[2]]['touched']=1
							self.container['disk'][disk]['partitions'].pop(part)
							self.container['history'].append('/sbin/parted --script %s resize %s %s %s' % (disk,self.container['disk'][disk]['partitions'][result[2]]['num'],result[2],result[2]+self.container['disk'][disk]['partitions'][result[2]]['size']))
							current += float(0.01)
							size -= float(0.01)

				if not self.container['disk'][disk]['partitions'].has_key(current):
					self.container['disk'][disk]['partitions'][current]={}
				self.container['disk'][disk]['partitions'][current]['touched']=1
				if len(mpoint) > 0 and not mpoint.startswith('/'):
					mpoint='/%s' % mpoint
				self.container['disk'][disk]['partitions'][current]['mpoint']=mpoint
				self.container['disk'][disk]['partitions'][current]['fstype']=fstype
				self.container['disk'][disk]['partitions'][current]['flag']=flag
				self.container['disk'][disk]['partitions'][current]['format']=format
				self.container['disk'][disk]['partitions'][current]['type']=type
				self.container['disk'][disk]['partitions'][current]['num']=0
				self.container['disk'][disk]['partitions'][current]['size']=new_sectors
				self.container['history'].append('/sbin/parted --script %s mkpart %s %s %s' % (disk,self.resolve_type(type),current,current+size))
				if type is 0:
					self.container['disk'][disk]['primary']+=1
				if not (old_size - size) < self.container['min_size']:
					self.container['disk'][disk]['partitions'][current]['size']=new_sectors
					if not end: #start at first sector of freespace
						new_free=current+new_sectors
					else: # new partition at the end of freespace
						self.container['disk'][disk]['partitions'][current+old_sectors-newsectors]=self.container['disk'][disk]['partitions'][current]
						new_free=current
					self.container['disk'][disk]['partitions'][new_free]={}
					self.container['disk'][disk]['partitions'][new_free]['touched']=1
					self.container['disk'][disk]['partitions'][new_free]['size']=old_sectors-new_sectors
					self.container['disk'][disk]['partitions'][new_free]['mpoint']=''
					self.container['disk'][disk]['partitions'][new_free]['fstype']=''
					self.container['disk'][disk]['partitions'][new_free]['flag']=[]
					self.container['disk'][disk]['partitions'][new_free]['format']=0
					self.container['disk'][disk]['partitions'][new_free]['type']=4
					self.container['disk'][disk]['partitions'][new_free]['num']=-1 #temporary wrong num
				if type is 1:
					self.minimize_extended(disk)
				self.rebuild_table( self.container['disk'][disk],disk)

				for f in flag:
					self.container['history'].append('/sbin/parted --script %s set %d %s on' % (disk,self.container['disk'][disk]['partitions'][current]['num'],f))
				self.parent.debug("history\n")
				for h in self.container['history']:
					self.parent.debug(h)




		def minimize_extended(self, disk):
			self.parent.debug('### minimize: %s'%disk)
			new_start=float(-1)
			start=new_start
			new_end=float(-1)
			end=new_end
			part_list=self.container['disk'][disk]['partitions'].keys()
			part_list.sort()
			for part in part_list:
				# check all logical parts and find minimum size for extended
				if self.container['disk'][disk]['partitions'][part]['type'] == 1:
					if new_end > 0:
						new_end=part+self.container['disk'][disk]['partitions'][part]['size']
					if new_start < 0 or part < new_start:
						new_start = part
					if new_end < 0 or new_end < part+self.container['disk'][disk]['partitions'][part]['size']:
						new_end = part+self.container['disk'][disk]['partitions'][part]['size']
				elif self.container['disk'][disk]['partitions'][part]['type'] == 2:
					start = part
					end=start+self.container['disk'][disk]['partitions'][part]['size']
			new_start -= float(0.01)
			if self.container['disk'][disk]['partitions'].has_key(start):
				if new_start > start:
					self.parent.debug('### minimize at start: %s'%[new_start,start])
					self.container['disk'][disk]['partitions'][start]['size']=end-new_start
					self.container['disk'][disk]['partitions'][new_start]=self.container['disk'][disk]['partitions'][start]
					self.container['history'].append('/sbin/parted --script %s resize %s %s %s; #1' % (disk,self.container['disk'][disk]['partitions'][start]['num'],new_start,new_end))
					self.container['disk'][disk]['partitions'].pop(start)
				elif new_end > end:
					self.parent.debug('### minimize at end: %s'%[new_end,end])
					self.container['disk'][disk]['partitions'][part_list[-1]]['type']=5
					self.container['disk'][disk]['partitions'][part_list[-1]]['num']=-1
					self.container['history'].append('/sbin/parted --script %s resize %s %s %s' % (disk,self.container['disk'][disk]['partitions'][start]['num'],start,new_end))


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
				if current_type == 0 or current_type == 2: # Copy primary
					#need to find next number for primary
					if old[part[i]]['num'] == 0:
						new_primary=part[i]
					else:
						primary.remove(int(old[part[i]]['num']))
					if current_type == 2:
						extended=part[i]
				if i > 0:
					previous_type=new[last_new]['type']
					if (previous_type == 4 and current_type == 4) or (previous_type == 5 and current_type == 5) or (previous_type == 4 and current_type == 5): # found freespace next to freespace -> merge
						new[last_new]['size']= (part[i] + old[part[i]]['size']) - last_new
					elif previous_type == 5 and current_type == 4:
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
					elif previous_type == 2 and current_type == 5 and not i == 1 and disc['partitions'][part[i-2]]['type'] == 4:
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

					elif previous_type == 2 and current_type == 5:
						old[part[i-1]]['size']-=old[part[i]]['size']
						new_start=part[i]
						new_end=new_start+old[part[i-1]]['size']
						new[new_start]=old[part[i-1]]
						self.container['history'].append('/sbin/parted --script %s resize %s %s %s' % (device,old[part[i-1]]['num'],new_start,new_end))
						new[part[i-1]]=old[part[i]]
						redo=1

					elif current_type == 2 and previous_type == 1:
						# new logical in front of extend found - need to resize extended
						old[part[i]]['size']+=old[part[i-1]]['size']
						new[last_new]=old[part[i]]
						new[last_new]['touched']=1
						old[part[i-1]]['size']-=1
						new[last_new+1]=old[part[i-1]]
						new[last_new+1]['touched']=1
						last_new+=1

					elif current_type == 1:
						# Copy logical and correct number
						if not old[part[i]]['num']:
							disc['logical']+=1
							old[part[i]]['num']=4+disc['logical']
						new[part[i]]=old[part[i]]
						last_new=part[i]

					elif current_type == 0:
						# Copy primary
						new[part[i]]=old[part[i]]
						last_new=part[i]

					elif current_type == 4 or current_type == 5:
						# Copy Freespace
						new[part[i]]=old[part[i]]
						last_new=part[i]

					elif current_type == 2:
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
				if disk['partitions'][part]['type'] == 1 and disk['partitions'][part]['num'] > deleted:
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
					if len(parts)-1 > current and disk['partitions'][parts[current-1]]['type'] == 1 and disk['partitions'][parts[current+1]]['type'] == 1:
						return 2
					primary=0
					if disk['primary'] < 4:
						primary = 1
					if len(parts)-1 > current and disk['partitions'][parts[current+1]]['type'] == 2:
						return 2+primary
					elif disk['partitions'][parts[current-1]]['type'] == 1:
						return 2+primary
					else:
						return 0+primary

				elif disk['primary'] < 4:
					return 3
				else:
					return 0
			else:
				return 3



		def resolve_type(self,type):
			if type is 0: # PRIMARY
				return 'primary'
			elif type is 1: # LOGICAL
				return 'logical'
			elif type is 2: # EXTENDED
				return 'extended'
			elif type is 4 or type is 5: # FREESPACE
				return 'free'
			elif type is 8 or type is 9:
				return 'meta'
			else:
				return 'unkown'

		def get_result(self):
			pass

		def write_devices(self):
			self.draw()
			self.act = self.active(self,_('Write partitions'),_('Please wait ...'),name='act')
			self.act.action='create_partitions'
			self.act.draw()
			self.act = self.active(self,_('Create Filesystems'),_('Please wait ...'),name='act')
			self.act.action='make_filesystem'
			self.act.draw()
			self.draw()

		class active(act_win):
			def __init__(self,parent,header,text,name='act'):
				self.pos_x=parent.minX+(parent.maxWidth/2)-15
				self.pos_y=parent.minY+5
				act_win.__init__(self,parent,header,text,name)

			def function(self):
				if self.action == 'create_partitions':
					self.parent.parent.debug('Partition: Create Partitions')
					for command in self.parent.container['history']:
						p=os.popen('%s 2>&1'%command)
						self.parent.parent.debug('PARTITION: %s'%command)
						p.close()
					self.parent.container['history']=[]
					self.parent.parent.written=1
				elif self.action == 'make_filesystem':
					self.parent.parent.debug('Partition: Create Filesystem')
					for disk in self.parent.container['disk'].keys():
						for part in self.parent.container['disk'][disk]['partitions'].keys():
							if self.parent.container['disk'][disk]['partitions'][part]['format']:
								device="/%s"%self.parent.parent.get_device(disk, part).replace("_","/")
								fstype=self.parent.container['disk'][disk]['partitions'][part]['fstype']
								if fstype in ['ext2','ext3','vfat','msdos']:
									mkfs_cmd='/sbin/mkfs.%s %s' % (fstype,device)
								elif fstype == 'xfs':
									mkfs_cmd='/sbin/mkfs.xfs -f %s' % device
								elif fstype == 'linux-swap':
									mkfs_cmd='/bin/mkswap %s' % device
								p=os.popen('%s 2>&1'%mkfs_cmd)
								self.parent.parent.debug('PARTITION: %s' % mkfs_cmd)
								p.close()
								self.parent.container['disk'][disk]['partitions'][part]['format']=0
				self.parent.layout()
				self.stop()

		class edit(subwin):
			def __init__(self,parent,pos_x,pos_y,width,heigth):
				subwin.__init__(self,parent,pos_x,pos_y,width,heigth)

			def helptext(self):
				return self.parent.helptext()

			def input(self, key):
				dev = self.parent.resolve_part(self.parent.elements[1].result()[0])
				type = dev[0]
				path = dev[1]
				disk=self.parent.container['disk'][path]

				if hasattr(self,"sub"):
					if not self.sub.input(key):
						self.parent.layout()
						return 0
				if key == 260 and self.elements[11].active:
					#move left
					self.elements[11].set_off()
					self.elements[12].set_on()
					self.current=12
					self.draw()
				elif key == 261 and self.elements[12].active:
					#move right
					self.elements[12].set_off()
					self.elements[11].set_on()
					self.current=11
					self.draw()
				elif key in [ 10, 32, 276 ]:
					if self.elements[12].usable() and self.elements[12].get_status():
						return 0
					elif ( self.elements[11].usable() and self.elements[11].get_status() ) or key == 276:
						if self.operation is 'create': # Speichern
							part=dev[2]
							mpoint=self.elements[2].result()
							if self.elements[4].result().isdigit():
								size=float(self.elements[4].result())
							else:
								return 1
							fstype=self.elements[6].result()[0]
							type=int(self.elements[7].result())
							if disk['partitions'][part]['size'] < size:
								size=disk['partitions'][part]['size']
							flag=['']
							if self.elements[8].result():
								flag.append('boot')
							if self.elements[9].result():
								flag.append('prep')
								flag.append('boot')

							if fstype == 'linux-swap':
								mpoint=''
							if len(mpoint) > 0 and not mpoint.startswith('/'):
								mpoint='/%s' % mpoint
							self.parent.container['temp']={'selected':self.parent.elements[1].result()[0],
										'mpoint':mpoint,
										'size':size,
										'fstype':fstype,
										'type':type,
										'flag':flag,
										}

							self.parent.parent.debug('checkbox selected=%s' % self.elements[10].selected)
							if not self.elements[10].result():
								self.sub=self.parent.no_format(self,self.pos_y+4,self.pos_x+1,self.width-2,self.height-8)
								self.sub.draw()
								return 1
							else:
								self.parent.container['temp']={}
								format=1

							num=0 # temporary zero
							self.parent.part_create(self.parent.elements[1].result()[0],mpoint,size,fstype,type,flag,format)
						elif self.operation is 'edit': # Speichern
							part=dev[2]
							mpoint=self.elements[6].result()
							fstype=self.elements[4].result()[0]
							flag=[]
							if self.elements[7].result():
								flag.append('boot')
							if self.elements[9].result():
								flag.append('prep')
								flag.append('boot')

							self.parent.container['temp']={'fstype':fstype}
							if fstype == 'linux-swap':
								mpoint=''
							if len(mpoint) > 0 and not mpoint.startswith('/'):
								mpoint='/%s' % mpoint
							self.parent.container['disk'][path]['partitions'][part]['mpoint']=mpoint
							#if self.elements[7].result():
							old_flags=self.parent.container['disk'][path]['partitions'][part]['flag']
							for f in old_flags:
								if f not in flag:
									self.parent.container['history'].append('/sbin/parted --script %s set %d %s off' % (path,self.parent.container['disk'][path]['partitions'][part]['num'],f))
							for f in flag:
								if f not in old_flags:
									self.parent.container['history'].append('/sbin/parted --script %s set %d %s on' % (path,self.parent.container['disk'][path]['partitions'][part]['num'],f))

							self.parent.container['disk'][path]['partitions'][part]['flag']=flag

							if self.parent.container['disk'][path]['partitions'][part]['fstype'] != fstype and not self.elements[10].result():
								self.sub=self.parent.no_format(self,self.pos_y+4,self.pos_x+1,self.width-2,self.height-8,0,path,part)
								self.sub.draw()
								return 1
							else:
								self.parent.container['temp']={}
								if self.elements[10].result():
									self.parent.container['disk'][path]['partitions'][part]['format']=1
								else:
									self.parent.container['disk'][path]['partitions'][part]['format']=0

							self.parent.container['disk'][path]['partitions'][part]['fstype']=fstype
						self.parent.container['disk'][path]=self.parent.rebuild_table(disk,path)
						self.parent.layout()
						self.parent.draw()
						return 0
					elif key == 10 and self.elements[self.current].usable():
						return self.elements[self.current].key_event(key)
				if self.elements[self.current].usable():
					self.elements[self.current].key_event(key)
				if self.operation == 'edit':
					if 'linux-swap' in self.elements[4].result():
						self.elements[6].disable()
					else:
						self.elements[6].enable()
					if self.current == 6:
						self.elements[6].set_on()
						self.elements[2].draw()
				elif self.operation == 'create':
					if 'linux-swap' in self.elements[6].result():
						self.elements[2].disable()
					else:
						self.elements[2].enable()
					if self.current == 2:
						self.elements[2].set_on()
						self.elements[2].draw()
				return 1

			def get_result(self):
				pass

			def layout(self):
				dev = self.parent.resolve_part(self.parent.elements[1].result()[0])
				type = dev[0]
				path = dev[1]
				disk=self.parent.container['disk'][path]
				self.operation=''

				if type is 'disk': # got a diskdrive
					self.operation='diskinfo'
					self.elements.append(textline(_('Physical Diskdrive'),self.pos_y+2,self.pos_x+2))#0
					self.elements.append(textline(_('Device: %s' %path),self.pos_y+4,self.pos_x+2))#1
					self.elements.append(textline(_('Size: %s' %disk['size']),self.pos_y+6,self.pos_x+2))#2
					self.elements.append(dummy())#3
					self.elements.append(textline(_('Primary Partitions: %s' %disk[(_('primary'))]),self.pos_y+10,self.pos_x+2))#4
					self.elements.append(textline(_('Logical Partitions: %s' %disk[(_('logical'))]),self.pos_y+12,self.pos_x+2))#5
					self.elements.append(dummy())#6
					self.elements.append(dummy())#7
					self.elements.append(dummy())#8
					self.elements.append(dummy())#9
					self.elements.append(button(_("Next"),self.pos_y+17,self.pos_x+20,15)) #10
					self.elements.append(dummy())#11
					self.current=10
					self.elements[self.current].set_on()


				elif type is 'part':
					start = dev[2]
					partition=disk['partitions'][start]
					part_type=self.parent.resolve_type(partition['type'])
					if partition['type'] is 4 or partition['type'] is 5: # got freespace
						self.operation='create'
						self.elements.append(textline(_('New Partition:'),self.pos_y+2,self.pos_x+5))#0

						self.elements.append(textline(_('Mount-Point'),self.pos_y+4,self.pos_x+5)) #1
						self.elements.append(input(partition['mpoint'],self.pos_y+4,self.pos_x+5+len(_('Mount-Point')),20)) #2
						self.elements.append(textline(_('Size (MB)'),self.pos_y+6,self.pos_x+5)) #3
						self.elements.append(input('%s'%int(partition['size']),self.pos_y+6,self.pos_x+5+len(_('Mount-Point')),20)) #4
						self.elements.append(textline(_('Filesystem'),self.pos_y+8,self.pos_x+5)) #5

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
						self.elements.append(select(dict,self.pos_y+9,self.pos_x+4,15,6)) #6
						self.elements[6].set_off()
						dict={}
						if self.parent.possible_type(disk, start) is 1:
							dict[_('primary')]=[0]
						elif self.parent.possible_type(disk, start) is 2:
							dict[_('logical')]=[1]
						elif self.parent.possible_type(disk, start) is 3:
							dict[_('primary')]=[0]
							dict[_('logical')]=[1]
						self.elements.append(radiobutton(dict,self.pos_y+9,self.pos_x+33,10,2,[0])) #7

						self.elements.append(checkbox({_('bootable'):'1'},self.pos_y+12,self.pos_x+33,11,1,[])) #8
						if self.parent.parent.cmdline.has_key('architecture') and self.parent.parent.cmdline['architecture'] == 'powerpc':
							self.elements.append(checkbox({_('PPC PreP'):'1'},self.pos_y+13,self.pos_x+33,11,1,[])) #9
						else:
							self.elements.append(dummy())#9
						if self.operation == 'create':
							self.elements.append(checkbox({_('format'):'1'},self.pos_y+14,self.pos_x+33,14,1,[0])) #10
						else:
							self.elements.append(checkbox({_('format'):'1'},self.pos_y+14,self.pos_x+33,14,1,[])) #10
						self.elements.append(button("F12-"+_("Save"),self.pos_y+17,self.pos_x+(self.width)-4,align="right")) #11
						self.elements.append(button("ESC-"+_("Cancel"),self.pos_y+17,self.pos_x+4,align="left")) #12
						self.current=2
						self.elements[self.current].set_on()
					else:  #got a valid partition
						self.operation='edit'
						self.elements.append(textline(_('Partition: %s' % self.parent.dev_to_part(partition,path,type="full")),self.pos_y+2,self.pos_x+5))#0
						if part_type== "primary":
							self.elements.append(textline(_('Typ: primary'),self.pos_y+4,self.pos_x+5))#1
						else:
							self.elements.append(textline(_('Typ: logical'),self.pos_y+4,self.pos_x+5))#1
						self.elements.append(textline(_('Size: %s' %partition['size']),self.pos_y+4,self.pos_x+33))#2
						self.elements.append(textline(_('Filesystem'),self.pos_y+7,self.pos_x+5)) #3

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
						self.elements.append(select(dict,self.pos_y+8,self.pos_x+4,15,6, filesystem_num)) #4
						self.elements.append(textline(_('Mount-Point'),self.pos_y+7,self.pos_x+33)) #5
						self.elements.append(input(partition['mpoint'],self.pos_y+8,self.pos_x+33,20)) #6
						if 'boot' in partition['flag']:
							self.elements.append(checkbox({_('bootable'):'1'},self.pos_y+10,self.pos_x+33,11,1,[0])) #7
						else:
							self.elements.append(checkbox({_('bootable'):'1'},self.pos_y+10,self.pos_x+33,11,1,[])) #7
						self.elements.append(dummy())#8
						if self.parent.parent.cmdline.has_key('architecture') and self.parent.parent.cmdline['architecture'] == 'powerpc':
							if 'prep' in partition['flag']:
								self.elements.append(checkbox({_('PPC PreP'):'1'},self.pos_y+11,self.pos_x+33,11,1,[0])) #9
							else:
								self.elements.append(checkbox({_('PPC PreP'):'1'},self.pos_y+11,self.pos_x+33,11,1,[])) #9
						else:
							self.elements.append(dummy())#9
						if partition['format']:
							self.elements.append(checkbox({_('format'):'1'},self.pos_y+12,self.pos_x+33,14,1,[0])) #10
						else:
							self.elements.append(checkbox({_('format'):'1'},self.pos_y+12,self.pos_x+33,14,1,[])) #10
						self.elements.append(button("F12-"+_("Save"),self.pos_y+17,self.pos_x+(self.width)-8,align="right")) #11
						self.elements.append(button("ESC-"+_("Cancel"),self.pos_y+17,self.pos_x+6,15)) #12
						if filesystem_num == 3:
							self.elements[6].disable()

		class del_extended(subwin):
			def input(self, key):
				if key in [ 10, 32 ]:
					if self.elements[3].get_status():
						self.parent.part_delete(self.parent.elements[1].result()[0])
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
								part=self.parent.container['temp'][disk][0]
								start=self.parent.container['temp'][disk][1]
								end=self.parent.container['temp'][disk][2]
								self.parent.container['disk'][disk]['partitions'][part]['size']=end-start
								self.parent.container['disk'][disk]['partitions'][start]=self.parent.container['disk'][disk]['partitions'][part]
								self.parent.container['history'].append('/sbin/parted --script %s resize %s %s %s' % (disk,self.parent.container['disk'][disk]['partitions'][part]['num'],start,end))
								self.parent.parent.debug('COMMAND: /sbin/parted --script %s resize %s %s %s' % (disk,self.parent.container['disk'][disk]['partitions'][part]['num'],start,end))
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

		class no_format(subwin):
			def __init__(self,parent,pos_y,pos_x,width,height, part_create=1,path=0,part=0):
				self.part_create=part_create
				self.path=path
				self.part=part
				subwin.__init__(self,parent,pos_y,pos_x,width,height)

			def input(self, key):
				if key in [ 10, 32 ]:
					if self.part_create:
						selected=self.parent.parent.container['temp']['selected']
						mpoint=self.parent.parent.container['temp']['mpoint']
						size=self.parent.parent.container['temp']['size']
						fstype=self.parent.parent.container['temp']['fstype']
						type=self.parent.parent.container['temp']['type']
						flag=self.parent.parent.container['temp']['flag']
						self.parent.parent.container['temp']={}
						if self.elements[3].get_status():
							format=1
							self.parent.parent.part_create(selected,mpoint,size,fstype,type,flag,format)
							return 0
						elif self.elements[4].get_status():
							format=0
							self.parent.parent.part_create(selected,mpoint,size,fstype,type,flag,format)
							return 0
					else:
						fstype=self.parent.parent.container['temp']['fstype']
						self.parent.parent.container['temp']={}
						if self.elements[3].get_status():
							format=1
						elif self.elements[4].get_status():
							format=0
						self.parent.parent.container['disk'][self.path]['partitions'][self.part]['format']=format
						self.parent.parent.container['disk'][self.path]['partitions'][self.part]['fstype']=fstype
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
				message=_('The select filesystem takes no effect,')
				self.elements.append(textline(message,self.pos_y+2,self.pos_x+2)) #0
				message=_('if format is not selected.')
				self.elements.append(textline(message,self.pos_y+3,self.pos_x+2)) #1
				message=_('Do you want to format this partition')
				self.elements.append(textline(message,self.pos_y+5,self.pos_x+2)) #2

				self.elements.append(button(_("Yes"),self.pos_y+8,self.pos_x+5,15)) #3
				self.elements.append(button(_("No"),self.pos_y+8,self.pos_x+35,15)) #4
				self.current=4
				self.elements[4].set_on()

			def get_result(self):
				pass


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
				self.parent.write_devices()
				return 0
			def _false(self):
				return 0

		class verify_exit(verify):
			def _ok(self):
				self.parent.write_devices()
				return 'next'

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
				self.parent.write_devices()
				return 0

		class wrong_rootfs(subwin):
			def layout(self):
				message=_('Wrong filesystem type for mount-point "/" !')
				self.elements.append(textline(message,self.pos_y+2,self.pos_x+(self.width/2),align="middle")) #0
				message=_('Please choose another filesystem.')
				self.elements.append(textline(message,self.pos_y+4,self.pos_x+(self.width/2),align="middle")) #1

				self.elements.append(button(_("Ok"),self.pos_y+7,self.pos_x+(self.width/2),15,align="middle")) #2
				self.current=3
				self.elements[3].set_on()

			def _ok(self):
				return 0
