#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: system setup
#
# Copyright 2011-2014 Univention GmbH
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

import copy
import ipaddr
import os
import tempfile
import subprocess
import threading
import univention.config_registry
import time
import re
import psutil
import csv
import os.path
import simplejson as json
import random
import urllib2
from contextlib import contextmanager

from univention.lib.i18n import Translation, Locale
from univention.management.console.log import MODULE
from univention.management.console.modules import UMC_CommandError

try:
	# execute imports in try/except block as during build test scripts are
	# triggered that refer to the netconf python submodules... and this
	# reference triggers the import below
	import dns.resolver
	import dns.reversename
	import dns.exception
	import univention.management.console.modules.appcenter.app_center as app_center
	from univention.lib.package_manager import PackageManager
except ImportError as e:
	MODULE.warn('Ignoring import error: %s' % e)

_ = Translation('univention-management-console-module-setup').translate

ucr = univention.config_registry.ConfigRegistry()
ucr.load()

PATH_SYS_CLASS_NET = '/sys/class/net'
PATH_SETUP_SCRIPTS = '/usr/lib/univention-system-setup/scripts/'
PATH_CLEANUP_PRE_SCRIPTS = '/usr/lib/univention-system-setup/cleanup-pre.d/'
PATH_CLEANUP_POST_SCRIPTS = '/usr/lib/univention-system-setup/cleanup-post.d/'
PATH_JOIN_SCRIPT = '/usr/lib/univention-system-setup/scripts/setup-join.sh'
PATH_PROFILE = '/var/cache/univention-system-setup/profile'
LOG_FILE = '/var/log/univention/setup.log'
PATH_BROWSER_PID = '/var/cache/univention-system-setup/browser.pid'
PATH_PASSWORD_FILE = '/var/cache/univention-system-setup/secret'
CMD_ENABLE_EXEC = ['/usr/share/univention-updater/enable-apache2-umc', '--no-restart']
CMD_ENABLE_EXEC_WITH_RESTART = '/usr/share/univention-updater/enable-apache2-umc'
CMD_DISABLE_EXEC = '/usr/share/univention-updater/disable-apache2-umc'
CITY_DATA_PATH = '/usr/share/univention-system-setup/city_data.json'
COUNTRY_DATA_PATH = '/usr/share/univention-system-setup/country_data.json'

RE_IPV4_TYPE = re.compile('^interfaces/[^/]*/type$')
RE_LOCALE = re.compile(r'([^.@ ]+).*')

# list of all needed UCR variables
UCR_VARIABLES = [
	# common
	'server/role',
	# language
	'locale', 'locale/default',
	# keyboard
	'xorg/keyboard/options/XkbLayout', 'xorg/keyboard/options/XkbModel',
	'xorg/keyboard/options/XkbOptions',
	# basis
	'hostname', 'domainname', 'ldap/base', 'windows/domain',
	# net: ipv4
	'gateway',
	'nameserver1', 'nameserver2', 'nameserver3',
	'dns/forwarder1', 'dns/forwarder2', 'dns/forwarder3',
	'proxy/http',
	# net: ipv6
	'ipv6/gateway',
	'interfaces/primary',
	# ssl
	'ssl/common', 'ssl/locality', 'ssl/country', 'ssl/state',
	'ssl/organization', 'ssl/organizationalunit', 'ssl/email',
]

def timestamp():
	return time.strftime('%Y-%m-%d %H:%M:%S')

def is_system_joined():
	return os.path.exists('/var/univention-join/joined')

def load_values():
	# load UCR variables
	ucr.load()
	values = dict([ (ikey, ucr[ikey]) for ikey in UCR_VARIABLES ])

	# net
	from univention.management.console.modules.setup.network import Interfaces
	interfaces = Interfaces()
	values['interfaces'] = interfaces.to_dict()
	values['physical_interfaces'] = [idev['name'] for idev in detect_interfaces()]

	# see whether the system has been joined or not
	values['joined'] = is_system_joined()

	# root password
	values['root_password'] = ''

	# get timezone
	if os.path.exists('/etc/timezone'):
		with open('/etc/timezone') as fd:
			values['timezone'] = fd.readline().strip()
	else:
		values['timezone']=''

	return values

