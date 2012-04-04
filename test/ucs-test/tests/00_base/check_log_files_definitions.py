# -*- coding: utf-8 -*.
import re

# possible erros
class errors(object):
	wanted = map(lambda p: re.compile(p, re.IGNORECASE), [
		".*(traceback).*",
		".*(error).*",
		".*(failed).*",
		".*(usage).*",
		"^E:",
	])
	ignore = map(re.compile, [
		'ERROR: Site univention-admin does not exist',
		'.*failedmirror=.*',
		'All done, no errors.',
		'I: .* libgpg-error0',
		'Installation finished. No error reported',
		'/dev.*/instmnt.*,errors=',
		'/dev/.*open failed: Read-only file system',
		'ERROR: Site univention-admin does not exist',
		'account_policy_get: tdb_fetch_uint32 failed for field .*, returning 0',
		'psql:/var/lib/postgres/pkgdb.indexes-.*: ERROR:  relation ".*_index" already exists',
		'.*Not/Inst/Cfg-files/Unpacked/Failed-cfg/Half-inst/trig-aWait/Trig-pend.*',
		'Not updating .*',
		'Error: There are no (services|hosts|host groups|contacts|contact groups) defined!',
		'Total Errors:\s+\d+',
		'account_policy_get: tdb_fetch_uint32 failed for ',
		'Cannot find nagios object .*',
		'ldapError: Type or value exists',									# Bug 19227
		'sed: read error on stdin: Is a directory',							# Bug 19227
		'invoke-rc.d: initscript udev, action "reload" failed.',			# Bug 19227
		'yes: write error',
	])

# possible warnings
class warnings(object):
	wanted = map(lambda p: re.compile(p, re.IGNORECASE), [
		".*(warning).*",
	])
	ignore = map(re.compile, [
		'.*LibClamAV Warning: \*\*\*.*',
		'WARNING: The following packages cannot be authenticated!',
		'Authentication warning overridden.',
		'^Create .*/warning',
		'WARNING: You are logged in using SSH -- this may interrupt the update and result in an inconsistent system!',
		'dpkg - warning: ignoring request to remove .* which isn.t installed.',
		'dpkg: warning - unable to delete old directory .*: Directory not empty',
		'dpkg - warning, overriding problem because --force enabled',
		'WARNING: cannot append .* to .*, value exists',
		'.*WARNING: ucf was run from a maintainer script that uses debconf, but',
		'Warning: The config registry variable .*? does not exist',
		'Total Warnings:\s+\d+',
		'sys:1: DeprecationWarning: Non-ASCII character.*but no encoding declared; see http://www.python.org/peps/pep-0263.html for details',
		'warning: commands will be executed using /bin/.*',
		'Not updating .*',
		'Warning: The home dir .* you specified already exists.',
		'dpkg: serious warning: files list file for package .* missing, assuming package has no files currently installed.',
		'WARNING!',
		'.* Restarting Squid HTTP proxy squid .* WARNING: .* is a subnetwork of .*',
		'.* WARNING: because of this .* is ignored to keep splay tree searching predictable',
		'.* WARNING: You should probably remove .* from the ACL named \'localnet0\'',
		'.*WARNING: All config files need \.conf: /etc/modprobe\.d/.+, it will be ignored in a future release\.',
		'update-rc\.d: warning: .* (start|stop) runlevel arguments \([^)]+\) do not match LSB Default-(Start|Stop) values ([^)]+)',
	])
