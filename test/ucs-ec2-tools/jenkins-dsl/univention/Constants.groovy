package univention

class Constants {
	static ROLE_MAPPING = [
		domaincontroller_master : 'master',
		domaincontroller_backup : 'backup',
		domaincontroller_slave : 'slave',
		memberserver : 'member',
	]

    static VERSIONS =  [
        '4.0' : ['patch_level' : '4', 'last_version' : '3.2'],
        '4.1' : ['patch_level' : '1', 'last_version' : '4.0'],
        '3.2' : ['patch_level' : '7', 'last_version' : '3.1'],
    ]
}
