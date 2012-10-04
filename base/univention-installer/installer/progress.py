#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  progress bar
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

# Module
import optparse
import sys
import os
import curses
import curses.ascii
import linecache
import grp
import shutil
import time
import select
import re
import threading
import subprocess
from local import _

import locale
locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

MAX_HEIGHT = 37
MAX_WIDTH = 100
fn_error_msg = "/tmp/installation_error.log"
fn_success_msg = "/tmp/installation_success.log"
fn_language = "/tmp/language"

systemrole2name = {}
i18n_debootstrap = {}
i18n_aptget = None

class RegExTranslator(object):
	def __init__(self):
		self.regexlist = []

	def add_rule(self, regex, formatstr):
		self.regexlist.append( [re.compile(regex), formatstr] )

	def translate(self, txt, strict=False):
		"""
		translate string "txt" by testing against all regex.
		If strict is True, None will be returned if nothing matched.
		If strict is False, "txt" will be returned.
		"""
		for regex, format in self.regexlist:
			match = regex.search(txt)
			if match:
				return format % match.groupdict()
		if strict:
			return None
		return txt

def init_translations():
	global systemrole2name, i18n_debootstrap, i18n_aptget

	systemrole2name = { 'domaincontroller_master': _('Master domain controller'),
						'domaincontroller_backup': _('Backup domain controller'),
						'domaincontroller_slave': _('Slave domain controller'),
						'memberserver': _('Member server'),
						'managed_client': _('Managed Client'),
						'mobile_client': _('Mobile Client'),
						'basesystem': _('Base system'),
						}

	i18n_debootstrap = RegExTranslator()
	i18n_debootstrap.add_rule('I: Retrieving (?P<pkg>.+)', _('Retrieving %(pkg)s') )
	i18n_debootstrap.add_rule('I: Validating (?P<pkg>.+)', _('Validating %(pkg)s') )
	i18n_debootstrap.add_rule('I: Extracting (?P<pkg>.+)', _('Extracting %(pkg)s') )
	i18n_debootstrap.add_rule('I: Unpacking (?P<pkg>.+)', _('Unpacking %(pkg)s') )
	i18n_debootstrap.add_rule('I: Configuring (?P<pkg>.+)', _('Configuring %(pkg)s') )

	i18n_aptget = RegExTranslator()
	i18n_aptget.add_rule('^Retrieving file (?P<current>\d+) of (?P<total>\d+)', _('Retrieving file %(current)s of %(total)s') )
	i18n_aptget.add_rule('^Installing (?P<pkg>\S+)', _('Installing %(pkg)s') )
	i18n_aptget.add_rule('^Preparing to configure (?P<pkg>\S+)', _('Preparing to configure %(pkg)s') )
	i18n_aptget.add_rule('^Preparing (?P<pkg>\S+)', _('Preparing %(pkg)s') )
	i18n_aptget.add_rule('^Unpacking (?P<pkg>\S+)', _('Unpacking %(pkg)s') )
	i18n_aptget.add_rule('^Configuring (?P<pkg>\S+)', _('Configuring %(pkg)s') )
	i18n_aptget.add_rule('^Installed (?P<pkg>\S+)', _('Installed %(pkg)s') )
	i18n_aptget.add_rule('^Running post-installation trigger (?P<pkg>\S+)', _('Running post-installation trigger %(pkg)s') )
	i18n_aptget.add_rule('^Running (?P<pkg>\S+)', _('Running %(pkg)s') )


class ProgressInfo(object):
	"""
	percentage: progress gained by this script (0 <= x <= 100; special value==-1 ==> use available remainder ==> 10,15,-1,20 results to 10,15,55,20 )
	steps: number of progress steps this script emits (1 <= x)
	triggerlist: list of regular expressions that trigger a step (e.g. [ re.compile('^pmstatus:[^:]:\d+:[^ ] wird installiert$')
	"""
	def __init__(self, percentage=1, steps=1, triggerlist=None):
		self.percentage = float(percentage)
		self.steps = steps
		self.percentage_per_step = self.percentage / float(steps)
		self.remaining_percentage = self.percentage
		self.triggerlist = []
		if triggerlist and type(triggerlist) in [ list, tuple ]:
			self.triggerlist = triggerlist

	def set_steps(self, steps):
		if steps < 1:
			steps = 1
		self.steps = steps
		self.percentage_per_step = self.percentage / float(steps)





