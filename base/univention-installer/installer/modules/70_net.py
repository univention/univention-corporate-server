#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: system configuration
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

import re
import curses
from objects import *
from local import _
import inspect
import tempfile
import ipaddr
import subprocess
import threading
import random

PATH_SYS_CLASS_NET = '/sys/class/net'
LEN_IPv4_ADDR = 15
LEN_IPv6_ADDR = 40


class NetworkInterface(object):
	def __init__(self, name):
		self.name = name
		self.macaddr = None      # MAC address
		self.IPv4_addr = None    # IPv4 address
		self.IPv4_dhcp = False   # DHCP
		self.IPv6_addr = None    # IPv6 address
		self.IPv6_ra = False     # accept router advertisements?

	def __str__(self):
		return 'NetIf(%s)' % self.name

	def __repr__(self):
		return 'NetIf(%s)' % self.name


def cmp_NetworkInterfaces(x,y):
	"""
	Compare function for network interface names
	Interfaces starting with "eth" will be listed first. All other
	interfaces will be listed alphabetically.
	e.g. eth0, eth1, atm0, atm1, tunnel0, wlan0, wlan1
	"""
	if x.name.startswith('eth') and not y.name.startswith('eth'):
		return -1
	elif not x.name.startswith('eth') and y.name.startswith('eth'):
		return 1

	return cmp(x.name, y.name)