def _xkeymap(keymap):
	'''Determine the x-keymap which belongs to 'keymap' by
	parsing /usr/share/univention-system-setup/locale/all-kmaps'''

	xkeymap = {'layout' : '', 'variant' : ''}
	fp = open('/usr/share/univention-system-setup/locale/all-kmaps', 'r')
	for line in fp:
		line_split = line.strip('\n').split(':')
		if line_split[1] == keymap:
			xkeymap['layout'] = line_split[2].split(' ')[0]
			if len(line_split[2].split(' ')) == 2:
				xkeymap['variant'] = line_split[2].split(' ')[1]
			break
	fp.close()
	return xkeymap

def auto_complete_values_for_join(newValues, current_locale=None):
	# try to automatically determine the domain
	if newValues['server/role'] != 'domaincontroller_master' and not newValues.get('domainname'):
		ucr.load()
		for nameserver in ('nameserver1', 'nameserver2', 'nameserver3'):
			if newValues.get('domainname'):
				break
			newValues['domainname'] = get_ucs_domain(newValues.get(nameserver, ucr.get(nameserver)))
		if not newValues['domainname']:
			raise Exception(_('Cannot automatically determine the domain. Please specify the server\'s fully qualified domain name.'))

	# add lists with all packages that should be removed/installed on the system
	if 'components' in newValues:
		selectedComponents = set(newValues.get('components', []))
		currentComponents = set()
		for iapp in get_apps():
			if iapp['is_installed']:
				for ipackages in (iapp['defaultpackages'], iapp['defaultpackagesmaster']):
					currentComponents = currentComponents.union(ipackages)

		# set of all available software packages
		allComponents = set()
		for iapp in get_apps():
			for ipackages in (iapp['defaultpackages'], iapp['defaultpackagesmaster']):
				allComponents = allComponents.union(ipackages)

		# get all packages that shall be removed
		removeComponents = list(allComponents & (currentComponents - selectedComponents))
		newValues['packages_remove'] = ' '.join(removeComponents)

		# get all packages that shall be installed
		installComponents = list(allComponents & (selectedComponents - currentComponents))
		newValues['packages_install'] = ' '.join(installComponents)

	if newValues['server/role'] == 'domaincontroller_master':
		# add newValues for SSL UCR variables
		if 'locale/default' in newValues:
			default_locale = Locale(newValues['locale/default'])
		else:
			default_locale = current_locale or Locale('en_US.UTF-8:UTF-8')
		newValues['ssl/state'] = default_locale.territory
		newValues['ssl/locality'] = default_locale.territory
		newValues['ssl/organization'] = newValues.get('organization', default_locale.territory)
		newValues['ssl/organizationalunit'] = 'Univention Corporate Server'
		newValues['ssl/email'] = 'ssl@{domainname}'.format(**newValues)

	if 'locale' not in newValues:
		# auto set the locale variable if not specified
		# make sure that en_US is supported in any case
		newValues['locale'] = newValues.get('locale/default', '')

		# make sure that the locale of the current session is also supported
		# ... otherwise the setup scripts will fail after regenerating the
		# locale data (in 20_language/10language)
		forcedLocales = ['en_US.UTF-8:UTF-8'] # we need en_US locale as default language
		if current_locale:
			current_locale = '{0}:{1}'.format(str(current_locale), current_locale.codeset)
			forcedLocales.append(current_locale)
		for ilocale in forcedLocales:
			if ilocale not in newValues['locale']:
				newValues['locale'] = '%s %s' % (newValues['locale'], ilocale)

	if 'windows/domain' not in newValues:
		newValues['windows/domain'] = domain2windowdomain(newValues.get('domainname'))

	return newValues

def pre_save(newValues):
	'''Modify the final dict before saving it to the profile file.'''

	# network interfaces
	from univention.management.console.modules.setup.network import Interfaces
	if 'interfaces' in newValues:
		interfaces = Interfaces()
		interfaces.from_dict(newValues.pop('interfaces'))
		interfaces.check_consistency()
		newValues.update(dict((key, value or '') for key, value in interfaces.to_ucr().iteritems()))

