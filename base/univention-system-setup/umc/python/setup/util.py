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
import univention_baseconfig
import time

PATH_SYS_CLASS_NET = '/sys/class/net'
PATH_SETUP_SCRIPTS = '/usr/lib/univention-system-setup/scripts'
LOG_FILE = '/var/log/univention/setup.log'

# list of all needed UCR variables
UCR_VARIABLES = [
	# language
	'locale', 'locale/default',
	# keyboard
	'locale/keymap',
	# basis
	'hostname', 'domainname', 'ldap/base', 'windows/domain',
	# net
	#'gateway',
	#'nameserver1', 'nameserver2', 'nameserver3',
	#'dns/forwarder1', 'dns/forwarder2', 'dns/forwarder3',
	#'proxy/http'
]

# net
#for idev in range(0,4):
#	for iattr in ['address' 'broadcast' 'netmask' 'network' 'type']:
#		UCR_VARIABLES.append('interfaces/eth%d/%s' % (idev, iattr))
#		if iattr != 'type':
#			for ivirt in range(0,4):
#				UCR_VARIABLES.append('interfaces/eth%d_%d/%s' % (idev, ivirt, iattr))

def timestamp():
	return time.strftime('%Y-%m-%d %H:%M:%S')

def load_values():
#	mapping={
#		'server/role':			'system_role',
#		'ldap/base':			'ldap_base',
#		'windows/domain':		'windows_domain',
#		'nameserver1':			'nameserver_1',
#		'nameserver2':			'nameserver_2',
#		'nameserver3':			'nameserver_3',
#		'dns/forwarder1':		'dns_forwarder_1',
#		'dns/forwarder2':		'dns_forwarder_2',
#		'dns/forwarder3':		'dns_forwarder_3',
#		'proxy/http':			'http_proxy',
#		'locale/default':		'locale_default',
#		'locale':				'locales',
#		'locale/keymap':		'keymap',
#		'ssl/email':			'ssl_email',
#		'ssl/country':			'ssl_country',
#		'ssl/organization':		'ssl_organization',
#		'ssl/organizationalunit':	'ssl_organizationalunit',
#		'ssl/state':			'ssl_state',
#		'ssl/locality':			'ssl_locality',
#		'ox/mail/domain/primary':	'ox_primary_maildomain',
#	}
#	for i in range(0,4):
#		mapping['interfaces/eth%d/type' % (i)]='eth%d_type' % (i)
#		mapping['interfaces/eth%d/address' % (i)]='eth%d_ip' % (i)
#		mapping['interfaces/eth%d/broadcast' % (i)]='eth%d_broadcast' % (i)
#		mapping['interfaces/eth%d/netmask' % (i)]='eth%d_netmask' % (i)
#		mapping['interfaces/eth%d/network' % (i)]='eth%d_network' % (i)
#		for j in range(0,4):
#			mapping['interfaces/eth%d_%d/address' % (i,j)]='eth%d_%d_ip' % (i,j)
#			mapping['interfaces/eth%d_%d/broadcast' % (i,j)]='eth%d_%d_broadcast' % (i,j)
#			mapping['interfaces/eth%d_%d/netmask' % (i,j)]='eth%d_%d_netmask' % (i,j)
#			mapping['interfaces/eth%d_%d/network' % (i,j)]='eth%d_%d_network' % (i,j)

	# load UCR variables
	baseConfig=univention_baseconfig.baseConfig()
	baseConfig.load()
	values = dict([ (ikey, baseConfig[ikey]) for ikey in UCR_VARIABLES ])

	#other values
	values['root_password'] = ''

	# get timezone
	if os.path.exists('/etc/timezone'):
		f=open('/etc/timezone')
		values['timezone']=f.readline().strip()
		f.close()
	else:
		values['timezone']=''


#	#             scan packages:
#	values['packages']=[]
#
#	installed_packages=[]
#	packages = package_cache.packages
#	for package in packages:
#		if package.current_state == 6 and package.inst_state == 0:
#			installed_packages.append(package.name)
#
#	import package_list
#	for category in package_list.PackageList:
#		for component in category['Packages']:
#			for p in component['Packages']:
#				debug('p=%s' % p )
#				if p in installed_packages:
#					values['packages'].append(p)
#
#	self.result=copy.deepcopy(values)

	return values;

def write_profile(values):
	cache_file=open('/var/cache/univention-system-setup/profile',"w+")
	for ientry in values.iteritems():
		cache_file.write('%s="%s"\n\n' % ientry)
	cache_file.close()

def run_scripts():
	for root, dirs, files in os.walk(PATH_SETUP_SCRIPTS): 
		# ignore the root
		if root == PATH_SETUP_SCRIPTS:
			continue

		# execute all scripts in subdirectories
		files.sort()
		for ifile in files:
			# get the full script path
			ipath = os.path.join(root, ifile)

			# write header before executing script file
			f = open(LOG_FILE, 'a')
			f.write('### %s (%s) ###\n' % (ipath[len(PATH_SETUP_SCRIPTS)+1:], timestamp()))
			f.close();

			# launch script
			os.system('%s >>/var/log/univention/setup.log 2>&1' % ipath)

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
	except (ipaddr.NetmaskValueError, ipaddr.AddressValueError):
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
	except (ipaddr.NetmaskValueError, ipaddr.AddressValueError):
		return False
	return True

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

