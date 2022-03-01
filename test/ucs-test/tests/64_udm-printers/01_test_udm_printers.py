#!/usr/share/ucs-test/runner pytest-3
## desc: Test UDM shares/printer
## tags: [udm, apptest]
## roles:
##   - domaincontroller_master
##   - domaincontroller_backup
##   - domaincontroller_slave
##   - memberserver
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import os
import random
import re
import shlex
import subprocess
import sys
import time

import ldap.dn
import pytest

import univention.testing.strings as uts
import univention.testing.ucr
import univention.testing.utils as utils

printserver_installed = utils.package_installed('univention-printserver')
samba_common_bin_installed = utils.package_installed('samba-common-bin')

PRINTER_PROTOCOLS = ['usb://', 'ipp://', 'socket://', 'parallel://', 'http://']


def random_fqdn(ucr):  # type: (univention.testing.ucr.UCSTestConfigRegistry) -> str
	return '%s.%s' % (uts.random_name(), ucr.get('domainname'))


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('careful')
def test_create_printer(ucr, udm):
	"""Create shares/printer and verify LDAP object"""
	ucr.load()

	properties = {
		'name': uts.random_name(),
		'location': uts.random_string(),
		'description': uts.random_name(),
		'spoolHost': random_fqdn(ucr),
		'uri': '%s %s' % (random.choice(PRINTER_PROTOCOLS), uts.random_ip(),),
		'model': 'foomatic-rip/Generic-PCL_4_Printer-gutenprint-ijs-simplified.5.2.ppd',
		'producer': 'cn=Generic,cn=cups,cn=univention,%s' % (ucr.get('ldap/base'),),
		'sambaName': uts.random_name(),
		'ACLtype': random.choice(['allow all', 'allow', 'deny']),
		'ACLUsers': 'uid=Administrator,cn=users,%s' % (ucr.get('ldap/base'),),
		'ACLGroups': 'cn=Printer Admins,cn=groups,%s' % (ucr.get('ldap/base'),),
	}

	print('*** Create shares/printer object')
	print_share_dn = udm.create_object(
		'shares/printer',
		position='cn=printers,%s' % (ucr['ldap/base'],),
		**properties)

	utils.verify_ldap_object(
		print_share_dn,
		{
			'cn': [properties['name']],
			'description': [properties['description']],
			'univentionObjectType': ['shares/printer'],
			'univentionPrinterACLGroups': [properties['ACLGroups']],
			'univentionPrinterACLUsers': [properties['ACLUsers']],
			'univentionPrinterACLtype': [properties['ACLtype']],
			'univentionPrinterLocation': [properties['location']],
			'univentionPrinterModel': [properties['model']],
			'univentionPrinterSambaName': [properties['sambaName']],
			'univentionPrinterSpoolHost': [properties['spoolHost']],
			'univentionPrinterURI': [properties['uri'].replace(' ', '')],
		},
		delay=1)

	print('*** Modify shares/printer object')
	properties['sambaName'] = uts.random_name()
	udm.modify_object('shares/printer', dn=print_share_dn, sambaName=properties['sambaName'])
	utils.verify_ldap_object(
		print_share_dn,
		{'univentionPrinterSambaName': [properties['sambaName']]},
		delay=1
	)


