# Extended Domain Services Documentation

Extended documentation for UCS domain services. Covers Unix system integration and SSL certificate management.

## Format

Sphinx RST (`index.rst`, `conf.py`). Files: `unix.rst`, `ssl.rst`.

## Build

```sh
make html      # Build HTML
make spelling  # Spell check
```

Uses the Sphinx Docker image from the parent `doc/Makefile`.
