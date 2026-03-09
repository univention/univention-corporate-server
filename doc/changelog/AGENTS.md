# Changelog Documentation

Per-release changelog for UCS patch levels. Lists security updates, bug fixes, and package changes. Versioned down to the patch level (e.g., `5.2-5`).

## Format

Sphinx RST (`index.rst`, `conf.py`).

## Build

```sh
make html      # Build HTML
make spelling  # Spell check
```

Uses the Sphinx Docker image from the parent `doc/Makefile`. Version is set via `CHANGELOG_TARGET_VERSION` in `.gitlab-ci/base-doc.yml`.