class object(content):
	def __init__(self, *args, **kwargs):
		content.__init__(self, *args, **kwargs)
		self.debug('__init__()')

		self.interfaces = []
		self.dummy_interface = False
		self.ask_forwarder = True
		self.warning_shown_for_ipv6addr = []  # list of IPv6 addresses

		# boolean: True, if edition "oxae" is specified
		self.is_ox = 'oxae' in self.cmdline.get('edition',[])

	def depends(self):
		self.debug('depends()')
		return {'system_role': ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver', 'basesystem', 'managed_client', 'mobile_client'] }

	def debug(self, txt):
		"""
		print special debug message with current code line
		"""
		info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
		line = info[1]
		content.debug(self, 'NETWORK:%d: %s' % (line,txt))

	def kill_subwin(self):
		"""
		Overloading method kill_subwin() to prevent that the user is able to close a subwindow by
		pressing ESC key if a subsubwindow is present.
		"""
		if hasattr(self.sub, 'sub'):
			delattr(self.sub,'sub')
			self.draw()
		elif hasattr(self.sub, 'exit'):
			self.sub.exit()
			self.draw()
		elif hasattr(self, 'sub'):
			delattr(self,'sub')
			self.draw()
		self.draw()

	def dhclient(self, interface, timeout=None):
		"""
		perform DHCP request for specified interface
		"""
		self.debug('DHCP broadcast on %s' % interface)
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
			self.debug('Reading dhclient pidfile')
			dhclientpid = int(open(pidfilename,'r').read().strip('\n\r\t '))
			self.debug('Sending signal 15 to pid %s' % dhclientpid)
			os.kill(dhclientpid, 15)
			time.sleep(1.0) # sleep 1s
			self.debug('Sending signal 9 to pid %s' % dhclientpid)
			os.kill(dhclientpid, 9)
			self.debug('dhclient daemon stopped successfully')
		except:
			self.debug('Stopping dhclient daemon stopped here')
		try:
			os.unlink(pidfilename)
		except:
			pass

		self.debug('DHCP output: %s' % stderr)
		file = open(tempfilename)
		dhcp_dict={}
		for line in file.readlines():
			key, value = line.strip().split('=', 1)
			dhcp_dict[key]=value.lstrip().strip('"')
		self.debug('DHCP answer: %s' % dhcp_dict)
		file.close()
		os.unlink(tempfilename)
		return dhcp_dict

	def detect_interfaces(self):
		"""
		Function to detect network interfaces in local sysfs.
		The loopback interface "lo" will be filtered out.
		"""
		self.debug('detect_interfaces()')
		self.interfaces = []

		dirnames = os.listdir(PATH_SYS_CLASS_NET)
		for dirname in dirnames:
			if os.path.isdir( os.path.join(PATH_SYS_CLASS_NET, dirname) ) and dirname.startswith('eth'):
				self.interfaces.append( NetworkInterface(dirname) )
				self.debug('Adding interface %s' % dirname )
				# try to read mac address of interface
				try:
					self.interfaces[-1].macaddr = open(os.path.join(PATH_SYS_CLASS_NET, dirname, 'address'),'r').read().strip()
					self.debug('MAC address: %s' % self.interfaces[-1].macaddr)
				except:
					pass

		self.interfaces.sort( cmp_NetworkInterfaces )

		if not self.interfaces:
			self.debug('No interface has been found')
			self.interfaces.append( NetworkInterface('eth0') )
			self.debug('Dummy interface has been added')
			self.dummy_interface = True

	def get_interface(self, name):
		"""
		get interface object with specified name
		"""
		for i in self.interfaces:
			if i.name == name:
				return i
		return None

	def is_proxy(self, proxy):
		if proxy and proxy != 'http://' and proxy != 'https://':
			if not proxy.startswith('http://') and not proxy.startswith('https://'):
				self.debug('is_proxy() ==> INVALID PROXY ==> %s' % proxy)
				return False
		return True

	def is_ipaddr(self, addr):
		try:
			x = ipaddr.IPAddress(addr)
		except ValueError:
			return False
		return True

	def is_ipv4addr(self, addr):
		try:
			x = ipaddr.IPv4Address(addr)
		except ValueError:
			return False
		return True

	def is_ipv4netmask(self, addr_netmask):
		try:
			x = ipaddr.IPv4Network(addr_netmask)
		except (ipaddr.NetmaskValueError, ipaddr.AddressValueError):
			return False
		return True

	def is_ipv6addr(self, addr):
		try:
			x = ipaddr.IPv6Address(addr)
		except ValueError:
			return False
		return True

	def is_ipv6netmask(self, addr_netmask):
		try:
			x = ipaddr.IPv6Network(addr_netmask)
		except (ipaddr.NetmaskValueError, ipaddr.AddressValueError):
			return False
		return True

	def start(self):
		self.debug('start()')
		self.debug('all_results=%r' % self.all_results)

		# system is server if not one of specified roles
		self.serversystem = not( self.all_results.get('system_role') in ['managed_client', 'mobile_client', 'fatclient', 'mobileclient', 'managedclient'] )

		# read interface information from system
		self.detect_interfaces()

		# get all interface names used in self.all_results
		REinterfaces = re.compile('^eth(\d+)_')
		iface_list= set([ 'eth%s' % REinterfaces.search(i).group(1) for i in self.all_results.keys() if REinterfaces.search(i) ])
		for name in iface_list:
			# try to get IPv4 address by reading IP address and netmask...
			addr_netmask = '%s/%s' % (self.all_results.get('%s_ip' % name), self.all_results.get('%s_netmask' % name))
			try:
				IPv4_addr = ipaddr.IPv4Network(addr_netmask)
			except (ipaddr.AddressValueError, ipaddr.NetmaskValueError):
				pass
			else:
				# ... all other values (broadcast and network) get calculated
				self.container['%s_ip' % name] = str(IPv4_addr.ip)
				self.container['%s_netmask' % name] = str(IPv4_addr.netmask)
				self.container['%s_broadcast' % name] = str(IPv4_addr.broadcast)
				self.container['%s_network' % name] = str(IPv4_addr.network)

			# set DHCP flag
			self.container['%s_type' % name] = ''
			IPv4_dhcp = ( self.all_results.get('%s_type' % name) in [ 'dynamic', 'dhcp' ] )
			if IPv4_dhcp:
				self.container['%s_type' % name] = 'dynamic'

			# set RA flag
			IPv6_ra = ( self.all_results.get('%s_acceptra' % name,'').lower().strip() in [ '1', 'yes', 'true' ] )
			self.container['%s_acceptra' % name] = str(IPv6_ra).lower()
			# try to get IPv4 address
			addr_netmask = '%s/%s' % (self.all_results.get('%s_ip6' % name), self.all_results.get('%s_prefix6' % name))
			try:
				IPv6_addr = ipaddr.IPv6Network(addr_netmask)
			except (ipaddr.AddressValueError, ipaddr.NetmaskValueError):
				pass
			else:
				self.container['%s_ip6' % name] = str(IPv6_addr.ip)
				self.container['%s_prefix6' % name] = str(IPv6_addr.prefixlen)

		for key in  ['gateway', 'gateway6', 'proxy_http', 'nameserver_1', 'nameserver_2', 'nameserver_3', 'dns_forwarder_1', 'dns_forwarder_2', 'dns_forwarder_3']:
			if self.all_results.get(key):
				self.container[key] = self.all_results.get(key)

	def put_result(self, results):
		self.debug('put_result()')
		content.put_result(self, results)

	def profile_prerun(self):
		self.debug('profile_prerun()')
		self.start()

	def profile_complete(self):
		self.debug('profile_complete()')

		for key in [ 'gateway6', 'gateway', 'nameserver_1', 'nameserver_2', 'nameserver_3',
					 'dns_forwarder_1', 'dns_forwarder_2', 'dns_forwarder_3',
					 ]:
			if self.check(key):
				self.debug('check failed for %s' % key)
				return False

		# check variables for existing interfaces
		for iface in self.interfaces:
			self.debug('testing interface %s' % (iface.name))
			for key in [ '%s_type', '%s_ip', '%s_netmask', '%s_broadcast', '%s_network', '%s_ip6', '%s_prefix6', '%s_acceptra' ]:
				var = key % iface.name
				if self.check(var):
					self.debug('check failed for %s' % (var))
					return False

		# is ip address
		invalid = _("Following value is invalid: ")
		for key, name in ( ('gateway', _('IPv4 Gateway')),
						   ('gateway6', _('IPv6 Gateway')),
						   ('nameserver_1', _('Domain DNS Server')),
						   ('dns_forwarder_1', _('External DNS Server')),
						   ):
			self.debug('testing %s' % key)
			if self.all_results.get(key) and not self.is_ipaddr(self.all_results.get(key,'')):
				if not self.ignore(key):
					self.message = invalid + name
					self.debug(self.message)
					return False

		# test proxy string
		proxy = self.all_results.get('proxy_http','').strip()
		self.debug('PROXY=%s' % proxy)
		if proxy and proxy !='http://' and proxy !='https://':
			if not (proxy.startswith('http://') or proxy.startswith('https://')):
				if not self.ignore('proxy_http'):
					self.debug('PROXY INVALID!')
					self.message=invalid+_('Proxy, example http://10.201.1.1:8080')
					return False

		# checl ipv4 and ipv6 values
		complete_cnt = 0
		REinterfaces = re.compile('^eth(\d+)_')
		iface_list= set([ 'eth%s' % REinterfaces.search(i).group(1) for i in self.all_results.keys() if REinterfaces.search(i) ])
		for interface in self.interfaces:
			name = interface.name
			# dhcp
			dhcpComplete = False
			if self.all_results.get("%s_type" % name) in ['dynamic', 'dhcp']:
				dhcpComplete = True
			# ipv4
			ipv4complete = False
			for key in ('ip', 'netmask', 'broadcast', 'network'):
				if not self.all_results.get('%s_%s' % (name, key)):
					break
			else:
				ipv4complete = True
			# ipv6
			ipv6complete = False
			for key in ('ip6', 'prefix6'):
				if not self.all_results.get('%s_%s' % (name, key)):
					break
			else:
				ipv6complete = True
			if ipv4complete or ipv6complete or dhcpComplete:
				complete_cnt += 1

		if complete_cnt < 1:
			if not self.ignore('interfaces'):
				self.message = _("You have to configure one or more network interfaces.")
				return False

		# activate network in profile mode
		self.activateNetwork(self.all_results)

		return True

	#def std_button():
	#def draw():
	#def help():

	def layout(self):
		self.debug('layout()')

		## clear layout
		self.reset_layout()
		self.default_ipv4_was_set = False

		# add default buttons
		self.std_button()

		# create cardbox with one card for each interface
		cardwidth = 75
		box = cardbox(self, self.pos_y+1, self.pos_x+2, 18, cardwidth )
		cards = {}
		for i in xrange(len(self.interfaces)):
			# get interface object
			iface = self.interfaces[i]
			# create new card
			card = box.append_card(iface.name)
			cards[iface.name] = card

			# headline
			card.add_elem('TXT_NETIF1', textline(_('Settings for interface "%s"') % iface.name, 0, 1, position_parent=card))

			if iface.macaddr:
				card.add_elem('TXT_NETMAC1', textline(_('MAC address: %s') % iface.macaddr, 0, cardwidth-3, align='right', position_parent=card))

			# ADD CHECKBOX
			val_ipv4={_('Enable IPv4'): ['CB_IPv4', 0]}
			val_ipv4_cb = []
			# activate checkbox if IPv4 address is present
			if self.container.get('%s_ip' % iface.name) or self.container.get('%s_type' % iface.name) in ['dynamic', 'dhcp']:
				val_ipv4_cb = [0]
			card.add_elem('CB_IPv4', checkbox(val_ipv4, 2, 1, 30, 2, val_ipv4_cb, position_parent=card))

			# IPv4 DHCP
			cb_ipv4dhcp = []
			if self.container.get('%s_type' % iface.name) in ['dynamic', 'dhcp']:
				cb_ipv4dhcp = [0]
			val_ipv4dhcp={_('Dynamic (DHCP)'): ['dynamic',0]}
			card.add_elem('CB_IPv4DHCP', checkbox(val_ipv4dhcp, 4, 3, 18,2, cb_ipv4dhcp, position_parent=card))
			card.add_elem('BTN_DHCLIENT', button('F5-'+_('DHCP Query'), 4, 27, position_parent=card))

			# IPv4 Address
			val_ipv4addr = self.container.get('%s_ip' % iface.name, '')
			card.add_elem('TXT_IPv4ADDR', textline(_('IPv4 address'), 5, 3, position_parent=card))
			card.add_elem('INP_IPv4ADDR', input(val_ipv4addr, 5, 21, LEN_IPv4_ADDR+4, position_parent=card))

			val_ipv4netmask = self.container.get('%s_netmask' % iface.name, '')
			card.add_elem('TXT_IPv4NETMASK', textline(_('Netmask'), 6, 3, position_parent=card))
			card.add_elem('INP_IPv4NETMASK', input(val_ipv4netmask, 6, 21, LEN_IPv4_ADDR+4, position_parent=card))

			# activate checkbox if IPv6 address is present
			val_ipv6={_('Enable IPv6'): ['dynamic', 0]}
			val_ipv6_cb = []
			if self.container.get('%s_ip6' % iface.name) or self.container.get('%s_acceptra' % iface.name) == 'true':
				val_ipv6_cb = [0]
			card.add_elem('CB_IPv6', checkbox(val_ipv6, 8, 1, 30, 2, val_ipv6_cb, position_parent=card))

			# activate checkbox if dynamic interface config is enabled
			val_ipv6ra={_('Dynamic (Stateless address autoconfiguration (SLAAC))'): ['CB_IPv6_RA', 0]}
			val_ipv6ra_cb = []
			if self.container.get('%s_acceptra' % iface.name) == 'true':
				val_ipv6ra_cb = [0]
			card.add_elem('CB_IPv6RA', checkbox(val_ipv6ra, 10, 3, 60, 2, val_ipv6ra_cb, position_parent=card))

			# IPv6 address
			val_ipv6addr = self.container.get('%s_ip6' % iface.name, '')
			card.add_elem('TXT_IPv6ADDR', textline(_('IPv6 address'), 11, 3, position_parent=card))
			card.add_elem('INP_IPv6ADDR', input(val_ipv6addr, 11, 21, LEN_IPv6_ADDR+3, position_parent=card))

			# IPv6 prefix
			val_ipv6prefix = self.container.get('%s_prefix6' % iface.name, '')
			card.add_elem('TXT_IPv6PREFIX', textline(_('IPv6 prefix'), 12, 3, position_parent=card))
			card.add_elem('INP_IPv6PREFIX', input(val_ipv6prefix, 12, 21, 7, position_parent=card))

		self.cards = cards
		self.add_elem('CARDBOX1', box)
		box.set_card(0)

		self.add_elem('BTN_IF_PREV', button(_('F2-Previous Interface'), self.pos_y+19, self.pos_x+10))
		self.add_elem('BTN_IF_NEXT', button(_('F3-Next Interface'), self.pos_y+19, self.pos_x+45))

		#
		# Global Settings
		#

		# offset for global settings
		offsetGy = self.pos_y + 22
		offsetGx = self.pos_x + 2

		self.add_elem('TXT_GLOBALSETTINGS', textline(_('Global Network Settings'), offsetGy, offsetGx))

		# - IPv4 Gateway
		val_gateway4 = self.container.get('gateway', '')
		offsetGy += 2
		self.add_elem('TXT_GATEWAY4', textline(_('IPv4 Gateway'), offsetGy, offsetGx+2))
		self.add_elem('INP_GATEWAY4', input(val_gateway4, offsetGy, offsetGx+22, LEN_IPv6_ADDR+3))

		# - IPv6 Gateway
		val_gateway6 = self.container.get('gateway6','')
		offsetGy += 1
		self.add_elem('TXT_GATEWAY6', textline(_('IPv6 Gateway'), offsetGy, offsetGx+2))
		self.add_elem('INP_GATEWAY6', input(val_gateway6, offsetGy, offsetGx+22, LEN_IPv6_ADDR+3))

		offsetGy += 1
		# True, if system role is domaincontroller or system is an OX system
		self.ask_domainnameserver = ( self.all_results.get('system_role') not in ['domaincontroller_master', 'basesystem'] ) or self.is_ox
		self.debug('ask_domainnameserver=%s  (%s, %s)' % (self.ask_domainnameserver, self.all_results.get('system_role'), self.is_ox))
		if self.ask_domainnameserver:
			offsetGy += 1
			# - Domain Nameserver
			val_nameserver1 = self.container.get('nameserver_1','')
			self.add_elem('TXT_NAMESERVER1', textline(_('Domain DNS Server'), offsetGy, offsetGx+2))
			self.add_elem('INP_NAMESERVER1', input(val_nameserver1, offsetGy, offsetGx+22, LEN_IPv6_ADDR+3))
			self.add_elem('BTN_MORE_NAMESERVER', button(_('More'), offsetGy, offsetGx+22+LEN_IPv6_ADDR+4))

		# True, if system role is domaincontroller or system is an OX system
		self.ask_forwarder = ( self.all_results.get('system_role') in ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'basesystem'] ) and not self.is_ox
		self.debug('ask_forwarder=%s  (%s, %s)' % (self.ask_forwarder, self.all_results.get('system_role'), self.is_ox))
		if self.ask_forwarder:
			offsetGy += 1
			# - DNS Forwarder
			val_forwarder1 = self.container.get('dns_forwarder_1','')
			self.add_elem('TXT_FORWARDER1', textline(_('External DNS Server'), offsetGy, offsetGx+2))
			self.add_elem('INP_FORWARDER1', input(val_forwarder1, offsetGy, offsetGx+22, LEN_IPv6_ADDR+3))
			self.add_elem('BTN_MORE_FORWARDER', button(_('More'), offsetGy, offsetGx+22+LEN_IPv6_ADDR+4))

		# - Proxy
		offsetGy += 2
		val_proxyhttp = self.container.get('proxy_http','http://')
		self.add_elem('TXT_PROXYHTTP', textline(_('HTTP proxy'), offsetGy, offsetGx+2))
		self.add_elem('INP_PROXYHTTP', input(val_proxyhttp, offsetGy, offsetGx+22, LEN_IPv6_ADDR+3))

		if self.dummy_interface:
			msg = _('Currently no network card could be detected. Depending on the selected services and system role an operative network card is required to successfully complete the installation.\nPlease check the network card of the computer. If a network card is installed, try to load additional kernel modules manually. If the installation will be continued without operative network card, a virtual dummy network card will be loaded automatically to complete installation.')
			self.sub = warning(msg, self.pos_y+39, self.pos_x+93)
			self.sub.draw()

		self.update_widget_states()

	def update_widget_states(self):
		"""
		Update disabled/enabled status of elements depending on other elements
		"""
		# check if any interface has IPv4 enabled
		self.ipv4_found = False
		for card in self.cards.values():
			self.ipv4_found = self.ipv4_found or card.get_elem('CB_IPv4').result()

		# check if any interface has IPv6 enabled
		self.ipv6_found = False
		for card in self.cards.values():
			self.ipv6_found = self.ipv6_found or card.get_elem('CB_IPv6').result()

		# if no interface has been configured, and first interface is visible then activate IPv4 for first interface
		if not self.default_ipv4_was_set and not self.ipv4_found and not self.ipv6_found and self.get_elem('CARDBOX1').get_card().name == self.interfaces[0].name:
			self.get_elem('CB_IPv4').select()  # activate IPv4
			self.move_focus( self.get_elem_id('INP_IPv4ADDR') )  # set focus to IPv4 address
			self.default_ipv4_was_set = True
			self.ipv4_found = True

		# if any interface has IPv4 enabled then enable ipv4 gateway
		if self.ipv4_found:
			self.get_elem('INP_GATEWAY4').enable()
		else:
			self.get_elem('INP_GATEWAY4').disable()

		# if any interface has IPv6 enabled then enable ipv6 gateway
		if self.ipv6_found:
			self.get_elem('INP_GATEWAY6').enable()
		else:
			self.get_elem('INP_GATEWAY6').disable()

		# if IPv6 checkbox is present...
		if self.elem_exists('CB_IPv6'):
			if self.get_elem('CB_IPv6').result():
				# IPv6 is enabled ==> turn on all IPv6 elements
				for name in [ 'CB_IPv6RA', 'INP_IPv6ADDR', 'INP_IPv6PREFIX' ]:
					self.get_elem(name).set_on()
					self.get_elem(name).enable()
			else:
				# IPv6 is disabled ==> turn off all IPv6 elements
				for name in [ 'CB_IPv6RA', 'INP_IPv6ADDR', 'INP_IPv6PREFIX' ]:
					self.get_elem(name).set_off()
					self.get_elem(name).disable()

		# if IPv4 checkbox is present...
		if self.elem_exists('CB_IPv4'):
			if self.get_elem('CB_IPv4').result():
				# IPv4 is enabled ==> enable CB for DHCP
				self.get_elem('CB_IPv4DHCP').enable()
				self.get_elem('BTN_DHCLIENT').enable()
				for name in [ 'INP_IPv4ADDR', 'INP_IPv4NETMASK' ]:
					if self.get_elem('CB_IPv4DHCP').result():
						# dhcp is on ==> turn off IPv4 address fields
						self.get_elem(name).disable()
					else:
						# dhcp is off ==> turn on IPv4 address fields
						self.get_elem(name).enable()
			else:
				for name in [ 'CB_IPv4DHCP', 'BTN_DHCLIENT', 'INP_IPv4ADDR', 'INP_IPv4NETMASK' ]:
					self.get_elem(name).set_off()
					self.get_elem(name).disable()

		# enable more button if at least forwarder1 has been set
		if self.elem_exists('INP_FORWARDER1'):
			if self.get_elem('INP_FORWARDER1').result().strip():
				self.get_elem('BTN_MORE_FORWARDER').enable()
			else:
				self.get_elem('BTN_MORE_FORWARDER').disable()

		# enable more button if at least nameserver1 has been set
		if self.elem_exists('INP_NAMESERVER1'):
			if self.get_elem('INP_NAMESERVER1').result().strip():
				self.get_elem('BTN_MORE_NAMESERVER').enable()
			else:
				self.get_elem('BTN_MORE_NAMESERVER').disable()

		# set focus to current element
		self.elements[self.current].set_on()
		# copy values from elements to self.container to prevent data loss if user switches to previous installer module via F11
		self.copy_elem_to_container()
		# redraw all elements of cardbox
		self.get_elem('CARDBOX1').draw(onlyChilds=True)

		for name in [ 'INP_GATEWAY4', 'INP_GATEWAY6' ]:
			self.get_elem(name).draw()

	def copy_elem_to_container(self):
		"""
		Copy values of current elements to self.container.
		This is required in input() to prevent data loss if user switches to previous installer modules by pressing key F11
		"""
		card = self.get_elem('CARDBOX1').get_card()
		name = card.name

		# reset old values
		self.container['%s_type' % name] = ''
		self.container['%s_ip' % name] = ''
		self.container['%s_netmask' % name] = ''
		self.container['%s_network' % name] = ''
		self.container['%s_broadcast' % name] = ''
		# IPv4
		if card.get_elem('CB_IPv4').result():
			if card.get_elem('CB_IPv4DHCP').result():
				self.container['%s_type' % name] = 'dynamic'
				if self.serversystem:
					self.container['%s_ip' % name] = card.get_elem('INP_IPv4ADDR').result().strip()
					self.container['%s_netmask' % name] = card.get_elem('INP_IPv4NETMASK').result().strip()
			else:
				self.container['%s_type' % name] = ''
				self.container['%s_ip' % name] =  card.get_elem('INP_IPv4ADDR').result().strip()
				self.container['%s_netmask' % name] =  card.get_elem('INP_IPv4NETMASK').result().strip()

		# calculate broadcast and network
		result = self.addr_netmask2result( name, self.container.get('%s_ip' % name,''), self.container.get('%s_netmask' % name,''))
		if result:
			self.container.update(result)

		# IPv6
		self.container['%s_ip6' % name] = ''
		self.container['%s_prefix6' % name] = ''
		self.container['%s_acceptra' % name] = 'false'
		if card.get_elem('CB_IPv6RA').result():
			self.container['%s_acceptra' % name] = 'true'

		self.container['%s_ip6' % name] = card.get_elem('INP_IPv6ADDR').result().strip()
		self.container['%s_prefix6' % name] = card.get_elem('INP_IPv6PREFIX').result().strip()

		keylist = [ [ 'INP_GATEWAY4', 'gateway' ],
					[ 'INP_GATEWAY6', 'gateway6' ],
					[ 'INP_FORWARDER1', 'dns_forwarder_1' ],
					[ 'INP_NAMESERVER1', 'nameserver_1' ],
					[ 'INP_PROXYHTTP', 'proxy_http' ],
					]

		for elem, key in keylist:
			if self.elem_exists(elem) and self.get_elem(elem).usable():
				self.container[key] = self.get_elem(elem).result().strip()
			else:
				self.container[key] = ''

	def tab(self):
		"""
		tab() get's called if tabulator key has been pressed
		"""
		if self.current == self.get_elem_id('INP_IPv4ADDR'): # if focus is on IPv4 address field
			if not self.get_elem('CB_IPv4DHCP').result(): # and if DHCP is disabled
				addr = self.get_elem('INP_IPv4ADDR').result().strip()
				if addr and self.is_ipv4addr(addr): # and a valid IPv4 address has been entered
					element = self.get_elem('INP_IPv4NETMASK')
					if not(element.result()): # and netmask is empty ==> then set default netmask
						element.text='255.255.255.0'
						element.set_cursor(len(element.text))
						self.copy_elem_to_container()
		content.tab(self)

	def input(self,key):
		"""
		input handling
		"""
		self.debug('input(%d)  sub=%s' % (key, hasattr(self,'sub')))

		if hasattr(self,'sub'):
			if hasattr(self.sub, 'input'):
				val = self.sub.input(key)
				if not val:
					del self.sub
					self.draw()
			elif hasattr(self.sub, 'key_event'):
				self.sub.key_event(key)
			return 1
		elif key in [ 10, 32 ] and self.btn_next():
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		elif key == curses.KEY_F2 or ( key in [ 10, 32 ] and self.get_elem('BTN_IF_PREV').get_status() ):
			self.get_elem('CARDBOX1').prev_card()
			self.update_widget_states()
			self.draw()
		elif key == curses.KEY_F3 or ( key in [ 10, 32 ] and self.get_elem('BTN_IF_NEXT').get_status() ):
			self.get_elem('CARDBOX1').next_card()
			self.update_widget_states()
			self.draw()
		elif key == curses.KEY_F5 or ( key in [ 10, 32 ] and self.get_elem('BTN_DHCLIENT').get_status() ):
			self.act = dhclient_active(self, _('DHCP Query'), _('Please wait ...'), name='act')
			self.act.draw()
			if not self.dhcpanswer:
				self.draw()
				self.sub = warning(_('No DHCP answer, please check DHCP server and network connectivity.'), self.pos_y+39, self.pos_x+93)
				self.sub.draw()
				r1 = random.randrange(1, 255)
				r2 = random.randrange(0, 255)
				ip_input = self.get_elem('INP_IPv4ADDR')
				ip_input.text = "169.254.%s.%s" % (r1, r2)
				ip_input.set_cursor(len(ip_input.text))
				ip_input.paste_text()
				ip_input.draw()
				netmask_input = self.get_elem('INP_IPv4NETMASK')
				netmask_input.text = "255.255.0.0"
				netmask_input.set_cursor(len(netmask_input.text))
				netmask_input.paste_text()
				netmask_input.draw()
			else:
				addr_elem = self.get_elem('INP_IPv4ADDR')
				if addr_elem.result():
					self.elements[self.current].set_off()		# reset actual focus highlight
					self.current = self.get_elem_id('BTN_DHCLIENT')	# set the tab cursor
					self.elements[self.current].set_on()		# set actual focus highlight
				self.draw()
		elif key in [ 10, 32 ] and self.ask_domainnameserver and self.get_elem('BTN_MORE_NAMESERVER').get_status(): # Enter & Button: "[More]" Nameserver
			self.sub = morewindow(self, self.minY, self.minX+1, self.maxWidth+18, self.maxHeight-18, morewindow.DOMAINDNS)
			self.sub.draw()
		elif key in [ 10, 32 ] and self.ask_forwarder and self.get_elem('BTN_MORE_FORWARDER').get_status(): # Enter & Button: "[More]" Forwarder
			self.sub = morewindow(self, self.minY, self.minX+1, self.maxWidth+18, self.maxHeight-18, morewindow.EXTERNALDNS)
			self.sub.draw()
		else:
			val = self.elements[self.current].key_event(key)
			# update widgets because checkboxes may have changed
			self.update_widget_states()
			return val

	def incomplete(self):
		self.debug('incomplete()')

		invalid = _('Following value is invalid: ')
		invalid_value = _('An invalid value has been entered for interface %(interface)s: %(elemname)s')
		anyDhcp = False

		# nothing configured?
		if not self.ipv4_found and not self.ipv6_found:
			return _('At least one interface must be configured.')

		# count static ipv6 addresses
		cnt_static_ipv6_addresses = 0

		# check every interface if config is complete
		for name, card in self.cards.items():
			if card.get_elem('CB_IPv4').result():
				dhcp = bool(card.get_elem('CB_IPv4DHCP').result())
				addr = card.get_elem('INP_IPv4ADDR').result().strip()
				netmask = card.get_elem('INP_IPv4NETMASK').result().strip()
				self.debug('%s: DHCP:%s  %s/%s' % (name, dhcp, addr, netmask))
				if dhcp:
					anyDhcp = True
				# check values agains IPv4 syntax
				if addr and not self.is_ipv4addr(addr):
					return invalid_value % { 'interface': name, 'elemname': _('IPv4 Address') }
				if netmask and not self.is_ipv4netmask('%s/%s' % (addr, netmask)):
					return invalid_value % { 'interface': name, 'elemname': _('IPv4 Netmask') }
				# at least dhcp or valid IPv4 has to be set
				if not(dhcp or (addr and netmask)):
					return _('Neither DHCP is activated nor an IPv4 address with netmask has been entered for interface "%s".') % name

			if card.get_elem('CB_IPv6').result():
				acceptra = bool(card.get_elem('CB_IPv6RA').result())
				addr = card.get_elem('INP_IPv6ADDR').result().strip()
				prefix = card.get_elem('INP_IPv6PREFIX').result().strip()
				self.debug('%s: RA:%s  %s/%s' % (name, acceptra, addr, prefix))
				# check values agains IPv6 syntax
				if addr and not self.is_ipv6addr(addr):
					return invalid_value % { 'interface': name, 'elemname': _('IPv6 Address') }
				if prefix and not self.is_ipv6netmask('%s/%s' % (addr, prefix)):
					return invalid_value % { 'interface': name, 'elemname': _('IPv6 Prefix') }
				if addr and prefix:
					cnt_static_ipv6_addresses += 1
				# at least acceptra or valid IPv6 has to be set
				if not(acceptra or (addr and prefix)):
					return _('Neither SLAAC is activated nor an IPv6 address with prefix has been entered for interface "%s".') % name
				if addr and prefix:
					if ipaddr.IPv6Address(addr) not in ipaddr.IPv6Network('2000::/3') and \
					   ipaddr.IPv6Address(addr) not in ipaddr.IPv6Network('fc00::/7') and \
					   addr not in self.warning_shown_for_ipv6addr:
						self.warning_shown_for_ipv6addr.append(addr)
						return _('The given IPv6 address "%(addr)s" of interface "%(interface)s" is not a global unicast address (2000::/3) and not a unique local unicast address (fc00::/7). This warning is shown only once for each address. The installation can be continued but might fail.') % { 'addr': addr, 'interface': name }

		# if IPv6-only is used, at least one static IPv6 address has to be defined
		if not self.ipv4_found and self.ipv6_found and cnt_static_ipv6_addresses == 0:
			return _('In IPv6-only environments at least one static IPv6 address has to be defined!')

		testlist = []  # list of 3-tuples ( profile name, descriptive name, is_required?, address type ('4', '6', '46') )
		if self.ipv4_found:
			testlist.append( [ 'gateway', _('IPv4 Gateway'), False, '4' ] )
		if self.ipv6_found:
			testlist.append( [ 'gateway6', _('IPv6 Gateway'), False, '6' ] )
		if self.ask_forwarder and not anyDhcp:
			testlist.append( [ 'dns_forwarder_1', _('External DNS Server'), False, '46' ] )
		if self.ask_domainnameserver and not anyDhcp:
			testlist.append( [ 'nameserver_1', _('Domain DNS Server'), True, '46' ] )

		for key, name, required, addrtype in testlist:
			if self.container.get(key) or required:
				if addrtype == '6':
					if not self.is_ipv6addr( self.container.get(key) ):
						self.debug('no valid IPv6 address: %s=%s' % (key, self.container.get(key)))
						return invalid + name
				elif addrtype == '4':
					if not self.is_ipv4addr( self.container.get(key) ):
						self.debug('no valid IPv4 address: %s=%s' % (key, self.container.get(key)))
						return invalid + name
				else:
					if not self.is_ipaddr( self.container.get(key) ):
						self.debug('no valid IPv4/IPv6 address: %s=%s' % (key, self.container.get(key)))
						return invalid + name

		proxy = self.container.get('proxy_http','')
		if not self.is_proxy(proxy):
			return invalid+_('Proxy, example http://10.201.1.1:8080')

		# activate network
		results = self.result()
		self.netact = ActivateNet(self, _('Setting up network'), _('Please wait ...'), name='netact', results=results)
		self.netact.draw()

		return 0

	def addr_netmask2result(self, name, addr, netmask, copyOnError=False):
		"""
		Converts given ipv4 address and netmask to dict with result variables.
		If address or netmask is not IPv4 compliant, these values will still be copied, if copyOnError is True.
		In this case the keys '*_broadcast' and '*_network' will contain an empty string.

		>>> addr_netmask2result('eth0', '192.168.0.58', '255.255.255.0')
		{ 'eth0_ip': '192.168.0.58',
		  'eth0_netmask': '255.255.255.0',
		  'eth0_broadcast': '192.168.0.255',
		  'eth0_network': '192.168.0.0'  }
		"""
		result = {}
		try:
			IPv4_addr = ipaddr.IPv4Network( '%s/%s' % (addr, netmask) )
		except Exception: # dirty hack: catch all exceptions - ipaddr throws sometime other exceptions than ipaddr.AddressValueError and ipaddr.NetmaskValueError
			if copyOnError:
				result['%s_ip' % name] = addr
				result['%s_netmask' % name] = netmask
				result['%s_broadcast' % name] = ''
				result['%s_network' % name] = ''
			else:
				return None
		else:
			result['%s_ip' % name] = str(IPv4_addr.ip)
			result['%s_netmask' % name] = str(IPv4_addr.netmask)
			result['%s_broadcast' % name] = str(IPv4_addr.broadcast)
			result['%s_network' % name] = str(IPv4_addr.network)

		return result

	def result(self):
		"""
		copy result from self.container to result
		"""
		self.debug('result()')
		self.debug('==> container = %r' % self.container)
		result = {}

		# copy common keys to result (default value is '')
		keylist = [ 'gateway', 'gateway6', 'proxy_http',
					'dns_forwarder_1', 'dns_forwarder_2', 'dns_forwarder_3',
					'nameserver_1', 'nameserver_2', 'nameserver_3' ]
		for key in keylist:
			if key == 'proxy_http':
				if not self.container.get(key) in ['http://', 'https://']:
					result[key] = self.container.get(key,'')
				else:
					result[key] = ''
			else:
				result[key] = self.container.get(key,'')

		# copy all eth* values to result
		for key,val in self.container.items():
			if key.startswith('eth'):
				result[key] = self.container.get(key)

		for key,val in result.items():
			self.debug('[%s]="%s"' % (key,val))

		# copy dns_forwarder_* to nameserver_* if domainnameserver widget has been disabled (e.g. on DC master)
		if not self.ask_domainnameserver:
			for src, dest in [ ['dns_forwarder_1', 'nameserver_1'], ['dns_forwarder_2', 'nameserver_2'], ['dns_forwarder_3', 'nameserver_3'] ]:
				result[dest] = result[src]

		return result

	def activateNetwork(self, result):

		self.debug("==> activateNetwork(net)")
	
		# write network profile
		profile = "/tmp/network_profile"
		if os.path.exists(profile):
			os.unlink(profile)
		networkFH = open(profile, "w+")
		for key in result.keys():
			if result[key]:
				networkFH.write("%s='%s'\n" % (key, result[key]))
		networkFH.flush()
		networkFH.close()
	
		# start network startup script
		if os.path.exists("/sbin/univention-installer-network-startup"):
			cmd = ["/sbin/univention-installer-network-startup"]
			process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
			(stdoutdata, stderrdata) = process.communicate()
			self.debug("==> activateNetwork stdout): %s" % stdoutdata)
			self.debug("==> activateNetwork stderr): %s" % stderrdata)
	
		return

	def helptext(self):
		self.debug('helptext()')

		return _('Network \n \n In this module the network configuration is done. \n \n In the upper part, all detected interfaces are show. By pressing F2 or F3 the next/previous interface can be selected. \n \n For each interface an IPv4 address with netmask and/or IPv6 address with prefix can be entered. \n The configuration of interfaces can also be done automatically: \n \n Dynamic (DHCP): \n   Mark this field if you want this interface to retrieve its IPv4 configuration via DHCP (Dynamic Host Configuration Protocol). \n \n Dynamic (Stateless address autoconfiguration (SLAAC)): \n   Mark this field if you want this interface to retrieve its IPv6 configuration via ND (IPv6 neighbour discovery) \n\n IPv4 Gateway: \n Default gateway to be used for IPv4 traffic. \n IPv6 Gateway: \n Default gateway to be used for IPv6 traffic. \n \n Domain DNS server: \n Enter the IP address of the primary name server, if you are adding a system to an existing UCS domain. \n More: \n Enter additional name servers \n \n External DNS server: \n Enter the IP address of a DNS server to forward queries to. \n More: \n Enter additional DNS forwarders \n \n HTTP-Proxy: \n Enter IP address and port number of HTTP-Proxy to be used (example: http://192.168.1.123:5858)')

	def modheader(self):
		return _('Network')

	def profileheader(self):
		return 'Network'


