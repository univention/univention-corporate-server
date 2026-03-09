# Univention Corporate Server (UCS)

Debian-based Linux distribution featuring the open-source identity and access management (IAM) "Nubus" and various integrated infrastructure and network services like Active Directory services (via Samba), RADIUS, Postfix, and Dovecot, and integrated server/cloud application management. Licensed under AGPLv3 (REUSE 3.3 compliant).

## Product Architecture

- The IAM **Nubus** is the **core domain**. It can be deployed on UCS (Debian packages) and in Kubernetes ("Nubus for Kubernetes", packaged with Helm).
- Additional services (Samba, RADIUS, Postfix, Dovecot, and App Center applications) belong to **supporting domains**.
- Some IAM components, although technically installed by the App Center, are part of Nubus (core domain): the Identity Provider (IdP) **Keycloak**, the authorization component **Guardian**, and the event system **Nubus Provisioning**.

### App Center

- Besides installing software using Debian packages, UCS can install additional software using the **App Center**.
- The App Center installs mostly third-party applications and connectors (e.g. Nextcloud, Open-Xchange) that get automatically integrated with the IAM's authentication and user provisioning mechanisms.
- The App Center installs software either using Debian packages from additional repositories or using Docker Compose.
- The App Center exists only in UCS, **not** in Kubernetes.

### Event Systems

UCS has two event systems for reacting to changes in the LDAP database:

- **Listener/Notifier**: An OpenLDAP overlay notifies a network service (the Notifier) about LDAP changes. The Listener service connects to the Notifier, retrieves changed objects, and executes Python-based Listener Modules. Also used for LDAP replication between UCS nodes. See [management/AGENTS.md](management/AGENTS.md) for details.
- **Nubus Provisioning**: A generic networked event system whose clients are called *Consumers*. Although it can enqueue all kinds of events, it is primarily used — like the Listener/Notifier system — to react to changes in the LDAP database. The source code is in a separate Git repository.

### Data Model and Persistence (UDM)

- UCS's primary database is an **LDAP directory**.
- The data model is implemented in the **UCS Directory Manager (UDM)**, a persistence layer between applications and LDAP that implements the IAM business logic.
- UDM has three interfaces: a **Python API**, a **CLI**, and a **REST API**. For details, see [management/univention-directory-manager-modules/AGENTS.md](management/univention-directory-manager-modules/AGENTS.md).
- Applications that interact with data in the LDAP directory **MUST** use UDM to change (create, update, delete) it and **SHOULD** use UDM to search and read it.
- For performance reasons, or because UDM objects don't expose all details of their corresponding LDAP objects, applications sometimes access LDAP directly.
  - This is a **layer violation** and generally undesirable. Data representation in LDAP and UDM can differ — the encoding of UDM data in LDAP is an internal technical detail.
  - Reading data from LDAP directly can be necessary in some circumstances. When you see this, **warn** developers that they are committing a layer violation.
  - Writing data directly to LDAP is strictly forbidden. Clients **MUST** use UDM for that. When you see this, treat it as an **error**.
- Changes to LDAP trigger two event systems — see the [Event Systems](#event-systems) section.

### Authentication

- Authentication is done using **Keycloak**. Keycloak imports users and groups from LDAP.

### Authorization

- Authorization is mostly implemented by each application individually (the legacy approach).
- UCS services are being migrated to a networked component called **Guardian**, which implements attribute-based access control (ABAC). Its source code is in a separate Git repository.

### User Interfaces

- Traditional UIs for UCS are web UIs implemented using the **UCS Management Console (UMC)** framework. For details, see [management/univention-management-console/AGENTS.md](management/univention-management-console/AGENTS.md).
- Newer UIs are web UIs running in Docker containers, with their source code in separate Git repositories.

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

The Python package tree is fractured across this repository to fit Debian packaging needs. When looking for a `univention.*`, `listener`, or `heimdal` module, use the `python-packages` skill for the full mapping of modules to directories.

### Pre-commit

The `.pre-commit-config.yaml` enforces: ruff, isort, autopep8, flake8, UCR template checks, debian control/changelog formatting, JSON/YAML/XML validation, trailing whitespace, REUSE compliance, and conventional commit messages.

**IMPORTANT:** After changing any file, ALWAYS run `prek` to execute the pre-commit linters and verify that all checks pass. Fix any issues reported before proceeding. Do NOT skip this step.

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). Include bug number as `Bug #12345` in commit messages.

### Licensing

All files must have SPDX headers. Use `make reuse` to annotate modified files. See `REUSE.toml` and `.reuse/` for templates.

### CI/CD

GitLab CI (`.gitlab-ci.yml`) with stages: prepare, build, test. The pipeline auto-generates build jobs from `debian/control` files. Documentation and debian package builds are triggered by file changes.

### UCR (Univention Config Registry)

Many packages use UCR templates (`conffiles/`) that generate config files from UCR variables. UCR templates have their own linting (`ucr-flake8`, `ucr-ruff`).
