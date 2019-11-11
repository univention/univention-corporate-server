# vim:set noexpandtab fileencoding=utf-8:
import re


class LogMessage(object):

	def __init__(self, wanted=None, ignore=None):
		self.wanted = self.recomp(self.wanted_list + (wanted or [])).match
		self.ignore = self.recomp(self.ignore_list + (ignore or [])).match
		self.ignore_extra = self.recomp(self.extra_ignore_list).match  # Bug #36160

	@staticmethod
	def recomp(patterns, ignore_case=True):
		pattern = '|'.join('(?:%s)' % _ for _ in patterns)
		return re.compile(pattern, re.IGNORECASE if ignore_case else 0)


class Errors(LogMessage):
	wanted_list = [
		".*error.*",
		".*failed.*",
		".*usage.*",
		"^E:",
	]

	# possible (ignored) errors:
	ignore_list = [
		'.*failedmirror=.*',
		'All done, no errors.',
		'I: .* libgpg-error0',
		'Installation finished. No error.* reported',
		'Not updating .*',
		'Error: There are no (?:services|hosts|host groups|contacts|contact groups) defined!',
		'Total Errors:\s+\d+',
		'Cannot find nagios object .*',
		'invoke-rc.d: initscript udev, action "reload" failed.',  # Bug 19227
		'yes: write error',
		'.*Update aborted by pre-update script of release.*',
		'.*update failed. Please check /var/log/univention/.*',
		'.*failed to convert the username .* to the uid.*',
		'.*Can not write log, .* failed.*',
		'.*Starting Univention Directory Policy:.*',
		'.*LISTENER .* : failed to connect to any notifier.*',
		'.*liberror-perl.*',
		'.*CONSISTENCY CHECK FAILED: cyls is too large .* setting to possible max .*',
		'.*error adding .*.pem',
		'.*failed .*VM used: java-6-cacao.*',
		'.*/etc/ca-certificates/update.d/.* exited with code 1',
		'.*well-known-sid-name-mapping.d/univention-ldap-server.py: postrun: Initiating graceful reload of ldap server.*',
		'.*connection to notifier was closed.*',
		'.*failed to recv result.*',
		'.*listener: 1',
		'.*error searching DN.*',  # Bug 37225
		".*Can't contact LDAP server.*",  # Bug 37225
		'.*nagios3 reported an error in configfile .* Please restart nagios3 manually.*',
		'.*failed to download keytab for memberserver, retry.*',  # Bug 37225
		'.*your request could not be fulfilled.*',  # Bug 37226
		'.*Starting ldap server.* slapd ...failed.*',  # Bug 37226
		'.*rsync: change_dir "/var/lib/samba/account-policy" failed: No such file or directory.*',  # Bug 37226
		'.*rsync error: some files/attrs were not transferred.*',  # Bug 37226
		'.*rsync: opendir "/etc/univention/ssl/unassigned-hostname.unassigned-domain" failed: Permission denied.*',  # Bug 37226
		'.*Failed to join domain: failed to find DC for domain.*',  # Bug 37226
		r".*statoverride: error: an override for '/var/log/dpkg\.log' already exists",  # Bug 37502
		r".*statoverride: error: an override for '/var/log/bootstrap\.log' already exists",  # Bug 37502
		r".*statoverride: error: an override for '/var/log/lastlog' already exists",  # Bug 37502
		r".*statoverride: error: an override for '/var/log/faillog' already exists",  # Bug 37502
		r".*ln: failed to create symbolic link `java': File exists",  # Bug 37503
		r"Action 'start' failed.",
		r'The Apache error log may have more information.',
		r'failed!',
		r'invoke-rc.d: initscript apache2, action "start" failed',
		r'invoke-rc.d: initscript apache2, action "restart" failed',
		r"E: Unable to locate package could-initramfs-growroot",
		r"'www-browser -dump http://localhost:80/server-status' failed.",  # Bug #38797
		r'.*MODULE *\( *ERROR *\) *: *$',     # Bug 45406
		'Further information regarding this error:',  # Bug 45406
		'Error: Unable to correct problems, you have held broken packages.',  # Bug 45406
		'.*MODULE      \( ERROR   \) : univention-samba: Failed to install',  # Bug 45406
		'.*MODULE      \( PROCESS \) : Installation of univention-samba failed. Try to re-create sources.list and try again.',  # Bug 45406
		'.*Failed to download required packages for univention-welcome-screen.*',  # Bug #37537: remove after release of univention-welcome-screen
		'.*E: Unable to locate package univention-welcome-screen.*', '.*E: Handler silently failed.*',  # Bug #37537 ^^
		'.*ERROR\(runtime\): uncaught exception - \(-1073741823.*', '.*open: error=2 \(No such file or directory\).*',  # Bug #39123
		'DNS Update for .* failed: ERROR_DNS_UPDATE_FAILED',  # Bug #39622
		'DNS update failed: NT_STATUS_UNSUCCESSFUL',  # Bug #39622
		'rndc: connect failed: 127.0.0.1#953: connection refused',  # Bug #39691
		'.*Ignoring import error: No module named ucs_version',  # Bug #39692
		'\[!\] error queue: 140DC002: error:140DC002:SSL routines:SSL_CTX_use_certificate_chain_file:system lib',  # Bug #39646
		'\[!\] error queue: 20074002: error:20074002:BIO routines:FILE_CTRL:system lib',  # Bug #39646
		'\[!\] SSL_CTX_use_certificate_chain_file: 2001002: error:02001002:system library:fopen:No such file or directory',  # Bug #39646
		'\[!\] Service \[memcached\]: Failed to initialize SSL context',  # Bug #39646
		'failed',  # Bug #39646
		'Failed to process Subfile /etc/univention/templates/files/etc/postgresql/.*/main/pg_hba.conf.d/.*-pg_.*.conf',  # 39595
		'/usr/sbin/grub-probe: error: cannot find a GRUB drive for /dev/vda.  Check your device.map.',  # Bug #38911
		r'Checking grub-pc/install_devices for errors[.]+',  # Bug #40733
		r'Done checking grub-pc/install_devices for errors[.]',  # Bug #40733
		'.*well-known-sid-name-mapping.d/univention-ldap-server.py.*slapd.service.',  # Bug #44904
		'.*failed to receive current ID.*',  # Bug 40962
		'.*error 104: Connection reset by peer while receiving from notifier.*',  # Bug 40962
		'E: object not found',
	]

	# extra ignore patterns for case when line == 'failed.'
	extra_ignore_list = (
		'Starting Univention Directory Notifier daemon.*',
		'warning: univention-directory-notifier: unable to open supervise/ok: file does not exist.*',
		'Terminating running univention-cli-server processes.*',
		'Stopping univention-s4-connector daemon.*',
	)


