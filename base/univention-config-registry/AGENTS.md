# univention-config-registry

Univention Config Registry (UCR) -- the central configuration manager for UCS. Provides CLI tools, Python and C APIs for reading/writing UCR variables and generating config files from templates.

## Binary Packages

- `univention-config-registry` -- transitional package (now in univention-base-files)
- `univention-config` -- main UCR command-line tool
- `univention-config-dev` -- development helpers for packages using UCR
- `python3-univention-config-registry` -- Python 3 API
- `libunivention-config0` -- C shared library
- `libunivention-config-dev` -- C development headers

## Key Directories

- `python/` -- Python UCR modules (`univention.config_registry`)
- `lib/` -- C library source (autotools)
- `include/` -- C header files
- `scripts/` -- helper scripts
- `tests/` -- extensive test suite (pytest)
- `doc/` -- documentation
- `etc/` -- default config snippets

## Notes

- Has comprehensive pytest-based tests (`tests/`)
- C library built with autotools (`configure.in`, `Makefile.am`)
