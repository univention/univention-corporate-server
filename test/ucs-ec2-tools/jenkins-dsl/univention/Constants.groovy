package univention

class Constants {
	static ROLE_MAPPING = [
		domaincontroller_master : 'master',
		domaincontroller_backup : 'backup',
		domaincontroller_slave : 'slave',
		memberserver : 'member',
	]
}
