# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.admin._ucr import configRegistry


__all__ = ['Authorization']

if configRegistry.is_true('directory/manager/delegative-administration/guardian'):
    from univention.admin.authorization import Authorization
else:
    from univention.admin.authorization.local import Authorization
