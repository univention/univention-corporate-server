# UCS Manual

Main administrator manual for Univention Corporate Server. Covers installation, domain/LDAP management, user/group management, UMC, shares, mail, printing, monitoring, IP configuration, Windows integration, cloud identity management, and software management.

## Format

Sphinx RST (`index.rst`, `conf.py`). Organized into topic subdirectories: `domain-ldap/`, `user-management/`, `central-management-umc/`, `mail/`, `software/`, etc. German translation via `locales/`.

## Build

```sh
make html      # Build HTML
make latexpdf  # Build PDF
make spelling  # Spell check
```

Uses the Sphinx Docker image from the parent `doc/Makefile`.