def write_profile(values):
	old_umask = os.umask(0177)
	try:
		with open(PATH_PROFILE, "w+") as cache_file:
			for ikey, ival in values.iteritems():
				cache_file.write('%s="%s"\n' % (ikey, ival or ''))
	finally:
		os.umask(old_umask)

class ProgressState( object ):
	def __init__( self ):
		self.reset()

	def reset( self ):
		self.name = ''
		self.message = ''
		self._percentage = 0.0
		self.fraction = 0.0
		self.fractionName = ''
		self.steps = 1
		self.step = 0
		self.max = 100
		self.errors = []
		self.critical = False

	@property
	def percentage( self ):
		return ( self._percentage + self.fraction * ( self.step / float( self.steps ) ) ) / self.max * 100

	def __eq__( self, other ):
		return self.name == other.name and self.message == other.message and self.percentage == other.percentage and self.fraction == other.fraction and self.steps == other.steps and self.step == other.step and self.errors == other.errors and self.critical == other.critical

	def __ne__( self, other ):
		return not self.__eq__( other )

	def __nonzero__( self ):
		return bool( self.name or self.message or self.percentage or self._join_error or self._misc_error )

class ProgressParser( object ):
	# regular expressions
	NAME = re.compile( '^__NAME__: *(?P<key>[^ ]*) (?P<name>.*)\n$' )
	MSG = re.compile( '^__MSG__: *(?P<message>.*)\n$' )
	STEPS = re.compile( '^__STEPS__: *(?P<steps>.*)\n$' )
	STEP = re.compile( '^__STEP__: *(?P<step>.*)\n$' )
	JOINERROR = re.compile( '^__JOINERR__: *(?P<error_message>.*)\n$' )
	ERROR = re.compile( '^__ERR__: *(?P<error_message>.*)\n$' )

	# fractions of setup scripts
	FRACTIONS = {
		'05_role/10role' : 40,
		'10_basis/12domainname' : 15,
		'10_basis/14ldap_basis' : 20,
		'30_net/10interfaces' : 20,
		'50_software/10software' : 50,
		'90_postjoin/10admember' : 30,
	}

	# current status
	def __init__( self ):
		self.current = ProgressState()
		self.old = ProgressState()
		self.reset()

	def reset( self ):
		ucr.load()
		self.current.reset()
		self.old.reset()
		self.fractions = copy.copy( ProgressParser.FRACTIONS )
		system_role = ucr.get('server/role')
		joined = is_system_joined()
		wizard_mode = not system_role and not joined
		if not wizard_mode:
			# when not wizard_mode, the software page is not rendered
			#   do not use more than 50% of the progress bar for something
			#   that cannot happen
			self.fractions.pop('50_software/10software', None)
		self.calculateFractions()

	def calculateFractions( self ):
		MODULE.info( 'Calculating maximum value for fractions ...' )
		for category in filter( lambda x: os.path.isdir( os.path.join( PATH_SETUP_SCRIPTS, x ) ), os.listdir( PATH_SETUP_SCRIPTS ) ):
			cat_path = os.path.join( PATH_SETUP_SCRIPTS, category )
			for script in filter( lambda x: os.path.isfile( os.path.join( cat_path, x ) ), os.listdir( cat_path ) ):
				name = '%s/%s' % ( category, script )
				if not name in self.fractions:
					self.fractions[ name ] = 1

		self.current.max = sum( self.fractions.values() )
		MODULE.info( 'Calculated a maximum value of %d' % self.current.max )

	@property
	def changed( self ):
		if self.current != self.old:
			MODULE.info( 'Progress state has changed!' )
			self.old = copy.copy( self.current )
			return True
		return False

	def parse( self, line ):
		# start new component name
		match = ProgressParser.NAME.match( line )
		if match is not None:
			self.current.name, self.current.fractionName = match.groups()
			self.current.message = ''
			self.current._percentage += self.current.fraction
			self.current.fraction = self.fractions.get( self.current.name, 1.0 )
			self.current.step = 0 # reset current step
			self.current.steps = 1
			return True

		# new status message
		match = ProgressParser.MSG.match( line )
		if match is not None:
			self.current.message = match.groups()[ 0 ]
			return True

		# number of steps
		match = ProgressParser.STEPS.match( line )
		if match is not None:
			try:
				self.current.steps = int( match.groups()[ 0 ] )
				self.current.step = 0
				return True
			except ValueError:
				pass

		# current step
		match = ProgressParser.STEP.match( line )
		if match is not None:
			try:
				self.current.step = float( match.groups()[ 0 ] )
				if self.current.step > self.current.steps:
					self.current.step = self.current.steps
				return True
			except ValueError:
				pass

		# error message: why did the join fail?
		match = ProgressParser.JOINERROR.match( line )
		if match is not None:
			error = '%s: %s' % (self.current.fractionName, match.groups()[ 0 ])
			self.current.errors.append( error )
			self.current.critical = True
			return True

		# error message: why did the script fail?
		match = ProgressParser.ERROR.match( line )
		if match is not None:
			error = '%s: %s' % (self.current.fractionName, match.groups()[ 0 ])
			self.current.errors.append( error )
			return True

		return False

