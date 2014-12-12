# -*- coding: utf-8 -*.
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
                '.*Failed to join domain: failed to find DC for domain.*'  # Bug 37226
	]

	# extra ignore patterns for case when line == 'failed.'
	extra_ignore_list = (
		'Starting Univention Directory Notifier daemon.*',
		'warning: univention-directory-notifier: unable to open supervise/ok: file does not exist.*'
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
                '.*No path in service .* - making it unavailable!']

	extra_ignore_list = []