@pytest.mark.skipif(not printserver_installed, reason='Missing software: univention-printserver')
@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('careful')
def test_create_printer_and_check_printing_works(ucr, udm):
	"""Create shares/printer and check if print access works"""
	ucr.load()
	admin_dn = ucr.get('tests/domainadmin/account', 'uid=Administrator,cn=users,%s' % (ucr.get('ldap/base'),))
	admin_name = ldap.dn.str2dn(admin_dn)[0][0][1]
	password = ucr.get('tests/domainadmin/pwd', 'univention')

	spoolhost = '.'.join([ucr['hostname'], ucr['domainname']])
	acltype = random.choice(['allow all', 'allow'])

	properties = {
		'name': uts.random_name(),
		'location': uts.random_string(),
		'description': uts.random_name(),
		'spoolHost': spoolhost,
		'uri': '%s %s' % (random.choice(PRINTER_PROTOCOLS), uts.random_ip(),),
		'model': 'hp-ppd/HP/HP_Business_Inkjet_2500C_Series.ppd',
		'producer': 'cn=Generic,cn=cups,cn=univention,%s' % (ucr.get('ldap/base'),),
		'sambaName': uts.random_name(),
		'ACLtype': acltype,
		'ACLUsers': admin_dn,
		'ACLGroups': 'cn=Printer Admins,cn=groups,%s' % (ucr.get('ldap/base'),),
	}

	print('*** Create shares/printer object')
	print_share_dn = udm.create_object(
		'shares/printer',
		position='cn=printers,%s' % (ucr['ldap/base'],),
		**properties)

	utils.verify_ldap_object(
		print_share_dn,
		{
			'cn': [properties['name']],
			'description': [properties['description']],
			'univentionObjectType': ['shares/printer'],
			'univentionPrinterACLGroups': [properties['ACLGroups']],
			'univentionPrinterACLUsers': [properties['ACLUsers']],
			'univentionPrinterACLtype': [properties['ACLtype']],
			'univentionPrinterLocation': [properties['location']],
			'univentionPrinterModel': [properties['model']],
			'univentionPrinterSambaName': [properties['sambaName']],
			'univentionPrinterSpoolHost': [properties['spoolHost']],
			'univentionPrinterURI': [properties['uri'].replace(' ', '')],
		},
		delay=1)

	print('*** Modify shares/printer samba share name')
	properties['sambaName'] = uts.random_name()
	udm.modify_object('shares/printer', dn=print_share_dn, sambaName=properties['sambaName'])
	utils.verify_ldap_object(
		print_share_dn,
		{'univentionPrinterSambaName': [properties['sambaName']]},
		delay=1
	)

	delay = 15
	print('*** Wait %s seconds for listener postrun' % delay)
	time.sleep(delay)
	p = subprocess.Popen(['lpq', '-P', properties['name']], close_fds=True)
	p.wait()
	assert not p.returncode, "CUPS printer {} not created after {} seconds".format(properties['name'], delay)

	p = subprocess.Popen(['su', admin_name, '-c', 'lpr -P %s /etc/hosts' % properties['name']], close_fds=True)
	p.wait()
	assert not p.returncode, "Printing to CUPS printer {} as {} failed".format(properties['name'], admin_name)

	s4_dc_installed = utils.package_installed("univention-samba4")
	s3_file_and_print_server_installed = utils.package_installed("univention-samba")
	smb_server = s3_file_and_print_server_installed or s4_dc_installed
	if smb_server:
		delay = 1
		time.sleep(delay)
		cmd = ['smbclient', '//localhost/%s' % properties['sambaName'], '-U', '%'.join([admin_name, password]), '-c', 'print /etc/hosts']
		print('\nRunning: %s' % ' '.join(cmd))
		p = subprocess.Popen(cmd, close_fds=True)
		p.wait()
		if p.returncode:
			share_definition = '/etc/samba/printers.conf.d/%s' % properties['sambaName']
			with open(share_definition) as f:
				print('### Samba share file %s :' % share_definition)
				print(f.read())
			print('### testpam for that smb.conf section:')
			p = subprocess.Popen(['testparm', '-s', '--section-name', properties['sambaName']], close_fds=True)
			p.wait()
			assert False, 'Samba printer share {} not accessible'.format(properties['sambaName'])

	p = subprocess.Popen(['lprm', '-P', properties['name'], '-'], close_fds=True)
	p.wait()


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('careful')
def test_create_printergroup(ucr, udm):
	"""Create shares/printergroup and verify LDAP object"""
	ucr.load()

	spoolHost = random_fqdn(ucr)

	printer_properties1 = {
		'name': uts.random_name(),
		'spoolHost': spoolHost,
		'uri': '%s %s' % (random.choice(PRINTER_PROTOCOLS), uts.random_ip(),),
		'model': 'foomatic-rip/Generic-PCL_4_Printer-gutenprint-ijs-simplified.5.2.ppd',
		'producer': 'cn=Generic,cn=cups,cn=univention,%s' % (ucr.get('ldap/base'),),
	}

	print('*** Create shares/printer object')
	udm.create_object(
		'shares/printer',
		position='cn=printers,%s' % (ucr['ldap/base'],),
		**printer_properties1)

	printer_properties2 = {
		'name': uts.random_name(),
		'spoolHost': spoolHost,
		'uri': '%s %s' % (random.choice(PRINTER_PROTOCOLS), uts.random_ip(),),
		'model': 'foomatic-rip/Generic-PCL_4_Printer-gutenprint-ijs-simplified.5.2.ppd',
		'producer': 'cn=Generic,cn=cups,cn=univention,%s' % (ucr.get('ldap/base'),),
	}

	print('*** Create shares/printer object')
	udm.create_object(
		'shares/printer',
		position='cn=printers,%s' % (ucr['ldap/base'],),
		**printer_properties2)

	printergroup_properties = {
		'name': uts.random_name(),
		'spoolHost': spoolHost,
		'groupMember': [printer_properties1['name'], printer_properties2['name']],
		'sambaName': uts.random_name(),
	}

	print('*** Create shares/printergroup object')
	printergroup_share_dn = udm.create_object(
		'shares/printergroup',
		position='cn=printers,%s' % (ucr['ldap/base'],),
		**printergroup_properties)

	utils.verify_ldap_object(
		printergroup_share_dn,
		{
			'cn': [printergroup_properties['name']],
			'univentionObjectType': ['shares/printergroup'],
			'univentionPrinterSambaName': [printergroup_properties['sambaName']],
			'univentionPrinterSpoolHost': [printergroup_properties['spoolHost']],
			'univentionPrinterGroupMember': printergroup_properties['groupMember'],
		},
		delay=1)

	print('*** Modify shares/printergroup object')
	printergroup_properties['sambaName'] = uts.random_name()
	udm.modify_object('shares/printergroup', dn=printergroup_share_dn, sambaName=printergroup_properties['sambaName'])
	utils.verify_ldap_object(
		printergroup_share_dn,
		{'univentionPrinterSambaName': [printergroup_properties['sambaName']]},
		delay=1
	)


