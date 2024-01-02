#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2013-2024 Univention GmbH
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

from .l10n import (
    DIR_BLACKLIST, MODULE_BLACKLIST, REFERENCE_LANG, UMC_MODULES, Error, MIMEChecker, NoMatchingFiles,
    NoSpecialCaseDefintionsFound, SpecialCase, UMCModuleTranslation, create_new_package, find_base_translation_modules,
    get_special_cases_from_checkout, get_special_cases_from_srcpkg, message_catalogs, read_special_case_definition,
    sourcefileprocessing, template_file, translate_special_case, update_package_translation_files, write_makefile,
)


__all__ = ['DIR_BLACKLIST', 'Error', 'MIMEChecker', 'MODULE_BLACKLIST', 'NoMatchingFiles', 'NoSpecialCaseDefintionsFound', 'REFERENCE_LANG', 'SpecialCase', 'UMCModuleTranslation', 'UMC_MODULES', 'create_new_package', 'find_base_translation_modules', 'get_special_cases_from_checkout', 'get_special_cases_from_srcpkg', 'message_catalogs', 'read_special_case_definition', 'sourcefileprocessing', 'template_file', 'translate_special_case', 'update_package_translation_files', 'write_makefile']
