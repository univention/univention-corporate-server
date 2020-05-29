#!/usr/bin/py.test

from copy import deepcopy

import pytest
from univention.unittests.udm import import_udm_module, MockedAccess, MockedPosition

from univention.admin.nagios import addPropertiesMappingOptionsAndLayout
from univention.admin.uexceptions import nagiosDNSForwardZoneEntryRequired, nagiosARecordRequired

nagios = import_udm_module('nagios')


@pytest.fixture
def ldap_database_file():
	return 'unittests/nagios.ldif'


@pytest.fixture
def nagios_member_no_option(ldap_database):
	dn = 'cn=member222,cn=computers,dc=intranet,dc=example,dc=de'
	ldap_obj = ldap_database.objs[dn]
	return nagios_support_obj(ldap_database, ldap_obj)


@pytest.fixture
def nagios_member(ldap_database):
	dn = 'cn=member221,cn=computers,dc=intranet,dc=example,dc=de'
	ldap_obj = ldap_database.objs[dn]
	return nagios_support_obj(ldap_database, ldap_obj)


@pytest.fixture
def nagios_master(ldap_database):
	dn = 'cn=master220,cn=dc,cn=computers,dc=intranet,dc=example,dc=de'
	ldap_obj = ldap_database.objs[dn]
	return nagios_support_obj(ldap_database, ldap_obj)


@pytest.fixture
def nagios_service_dns(ldap_database):
	dn = 'cn=UNIVENTION_DNS,cn=nagios,dc=intranet,dc=example,dc=de'
	return ldap_database.objs[dn]


@pytest.fixture
def nagios_service_ntp(ldap_database):
	dn = 'cn=UNIVENTION_NTP,cn=nagios,dc=intranet,dc=example,dc=de'
	return ldap_database.objs[dn]


Support = nagios.Support


if not hasattr(Support, 'option_toggled'):
	class Support(Support):
		def option_toggled(self, x):
			return x in self.options and x not in self.old_options or x not in self.options and x in self.old_options


if not hasattr(Support, 'hasChanged'):
	class Support(Support):
		def hasChanged(self, x):
			return self.info.get(x) != self.oldinfo.get(x)


if not hasattr(Support, '__setitem__'):
	class Support(Support):
		def __setitem__(self, x, y):
			self.info[x] = y


if not hasattr(Support, '__getitem__'):
	class Support(Support):
		def __getitem__(self, x):
			return self.info.get(x)


if not hasattr(Support, 'has_property'):
	class Support(Support):
		def has_property(self, x):
			return x in self.info


def nagios_support_obj(database, obj):
	support = Support()
	support.dn = obj.dn
	support.oldattr = obj.attrs
	support.lo = MockedAccess(database)
	support.alloc = []
	support.position = MockedPosition()
	support.options = []
	support.info = {}
	support.info['name'] = support.oldattr['cn'][0].decode('utf-8')
	if support.oldattr.get('aRecord'):
		support.info['ip'] = [record.decode('utf-8') for record in support.oldattr['aRecord']]
	if support.oldattr.get('associatedDomain'):
		support.info['domain'] = [domain.decode('utf-8') for domain in support.oldattr['associatedDomain']][0]

	if 'nagios' not in support.options:
		if support.oldattr.get('univentionNagiosEnabled', [b''])[0] == b'1':
			support.options.append('nagios')
	support.old_options = support.options[:]
	nagiosParents = []
	for parent in support.oldattr.get('univentionNagiosParent', []):
		cn = parent.decode('utf-8').split('.')[0]
		host_dns = support.lo.searchDn('(&(objectClass=univentionHost)(cn={}))'.format(cn))
		if host_dns:
			nagiosParents.append(host_dns[0])
	support.info['nagiosParents'] = nagiosParents
	support.nagios_open()
	support.oldinfo = deepcopy(support.info)

	return support


# implementing the interace that Support assumes it has
if not hasattr(Support, 'option_toggled'):
	class Support(Support):
		def option_toggled(self, x):
			return x in self.options and x not in self.old_options or x not in self.options and x in self.old_options