class ActivateNet(act_win):

	def __init__(self, parent, header, text, name, results):
		self.pos_x = parent.minX + 10
		self.pos_y = parent.minY + 2
		act_win.__init__(self,parent,header,text,name)
		self.results = results

	def function(self):
		self.parent.all_results.update(self.results)
		self.parent.activateNetwork(self.results)

class dhclient_active(act_win):
	# dhclient activity indicator window
	def __init__(self,parent,header,text,name):
		# set this further right to avoid backdrop on left_menu, which fails to be redrawn
		self.pos_x = parent.minX+10
		self.pos_y = parent.minY+2
		act_win.__init__(self,parent,header,text,name)

	def function(self):
		# dhclient call and result evaluation
		interface = self.parent.get_elem('CARDBOX1').get_card().name
		dhcp_dict = self.parent.dhclient(interface, 45)
		ip_str = dhcp_dict.get('%s_ip' % interface) or ''
		if not ip_str:
			self.parent.dhcpanswer = False
		else:
			self.parent.dhcpanswer = True

			ip_input = self.parent.get_elem('INP_IPv4ADDR')
			ip_input.text = dhcp_dict.get('%s_ip' % interface) or ''
			ip_input.set_cursor(len(ip_input.text))
			ip_input.paste_text()
			ip_input.draw()

			netmask_input = self.parent.get_elem('INP_IPv4NETMASK')
			netmask_input.text = dhcp_dict.get('%s_netmask' % interface) or ''
			netmask_input.set_cursor(len(netmask_input.text))
			netmask_input.paste_text()
			netmask_input.draw()

			gateway_str = dhcp_dict.get('gateway') or ''
			if gateway_str:
				gateway_input = self.parent.get_elem('INP_GATEWAY4')
				gateway_input.text = gateway_str
				gateway_input.set_cursor(len(gateway_input.text))
				gateway_input.paste_text()
				gateway_input.draw()

			nameserver1_str = dhcp_dict.get('nameserver_1') or ''
			if nameserver1_str:
				if self.parent.elem_exists('INP_NAMESERVER1'):
					nameserver1_input = self.parent.get_elem('INP_NAMESERVER1')
				else:
					nameserver1_input = self.parent.get_elem('INP_FORWARDER1')
				nameserver1_input.text = nameserver1_str
				nameserver1_input.set_cursor(len(nameserver1_input.text))
				nameserver1_input.paste_text()
				nameserver1_input.draw()

			nameserver2_str = dhcp_dict.get('nameserver_2') or ''
			if nameserver2_str:
				if self.parent.elem_exists('INP_NAMESERVER1'):
					self.parent.container['nameserver_2'] = nameserver2_str

			nameserver3_str = dhcp_dict.get('nameserver_3') or ''
			if nameserver3_str:
				if self.parent.elem_exists('INP_NAMESERVER1'):
					self.parent.containers['nameserver_3'] = nameserver3_str

			# update widgets and save values
			self.parent.update_widget_states()


