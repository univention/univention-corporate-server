#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  main function for the installation interface
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

# Module
import sys
import os
import traceback
import curses
import curses.ascii
import objects
try:
	import getopt
except:
	pass
from local import _
from objects import *

import locale
locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

profile=0
cmdline={}

read_cmdline = False

if len(sys.argv) > 1:

	longopts=['profile', 'noprobe', 'floppy', 'usb', 'loadmodules=', 'excludemodules=', 'loadmodule=', 'excludemodule=', 'nfspath=', 'nfsserver=', 'ip=', 'profile_file=', 'simple', 'cmdline', 'version=', 'extension=', 'edition=', 'expert_partition', 'mbr_partition', 'nousbstorage', 'nousbcdrom', 'name=', 'codename=', 'use_efi=']
	try:
		opts, args=getopt.getopt(sys.argv[1:], '', longopts)
	except getopt.error, msg:
		print msg
		sys.exit(1)

	files=[]
	packages_dir=''
	for opt, val in opts:
		if opt == '--profile':
			cmdline['profile']='cdrom'
			profile=1
		elif opt == '--floppy':
			cmdline['profile']='floppy'
		elif opt == '--usb':
			cmdline['profile']='usb'
		elif opt == '--noprobe':
			cmdline['noprobe']=1
		elif opt == '--loadmodules' or opt == '--loadmodule':
			cmdline['loadmodules']=val
		elif opt == '--nfspath':
			cmdline['nfspath']=val
		elif opt == '--nfsserver':
			cmdline['nfsserver']=val
		elif opt == '--ip':
			cmdline['ip']=val
		elif opt == '--simple': # No extended ASC
			cmdline['simple']=1
		elif opt == '--profile_file' and val:
			cmdline['profile_file']=val
		elif opt == '--version' and val:
			cmdline['version']=val
		elif opt == '--extension' and val:
			cmdline['extension']=val
		elif opt == '--name' and val:
			cmdline['name']=val
		elif opt == '--codename' and val:
			cmdline['codename']=val
		elif opt == '--edition' and val:
			cmdline['edition']=[]
			for e in val.split(','):
				cmdline['edition'].append(e)
		elif opt == '--cmdline':
			read_cmdline = True
		elif opt == '--expert_partition':
			cmdline['expert_partition'] = True
		elif opt == '--mbr_partition':
			cmdline['mbr_partition'] = True
		elif opt == '--nousbstorage':
			cmdline['nousbstorage'] = True
		elif opt == '--nousbcdrom':
			cmdline['nousbcdrom'] = True
		elif opt == 'use_efi' and val:
			cmdline['use_efi'] = val

