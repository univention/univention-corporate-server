#
# Univention Directory Reports
#  module for creating reports about any kind of Univention Admin object
#
# SPDX-FileCopyrightText: 2007-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


from univention.directory.reports.admin import cache_object, connect, connected, get_object, identify, set_format
from univention.directory.reports.config import Config
from univention.directory.reports.document import Document
from univention.directory.reports.error import ReportError
from univention.directory.reports.report import Report


__all__ = ['Config', 'Document', 'Report', 'ReportError', 'cache_object', 'connect', 'connected', 'get_object', 'identify', 'set_format']
