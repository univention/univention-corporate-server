# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  creates a report document
#
# Copyright 2007-2019 Univention GmbH
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

from __future__ import print_function

import os
import sys
import copy
import codecs
import tempfile
import subprocess

from univention.directory.reports.error import ReportError
from univention.directory.reports.parser import Parser
from univention.directory.reports.output import Output
from univention.directory.reports.interpreter import Interpreter
from univention.directory.reports import admin

import trml2pdf

from univention.lib.i18n import Translation
_ = Translation('univention-directory-reports').translate


class Document(object):
	(TYPE_LATEX, TYPE_CSV, TYPE_RML, TYPE_UNKNOWN) = range(4)

	@classmethod
	def get_type(cls, template):
		if template.endswith('.tex'):
			return cls.TYPE_LATEX
		elif template.endswith('.csv'):
			return cls.TYPE_CSV
		elif template.endswith('.rml'):
			return cls.TYPE_RML
		return cls.TYPE_UNKNOWN

	def __init__(self, template, header=None, footer=None):
		self._template = template
		self._header = header
		self._footer = footer
		self._type = self.get_type(self._template)
		self.__check_files()

	def __check_files(self):
		if self._type in (Document.TYPE_LATEX, Document.TYPE_RML):
			files = (self._header, self._footer, self._template)
		elif self._type == Document.TYPE_CSV:
			files = (self._template, )
		else:
			files = tuple()
		for filename in files:
			if not os.path.isfile(filename):
				raise ReportError(_("Configuration error: File %r could not be opened.") % (filename,))

	def __create_tempfile(self):
		if self._type == Document.TYPE_LATEX:
			suffix = '.src'
		elif self._type == Document.TYPE_CSV:
			suffix = '.csv'
		else:
			suffix = self._template.rsplit('.', 1)[1]
		fd, filename = tempfile.mkstemp(suffix, 'univention-directory-reports-')
		os.chmod(filename, 0o644)
		os.close(fd)

		return filename

	def __append_file(self, fd, filename, obj=None):
		parser = Parser(filename=filename)
		parser.tokenize()
		tks = copy.deepcopy(parser._tokens)
		interpret = Interpreter(obj, tks)
		interpret.run()
		output = Output(tks, fd=fd)
		output.write()

	def create_source(self, objects=[]):
		"""Create report from objects (list of DNs)."""
		tmpfile = self.__create_tempfile()
		admin.set_format(self._type)
		parser = Parser(filename=self._template)
		parser.tokenize()
		tokens = parser._tokens
		fd = codecs.open(tmpfile, 'wb+', encoding='utf8')
		if parser._header:
			fd.write(parser._header.data)
		elif self._header:
			self.__append_file(fd, self._header)

		for dn in objects:
			if isinstance(dn, basestring):
				obj = admin.get_object(None, dn)
			else:
				obj = admin.cache_object(dn)
			if obj is None:
				print("warning: dn '%s' not found, skipped." % dn, file=sys.stderr)
				continue
			tks = copy.deepcopy(tokens)
			interpret = Interpreter(obj, tks)
			interpret.run()
			output = Output(tks, fd=fd)
			output.write()
		if parser._footer:
			fd.write(parser._footer.data)
		elif self._footer:
			self.__append_file(fd, self._footer)
		fd.close()

		return tmpfile

	def create_pdf(self, latex_file):
		"""Run pdflatex on latex_file and return path to generated file or None on errors."""
		cmd = ['/usr/bin/pdflatex', '-interaction=nonstopmode', '-halt-on-error', '-output-directory=%s' % os.path.dirname(latex_file), latex_file]
		devnull = open(os.path.devnull, 'w')
		try:
			env_vars = {'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin', 'HOME': '/var/cache/univention-directory-reports'}
			if not subprocess.call(cmd, stdout=devnull, stderr=devnull, env=env_vars):
				if not subprocess.call(cmd, stdout=devnull, stderr=devnull, env=env_vars):
					return '%s.pdf' % latex_file.rsplit('.', 1)[0]
			raise ReportError(_('Failed creating PDF file.'))
		finally:
			devnull.close()
			basefile = latex_file.rsplit('.', 1)[0]  # strip suffix
			for file_ in [latex_file] + ['%s.%s' % (basefile, suffix) for suffix in ('aux', 'log')]:
				try:
					os.unlink(file_)
				except EnvironmentError:
					pass

	def create_rml_pdf(self, rml_file):
		output = '%s.pdf' % (os.path.splitext(rml_file)[0],)
		with open(rml_file, 'rb') as fd:
			outputfile = trml2pdf.parseString(fd.read(), output)
		try:
			os.unlink(rml_file)
		except EnvironmentError:
			pass
		return outputfile
