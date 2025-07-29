#
# Univention Directory Reports
#  write an interpreted token structure to a file
#
# SPDX-FileCopyrightText: 2007-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import locale
import os.path
import shlex
from configparser import ConfigParser


class Config(ConfigParser):

    def __init__(self, filename='/etc/univention/directory/reports/config.ini'):
        ConfigParser.__init__(self)
        self._filename = filename
        self.read(filename)
        defaults = self.defaults()
        self._oldHeader = defaults.get('header', None)
        self._oldFooter = defaults.get('footer', None)
        self.default_report_name = defaults.get('report', None)
        self.default_report_dir = defaults.get('output_dir', None)
        self._reports = {}

        # get the language, defaults to English if nothing is set
        self._lang = locale.getlocale(locale.LC_MESSAGES)[0]
        if not self._lang:
            self._lang = "en_US"

        for _key, value in self.items('reports'):
            # Entries are expected to have the form (see also config.ini):
            #   <module> <name> <directoryPath> <templateFile>
            # For compatibility reasons, we need also to accept the deprecated format:
            #   <module> <name> <templateFilePath>
            # make sure that the entries match this format
            module, name, dir, filename = [''] * 4
            tmpList = shlex.split(value)
            if len(tmpList) == 3:
                # old format, insert empty string for 'directory'
                tmpList.insert(2, '')
            if len(tmpList) != 4:
                # wrong format
                continue
            module, name, dir, filename = tmpList

            # save the entry to our internal list
            if module in self._reports:
                self._reports[module].append((name, dir, filename))
            else:
                self._reports[module] = [(name, dir, filename)]

    def _get_report_entry(self, module, name=None):
        """Find the correct internal report entry for a given a module and a report name."""
        # return None for non-existent module
        if module not in self._reports:
            return None
        # return first report if only the module name is given
        if not name:
            return self._reports[module][0]
        # if module name and report name are given, try to find the correct entry
        for report in self._reports[module]:
            if report[0] == name:
                return report
        # if anything fails, return None
        return None

    def _guess_path(self, directory, fileName, alternativePath=''):
        """
        Guess the correct path for a given template file. Possible paths:
        (1) directory/<language>/fileName
        (2) directory/fileName
        (3) alternativePath
        """
        # guess the header/footer path in order to support the old format
        guessedPaths = []

        # if the directory path is non-empty, this is how it should be, our first guess
        if directory:
            guessedPaths.append(os.path.join(directory, self._lang, fileName))
        # in case there is no language directory, our second guess
        # (works also for empty directory)
        guessedPaths.append(os.path.join(directory, fileName))
        # if given, our last guess is the alternative path
        if alternativePath:
            guessedPaths.append(alternativePath)

        # get the first valid path
        while guessedPaths:
            path = guessedPaths.pop(0)
            if os.path.exists(path):
                return path
        return None

    def get_header(self, module, name=None, suffix='.tex'):
        report = self._get_report_entry(module, name)
        if not report:
            return None
        return self._guess_path(report[1], 'header%s' % (suffix,), self._oldHeader)

    def get_footer(self, module, name=None, suffix='.tex'):
        report = self._get_report_entry(module, name)
        if not report:
            return None
        return self._guess_path(report[1], 'footer%s' % (suffix,), self._oldFooter)

    def get_report_names(self, module):
        reports = self._reports.get(module, [])
        return [item[0] for item in reports]

    def get_report(self, module, name=None):
        report = self._get_report_entry(module, name)
        if not report:
            return None
        return self._guess_path(report[1], report[2])

    def get_output_dir(self):
        if self.default_report_dir and os.path.exists(self.default_report_dir):
            return self.default_report_dir
