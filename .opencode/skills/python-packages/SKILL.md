---
name: python-packages
description: Maps univention.* Python modules to their source directories in this monorepo. Use when looking for where a univention module is defined or when resolving import paths.
---

# Python Package Index

The Python package tree is fractured across this repository to fit Debian packaging needs. When looking for a `univention.*` module, search the entire repository.

## Installable Python distributions (have setup.py / setup.cfg)

| Distribution name | Directory | Key Python modules |
|---|---|---|
| Univention Configuration Registry | `base/univention-config-registry` | `univention.config_registry` |
| univention-debug-python | `base/univention-debug-python` | `univention.debug` (Python interface) |
| univention-ipcalc | `base/univention-ipcalc` | `univention.ipcalc` |
| univention-licence-python | `base/univention-licence-python` | `univention.license` |
| univention-python | `base/univention-python` | `univention.uldap`, `univention.config_registry` helpers |
| univention-python-heimdal | `base/univention-python-heimdal` | `heimdal` (C extension) |
| Univention Updater | `base/univention-updater` | `univention.updater` |
| univention-appcenter | `management/univention-appcenter` | `univention.appcenter` |
| univention-directory-listener | `management/univention-directory-listener` | `univention.listener` |
| univention-management-console | `management/univention-management-console` | `univention.management.console` |
| univention-portal | `management/univention-portal` | `univention.portal` |
| univention-debhelper | `packaging/univention-debhelper` | `univention.debhelper` |
| univention-l10n | `packaging/univention-l10n` | `univention.l10n` |
| univention-unittests | `packaging/univention-unittests` | `univentionunittests` |
| ucslint | `packaging/ucslint` | `univention.ucslint` |
| univention-radius | `services/univention-radius` | `univention.radius` |

## Python modules installed via Debian packaging only (no setup.py)

| Python module | Directory |
|---|---|
| `univention.admin`, `univention.udm`, `univention.admincli` | `management/univention-directory-manager-modules` |
| `univention.admin.rest` | `management/univention-directory-manager-rest` |
| `univention.authorization` | `management/univention-authorization` |
| `univention.directory.reports` | `management/univention-directory-reports` |
| `univention.lib` | `base/univention-lib` |
| `univention.ldap_cache` | `base/univention-group-membership-cache` |
| `univention.connector` | `services/univention-ad-connector` |
| `univention.s4connector` | `services/univention-s4-connector` |
| `univention.mail` | `mail/univention-mail-dovecot` |
| `univention.monitoring` | `monitoring/univention-monitoring-client` |
| `univention.testing` | `test/ucs-test` |
| `listener` | `management/univention-directory-listener` |
