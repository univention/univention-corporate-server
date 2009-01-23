#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: software package selection
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
import string
import os
from objects import *
from local import _

NewPackageList = []

class object(content):

	def draw(self):
		if hasattr(self, 'system_role'):
			if self.system_role != self.all_results['system_role']:
				if hasattr(self, 'sub'):
					self.sub.layout()
		content.draw(self)
		if hasattr(self, 'sub'):
			self.sub.draw()

	def profile_complete(self):
		if self.check('components') | self.check('packages'):
			return False
		return True

	def checkname(self):
		return ['components']


	def layout(self):
		# reload(package_list)
		self.debug('layout packages')
		self.sub=self.packages(self,self.minY-2,self.minX-20,self.maxWidth+20,self.maxHeight+5)
		self.sub.draw()
		pass

	def kill_subwin(self):
		#Defined to prevend subwin from killing (module == subwin)
		if hasattr(self.sub, 'sub'):
			self.sub.sub.exit()
		return ""

	def start(self):
		self.sub = self.active(self,_('Preparing Package List'),_('Please wait ...'))
		self.sub.action='preparing-package-list'
		self.sub.draw()

	class active(act_win):
		def function(self):
			if self.action == 'preparing-package-list':
				import package_list
				import repository
				filter = True
				PackagesList = []
				if not ( self.parent.cmdline.has_key('mode') and self.parent.cmdline['mode'] == 'setup' ):
					if self.parent.all_results.has_key('cdrom_device'):
						cdrom_device=self.parent.all_results['cdrom_device']

						if cdrom_device.startswith('nfs:'):
							res = os.system('/bin/mount -t nfs %s /mnt >/dev/null 2>&1' % (cdrom_device.replace('nfs:', '')))
						elif cdrom_device.startswith('smbfs:'):
							res = os.system('/bin/mount -t smbfs %s /profmnt >/dev/null 2>&1' % (cdrom_device.replace('smbfs:', '')))
						else:
							res=os.system('/bin/mount -t iso9660 %s /mnt >/dev/null 2>&1'%cdrom_device)
					major, minor = self.get_first_version()

					repository.get_package_list( PackagesList )
					repository.create_sources_list()
					res=os.system('umount /mnt >/dev/null 2>&1')

				if os.path.exists('/usr/bin/apt-get'):
					res = os.system('apt-get update >/dev/null 2>&1' )
				for i in range(0,len( package_list.PackageList )):
					failed = []
					for j in range(0,len(package_list.PackageList[i]['Packages'])):
						active = False
						if package_list.PackageList[i]['Packages'][j].has_key('Edition'):
							if self.parent.cmdline.has_key('edition'):
								for ea in package_list.PackageList[i]['Packages'][j]['Edition']:
									if ea in self.parent.cmdline['edition']:
										active = True
										break
							else:
								active = True
						else:
							active = True

						if not active:
							failed.append(package_list.PackageList[i]['Packages'][j]['Name'])


						for p in package_list.PackageList[i]['Packages'][j]['Packages']:
							if os.path.exists('/usr/bin/apt-cache'):
								res = os.system('apt-cache show %s >/dev/null 2>&1' % p )
								if res != 0:
									failed.append(package_list.PackageList[i]['Packages'][j]['Name'])
									break
							else:
								if not p in PackagesList and not PackagesList == 'INVALID':
									failed.append(package_list.PackageList[i]['Packages'][j]['Name'])
									break
					if len(failed) < len(package_list.PackageList[i]['Packages']):
						position=len(NewPackageList)
						NewPackageList.append(copy.deepcopy(package_list.PackageList[i]))
						NewPackageList[position]['Packages'] = []
						for j in range(0,len(package_list.PackageList[i]['Packages'])):
							if not package_list.PackageList[i]['Packages'][j]['Name'] in failed:
								NewPackageList[position]['Packages'].append(package_list.PackageList[i]['Packages'][j])

			self.stop()

	class packages(subwin):

		def _init_categories(self):
			self.categories={}
			count=0
			for i in range(0,len( NewPackageList )):
				found=0
				on=0
				off=0
				for j in range(0,len(NewPackageList[i]['Packages'])):
					if 'all' in NewPackageList[i]['Packages'][j]['Possible'] or self.parent.all_results.has_key( 'system_role') and self.parent.all_results['system_role'] in NewPackageList[i]['Packages'][j]['Possible']:
						if not NewPackageList[i]['Packages'][j].has_key('Architecture') or (NewPackageList[i]['Packages'][j].has_key('Architecture') and self.parent.cmdline['architecture'] in NewPackageList[i]['Packages'][j]['Architecture']):
							if self.parent.all_results.has_key('packages'):
								if NewPackageList[i]['Packages'][j]['Packages'][0] in self.parent.all_results['packages']:
									on=on+1
								else:
									off=off+1
							else:
								if 'all' in NewPackageList[i]['Packages'][j]['Active'] or self.parent.all_results.has_key( 'system_role' ) and self.parent.all_results['system_role'] in NewPackageList[i]['Packages'][j]['Active']:
									disable=False
									if NewPackageList[i]['Packages'][j].has_key('EditionDisable'):
										for ea in NewPackageList[i]['Packages'][j]['EditionDisable']:
											if ea in self.parent.cmdline['edition']:
												disable=True
									if disable:
										off=off+1
									else:
										on=on+1
								else:
									off=off+1
							found=1
				if found==1:
					if on and not off:
						self.categories[NewPackageList[i]['Category']]=[NewPackageList[i]['Category'], count, 2, NewPackageList[i]['Description']]
					elif off and not on:
						self.categories[NewPackageList[i]['Category']]=[NewPackageList[i]['Category'], count, 0, NewPackageList[i]['Description']]
					else:
						self.categories[NewPackageList[i]['Category']]=[NewPackageList[i]['Category'], count, 1, NewPackageList[i]['Description']]
					count=count+1


		def _init_packages(self):
			self.packages=[]
			for i in range(0,len( NewPackageList )):
				p={}
				count=0
				for j in range(0,len(NewPackageList[i]['Packages'])):
					if 'all' in NewPackageList[i]['Packages'][j]['Possible'] or self.parent.all_results.has_key( 'system_role' ) and self.parent.all_results['system_role'] in NewPackageList[i]['Packages'][j]['Possible']:
						if not NewPackageList[i]['Packages'][j].has_key('Architecture') or (NewPackageList[i]['Packages'][j].has_key('Architecture') and self.parent.cmdline['architecture'] in NewPackageList[i]['Packages'][j]['Architecture']):
							if self.parent.all_results.has_key('packages'):
								if NewPackageList[i]['Packages'][j]['Packages'][0] in self.parent.all_results['packages']:
									p[NewPackageList[i]['Packages'][j]['Name']]=[NewPackageList[i]['Packages'][j]['Name'], count, 1, NewPackageList[i]['Packages'][j]['Description'], NewPackageList[i]['Packages'][j]['Packages']]
								else:
									p[NewPackageList[i]['Packages'][j]['Name']]=[NewPackageList[i]['Packages'][j]['Name'], count, 0, NewPackageList[i]['Packages'][j]['Description'], NewPackageList[i]['Packages'][j]['Packages']]
							else:
								if 'all' in NewPackageList[i]['Packages'][j]['Active'] or self.parent.all_results.has_key( 'system_role' ) and self.parent.all_results['system_role'] in NewPackageList[i]['Packages'][j]['Active']:
									disable=False
									if NewPackageList[i]['Packages'][j].has_key('EditionDisable'):
										for ea in NewPackageList[i]['Packages'][j]['EditionDisable']:
											if ea in self.parent.cmdline['edition']:
												disable=True
									if disable:
										p[NewPackageList[i]['Packages'][j]['Name']]=[NewPackageList[i]['Packages'][j]['Name'], count, 0, NewPackageList[i]['Packages'][j]['Description'], NewPackageList[i]['Packages'][j]['Packages']]
									else:
										p[NewPackageList[i]['Packages'][j]['Name']]=[NewPackageList[i]['Packages'][j]['Name'], count, 1, NewPackageList[i]['Packages'][j]['Description'], NewPackageList[i]['Packages'][j]['Packages']]
								else:
									p[NewPackageList[i]['Packages'][j]['Name']]=[NewPackageList[i]['Packages'][j]['Name'], count, 0, NewPackageList[i]['Packages'][j]['Description'], NewPackageList[i]['Packages'][j]['Packages']]
							count=count+1
				if len(p) > 0:
					self.packages.append(p)

		def _save_packages(self, category_name, package_names):
			add=[]
			remove=[]
			for c in self.categories.keys():
				if c == category_name:
					category_index=self.categories[c][1]
					break
			for p in self.packages[category_index].keys():
				if p in package_names:
					self.packages[category_index][p][2]=1
					add.append(self.packages[category_index][p][0])
				else:
					remove.append(self.packages[category_index][p][0])
					self.packages[category_index][p][2]=0

			for c in self.categories.keys():
				if c != category_name:
					i=self.categories[c][1]
					for k in self.packages[i].keys():
						if self.packages[i][k][0] in add:
							self.parent.debug('found: %s' % str(self.packages[i][k]))
							self.packages[i][k][2]=1
						if self.packages[i][k][0] in remove:
							self.packages[i][k][2]=0
			pass

		def _get_category_by_index(self, index):
			for i in self.categories.keys():
				if self.categories[i][1] == index:
					return i
		def _get_category_by_name(self, index):
			for c in self.categories.keys():
				if index == c:
					return self.categories[c][1]
		def _get_category_list_by_name(self, index):
			l=[]
			for c in self.categories.keys():
				if c in index:
					l.append(self.categories[c][1])
			return l

		def _check_checkbox3(self):
			for c in self.categories.keys():
				packages_enabled=0
				packages_disabled=0
				category_index=self._get_category_by_name(c)
				for p in self.packages[self.categories[c][1]]:
					if self.packages[category_index][p][2] == 1:
						packages_enabled=packages_enabled+1
					else:
						packages_disabled=packages_disabled+1
				if packages_enabled == 0 and packages_disabled > 0:
					self.categories[c][2]=0
				elif packages_enabled > 0 and packages_disabled == 0:
					self.categories[c][2]=2
				else:
					self.categories[c][2]=1

		def _get_status(self):
			half=[]
			full=[]
			for c in self.categories.keys():
				if self.categories[c][2]==1:
					half.append(self.categories[c][1])
				elif self.categories[c][2]==2:
					full.append(self.categories[c][1])

			return half,full

		def getSelected(self, category):
			selected=[]
			for c in self.categories.keys():
				if c == category:
					index=self.categories[c][1]
					break
			for key in self.packages[index].keys():
				if self.packages[index][key][2] == 1:
					selected.append(self.packages[index][key][1])
			return selected

		def _set_package_status(self, category, status):
			keylist=[]
			for c in self.categories.keys():
				if c == category:
					index=self.categories[c][1]
			for key in self.packages[index].keys():
				self.packages[index][key][2]=status
				keylist.append(key)
			for c in self.categories.keys():
				if c != category:
					i=self.categories[c][1]
					for k in self.packages[i].keys():
						if self.packages[i][k][0] in keylist:
							self.parent.debug('found: %s' % str(self.packages[i][k]))
							self.packages[i][k][2]=status



		def getPackages(self, category):
			for i in self.categories.keys():
				if i == category:
					index=self.categories[i][1]
					break
			return self.packages[index]

		def layout(self):
			self.packages=[]
			self.categories=[]
			self.elements=[]
			self.container=self.parent.container
			self.minY=self.parent.minY
			self.minX=self.parent.minX-16
			self.maxWidth=self.parent.maxWidth
			self.maxHeight=self.parent.maxHeight
			self.elements.append(textline(_('Components'),self.minY,self.minX+2)) #0
			self.elements.append(textline(_('Packages'),self.minY,self.minX+30)) #1
			self.elements.append(hLine(self.minY+1,self.minX-1, self.maxWidth+15)) #2
			self.elements.append(vLine(self.minY,self.minX+28, self.maxHeight-5)) #3
			self.elements[3].pad.addch(1,0,curses.MY_PLUS)

			self._init_categories()
			self._init_packages()


			half,full=self._get_status()
			self.elements.append(checkbox3(self.categories, self.minY+2,self.minX-2, 25, 14, half,full)) #4
			self.elements.append(checkbox(self.getPackages(self._get_category_by_index(0)), self.minY+2,self.minX+30, 30, 14, self.getSelected(self._get_category_by_index(0)))) #5
			if self.parent.cmdline.has_key('mode') and self.parent.cmdline['mode'] == 'setup':
				self.elements.append(button(_("F12-Accept changes"),self.minY+17,self.pos_x+65, align='right')) #6
				self.parent.debug('moaded_modules=%s' % self.parent.cmdline['loaded_modules'])
				if self.parent.cmdline.has_key('loaded_modules') and len(self.parent.cmdline['loaded_modules']) >1:
					self.elements.append(button(_("F11-Back"),self.minY+17,self.pos_x+2, align='left')) #7
				else:
					self.elements.append(textline("",self.minY+17,self.pos_x+2, align='left')) #7
			else:
				self.elements.append(button(_("F12-Next"),self.minY+17,self.pos_x+65, align='right')) #6
				self.elements.append(button(_("F11-Back"),self.minY+17,self.pos_x+2, align='left')) #7
			self.elements[5].set_off()
			self.elements[4].set_on()
			self.current=4

		def input(self,key):

			category_name_old=self._get_category_by_index(self.elements[4].current)
			old_state=self.elements[4].current
			cat_active=self.elements[4].active

			if key == 276:
					return 'next'
			if key in [ 10, 32 ] and self.elements[6].usable() and self.elements[6].get_status():
					return 'next'
			elif key in [ 10, 32 ] and self.elements[7].usable() and self.elements[7].get_status():
					return 'prev'
			elif key == 261:
				# move right
				if self.elements[4].active:
					self.elements[4].set_off()
					self.elements[5].set_on()
					self.current=5
					self.draw()
			elif key == 260:
				# move left
				if hasattr(self.elements[5], 'active') and self.elements[5].active:
					self.elements[5].set_off()
					self.elements[4].set_on()
					self.current=4
					self.draw()
			elif key == 258:
				# down
				self.elements[self.current].key_event(key)
				if self.elements[4].active:
					self._save_packages(category_name_old,self.elements[5].result())
					self.category_name=self._get_category_by_index(self.elements[4].current)
					self.elements[5]=checkbox(self.getPackages(self.category_name), self.minY+2,self.minX+30, 30, 14,  self.getSelected(self.category_name)) #5
					self._check_checkbox3()
					old_state=self.elements[4].current
					half,full=self._get_status()
					self.elements[4]=checkbox3(self.categories, self.minY+2,self.minX-2, 25, 14, half, full)
					self.elements[4].current=old_state
					self.elements[4].set_on()
					self.elements[4].select_all()
					self.draw()
			elif key == 259:
				#up
				self.elements[self.current].key_event(key)
				if self.elements[4].active:
					self._save_packages(category_name_old,self.elements[5].result())
					self.category_name=self._get_category_by_index(self.elements[4].current)
					self.elements[5]=checkbox(self.getPackages(self.category_name), self.minY+2,self.minX+30, 30, 14, self.getSelected(self.category_name)) #5
					self._check_checkbox3()
					old_state=self.elements[4].current
					half,full=self._get_status()
					self.elements[4]=checkbox3(self.categories, self.minY+2,self.minX-2, 25, 14,half,full)
					self.elements[4].current=old_state
					self.elements[4].set_on()
					self.elements[4].select_all()
					self.draw()
			elif key == 32:
				#space
				self.elements[self.current].key_event(key)
				if hasattr(self.elements[5], 'active') and self.elements[5].active:
					self._save_packages(category_name_old,self.elements[5].result())
					self.category_name=self._get_category_by_index(self.elements[4].current)
					self._check_checkbox3()
					half,full=self._get_status()
					self.elements[4]=checkbox3(self.categories, self.minY+2,self.minX-2, 25, 14,half,full)
					self.elements[4].current=old_state
					self.elements[4].select_all()
					self.draw()
				elif self.elements[4].active:
					self.category_name=self._get_category_by_index(self.elements[4].current)
					half,full=self.elements[4].result()
					l=self._get_category_list_by_name(full)
					if self.elements[4].current in l:
						self._set_package_status(self.category_name, 1)
					else:
						self._set_package_status(self.category_name, 0)
					self.elements[5]=checkbox(self.getPackages(self.category_name), self.minY+2,self.minX+30, 30, 14, self.getSelected(self.category_name)) #5
					self.category_name=self._get_category_by_index(self.elements[4].current)
					self._check_checkbox3()
					half,full=self._get_status()
					self.elements[4]=checkbox3(self.categories, self.minY+2,self.minX-2, 25, 14,half,full)
					self.elements[4].current=old_state
					self.elements[4].select_all()
					self.elements[4].set_on()
					self.draw()

			elif self.elements[self.current].usable():
				self.elements[self.current].key_event(key)
			return 1

		def helptext(self):
			if hasattr(self.elements[5], 'active') and self.elements[5].active:
				index=self.elements[4].current
				for p in self.packages[index].keys():
					if self.packages[index][p][1] == self.elements[5].current:
						return self.packages[index][p][3]
			elif self.elements[4].active:
				category_name=self._get_category_by_index(self.elements[4].current)
				return self.categories[category_name][3]
			return _("No helptext available.")

		def get_result(self):
			result=[]
			for c in self.categories.keys():
				index=self.categories[c][1]
				for key in self.packages[index].keys():
					if self.packages[index][key][2] == 1:
						for p in self.packages[index][key][4]:
							result.append(p)
			return result


	def input(self,key):
		if hasattr(self,"sub"):
			res=self.sub.input(key)
			if res == 'next' or res == 'prev':
				self.subresult=self.sub.get_result()
				return res
		elif ( key in [ 10, 32 ] and self.btn_next() ) or key == 276:
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		else:
			return self.elements[self.current].key_event(key)

	def incomplete(self):
		return 0

	def helptext(self):
		return _('Software \n \n Choose the softwarecomponents you want to install. You can change details for some modules in the following steps.')

	def modheader(self):
		return _('Software')

	def result(self):
		result={}
		if hasattr(self,"sub"):
			result['packages']=string.join(self.sub.get_result(), ' ')
		else:
			result['packages']=string.join(self.subresult, ' ')
		return result
