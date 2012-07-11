#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: software package selection
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

import string
import os
from objects import *
from local import _

NewPackageList = []


class object(content):
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

						if active:
							for ed in package_list.PackageList[i]['Packages'][j].get('EditionDisable',[]):
								if ed in self.parent.cmdline.get('edition',[]):
									active = False

						if not active:
							failed.append(package_list.PackageList[i]['Packages'][j]['Name'])

						for p in package_list.PackageList[i]['Packages'][j]['Packages']:
							if os.path.exists('/usr/bin/apt-cache'):
								res = os.system('apt-cache show %s >/dev/null 2>&1' % p )
								if res != 0:
									if not package_list.PackageList[i]['Packages'][j]['Name'] in failed:
										failed.append(package_list.PackageList[i]['Packages'][j]['Name'])
									break
							else:
								if not p in PackagesList and not PackagesList == 'INVALID':
									if not package_list.PackageList[i]['Packages'][j]['Name'] in failed:
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

	def depends(self):
		# depends() is called every time the user enters this module - so we can reset position here
		self.reset_position_in_layout()
		return {}

	def start(self):
		self.sub = self.active(self,_('Preparing package list'),_('Please wait ...'))
		self.sub.action='preparing-package-list'
		self.sub.draw()
		self.samba3_warning = False
		self.samba4_warning = False

	def _init_categories(self):
		self.categories={}
		self.category_order=[]
		count=0
		for i in range(0,len( NewPackageList )):
			found=0
			on=0
			off=0
			for j in range(0,len(NewPackageList[i]['Packages'])):
				if 'all' in NewPackageList[i]['Packages'][j]['Possible'] or self.all_results.has_key( 'system_role') and self.all_results['system_role'] in NewPackageList[i]['Packages'][j]['Possible']:
					if not NewPackageList[i]['Packages'][j].has_key('Architecture') or (NewPackageList[i]['Packages'][j].has_key('Architecture') and self.cmdline['architecture'] in NewPackageList[i]['Packages'][j]['Architecture']):
						if self.all_results.has_key('packages'):
							if NewPackageList[i]['Packages'][j]['Packages'][0] in self.all_results['packages']:
								on=on+1
							else:
								off=off+1
						else:
							if 'all' in NewPackageList[i]['Packages'][j]['Active'] or self.all_results.has_key( 'system_role' ) and self.all_results['system_role'] in NewPackageList[i]['Packages'][j]['Active']:
								disable=False
								if NewPackageList[i]['Packages'][j].has_key('EditionDisable'):
									for ea in NewPackageList[i]['Packages'][j]['EditionDisable']:
										if ea in self.cmdline['edition']:
											disable=True
								if disable:
									off=off+1
								else:
									on=on+1
							else:
								off=off+1
						found=1
			if found==1:
				self.category_order.append(NewPackageList[i]['Category'])
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
			installed_packages = []
			for j in range(0,len(NewPackageList[i]['Packages'])):
				if 'all' in NewPackageList[i]['Packages'][j]['Possible'] or self.all_results.has_key( 'system_role' ) and self.all_results['system_role'] in NewPackageList[i]['Packages'][j]['Possible']:
					if not NewPackageList[i]['Packages'][j].has_key('Architecture') or (NewPackageList[i]['Packages'][j].has_key('Architecture') and self.cmdline['architecture'] in NewPackageList[i]['Packages'][j]['Architecture']):
						if self.all_results.has_key('packages'):
							if NewPackageList[i]['Packages'][j]['Packages'][0] in self.all_results['packages']:
								p[NewPackageList[i]['Packages'][j]['Name']]=[NewPackageList[i]['Packages'][j]['Name'], count, 1, NewPackageList[i]['Packages'][j]['Description'], NewPackageList[i]['Packages'][j]['Packages']]
							else:
								p[NewPackageList[i]['Packages'][j]['Name']]=[NewPackageList[i]['Packages'][j]['Name'], count, 0, NewPackageList[i]['Packages'][j]['Description'], NewPackageList[i]['Packages'][j]['Packages']]
						else:
							if 'all' in NewPackageList[i]['Packages'][j]['Active'] or self.all_results.has_key( 'system_role' ) and self.all_results['system_role'] in NewPackageList[i]['Packages'][j]['Active']:
								disable=False
								if NewPackageList[i]['Packages'][j].has_key('EditionDisable'):
									for ea in NewPackageList[i]['Packages'][j]['EditionDisable']:
										if ea in self.cmdline['edition']:
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
		# dump the package status
		if self.cmdline.has_key('mode') and self.cmdline['mode'] == 'setup':
			file = open('/var/cache/univention-system-setup/packages.state', 'w')
			for p in self.packages:
				for p_key in p.keys():
					if p[p_key][2] == 1:
						for name in p[p_key][4]:
							file.write('%s\n' % name)
			file.close()

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
						self.debug('found: %s' % str(self.packages[i][k]))
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

	def getPackages(self, category):
		for i in self.categories.keys():
			if i == category:
				index=self.categories[i][1]
				break
		return self.packages[index]

	def layout(self):
		self.packages=[]
		self.categories=[]
		self.reset_layout()

		self._init_categories()
		self._init_packages()

		pos = 0
		for k in self.category_order:
			p = self.getPackages(k)
			self.add_elem('packages_%s' % k, checkbox(p, self.minY-9+pos,self.minX+6, 65, 14, self.getSelected(k))) #5
			pos += (len(p) + 1)

		if self.cmdline.has_key('mode') and self.cmdline['mode'] == 'setup':
			self.add_elem('__NEXT_BUTTON__', button(_("F12-Accept changes"),self.pos_y+self.height-2,self.pos_x+self.width-2, align='right')) #6
			self.debug('moaded_modules=%s' % self.cmdline['loaded_modules'])
			if self.cmdline.has_key('loaded_modules') and len(self.cmdline['loaded_modules']) >1:
				self.add_elem('__BACK_BUTTON__', button(_("F11-Back"),self.pos_y+self.height-2,self.pos_x+4, align='left')) #7
			else:
				self.add_elem('__BACK_BUTTON__', textline("",self.pos_y+self.height-2,self.pos_x+4,align='left')) #7
		else:
			self.add_elem('__NEXT_BUTTON__', button(_("F12-Next"),self.pos_y+self.height-2,self.pos_x+self.width-2, align='right')) #6
			self.add_elem('__BACK_BUTTON__', button(_("F11-Back"),self.pos_y+self.height-2,self.pos_x+4, align='left')) #7

		self.add_elem('headline', textline(_('Please select the software components you want to install:'), self.minY-11,self.minX+3))

		self.current=0
		self.elements[0].set_on()

		# skip the initial "tab" "tab"
		self.skip_tab = True

	def reset_position_in_layout(self):
		if self.elements and hasattr(self, 'categories'):
			for i in xrange(len(self.categories)):
				elem = self.get_elem_by_id(i)
				if elem.usable():
					elem.current=0
					elem.set_off()
			self.current = 0
			self.elements[0].set_on()

	def real_tab(self):
		while not self.elements[self.current].usable():
			self.current = (self.current+1)%len(self.elements)
		self.elements[self.current].set_off()
		self.elements[self.current].draw()
		self.current = (self.current+1)%len(self.elements)
		while not self.elements[self.current].usable():
			self.current = (self.current+1)%len(self.elements)
		self.elements[self.current].set_on()
		self.elements[self.current].draw()

	def tab(self):
		if self.current < len(self.categories):
			if (self.elements[self.current].current) >= len(self.elements[self.current].button)-1:
				self.elements[self.current].set_off()
				self.elements[self.current].current=0
				self.real_tab()
			else:
				self.elements[self.current].key_event(258)
		else:
			self.real_tab()

	def real_tab_reverse(self):
		while not self.elements[self.current].usable():
			self.current = (self.current+1)%len(self.elements)
		self.elements[self.current].set_off()
		self.elements[self.current].draw()
		self.current = (self.current-1)%len(self.elements)
		while not self.elements[self.current].usable():
			self.current = (self.current-1)%len(self.elements)

		# if possible, activate the last element of the selectbox
		if hasattr(self.elements[self.current], 'button'):
			self.elements[self.current].current = len(self.elements[self.current].button)-1
		self.elements[self.current].set_on()
		self.elements[self.current].draw()

	def tab_reverse(self):
		if self.current < len(self.categories):
			if self.elements[self.current].current == 0:
				self.elements[self.current].set_off()
				self.elements[self.current].current=0
				self.real_tab_reverse()
			else:
				self.elements[self.current].key_event(259)
		else:
			self.real_tab_reverse()

	def input(self,key):
		current_category=self._get_category_by_index(self.current)
		if current_category:
			self._save_packages(current_category, self.get_elem('packages_%s' % current_category).result())

		if hasattr(self,"sub"):
			res=self.sub.input(key)
			if res == 'next' or res == 'prev':
				self.subresult=self.sub.get_result()
				return res

		elif key == 276:
			return 'next'
		if key in [ 10, 32 ] and self.get_elem('__NEXT_BUTTON__').usable() and self.get_elem_id('__NEXT_BUTTON__') == self.current and self.get_elem('__NEXT_BUTTON__').get_status():
			return 'next'
		elif key in [ 10, 32 ] and self.get_elem('__BACK_BUTTON__').usable() and self.get_elem_id('__BACK_BUTTON__') == self.current and self.get_elem('__BACK_BUTTON__').get_status():
			return 'prev'
		elif key == 258:
			# down
			self.tab()
		elif key == 259:
			#up
			self.tab_reverse()
		elif key == 32:
			#space
			self.elements[self.current].key_event(key)
		else:
			self.elements[self.current].key_event(key)

		# Save the package status again
		current_category=self._get_category_by_index(self.current)
		if current_category:
			self._save_packages(current_category, self.get_elem('packages_%s' % current_category).result())

	def incomplete(self):
		p_list=[]
		s3 = s4 = None
		kvm = xen = None

		for c in self.categories.keys():
			index=self.categories[c][1]
			for key in self.packages[index].keys():
				if self.packages[index][key][2] == 1:
					for p in self.packages[index][key][4]:
						if p == 'univention-samba':
							s3 = (index, key)
						elif p == 'univention-samba4':
							s4 = (index, key)
						elif p == 'univention-virtual-machine-manager-node-kvm':
							kvm = (index, key)
						elif p == 'univention-virtual-machine-manager-node-xen':
							xen = (index, key)
						p_list.append(p)

		if xen and kvm:
			return _('Software conflict!\n\nIt is not allowed to install the software packages %s and %s on one system. Please select only one of these two component.') % (self.packages[kvm[0]][kvm[1]][0], self.packages[xen[0]][xen[1]][0])

		if s3 and s4:
			return _('Software conflict!\n\nIt is not allowed to install the software packages %s and %s on one system. Please select only one of these two component.') % (self.packages[s4[0]][s4[1]][0], self.packages[s3[0]][s3[1]][0])

		if self.all_results['system_role'] in ['domaincontroller_backup', 'domaincontroller_slave']:
			if s3 and self.samba3_warning == False:
				self.samba3_warning = True
				return _('The software package %s was selected. It is not possible to mix NT and Active Directory compatible domaincontroller.\n\nMake sure the existing UCS domain is NT-compatible (Samba 3). This warning is shown only once. The installation can be continued with this selection.') % (self.packages[s3[0]][s3[1]][0])

			if s4 and self.samba4_warning == False:
				if self.all_results['system_role'] in ['domaincontroller_backup', 'domaincontroller_slave']:
					self.samba4_warning = True
					return _('The software package %s was selected. It is not possible to mix NT and Active Directory compatible domaincontroller.\n\nMake sure the existing UCS domain is Active Directory-compatible (Samba 4). This warning is shown only once. The installation can be continued with this selection.') % (self.packages[s4[0]][s4[1]][0])

		return 0

	def helptext(self):
		return _('Software \n \n Select the software components you want to install. You can change details for some modules in the following steps.')

	def modheader(self):
		return _('Software')

	def profileheader(self):
		return 'Software'

	def result(self):
		result={}
		p_list=[]
		for c in self.categories.keys():
			self.debug('c: %s' % c)
			index=self.categories[c][1]
			self.debug('\tindex: %s' % index)
			for key in self.packages[index].keys():
				self.debug('\t\tkey: %s' % key)
				if self.packages[index][key][2] == 1:
					self.debug('\t\t\tself.packages[index][key][2] ->  %s' % self.packages[index][key][2])
					for p in self.packages[index][key][4]:
						p_list.append(p)
		result['packages'] = string.join(p_list, ' ')
		return result
