# Architecture Documentation

UCS architecture documentation covering system components, services, and design concepts. Organized into `components/`, `services/`, and `concepts/` subdirectories with ArchiMate modeling references.

## Format

Sphinx RST (`index.rst`, `conf.py`). Includes a bibliography (`bibliography.bib`).

## Build

```sh
make html      # Build HTML
make latexpdf  # Build PDF
make spelling  # Spell check
```

Uses the Sphinx Docker image from the parent `doc/Makefile`.
