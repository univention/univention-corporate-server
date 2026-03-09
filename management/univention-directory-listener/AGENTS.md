# univention-directory-listener

LDAP change notification client that invokes Python handler modules on object changes. Maintains a local LMDB cache to detect per-attribute changes and provides both old and new objects to handlers.

## Binary packages

- `univention-directory-listener`

## Directory structure

- `src/` -- C source code for the listener daemon
- `python/` -- Python modules (`univention.listener`)
- `listener/` -- Built-in listener handler modules
- `conffiles/` -- UCR templates
- `examples/` -- Example listener modules
- `tests/` -- Test suite
- `doc/` -- Documentation
- `etc/` -- Default configuration files
- `tools/` -- Helper tools
- `debian/` -- Debian packaging
