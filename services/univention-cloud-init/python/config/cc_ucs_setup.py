# vi: ts=4 expandtab
#
# Univention cloud-init config handler
#
# Copyright 2014-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

from cloudinit.settings import PER_INSTANCE

frequency = PER_INSTANCE


def handle(name, cfg, cloud, log, args):

	log.debug('Executing Module %s' % name)

	if "ucs_setup" not in cfg:
		log.debug(("Skipping module named %s, ucs_setup not present in config"), name)
		return

	# read config options and write them to a profile
	p = dict((k, v) for k, v in cfg["ucs_setup"].items() if v is not None)
	hostname = p.get('hostname', 'ucs')
	domainname = p.get('domainname', 'ucs.local')
	windowsdomain = p.get('windowsdomain', 'UCS')
	ldap_base = p.get('ldap_base', 'dc=ucs,dc=local')
	rootpassword = p.get('rootpassword', 'univention')
	role = p.get('role', 'domaincontroller_master')
	defaultlocale = p.get('defaultlocale', 'de_DE.UTF-8:UTF-8')
	components = p.get('components', '')
	packages_install = p.get('packages_install', '')
	packages_remove = p.get('packages_remove', '')
	eth0_address = p.get('eth0_address', 'dhcp')
	eth0_broadcast = p.get('eth0_broadcast', '')
	eth0_netmask = p.get('eth0_netmask', '')
	eth0_network = p.get('eth0_network', '')
	nameserver = p.get('nameserver', '')
	dnsforwarder = p.get('dnsforwarder', '')
	gateway = p.get('gateway', '')
	sslou = p.get('sslou', 'Univention Corporate Server')
	sslorg = p.get('sslorg', 'DE')
	sslemail = p.get('sslemail', 'ssl@%s' % domainname)
	sslstate = p.get('sslstate', 'DE')
	ssllocality = p.get('ssllocality', 'DE')
	timezone = p.get('timezone', 'America/New_York')
	keymap = p.get('keymap', 'en_us')

	template = '''hostname="%s"
domainname="%s"
windows/domain="%s"
ldap/base="%s"
server/role="%s"
root_password="%s"
locale/default="%s"
components="%s"
packages_install="%s"
packages_remove="%s"
locale="de_DE.UTF-8:UTF-8 en_US.UTF-8:UTF-8"
ssl/organizationalunit="%s"
ssl/organization="%s"
ssl/email="%s"
ssl/state="%s"
ssl/locality="%s"
timezone="%s"
locale/keymap="%s"
interfaces/primary="eth0"
''' % (hostname, domainname, windowsdomain, ldap_base, role, rootpassword, defaultlocale, components, packages_install, packages_remove, sslou, sslorg, sslemail, sslstate, ssllocality, timezone, keymap)

	if gateway:
		template += '''gateway="%s"
''' % gateway
	if nameserver:
		template += '''nameserver1="%s"
''' % nameserver
	if dnsforwarder:
		template += '''dns/forwarder1="%s"
''' % dnsforwarder

	if eth0_address != "dhcp":
		template += '''interfaces/eth0/type="static"
interfaces/eth0/address="%s"
interfaces/eth0/broadcast="%s"
interfaces/eth0/netmask="%s"
interfaces/eth0/network="%s"
''' % (eth0_address, eth0_broadcast, eth0_netmask, eth0_network)
	else:
		template += '''interfaces/eth0/type="dhcp"
'''

	with open('/var/cache/univention-system-setup/profile', 'w') as profile:
		profile.write(template)