if len(sys.argv) < 1 or read_cmdline:
	f=open('/proc/cmdline', 'r')
	lines=f.readlines()
	f.close()
	array=lines[0].strip().split(' ')
	next_profile=False
	cmdline['nfs']=False
	cmdline['use_text']=False
	for a in array:
		if a.find('=') != -1:
			opt,val=a.split('=',1)
		else:
			opt=a
			val=None
		if opt == 'profile':
			profile=1
			cmdline['profile']='cdrom'
			next_profile=True
			if val:
				cmdline['profile_file']=val
		elif opt == 'floppy':
			cmdline['profile']='floppy'
		elif opt == 'usb':
			cmdline['profile']='usb'
		elif opt == 'noprobe':
			cmdline['noprobe']=1
		elif (opt == 'loadmodules' or opt == 'loadmodule') and val:
			cmdline['loadmodules']=val.strip('\'"')
		elif (opt == 'excludemodules' or opt == 'excludemodule') and val:
			cmdline['excludemodules']=val.strip('\'"')
		elif opt == 'nfspath' and val:
			cmdline['nfspath']=val.strip('\'"')
		elif opt == 'nfsserver' and val:
			cmdline['nfsserver']=val.strip('\'"')
		elif opt == 'lang' and val:
			cmdline['lang']=val.strip('\'"')
		elif opt == 'ip' and val:
			cmdline['ip']=val
		elif opt == '--simple':  # No extended ASC
			cmdline['simple']=1
		elif opt == 'recover':  # recover-mode
			cmdline['recover']=True
		elif opt == 'profile_file' and val:
			cmdline['profile_file']=val
		elif opt == 'nfs':
			cmdline['nfs']=True
		elif opt == 'product':
			cmdline['product']=val
		elif opt == 'use_text':
			cmdline['use_text']=True
		elif opt == 'expert_partition':
			cmdline['expert_partition'] = True
		elif opt == 'mbr_partition':
			cmdline['mbr_partition'] = True
		elif opt == 'nousbstorage':
			cmdline['nousbstorage'] = True
		elif opt == 'nousbcdrom':
			cmdline['nousbcdrom'] = True
		elif opt == 'nfsdelay':
			cmdline['nfsdelay']=val
		elif opt == 'use_efi':
			cmdline['use_efi'] = val

		elif next_profile:
			if not val:
				cmdline['profile_file']=opt
			next_profile=False
	if cmdline['nfs'] and cmdline['use_text']:
		profile=0
	elif cmdline['nfs'] and not cmdline['use_text']:
		profile=1


if profile == 1:
	if not cmdline.has_key('profile'):
		cmdline['profile']='cdrom'

cmdline['mode']='installation'

# check architecture
f=os.popen('/bin/uname -m')
architecture=f.readlines()[0].strip('\n')
if architecture in ['powerpc', 'ppc', 'ppc64' ]:
	cmdline['architecture']='powerpc'
else:
	cmdline['architecture']='x86'


moddir = 'modules'
sys.path.append(moddir)
sys.path.append('/lib/univention-installer/modules')
try:
	files=os.listdir(moddir)
except OSError:
	files=os.listdir('/lib/univention-installer/modules')
modules=[]
for file in files:
	temp=file.split('.')
	if len(temp) == 2 and temp[1] == 'py':
		if cmdline.has_key( 'recover' ) and cmdline[ 'recover' ]:
			if not file in [ '01_modules.py' ]:
				continue
		if not profile and file == '15_profile.py':
			continue
		if cmdline.get('mode') != 'setup' and file in ['45_password.py']:
			continue
		if temp[0].split('_')[0].isdigit():
			if cmdline.has_key("expert_partition") and (temp[0] == "65_partition" or temp[0] == "66_gpt_partition"):
				continue
			if not cmdline.has_key("expert_partition") and temp[0] == "60_expert_partition":
				continue
			# in interactive mode only one module (65_partition XOR 66_gpt_partition) will be used; selected by kernel cmdline argument
			# in profile mode each module checks profile and disables itself automatically
			if not profile and 'mbr_partition' in cmdline and temp[0] == "66_gpt_partition":
				continue
			if not profile and not 'mbr_partition' in cmdline and temp[0] == "65_partition":
				continue
			modules.append(temp[0])
modules.sort()


def exit_curses():
	stdscr.keypad(0)
	curses.nocbreak()
	curses.echo()
	curses.endwin()


def abort(max_x,max_y):
	text=_('Press Ctrl+c to exit or any key to continue. After exiting the installer please reboot the system or press Ctrl+Alt+F2 to get an shell prompt.')
	message=objects.warning(text, max_y, max_x)
	message.draw()
	c = stdscr.getch()
	return 0


def debug(text):
	file='/tmp/installer.log'
	f=open(file, 'a+')
	f.write("(main) %s\n" % text)
	f.close()