class Tracebacks(LogMessage):
	wanted_list = [
		".*traceback.*",
	]

	ignore_list = []
	extra_ignore_list = []


class Warnings(LogMessage):
	wanted_list = [
		".*warning.*",
	]

	# possible (ignored) warnings:
	ignore_list = [
		'WARNING: The following packages cannot be authenticated!',
		'Authentication warning overridden.',
		'^Create .*/warning',
		'WARNING: You are logged in using SSH -- this may interrupt the update and result in an inconsistent system!',
		'dpkg - warning: ignoring request to remove .* which isn.t installed.',
		'dpkg: warning - unable to delete old directory .*: Directory not empty',
		'dpkg - warning, overriding problem because --force enabled',
		'dpkg: serious warning: files list file for package .* missing, assuming package has no files currently installed.',
		'.*dpkg: warning: unable to delete old directory .* Directory not empty.*',
		'WARNING: cannot append .* to .*, value exists',
		'Warning: The config registry variable .*? does not exist',
		'Total Warnings:\s+\d+',
		'sys:1: DeprecationWarning: Non-ASCII character.*but no encoding declared; see http://www.python.org/peps/pep-0263.html for details',
		'warning: commands will be executed using /bin/.*',
		'Not updating .*',
		'Warning: The home dir .* you specified already exists.',
		'WARNING!',
		'.*WARNING: All config files need \.conf: /etc/modprobe\.d/.+, it will be ignored in a future release\.',
		'update-rc\.d: warning: .* (?:start|stop) runlevel arguments \([^)]+\) do not match LSB Default-(?:Start|Stop) values [^)]+',
		'.*warning: rule .* already exists.*',
		'.*Not starting .*: no services enabled.*',
		'.*Running /etc/init.d/.* is deprecated.*',
		'.*The resulting partition is not properly aligned for best performance.*',
		'.*Updating certificates in /etc/ssl/certs.* WARNING: Skipping duplicate certificate ca-certificates.crt.*',
		'.*Permanently added .* to the list of known hosts.*',
		'.*usr/sbin/grub-probe: warning: disk does not exist, so falling back to partition device.*',
		'.*WARNING: cannot read /sys/block/vda.* (?:No such file or directory|Datei oder Verzeichnis nicht gefunden).*',
		'.*warning: univention-directory-notifier: unable to open supervise/ok: .*',
		'.*No path in service .* - making it unavailable!',
	]

	extra_ignore_list = []
