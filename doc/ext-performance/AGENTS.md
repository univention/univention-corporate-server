# Performance Guide

Performance tuning guide for UCS environments with more than 5,000 users. Covers OpenLDAP optimization, listener/notifier replication tuning, Samba performance, and general system configuration.

## Format

Sphinx RST (`index.rst`, `conf.py`). Single-file document.

## Build

```sh
make html      # Build HTML
make spelling  # Spell check
```

Uses the Sphinx Docker image from the parent `doc/Makefile`.