@pytest.mark.skipif(not printserver_installed, reason='Missing software: univention-printserver')
@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('safe')
def test_check_ppd():
	"""Check PPD files"""
	# bugs: [43417]
	ldap_printer = []
	printer_files = []
	print('searching for printer models')
	for dn, attr in utils.get_ldap_connection().search(filter='(objectClass=univentionPrinterModels)', attr=['printerModel']):
		for printerModel in attr.get('printerModel', ()):
			printerModel = printerModel.decode('UTF-8')
			model, desc = shlex.split(printerModel)
			desc = printerModel.split('"')[3]
			if desc.startswith('deprecated (only available'):
				continue
			if model.endswith('.ppd') or model.endswith('.ppd.gz'):
				model = model.split('/')[-1]
				ldap_printer.append(model)

	for root, dirs, files in os.walk('/usr/share/ppd/'):
		for file_ in files:
			if file_.endswith('.ppd') or file_.endswith('ppd.gz'):
				printer_files.append(file_)

	for line in subprocess.check_output(['/usr/lib/cups/driver/foomatic-db-compressed-ppds', 'list']).decode('UTF-8', 'replace').splitlines():
		file_ = shlex.split(line)[0]
		printer_files.append(file_.split('/')[-1])

	# check if we found something
	assert ldap_printer
	assert printer_files

	# check diff
	missing_files = set(ldap_printer) - set(printer_files)
	missing_printers = set(printer_files) - set(ldap_printer)
	message = ''
	if missing_files:
		# ignore missing cups-pdf ppd (univention-cups-pdf is not installed)
		if missing_files - {'CUPS-PDF.ppd', 'CUPS-PDF_opt.ppd', 'CUPS-PDF_noopt.ppd'}:
			message += 'No PPD file found for LDAP printers:\n' + '\n\t'.join(missing_files)
	if missing_printers:
		message += '\n\n' + 'No LDAP printer found for PPD files:\n' + '\n\t'.join(missing_printers)
	if message:
		print(message, file=sys.stderr)
		sys.exit(1)


def get_testparm_var(smbconf, sectionname, varname):
	if not os.path.exists("/usr/bin/testparm"):
		return False

	cmd = [
		"/usr/bin/testparm", "-s", "-l",
		"--section-name=%s" % sectionname,
		"--parameter-name=%s" % varname,
		smbconf]
	p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
	(out, err) = p1.communicate()
	return out.strip().decode('UTF-8', 'replace')


def _testparm_is_true(smbconf, sectionname, varname):
	testpram_output = get_testparm_var(smbconf, sectionname, varname)
	return testpram_output.lower() in ('yes', 'true', '1', 'on')


def rename_share_and_check(udm, printer, expected_value):
	printer_samba_name = uts.random_name()
	udm.modify_object('shares/printer', dn=printer, sambaName=printer_samba_name)
	utils.verify_ldap_object(printer, {'univentionPrinterSambaName': [printer_samba_name]})
	utils.wait_for_replication()

	filename = '/etc/samba/printers.conf.d/%s' % printer_samba_name
	samba_force_printername = _testparm_is_true(filename, printer_samba_name, 'force printername')
	assert samba_force_printername == expected_value, "samba option \"force printername\" changed after UDM share modification"
	print("Ok, samba option \"force printername\" still set to %s" % (expected_value,))