class error_message(subwin):
	def __init__(self,parent,pos_y,pos_x,width,height, message):
		self.message=message
		self.message_width = width - 4
		text = _( 'This error message is shown when an unexpected error occures '
				'during the installation process. The best way is to reboot '
				'the computer and retry the installation. Confirming this '
				'message will restart the installation process without '
				'rebooting.' )
		self.comment = []
		i = 0
		while len( text ) > width - 4:
			end = text.rfind( ' ', 0, width - 4 )
			i += 1
			self.comment.append( text[ : end ] )
			text= text[ end + 1 : ]
		self.comment.append( text[ : end ] )
		height += i
		y = ( max_y - height ) / 2
		subwin.__init__( self,parent, y, pos_x, width, height )

	def layout(self):
		dict={}
		self.elements.append(textline(_('A Python Exception has occured!'),self.pos_y+2,self.pos_x+2)) #0

		debug( str( self.comment ) )
		i = 0
		for line in self.comment:
			obj = textline( line, self.pos_y + 3 + i, self.pos_x + 2 )
			i += 1
			self.elements.append( obj )

		count=i
		f=open('/tmp/installation.error', 'a+')
		for l in self.message:
			l=l.replace('\n','')
			l=l.replace('\r','')
			l=l.strip(' ')
			self.elements.append(textline(l[:self.message_width],self.pos_y+4+count,self.pos_x+2)) #2...
			count=count+1
			f.write(str(l)+'\n')

		self.elements.append(button(_('Ok'),self.pos_y+self.height-2,self.pos_x+(self.width/2),align='middle')) #2

		f.close()

	def input(self, key):
		if key == 10:
			return 1
		elif key == 9:
			self.tab()
		else:
			return self.elements[self.current].key_event(key)


