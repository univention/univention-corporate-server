#!/usr/share/ucs-test/runner python3
## desc: Create shares/share and check if share connect works
## tags: [udm]
## roles:
##   - domaincontroller_master
##   - domaincontroller_backup
##   - domaincontroller_slave
##   - memberserver
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import random
import subprocess
import time

import ldap.dn

import univention.testing.strings as uts
import univention.testing.ucr
import univention.testing.udm as udm_test
import univention.testing.utils as utils


def random_fqdn(ucr):  # type: (univention.testing.ucr.UCSTestConfigRegistry) -> str
	return '%s.%s' % (uts.random_name(), ucr.get('domainname'))


boolean_to_unmapped = {'0': 'no', '1': 'yes'}


## This is *very* inconsistent:
# Most boolean syntax properties *must* be set with 0/1 but are returned as no/yes.
# OTOH some are returned as 0/1: sambaNtAclSupport sambaInheritAcls sambaOplocks sambaLevel2Oplocks sambaFakeOplocks
def keyAndValue_to_ldap(property_values):
	if not isinstance(property_values, list):
		property_values = [property_values]
	_keyAndValue_to_ldap = {
		'"acl xattr update mtime" yes': 'acl xattr update mtime = yes',
		'"access based share enum" yes': 'access based share enum = yes',
	}
	return [_keyAndValue_to_ldap[v] for v in property_values]