class morewindow(subwin):
	DOMAINDNS = 'nameserver'
	EXTERNALDNS = 'forwarder'

	def __init__(self, parent, pos_y, pos_x, width, height, fieldtype):
		self.type = fieldtype
		if self.type == self.DOMAINDNS:
			self.name = _('Domain DNS Server')
			self.title = _(' More Domain DNS Servers')
			self.containerkey = 'nameserver_%d'
		elif self.type == self.EXTERNALDNS:
			self.name = _('External DNS Server')
			self.title = _(' More External DNS Servers')
			self.containerkey = 'dns_forwarder_%d'
		self.values = []
		subwin.__init__(self, parent, pos_y, pos_x, width, height)

	def get_values(self):
		self.values = []
		for i in xrange(1,3+1):
			self.values.append( self.parent.container.get(self.containerkey % i,'') )

	def layout(self):
		MAXIP = LEN_IPv6_ADDR + 3

		self.get_values()

		# 1. Nameserver/DNS-Fwd
		self.add_elem('TXT1', textline( _('1. %s') % self.name, self.pos_y+2, self.pos_x+2))
		self.add_elem('TXT2', textline( _('2. %s') % self.name, self.pos_y+3, self.pos_x+2))
		self.add_elem('TXT3', textline( _('3. %s') % self.name, self.pos_y+4, self.pos_x+2))
		self.add_elem('VALUE1', textline(self.values[0][:LEN_IPv6_ADDR+1], self.pos_y+2, self.pos_x+30))  # limit length of IP address
		self.add_elem('VALUE2', input(self.values[1], self.pos_y+3, self.pos_x+29, MAXIP))
		self.add_elem('VALUE3', input(self.values[2], self.pos_y+4, self.pos_x+29, MAXIP))

		self.add_elem('BTN_CANCEL', button('ESC-'+_('Cancel'), self.pos_y+7, self.pos_x+8))
		self.add_elem('BTN_OK', button('F12-'+_('Ok'), self.pos_y+7, self.pos_x+(self.width)-8, 13, align="right"))

		self.current = self.get_elem_id('VALUE2')
		self.elements[self.current].set_on()

	def helptext(self):
		return self.parent.helptext()

	def modheader(self):
		return self.title

	def profileheader(self):
		return self.title

	def put_result(self):
		result = {}

		for i in xrange(2,3+1):
			val = self.get_elem('VALUE%d' % i).result().strip()
			self.parent.container[self.containerkey % i] = val
			result[self.containerkey % i] = val

		return result

	def incomplete(self):
		missing = _('The following value is missing: ')
		invalid = _('The following value is invalid: ')

		# check for valid IP address
		for i in xrange(2,3+1):
			val = self.get_elem('VALUE%d' % i).result().strip()
			# IP address has to meet IPv4 or IPv6 syntax AND
			# values like "0.0.0.0", "255.255.255.255" and "::" are not allowed
			if val and not(self.parent.is_ipaddr(val) and val != '0.0.0.0' and val != '255.255.255.255' and val != '::'):
				return '%s%d. %s' % (invalid, i, self.name)
			self.values[i-1] = val

		# check if first and third value is set
		if self.values[2] and not self.values[1]:
			return '%s%d. %s' % (missing, 2, self.name)

		return None

	def input(self,key):
		self.parent.debug('morewindow: input(): %s  sub=%s' % (key,hasattr(self,'sub')))
		if hasattr(self,'sub'):
			self.sub.key_event(key)
			return 1
		elif ( key in [ 10 ] and self.get_elem('BTN_OK').get_status() ) or key == 276: #Ok
			msg = self.incomplete()
			if msg:
				self.parent.debug('morewindow() incomplete: %s' % msg)
				self.sub = warning(msg, self.pos_y+15, self.pos_x+90)
				self.sub.draw()
				return 1
			self.put_result()
			return 0
		elif key in [ 10 ] and self.get_elem('BTN_CANCEL').get_status(): #Cancel
			return 0
		elif key == 10 and self.elements[self.current].usable():
			return self.elements[self.current].key_event(key)
		elif self.elements[self.current].usable():
			self.elements[self.current].key_event(key)
			return 1
		return 1

	def draw(self):
		subwin.draw(self)
		if hasattr(self,"sub"):
			self.sub.draw()