def sorted_files_in_subdirs( directory ):
	for entry in sorted(os.listdir(directory)):
		path = os.path.join(directory, entry)
		if os.path.isdir(path):
			for filename in sorted(os.listdir(path)):
				yield os.path.join(path, filename)





def run_scripts( progressParser, restartServer = False ):
	# write header before executing scripts
	f = open(LOG_FILE, 'a')
	f.write('\n\n=== RUNNING SETUP SCRIPTS (%s) ===\n\n' % timestamp())
	f.flush()

	# read-only handle to LOG_FILE for observing file end
	fr = open(LOG_FILE)

	# start observing at the end of the file
	fr.seek(0, os.SEEK_END)
	lastPos = fr.tell()

	# next full line to pass to the progressParser
	fullLine = ''

	# make sure that UMC servers and apache will not be restartet
	subprocess.call( CMD_DISABLE_EXEC, stdout = f, stderr = f )

	for scriptpath in sorted_files_in_subdirs( PATH_SETUP_SCRIPTS ):
			# launch script
			MODULE.info('Running script %s\n' % scriptpath)
			p = subprocess.Popen( scriptpath, stdout = f, stderr = subprocess.STDOUT )

			while p.poll() is None:
				fr.seek(0, os.SEEK_END) # update file handle
				fr.seek(lastPos, os.SEEK_SET) # continue reading at last position

				currentLine = fr.readline() # try to read until next line break
				if not currentLine:
					continue

				fullLine += currentLine
				lastPos += len(currentLine)
				if currentLine[-1] == '\n':
					progressParser.parse(fullLine)
					fullLine = ''

	fr.close()

	# enable execution of servers again
	subprocess.call(CMD_ENABLE_EXEC, stdout=f, stderr=f)

	if restartServer:
		f.write('=== Restart of UMC server and web server (%s) ===\n' % timestamp())
		f.flush()
		subprocess.call(['/etc/init.d/univention-management-console-server', 'restart'], stdout=f, stderr=f)
		subprocess.call(['/etc/init.d/univention-management-console-web-server', 'restart'], stdout=f, stderr=f)

	f.write('\n=== DONE (%s) ===\n\n' % timestamp())
	f.close()

@contextmanager
def _temporary_password_file(password):
	# write password file
	fp = open(PATH_PASSWORD_FILE, 'w')
	fp.write('%s' % password)
	fp.close()
	os.chmod(PATH_PASSWORD_FILE, 0600)
	try:
		yield PATH_PASSWORD_FILE
	finally:
		# remove password file
		os.remove(PATH_PASSWORD_FILE)