class mods:
	def __init__(self,modules,max_x,max_y,initialized=1, cmdline={}):
		self.max_x=max_x
		self.max_y=max_y
		self.modules=modules
		self.cmdline=cmdline
		#self.loop=0
		#if cmdline.has_key('profile'):
		#	self.loop=1
		self.result={} #internal result
		self.profile={} #external results (sorted)
		self.inst_mods={}
		for m in self.modules:
			self.inst_mods[m] = __import__(m)
		self.current=0
		self.obj=[]
		self.modview=[]
		last=(0,0)
		for i in range(len(self.modules)):
			if i == 0 and  i == len(self.modules)-1: # module is first and last
				last=(0,0)
			elif i == 0 and i != len(self.modules)-1: # module is first
				last=(0,1)
			elif i != 0 and i == len(self.modules)-1: # module is last
				last=(1,0)
			else: # module is not first or last
				last=(1,1)
			self.obj.append(self.inst_mods[self.modules[i]].object(self.max_y,self.max_x,last, file='/tmp/installer.log', cmdline=cmdline))
		self.window=self.mainwin()
		self.headerline=self.header()
		self.footline1=self.footer((0,0)) # first and last
		self.footline2=self.footer((0,1)) # first not last
		self.footline3=self.footer((1,0)) # last not first
		self.footline4=self.footer((1,1)) # not last not first
		self.current_old=0
		if not initialized:
			self.obj[0].initialized=0
		else:
			self.obj[0].initialized=1
		self.left_menu()

	def mainwin(self):
		window = curses.newpad(37,100)
		window.bkgd(" ",curses.color_pair(4))
		window.border(' ',' ',curses.MY_HLINE,curses.MY_HLINE,curses.MY_HLINE,curses.MY_HLINE,curses.MY_HLINE,curses.MY_HLINE)
		return window

	def header(self):
		codename = self.cmdline.get('codename', "golden beech")
		extension = self.cmdline.get('extension', '')
		version = self.cmdline.get('version', '3.0')
		name = self.cmdline.get('name', 'Univention Corporate Server')

		headLine = " " + name + " " + version
		if extension:
			headLine = headLine + " " + extension
		headLine = headLine + " (" + codename + ")"

		return objects.headline(headLine,  max_y/2-18,max_x/2-45)

	def footer(self, last):
		if last[0]==0: # first
			if last[1]==0: # last
				if self.cmdline.has_key( 'recover' ) and self.cmdline[ 'recover' ]:
					text = _(' F1-Help | F12-Start Recover Shell | Ctrl+c-Exit')
				else:
					text = _(' F1-Help | F12-Start Installation | Ctrl+c-Exit')
			elif last[1]==1: # not last
				text = _(' F1-Help | F12-Next | Ctrl+c-Exit')
		elif last[0]==1: # not first
			if last[1]==0: # last
				if self.cmdline.has_key( 'recover' ) and self.cmdline[ 'recover' ]:
					text = _(' F1-Help | F11-Back | F12-Start Recover Shell | Ctrl+c-Exit')
				else:
					text = _(' F1-Help | F11-Back | F12-Start Installation | Ctrl+c-Exit')
			elif last[1]==1: # not last
				text = _(' F1-Help | F11-Back | F12-Next | Ctrl+c-Exit')

		return objects.footline(text,max_y/2+18,max_x/2-(len(text)/2))

	def draw(self):
		for i in range(len(self.modview)):
			if self.obj[self.current].modheader() == self.modview[i][0].text:
				self.modview[i][0].active()
			else:
				self.modview[i][0].bgcolor()
			self.modview[i][0].draw()

		# refresh header, footer and buttons (language update)
		self.footline1=self.footer((0,0))
		self.footline2=self.footer((0,1))
		self.footline3=self.footer((1,0))
		self.footline4=self.footer((1,1))
		self.obj[self.current].std_button()
		self.obj[self.current].refresh_modheader()

		if self.current == len(self.modules)-1 and self.current == 0:
			self.window.noutrefresh(0,0,self.max_y/2+18,self.max_x/2-50,self.max_y/2+18,self.max_x/2+50)
			self.footline1.draw()
		elif self.current == 0:
			self.window.noutrefresh(0,0,self.max_y/2+18,self.max_x/2-50,self.max_y/2+18,self.max_x/2+50)
			self.footline2.draw()
		elif self.current == len(self.modules)-1:
			self.window.noutrefresh(0,0,self.max_y/2+18,self.max_x/2-50,self.max_y/2+18,self.max_x/2+50)
			self.footline3.draw()
		else:
			self.window.noutrefresh(0,0,self.max_y/2+18,self.max_x/2-50,self.max_y/2+18,self.max_x/2+50)
			self.footline4.draw()
		self.obj[self.current].draw()

	def draw_all(self):
		self.window.noutrefresh(0,0,self.max_y/2-18,self.max_x/2-50,self.max_y/2+18,self.max_x/2+50)
		self.headerline.draw()
		if self.current == len(self.modules)-1 and self.current == 0:
			self.footline1.draw()
		elif self.current == 0:
			self.footline2.draw()
		elif self.current == len(self.modules)-1:
			self.footline3.draw()
		else:
			self.footline4.draw()
		self.draw()
		curses.doupdate()

	def left_menu(self):
		debug('leftmenu')
		self.modview=[]
		count=0
		for i in range(len(self.modules)):
			depends=self.obj[i].mod_depends()
			if len(depends) > 0:
				for key in depends.keys():
					if self.result.has_key(key):
						for l in depends[key]:
							if l in self.result[key]:
								self.modview.append((objects.modline(self.obj[i].modheader(),self.max_y/2-16+count,self.max_x/2-48),self.obj[i].mod_depends()))
								count=count+1
								break
			else:
				self.modview.append((objects.modline(self.obj[i].modheader(),self.max_y/2-16+count,self.max_x/2-48),self.obj[i].mod_depends()))
				count=count+1

	def result_update(self):
		self.result.update(self.obj[self.current].get_result())
		# external result (sorted)
		self.profile[self.obj[self.current].profileheader()]=self.obj[self.current].get_result()
		self.obj[self.current].put_result(self.result)

	def check_depends(self, number):
		if number >= len(self.modules):
			return 0
		dep=[]
		dep=self.obj[number].mod_depends()
		if len(dep) > 0:
			found=0
			for key in dep.keys():
				if self.result.has_key(key):
					for entry in dep[key]:
						if entry in self.result[key]:
							debug('found')
							found=1
			if not found:
				debug('check depends return 1 for %s'% self.obj[number].modheader())
				return 1
			else:
				debug('check depends return 0 for %s'% self.obj[number].modheader())
				return 0
		else:
			debug('check depends return 0 for %s'% self.obj[number].modheader())
			return 0

	def chg_current(self,diff):
		if self.current+diff >= len(self.modules):
			debug('>= len(self.modules)')
			self.write_profile()
			return 1
		self.current += diff
		self.obj[self.current].put_result(self.result)
		self.left_menu()
		self.draw_all()

	def tab(self):
		self.obj[self.current].tab()

	def tab_reverse(self):
		self.obj[self.current].tab_reverse()

	def help(self):
		self.obj[self.current].help()
		while 1:
			c = stdscr.getch()
			if not self.obj[self.current].help_input(c):
				break
		self.draw_all()

	def input(self,key):
		if key == 27 and hasattr(self.obj[self.current],"sub"):
			self.obj[self.current].kill_subwin()
		elif key in [ 3, 9, 10, 27 ] + range(32,277) + [ 338, 339, 360 ]:
			return self.obj[self.current].input(key)

	def write_profile(self, profile_mode=0):
		profile=open('/tmp/installation_profile',"w+")
		profile.write('\n#### UCS-Profile ####\n\n')
		if not profile_mode:
			for key in self.profile.keys():
				if key == 'Profil':
					continue
				profile.write('\n# [%s]\n' % key)
				for subkey in self.profile[key].keys():
					if self.profile[key][subkey]:
						profile.write("%s='%s'\n\n" % (subkey,self.profile[key][subkey]))
		else:
			for key in self.result.keys():
				if key.strip(" ") == "":
					continue
				if self.result[key]:
					profile.write("%s='%s'\n" % (key,self.result[key]))
				else:
					profile.write("#%s=\n" % key)
		profile.flush()
		profile.close()


