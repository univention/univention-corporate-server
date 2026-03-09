# Documentation (`doc/`)

Product documentation for Univention Corporate Server. All subdirectories are Sphinx RST documentation projects (not Debian packages), except `errata/` and `extended-docs/` which contain structured data.

## Build

The top-level `Makefile` drives all subdirectory builds via a Sphinx Docker image. Common targets: `make html`, `make latexpdf`, `make spelling`, `make clean`. Translations use `make update-po`.

## Subdirectories

- [app-center/AGENTS.md](app-center/AGENTS.md) -- App Center provider documentation (how to publish apps).
- [architecture/AGENTS.md](architecture/AGENTS.md) -- UCS architecture documentation (components, services, concepts).
- [changelog/AGENTS.md](changelog/AGENTS.md) -- Per-release changelog (security fixes, package updates).
- [debian-admins/AGENTS.md](debian-admins/AGENTS.md) -- Guide for Debian/Ubuntu admins transitioning to UCS.
- [developer-reference/AGENTS.md](developer-reference/AGENTS.md) -- Developer reference for extending UCS (UDM, UMC, listeners, packaging).
- [errata/AGENTS.md](errata/AGENTS.md) -- Errata advisory templates and schema (YAML/JSON, not Sphinx).
- [ext-delegative-administration/AGENTS.md](ext-delegative-administration/AGENTS.md) -- Delegative administration (experimental feature docs).
- [ext-domain/AGENTS.md](ext-domain/AGENTS.md) -- Extended domain services (Unix, SSL).
- [ext-installation/AGENTS.md](ext-installation/AGENTS.md) -- Extended installation docs (appliance, profile-based install).
- [ext-networks/AGENTS.md](ext-networks/AGENTS.md) -- Extended IP and network management (proxy, VLAN).
- [ext-performance/AGENTS.md](ext-performance/AGENTS.md) -- Performance guide for large environments.
- [ext-windows/AGENTS.md](ext-windows/AGENTS.md) -- Extended Windows integration (Samba/AD, GPO).
- [extended-docs/AGENTS.md](extended-docs/AGENTS.md) -- Structured data for deprecated UCR variables (YAML/JSON, not Sphinx).
- [manual/AGENTS.md](manual/AGENTS.md) -- Main UCS administrator manual.
- [quickstart/AGENTS.md](quickstart/AGENTS.md) -- Quickstart guide for new UCS users.
- [release-notes/AGENTS.md](release-notes/AGENTS.md) -- Release notes for each UCS patch level.
- [scenarios/AGENTS.md](scenarios/AGENTS.md) -- Deployment scenario descriptions (small, mid-sized, enterprise).
