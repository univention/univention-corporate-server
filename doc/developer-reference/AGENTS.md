# Developer Reference

Developer guide for extending UCS. Covers UDM (directory manager modules), UMC (web console modules), listener/notifier, UCR, LDAP, packaging, App Center integration, repositories, and translations.

## Format

Sphinx RST (`index.rst`, `conf.py`). Organized into topic subdirectories: `join/`, `listener/`, `packaging/`, `translation/`, `ucr/`, `udm/`, `umc/`.

## Build

```sh
make html      # Build HTML
make latexpdf  # Build PDF
make spelling  # Spell check
```

Uses the Sphinx Docker image from the parent `doc/Makefile`.