@pytest.mark.skipif(not printserver_installed, reason='Missing software: univention-printserver')
@pytest.mark.skipif(not samba_common_bin_installed, reason='Missing software: samba-common-bin')
@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('ucr_value', [None, "false"])
def test_force_printername(ucr, udm, ucr_value):
	"""Check state of "force printername" during UDM printer modify"""

	ucr_var = "samba/force_printername"

	ucr.load()
	previous_value = ucr.get(ucr_var)

	if ucr_value is None:
		univention.config_registry.handler_unset([ucr_var])

	else:
		keyval = "%s=%s" % (ucr_var, ucr_value)
		univention.config_registry.handler_set([keyval])

	if ucr_value != previous_value:
		subprocess.call(["systemctl", "restart", "univention-directory-listener"], close_fds=True)

	ucr.load()
	expected_value = ucr.is_true(ucr_var, True)  # This is the behavior of cups-printers.py

	printer_name = uts.random_name()

	printer_properties = {
		'model': 'foomatic-ppds/Apple/Apple-12_640ps-Postscript.ppd.gz',
		'uri': 'parallel /dev/lp0',
		'spoolHost': '%s.%s' % (ucr['hostname'], ucr['domainname']),
		'name': printer_name
	}

	printer = udm.create_object('shares/printer', position='cn=printers,%s' % ucr['ldap/base'], **printer_properties)
	utils.verify_ldap_object(printer, {
		'univentionPrinterModel': [printer_properties['model']],
		'univentionPrinterURI': [printer_properties['uri'].replace(' ', '')],
		'univentionPrinterSpoolHost': [printer_properties['spoolHost']]
	})
	utils.wait_for_replication()

	old_filename = '/etc/samba/printers.conf.d/%s' % printer_name
	samba_force_printername = _testparm_is_true(old_filename, printer_name, 'force printername')
	assert samba_force_printername == expected_value, "samba option \"force printername\" not set to %s" % (expected_value,)
	print("Ok, samba option \"force printername\" set to %s" % (expected_value,))

	# Check behavior during UDM modification
	rename_share_and_check(udm, printer, expected_value)

	# And check again after inverting the UCR setting:
	if not expected_value:
		# This simulates the update case
		keyval = "%s=%s" % (ucr_var, "yes")
		univention.config_registry.handler_set([keyval])
	else:
		keyval = "%s=%s" % (ucr_var, "no")
		univention.config_registry.handler_set([keyval])

	subprocess.call(["systemctl", "restart", "univention-directory-listener"], close_fds=True)

	rename_share_and_check(udm, printer, expected_value)

	# restart listener with original UCR values:
	subprocess.call(["systemctl", "restart", "univention-directory-listener"], close_fds=True)


def get_uirs():
	cmd = ['udm-test', 'settings/printeruri', 'list']
	out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
	uris = re.findall(r'printeruri:\s(\w*):', out.decode('UTF-8', 'replace'))
	return uris


def printer_enabled(printer_name):
	cmd = ['lpstat', '-p']
	out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
	if err:
		print('stdout from lpstat -p: %s' % out)
		print('stderr from lpstat -p: %s' % err)
	return printer_name in out.decode('UTF-8', 'replace')


@pytest.mark.skipif(not printserver_installed, reason='Missing software: univention-printserver')
@pytest.mark.tags('udm', 'apptest')
@pytest.mark.exposure('dangerous')
def test_create_printer_for_every_printer_URI(ucr, udm):
	"""create printer for every printer URI"""
	# bugs: [36267, 38812, 40591]
	account = utils.UCSTestDomainAdminCredentials()
	position = ucr.get('ldap/hostdn').split(',', 1)[1]
	for uri in get_uirs():
		printer_name = uts.random_name()
		udm.create_object(
			modulename='shares/printer',
			name=printer_name,
			position='%s' % position,
			binddn=account.binddn,
			bindpwd=account.bindpw,
			set={
				'spoolHost': '%(hostname)s.%(domainname)s' % ucr,
				'model': 'None',
				'uri': '%s:// /tmp/%s' % (uri, printer_name)
			}
		)
		if not printer_enabled(printer_name):
			print('Wait for 30 seconds and try again')
			time.sleep(30)
			assert printer_enabled(printer_name), 'Printer (%s) is created but not enabled' % printer_name


@pytest.mark.skipif(not printserver_installed, reason='Missing software: univention-printserver')
@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('dangerous')
def test_modify_printer_and_check_cupsd(ucr, udm):
	"""Create and modify shares/printer, check if cupsd still running"""
	ucr.load()
	name = uts.random_name()
	printer_properties = {
		'model': 'foomatic-rip/Alps-MD-5000-md5k.ppd',
		'uri': 'file:/ tmp/%s' % name,
		'spoolHost': '%s.%s' % (ucr['hostname'], ucr['domainname']),
		'name': name,
	}
	printer = udm.create_object('shares/printer', position='cn=printers,%s' % ucr['ldap/base'], **printer_properties)
	utils.verify_ldap_object(printer, {
		'univentionPrinterModel': [printer_properties['model']],
		'univentionPrinterURI': [printer_properties['uri'].replace(' ', '')],
		'univentionPrinterSpoolHost': [printer_properties['spoolHost']]
	})
	udm.modify_object('shares/printer', dn=printer, ACLUsers=['cn=test,cn=users'], ACLtype='allow')
	time.sleep(3)
	# check if cups is still running
	subprocess.check_call(['lpstat', '-a'])