if not hasattr(Support, 'hasChanged'):
	class Support(Support):
		def hasChanged(self, x):
			return self.info.get(x) != self.oldinfo.get(x)


if not hasattr(Support, '__setitem__'):
	class Support(Support):
		def __setitem__(self, x, y):
			self.info[x] = y


if not hasattr(Support, '__getitem__'):
	class Support(Support):
		def __getitem__(self, x):
			return self.info.get(x)


if not hasattr(Support, 'has_property'):
	class Support(Support):
		def has_property(self, x):
			return x in self.info


def support_from(database, dn):
	obj = database.objs[dn]
	support = Support()
	support.oldattr = obj.attrs
	support.lo = MockedAccess(database)
	support.alloc = []
	support.position = MockedPosition()
	support.options = []
	support.info = {}
	support.info['name'] = support.oldattr['cn'][0].decode('utf-8')
	if support.oldattr.get('aRecord'):
		support.info['ip'] = [record.decode('utf-8') for record in support.oldattr['aRecord']]
	if support.oldattr.get('associatedDomain'):
		support.info['domain'] = [domain.decode('utf-8') for domain in support.oldattr['associatedDomain']][0]

	if 'nagios' not in support.options:
		if support.oldattr.get('univentionNagiosEnabled', [b''])[0] == b'1':
			support.options.append('nagios')
	support.old_options = support.options[:]
	nagiosParents = []
	for parent in support.oldattr.get('univentionNagiosParent', []):
		cn = parent.decode('utf-8').split('.')[0]
		host_dns = support.lo.searchDn('(&(objectClass=univentionHost)(cn={}))'.format(cn))
		if host_dns:
			nagiosParents.append(host_dns[0])
	support.info['nagiosParents'] = nagiosParents
	support.nagios_open()
	support.oldinfo = deepcopy(support.info)

	return support


