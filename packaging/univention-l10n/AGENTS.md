# univention-l10n

Development tools for building and installing localization (l10n/i18n) data for UCS packages. Handles PO file extraction, merging, and translation template generation.

## Binary Packages

- `univention-l10n-dev` -- Build-time l10n tools and Python library

## Directory Structure

- `univention/` -- Python package (`univention.l10n`)
- `univention-l10n-build` -- Build-time script to compile translations
- `univention-l10n-install` -- Install-time script for translation files
- `univention-ucs-translation-build-package` -- Builds translation packages
- `univention-ucs-translation-merge` -- Merges translation catalogs
- `univention-ucs-translation-fakemessage` -- Generates fake translations for testing
- `univention-l10n.schema.json` -- JSON schema for l10n configuration
- `univention_l10n.pm` -- Perl debhelper plugin
- `setup.py`, `setup.cfg` -- Python packaging
