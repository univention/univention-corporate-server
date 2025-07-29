#
# Univention Directory Reports
#
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os

from univention.directory.reports.admin import clear_cache, connect
from univention.directory.reports.config import Config
from univention.directory.reports.document import Document
from univention.directory.reports.error import ReportError
from univention.lib.i18n import Translation


_ = Translation('univention-directory-reports').translate


class Report:

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
