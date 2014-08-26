# -*- coding: utf-8 -*.
import re


class Errors(object):
    wanted = map(lambda p: re.compile(p, re.IGNORECASE),
                 [".*(error).*",
                  ".*(failed).*",
                  ".*(usage).*",
                  "^E:"])

    # possible (ignored) errors:
    ignore_list = [
        '.*failedmirror=.*',
        'All done, no errors.',
        'I: .* libgpg-error0',
        'Installation finished. No error.* reported',
        'Not updating .*',
        'Error: There are no (services|hosts|host groups|contacts|contact groups) defined!',
        'Total Errors:\s+\d+',
        'Cannot find nagios object .*',
        'invoke-rc.d: initscript udev, action "reload" failed.',			# Bug 19227
        'yes: write error',
        '.*Update aborted by pre-update script of release.*',
        '.*update failed. Please check /var/log/univention/.*',
        '.*failed to convert the username listfilter to the uid.*',
        '.*Can not write log, .* failed.*',
        '.*Starting Univention Directory Policy:.*',
        '.*LISTENER .* : failed to connect to any notifier.*',
        '.*liberror-perl.*',
        '.*CONSISTENCY CHECK FAILED: cyls is too large .* setting to possible max .*',
        '.*error adding .*.pem',
        '.*failed .*VM used: java-6-cacao.*',
        '.*/etc/ca-certificates/update.d/.* exited with code 1']

    ignore = map(re.compile, ignore_list)


class Tracebacks(object):
    wanted = map(lambda p: re.compile(p, re.IGNORECASE),
                 [".*(traceback).*"])


class Warnings(object):
    wanted = map(lambda p: re.compile(p, re.IGNORECASE),
                 [".*(warning).*"])

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
        'update-rc\.d: warning: .* (start|stop) runlevel arguments \([^)]+\) do not match LSB Default-(Start|Stop) values ([^)]+)',
        '.*warning: rule .* already exists.*',
        '.*Not starting .*: no services enabled.*',
        '.*Running /etc/init.d/.* is deprecated.*',
        '.*The resulting partition is not properly aligned for best performance.*',
        '.*Updating certificates in /etc/ssl/certs.* WARNING: Skipping duplicate certificate ca-certificates.crt.*',
        '.*Permanently added .* to the list of known hosts.*',
        '.*usr/sbin/grub-probe: warning: disk does not exist, so falling back to partition device.*',
        '.*WARNING: cannot read /sys/block/vda.* No such file or directory.*']

    ignore = map(re.compile, ignore_list)
