#
# UCS test
#
# SPDX-FileCopyrightText: 2016-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.appcenter.app_cache import Apps


APPCENTER_FILE = "/var/cache/appcenter-uninstalled.txt"


def get_requested_apps():
    ret = []
    try:
        with open(APPCENTER_FILE) as f:
            for line in f:
                app = Apps().find(line.strip())
                if app:
                    ret.append(app)
                else:
                    pass
                    # utils.fail('Error finding %s' % (line,))
    except OSError:
        pass
        # utils.fail('Error reading %s: %s' % (APPCENTER_FILE, exc))
    return ret
