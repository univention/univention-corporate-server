# Extended Windows Integration Documentation

Extended documentation for Windows integration with UCS. Covers advanced Samba/AD topics including read-only domain controllers, Group Policy Objects (GPO), and Active Directory integration.

## Format

Sphinx RST (`index.rst`, `conf.py`). Single-file document with `images/` directory.

## Build

```sh
make html      # Build HTML
make spelling  # Spell check
```

Uses the Sphinx Docker image from the parent `doc/Makefile`.
