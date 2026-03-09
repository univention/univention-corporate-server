# Extended Installation Documentation

Extended documentation for UCS installation methods. Covers UCS appliance setup, custom appliance builds, and profile-based automated installation.

## Format

Sphinx RST (`index.rst`, `conf.py`). Files: `ucs-appliance.rst`, `appliance.rst`, `profile.rst`.

## Build

```sh
make html      # Build HTML
make spelling  # Spell check
```

Uses the Sphinx Docker image from the parent `doc/Makefile`.