if __name__ == '__main__':
	with univention.testing.ucr.UCSTestConfigRegistry() as ucr, udm_test.UCSTestUDM() as udm:
		ucr.load()
		admin_dn = ucr.get('tests/domainadmin/account', 'uid=Administrator,cn=users,%s' % (ucr.get('ldap/base'),))
		admin_name = ldap.dn.str2dn(admin_dn)[0][0][1]
		password = ucr.get('tests/domainadmin/pwd', 'univention')
		sambaOplocks = random.choice(['0', '1'])

		properties = {
			'name': uts.random_name(),
			'host': '.'.join([ucr['hostname'], ucr['domainname']]),
			'path': '/test/%s' % uts.random_string(),
			'owner': uts.random_int(),
			'group': uts.random_int(),
			'directorymode': '00750',
			'writeable': random.choice(['0', '1']),
			'sync': random.choice(['sync', 'async']),
			'subtree_checking': random.choice(['0', '1']),
			'root_squash': random.choice(['0', '1']),
			'nfs_hosts': uts.random_name(),
			'sambaWriteable': random.choice(['0', '1']),
			'sambaName': uts.random_string(),
			'sambaBrowseable': random.choice(['0', '1']),
			'sambaPublic': random.choice(['0', '1']),
			'sambaDosFilemode': random.choice(['0', '1']),
			'sambaHideUnreadable': random.choice(['0', '1']),
			'sambaCreateMode': '00740',
			'sambaDirectoryMode': '00750',
			'sambaForceCreateMode': '0',
			'sambaForceDirectoryMode': '0',
			'sambaSecurityMode': '00770',
			'sambaDirectorySecurityMode': '00770',
			'sambaForceSecurityMode': '0',
			'sambaForceDirectorySecurityMode': '0',
			'sambaLocking': random.choice(['0', '1']),
			'sambaBlockingLocks': random.choice(['0', '1']),
			'sambaStrictLocking': random.choice(['Auto', '1', '0']),
			'sambaOplocks': sambaOplocks,
			'sambaLevel2Oplocks': random.choice(['0', '1']) if sambaOplocks else sambaOplocks,
			'sambaFakeOplocks': random.choice(['0', '1']),
			'sambaBlockSize': uts.random_int(bottom_end=512, top_end=4096),
			'sambaCscPolicy': random.choice(['manual', 'documents', 'programs', 'disable']),
			# 'sambaHostsAllow': random_fqdn(ucr),
			# 'sambaHostsDeny': random_fqdn(ucr),
			'sambaValidUsers': '%s, @"%s %s"' % (admin_name, uts.random_name(), uts.random_name()),
			'sambaInvalidUsers': '%s, @"%s %s"' % (uts.random_name(), uts.random_name(), uts.random_name()),
			# 'sambaForceUser': uts.random_name(),
			# 'sambaForceGroup': uts.random_name(),
			'sambaHideFiles': uts.random_name(),
			'sambaNtAclSupport': random.choice(['0', '1']),
			'sambaInheritAcls': random.choice(['0', '1']),
			'sambaPostexec': '/bin/true',
			'sambaPreexec': '/bin/true',
			'sambaWriteList': '%s' % (uts.random_name(),),
			# 'sambaVFSObjects': '%s, %s' % (uts.random_name(), uts.random_name()),
			'sambaMSDFSRoot': random.choice(['0', '1']),
			'sambaInheritOwner': random.choice(['0', '1']),
			'sambaInheritPermissions': random.choice(['0', '1']),
			# 'sambaCustomSettings': ['"acl xattr update mtime" yes', '"access based share enum" yes'],
			'sambaCustomSettings': '"acl xattr update mtime" yes',
			'nfsCustomSettings': 'nohide',
		}

		print('*** Create shares/share object')
		file_share_dn = udm.create_object(
			'shares/share',
			position='cn=shares,%s' % (ucr['ldap/base'],),
			**properties)

		utils.verify_ldap_object(
			file_share_dn,
			{
				'cn': [properties['name']],
				'univentionShareHost': [properties['host']],
				'univentionSharePath': [properties['path']],
				'univentionObjectType': ['shares/share'],
				'univentionShareUid': [properties['owner']],
				'univentionShareGid': [properties['group']],
				'univentionShareDirectoryMode': [properties['directorymode']],
				'univentionShareWriteable': [boolean_to_unmapped[properties['writeable']]],
				'univentionShareNFSSync': [properties['sync']],
				'univentionShareNFSAllowed': [properties['nfs_hosts']],
				'univentionShareNFSRootSquash': [boolean_to_unmapped[properties['root_squash']]],
				'univentionShareNFSSubTree': [boolean_to_unmapped[properties['subtree_checking']]],
				'univentionShareSambaName': [properties['sambaName']],
				'univentionShareSambaBrowseable': [boolean_to_unmapped[properties['sambaBrowseable']]],
				'univentionShareSambaPublic': [boolean_to_unmapped[properties['sambaPublic']]],
				'univentionShareSambaDosFilemode': [boolean_to_unmapped[properties['sambaDosFilemode']]],
				'univentionShareSambaHideUnreadable': [boolean_to_unmapped[properties['sambaHideUnreadable']]],
				'univentionShareSambaCreateMode': [properties['sambaCreateMode']],
				'univentionShareSambaDirectoryMode': [properties['sambaDirectoryMode']],
				'univentionShareSambaForceCreateMode': [properties['sambaForceCreateMode']],
				'univentionShareSambaForceDirectoryMode': [properties['sambaForceDirectoryMode']],
				'univentionShareSambaSecurityMode': [properties['sambaSecurityMode']],
				'univentionShareSambaDirectorySecurityMode': [properties['sambaDirectorySecurityMode']],
				'univentionShareSambaForceSecurityMode': [properties['sambaForceSecurityMode']],
				'univentionShareSambaLocking': [properties['sambaLocking']],
				'univentionShareSambaBlockingLocks': [properties['sambaBlockingLocks']],
				'univentionShareSambaStrictLocking': [properties['sambaStrictLocking']],
				'univentionShareSambaOplocks': [properties['sambaOplocks']],
				'univentionShareSambaLevel2Oplocks': [properties['sambaLevel2Oplocks']],
				'univentionShareSambaFakeOplocks': [properties['sambaFakeOplocks']],
				'univentionShareSambaBlockSize': [properties['sambaBlockSize']],
				'univentionShareSambaCscPolicy': [properties['sambaCscPolicy']],
				'univentionShareSambaValidUsers': [properties['sambaValidUsers']],
				'univentionShareSambaInvalidUsers': [properties['sambaInvalidUsers']],
				# 'univentionShareSambaHostsAllow': [properties['sambaHostsAllow']],
				# 'univentionShareSambaHostsDeny': [properties['sambaHostsDeny']],
				# 'univentionShareSambaForceUser': [properties['sambaForceUser']],
				# 'univentionShareSambaForceGroup': [properties['sambaForceGroup']],
				'univentionShareSambaHideFiles': [properties['sambaHideFiles']],
				'univentionShareSambaNtAclSupport': [properties['sambaNtAclSupport']],
				'univentionShareSambaInheritAcls': [properties['sambaInheritAcls']],
				'univentionShareSambaPostexec': [properties['sambaPostexec']],
				'univentionShareSambaPreexec': [properties['sambaPreexec']],
				'univentionShareSambaWriteable': [boolean_to_unmapped[properties['sambaWriteable']]],
				'univentionShareSambaWriteList': [properties['sambaWriteList']],
				# 'univentionShareSambaVFSObjects': [properties['sambaVFSObjects']],
				'univentionShareSambaMSDFS': [boolean_to_unmapped[properties['sambaMSDFSRoot']]],
				'univentionShareSambaInheritOwner': [boolean_to_unmapped[properties['sambaInheritOwner']]],
				'univentionShareSambaInheritPermissions': [boolean_to_unmapped[properties['sambaInheritPermissions']]],
				'univentionShareSambaCustomSetting': keyAndValue_to_ldap(properties['sambaCustomSettings']),
				'univentionShareNFSCustomSetting': [properties['nfsCustomSettings']],
			},
			delay=1)

		delay = 15
		print('*** Wait %s seconds for listener postrun' % delay)
		time.sleep(delay)

		s4_dc_installed = utils.package_installed("univention-samba4")
		s3_file_and_print_server_installed = utils.package_installed("univention-samba")
		smb_server = s3_file_and_print_server_installed or s4_dc_installed
		if smb_server:
			delay = 1
			time.sleep(delay)
			cmd = ['smbclient', '//localhost/%s' % properties['sambaName'], '-U', '%'.join([admin_name, password]), '-c', 'showconnect']
			print('\nRunning: %s' % ' '.join(cmd))
			p = subprocess.Popen(cmd, close_fds=True)
			p.wait()
			if p.returncode:
				share_definition = '/etc/samba/shares.conf.d/%s' % properties['sambaName']
				with open(share_definition) as f:
					print('### Samba share file %s :' % share_definition)
					print(f.read())
				print('### testpam for that smb.conf section:')
				p = subprocess.Popen(['testparm', '-s', '--section-name', properties['sambaName']], close_fds=True)
				p.wait()
				utils.fail('Samba fileshare {} not accessible'.format(properties['sambaName']))