def run_joinscript( progressParser, _username, password ):
	# write header before executing join script
	f = open(LOG_FILE, 'a')
	f.write('\n\n=== RUNNING SETUP JOIN SCRIPT (%s) ===\n\n' % timestamp())
	f.flush()

	progressParser.fractions[ 'setup-join.sh' ] = 50
	progressParser.current.max = sum( progressParser.fractions.values() )
	def runit( command ):
		p = subprocess.Popen( command, stdout = subprocess.PIPE, stderr = subprocess.STDOUT )
		while True:
			line = p.stdout.readline()
			if not line:
				break
			progressParser.parse( line )
			f.write( line )
		p.wait()

	cmd = [ PATH_JOIN_SCRIPT ]
	if _username and password:

		with _temporary_password_file(password) as password_file:
			# sanitize username
			reg = re.compile('[^ a-zA-Z_1-9-]')
			username = reg.sub('_', _username)

			# run join scripts
			runit( cmd + [ '--dcaccount', username, '--password_file', password_file ] )

	else:
		# run join scripts
		runit( cmd )

	f.write('\n=== DONE (%s) ===\n\n' % timestamp())
	f.close()

def cleanup():
	# write header before executing scripts
	f = open(LOG_FILE, 'a')
	f.write('\n\n=== Cleanup (%s) ===\n\n' % timestamp())
	f.flush()

	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()

	# The browser was only started, if system/setup/boot/start is true
	if ucr.is_true('system/setup/boot/start', False):
		MODULE.info('Appliance mode: try to shut down the browser')
		try:
			fpid = open(PATH_BROWSER_PID)
			strpid = fpid.readline().strip()
			pid = int(strpid)
			p = psutil.Process(pid)
			p.kill()
		except IOError:
			MODULE.warn('cannot open browser PID file: %s' % PATH_BROWSER_PID)
		except ValueError:
			MODULE.error('browser PID is not a number: "%s"' % strpid)
		except psutil.NoSuchProcess:
			MODULE.error('cannot kill process with PID: %s' % pid)

		# Maybe the system-setup CMD tool was started
		for p in psutil.process_iter():
			if p.name == 'python2.7' and '/usr/share/univention-system-setup/univention-system-setup' in p.cmdline:
				p.kill()

	# Run cleanup-pre scripts
	run_scripts_in_path(PATH_CLEANUP_PRE_SCRIPTS, f, "cleanup-pre")

	# unset the temporary interface if set
	for var in ucr.keys():
		if RE_IPV4_TYPE.match(var) and ucr.get(var) == 'appliance-mode-temporary':
			f.write('unset %s' % var)
			keys = [var]
			for k in ['netmask', 'address', 'broadcast', 'network']:
				keys.append(var.replace('/type', '/%s' % k))
			univention.config_registry.handler_unset(keys)
			# Shut down temporary interface
			subprocess.call(['ifconfig', var.split('/')[1].replace('_', ':'), 'down'])

	# force a restart of UMC servers and apache
	subprocess.call( CMD_DISABLE_EXEC, stdout = f, stderr = f )
	subprocess.call( CMD_ENABLE_EXEC_WITH_RESTART, stdout = f, stderr = f )

	# Run cleanup-post scripts
	run_scripts_in_path(PATH_CLEANUP_POST_SCRIPTS, f, "cleanup-post")

	f.write('\n=== DONE (%s) ===\n\n' % timestamp())
	f.flush()
	f.close()

	return True

def run_scripts_in_path(path, logfile, category_name=""):
	logfile.write('\n=== Running %s scripts (%s) ===\n' % (category_name, timestamp()))
	logfile.flush()

	if os.path.isdir(path):
		for filename in sorted(os.listdir(path)):
			logfile.write('= Running %s\n' % filename);
			logfile.flush()
			try:
				subprocess.call(os.path.join(path, filename), stdout=logfile, stderr=logfile)
			except (OSError, IOError):
				logfile.write('%s' % (traceback.format_exc(),))
			logfile.flush()

	logfile.write('\n=== done (%s) ===\n' % timestamp())
	logfile.flush()

