#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: profile selection
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

import time
import os
import curses
import string
from objects import *
from local import _

class object(content):
	#def std_button():
	#def draw():
	#def help():
	#def tab():
	#def btn_next():
	#def btn_back():

	class profile_password(subwin):
		def layout(self):
			self.elements.append(textline(_('Please enter the password:'),self.pos_y+2,self.pos_x+2))#0
			self.elements.append(password("",self.pos_y+3,self.pos_x+2, 30))#1
			self.elements.append(button(_('Ok'),self.pos_y+5,self.pos_x+8,12)) #2
			self.elements.append(button(_('Cancel'),self.pos_y+5,self.pos_x+(self.width)-8,align="right")) #3
			self.elements[1].set_on()
			self.current=1

		def input(self,key):
			if key in [ 10, 32 ] and self.elements[2].usable() and self.elements[2].get_status(): # Ok
				return 0
			elif key in [ 10, 32 ] and self.elements[3].usable() and self.elements[3].get_status(): #Cancel
				return -1
			elif key == 32:
				return 0
			elif key == 261 and self.elements[2].active:
				#move right
				self.elements[2].set_off()
				self.elements[3].set_on()
				self.current=3
				self.draw()
			elif key == 260 and self.elements[3].active:
				#move left
				self.elements[3].set_off()
				self.elements[2].set_on()
				self.current=2
				self.draw()
			elif self.elements[self.current].usable():
				self.elements[self.current].key_event(key)
			return 1

	def profile_complete(self):
		self.debug('check profile 04_profile')
		if self.check('profile_file'):
			self.debug('profile_file invalid')
			return False
		if hasattr(self, 'view_warning') and self.view_warning == 1:
			if self.cmdline.has_key('profile_file'):
				self.cmdline['profile_file']=""
			if self.all_results.has_key('profile_file'):
				self.all_results['profile_file']=""
			self.view_warning=0
		if (self.cmdline.has_key('profile_file') and self.cmdline['profile_file']) or (self.all_results.has_key('profile_file') and self.all_results['profile_file']):
			self.mount=['',''] #The mountpoint. is set by active [device,mountpoint]
			self.profile={} #Cache the whole profile
			self.debug('profile mode from 04_profile')
			self.media=self.cmdline['profile']
			self.path='/profmnt'
			if self.media == 'floppy':
				self.sub=self.active(self,'Mounting Floppy','','mount','/dev/fd0')
			elif self.media == 'usb':
				usbdev=self.searchusb()
				self.sub=self.active(self,'Mounting USB-Device','','mount',usbdev)
			else:
				if self.all_results.has_key('cdrom_device'):
					cddev=self.all_results['cdrom_device']
				self.debug('cddev: "%s"'%cddev)
				self.path='/profmnt/profiles'
				self.sub=self.active(self,'Mounting CD-Rom','','mount',cddev)
				self.sub.draw()

			self.currentpath=self.path
			if (self.cmdline.has_key('profile_file') and os.path.exists(os.path.join(self.currentpath,self.cmdline['profile_file']))) or (self.all_results.has_key('profile_file') and os.path.exists(os.path.join(self.currentpath,self.all_results['profile_file']))):
				if self.cmdline.has_key('profile_file') and os.path.exists(os.path.join(self.currentpath,self.cmdline['profile_file'])):
					profile=os.path.join(self.currentpath,self.cmdline['profile_file'])
					self.debug('profile mode 1')
				if self.all_results.has_key('profile_file') and os.path.exists(os.path.join(self.currentpath,self.all_results['profile_file'])):
					profile=os.path.join(self.currentpath,self.all_results['profile_file'])
					self.debug('profile mode 2')
				passwd=None
				file=open(profile,'r')
				for line in file.readlines():
					if line.find('=') > -1:
						line=line.strip(' ')
						if not line[0].startswith('#'):
							lline=line.split('=', 1)
							lline[0]=lline[0].strip('\n\'" ')
							lline[1]=lline[1].strip('\n\'" ')
							if lline[0] == "profile_password":
								passwd=lline[1]
				file.close()

				if passwd:
					self.sub=self.profile_password(self,self.minY+2,self.minX+3,self.maxWidth-10,8)
					self.sub.draw()
					stdscr = curses.initscr()
					while 1:
						c = stdscr.getch()

						if c == 9:
							self.tab()
						else:
							res=self.sub.input(c)
							if res < 1:
								break

						self.sub.draw()
					if res == 0:
						pwd=self.sub.elements[1].get_text()
						if pwd == passwd:
							self.sub.exit()
							return True
						else:
							self.sub.exit()
							self.message=_("Wrong password")
							if self.cmdline.has_key('profile_file'):
								self.cmdline['profile_file']=""
							if self.all_results.has_key('profile_file'):
								self.all_results['profile_file']=""
							self.view_warning=1
							return False
					else:
						self.view_warning=1
						return False
			else:
				if self.ignore('profile_file'):
					return True
				return False
		else:
			return False

		return True

	def run_profiled(self):
		#self.mount=['',''] #The mountpoint. is set by active [device,mountpoint]
		#self.profile={} #Cache the whole profile
		#self.debug('profile mode from 04_profile')
		#self.media=self.cmdline['profile']
		#self.path='/profmnt'
		#if self.media == 'floppy':
		#	self.sub=self.active(self,'Mounting Floppy','','mount','/dev/fd0')
		#elif self.media == 'usb':
		#	self.sub=self.active(self,'Initialize USB Devices','','sleep',10)
		#	usbdev=self.searchusb()
		#	self.sub=self.active(self,'Mounting USB-Device','','mount',usbdev)
		#else:
		#	if self.all_results.has_key('cdrom_device'):
		#		cddev=self.all_results['cdrom_device']
		#	self.debug('cddev: "%s"'%cddev)
		#	self.path='/profmnt/profiles'
		#	self.sub=self.active(self,'Mounting CD-Rom','','mount',cddev)
		#	self.sub.draw()

		if not hasattr(self, 'path'):
			return {}

		self.currentpath=self.path
		self.debug('CMD: %s'%self.cmdline)
		if self.cmdline.has_key('profile_file') and os.path.exists(os.path.join(self.currentpath,self.cmdline['profile_file'])):
			self.readprofile(os.path.join(self.currentpath,self.cmdline['profile_file']))
			return self.profile
		elif self.all_results.has_key('profile_file') and os.path.exists(os.path.join(self.currentpath,self.all_results['profile_file'])):
			self.readprofile(os.path.join(self.currentpath,self.all_results['profile_file']))
			return self.profile

	def checkname(self):
		return ['profile']

	def start(self):
		self.profile={} #Cache the whole profile
		# Browser
		self.scaneddir={}
		self.files=[]
		self.mapping=[]
		self.mount=['',''] #The mountpoint. is set by active [device,mountpoint]

		if self.cmdline.has_key('profile'):
			self.media=self.cmdline['profile']
			self.path='/profmnt'
			if self.media == 'floppy':
				self.sub=self.active(self,'Mounting Floppy','','mount','/dev/fd0')
				self.sub.draw()
			elif self.media == 'usb':
				self.sub=self.active(self,'Initialize USB Devices','','sleep',10)
				usbdev=self.searchusb()
				self.sub=self.active(self,'Mounting USB-Device','','mount',usbdev)
				self.sub.draw()
			else:
				if self.all_results.has_key('cdrom_device'):
					cddev=self.all_results['cdrom_device']
					if not cddev.startswith('/dev/'):
						if not cddev.startswith('nfs:') and not cddev.startswith('smbfs:'):
							cddev='/dev/%s' % cddev
				self.debug('cddev: "%s"'%cddev)
				self.path='/profmnt/profiles'
				self.sub=self.active(self,'Mounting CD-Rom','','mount',cddev)
				self.sub.draw()

			self.currentpath=self.path

			self.files=self.formdict(self.listdir(self.path))

	def layout(self):
		status = activity(self.minY+2,self.minX+2,20)

		self.reset_layout()
		self.std_button()
		selected=[]

		if not hasattr(self, 'files'):
			# Profil installation profile_check returned false, need to run def start()
			self.start()

		text='%-32s%18s'%(_('Filename'),_('Size'))#52 zeichen!

		self.elements.append(textline(text,self.pos_y+2,self.pos_x+6)) #2
		self.elements.append(select(self.files,self.pos_y+3,self.pos_x+6,52,17)) #3

		self.elements[self.current].set_off()
		self.current=3
		self.elements[3].set_on()

	def redraw(self):
		self.container['current']=self.current
		self.layout()
		self.elements[self.current].set_off()
		self.current=self.container['current']
		self.elements[self.current].set_on()
		self.draw()

	def input(self,key):
		if hasattr(self,"sub"):
			if not self.sub.input(key):
				self.sub.exit()
				self.redraw()
		elif key in [ 10, 32 ] and self.btn_next():
			if self.elements[3].usable() and self.getfile(self.elements[3].result()[0])[1] == 'DIR':
			#If next is pressed and a dir is choosen in element[3] cd into that dir
				newpath=self.getfile(self.elements[3].result()[0])[0]
				self.cd(newpath)
				pass
			else:
				return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		elif key == 10 and self.elements[3].usable() and self.getfile(self.elements[3].result()[0])[1] == 'DIR':
		#Enter and selected element is a DIR
			newpath=self.getfile(self.elements[3].result()[0])[0]
			self.cd(newpath)
			pass
		elif key == 10 and self.elements[3].usable() and self.getfile(self.elements[3].result()[0])[1] == 'FILE':
		#Enter and selected element is a (Pro)FILE - jump to next
			return 'tab'
		elif key == curses.KEY_DOWN or key == curses.KEY_UP or key == 338 or key == 339: #PG_DN, PG_UP
			self.elements[3].key_event(key)
		elif key == 10 and self.elements[self.current].usable():
			return self.elements[self.current].key_event(key)
		else:
			self.elements[self.current].key_event(key)
		return 1

	def cd(self,dir):
		if dir == '..':
			if self.currentpath == self.path:
				return 0
			if self.currentpath[-1:] == '/':
				self.currentpath=self.currentpath[:-1]
			newpath=self.currentpath[:self.currentpath.rfind('/')]
			if newpath[-1:] == '/':
				newpath=newpath[:-1]
			self.currentpath=newpath
			self.files=self.formdict(self.listdir(newpath))
			self.redraw()
		else:
			newpath=os.path.join(self.currentpath,self.getfile(self.elements[3].result()[0])[0])
			self.currentpath=newpath
			self.files=self.formdict(self.listdir(newpath))
			self.redraw()

	def getfile(self,line):
		for val in self.mapping:
			if val[2] == line:
				return val
		return 0

	def incomplete(self, what=''):
		if not what:
			if self.elements[3].usable() and self.getfile(self.elements[3].result()[0])[1] == 'FILE':
				file=os.path.join(self.currentpath,self.getfile(self.elements[3].result()[0])[0])
				return 0
			else:
				return _('You have to select a Profile.')
		else:
			return what

	def helptext(self): # All about this Modul - '###' creates a newline
		return _('Profile \n \n Select a predefined installation profile or enter the position of your own profile. \n \n Please mark the device with the preconfigured profile. \n  \n Press F2 to add a missing device or F3 to browse for the correct path.')

	def modheader(self):
		return _('Profile')

	def profileheader(self):
		return 'Profile'

	def result(self):
		result={}
		if self.elements[3].usable() and self.getfile(self.elements[3].result()[0])[1] == 'FILE':
			result['profile_file']=os.path.join(self.currentpath,self.getfile(self.elements[3].result()[0])[0])
			tmpprof=self.readprofile(result['profile_file'])
			for key in tmpprof.keys():
				result[key]=tmpprof[key]
		else:
			self.incomplete()
		return result

	def readprofile(self, profile):
		self.debug('profile read')
		file=open(profile,'r')
		self.debug('profile opend')
		for line in file.readlines():
			self.debug('next line')
			if line.find('=') > -1:
				line=line.strip(' ')
				if line[0] != '#':
					lline=line.split('=', 1)
					lline[0]=lline[0].strip('\n\'" ')
					lline[1]=lline[1].strip('\n\'" ')
					self.profile[lline[0]]=lline[1]
		file.close()
		return self.profile

	def searchusb(self):
		self.sub=self.active(self,_('Loading Modules'),'','loadmodule',['usb-storage'])
		self.sub.draw()
		self.sub=self.active(self,_('Initialize USB Devices'),'','sleep',10)
		self.sub.draw()
		usbdev=[]
		uname=os.popen('/bin/uname -r')
		self.container['kernelversion']=uname.readline().strip()

		if os.path.exists('/lib/univention-installer/usb-device.sh'):
			if self.container['kernelversion'].startswith('2.4.'):
				devices=os.popen('/lib/univention-installer/usb-device.sh 2.4')
			else:
				devices=os.popen('/lib/univention-installer/usb-device.sh 2.6')
			for device in devices.readlines():
				usbdev.append('/dev/%s' % device.split(' ')[3].strip())
				usbdev.append('/dev/%s1' % device.split(' ')[3].strip())
		elif os.path.exists('usb-device.sh'):
			if self.container['kernelversion'].startswith('2.4.'):
				devices=os.popen('./usb-device.sh 2.4')
			else:
				devices=os.popen('./usb-device.sh 2.6')
			for device in devices.readlines():
				usbdev.append('/dev/%s' % device.split(' ')[3].strip())
				usbdev.append('/dev/%s1' % device.split(' ')[3].strip())
		return usbdev

	def formdict(self, listdir):
		'''
		Formats return of def listdir to fit select-box output
		Writes all lines to self.mapping for "reverse" getting of selected elements
		Returns a select-box-ready list of files and dirs in path given to def listdir.
		'''
		tmplist=[]
		self.mapping=[]
		count=0
		if not listdir == 0:
			if not self.currentpath == self.path:
				tmplist.append('%-43s%4s %2s'%('..','DIR',''))
				self.mapping.append(['..','DIR',count])
				count+=1
			for line in listdir:
				if line[1] == 'DIR':
					tmplist.append('%-43s%4s %2s'%(line[0],'DIR',''))
				elif line[1] == 'FILE':
					tmplist.append('%-43s%4s %2s'%(line[0],line[2],line[3]))
				self.mapping.append([line[0],line[1],count])
				count+=1
			return tmplist
		else:
			return 0

	def listdir(self, path):
		'''
		Collects file sizes and marks dirs as DIR - files as FILE
		Returns a list of all dirs and files within given path.
		'''
		self.scandir(path)
		tmp=[]
		if self.scaneddir.has_key(path):
			dirs=sorted(self.scaneddir[path][0], key=str.lower)
			files=sorted(self.scaneddir[path][1], key=str.lower)
			if not dirs == []:
				for dir in dirs:
					tmp.append([dir,'DIR'])
			if not files == []:
				for file in files:
					fsize=int(os.stat(os.path.join(path,file))[6])
					entity='b' #Size in bytes
					if fsize >= 1024:
						entity='Kb' #Size in Kbytes
						fsize=fsize/1024
						if fsize >= 1024:
							entity='Mb'
							fsize=fsize/1024 #Size in Mbyte
							if fsize >= 1024:
								entity='Gb'
								fsize=fsize/1024 #Size in Gbyte
					tmp.append([file,'FILE',fsize,entity])
			return tmp
		else:
			return 0

	def scandir(self, path):
		'''
		Scans a whole directory tree.
		Returns a Dics "self.scaneddir". Only used by def listdir
		'''
		self.scaneddir={}
		for root, dirs, files in os.walk(path):
			self.scaneddir[root]=[dirs,files]
		return self.scaneddir

	class active(act_win):
		def __init__(self,parent,header,text,action,data=''):
			if text == '':
				text=_('Please wait...')
			self.action=action
			self.data=data
			act_win.__init__(self,parent,header,text)

		def function(self):
			if self.action == 'loadmodule':
				for module in self.data:
					os.system('/sbin/modprobe %s >/dev/null 2>&1'%module)
					time.sleep(4)
			elif self.action == 'mount':
				if type(self.data) == type([]):
					for d in self.data:
						p='/profmnt/%s' % string.replace(d,'/dev/', '')
						self.parent.debug('mount %s' % p)
						if not os.path.exists(p):
							os.mkdir(p)
						self.parent.debug('/bin/mount %s %s -t vfat >/dev/null 2>&1'%(d,p))
						res=os.system('/bin/mount %s %s -t vfat >/dev/null 2>&1'%(d,p))
						if res != 0:
							self.parent.debug('/bin/mount %s %s >/dev/null 2>&1'%(d,p))
							res=os.system('/bin/mount %s %s >/dev/null 2>&1'%(d,p))
							if res != 0:
								try:
									os.rmdir('%s' % p)
								except:
									pass
					self.parent.mount[0]=self.data
					self.parent.mount[1]='/profmnt'
				else:
					if self.data.startswith('nfs:'):
						res=os.system('/bin/mount -t nfs %s /profmnt >/dev/null 2>&1' % (self.data.replace('nfs:', '')))
						self.parent.debug('Mount /profmnt: "%s"'%res)
					elif self.data.startswith('smbfs:'):
						res=os.system('/bin/mount -t smbfs %s /profmnt >/dev/null 2>&1' % (self.data.replace('smbfs:', '')))
						self.parent.debug('Mount /profmnt: "%s"'%res)
					else:
						res=os.system('/bin/mount %s /profmnt -t vfat >/dev/null 2>&1'%self.data)
						if res != 0:
							#Warning Window - try again without vfat
							res=os.system('/bin/mount %s /profmnt >/dev/null 2>&1'%self.data)
						self.parent.debug('Mount /profmnt: "%s"'%res)
					self.parent.mount[0]=self.data
					self.parent.mount[1]='/profmnt'
				pass
			elif self.action == 'umount':
				if type(self.data) == type([]):
					for d in self.data:
						p='/proofmnt/%s' % string.replace(d, '/dev/', '')
						if os.path.exists(p):
							res=os.system('umount %s >/dev/null 2>&1'%p)
							self.parent.debug('Umount: "%s"'%res)
				else:
					res=os.system('umount %s >/dev/null 2>&1'%self.data)
					self.parent.debug('Umount: "%s"'%res)
					self.parent.mount[1]=''
				pass
			elif self.action == 'sleep':
				time.sleep(self.data)
			self.stop()
