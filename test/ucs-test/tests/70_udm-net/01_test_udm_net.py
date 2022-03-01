#!/usr/share/ucs-test/runner pytest-3 -s
## tags: [udm-net,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import univention.testing.strings as uts
import univention.uldap as uldap
from univention.testing import utils


class Test_UDMNetwork(object):

	def test_create_network(self, udm):
		"""Test the base functionality to create and remove a network"""
		networkName = uts.random_name()
		network = udm.create_object('networks/network', name=networkName, network='10.20.30.0', netmask='24')

		ldap = uldap.getAdminConnection()
		ldapFilter = '(&(cn=%s)(objectClass=univentionNetworkClass))' % networkName
		assert network in ldap.searchDn(filter=ldapFilter)

		udm.remove_object('networks/network', dn=network)
		assert network not in ldap.searchDn(filter=ldapFilter)

	def test_remove_iprange_from_network(self, udm):
		"""Remove ip range from network"""
		# bugs: [35074]
		networkName = uts.random_name()
		ipRange = "10.20.30.30 10.20.30.31"
		network = udm.create_object('networks/network', name=networkName, network='10.20.30.0', netmask='24', ipRange=ipRange)
		utils.verify_ldap_object(network, {'univentionIpRange': [ipRange]})
		network = udm.modify_object('networks/network', dn=network, remove={'ipRange': [ipRange]})
		utils.verify_ldap_object(network, {'univentionIpRange': []})
