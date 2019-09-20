# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#
# Copyright 2017-2019 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

import os

from univention.directory.reports.error import ReportError
from univention.directory.reports.document import Document
from univention.directory.reports.admin import connect, clear_cache
from univention.directory.reports.config import Config

from univention.lib.i18n import Translation
_ = Translation('univention-directory-reports').translate


class Report(object):

	def __init__(self, lo, config=None):
		self.lo = lo
		self.config = config or Config()

	def create(self, module, report, objects):
		"""Create a report of objects for the specified module in the specified report type format"""
		connect(access=self.lo)
		clear_cache()

		template = self.config.get_report(module, report)
		if template is None:
			if not module:
				raise ReportError(_('Please specify a module.'))
			if module not in self.config._reports:
				raise ReportError(_('No report for the specified module %r exists.') % (module,))
			if report:
				raise ReportError(_('The report %r does not exists or is misconfigured.') % (report,))
			raise ReportError(_('No %r report exists for the module %r.') % (report, module))

		suffix = '.rml' if Document.get_type(template) == Document.TYPE_RML else '.tex'
		header = self.config.get_header(module, report, suffix)
		footer = self.config.get_footer(module, report, suffix)
		doc = Document(template, header=header, footer=footer)

		tmpfile = doc.create_source(objects)
		pdffile = tmpfile
		func = {Document.TYPE_RML: doc.create_rml_pdf, Document.TYPE_LATEX: doc.create_pdf}.get(doc._type)
		if func:
			pdffile = func(tmpfile)
		if not pdffile or not os.path.exists(pdffile):
			raise ReportError(_('The report could not be created.'))
		return pdffile