# create a window-object
stdscr = curses.initscr()

if cmdline.has_key('simple'):
	curses.MY_VLINE='|'
	curses.MY_HLINE='-'
	curses.MY_BOARD='#'
	curses.MY_PLUS='+'
	curses.EDGE_TL=' '
	curses.EDGE_TR=' '
	curses.EDGE_BL=' '
	curses.EDGE_BR=' '
else:
	curses.MY_VLINE=curses.ACS_VLINE
	curses.MY_HLINE=curses.ACS_HLINE
	curses.MY_BOARD=curses.ACS_BOARD
	curses.MY_PLUS=curses.ACS_PLUS
	curses.EDGE_TL=curses.ACS_ULCORNER
	curses.EDGE_TR=curses.ACS_URCORNER
	curses.EDGE_BL=curses.ACS_LLCORNER
	curses.EDGE_BR=curses.ACS_LRCORNER


# use color
curses.start_color()
if curses.can_change_color():
	# init_color(color_number, r, g, b)
	curses.init_color(7, 960 , 930 , 910)
	#curses.init_color(1, 870 , 160 , 0)
	curses.init_color(1, 816 , 0 , 204)
	#curses.init_color(1, 870 , 160 , 0)
	curses.init_color(3, 816 , 0 , 204)
	#curses.init_color(3, 204 , 0 , 51)
	#curses.init_color(3, 930 , 470 , 60)
