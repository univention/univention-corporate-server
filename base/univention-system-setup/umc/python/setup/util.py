#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: system setup
#
# Copyright 2011 Univention GmbH
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

import ipaddr
import os
import tempfile
import subprocess
import threading
import univention.config_registry
import time
import fnmatch
import re
import sys
import apt
import psutil

from univention.management.console.log import MODULE

if not '/lib/univention-installer/' in sys.path:
	sys.path.append('/lib/univention-installer/')
import package_list

ucr=univention.config_registry.ConfigRegistry()
ucr.load()

PATH_SYS_CLASS_NET = '/sys/class/net'
PATH_SETUP_SCRIPTS = '/usr/lib/univention-system-setup/scripts'
PATH_JOIN_SCRIPT = '/usr/lib/univention-system-setup/scripts/setup-join.sh'
PATH_PROFILE = '/var/cache/univention-system-setup/profile'
LOG_FILE = '/var/log/univention/setup.log'
PATH_BROWSER_PID = '/var/cache/univention-system-setup/browser.pid'
PATH_PASSWORD_FILE = '/var/cache/univention-system-setup/secret'
CMD_ENABLE_EXEC = ['/usr/share/univention-updater/enable-apache2-umc', '--no-restart']
CMD_DISABLE_EXEC = '/usr/share/univention-updater/disable-apache2-umc'


# list of all needed UCR variables
UCR_VARIABLES = [
	# common
	'server/role',
	# language
	'locale', 'locale/default',
	# keyboard
	'locale/keymap',
	# basis
	'hostname', 'domainname', 'ldap/base', 'windows/domain',
	# net: ipv4
	'gateway',
	'nameserver1', 'nameserver2', 'nameserver3',
	'dns/forwarder1', 'dns/forwarder2', 'dns/forwarder3',
	'proxy/http',
	# net: ipv6
	'ipv6/gateway',
	# ssl
	'ssl/common', 'ssl/locality', 'ssl/country', 'ssl/state',
	'ssl/organization', 'ssl/organizationalunit', 'ssl/email',
]

# net
for idev in range(0,4):
	for iattr in ('address', 'netmask', 'type'):
		UCR_VARIABLES.append('interfaces/eth%d/%s' % (idev, iattr))
		if iattr != 'type':
			for ivirt in range(0,4):
				UCR_VARIABLES.append('interfaces/eth%d_%d/%s' % (idev, ivirt, iattr))

def timestamp():
	return time.strftime('%Y-%m-%d %H:%M:%S')

def load_values():
	# load UCR variables
	ucr.load()
	values = dict([ (ikey, ucr[ikey]) for ikey in UCR_VARIABLES ])

	# net: ipv6 interfaces
	for k, v in ucr.items():
		if fnmatch.fnmatch(k, 'interfaces/eth*/ipv6/*'):
			values[k] = v

	# see whether the system has been joined or not
	values['joined'] = os.path.exists('/var/univention-join/joined')

	# root password
	values['root_password'] = ''

	# get timezone
	if os.path.exists('/etc/timezone'):
		f=open('/etc/timezone')
		values['timezone']=f.readline().strip()
		f.close()
	else:
		values['timezone']=''

	# get installed components
	values['components'] = ' '.join([icomp['id'] for icomp in get_installed_components()])

	return values

def pre_save(newValues, oldValues):
	'''Modify the final dict before saving it to the profile file.'''

	# add broadcast addresses for ipv4 addresses using the ipaddr library
	regIpv4Device = re.compile(r'interfaces/(?P<device>[^/]+)/(?P<type>.*)')
	for ikey, ival in newValues.iteritems():
		m = regIpv4Device.match(ikey)
		if m:
			vals = m.groupdict()
			if vals['type'] == 'address' or vals['type'] == 'netmask':
				# new value might already exist
				broadcastKey = 'interfaces/%s/broadcast' % vals['device']
				networkKey = 'interfaces/%s/network' % vals['device']
				maskKey = 'interfaces/%s/netmask' % vals['device']
				addressKey = 'interfaces/%s/address' % vals['device']

				# try to compute the broadcast address
				address = newValues.get(addressKey, oldValues.get(addressKey, ''))
				mask = newValues.get(maskKey, oldValues.get(maskKey, ''))
				broadcast = get_broadcast(address, mask)
				network = get_network(address, mask)
				if broadcast:
					# we could compute a broadcast address
					newValues[broadcastKey] = broadcast
				if network:
					# we could compute a network address
					newValues[networkKey] = network
	
	# add lists with all packages that should be removed/installed on the system
	if 'components' in newValues:
		regSpaces = re.compile(r'\s+')
		selectedComponents = set(regSpaces.split(newValues.get('components', '')))
		currentComponents = set([icomp['id'] for icomp in get_installed_components()])
		allComponents = set([ icomp['id'] for icomp in get_components() ])

		# get all packages that shall be removed
		removeComponents = list(allComponents & (currentComponents - selectedComponents))
		newValues['packages_remove'] = ' '.join([ i.replace(':', ' ') for i in removeComponents ])

		# get all packages that shall be installed
		installComponents = list(allComponents & (selectedComponents - currentComponents))
		newValues['packages_install'] = ' '.join([ i.replace(':', ' ') for i in installComponents ])
		

