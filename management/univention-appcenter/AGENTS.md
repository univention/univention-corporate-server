# univention-appcenter

Univention App Center: app lifecycle management, Docker integration, and UMC modules for software management.

## Binary packages

- `univention-management-console-module-appcenter` -- UMC module for package/app management
- `univention-appcenter` -- CLI tools for the App Center
- `python3-univention-appcenter` -- Python library for App Center
- `univention-appcenter-dev` / `python3-univention-appcenter-dev` -- Development tools
- `univention-appcenter-docker` / `python3-univention-appcenter-docker` -- Docker integration
- `univention-management-console-module-apps` -- UMC overview page for installed apps

## Directory structure

- `python/` -- Python library modules (`univention.appcenter`)
- `umc/` -- UMC module definitions (Python + JS)
- `conffiles/` -- UCR templates
- `udm/` -- UDM module extensions
- `listener/` -- Directory Listener modules
- `ldap/` -- LDAP schema files
- `scripts/` -- Helper scripts
- `unittests/` -- Unit tests
- `debian/` -- Debian packaging
