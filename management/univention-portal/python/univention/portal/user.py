# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


from univention.portal import config


class User:
    def __init__(self, username, display_name, groups, headers):
        self.username = username
        self.display_name = display_name
        self.groups = [group.lower() for group in groups]
        self.headers = headers

    def is_admin(self):
        if self.is_anonymous():
            return False
        admin_groups = config.fetch("admin_groups")
        return any(self.is_member_of(group) for group in admin_groups)

    def is_anonymous(self):
        return self.username is None

    def is_member_of(self, group):
        return group.lower() in self.groups