def write_profile(values):
	cache_file=open(PATH_PROFILE,"w+")
	for ikey, ival in values.iteritems():
		newVal = ival
		if ival == None:
			newVal = ''
		cache_file.write('%s="%s"\n\n' % (ikey, newVal))
	cache_file.close()

def run_scripts(restartServer=False):
	# write header before executing scripts
	f = open(LOG_FILE, 'a')
	f.write('\n\n=== RUNNING SETUP SCRIPTS (%s) ===\n\n' % timestamp())
	f.flush()

	# make sure that UMC servers and apache will not be restartet
	subprocess.call(CMD_DISABLE_EXEC, stdout=f, stderr=f)

	for root, dirs, files in os.walk(PATH_SETUP_SCRIPTS): 
		# ignore the root
		if root == PATH_SETUP_SCRIPTS:
			continue

		# execute all scripts in subdirectories
		files.sort()
		for ifile in files:
			# get the full script path
			ipath = os.path.join(root, ifile)

			# launch script
			subprocess.call(ipath, stdout=f, stderr=f)

	# enable execution of servers again
	subprocess.call(CMD_ENABLE_EXEC, stdout=f, stderr=f)

	if restartServer:
		f.write('=== Restart of UMC server and web server (%s) ===\n' % timestamp())
		f.flush()
		subprocess.call(['/etc/init.d/univention-management-console-server', 'restart'], stdout=f, stderr=f)
		subprocess.call(['/etc/init.d/univention-management-console-web-server', 'restart'], stdout=f, stderr=f)

	f.write('\n=== DONE (%s) ===\n\n' % timestamp())
	f.close()

def run_joinscript(_username = None, password = None):
	# write header before executing join script
	f = open(LOG_FILE, 'a')
	f.write('\n\n=== RUNNING SETUP JOIN SCRIPT (%s) ===\n\n' % timestamp())
	f.flush()

	# write password file
	if _username and password:
		f = open(PATH_PASSWORD_FILE, 'w')
		f.write('%s' % password)
		f.close()
		os.chmod(PATH_PASSWORD_FILE, 0600)

		# sanitize username
		reg = re.compile('[^ a-zA-Z_1-9-]')
		username = reg.sub('_', _username)

		# run join scripts
		subprocess.call([PATH_JOIN_SCRIPT, '--dcaccount', username, '--password_file', PATH_PASSWORD_FILE], stdout=f, stderr=f)

		# remove password file
		os.remove(PATH_PASSWORD_FILE)
	else:
		# run join scripts
		subprocess.call(PATH_JOIN_SCRIPT, stdout=f, stderr=f)

	f.write('\n=== DONE (%s) ===\n\n' % timestamp())
	f.close()

def shutdown_browser():
	try:
		fpid = open(PATH_BROWSER_PID)
		strpid = fpid.readline().strip()
		pid = int(strpid)
		p = psutil.Process(pid)
		p.kill()
		return True
	except IOError:
		MODULE.error('cannot open browser PID file: %s' % PATH_BROWSER_PID)
	except ValueError:
		MODULE.error('browser PID is not a number: "%s"' % strpid)
	except psutil.NoSuchProcess:
		MODULE.error('cannot kill process with PID: %s' % pid)
	return False

def detect_interfaces():
	"""
	Function to detect network interfaces in local sysfs.
	The loopback interface "lo" will be filtered out.
	Returns a list of dicts with the entries 'name' and 'mac'.
	"""
	interfaces = []

	dirnames = os.listdir(PATH_SYS_CLASS_NET)
	for dirname in dirnames:
		if os.path.isdir( os.path.join(PATH_SYS_CLASS_NET, dirname) ) and dirname.startswith('eth'):
			idev = { 'name': dirname }
			# try to read mac address of interface
			try:
				idev['mac'] = open(os.path.join(PATH_SYS_CLASS_NET, dirname, 'address'),'r').read().strip()
			except:
				pass
			interfaces.append(idev)

	return interfaces