def detect_interfaces():
	"""
	Function to detect network interfaces in local sysfs.
	The loopback interface "lo" will be filtered out.
	Returns a list of dicts with the entries 'name' and 'mac'.
	"""
	interfaces = []

	if not os.path.exists(PATH_SYS_CLASS_NET):
		return interfaces
	for dirname in os.listdir(PATH_SYS_CLASS_NET):
		pathname = os.path.join(PATH_SYS_CLASS_NET, dirname)
		if not os.path.isdir(pathname):
			continue
		# filter out lo, etc. interfaces
		if open(os.path.join(pathname, 'type'), 'r').read().strip() not in ('1', '2', '3', '4', '5', '6', '7', '8', '15', '19'):
			continue
		# filter out bridge, bond devices
		if any(os.path.exists(os.path.join(pathname, path)) for path in ('bridge', 'bonding')):
			continue
		# filter out vlan devices
		if '.' in dirname:
			continue
		mac = None
		try:
			# try to read mac address
			mac = open(os.path.join(pathname, 'address'), 'r').read().strip()
		except (OSError, IOError):
			pass
		interfaces.append({'name': dirname, 'mac': mac})

	return interfaces

def dhclient(interface, timeout=None):
	"""
	perform DHCP request for specified interface. If succesful, returns a dict
	similar to the following:
	{
		'address': '10.200.26.51',
		'broadcast': '10.200.26.255',
		'domainname': 'univention.qa',
		'gateway': '',
		'nameserver_1': '10.200.26.27',
		'nameserver_2': '',
		'nameserver_3': '',
		'netmask': '255.255.255.0'
	}
	"""
	tempfilename = tempfile.mkstemp( '.out', 'dhclient.', '/tmp' )[1]
	pidfilename = tempfile.mkstemp( '.pid', 'dhclient.', '/tmp' )[1]
	cmd = ('/sbin/dhclient',
			'-1',
			'-lf', '/tmp/dhclient.leases',
			'-pf', pidfilename,
			'-sf', '/usr/share/univention-system-setup/dhclient-script-wrapper',
			'-e', 'dhclientscript_outputfile=%s' % (tempfilename,),
			interface)
	MODULE.info('Launch dhclient query via command: %s' % (cmd, ))
	p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

	# read from stderr until timeout, following recipe of subprocess.communicate()
	def _readerthread(fh, stringbufferlist):
		stringbufferlist.append(fh.read())

	stderr = []
	stderr_thread = threading.Thread(target=_readerthread, args=(p.stderr, stderr))
	stderr_thread.setDaemon(True)
	stderr_thread.start()
	stderr_thread.join(timeout)

	if stderr:
		stderr=stderr[0]

	# note: despite '-1' background dhclient never seems to terminate
	try:
		dhclientpid = int(open(pidfilename,'r').read().strip('\n\r\t '))
		os.kill(dhclientpid, 15)
		time.sleep(1.0) # sleep 1s
		os.kill(dhclientpid, 9)
	except:
		pass
	try:
		os.unlink(pidfilename)
	except:
		pass

	dhcp_dict={}
	MODULE.info('dhclient returned the following values:')
	with open(tempfilename) as file:
		for line in file.readlines():
			key, value = line.strip().split('=', 1)
			dhcp_dict[key]=value[1:-1]
			MODULE.info('  %s: %s' % (key, dhcp_dict[key]))
	os.unlink(tempfilename)

	# see wether the nameserver is part of a UCS domain
	if 'nameserver_1' in dhcp_dict:
		dhcp_dict['is_ucs_nameserver_1'] = bool(get_ucs_domain(dhcp_dict['nameserver_1']))
		MODULE.info('Check wether the nameserver %s is a UCS nameserver -> %s' % (dhcp_dict['nameserver_1'], dhcp_dict['is_ucs_nameserver_1']))

	return dhcp_dict