class TestSupport(object):
	def test_nagios_get_assigned_services(self, nagios_master, nagios_service_dns, nagios_service_ntp):
		dns_from_method = nagios_master.nagiosGetAssignedServices()
		dns_from_ldif = [nagios_service_dns.dn, nagios_service_ntp.dn]
		assert dns_from_method == dns_from_ldif

	def test_nagios_remove_host_from_parent(self, nagios_master, nagios_member):
		parent_fqdn = '{}.{}'.format(nagios_master['name'], nagios_master['domain']).encode('utf-8')
		assert parent_fqdn in nagios_member.lo.getAttr(nagios_member.dn, 'univentionNagiosParent')
		nagios_master.nagiosRemoveHostFromParent()
		assert parent_fqdn not in nagios_member.lo.getAttr(nagios_member.dn, 'univentionNagiosParent')

	def test_nagios_remove_host_from_service(self, nagios_master, nagios_service_dns, nagios_service_ntp):
		assert nagios_service_dns.attrs.get('univentionNagiosHostname') is not None
		assert nagios_service_ntp.attrs.get('univentionNagiosHostname') is not None
		nagios_master.nagiosRemoveHostFromServices()
		assert nagios_service_dns.attrs.get('univentionNagiosHostname') is None
		assert nagios_service_ntp.attrs.get('univentionNagiosHostname') is None

	def test_nagios_get_parent_hosts(self, nagios_master, nagios_member):
		assert nagios_member.nagiosGetParentHosts() == [nagios_master.dn]

	def test_nagios_save_parent_host_list_changed(self, nagios_member):
		nagios_member.hasChanged = lambda x: x == 'nagiosParents'
		ml = []
		nagios_member.nagiosSaveParentHostList(ml)
		assert ml == [('univentionNagiosParent', [b'master220.intranet.example.de', b'fantasy.intranet.example.de'], [b'master220.intranet.example.de'])]

	def test_nagios_save_parent_host_list_not_changed(self, nagios_member):
		nagios_member.hasChanged = lambda x: x != 'nagiosParents'
		ml = []
		nagios_member.nagiosSaveParentHostList(ml)
		assert ml == []

	def test_nagios_open_no_nagios(self, mocker, nagios_member_no_option):
		services = mocker.patch.object(nagios_member_no_option, 'nagiosGetAssignedServices')
		parents = mocker.patch.object(nagios_member_no_option, 'nagiosGetParentHosts')
		nagios_member_no_option.nagios_open()
		assert nagios_member_no_option['nagiosServices'] is not services()
		assert nagios_member_no_option['nagiosParents'] is not parents()

	def test_nagios_open_with_nagios(self, mocker, nagios_member):
		services = mocker.patch.object(nagios_member, 'nagiosGetAssignedServices')
		parents = mocker.patch.object(nagios_member, 'nagiosGetParentHosts')
		nagios_member.nagios_open()
		assert nagios_member['nagiosServices'] is services()
		assert nagios_member['nagiosParents'] is parents()

	def test_nagio_ldap_modlist_no_change(self, nagios_master):
		ml = []
		nagios_master.nagios_ldap_modlist(ml)
		assert ml == []

	def test_nagio_ldap_modlist_no_ip(self, nagios_master):
		nagios_master.info['ip'] = []
		with pytest.raises(nagiosARecordRequired):
			nagios_master.nagios_ldap_modlist([])

	def test_nagio_ldap_modlist_no_domain(self, nagios_master):
		nagios_master.info['domain'] = ''
		nagios_master.info['dnsEntryZoneForward'] = []
		with pytest.raises(nagiosDNSForwardZoneEntryRequired):
			nagios_master.nagios_ldap_modlist([])

	def test_nagio_ldap_modlist_remove_option(self, nagios_master):
		nagios_master.options.remove('nagios')
		ml = []
		nagios_master.nagios_ldap_modlist(ml)
		assert ml == [('univentionNagiosEnabled', [b'1'], b'')]

	def test_nagio_ldap_modlist_add_option(self, nagios_member_no_option):
		nagios_member_no_option.options.append('nagios')
		ml = []
		nagios_member_no_option.nagios_ldap_modlist(ml)
		assert ml == [('univentionNagiosEnabled', b'', b'1')]

	def test_ldap_post_modify_with_remove_from_services(self, mocker, nagios_member):
		nagios_member.nagiosRemoveFromServices = False
		mocker.patch.object(nagios_member, 'nagiosModifyServiceList')
		nagios_member.nagios_ldap_post_modify()
		assert nagios_member.nagiosModifyServiceList.call_count == 1

	def test_ldap_post_modify_no_remove_from_services(self, mocker, nagios_member):
		nagios_member.nagiosRemoveFromServices = True
		mocker.patch.object(nagios_member, 'nagiosRemoveHostFromServices')
		mocker.patch.object(nagios_member, 'nagiosRemoveHostFromParent')
		nagios_member.nagios_ldap_post_modify()
		assert nagios_member.nagiosRemoveHostFromServices.call_count == 1
		assert nagios_member.nagiosRemoveHostFromParent.call_count == 1

	def test_ldap_post_create_no_nagios(self, mocker, nagios_member_no_option):
		mocker.patch.object(nagios_member_no_option, 'nagiosModifyServiceList')
		nagios_member_no_option.nagios_ldap_post_create()
		nagios_member_no_option.nagiosModifyServiceList.assert_not_called()

	def test_ldap_post_create_with_nagios(self, mocker, nagios_member):
		mocker.patch.object(nagios_member, 'nagiosModifyServiceList')
		nagios_member.nagios_ldap_post_create()
		assert nagios_member.nagiosModifyServiceList.call_count == 1

	def test_nagios_post_remove(self, mocker, nagios_member):
		mocker.patch.object(nagios_member, 'nagiosRemoveHostFromServices')
		mocker.patch.object(nagios_member, 'nagiosRemoveHostFromParent')
		nagios_member.nagios_ldap_post_remove()
		assert nagios_member.nagiosRemoveHostFromServices.call_count == 1
		assert nagios_member.nagiosRemoveHostFromParent.call_count == 1

	def test_nagios_modify_service_list_change_name(self, nagios_master, nagios_service_dns, nagios_service_ntp):
		nagios_master['name'] = 'newmaster220'
		assert nagios_service_dns.attrs['univentionNagiosHostname'] == [b'master220.intranet.example.de']
		assert nagios_service_ntp.attrs['univentionNagiosHostname'] == [b'master220.intranet.example.de']
		nagios_master.nagiosModifyServiceList()
		assert nagios_service_dns.attrs['univentionNagiosHostname'] == [b'newmaster220.intranet.example.de']
		assert nagios_service_ntp.attrs['univentionNagiosHostname'] == [b'newmaster220.intranet.example.de']

	def test_nagios_modify_service_list_change_domain(self, nagios_master, nagios_service_dns, nagios_service_ntp):
		nagios_master['domain'] = 'newexample.com'
		assert nagios_service_dns.attrs['univentionNagiosHostname'] == [b'master220.intranet.example.de']
		assert nagios_service_ntp.attrs['univentionNagiosHostname'] == [b'master220.intranet.example.de']
		nagios_master.nagiosModifyServiceList()
		assert nagios_service_dns.attrs['univentionNagiosHostname'] == [b'master220.newexample.com']
		assert nagios_service_ntp.attrs['univentionNagiosHostname'] == [b'master220.newexample.com']

	def test_nagios_modify_service_list_change_name_and_domain(self, nagios_master, nagios_service_dns, nagios_service_ntp):
		nagios_master['name'] = 'newmaster220'
		nagios_master['domain'] = 'newexample.com'
		assert nagios_service_dns.attrs['univentionNagiosHostname'] == [b'master220.intranet.example.de']
		assert nagios_service_ntp.attrs['univentionNagiosHostname'] == [b'master220.intranet.example.de']
		nagios_master.nagiosModifyServiceList()
		assert nagios_service_dns.attrs['univentionNagiosHostname'] == [b'newmaster220.newexample.com']
		assert nagios_service_ntp.attrs['univentionNagiosHostname'] == [b'newmaster220.newexample.com']

	def test_nagios_modify_service_list_add_service(self, nagios_member, nagios_service_dns, nagios_service_ntp):
		nagios_member['nagiosServices'] = [nagios_service_dns.dn, nagios_service_ntp.dn, '']
		assert b'member221.intranet.example.de' not in nagios_service_dns.attrs['univentionNagiosHostname']
		assert b'member221.intranet.example.de' not in nagios_service_ntp.attrs['univentionNagiosHostname']
		nagios_member.nagiosModifyServiceList()
		assert b'member221.intranet.example.de' in nagios_service_dns.attrs['univentionNagiosHostname']
		assert b'member221.intranet.example.de' in nagios_service_ntp.attrs['univentionNagiosHostname']

	def test_nagios_modify_service_list_remove_service(self, nagios_master, nagios_service_dns, nagios_service_ntp):
		nagios_master['nagiosServices'] = [nagios_service_dns.dn]
		assert nagios_service_dns.attrs['univentionNagiosHostname'] == [b'master220.intranet.example.de']
		assert nagios_service_ntp.attrs['univentionNagiosHostname'] == [b'master220.intranet.example.de']
		nagios_master.nagiosModifyServiceList()
		assert nagios_service_dns.attrs['univentionNagiosHostname'] == [b'master220.intranet.example.de']
		assert nagios_service_ntp.attrs.get('univentionNagiosHostname') is None

	def test_nagios_cleanup(self, mocker, nagios_member):
		mocker.patch.object(nagios_member, 'nagiosRemoveHostFromServices')
		mocker.patch.object(nagios_member, 'nagiosRemoveHostFromParent')
		nagios_member.nagios_cleanup()
		assert nagios_member.nagiosRemoveHostFromServices.call_count == 1
		assert nagios_member.nagiosRemoveHostFromParent.call_count == 1


def test_add_properties(mocker):
	properties = {}
	mapping = mocker.Mock()
	options = {}
	layout = []
	addPropertiesMappingOptionsAndLayout(properties, mapping, options, layout)
	assert sorted(properties) == ['nagiosContactEmail', 'nagiosParents', 'nagiosServices']
	mapping.register.assert_called_once_with('nagiosContactEmail', 'univentionNagiosEmail', None, None)
	assert sorted(options) == ['nagios']
	assert len(layout) == 2
