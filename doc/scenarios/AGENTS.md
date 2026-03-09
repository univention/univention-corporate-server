# Deployment Scenarios

Documentation describing UCS deployment scenarios for different organization sizes: small environments, mid-sized businesses, and enterprise setups. German translation available via `locales/`.

## Format

Sphinx RST (`index.rst`, `conf.py`). Files: `small.rst`, `mid-sized.rst`, `enterprise.rst`.

## Build

```sh
make html      # Build HTML
make spelling  # Spell check
```

Uses the Sphinx Docker image from the parent `doc/Makefile`.