class ProgressDialog(object):
	def __init__(self, options):
		self.options = options
		self.fd_read = None
		self.fd_write = None
		self.thread = None
		# during installation, logfile changes from installer.log to /instmnt/.../installation.log
		self.logfile = '/tmp/installer.log'
		self.width = MAX_WIDTH
		self.height = 9
		self.inbuffer = ''
		self.redraw_blocked = False
		self.progress = 0   # progress starts at 0%
		self.progress_msg = ''  # messages like "Unpacking foobar" returned by apt-get
		self.script_msg = _('Preparing installation') # headlines returned by each script
		self.default_percentage = 0.5
		self.current_script = None
		self.profile = {}
		self.win = None
		self.infowin = None
		self.script2progress = { '10_debootstrap.sh': ProgressInfo( percentage=4, steps=1, triggerlist = [ re.compile('^I: (Configuring|Unpacking|Extracting|Retrieving|Validating) ') ] ),
								 '25_install_config_registry.sh': ProgressInfo( percentage=4, steps=1, triggerlist = [ re.compile('^pmstatus:[^:]+:[.\d]+:(?:Installing|Unpacking|Installed) [^ ]+$'),
																													   re.compile('^pmstatus:[^:]+:[.\d]+:[^ ]+ (?:wird installiert|wird entpackt|installiert)$') ] ),
								 '35_kernel.sh': ProgressInfo( percentage=4, steps=1, triggerlist = [ re.compile('^pmstatus:[^:]+:[.\d]+:(?:Installing|Unpacking|Installed) [^ ]+$'),
																									  re.compile('^pmstatus:[^:]+:[.\d]+:[^ ]+ (?:wird installiert|wird entpackt|installiert)$') ] ),
								 '50_packages.sh': ProgressInfo( percentage=-1, steps=1, triggerlist = [ re.compile('^pmstatus:[^:]+:[.\d]+:(?:Installing|Unpacking|Installed) [^ ]+$'),
																										 re.compile('^pmstatus:[^:]+:[.\d]+:[^ ]+ (?:wird installiert|wird entpackt|installiert)$') ] ),
								 '75_join.sh': ProgressInfo( percentage=5, steps=1, triggerlist = [ re.compile('^__JOINSCRIPT__ ') ] ),
								 }
		# set dialog title
		self.title = options.name
		if options.version:
			self.title = '%s %s' % (self.title, options.version)
		if options.extension:
			self.title = '%s %s' % (self.title, options.extension)
		if options.codename:
			self.title = '%s (%s)' % (self.title, options.codename)
		self.title = '[ %s ]' % self.title

		self.read_installation_profile()


	def read_installation_profile(self):
		self.profile = {}
		try:
			lines = open('/tmp/installation_profile', 'r').readlines()
			for line in lines:
				try:
					key, val = line.split('=',1)
					self.profile[key] = val.strip('\n\r"\' ')
				except:
					pass
		except:
			pass

		# determine *one* IP address from profile
		keylist4 = [ x for x in self.profile.keys() if x.startswith('eth') and x.endswith('_ip') ]
		keylist4.sort()
		keylist6 = [ x for x in self.profile.keys() if x.startswith('eth') and x.endswith('_ip6') ]
		keylist6.sort()
		keylist = keylist4 + keylist6
		for key in keylist:
			val = self.profile.get(key)
			if val:
				self.profile['hostaddress'] = val
				break


	def prepare_gui(self):
		global MAX_HEIGHT, MAX_WIDTH
		# get screen dimension
		self.stdscr = curses.initscr()
		MAX_HEIGHT, MAX_WIDTH = self.stdscr.getmaxyx()

		ad_height = MAX_HEIGHT - self.height

		self.width = MAX_WIDTH
		x = 0
		y = (MAX_HEIGHT - self.height) / 2

		curses.start_color()
		if curses.can_change_color():
			# init_color(color_number, r, g, b)
			curses.init_color(7, 960 , 930 , 910)
			curses.init_color(1, 816 , 0 , 204)
			curses.init_color(3, 816 , 0 , 204)

		curses.noecho()
		curses.curs_set(0)
		self.stdscr.keypad(1)
		curses.cbreak()

		# colors
		curses.start_color()
		curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
		curses.init_pair(2, curses.COLOR_RED, curses.COLOR_WHITE)
		curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED)

		# main window
		self.win = curses.newwin(self.height, self.width, 0, 0)
		self.infowin = curses.newwin(MAX_HEIGHT-self.height, self.width, self.height, 0)

		self.infowin.clear()
		self.win.clear()

		self.stdscr.refresh()
		self.draw()
		self.draw_info()


	def create_success_msg(self):
		msg = []

		msg.append( _('The installation has been finished successfully!') )
		msg.append( '' )

		if self.profile.get('hostaddress'):
			msg.append( _('This system has been configured to IP address %s') % self.profile.get('hostaddress') )
		else:
			msg.append( _('This system has been configured for DHCP usage') )

		if self.profile.get('auto_join') == 'false' or self.profile.get('call_master_joinscripts') in [ 'false', 'no' ]:
			msg.append( _('and has not been joined to UCS domain yet.') )
		else:
			msg.append( _('and has been joined to UCS domain.') )

		msg.append( _('Please remove installation media from drive and' ) )
		msg.append( _('press ENTER to reboot this system.') )

		# do not display UMC hint on basesystem
		if self.profile.get('system_role') not in ['basesystem']:
			msg.append( '' )
			msg.append( _('Administrative frontend:') )
			msg.append( '' )

			fqdn = '%s.%s' % (self.profile.get('hostname'), self.profile.get('domainname'))

			# open xchange stuff
			if self.profile.get('ox_primary_maildomain'):
				msg.append( _('  Open-Xchange frontend'))
				msg.append( _('    https://%s/ox6/') % fqdn[:80] )
				if self.profile.get('hostaddress'):
					address = self.profile.get('hostaddress')
					if ':' in address:
						address = '[%s]' % address
					msg.append( _('    https://%s/ox6/') % address )
				msg.append( _('    Administrative account name: oxadmin') )
				msg.append( '' )

			msg.append( _('  Univention Management Console') )
			msg.append( _('    https://%s/umc/') % fqdn[:80] )
			if self.profile.get('hostaddress'):
				address = self.profile.get('hostaddress')
				if ':' in address:
					address = '[%s]' % address
				msg.append( _('    https://%s/umc/') % address )
			msg.append( _('    Administrative account name: Administrator') )

		msg.append( '' )
		msg.append( _('Additional information:   http://www.univention.de/en/download/documentation/') )
		msg.append( _('Support & Knowledge Base: http://sdb.univention.de') )

		return msg


	def get_success_msg(self):
		msg = []
		if os.path.isfile( fn_success_msg ):
			msg.append( _('The installation has been finished successfully!') )
			msg.append( '' )
			try:
				lines = open(fn_success_msg,'r').readlines()
				for line in lines:
					msg.append( line.rstrip('\r\n\t ') )
			except:
				pass
		return msg


	def get_error_msg(self):
		msg = []
		# does error message exist?
		if os.path.isfile( fn_error_msg ):
			msg.append( _('Some problems occurred during installation!') )
			msg.append( _('Please read the following error messages carefully.') )
			msg.append( _('In case of doubt a reinstallation might be reasonable.') )
			msg.append( '' )
			try:
				lines = open(fn_error_msg,'r').readlines()
				for line in lines:
					msg.append( line.rstrip('\r\n\t ') )
			except:
				pass
		return msg


	def show_ending_msg(self):
		# if auto_reboot is set then do not show this message
		if self.profile.get('auto_reboot','').lower() in ['yes', 'true']:
			return

		# disable redrawing of windows
		self.redraw_blocked = True

		self.infowin.bkgd(curses.color_pair(1))
		self.infowin.box()

		msg = self.get_error_msg()
		if not msg:
			msg = self.get_success_msg()
		if not msg:
			msg = self.create_success_msg()

		max_width = 0
		for line in msg:
			if len(line) > max_width:
				max_width = len(line.decode('utf-8'))
		width = max_width + 4
		height = len(msg) + 6

		# limit width and height
		if width >= MAX_WIDTH:
			width = MAX_WIDTH-2
		if height >= MAX_HEIGHT:
			height = MAX_HEIGHT-2
			msg = msg[:height-6]    # also limit msg list

		self.endwin = curses.newwin(height, width, (MAX_HEIGHT - height) / 2, (MAX_WIDTH - width) / 2)
		self.endwin.clear()
		self.endwin.bkgd(curses.color_pair(1))
		self.endwin.box()
		y = 2
		for line in msg:
			self.endwin.addnstr(y, 2, line, width-4, curses.color_pair(1))
			y += 1
		self.endwin.addstr(height - 3, width / 2 - 3,"[ OK ]", curses.color_pair(3))
		self.endwin.refresh()
		# wait for user input
		while 1:
			c = self.stdscr.getch()
			# exit if ENTER, F12 or Space is pressed
			if c == 10 or c == 276 or c == 32:
				break

		# reenable redrawing of windows
		self.redraw_blocked = False
		# redraw windows
		self.stdscr.refresh()
		self.draw()
		self.draw_info()


	def draw_info(self):
		# redraw disabled by show_ending_msg()
		if self.redraw_blocked:
			return

		# update info window
		self.infowin.bkgd(curses.color_pair(1))
		self.infowin.box()

		msg = _('''Congratulations! The installation of %(name)s is currently running.

Base information of local system:
  Hostname:      %(hostname)s
  System role:   %(systemrole)s
  IP address:    %(address)s


Please visit the following websites to learn more about %(name)s:

- Quickstart Guide:
  http://wiki.univention.de/index.php?title=UCS_Quickstart/en

- Manuals and further information:
  http://www.univention.de/en/download/documentation/

- Forum:
  http://forum.univention.de

- Support & Knowledge Base:
  http://sdb.univention.de
''') % { 'name': self.options.name,
		 'hostname': '%s.%s' % (self.profile.get('hostname','unknown'), self.profile.get('domainname','example.com')),
		 'systemrole': systemrole2name[ self.profile.get('system_role','domaincontroller_master') ],
		 'address': self.profile.get('hostaddress', _('dynamic')),
		 }

		y = 2
		for line in msg.split('\n'):
			self.infowin.addstr(y, 3, line)
			y += 1

		self.infowin.refresh()


	def draw(self):
		# redraw disabled by show_ending_msg()
		if self.redraw_blocked:
			return

		# sanity check
		if self.progress > 100:
			self.progress = 100

		# calculate
		barlength = self.width-12
		solid_cnt = int(float(barlength) /100 * self.progress)
		empty_cnt = barlength - solid_cnt

		# update progress window
		self.win.bkgd(curses.color_pair(1))
		self.win.box()
		self.win.addstr(0, 3, self.title, curses.color_pair(1))

		# draw script message
		self.win.addstr(2, 3, self.script_msg.ljust(barlength), curses.color_pair(1))

		# draw bar
		for i in xrange(3,3+solid_cnt):
			self.win.addch(4, i, ' ', curses.color_pair(2) | curses.A_REVERSE)
		for i in xrange(3+solid_cnt, 3+barlength):
			self.win.addch(4, i, curses.ACS_BOARD, curses.color_pair(2))
		self.win.addstr(4, 3+barlength+1, '%.1f%%' % self.progress , curses.color_pair(1))

		# draw progress message
		self.win.addstr(6, 3, self.progress_msg.ljust(barlength), curses.color_pair(1))

		self.win.refresh()


	def read_data(self):
		# check if available data is present
		readevents = select.select( [ self.fd_read ], [], [], 1 )[0]
		if readevents:
			# add data to inbuffer
			self.inbuffer += os.read( self.fd_read, 100*1024 )
			if '\n' in self.inbuffer:
				# at least on line is available: split lines and put remainder back to inbuffer
				lines = self.inbuffer.split('\n')
				self.inbuffer = lines[-1]
				del lines[-1]
				open('/tmp/progress.log','a').write( '\n'.join(lines) + '\n' )

				for line in lines:
					# __SCRIPT__ will be emitted by progress.py just before the next script gets called to transfer script filename to read_data()
					if line.startswith('__SCRIPT__:'):
						if self.current_script:
							# transfer remaining progress of script to current progress counter
							self.progress += self.script2progress[ self.current_script ].remaining_percentage
						self.current_script = line.split(':',1)[1]
						self.progress_msg = ''

					# __MSG__ will be emitted by scripts for displaying any kind of data
					elif line.startswith('__MSG__:'):
						self.script_msg = line.split(':',1)[1]

					# __SUBMSG__ will be emitted by scripts for displaying any kind of data
					elif line.startswith('__SUBMSG__:'):
						self.progress_msg = line.split(':',1)[1]

					# __STEPS__ will be emitted by scripts like 50_packages.py to inform read_data() how often the triggers should fire
					# value has to be an integer
					elif line.startswith('__STEPS__:'):
						self.script2progress[ self.current_script ].set_steps( int(line.split(':',1)[1]) )
						self.log('PROGRESS: STEPS=%s' % self.script2progress[ self.current_script ].steps)
						self.log('PROGRESS: PPSTEP=%s' % self.script2progress[ self.current_script ].percentage_per_step)
						self.log('PROGRESS: PERCENTAGE=%s' % self.script2progress[ self.current_script ].percentage)
						self.log('PROGRESS: REMPERCENT=%s' % self.script2progress[ self.current_script ].remaining_percentage)

					# if a script is running then test line against triggerlist
					elif self.current_script:
						for trigger in self.script2progress[ self.current_script ].triggerlist:
							if trigger.search(line):
								progressinfo = self.script2progress[ self.current_script ]  # get ProgressInfo object
								if progressinfo.remaining_percentage >= progressinfo.percentage_per_step:
									# more than one step remaining in "remaining_percentage" ==> add only one "step" to progress counter
									self.progress += progressinfo.percentage_per_step
									progressinfo.remaining_percentage -= progressinfo.percentage_per_step
								else:
									# less than one step remaining in "remaining_percentage" ==> add "remaining_percentage" to progress counter
									self.progress += progressinfo.remaining_percentage
									progressinfo.remaining_percentage = 0

					if line.startswith('pmstatus:') or line.startswith('dlstatus:'):
						# display apt-get messages
						self.progress_msg = i18n_aptget.translate( line.split(':',4)[3] )

					elif line.startswith('I: '):
						# translate and return only valid translations (i.e. reg exp matches)
						msg = i18n_debootstrap.translate(line, strict=True)
						if msg:
							self.progress_msg = msg

					elif line.startswith('__JOINSCRIPT__ '):
						# display name of current joinscript
						self.progress_msg = _('Current joinscript: ') + line.replace('__JOINSCRIPT__ ','')


	def stop_gui(self):
		# stop curses
		self.stdscr.keypad(0)
		curses.nocbreak()
		curses.echo()
		curses.endwin()


	def process_input(self):
		while self.thread.is_alive():
			self.read_data()
			self.draw()
		self.draw()


	def run(self):
		self.prepare_gui()
		self.create_communication_pipe()
		time.sleep(3)
		self.thread = threading.Thread(target=self.call_installer_scripts)
		self.thread.start()
		self.process_input()
		self.stop_gui()


	def create_communication_pipe(self):
		pipe_read, pipe_write = os.pipe()
		if pipe_read != 9 and pipe_write !=9:
			os.dup2(pipe_write, 9)
		else:
			print 'Failed to dup2 write filedescriptor'
			sys.exit(1)
		self.fd_read = pipe_read
		self.fd_write = pipe_write


	def log(self, msg):
		if self.logfile:
			open(self.logfile, 'a+').write('\nPROGRESS: %s\n' % msg)


	def call_cmd(self, cmd, shell=False):
		self.log('calling %s' % cmd)
		exitcode = subprocess.call(cmd, shell=shell)
		if exitcode:
			self.log('%s returned exitcode %s' % (cmd, exitcode))


	def call_installer_scripts(self):
		IGNORE_LIST = [ '00_scripts.sh', '95_completemsg.sh', '99_reboot.sh' , '06_network.sh']

		# regenerate locale: 05_language.py wrote locale to /etc/locale.gen
		self.call_cmd('/sbin/locale-gen 2>&1 >> /tmp/installer.log', shell=True)

		# /etc/locale.gen should contain a string like "de_DE.UTF-8 UTF-8"
		locale = open('/etc/locale.gen','r').read().strip()
		if ' ' in locale:
			locale = locale.split(' ',1)[0]

		# write small helper to /tmp/
		fd = open('/tmp/progress.lib','w')
		fd.write('export INSTALLERLOCALE=%s\n' % locale)
		fd.write('export TEXTDOMAIN="installer"\n')
		fd.write('export TEXTDOMAINDIR="/lib/univention-installer/locale"\n')
		fd.close()

		# send message to main loop and run 00_scripts.sh
		os.write(self.fd_write, '__MSG__:%s\n' % _('Preparing installation'))
		self.call_cmd(['/lib/univention-installer-scripts.d/00_scripts.sh'])

		# get list of scripts to be called
		scripts = [ os.path.join('/lib/univention-installer-scripts.d/', x) for x in os.listdir('/lib/univention-installer-scripts.d/') if x not in IGNORE_LIST ]
		scripts.sort()

		# accumulate all progress steps if "percentage" is not negative
		# negative "percentage" indicates main_script that gains the remainder to fill up to 100%
		cumulative_progress = 0.0
		main_script = None
		for script in scripts:
			scriptname = os.path.basename(script)
			if not scriptname in self.script2progress:
				self.script2progress[scriptname] = ProgressInfo( percentage=self.default_percentage, steps=1 )
			if self.script2progress[scriptname].percentage < 0:	 # main script has progress value lower than 0
				main_script = self.script2progress[scriptname]		 # ==> save reference to this object
				self.log('main script == %s' % scriptname)
			else:
				# otherwise accumulate progress parts
				cumulative_progress += self.script2progress[scriptname].percentage
				self.log('script %s ==> %s%%' % (script, self.script2progress[scriptname].percentage))

		if main_script:
			# assign remaining percentage to main script
			main_script.percentage = 100.0 - cumulative_progress
			main_script.remaining_percentage = main_script.percentage
			self.log('main_script ==> %s%%' % main_script.percentage)

		for script in scripts:
			self.log('script %s' % script)

			if os.path.exists('/tmp/logging'):

				# create installation.log on target system
				fn = '/instmnt/var/log/univention/installation.log'
				try:
					# create directory if missing
					if not os.path.isdir( os.path.dirname(fn) ):
						os.makedirs( os.path.dirname(fn) )

					# create logfile and fix logfile permissions
					open(fn, 'a+') # create file / touch it
					gid_adm = grp.getgrnam('adm')[2]  # get gid of group "adm"
					os.chown(fn, 0, gid_adm)		  # chown root:adm $fn
					os.chmod(fn, 0640)				  # chmod 0640 $fn
				except OSError, e:
					self.log('EXCEPTION occured while creating %s: %s' % (fn, str(e)))

				# switch to new logfile
				self.logfile = fn

				# copy installer.log to target system
				fn = '/instmnt/var/log/univention/installer.log'
				if os.path.exists('/tmp/installer.log') and not os.path.exists(fn):
					self.log('switching logfile')
					open(fn,'a+').write( open('/tmp/installer.log','r').read() )  # append old file to new file
					os.chown(fn, 0, gid_adm)		  # chown root:adm $fn
					os.chmod(fn, 0640)				  # chmod 0640 $fn

				# copy debootstrap.log to target system
				fnA = '/tmp/debootstrap.log.gz'
				fnB = '/instmnt/var/log/univention/debootstrap.log.gz'
				if os.path.exists(fnA):
					shutil.copyfile(fnA, fnB)
					os.chown(fnB, 0, gid_adm)
					os.chmod(fnB, 0640)

			# send script name to main loop
			os.write(self.fd_write, '\n__SCRIPT__:%s\n' % os.path.basename(script))
			if os.path.exists('/tmp/logging'):
				self.call_cmd( '/bin/sh %s < /dev/tty1 2>&1 | tee -a /instmnt/var/log/univention/installation.log > /dev/tty6' % script, shell=True)
			else:
				self.call_cmd( '/bin/sh %s < /dev/tty1 2>&1 | tee -a /tmp/installer.log > /dev/tty6' % script, shell=True)

			self.log('script %s done' % script)

		self.progress = 100
		os.write(self.fd_write, '__MSG__:%s\n' % _('Installation complete'))

		self.log('compressing logfile and displaying complete message')

		# disable logging
		self.logfile = '/tmp/progress.log'

		if os.path.exists('/tmp/logging'):
			self.call_cmd(['gzip', '/instmnt/var/log/univention/installation.log'])
			self.call_cmd(['gzip', '/instmnt/var/log/univention/installer.log'])

		time.sleep(1)

		self.show_ending_msg()

		os.write(self.fd_write, '__MSG__:%s\n' % _('Preparing reboot'))
		time.sleep(1)
		self.stdscr.clear()
		self.stdscr.refresh()
		self.call_cmd(['/lib/univention-installer-scripts.d/99_reboot.sh'])


def main():
	parser = optparse.OptionParser( )
	parser.add_option('-t', '--edition', dest='edition', default='', action='store', help='product edition')
	parser.add_option('-c', '--codename', dest='codename', default='', action='store', help='product codename')
	parser.add_option('-e', '--extension', dest='extension', default='', action='store', help='product extension')
	parser.add_option('-v', '--version', dest='version', default='3.0', action='store', help='product version')
	parser.add_option('-n', '--name', dest='name', default='Univention Corporate Server', action='store', help='product name')
	(options, args) = parser.parse_args()

	# get and set language
	if os.path.isfile(fn_language):
		language = linecache.getline(fn_language, 1).strip('\n')
		os.environ['LANGUAGE'] = language

	init_translations()

	win = ProgressDialog(options)
	win.run()


if __name__ == '__main__':
	main()
