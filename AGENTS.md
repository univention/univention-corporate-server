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

### Package Structure

Directories containing a `debian/` subdirectory are Debian source packages. Each builds one or more `.deb` packages. The `debian/control` file describes the package.

### Python

- Target: Python 3.11
- Style: PEP 8, max line length ~120 (not strictly enforced by ruff, which uses 180)
- Linters/formatters: ruff, isort, autopep8, flake8 (configured in `pyproject.toml`)
- Run `make lint` to check modified files, `make format` to auto-fix.

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
