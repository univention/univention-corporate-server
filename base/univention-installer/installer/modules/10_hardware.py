#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: detection of source device
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

import subprocess
import time, os
import re
from objects import *
from local import _

class object(content):
	def __init__(self, max_y, max_x, last, file, cmdline):
		self.cdrom_test=1
		self.auto_input_enabled = True
		self.prepared=0
		content.__init__(self, max_y, max_x, last, file, cmdline)
	#def std_button():
	#def draw():
	#def help():
	#def tab():
	#def btn_next():
	#def btn_back():

	def checkname(self):
		return ['hardware']

	def prepare(self):
		self.debug('==> prepare(%s)' % self.prepared)
		if self.prepared == 1:
			return
		self.prepared=1
		if os.system('/bin/ifconfig | egrep ^[a-z] | egrep -q -v "^lo\b"') == 0:
			self.activate_network=1
			if not self.container.has_key('cdrom_devices'):
				self.container['cdrom_devices']=[]
			if self.cmdline.has_key('nfsserver') and self.cmdline.has_key('nfspath'):
				self.container['cdrom_devices'].append('nfs:%s:%s' % (self.cmdline['nfsserver'], self.cmdline['nfspath']))
			elif self.cmdline.has_key('ip'):
				self.container['cdrom_devices'].append('nfs:%s:/var/lib/univention-repository/' % (self.cmdline['ip'].split(':')[1]))
		else:
			self.activate_network=0

	def profile_prerun(self):
		self.debug('==> profile_prerun')
		if self.cmdline.has_key('nfsserver') and self.cmdline.has_key('nfspath'):
			self.container['cdrom_device']='nfs:%s:%s' % (self.cmdline['nfsserver'], self.cmdline['nfspath'])
		else:
			if self.ignore('cdrom_device'):
				return
			self.sub = self.active(self,_('Searching CD-ROM Drive'),_('Please wait ...'))
			self.sub.action='cdrom-search'
			self.sub.draw()
			self.prepare()
			self.debug('self.container=%s' % self.container)

		if self.ignore('cdrom_device'):
			return

		self.sub = self.active(self,_('Testing CD-ROM Drive'),_('Please wait ...'))
		self.sub.action='cdrom-test-profile'
		self.sub.draw()
		self.debug('self.container=%s' % self.container)

		#prepare cdrom
		self.sub = self.active(self,_('Mounting CD-ROM Drive'),_('Please wait ...'))
		self.sub.action='cdrom-prepare'
		self.sub.draw()
		self.debug('self.container=%s' % self.container)

	def profile_complete(self):
		self.debug('==> profile_complete')
		if self.check('cdrom_device'):
			return False
		if self.container.has_key('cdrom_device') and self.container['cdrom_device']:
			return True
		if self.ignore('cdrom_device'):
			return True
		self.message=_("No valid source found")
		return False

	def run_profiled(self): # this can define a special way when running by profile
		self.debug('==> run_profiled')
		if self.container['cdrom_device'].startswith('nfs') or self.container['cdrom_device'].startswith('smbfs') or self.container['cdrom_device'].startswith('/dev/'):
			return {'cdrom_device': self.container['cdrom_device']}
		else:
			if not self.container['cdrom_device'].startswith('nfs') and not self.container['cdrom_device'].startswith('smbfs'):
				return {'cdrom_device': '/dev/%s' % self.container['cdrom_device']}
			else:
				return {'cdrom_device': self.container['cdrom_device']}


	def layout(self):
		self.debug('==> layout')

		self.prepare()

		status = activity(self.minY+2,self.minX+2,20)

		self.debug('not has_key cdrom_device')
		self.reset_layout()
		self.std_button()
		cds={}
		self.count=0
		append=0
		if not hasattr(self,'selected'):
			self.selected=[]
			append=1

		for cd in self.container['cdrom_devices']:
			cd=cd.replace('/dev/','')
			if cd.startswith('nfs:') or cd.startswith('smbfs:'):
				key = '%s' % cd
			else:
				key = '/dev/%s' % cd
			cds[ key ]=[ key, self.count ]
			if append:
				if not self.count in self.selected:
					self.selected.append(self.count)
			self.count=self.count+1

		self.elements.append(textline(_('Check devices for UCS CD:'),self.minY-11,self.minX+5)) #2
		self.elements.append(checkbox(cds, self.minY-9, self.minX+5, 45, 10, self.selected)) #3
		self.elements.append(button(_('F2-Add'), self.minY+2, self.minX+5, align="left")) #4
		if self.activate_network:
			self.elements.append(button(_('F3-Add'), self.minY+3, self.minX+5, align="left")) #5
		else:
			self.elements.append( dummy() )
		self.elements.append(button(_('F4-Rescan'), self.minY+3+self.activate_network, self.minX+5, align="left")) #6
		self.elements.append(textline(_('CD-ROM Device'), self.minY+2, self.minX+12+len(_('F2-Add')))) #7
		if self.activate_network:
			self.elements.append(textline(_('Network Device'), self.minY+3, self.minX+12+len(_('F2-Add')))) #8
		else:
			self.elements.append( dummy() )

		self.cdrom_test=1


	def postrun(self):
		self.debug('==> postrun(%s)' % self.cdrom_test)
		if self.cdrom_test:
			#test cdrom
			self.sub = self.active(self,_('Testing CD-ROM Drive'),_('Please wait ...'))
			self.sub.action='cdrom-test'
			self.sub.draw()

			#prepare cdrom
			msg=_('Mounting CD-ROM Drive')
			dev=self.container.get('cdrom_device','')
			if dev:
				if ':' in dev:
					msg=_('Mounting Network Device %s') % dev.split('/',1)[0]
				else:
					msg=_('Mounting CD-ROM Drive %s') % dev
				self.sub = self.active(self,msg,_('Please wait ...'))
				self.sub.action='cdrom-prepare'
				self.sub.draw()
			self.cdrom_test=0

			#self.debug('layout again')
			#self.layout()
			#self.draw()

	def auto_input(self):
		# Return "next" (== F12) and disable auto_input() function.
		# This way, only one F12 keypress will be done automatically.
		self.debug('==> auto_input')
		self.auto_input_enabled = False
		return "next"

	def input(self,key): # return 1 0 -1
		self.debug('key=%d' % key)
		if hasattr(self,"sub"):
			if not self.sub.input(key):
				if not self.sub.invalid:
					dev = self.sub.get_devices()
					dev = dev.replace( '/dev/', '' )
					if not dev in self.container['cdrom_devices']:
						self.container['cdrom_devices'].append( dev )
						self.selected=self.elements[3].selected
						self.selected.append(self.count)
						self.count=self.count+1
				self.sub.exit()
				self.layout()
				self.draw()
		elif key in [ 10, 32 ] and self.btn_next():
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		elif (key in [ 10, 32 ] and self.elements[4].get_status()) or key == 266: #cdrom F2
			self.sub = self.added_device(self, self.minY, self.minX+8, 38, 5)
			self.sub.draw()
			pass
		elif self.activate_network and (key in [ 10, 32 ] and self.elements[5].get_status()) or key == 267: #network
			self.sub = self.added_network_device(self, self.minY-2, self.minX+8, 50, 13)
			self.sub.draw()
			pass
		elif (key in [ 10, 32 ] and self.elements[6].get_status()) or key == 268: #rescan
			self.container['cdrom_device']=''
			self.cdrom_test=1
			self.postrun()
			#return 'next'
		else:
			return self.elements[self.current].key_event(key)

	def incomplete(self):
		self.debug('==> incomplete')
		if self.container.has_key('cdrom_device') and self.container['cdrom_device']:
			return 0
		else:
			self.cdrom_test=1
			return _("No valid source found")

	def helptext(self): # All about this Modul - '###' creates a newline
		return _('Detects the source device. \n \n Please select \"Add CD-ROM device\" or \"Add network device\" if the needed device is missing. \n \n Please use "Rescan" if you want to autodetect devices again.')

	def modheader(self):
		return _('Source device')

	def profileheader(self):
		return 'Source device'

	def result(self):
		self.debug('==> result')
		result={}
		if self.container.has_key('cdrom_device'):
			result['cdrom_device']=self.container['cdrom_device']
		return result

	def start(self):
		self.debug('==> start')
		#search cdrom
		self.sub = self.active(self,_('Searching CD-ROM Drive'),_('Please wait ...'))
		self.sub.action='cdrom-search'
		self.sub.draw()


	class added_device(subwin):
		def layout(self):
			self.invalid=0
			self.network=0
			selected=[]
			#self.elements.append(textline(_('Adding cdrom device'),self.pos_y+1,self.pos_x+2)) #0
			self.elements.append(input('/dev/', self.pos_y+1, self.pos_x+3,30))#0
			self.elements.append(button("F12-"+_("Ok"),self.pos_y+3,self.pos_x+22,14)) #1
			self.elements.append(button("ESC-"+_("Cancel"),self.pos_y+3,self.pos_x+3,16)) #2
			self.current=0
			self.elements[self.current].set_on()
		def get_devices(self):
			return self.elements[0].text
		def modheader(self):
			return _('Add CD-ROM device')
		def input(self, key):
			if ( key in [ 10, 32 ] and self.elements[1].usable() and self.elements[1].get_status() ) or key == 276:
				return 0
			elif key in [ 10, 32] and self.elements[2].usable() and self.elements[2].get_status():
				self.invalid=1
				return 0
			elif key == 10 and self.elements[0].get_status():
				return 0
			elif key == 27:
				self.invalid=1
				return 0
			elif self.elements[self.current].usable():
				self.elements[self.current].key_event(key)
			return 1

	class added_network_device(subwin):
		def layout(self):
			self.invalid=0
			selected=[]
			self.network=1
			#self.elements.append(textline(_('Adding network device'),self.pos_y+1,self.pos_x+2)) #0
			self.elements.append(radiobutton({'nfs': ['nfs', 1],'smbfs': ['smbfs', 2]},self.pos_y+1,self.pos_x+3, 10, 2, [1])) #0
			self.elements.append(textline(_('Servername'),self.pos_y+4,self.pos_x+3)) #1
			self.elements.append(input('', self.pos_y+5, self.pos_x+3,40))#2
			self.elements.append(textline(_('Path'),self.pos_y+7,self.pos_x+3)) #3
			self.elements.append(input('/var/lib/univention-repository', self.pos_y+8, self.pos_x+3,40))#4
			self.elements.append(button("F12-"+_("Ok"),self.pos_y+11,self.pos_x+34,14)) #5
			self.elements.append(button("ESC-"+_("Cancel"),self.pos_y+11,self.pos_x+3,16)) #6
			self.current=2
			self.elements[self.current].set_on()
		def get_devices(self):
			return 'nfs:%s:%s' % (self.elements[2].text, self.elements[4].text)
		def modheader(self):
			return _('Adding network device')
		def input(self, key):
			if key in [ 10, 32 ]:
				if self.elements[0].usable():
					self.elements[0].key_event(key)
					pass
				if self.elements[5].usable() and self.elements[5].get_status():
					return 0
				if self.elements[6].usable() and self.elements[6].get_status():
					self.invalid=1
					return 0
				if key == 10 and (self.elements[2].get_status() or self.elements[4].get_status()):
					return 0
				if key == 27:
					self.invalid=1
					return 0
			elif self.elements[self.current].usable():
				self.elements[self.current].key_event(key)
			return 1

	class active(act_win):
		def function(self):
			self.parent.debug('==> %s' % self.action)
			if self.action == 'cdrom-search':
				#Kernel 2.4
				cdrom_devices = set()

				# waiting for drivers
				os.system("udevadm settle || true")


				if os.path.exists('/proc/ide'):
					for f in os.listdir('/proc/ide/'):
						if f.startswith('ide'):
							for ff in os.listdir(os.path.join('/proc/ide/', f)):
								if ff.startswith('hd'):
									k=open(os.path.join('/proc/ide', f, ff, 'media'), 'r')
									l=k.readline()
									if l.startswith('cdrom'):
										device = '/dev/%s' % ff
										if os.path.exists(device):
											cdrom_devices.add(device)
									k.close()

				if os.path.exists('/proc/scsi/scsi'):
					_sre=re.compile('Type:\s*CD-ROM')
					count=0
					f=open('/proc/scsi/scsi', 'r')
					lines=f.readlines()
					for line in lines:
						if _sre.search(line):
							device = '/dev/scd%d' % count
							if os.path.exists(device):
								cdrom_devices.add(device)
							count=count+1

				p = subprocess.Popen( ['find', '/dev', '-type', 'b', '-exec', 'file', '-s', '{}', ';'], stdout=subprocess.PIPE )
				stdout = p.communicate()[0]
				for line in stdout.splitlines():
					self.parent.debug('line=%s' % line)
					if 'filesystem' in line and not 'mounted' in line and not 'unclean' in line:
						device = line.split(':',1)[0]
						self.parent.debug('adding device %s' % device)
						cdrom_devices.add(device)

				# virt
				for i in map(chr, range(ord('a'), ord('z')+1)):
					# xen
					device = '/dev/xvd%s' % i
					if os.path.exists(device):
						cdrom_devices.add(device)
					# virtio
					device = '/dev/vd%s' % i
					if os.path.exists(device):
						cdrom_devices.add(device)

				# defaults
				for device in ('/dev/scd0', '/dev/scd1'):
					if os.path.exists(device):
						cdrom_devices.add(device)

				self.parent.debug('list of devices to test: %s' % cdrom_devices)

				self.parent.container['cdrom_devices'] = list(cdrom_devices)

			elif self.action == 'cdrom-test' or self.action == 'cdrom-test-profile':

				if self.action == 'cdrom-test-profile':
					result_list=self.parent.container['cdrom_devices']
				else:
					result_list=self.parent.elements[3].result()

				self.parent.debug('result_list=%s' % result_list)

				#for dev in self.parent.container['cdrom_devices']:
				for dev in result_list:
					if dev.startswith('nfs:'):
						time.sleep(int(self.parent.cmdline.get('nfsdelay','0')))
						dev=dev.replace('nfs:', '')
						res=os.system('/bin/mount -t nfs %s /mnt -o exec >/dev/null 2>&1' % dev)
						if res == 0:
							if os.path.exists('/mnt/.univention_install'):
								self.parent.container['cdrom_device']='nfs:%s' % dev
					elif dev.startswith('smbfs:'):
						time.sleep(int(self.parent.cmdline.get('nfsdelay','0')))
						dev=dev.replace('smbfs:', '')
						res=os.system('/bin/mount -t smbfs %s /mnt -o exec >/dev/null 2>&1' % dev)
						if res == 0:
							if os.path.exists('/mnt/.univention_install'):
								self.parent.container['cdrom_device']='smbfs:%s' % dev
					else:
						if dev.startswith('/dev'):
							res=os.system('/bin/mount -t iso9660 %s /mnt -o exec >/dev/null 2>&1' % dev)
						else:
							res=os.system('/bin/mount -t iso9660 /dev/%s /mnt -o exec >/dev/null 2>&1' % dev)
						if res == 0:
							if os.path.exists('/mnt/.univention_install'):
								self.parent.container['cdrom_device']=dev
					try:
						os.system('umount /mnt >/dev/null 2>&1')
					except:
						pass

				self.parent.debug('cdrom_device=%s' % self.parent.container.get('cdrom_device','NO DEVICE FOUND'))


			elif self.action == 'cdrom-prepare':
				self.parent.debug('preparing cdrom_device=%s' % self.parent.container.get('cdrom_device','NO DEVICE FOUND'))
				if self.parent.container.has_key('cdrom_device'):
					dev=self.parent.container['cdrom_device']
					if dev.startswith('nfs:'):
						dev=dev.replace('nfs:', '')
						res=os.system('/bin/mount -t nfs %s /mnt -o exec >/dev/null 2>&1' % dev)
						if res == 0:
							if os.path.exists('/mnt/.univention_install'):
								self.parent.container['cdrom_device']='nfs:%s' % dev
					elif dev.startswith('smbfs:'):
						dev=dev.replace('smbfs:', '')
						res=os.system('/bin/mount -t smbfs %s /mnt -o exec >/dev/null 2>&1' % dev)
						if res == 0:
							if os.path.exists('/mnt/.univention_install'):
								self.parent.container['cdrom_device']='smbfs:%s' % dev
					else:
						if dev.startswith('/dev'):
							res=os.system('/bin/mount %s /mnt -o exec >/dev/null 2>&1' % dev)
						else:
							res=os.system('/bin/mount /dev/%s /mnt -o exec >/dev/null 2>&1' % dev)
						if res == 0:
							if os.path.exists('/mnt/.univention_install'):
								self.parent.container['cdrom_device']=dev
				if os.path.exists('/mnt/images/runtime.img'):
					os.system('cp /mnt/images/runtime.img /tmp')
					os.mkdir('/tmp/runtime')
					os.system('/bin/mount -o loop /tmp/runtime.img /tmp/runtime')
				# copy additional modules
				for filename in ( 'package_list', 'repository' ):
					if os.path.exists( '/mnt/script/installer/%s.py' % filename ):
						os.remove( '/lib/univention-installer/%s.py' % filename )
						os.system('cp /mnt/script/installer/%s.py /lib/univention-installer/' % filename )
				if os.path.exists('/mnt/script/installer/modules'):
					os.system('cp /mnt/script/installer/modules/*.py /lib/univention-installer/modules/ >/dev/null 2>&1')
				os.system('mkdir -p /usr/share')
				os.system('ln -sf /mnt/keymaps /usr/share/keymaps')

				try:
					os.system('umount /mnt >/dev/null 2>&1')
				except:
					pass

				self.parent.debug('preparing cdrom_device done')

			self.stop()
