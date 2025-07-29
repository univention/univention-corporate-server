#
# Univention Directory Manager Modules
#  direcory manager syntax for Apps
#
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.admin.syntax import OkOrNot, TrueFalseUp, boolean


# For UCS systems < UCS 4.4 in the domain we define these syntax classes and distribute them

try:
    from univention.admin.syntax import AppActivatedBoolean as appcenterFoo
    del appcenterFoo
except ImportError:
    class AppActivatedBoolean(boolean):
        pass

try:
    from univention.admin.syntax import AppActivatedTrue as appcenterFoo
    del appcenterFoo
except ImportError:
    class AppActivatedTrue(TrueFalseUp):
        pass

try:
    from univention.admin.syntax import AppActivatedOK as appcenterFoo
    del appcenterFoo
except ImportError:
    class AppActivatedOK(OkOrNot):
        pass
