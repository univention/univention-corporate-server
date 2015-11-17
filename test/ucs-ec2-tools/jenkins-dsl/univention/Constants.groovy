package univention

class Constants {
	static ROLE_MAPPING = [
		domaincontroller_master : 'master',
		domaincontroller_backup : 'backup',
		domaincontroller_slave : 'slave',
		memberserver : 'member',
	]

	static LAST_VERSION = [
		'4.0' : '3.2',
		'3.2' : '3.1',
		'4.1' : '4.0',
	]

    static LASTEST_PATCHLEVEL = [
        '4.0' : '4',
        '4.1' : '0',
        '3.2' : '7',
    ]
}