_apps = None
def get_apps(no_cache=False):
	global _apps
	if _apps and not no_cache:
		return _apps

	package_manager = PackageManager(
		info_handler=MODULE.process,
		step_handler=None,
		error_handler=MODULE.warn,
		lock=False,
		always_noninteractive=True,
	)
	package_manager.set_finished() # currently not working. accepting new tasks

	# circumvent download of categories.ini file
	app_center.Application._get_category_translations(fake=True)
	try:
		applications = app_center.Application.all(only_local=True)
	except (urllib2.HTTPError, urllib2.URLError) as e:
		# should not happen as we only access cached, local data
		raise UMC_CommandError(_('Could not query App Center: %s') % e)
	_apps = [iapp.to_dict(package_manager) for iapp in applications if iapp.get('withoutrepository')]
	return _apps

def is_proxy(proxy):
	if proxy and proxy != 'http://' and proxy != 'https://':
		if not proxy.startswith('http://') and not proxy.startswith('https://'):
			return False
	return True

def is_ipaddr(addr):
	try:
		ipaddr.IPAddress(addr)
	except ValueError:
		return False
	return True

def is_ipv4addr(addr):
	try:
		ipaddr.IPv4Address(addr)
	except ValueError:
		return False
	return True

def is_ipv4netmask(addr_netmask):
	try:
		ipaddr.IPv4Network(addr_netmask)
	except (ValueError, ipaddr.NetmaskValueError, ipaddr.AddressValueError):
		return False
	return True

def is_ipv6addr(addr):
	try:
		ipaddr.IPv6Address(addr)
	except ValueError:
		return False
	return True

def is_ipv6netmask(addr_netmask):
	try:
		ipaddr.IPv6Network(addr_netmask)
	except (ValueError, ipaddr.NetmaskValueError, ipaddr.AddressValueError):
		return False
	return True

def is_hostname(hostname):
	return is_hostname.RE.match(hostname) is not None
is_hostname.RE = re.compile("^[a-z]([a-z0-9-]*[a-z0-9])*$")

def is_domainname(domainname):
	"""
	Check if domainname is a valid DNS domainname accoring to RFC952/1123.
	>>> is_domainname('foo')
	True
	>>> is_domainname('f00.bar')
	True
	>>> is_domainname('-f.bar')
	False
	>>> is_domainname('f-.bar')
	False
	>>> is_domainname('f..bar')
	False
	>>> is_domainname('#.bar')
	False
	>>> is_domainname('1234567890123456789012345678901234567890123456789012345678901234.bar')
	False
	"""
	return all(is_domainname.RE.match(_) for _ in domainname.split('.'))
