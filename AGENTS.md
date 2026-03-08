# Univention Corporate Server (UCS) - Repository Guide

This repository contains the source code of most parts of Univention Corporate Server (UCS), a Debian-based Linux distribution featuring the IAM "Nubus" and integrated network services (Samba, RADIUS, Postfix, Dovecot, etc.).

The repository contains mostly Debian source packages, Sphinx documentation, and integration tests. Deployment code is mostly shell; business logic is mostly Python.

## UCS versions

- Format: `<MAJOR>.<MINOR>-<PATCH>` (e.g., `4.4-10`, `5.2-5`).
- Git branches matching this format exactly are **release branches** (e.g., `4.4-10`, `5.2-5`). All other branches are NOT release branches, even those starting with `release-`.
- The **default branch** is the newest published UCS version (NOT `main` or `master`).

## Package updates (errata)

- Package updates for a UCS version are called **errata updates**.
- They have a monotonically growing number starting at `1` with the release of the major version.
- Every package update requires an **advisory**.
- Advisories for planned updates: `doc/errata/staging/`
- Advisories for released updates: `doc/errata/published/`

## Python

### Python versions

| UCS version | Python version(s) |
|---|---|
| UCS 5.2 | Python 3.11 |
| UCS 5.0 | Python 3.7 |
| UCS 4.4 | Python 2.7 and Python 3.7 |
| Older | Not supported |

### Python package index

The Python package tree is fractured across this repository to fit Debian packaging needs. When looking for a `univention.*` module, search the entire repository.

#### Installable Python distributions (have setup.py / setup.cfg)

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
| univention-unittests | `packaging/univention-unittests` | Pytest plugins for UCS |
| ucslint | `packaging/ucslint` | `univention.ucslint` |
| univention-radius | `services/univention-radius` | `univention.radius` |

#### Python modules installed via Debian packaging only (no setup.py)

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

## Debian source packages

Most subdirectories containing a `debian/` folder are Debian source packages. Official binary packages are NOT built by GitLab CI, but in a dedicated build system accessed via SSH.

## AGENTS.md index

| File | Description |
|---|---|
| [base/AGENTS.md](base/AGENTS.md) | Base system packages: UCR, PAM, Kerberos, SSL, updater, shared libraries |
| [container/AGENTS.md](container/AGENTS.md) | Docker-related packages for running UCS in containers |
| [doc/AGENTS.md](doc/AGENTS.md) | Sphinx product documentation, errata advisories |
| [mail/AGENTS.md](mail/AGENTS.md) | Mail services: Postfix, Dovecot, fetchmail, spam/antivirus |
| [management/AGENTS.md](management/AGENTS.md) | IAM core: LDAP, UDM, UMC, App Center, Portal, Self Service, domain join |
| [monitoring/AGENTS.md](monitoring/AGENTS.md) | Monitoring: Nagios plugins, monitoring client |
| [oidc/AGENTS.md](oidc/AGENTS.md) | OpenID Connect: SASL OAUTHBEARER plugin |
| [packaging/AGENTS.md](packaging/AGENTS.md) | Packaging tools: ucslint, debhelper, l10n, templates, pytest plugins |
| [saml/AGENTS.md](saml/AGENTS.md) | SAML: PAM module for SAML assertion verification |
| [services/AGENTS.md](services/AGENTS.md) | Network services: DNS, DHCP, Samba, RADIUS, AD/S4 connectors, Apache, databases |
| [test/AGENTS.md](test/AGENTS.md) | Integration tests, CI scenarios, test framework, utilities |