# create color_pair(number, fg, bg)
curses.init_pair(1,curses.COLOR_WHITE, curses.COLOR_BLACK)
curses.init_pair(2,curses.COLOR_YELLOW, curses.COLOR_WHITE)
curses.init_pair(3,curses.COLOR_WHITE, curses.COLOR_YELLOW)
curses.init_pair(4,curses.COLOR_BLACK, curses.COLOR_WHITE)
curses.init_pair(5,curses.COLOR_RED, curses.COLOR_WHITE)
# 0 COLOR_BLACK # 4 COLOR_BLUE # 6 COLOR_CYAN # 2 COLOR_GREEN
# 5 COLOR_MAGENTA # 1 COLOR_RED # 7 COLOR_WHITE # 3 COLOR_YELLOW

# turn off echo
curses.noecho()
# diables cursor
curses.curs_set(0)
# enable/disable cbreak-mode
curses.cbreak()
# enable/disable keypad for returning a special value such as curses.KEY_LEFT
stdscr.keypad(1)
#disable background
#stdscr.bkgd(curses.MY_PLUS,curses.color_pair(1))
max_y, max_x = stdscr.getmaxyx()
if max_y == 24:
	max_y=23

# refresh screen
stdscr.refresh()

def next_screen_profile(view_warning):
	installer.obj[installer.current].put_result(installer.result)
	installer.obj[installer.current].profile_prerun()

	if installer.obj[installer.current].profile_complete():
		result=installer.obj[installer.current].run_profiled()
		if result:
			installer.result.update(result)
			installer.profile[installer.obj[installer.current].modheader()]=result

		i=1
		if installer.current+i >= len(installer.modules):
			debug('>= len(self.modules)')
			installer.write_profile(1)
			return 2
		while installer.check_depends(installer.current+i):
			i=i+1
			if installer.current+i >= len(installer.modules):
				debug('>= len(self.modules)')
				installer.write_profile(1)
				return 2
		installer.current=installer.current+i
		return 0
	else:
		installer.write_profile(1)
		if hasattr(installer.obj[installer.current], 'message'):
			debug('%s' % installer.obj[installer.current].message)
		if hasattr(installer.obj[installer.current], 'message') and (hasattr(installer.obj[installer.current], 'view_warning') or view_warning):
			view_warning=1
			missing=installer.obj[installer.current].message
			if missing:
				message=objects.warning(missing,installer.max_y,installer.max_x)
				message.draw()
				stdscr.getch()
				installer.obj[installer.current].layout_reset()

		debug('incomplete: %d' % installer.current)
		for i in installer.obj[installer.current].modvars():
			if not installer.obj[installer.current].all_results.has_key(i):
				installer.obj[installer.current].all_results[i]=''
		if not view_warning:
			installer.left_menu()
			installer.obj[installer.current].startIt=1
		installer.draw_all()
		return 1


def next_screen():
	if hasattr(installer.obj[installer.current], 'postrun'):
		installer.obj[installer.current].postrun()
	missing=installer.obj[installer.current].incomplete()
	if missing:
		if type(missing) == type(1):
			return 0
		message=objects.warning(missing,installer.max_y,installer.max_x)
		message.draw()
		c = None
		while c != 27:
			c = stdscr.getch()
		installer.draw_all()
	else:
		installer.result_update()
		i=1
		while installer.check_depends(installer.current+i):
			i=i+1
		if installer.chg_current(i):
			return 1
		return 0


def prev_screen():
	i=1

	if installer.current == 0:
		return 0

	while installer.check_depends(installer.current-i):
		i=i+1
	if installer.chg_current(-i):
		return 1
	return 0


