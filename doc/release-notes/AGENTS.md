# Release Notes

Release notes for each UCS patch level release. Covers release highlights, installation/update instructions, resolved issues, and known problems. German translation available via `locales/`.

## Format

Sphinx RST (`index.rst`, `conf.py`). Versioned per patch level (e.g., `5.2-5`) via `CHANGELOG_TARGET_VERSION`.

## Build

```sh
make html      # Build HTML
make spelling  # Spell check
```

Uses the Sphinx Docker image from the parent `doc/Makefile`.