is_domainname.RE = re.compile(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$', re.I)

def is_windowsdomainname(domainname):
	return is_windowsdomainname.RE.match(domainname) is not None and len(domainname) < 14
is_windowsdomainname.RE = re.compile(r"^[A-Z](?:[A-Z0-9-]*[A-Z0-9])?$")

def domain2windowdomain(domainname):
	if '.' in domainname:
		windomain = domainname.split('.')[0]
	windomain = windomain.upper()

	invalidChars = re.compile(r"^[^A-Z]*([A-Z0-9-]*?)[^A-Z0-9]*$")
	match = invalidChars.match(windomain)
	if match:
		windomain = match.group(1)
	else:
		windomain = ''

	windomain = windomain[:15] ## enforce netbios limit

	if not windomain:
		# fallback name
		windomain = 'UCSDOMAIN'
	return windomain

def is_domaincontroller(domaincontroller):
	return is_domaincontroller.RE.match(domaincontroller) is not None
is_domaincontroller.RE = re.compile("^[a-zA-Z].*\..*$")

# new defined methods
def is_ascii(str):
	try:
		str.decode("ascii")
		return True
	except:
		return False

def _get_dns_resolver(nameserver):
	resolver = dns.resolver.Resolver()
	resolver.lifetime = 10  # make sure that we get an early timeout
	resolver.nameservers = [nameserver]
	return resolver

def is_ucs_domain(nameserver, domain):
	if not nameserver or not domain:
		return False

	# register nameserver
	resolver = _get_dns_resolver(nameserver)

	# perform a SRV lookup
	try:
		resolver.query('_domaincontroller_master._tcp.%s' % domain, 'SRV')
		return True
	except dns.resolver.NXDOMAIN:
		MODULE.warn('No valid UCS domain (%s) at nameserver %s!' % (domain, nameserver))
	return False

def get_ucs_domain(nameserver):
	domain = get_domain(nameserver)
	if not is_ucs_domain(nameserver, domain):
		return None
	return domain

def get_domain(nameserver):
	master = get_master(nameserver)
	if master:
		return '.'.join(master.split('.')[1:])

def get_master(nameserver):
	# register nameserver
	resolver = _get_dns_resolver(nameserver)

	# perform a reverse lookup
	try:
		reverse_address = dns.reversename.from_address(nameserver)
		reverse_lookup = resolver.query(reverse_address, 'PTR')
		if not len(reverse_lookup):
			return None

		fqdn = reverse_lookup[0]
		parts = [i for i in fqdn.target.labels if i]
		domain = '.'.join(parts)

		return domain
	except dns.resolver.NXDOMAIN as exc:
		MODULE.warn('Lookup for nameserver %s failed: %s' % (nameserver, exc))
	except dns.exception.Timeout as exc:
		MODULE.warn('Lookup for nameserver %s timed out: %s' % (nameserver, exc))
	return None

def get_available_locales(pattern, category='language_en'):
	'''Return a list of all available locales.'''
	try:
		fsupported = open('/usr/share/i18n/SUPPORTED')
		flanguages = open('/usr/share/univention-system-setup/locale/languagelist')
	except:
		MODULE.error( 'Cannot find locale data for languages in /usr/share/univention-system-setup/locale' )
		return

	# get all locales that are supported
	rsupported = csv.reader(fsupported, delimiter=' ')
	supportedLocales = { 'C': True }
	for ilocale in rsupported:
		# we only support UTF-8
		if ilocale[1] != 'UTF-8':
			continue

		# get the locale
		m = RE_LOCALE.match(ilocale[0])
		if m:
			supportedLocales[m.groups()[0]] = True

	category = {'langcode': 0, 'language_en': 1, 'language': 2, 'countrycode': 4, 'fallbacklocale': 5}.get(category, 1)

	# open all languages
	rlanguages = csv.reader(flanguages, delimiter=';')
	locales = []
	for ilang in rlanguages:
		if ilang[0].startswith('#'):
			continue

		if not pattern.match(ilang[category]):
			continue

		# each language might be spoken in several countries
		ipath = '/usr/share/univention-system-setup/locale/short-list/%s.short' % ilang[0]
		if os.path.exists(ipath):
			try:
				# open the short list with countries belonging to the language
				fshort = open(ipath)
				rshort = csv.reader(fshort, delimiter='\t')

				# create for each country a locale entry
				for jcountry in rshort:
					code = '%s_%s' % (ilang[0], jcountry[0])
					if code in supportedLocales:
						locales.append({
							'id': '%s.UTF-8:UTF-8' % code,
							'label': '%s (%s)' % (ilang[1], jcountry[2])
						})
				continue
			except Exception:
				pass

		# get the locale code
		code = ilang[0]
		if code.find('_') < 0 and code != 'C':
			# no underscore -> we need to build the locale ourself
			code = '%s_%s' % (ilang[0], ilang[4])

		# final entry
		if code in supportedLocales:
			locales.append({
				'id': '%s.UTF-8:UTF-8' % code,
				'label': ilang[1]
			})

	return locales

_city_data = None
def get_city_data():
	global _city_data
	if not _city_data:
		with open(CITY_DATA_PATH) as infile:
			_city_data = json.load(infile)
	return _city_data

_country_data = None
def get_country_data():
	global _country_data
	if not _country_data:
		with open(COUNTRY_DATA_PATH) as infile:
			_country_data = json.load(infile)
	return _country_data

def get_random_nameserver(country):
	ipv4_servers = country.get('ipv4') or country.get('ipv4_erroneous') or [None]
	ipv6_servers = country.get('ipv6') or country.get('ipv6_erroneous') or [None]
	return dict(
		ipv4_nameserver=random.choice(ipv4_servers),
		ipv6_nameserver=random.choice(ipv6_servers),
	)