try:
	debug('Commandline: %s' % cmdline)

	# init main window
	installer=mods(modules,max_x,max_y, cmdline=cmdline)
	installer.draw_all()
	view_warning=0
	if cmdline.has_key('profile'):
		# profile installation
			while 1:
				res=next_screen_profile(view_warning)
				view_warning=0
				if res == 2:
					break
				elif res == 1:
					while 1:
						debug('waiting 2')
						curses.doupdate()
						c = stdscr.getch()
						if c == 276: # F12 -> next
							installer.obj[installer.current].interactive=True
							installer.result_update()
							debug('check for f12_run')
							if installer.obj[installer.current].profile_f12_run() == 1:
								continue
							if next_screen_profile(view_warning) == 1:
								view_warning=1
								debug('again invalid')
							break
						elif c == curses.KEY_F1: # F1 -> help
							installer.help()
						elif c == 9: # Tab
							installer.tab()
						elif c == 353: #SHIFT TAB
							installer.tab_reverse()
						else:
							act = installer.input(c)
							if act == 'next':
								installer.obj[installer.current].interactive=True
								installer.result_update()
								if next_screen_profile(view_warning) == 1:
									view_warning=1
									debug('again invalid')
								break
							elif act == 'tab':
								installer.tab()
				curses.doupdate()

	else:
		# interactive installation
		while 1:
			try:

				if hasattr(installer.obj[ installer.current ], "needs_draw_all"):
					if installer.obj[ installer.current ].needs_draw_all:
						installer.draw_all()

				# If module has defined function auto_input() and boolean flag auto_input_enabled
				# and auto_input_enabled==True then use result of auto_input() instead of keypress
				# as new input. Return value may be keycode (integer) or 'back' or 'next'.
				# Otherwise use user keypress as new input.
				if hasattr(installer.obj[ installer.current ], "auto_input") and \
					   hasattr(installer.obj[ installer.current ], "auto_input_enabled") and \
					   installer.obj[ installer.current ].auto_input_enabled:
					c = installer.obj[ installer.current ].auto_input()
				else:
					c = stdscr.getch()

				if c == 275 or c == 'back': # F11 -> back
					prev_screen()
				elif c == 276 or c == 'next': # F12 -> next
					if hasattr( installer.obj[ installer.current ], 'sub' ):
						if installer.obj[ installer.current ].input( c ) == 'next':
							next_screen()
					elif next_screen():
						break
				elif c == curses.KEY_F1: # F1 -> help
					installer.help()
				elif c == 9: # Tab
					installer.tab()
				elif c == 353: #SHIFT TAB
					installer.tab_reverse()
				else:
					act = installer.input(c)
					if act == 'next':
						if next_screen():
							break
					elif act == 'prev':
						prev_screen()
					elif act == 'tab':
						installer.tab()

			except KeyboardInterrupt:
				c = stdscr.getch()
				if abort(max_x,max_y):
					break
				else:
					installer.draw_all()
			curses.doupdate()
except KeyboardInterrupt:
	#info = sys.exc_info()
	exit_curses()
	sys.exit(0)
except:
	info = sys.exc_info()

	err_height = 20
	err_width = 92
	err_min_x=(max_x/2)-(err_width/2) - 1
	err_min_y=(max_y/2)-(err_height/2)
	try:
		def format_exception(info):
			(info_type, info_value, info_traceback, ) = info
			newlist = []
			for (filename, line, function, text, ) in traceback.extract_tb(info_traceback):
				if not (filename.startswith('<') and filename.endswith('>')):
					if '/' in filename:
						filename = filename[ filename.rfind('/')+1 : ]
				newlist.append( (filename, line, function, text, ) )
			outlist = []
			for line in traceback.format_list(newlist) + traceback.format_exception_only(info_type, info_value):
				line = line.replace('\n', ' ')
				while '  ' in line:
					line = line.replace('  ', ' ')
				outlist.append(line)
			outlist = ['Traceback (most recent call last):'] + outlist[-9:]
			return outlist
		error=error_message(None, err_min_y, err_min_x, err_width+2, err_height, format_exception(info))
		for line in apply(traceback.format_exception,info):
			debug(line)
		error.draw()
		curses.doupdate()
		while 1:
			c = stdscr.getch()
			if error.input(c):
				break
		exit_curses()
		sys.exit(0)
	except:
		exit_curses()
		sys.exit(0)

exit_curses()
