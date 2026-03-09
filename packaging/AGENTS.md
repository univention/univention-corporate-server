# packaging/

Build and packaging tools, linters, localization utilities, pytest plugins, and example/template packages for UCS Debian package development.

All subdirectories are Debian source packages (each contains a `debian/` directory):

- [ucslint/AGENTS.md](ucslint/AGENTS.md) -- Linter that checks Debian source packages against common UCS packaging mistakes.
- [univention-debhelper/AGENTS.md](univention-debhelper/AGENTS.md) -- Helper programs for `debian/rules` to automate UCS package build tasks.
- [univention-directory-manager-module-example/AGENTS.md](univention-directory-manager-module-example/AGENTS.md) -- Example UDM module demonstrating how to manage custom LDAP objects.
- [univention-l10n/AGENTS.md](univention-l10n/AGENTS.md) -- Development tools for building localization (l10n) data for UCS packages.
- [univention-package-template/AGENTS.md](univention-package-template/AGENTS.md) -- Template/scaffold for creating new UCS Debian packages.
- [univention-package-template-python/AGENTS.md](univention-package-template-python/AGENTS.md) -- Template/scaffold for creating new UCS Python module packages.
- [univention-unittests/AGENTS.md](univention-unittests/AGENTS.md) -- Pytest plugins for UCS-specific unit testing.
