#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2013-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from .l10n import (
    DIR_BLACKLIST, MODULE_BLACKLIST, REFERENCE_LANG, UMC_MODULES, Error, MIMEChecker, NoMatchingFiles,
    NoSpecialCaseDefintionsFound, SpecialCase, UMCModuleTranslation, create_new_package, find_base_translation_modules,
    get_special_cases_from_checkout, get_special_cases_from_srcpkg, message_catalogs, read_special_case_definition,
    sourcefileprocessing, template_file, translate_special_case, update_package_translation_files, write_makefile,
)


__all__ = ['DIR_BLACKLIST', 'MODULE_BLACKLIST', 'REFERENCE_LANG', 'UMC_MODULES', 'Error', 'MIMEChecker', 'NoMatchingFiles', 'NoSpecialCaseDefintionsFound', 'SpecialCase', 'UMCModuleTranslation', 'create_new_package', 'find_base_translation_modules', 'get_special_cases_from_checkout', 'get_special_cases_from_srcpkg', 'message_catalogs', 'read_special_case_definition', 'sourcefileprocessing', 'template_file', 'translate_special_case', 'update_package_translation_files', 'write_makefile']
