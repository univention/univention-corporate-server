#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: kernel modules detection and loading
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
import time
from objects import *
from local import _

import os, string

KERNEL2_4_MODUL_LIST={}

KERNEL2_6_MODUL_LIST={}

# read kernel modules lists from file
def __read_kernel_modules( version, hash ):
	try:
		mods = open( 'modules/kernel-%s' % version )
	except:
		mods = open( '/lib/univention-installer/modules/kernel-%s' % version )
	num = 0
	for mod in mods.readlines():
		mod = mod[ : -1 ]
		hash[ mod ] = [ mod, num ]
		num += 1
	mods.close()

__read_kernel_modules( '2.4', KERNEL2_4_MODUL_LIST )
__read_kernel_modules( '2.6', KERNEL2_6_MODUL_LIST )

class object(content):
	#def __init__():
	#def std_button():
	#def draw():
	#def help():
	#def tab():
	#def btn_next():
	#def btn_back():

	def checkname(self):
		return ['modules']

	def profile_prerun(self):
		self.start()
		if self.cmdline.has_key('loadmodules') and self.cmdline['loadmodules']:
			for m in self.cmdline['loadmodules'].split(' '):
				if len(m.strip(' ')) > 0:
					self.sub = self.active(self,_('Load modules'),_('Loading module %s' % m))
					self.sub.action='loadmodule'
					self.sub.loadmodule=m
					self.sub.draw()
		for m in self.container['hardware']['kudzu']:
			if self.cmdline.has_key('excludemodule') and self.cmdline['excludemodule']:
				if m in self.cmdline['excludemodule'].split(' '):
					continue
			self.sub = self.active(self,_('Load modules'),_('Loading module %s' % m))
			self.sub.action='loadmodule'
			self.sub.loadmodule=m
			self.sub.draw()
		if os.path.exists('/lib/univention-installer/network.sh'):
			if self.cmdline.has_key('mode'):
				if self.cmdline['mode'] == 'installation':
					os.system('/lib/univention-installer/network.sh >/dev/null')
			else:
				os.system('/lib/univention-installer/network.sh >/dev/null')


	#def run_profiled(self): # this can define a special way when running by profile

	class modules_window(subwin):
		def layout(self):
			selected=[]
			self.elements.append(textline(_('Additional modules to load:'),self.pos_y+1,self.pos_x+2)) #0
			if self.parent.container['kernelversion'].startswith('2.4.'):
				kernel_modules = KERNEL2_4_MODUL_LIST
			elif self.parent.container['kernelversion'].startswith('2.6.'):
				kernel_modules = KERNEL2_6_MODUL_LIST
			for i in self.parent.container['hardware']['local']:
				if i in kernel_modules.keys():
					selected.append( kernel_modules[i][1] )
			self.elements.append(checkbox(kernel_modules, self.pos_y+3,self.pos_x+2, 40, 10, selected )) #1
			self.elements.append(button('F12-'+_("Save"),self.pos_y+15,self.pos_x+(self.width)-4,align="right")) #3
			self.elements.append(button('ESC-'+_("Cancel"),self.pos_y+15,self.pos_x+5,18)) #2
		def modheader(self):
			return _('Modules')
		def input(self, key):
			if key in [ 10, 32, 276 ]:
				if ( self.elements[2].usable() and self.elements[2].get_status() ) or key == 276:
					self.parent.container['hardware']['local']=self.elements[1].result()
					return 0
				if self.elements[3].usable() and self.elements[3].get_status():
					return 0
				if self.current == 1 and key == 32:
					self.elements[self.current].key_event(key)
			elif key == 261 and self.elements[3].get_status():
				self.elements[3].set_off()
				self.elements[3].draw()
				self.elements[2].set_on()
				self.elements[2].draw()
				# move right
			elif key == 260 and self.elements[2].get_status():
				# move left
				self.elements[2].set_off()
				self.elements[2].draw()
				self.elements[3].set_on()
				self.elements[3].draw()
			elif self.elements[self.current].usable():
				self.elements[self.current].key_event(key)
			return 1

	def layout(self):

		self.elements=[]
		self.std_button()
		self.elements.append(textline(_('The following hardware was found:'),self.minY+1,self.minX+2)) #2
		selected=[]
		fixed=[]
		count=0
		tmplist=[]
		hwlist={}
		mustlist={}

		if not self.container['hardware'].has_key('tmp'):
			tmplist=self.container['hardware']['kudzu']
		else:
			tmplist=self.container['hardware']['tmp']

		tmplist.sort()

		tmplist_local = self.container['hardware']['local']
		tmplist_local.sort()
		tmplist+=tmplist_local

		tmplist_profile = self.container['hardware']['profile']
		tmplist_profile.sort()
		tmplist+=tmplist_profile

		for h in range(0,len(tmplist)):
			if hwlist.has_key(tmplist[h]):
				continue
			hwlist[tmplist[h]]=[tmplist[h], count]
			selected.append(count)
			count=count+1

		if self.all_results.has_key('exclude_modules'):
			exmod=self.all_results['exclude_modules'].split()
			for m in range(0,len(exmod)):
				if hwlist.has_key(exmod[m]):
					fixed.append(hwlist[exmod[m]][1])
					selected.remove(hwlist[exmod[m]][1])

		if self.all_results.has_key('include_modules'):
			incmod=self.all_results['include_modules'].split()
			for m in range(0,len(incmod)):
				if hwlist.has_key(incmod[m]):
					fixed.append(hwlist[incmod[m]][1])
					continue
				hwlist[incmod[m]]=[incmod[m],count]
				selected.append(count)
				fixed.append(count)
				count+=1



		self.elements.append(checkbox(hwlist, self.minY+2,self.minX+4, 40, 10, selected,fixed)) #3

		self.elements.append(button(_('Add modules'),self.maxY-1,self.minX+(self.width/2)-2,align="middle")) #4
		self.elements[0].set_off()
		self.current=3
		self.elements[3].set_on()
		self.draw()

	def input(self,key): # return 1 0 -1
		self.debug('key=%d' % key)
		if hasattr(self,"sub"):
			if not self.sub.input(key):
				self.subresult=self.sub.get_result()
				self.sub.exit()
				# save old status
				count=0
				self.container['hardware']['tmp']=[]
				for i in self.elements[3].result():
					if i in self.container['hardware']['kudzu']:
						self.container['hardware']['tmp'].append(i)
				self.layout()
				self.draw()
		elif key in [ 10, 32 ] and self.btn_next():
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		#elif key == 260 and self.btn_next():
		#	first module
		#	self.elements[self.current].set_off()
		#	self.elements[self.current].draw()
		#	self.current=1
		#	self.elements[self.current].set_on()
		#	self.elements[self.current].draw()
		elif key == 261 and self.btn_back():
			self.elements[self.current].set_off()
			self.elements[self.current].draw()
			self.current=0
			self.elements[self.current].set_on()
			self.elements[self.current].draw()

		elif key in [ 10, 32 ] and self.elements[4].get_status():
			self.sub=self.modules_window(self,self.minY,self.minX,self.width-10,self.height-5)
			self.sub.draw()
		else:
			return self.elements[self.current].key_event(key)
		return 1

	def incomplete(self):
		return 0

	def helptext(self): # All about this Modul - '###' creates a newline
		return _('Hardware-Scan \n \n This module automatically detects your hardware setup. \n If your hardware is not listed please choose "Add module" and mark the missing module by using the space key.')

	def modheader(self):
		return _('Hardware-Scan')

	def result(self):
		result={}
		result['modules']="%s"%string.join(self.elements[3].result()," ")
		return result

	def start(self):
		self.action=''
		self.container['hardware']={}
		self.container['hardware']['kudzu']=[]
		self.container['hardware']['local']=[]
		self.container['hardware']['profile']=[]
		if not self.cmdline.has_key('noprobe'):
			if self.all_results.has_key('modules'):
				self.container['hardware']['profile']=self.all_results['modules'].split()
			#if self.all_results.has_key('to_scan') and ("hardware" in self.all_results['to_scan'].split()):
			if self.initialized:
				self.sub = self.active(self,_('Hardware-Scan'),_('Please wait...'))
				self.sub.draw()
		uname=os.popen('/bin/uname -r')
		self.container['kernelversion']=uname.readline().strip()
	def postrun(self):
		f=open('/proc/modules')
		proc_lines=f.readlines()
		f.close()
		if self.cmdline.has_key('extramodules') and self.cmdline['extramodules']:
			for m in self.cmdline['extramodules'].split(' '):
				if len(m.strip(' ')) > 0:
					self.sub = self.active(self,_('Load modules'),_('Loading module %s' % m))
					self.sub.action='loadmodule'
					self.sub.loadmodule=m
					self.sub.draw()
		for m in self.elements[3].result():
			load=1
			for l in proc_lines:
				if self.container['kernelversion'].startswith('2.6'):
					if l.replace('_','-').startswith(m.split('/')[-1]+" "):
						load=0
						break
				elif self.container['kernelversion'].startswith('2.4'):
					if l.startswith(m.split('/')[-1]+" "):
						load=0
						break
			if load:
				if self.cmdline.has_key('excludemodule') and self.cmdline['excludemodule']:
					if m in self.cmdline['excludemodule'].split(' '):
						continue
				self.sub = self.active(self,_('Load modules'),_('Loading module %s' % m))
				self.sub.action='loadmodule'
				self.sub.loadmodule=m
				self.sub.draw()
		if os.path.exists('/lib/univention-installer/network.sh'):
			os.system('/lib/univention-installer/network.sh >/dev/null')


	class active(act_win):
		def _scan_hardware(self):
			if os.path.exists('/usr/sbin/kudzu'):
				res=os.popen('/usr/sbin/kudzu -p')
			elif os.path.exists('/sbin/kudzu'):
				res=os.popen('/sbin/kudzu -p')
			else:
				res=os.popen('cat /dev/null')
			lines=res.readlines()

			kudzu=[]


			start=0
			h = {}
			for line in lines:
				line=line.strip('\n')
				if line == '-' and not start:
					start=1
					h={}
				elif line == '-':
					kudzu.append(h)
					h={}
				else:
					ll=line.split(':',1)
					h[ll[0]]=ll[1]
			# add last entry
			if len( h ):
				kudzu.append( h )

			if self.parent.cmdline['architecture'] == 'powerpc':
				#FIXME: kudzu should find this module
				self.parent.container['hardware']['kudzu'].append("iseries_veth")

			for h in range(0,len(kudzu)):
				if kudzu[h].has_key('driver'):
					driver=kudzu[h]['driver'].strip(' ')
					if driver != 'ignore' and driver != 'unknown' and driver not in kudzu and not driver in ['generic3ps/2']:
						self.parent.container['hardware']['kudzu'].append(driver)

					# FSC Hardware need this hack
					if driver.lower() == "i2o_core":
						#FIXME, should be recommended driver
						if "i2o_block" not in self.parent.container['hardware']['kudzu']:
							self.parent.container['hardware']['kudzu'].append("i2o_block")

			if not self.parent.container['hardware'].has_key('kudzu') or not 'ide-generic' in self.parent.container['hardware']['kudzu']:
				self.parent.container['hardware']['kudzu'].append('ide-generic')
			if not self.parent.container['hardware'].has_key('kudzu') or not 'ide-disk' in self.parent.container['hardware']['kudzu']:
				self.parent.container['hardware']['kudzu'].append('ide-disk')
			if not self.parent.container['hardware'].has_key('kudzu') or not 'sd_mod' in self.parent.container['hardware']['kudzu']:
				self.parent.container['hardware']['kudzu'].append('sd_mod')
			if not self.parent.container['hardware'].has_key('kudzu') or not 'dm-mod' in self.parent.container['hardware']['kudzu']:
				self.parent.container['hardware']['kudzu'].append('dm-mod')
			if self.parent.cmdline.get('recover', False):
				if not self.parent.container['hardware'].has_key('kudzu') or not 'st' in self.parent.container['hardware']['kudzu']:
					self.parent.container['hardware']['kudzu'].append('st')
			#for h in range(0,len(hardware)):
			#	if hardware[h].has_key('desc'):
			#		print hardware[h]['desc']
			#	else:
			#		print 'no desc: %s' % hardware[h]
		def function(self):
			if hasattr(self,'action'):
				if self.action == 'loadmodule':
					os.system('/sbin/modprobe %s >/dev/null 2>&1' % self.loadmodule.split('/')[-1])
					time.sleep(0.5)
				else:
					self._scan_hardware()
			else:
				self._scan_hardware()

			self.stop()
