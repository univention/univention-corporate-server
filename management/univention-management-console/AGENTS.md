# univention-management-console

UCS Management Console (UMC): web-based administration tool with an extensible module architecture. Includes the backend server (Tornado), AJAX web frontend (Dojo-based), web server integration, Python library, and development tools.

## Binary packages

- `univention-management-console` -- Meta package pulling in all UMC components
- `univention-management-console-server` -- Backend daemon
- `python3-univention-management-console` -- Python library
- `univention-management-console-dev` -- Development files for UMC modules
- `univention-management-console-frontend` -- AJAX web frontend
- `univention-management-console-web-server` -- Apache/WSGI web server integration
- `univention-management-console-web-server-fix` -- Web server fix helper
- `univention-management-console-login` -- Generic login page

## Directory structure

- `src/` -- Python source (`univention.management.console`)
- `www/` -- Web frontend files (JS, HTML)
- `conffiles/` -- UCR templates
- `scripts/` -- Helper scripts
- `tests/` -- Test suite
- `dev/` -- Development utilities
- `umc-module-templates/` -- Templates for creating new UMC modules
- `systemd/` -- Systemd service files
- `data/` -- Static data files
- `debian/` -- Debian packaging
