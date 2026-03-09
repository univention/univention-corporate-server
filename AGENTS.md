# Univention Corporate Server (UCS)

Open-source identity management and IT infrastructure platform. Features Active Directory services (via Samba), an App Center, LDAP directory, and integrated server/cloud application management. Licensed under AGPLv3 (REUSE 3.3 compliant).

## Repository Layout

Each top-level directory has its own `AGENTS.md` with further details:

- [base/AGENTS.md](base/AGENTS.md) -- Core system packages: config registry, PAM, SSL, firewall, Kerberos, updater, system setup, etc.
- [container/AGENTS.md](container/AGENTS.md) -- Docker container integration packages.
- [doc/AGENTS.md](doc/AGENTS.md) -- Documentation (manual, developer reference, architecture, release notes, errata).
- [mail/AGENTS.md](mail/AGENTS.md) -- Mail stack: Postfix, Dovecot, anti-virus, anti-spam, fetchmail.
- [management/AGENTS.md](management/AGENTS.md) -- Management layer: UMC (web console), UDM (directory manager), LDAP server, portal, App Center, join, self-service.
- [monitoring/AGENTS.md](monitoring/AGENTS.md) -- Monitoring: Nagios plugins for RAID, Samba, SMART, services, AD/S4 connectors.
- [oidc/AGENTS.md](oidc/AGENTS.md) -- OpenID Connect: SASL OAUTHBEARER plugin and PAM module for OAuth.
- [packaging/AGENTS.md](packaging/AGENTS.md) -- Build/packaging tools: ucslint, debhelper, l10n, UDM module example, pytest plugins.
- [saml/AGENTS.md](saml/AGENTS.md) -- SAML authentication: PAM and SASL plugins for SAML assertions.
- [services/AGENTS.md](services/AGENTS.md) -- Infrastructure services: DNS (BIND), DHCP, NFS, Samba, Samba4, Apache, RADIUS, AD/S4 connectors, Keycloak, Squid, etc.
- [test/AGENTS.md](test/AGENTS.md) -- Test framework and tools: ucs-test, GUI tests, product tests, scenarios, appliance generation.

## Conventions

### UCS versions

- Format: `<MAJOR>.<MINOR>-<PATCH>` (e.g., `4.4-10`, `5.2-5`).
- Git branches matching this format exactly are **release branches** (e.g., `4.4-10`, `5.2-5`). All other branches are NOT release branches, even those starting with `release-`.
- The **default branch** is the newest published UCS version (NOT `main` or `master`).

### Package updates (errata)

- Package updates for a UCS version are called **errata updates**.
- They have a monotonically growing number starting at `1` with the release of the major version.
- Every package update requires an **advisory**.
- Advisories for planned updates: `doc/errata/staging/`
- Advisories for released updates: `doc/errata/published/`

### Package Structure

Directories containing a `debian/` subdirectory are Debian source packages. Each builds one or more `.deb` packages. The `debian/control` file describes the package.

### Python

- Target: Python 3.11
- Style: PEP 8, max line length ~120 (not strictly enforced by ruff, which uses 180)
- Linters/formatters: ruff, isort, autopep8, flake8 (configured in `pyproject.toml`)
- Run `make lint` to check modified files, `make format` to auto-fix.

#### Python package index

The Python package tree is fractured across this repository to fit Debian packaging needs. When looking for a `univention.*` module, search the entire repository.

##### Installable Python distributions (have setup.py / setup.cfg)

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

##### Python modules installed via Debian packaging only (no setup.py)

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

### Pre-commit

The `.pre-commit-config.yaml` enforces: ruff, isort, autopep8, flake8, UCR template checks, debian control/changelog formatting, JSON/YAML/XML validation, trailing whitespace, REUSE compliance, and conventional commit messages.

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). Include bug number as `Bug #12345` in commit messages.

### Licensing

All files must have SPDX headers. Use `make reuse` to annotate modified files. See `REUSE.toml` and `.reuse/` for templates.

### CI/CD

GitLab CI (`.gitlab-ci.yml`) with stages: prepare, build, test. The pipeline auto-generates build jobs from `debian/control` files. Documentation and debian package builds are triggered by file changes.

### UCR (Univention Config Registry)

Many packages use UCR templates (`conffiles/`) that generate config files from UCR variables. UCR templates have their own linting (`ucr-flake8`, `ucr-ruff`).