def get_broadcast(ip, netmask):
	try:
		ip = ipaddr.IPv4Network('%s/%s')
		return ip.broadcast
	except ValueError:
		pass
	return None

def get_network(ip, netmask):
	try:
		ip = ipaddr.IPv4Network('%s/%s')
		return ip.network
	except ValueError:
		pass
	return None

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
	cmd='/sbin/dhclient -1 -lf /tmp/dhclient.leases -pf %s -sf /lib/univention-installer/dhclient-script-wrapper -e dhclientscript_outputfile="%s" %s' % (pidfilename, tempfilename, interface)
	p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

	# read from stderr until timeout, following recipe of subprocess.communicate()
	def _readerthread(fh, stringbufferlist):
		stringbufferlist.append(fh.read())

	stderr = []
	stderr_thread = threading.Thread(target=_readerthread,
									args=(p.stderr, stderr))
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

	file = open(tempfilename)
	dhcp_dict={}
	for line in file.readlines():
		key, value = line.strip().split(':', 1)
		dhcp_dict[key]=value.lstrip()
	file.close()
	os.unlink(tempfilename)
	return dhcp_dict

def get_components():
	'''Returns a list of components that may be installed on the current system.'''

	# get all package sets that are available for the current system role
	role = ucr.get('server/role')
	pkglist = [ jpackage for icategory in package_list.PackageList 
			for jpackage in icategory['Packages']
			if 'all' in jpackage['Possible'] or role in jpackage['Possible'] ]

	# generate a unique ID for each component
	for ipkg in pkglist:
		ipkg['Packages'].sort()
		ipkg['id'] = ':'.join(ipkg['Packages'])
	return pkglist

def get_installed_packages():
	'''Returns a list of all installed packages on the system.'''
	cache = apt.Cache()
	return [ p.name for p in cache if p.is_installed ]

def get_installed_components():
	'''Returns a list of components that are currently fully installed on the system.'''
	allPackages = set(get_installed_packages())
	allComponents = get_components()
	return [ icomp for icomp in allComponents if not len(set(icomp['Packages']) - allPackages) ]

# from univention-installer/installer/modules/70_net.py
def is_proxy(proxy):
	if proxy and proxy != 'http://' and proxy != 'https://':
		if not proxy.startswith('http://') and not proxy.startswith('https://'):
			return False
	return True

def is_ipaddr(addr):
	try:
		x = ipaddr.IPAddress(addr)
	except ValueError:
		return False
	return True

def is_ipv4addr(addr):
	try:
		x = ipaddr.IPv4Address(addr)
	except ValueError:
		return False
	return True

def is_ipv4netmask(addr_netmask):
	try:
		x = ipaddr.IPv4Network(addr_netmask)
	except (ValueError, ipaddr.NetmaskValueError, ipaddr.AddressValueError):
		return False
	return True

def is_ipv6addr(addr):
	try:
		x = ipaddr.IPv6Address(addr)
	except ValueError:
		return False
	return True

def is_ipv6netmask(addr_netmask):
	try:
		x = ipaddr.IPv6Network(addr_netmask)
	except (ValueError, ipaddr.NetmaskValueError, ipaddr.AddressValueError):
		return False
	return True

# from univention-installer/installer/objects.py
def is_hostname(hostname):
	_re=re.compile("^[a-z]([a-z0-9-]*[a-z0-9])*$")
	if _re.match(hostname):
		return True
	return False

def is_domainname(domainname):
	_re=re.compile("^([a-z0-9]([a-z0-9-]*[a-z0-9])*[.])*[a-z0-9]([a-z0-9-]*[a-z0-9])*$")
	if _re.match(domainname):
		return True
	return False

def is_windowsdomainname(domainname):
	_re=re.compile("^([A-Z]([A-Z0-9-]*[A-Z0-9])*[.])*[A-Z]([A-Z0-9-]*[A-Z0-9])*$")
	if _re.match(domainname):
		return True
	return False

def is_domaincontroller(domaincontroller):
	_re=re.compile("^[a-zA-Z].*\..*$")
	if _re.match(domaincontroller):
		return True
	return False

# new defined methods
def is_ascii(str):
	try:
		str.decode("ascii")
		return True
	except:
		return False

